"""
Servicio para interactuar con Azure Cosmos DB
"""
import os
import logging
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from azure.cosmos.database import DatabaseProxy
from azure.cosmos.container import ContainerProxy

from ..models.cosmos_models import AnalysisRecord, TeamRecommendation, Risk


class CosmosDBService:
    """
    Servicio para guardar y consultar análisis en Cosmos DB
    
    Database: proposal-analysis
    Container: analysis-records
    Partition Key: /work_item_id
    """
    
    def __init__(self, 
                 connection_string: Optional[str] = None,
                 database_name: str = "proposal-analysis",
                 container_name: str = "analysis-records"):
        """
        Inicializa el servicio de Cosmos DB
        
        Args:
            connection_string: Connection string de Cosmos DB (si no se provee, usa variable de entorno)
            database_name: Nombre de la base de datos
            container_name: Nombre del contenedor
        """
        try:
            # Obtener connection string
            self.connection_string = connection_string or os.getenv("AZURE_COSMOS_CONNECTION_STRING")
            
            if not self.connection_string:
                raise ValueError(
                    "❌ AZURE_COSMOS_CONNECTION_STRING no configurado. "
                    "Configura la variable de entorno o pasa connection_string al constructor."
                )
            
            logging.info(f"🔄 Inicializando CosmosClient...")
            logging.info(f"   Database: {database_name}")
            logging.info(f"   Container: {container_name}")
            
            # Inicializar cliente
            self.client = CosmosClient.from_connection_string(self.connection_string)
            self.database_name = database_name
            self.container_name = container_name
            
            # Referencias (se crean bajo demanda)
            self._database: Optional[DatabaseProxy] = None
            self._container: Optional[ContainerProxy] = None
            
            logging.info(f"✅ CosmosDBService inicializado: {database_name}/{container_name}")
            
        except Exception as e:
            logging.error(f"❌ Error inicializando CosmosDBService: {str(e)}")
            raise
    
    @property
    def database(self) -> DatabaseProxy:
        """Obtiene o crea la base de datos"""
        if self._database is None:
            try:
                self._database = self.client.create_database_if_not_exists(id=self.database_name)
                logging.info(f"📊 Base de datos '{self.database_name}' lista")
            except Exception as e:
                logging.error(f"❌ Error accediendo a base de datos: {str(e)}")
                raise
        return self._database
    
    @property
    def container(self) -> ContainerProxy:
        """Obtiene o crea el contenedor"""
        if self._container is None:
            try:
                # Crear contenedor con partition key /work_item_id (serverless, sin throughput)
                self._container = self.database.create_container_if_not_exists(
                    id=self.container_name,
                    partition_key=PartitionKey(path="/work_item_id")
                )
                logging.info(f"📦 Contenedor '{self.container_name}' listo")
            except Exception as e:
                logging.error(f"❌ Error accediendo a contenedor: {str(e)}")
                raise
        return self._container
    
    def save_analysis(self, analysis_data: Dict[str, Any], 
                     work_item_id: int,
                     work_item_url: str,
                     original_description: str,
                     attachments: List[str],
                     extracted_text_length: int,
                     organization: str = "",
                     project: str = "") -> Optional[AnalysisRecord]:
        """
        Guarda un análisis completo en Cosmos DB
        
        Args:
            analysis_data: Datos del análisis (resultado del OpenAI service)
            work_item_id: ID del Work Item
            work_item_url: URL del Work Item
            original_description: Descripción original
            attachments: Lista de nombres de adjuntos
            extracted_text_length: Longitud del texto extraído
            organization: Organización de Azure DevOps
            project: Proyecto de Azure DevOps
            
        Returns:
            AnalysisRecord guardado o None si falla
        """
        try:
            logging.info(f"💾 Guardando análisis en Cosmos DB...")
            
            # Generar ID único
            record_id = str(uuid.uuid4())
            
            # Convertir team_recommendations a modelos Pydantic
            team_recommendations = []
            for team in analysis_data.get("team_recommendations", []):
                team_recommendations.append(TeamRecommendation(**team))
            
            # Convertir risks a modelos Pydantic
            risks = []
            for risk in analysis_data.get("risks", []):
                risks.append(Risk(**risk))
            
            # Crear registro
            record = AnalysisRecord(
                id=record_id,
                work_item_id=work_item_id,
                work_item_url=work_item_url,
                processed_at=datetime.utcnow().isoformat(),
                status="completed",
                
                # Análisis
                executive_summary=analysis_data.get("executive_summary", ""),
                key_points=analysis_data.get("key_points", []),
                technical_assessment=analysis_data.get("technical_assessment"),
                
                # Tecnologías
                technology_stack=analysis_data.get("technology_stack", {}),
                technology_recommendations=analysis_data.get("technology_recommendations", []),
                architecture_suggestions=analysis_data.get("architecture_suggestions", []),
                
                # Torres y equipos
                required_towers=analysis_data.get("required_towers", []),
                team_recommendations=team_recommendations,
                
                # Riesgos
                risks=risks,
                overall_risk_level=analysis_data.get("overall_risk_level", "Medio"),
                
                # Estimaciones
                effort_estimate=analysis_data.get("effort_estimate"),
                
                # Confianza
                analysis_confidence=analysis_data.get("analysis_confidence", 0.0),
                recommendations=analysis_data.get("recommendations", []),
                next_steps=analysis_data.get("next_steps", []),
                
                # Datos originales
                original_description=original_description,
                attachments_processed=attachments,
                extracted_text_length=extracted_text_length,
                
                # Metadata
                organization=organization,
                project=project
            )
            
            # Guardar en Cosmos DB
            item = record.model_dump()
            created_item = self.container.create_item(body=item)
            
            logging.info(f"✅ Análisis guardado en Cosmos DB: {record_id}")
            logging.info(f"   Work Item: {work_item_id}")
            logging.info(f"   Torres: {len(record.required_towers)}")
            logging.info(f"   Equipos: {len(record.team_recommendations)}")
            logging.info(f"   Riesgos: {len(record.risks)}")
            
            return record
            
        except exceptions.CosmosHttpResponseError as e:
            logging.error(f"❌ Error HTTP de Cosmos DB: {e.status_code} - {e.message}")
            return None
        except Exception as e:
            logging.error(f"❌ Error guardando en Cosmos DB: {str(e)}")
            return None
    
    def get_analysis_by_work_item(self, work_item_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene el análisis más reciente para un Work Item
        
        Args:
            work_item_id: ID del Work Item
            
        Returns:
            Diccionario con el análisis o None
        """
        try:
            query = f"SELECT * FROM c WHERE c.work_item_id = {work_item_id} ORDER BY c.created_at DESC"
            items = list(self.container.query_items(
                query=query,
                enable_cross_partition_query=False,
                partition_key=work_item_id
            ))
            
            if items:
                logging.info(f"📊 Análisis encontrado para Work Item {work_item_id}")
                return items[0]  # Más reciente
            else:
                logging.info(f"ℹ️ No se encontró análisis para Work Item {work_item_id}")
                return None
                
        except Exception as e:
            logging.error(f"❌ Error consultando Cosmos DB: {str(e)}")
            return None
    
    def get_recent_analyses(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene los análisis más recientes
        
        Args:
            limit: Número máximo de resultados
            
        Returns:
            Lista de análisis
        """
        try:
            query = f"SELECT * FROM c ORDER BY c.created_at DESC OFFSET 0 LIMIT {limit}"
            items = list(self.container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            logging.info(f"📊 {len(items)} análisis recientes obtenidos")
            return items
            
        except Exception as e:
            logging.error(f"❌ Error consultando análisis recientes: {str(e)}")
            return []
    
    def get_analyses_by_tower(self, tower_name: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Obtiene análisis que requieren una torre específica
        
        Args:
            tower_name: Nombre de la torre (ej: "Torre IA")
            limit: Número máximo de resultados
            
        Returns:
            Lista de análisis
        """
        try:
            query = f"""
            SELECT * FROM c 
            WHERE ARRAY_CONTAINS(c.required_towers, '{tower_name}')
            ORDER BY c.created_at DESC 
            OFFSET 0 LIMIT {limit}
            """
            items = list(self.container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            logging.info(f"📊 {len(items)} análisis encontrados para torre '{tower_name}'")
            return items
            
        except Exception as e:
            logging.error(f"❌ Error consultando por torre: {str(e)}")
            return []
