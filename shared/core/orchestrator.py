"""
Orquestador principal para el análisis inteligente de oportunidades
Coordina el flujo completo desde la recepción del payload hasta la respuesta
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional

from ..models.opportunity import OpportunityPayload
from ..services.openai_service import OpenAIService
from ..services.search_service import SearchService
from ..services.blob_storage_service import BlobStorageService
from ..services.cosmos_service import CosmosDBService
from ..generators.adaptive_card import generate_opportunity_card
from ..generators.pdf_generator import PDFGenerator


class OpportunityOrchestrator:
    """
    Orquestador para el análisis de oportunidades de Dynamics 365.
    
    Flujo:
    1. Recibir payload de Power Automate
    2. Validar y parsear datos de oportunidad
    3. Buscar equipos relevantes en Azure AI Search
    4. Analizar con DeepSeek-R1
    5. Generar PDF del análisis
    6. Guardar en Cosmos DB
    7. Generar Adaptive Card para Teams
    8. Retornar respuesta estructurada
    """
    
    def __init__(self):
        """Inicializa los servicios necesarios"""
        self.openai_service = OpenAIService()
        self.search_service = SearchService()
        self.blob_service = BlobStorageService()
        
        # Cosmos DB es opcional
        try:
            self.cosmos_service = CosmosDBService()
            self.cosmos_enabled = True
        except Exception as e:
            logging.warning(f"⚠️ Cosmos DB no configurado: {str(e)}")
            self.cosmos_service = None
            self.cosmos_enabled = False
        
        logging.info("✅ OpportunityOrchestrator inicializado")
    
    async def process_opportunity(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa una oportunidad recibida desde Power Automate
        
        Args:
            payload: Datos de la oportunidad desde Dataverse/Power Automate
            
        Returns:
            Diccionario con el resultado del análisis
        """
        start_time = datetime.utcnow()
        
        try:
            # ========================================
            # PASO 1: Validar y parsear payload
            # ========================================
            logging.info("📥 Paso 1: Validando payload...")
            
            try:
                opportunity = OpportunityPayload(**payload)
            except Exception as e:
                logging.error(f"❌ Error validando payload: {str(e)}")
                return self._error_response(
                    "VALIDATION_ERROR",
                    f"Error validando datos de oportunidad: {str(e)}",
                    payload.get("opportunityid", "unknown"),
                    payload.get("name", "Unknown")
                )
            
            logging.info(f"✅ Oportunidad validada: {opportunity.name}")
            
            # ========================================
            # PASO 2: Preparar texto para análisis
            # ========================================
            logging.info("📝 Paso 2: Preparando texto para análisis...")
            
            analysis_text = opportunity.format_for_analysis()
            logging.info(f"📝 Texto preparado: {len(analysis_text)} caracteres")
            
            # ========================================
            # PASO 3: Buscar equipos relevantes
            # ========================================
            logging.info("🔍 Paso 3: Buscando equipos relevantes...")
            
            # Usar la descripción limpia como query de búsqueda
            search_query = opportunity.clean_description[:500] if opportunity.clean_description else opportunity.name
            
            teams = self.search_service.search_teams(search_query, top=15)
            
            if not teams:
                logging.warning("⚠️ No se encontraron equipos, obteniendo todos...")
                teams = self.search_service.get_all_teams()
            
            logging.info(f"✅ {len(teams)} equipos encontrados")
            
            # ========================================
            # PASO 4: Análisis con IA
            # ========================================
            logging.info("🧠 Paso 4: Analizando con DeepSeek-R1...")
            
            analysis_result = self.openai_service.analyze_opportunity(
                opportunity_text=analysis_text,
                available_teams=teams
            )
            
            if not analysis_result:
                logging.error("❌ El análisis de IA no retornó resultados")
                return self._error_response(
                    "AI_ANALYSIS_ERROR",
                    "No se pudo completar el análisis con IA",
                    opportunity.opportunityid,
                    opportunity.name
                )
            
            logging.info("✅ Análisis completado")
            
            # ========================================
            # PASO 5: Procesar torres recomendadas
            # ========================================
            logging.info("🏗️ Paso 5: Procesando torres recomendadas...")
            
            # Normalizar torres del análisis
            required_towers = analysis_result.get("required_towers", [])
            team_recommendations = analysis_result.get("team_recommendations", [])
            
            # Enriquecer con datos de equipos encontrados
            enriched_teams = self._enrich_team_recommendations(team_recommendations, teams)
            analysis_result["team_recommendations"] = enriched_teams
            
            logging.info(f"✅ {len(required_towers)} torres requeridas, {len(enriched_teams)} equipos recomendados")
            
            # ========================================
            # PASO 6: Guardar en Cosmos DB (opcional)
            # ========================================
            cosmos_id = None
            if self.cosmos_enabled and self.cosmos_service:
                logging.info("💾 Paso 6: Guardando en Cosmos DB...")
                
                try:
                    record = {
                        "id": f"opp-{opportunity.opportunityid}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                        "opportunity_id": opportunity.opportunityid,
                        "opportunity_name": opportunity.name,
                        "opportunity_url": opportunity.dynamics_url,
                        "event_type": opportunity.event_type,
                        "analysis": analysis_result,
                        "processed_at": datetime.utcnow().isoformat(),
                        "source": "power_automate"
                    }
                    
                    result = self.cosmos_service.save_analysis(record)
                    cosmos_id = result.get("id") if result else None
                    logging.info(f"✅ Guardado en Cosmos: {cosmos_id}")
                except Exception as e:
                    logging.warning(f"⚠️ Error guardando en Cosmos: {str(e)}")
            else:
                logging.info("⏭️ Paso 6: Cosmos DB no habilitado, saltando...")
            
            # ========================================
            # PASO 7: Generar PDF
            # ========================================
            logging.info("📄 Paso 7: Generando PDF...")
            
            pdf_url = None
            try:
                pdf_generator = PDFGenerator()
                pdf_bytes = pdf_generator.generate(
                    title=f"Análisis: {opportunity.name}",
                    analysis=analysis_result,
                    metadata={
                        "opportunity_id": opportunity.opportunityid,
                        "opportunity_name": opportunity.name,
                        "opportunity_url": opportunity.dynamics_url,
                        "generated_at": datetime.utcnow().isoformat()
                    }
                )
                
                # Subir a Blob Storage
                blob_name = f"opportunity-analysis/{opportunity.opportunityid}/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
                pdf_url = self.blob_service.upload_pdf(pdf_bytes, blob_name)
                logging.info(f"✅ PDF subido: {blob_name}")
                
            except Exception as e:
                logging.warning(f"⚠️ Error generando PDF: {str(e)}")
            
            # ========================================
            # PASO 8: Generar Adaptive Card
            # ========================================
            logging.info("🎨 Paso 8: Generando Adaptive Card...")
            
            adaptive_card = generate_opportunity_card(
                opportunity_id=opportunity.opportunityid,
                opportunity_name=opportunity.name,
                opportunity_url=opportunity.dynamics_url,
                analysis_data=analysis_result,
                pdf_url=pdf_url
            )
            
            logging.info("✅ Adaptive Card generado")
            
            # ========================================
            # PASO 9: Construir respuesta
            # ========================================
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            response = {
                "success": True,
                "opportunity_id": opportunity.opportunityid,
                "opportunity_name": opportunity.name,
                "opportunity_url": opportunity.dynamics_url,
                "event_type": opportunity.event_type,
                
                "analysis": {
                    "executive_summary": analysis_result.get("executive_summary"),
                    "key_requirements": analysis_result.get("key_requirements", []),
                    "required_towers": required_towers,
                    "team_recommendations": enriched_teams,
                    "overall_risk_level": analysis_result.get("overall_risk_level"),
                    "risks": analysis_result.get("risks", []),
                    "timeline_estimate": analysis_result.get("timeline_estimate"),
                    "effort_estimate": analysis_result.get("effort_estimate"),
                    "recommendations": analysis_result.get("recommendations", []),
                    "next_steps": analysis_result.get("next_steps", []),
                    "clarification_questions": analysis_result.get("clarification_questions", []),
                    "confidence": analysis_result.get("analysis_confidence", 0.0)
                },
                
                "outputs": {
                    "adaptive_card": adaptive_card,
                    "pdf_url": pdf_url,
                    "cosmos_record_id": cosmos_id
                },
                
                "metadata": {
                    "processed_at": datetime.utcnow().isoformat(),
                    "processing_time_seconds": round(processing_time, 2),
                    "model_used": "DeepSeek-R1",
                    "teams_evaluated": len(teams)
                }
            }
            
            logging.info(f"✅ Procesamiento completado en {processing_time:.2f}s")
            return response
            
        except Exception as e:
            logging.error(f"❌ Error procesando oportunidad: {str(e)}")
            import traceback
            logging.error(f"❌ Traceback: {traceback.format_exc()}")
            
            return self._error_response(
                "PROCESSING_ERROR",
                str(e),
                payload.get("opportunityid", "unknown"),
                payload.get("name", "Unknown")
            )
    
    def _enrich_team_recommendations(
        self, 
        ai_recommendations: list, 
        search_results: list
    ) -> list:
        """
        Enriquece las recomendaciones de IA con datos reales de los equipos
        """
        enriched = []
        
        # Crear lookup de equipos por nombre/torre
        teams_lookup = {}
        for team in search_results:
            name = team.get("name", "").upper()
            tower = team.get("tower", "").upper()
            teams_lookup[name] = team
            teams_lookup[tower] = team
        
        for rec in ai_recommendations:
            if not isinstance(rec, dict):
                continue
            
            # Buscar equipo real
            team_name = rec.get("team_name", "").upper()
            tower = rec.get("tower", "").upper()
            
            real_team = teams_lookup.get(team_name) or teams_lookup.get(tower)
            
            if real_team:
                # Usar datos reales del equipo
                enriched.append({
                    "tower": real_team.get("tower", rec.get("tower")),
                    "team_name": real_team.get("name", rec.get("team_name")),
                    "team_lead": real_team.get("leader", rec.get("team_lead", "")),
                    "team_lead_email": real_team.get("leader_email", rec.get("team_lead_email", "")),
                    "relevance_score": rec.get("relevance_score", 0.8),
                    "matched_skills": rec.get("matched_skills", []),
                    "justification": rec.get("justification", ""),
                    "estimated_involvement": rec.get("estimated_involvement", "")
                })
            else:
                # Usar datos de la recomendación de IA
                enriched.append(rec)
        
        return enriched
    
    def _error_response(
        self, 
        code: str, 
        message: str, 
        opportunity_id: str,
        opportunity_name: str
    ) -> Dict[str, Any]:
        """Genera respuesta de error estructurada"""
        return {
            "success": False,
            "opportunity_id": opportunity_id,
            "opportunity_name": opportunity_name,
            "error": {
                "code": code,
                "message": message
            },
            "metadata": {
                "processed_at": datetime.utcnow().isoformat()
            }
        }
