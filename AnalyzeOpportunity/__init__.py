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

logging.basicConfig(level=logging.INFO, force=True)


class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder que maneja datetime objects"""
    def default(self, obj):
        try:
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            return super().default(obj)
        except Exception:
            return str(obj)


async def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP Trigger principal para análisis de oportunidades.

    Flujo:
    1. Power Automate detecta nueva oportunidad en Dataverse
    2. Power Automate envía HTTP POST con el body de la oportunidad
    3. Esta función procesa los datos con IA (GPT-4o-mini)
    4. Retorna análisis con Adaptive Card para Teams

    Payload esperado:
    {
        "opportunityid": "guid",
        "name": "Nombre de la oportunidad",
        "description": "...",
        "cr807_descripciondelrequerimientofuncional": "...",
        ... otros campos de Dynamics 365
    },
    "teams_id": "ID del equipo de Teams",
    "channel_id": "ID del canal de Teams"
    """
    logging.info("=" * 60)
    logging.info("🚀 AGENTE DE ANÁLISIS INTELIGENTE - Función iniciada")
    logging.info(f"📍 Python version: {sys.version}")
    logging.info(f"📍 sys.path: {sys.path[:3]}")
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

        # Extraer estructura: body, teams_id, channel_id
        # Soporta ambos formatos:
        # 1. Nuevo: { "body": {...}, "teams_id": "...", "channel_id": "..." }
        # 2. Legacy: { "opportunityid": "...", ... } (todo flat)

        if "body" in payload and isinstance(payload["body"], dict):
            # Nuevo formato estructurado
            opportunity_data = payload["body"]
            teams_id = payload.get("teams_id") or payload.get("teamsId")
            channel_id = payload.get("channel_id") or payload.get("channelId")
            logging.info("📦 Payload estructurado detectado (body + teams_id + channel_id)")
        else:
            # Formato legacy (flat)
            opportunity_data = payload
            teams_id = payload.get("teams_id") or payload.get("teamsId")
            channel_id = payload.get("channel_id") or payload.get("channelId")
            logging.info("📦 Payload flat detectado (legacy)")

        # Agregar teams_id y channel_id al opportunity_data para el orquestador
        opportunity_data["teams_id"] = teams_id
        opportunity_data["channel_id"] = channel_id

        # Validar campos requeridos
        if "opportunityid" not in opportunity_data:
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "error": {
                        "code": "MISSING_OPPORTUNITY_ID",
                        "message": "El payload debe contener 'opportunityid' (dentro de 'body' o directamente)"
                    }
                }),
                status_code=400,
                mimetype="application/json"
            )

        logging.info(f"📥 Oportunidad recibida: {opportunity_data.get('name', 'Sin nombre')}")
        logging.info(f"📥 ID: {opportunity_data.get('opportunityid')}")
        logging.info(f"📥 Evento: {opportunity_data.get('SdkMessage', 'N/A')}")
        logging.info(f"📥 Teams ID: {teams_id or 'N/A'}")
        logging.info(f"📥 Channel ID: {channel_id or 'N/A'}")

        # Importar orquestador de forma perezosa para evitar fallos en tiempo de carga
        logging.info("⚙️ Inicializando orquestador (import perezoso)...")
        try:
            from shared.core.orchestrator import OpportunityOrchestrator
            logging.info("✅ OpportunityOrchestrator importado exitosamente")
        except Exception as e:
            logging.error(f"❌ Error importando OpportunityOrchestrator: {str(e)}")
            import traceback
            tb = traceback.format_exc()
            logging.error(f"❌ Traceback completo:\n{tb}")
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "error": {
                        "code": "IMPORT_ERROR",
                        "message": f"Error cargando componentes del servicio: {str(e)}",
                        "traceback": tb.splitlines()[-20:]
                    },
                    "retry_suggested": False,
                    "metadata": {"processed_at": datetime.utcnow().isoformat()}
                }),
                status_code=200,
                mimetype="application/json",
                charset="utf-8"
            )

        logging.info("🔄 Procesando oportunidad...")
        orchestrator = OpportunityOrchestrator()
        result = await orchestrator.process_opportunity(opportunity_data)

        # Determinar código de respuesta
        # Evitar reintentos automáticos desde Power Automate/consumidores externos
        # cuando el fallo es por falta de configuración de servicios (no es un error transitorio).
        error_code = None
        if isinstance(result, dict) and result.get("error"):
            error_code = result.get("error", {}).get("code")

        if result.get("success", False):
            status_code = 200
        elif error_code == "SERVICE_NOT_CONFIGURED":
            # Devolver 200 con detalle de error para evitar reintentos automáticos
            status_code = 200
            # marcar explícitamente que no se recomiendan reintentos
            result.setdefault("retry_suggested", False)
        else:
            status_code = 500

        logging.info("=" * 60)
        if result.get("success"):
            logging.info("✅ PROCESAMIENTO EXITOSO")
        else:
            logging.error("❌ PROCESAMIENTO FALLIDO")
        logging.info("=" * 60)

        return func.HttpResponse(
            json.dumps(result, cls=DateTimeEncoder, ensure_ascii=False, indent=2),
            status_code=status_code,
            mimetype="application/json",
            charset="utf-8"
        )

    except Exception as e:
        logging.error(f"❌ ERROR CRÍTICO: {str(e)}")
        import traceback
        tb = traceback.format_exc()
        logging.error(f"❌ TRACEBACK: {tb}")

        # Devuelve 200 con el traceback en el cuerpo para facilitar depuración en producción.
        # Nota: parche temporal — eliminar antes de exponer públicamente.
        return func.HttpResponse(
            json.dumps({
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e),
                    "type": type(e).__name__,
                    "traceback": tb.splitlines()[-20:]
                },
                "metadata": {
                    "processed_at": datetime.utcnow().isoformat()
                }
            }),
            status_code=200,
            mimetype="application/json",
            charset="utf-8"
        )
