"""
Tests unitarios para los modelos del Agente de Análisis Inteligente.

Ejecutar con:
    .venv\\Scripts\\python.exe -m pytest tests/ -v
"""

import pytest
from shared.models.opportunity import OpportunityPayload
from shared.core.orchestrator import OpportunityOrchestrator


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def payload_completo():
    """Payload válido y completo de una oportunidad de Dynamics 365."""
    return {
        "opportunityid": "2f1511d1-0b08-42bc-aeea-62f0f539194b",
        "name": "Implementación Sistema de IA para Automatización",
        "description": "El cliente requiere un sistema de inteligencia artificial.",
        "cr807_descripciondelrequerimientofuncional": "Se necesita desarrollar un pipeline de ML.",
        "estimatedclosedate": "2026-06-30",
        "estimatedvalue": 150000.0,
        "budgetamount": 120000.0,
        "statecode": 0,
        "statuscode": 1,
        "SdkMessage": "Create",
        "customername": "Cliente Ejemplo S.A.",
        "ownername": "Juan Pérez",
    }


@pytest.fixture
def payload_minimo():
    """Payload con solo los campos obligatorios."""
    return {
        "opportunityid": "aaaabbbb-cccc-dddd-eeee-ffffaaaabbbb",
        "name": "Test Mínimo",
    }


@pytest.fixture
def payload_con_html():
    """Payload con HTML en las descripciones."""
    return {
        "opportunityid": "11111111-2222-3333-4444-555555555555",
        "name": "Oportunidad con HTML",
        "description": "<p>Descripción <b>con</b> HTML&nbsp;especial &amp; caracteres.</p>",
        "cr807_descripciondelrequerimientofuncional": "<ul><li>Requerimiento 1</li><li>Rq 2</li></ul>",
    }


# ============================================================
# Tests de OpportunityPayload
# ============================================================

