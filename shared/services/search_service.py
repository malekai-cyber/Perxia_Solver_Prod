"""
Servicio para Azure AI Search
Búsqueda de equipos y conocimiento organizacional
"""

import os
import logging
from typing import List, Dict, Any
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential


class SearchService:
    """Servicio para Azure AI Search"""

    def __init__(self):
        self.endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.key = os.getenv("AZURE_SEARCH_KEY")
        self.index_name = os.getenv("AZURE_SEARCH_INDEX_TEAMS", "teams-index")

        if not self.endpoint or not self.key:
            raise ValueError("AZURE_SEARCH_ENDPOINT y AZURE_SEARCH_KEY son requeridos")

        self.client = SearchClient(
            endpoint=self.endpoint,
            index_name=self.index_name,
            credential=AzureKeyCredential(self.key)
        )

        logging.info(f"✅ SearchService inicializado: {self.index_name}")

    # -----------------------------------------------------------------------
    # Campos que siempre se seleccionan en las búsquedas
    # -----------------------------------------------------------------------
    _SELECT_FIELDS = [
        "id", "team_name", "tower", "team_lead", "team_lead_email",
        "skills", "expertise_areas", "technologies", "frameworks", "description",
    ]

    def _map_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Convierte un resultado de Azure AI Search al formato interno de equipo."""
        def _as_list(val):
            return val if isinstance(val, list) else []

        return {
            "id": result.get("id", ""),
            "name": result.get("team_name", ""),
            "tower": result.get("tower", ""),
            "leader": result.get("team_lead", ""),
            "leader_email": result.get("team_lead_email", ""),
            "skills": _as_list(result.get("skills")),
            "expertise_areas": _as_list(result.get("expertise_areas")),
            "technologies": _as_list(result.get("technologies")),
            "frameworks": _as_list(result.get("frameworks")),
            "description": result.get("description", ""),
            "search_score": result.get("@search.score", 0.0),
        }

    def search_teams(self, query: str, top: int = 10) -> List[Dict[str, Any]]:
        """
        Busca equipos relevantes basándose en una query.

        Args:
            query: Texto de búsqueda (tecnologías, habilidades, etc.)
            top: Número máximo de resultados.

        Returns:
            Lista de equipos encontrados.
        """
        try:
            logging.info(f"🔍 Buscando equipos para: {query[:100]}...")

            results = self.client.search(
                search_text=query,
                top=top,
                select=self._SELECT_FIELDS,
                include_total_count=True,
            )

            teams = [self._map_result(r) for r in results]
            logging.info(f"✅ {len(teams)} equipos encontrados")
            return teams

        except Exception as e:
            logging.error(f"❌ Error buscando equipos: {str(e)}")
            return []

    def get_all_teams(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los equipos disponibles.

        Returns:
            Lista completa de equipos.
        """
        try:
            logging.info("📋 Obteniendo todos los equipos...")

            results = self.client.search(
                search_text="*",
                select=self._SELECT_FIELDS,
                top=100,
            )

            teams = [self._map_result(r) for r in results]
            logging.info(f"✅ {len(teams)} equipos totales")
            return teams

        except Exception as e:
            logging.error(f"❌ Error obteniendo equipos: {str(e)}")
            return []

    def search_by_skills(self, skills: List[str], top: int = 10) -> List[Dict[str, Any]]:
        """
        Busca equipos que tengan habilidades específicas

        Args:
            skills: Lista de habilidades requeridas
            top: Número máximo de resultados

        Returns:
            Lista de equipos que matchean las habilidades
        """
        # Crear query con las habilidades
        query = " OR ".join(skills)
        return self.search_teams(query, top)
