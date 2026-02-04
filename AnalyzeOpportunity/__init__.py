"""
Azure Function: AnalyzeOpportunity

Recibe oportunidades desde Power Automate y retorna análisis inteligente.

Endpoint: POST /api/analyze
Payload: Body de oportunidad desde Dataverse

Response:
{
    "success": true,
    "opportunity_id": "...",
    "opportunity_name": "...",
    "analysis": {...},
    "outputs": {
        "adaptive_card": {...},
        "pdf_url": "..."
    }
}
"""

import os
import sys
import json
import logging
from datetime import datetime, date
import azure.functions as func

# Agregar shared al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.core.orchestrator import OpportunityOrchestrator

logging.basicConfig(level=logging.INFO)


class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder que maneja datetime objects"""
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


async def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP Trigger principal para análisis de oportunidades.
    
    Flujo:
    1. Power Automate detecta nueva oportunidad en Dataverse
    2. Power Automate envía HTTP POST con el body de la oportunidad
    3. Esta función procesa los datos con IA (DeepSeek-R1)
    4. Retorna análisis con Adaptive Card para Teams
    
    Payload esperado:
    {
        "opportunityid": "guid",
        "name": "Nombre de la oportunidad",
        "description": "...",
        "cr807_descripciondelrequerimientofuncional": "...",
        ... otros campos de Dynamics 365
    }
    """
    logging.info("=" * 60)
    logging.info("🚀 AGENTE DE ANÁLISIS INTELIGENTE - Función iniciada")
    logging.info("=" * 60)
    
    try:
        # Validar método
        if req.method != "POST":
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "error": {
                        "code": "METHOD_NOT_ALLOWED",
                        "message": "Solo se acepta método POST"
                    }
                }),
                status_code=405,
                mimetype="application/json"
            )
        
        # Obtener payload
        try:
            payload = req.get_json()
        except ValueError as e:
            logging.error(f"❌ Error parseando JSON: {str(e)}")
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "error": {
                        "code": "INVALID_JSON",
                        "message": "El body de la petición no es un JSON válido"
                    }
                }),
                status_code=400,
                mimetype="application/json"
            )
        
        if not payload:
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "error": {
                        "code": "EMPTY_PAYLOAD",
                        "message": "El body de la petición está vacío"
                    }
                }),
                status_code=400,
                mimetype="application/json"
            )
        
        # Validar campos requeridos
        if "opportunityid" not in payload:
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "error": {
                        "code": "MISSING_OPPORTUNITY_ID",
                        "message": "El payload debe contener 'opportunityid'"
                    }
                }),
                status_code=400,
                mimetype="application/json"
            )
        
        logging.info(f"📥 Oportunidad recibida: {payload.get('name', 'Sin nombre')}")
        logging.info(f"📥 ID: {payload.get('opportunityid')}")
        logging.info(f"📥 Evento: {payload.get('SdkMessage', 'N/A')}")
        
        # Crear orquestador y procesar
        logging.info("⚙️ Inicializando orquestador...")
        orchestrator = OpportunityOrchestrator()
        
        logging.info("🔄 Procesando oportunidad...")
        result = await orchestrator.process_opportunity(payload)
        
        # Determinar código de respuesta
        status_code = 200 if result.get("success", False) else 500
        
        logging.info("=" * 60)
        if result.get("success"):
            logging.info("✅ PROCESAMIENTO EXITOSO")
        else:
            logging.error("❌ PROCESAMIENTO FALLIDO")
        logging.info("=" * 60)
        
        return func.HttpResponse(
            json.dumps(result, cls=DateTimeEncoder, ensure_ascii=False, indent=2),
            status_code=status_code,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f"❌ ERROR CRÍTICO: {str(e)}")
        import traceback
        logging.error(f"❌ TRACEBACK: {traceback.format_exc()}")
        
        return func.HttpResponse(
            json.dumps({
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e),
                    "type": type(e).__name__
                },
                "metadata": {
                    "processed_at": datetime.utcnow().isoformat()
                }
            }),
            status_code=500,
            mimetype="application/json"
        )