class TestOpportunityPayload:
    """Tests para el modelo Pydantic OpportunityPayload."""

    def test_payload_completo_valido(self, payload_completo):
        """Un payload completo debe instanciarse sin errores."""
        op = OpportunityPayload(**payload_completo)
        assert op.opportunityid == "2f1511d1-0b08-42bc-aeea-62f0f539194b"
        assert op.name == "Implementación Sistema de IA para Automatización"
        assert op.estimatedvalue == 150000.0
        assert op.statecode == 0

    def test_payload_minimo_valido(self, payload_minimo):
        """Los campos opcionales deben tomar None por defecto."""
        op = OpportunityPayload(**payload_minimo)
        assert op.opportunityid == "aaaabbbb-cccc-dddd-eeee-ffffaaaabbbb"
        assert op.name == "Test Mínimo"
        assert op.description is None
        assert op.estimatedvalue is None
        assert op.SdkMessage is None

    def test_campos_obligatorios_faltantes(self):
        """Debe lanzar ValidationError si faltan campos obligatorios."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            OpportunityPayload(name="Solo nombre")  # Falta opportunityid

    def test_extra_campos_permitidos(self, payload_minimo):
        """Campos extra no definidos deben ser aceptados (extra='allow')."""
        payload = {**payload_minimo, "campo_extra": "valor_extra", "otro_campo": 123}
        op = OpportunityPayload(**payload)
        assert op.opportunityid == payload_minimo["opportunityid"]

    def test_state_name_abierta(self, payload_completo):
        """statecode=0 debe retornar 'Abierta'."""
        op = OpportunityPayload(**payload_completo)
        assert op.state_name == "Abierta"

    def test_state_name_ganada(self, payload_completo):
        """statecode=1 debe retornar 'Ganada'."""
        payload = {**payload_completo, "statecode": 1}
        op = OpportunityPayload(**payload)
        assert op.state_name == "Ganada"

    def test_state_name_perdida(self, payload_completo):
        """statecode=2 debe retornar 'Perdida'."""
        payload = {**payload_completo, "statecode": 2}
        op = OpportunityPayload(**payload)
        assert op.state_name == "Perdida"

    def test_state_name_desconocido(self, payload_minimo):
        """statecode no reconocido debe retornar 'Desconocido'."""
        payload = {**payload_minimo, "statecode": 99}
        op = OpportunityPayload(**payload)
        assert op.state_name == "Desconocido"

    def test_event_type_desde_sdk_message(self, payload_completo):
        """event_type debe retornar SdkMessage."""
        op = OpportunityPayload(**payload_completo)
        assert op.event_type == "Create"

    def test_event_type_sin_sdk_message(self, payload_minimo):
        """event_type debe retornar 'Unknown' si SdkMessage es None."""
        op = OpportunityPayload(**payload_minimo)
        assert op.event_type == "Unknown"

    def test_clean_description_con_html(self, payload_con_html):
        """clean_description debe eliminar tags HTML."""
        op = OpportunityPayload(**payload_con_html)
        clean = op.clean_description
        assert "<" not in clean
        assert ">" not in clean
        assert "&nbsp;" not in clean
        assert "&amp;" not in clean
        assert "Requerimiento 1" in clean

    def test_clean_description_prefiere_campo_funcional(self, payload_completo):
        """clean_description debe preferir cr807_descripciondelrequerimientofuncional sobre description."""
        op = OpportunityPayload(**payload_completo)
        clean = op.clean_description
        assert "pipeline de ML" in clean

    def test_clean_description_fallback_a_description(self):
        """Si no hay campo funcional, usa description."""
        op = OpportunityPayload(
            opportunityid="xxx",
            name="Test",
            description="Solo la descripción general",
        )
        assert "Solo la descripción general" in op.clean_description

    def test_clean_description_vacio(self, payload_minimo):
        """Si no hay ninguna descripción, retorna string vacío."""
        op = OpportunityPayload(**payload_minimo)
        assert op.clean_description == ""

    def test_format_for_analysis_contiene_nombre(self, payload_completo):
        """format_for_analysis debe incluir el nombre de la oportunidad."""
        op = OpportunityPayload(**payload_completo)
        texto = op.format_for_analysis()
        assert op.name in texto

    def test_format_for_analysis_contiene_valor(self, payload_completo):
        """format_for_analysis debe incluir el valor estimado."""
        op = OpportunityPayload(**payload_completo)
        texto = op.format_for_analysis()
        assert "150,000.00" in texto

    def test_format_for_analysis_contiene_descripcion_funcional(self, payload_completo):
        """format_for_analysis debe incluir la descripción funcional."""
        op = OpportunityPayload(**payload_completo)
        texto = op.format_for_analysis()
        assert "pipeline de ML" in texto

    def test_format_for_analysis_sin_descripcion(self, payload_minimo):
        """format_for_analysis debe funcionar aunque no haya descripción."""
        op = OpportunityPayload(**payload_minimo)
        texto = op.format_for_analysis()
        assert op.name in texto   # Al menos el nombre debe estar


# ============================================================
# Tests del Orchestrator (lógica interna, sin servicios externos)
# ============================================================

class TestOrchestratorInternos:
    """Tests de los métodos helper del Orchestrator que no usan servicios externos."""

    def test_error_response_estructura(self):
        """_error_response debe retornar el diccionario con la estructura correcta."""
        orch = OpportunityOrchestrator.__new__(OpportunityOrchestrator)
        resp = orch._error_response("TEST_ERROR", "Mensaje de prueba", "opp-123", "Opp Test")

        assert resp["success"] is False
        assert resp["opportunity_id"] == "opp-123"
        assert resp["opportunity_name"] == "Opp Test"
        assert resp["error"]["code"] == "TEST_ERROR"
        assert resp["error"]["message"] == "Mensaje de prueba"
        assert "processed_at" in resp["metadata"]

    def test_enrich_team_recommendations_con_match(self):
        """_enrich_team_recommendations debe enriquecer con datos reales cuando hay match."""
        orch = OpportunityOrchestrator.__new__(OpportunityOrchestrator)

        search_results = [
            {
                "name": "TORRE IA",
                "tower": "Torre IA",
                "leader": "María López",
                "leader_email": "mlopez@empresa.com",
            }
        ]
        ai_recs = [
            {
                "team_name": "TORRE IA",
                "tower": "Torre IA",
                "relevance_score": 0.9,
                "matched_skills": ["ML", "NLP"],
                "justification": "Necesita IA avanzada",
                "estimated_involvement": "Full-time",
            }
        ]

        enriched = orch._enrich_team_recommendations(ai_recs, search_results)

        assert len(enriched) == 1
        assert enriched[0]["team_lead"] == "María López"
        assert enriched[0]["team_lead_email"] == "mlopez@empresa.com"
        assert enriched[0]["relevance_score"] == 0.9

    def test_enrich_team_recommendations_sin_match(self):
        """Si no hay match en search, se usa la recomendación de IA tal como viene."""
        orch = OpportunityOrchestrator.__new__(OpportunityOrchestrator)

        search_results = []
        ai_recs = [
            {
                "team_name": "Torre Desconocida",
                "tower": "Torre X",
                "relevance_score": 0.7,
            }
        ]

        enriched = orch._enrich_team_recommendations(ai_recs, search_results)

        assert len(enriched) == 1
        assert enriched[0]["team_name"] == "Torre Desconocida"

    def test_enrich_ignora_items_no_dict(self):
        """_enrich_team_recommendations debe ignorar ítems que no sean diccionarios."""
        orch = OpportunityOrchestrator.__new__(OpportunityOrchestrator)
        enriched = orch._enrich_team_recommendations(["string", 123, None], [])
        assert enriched == []
