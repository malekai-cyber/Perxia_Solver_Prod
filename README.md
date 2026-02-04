# 🤖 Agente de Análisis Inteligente

Sistema de análisis automático de oportunidades comerciales usando IA (DeepSeek-R1).

## 📋 Descripción

Este proyecto implementa una Azure Function que recibe oportunidades desde **Microsoft Dynamics 365** (vía Power Automate) y genera análisis inteligentes que incluyen:

- ✅ **Resumen ejecutivo** del requerimiento
- ✅ **Recomendación de equipos/torres** según las habilidades requeridas
- ✅ **Evaluación de riesgos** con mitigaciones
- ✅ **Estimación de esfuerzo** y timeline
- ✅ **Adaptive Card** para Microsoft Teams
- ✅ **PDF** con el análisis completo

## 🏗️ Arquitectura

```
┌─────────────────┐     HTTP POST     ┌──────────────────────┐
│  Power Automate │ ────────────────► │  Azure Function      │
│  (Dataverse     │                   │  AnalyzeOpportunity  │
│   Trigger)      │                   └──────────┬───────────┘
└─────────────────┘                              │
                                                 ▼
                               ┌─────────────────────────────────┐
                               │     OpportunityOrchestrator     │
                               └─────────────────────────────────┘
                                        │
         ┌──────────────────────────────┼──────────────────────────────┐
         │                              │                              │
         ▼                              ▼                              ▼
┌─────────────────┐          ┌──────────────────┐          ┌──────────────────┐
│  Azure OpenAI   │          │  Azure AI Search │          │  Azure Blob      │
│  (DeepSeek-R1)  │          │  (Teams Index)   │          │  Storage (PDFs)  │
└─────────────────┘          └──────────────────┘          └──────────────────┘
         │                              │                              │
         └──────────────────────────────┼──────────────────────────────┘
                                        │
                                        ▼
                               ┌─────────────────────────────────┐
                               │         Response JSON           │
                               │  • Analysis                     │
                               │  • Adaptive Card (Teams)        │
                               │  • PDF URL                      │
                               └─────────────────────────────────┘
```

## 📁 Estructura del Proyecto

```
agente_analisis_inteligente/
├── AnalyzeOpportunity/          # Azure Function principal
│   ├── __init__.py              # Handler HTTP
│   └── function.json            # Configuración del trigger
├── shared/
│   ├── core/
│   │   └── orchestrator.py      # Orquestador principal
│   ├── models/
│   │   ├── opportunity.py       # Modelo de oportunidad (Pydantic)
│   │   └── analysis.py          # Modelos de análisis
│   ├── services/
│   │   ├── openai_service.py    # Cliente Azure OpenAI
│   │   ├── search_service.py    # Cliente Azure AI Search
│   │   ├── blob_storage_service.py  # Cliente Blob Storage
│   │   └── cosmos_service.py    # Cliente Cosmos DB (opcional)
│   └── generators/
│       ├── adaptive_card.py     # Generador de Adaptive Cards
│       └── pdf_generator.py     # Generador de PDFs
├── data/
│   └── teams_data.json          # Datos de equipos/torres
├── host.json                    # Configuración de Azure Functions
├── requirements.txt             # Dependencias Python
├── local.settings.json.example  # Ejemplo de configuración local
└── README.md
```

## ⚙️ Configuración

### 1. Variables de Entorno

Copia `local.settings.json.example` a `local.settings.json` y configura:

```json
{
  "Values": {
    "AZURE_OPENAI_ENDPOINT": "https://your-endpoint.openai.azure.com/",
    "AZURE_OPENAI_KEY": "your-api-key",
    "AZURE_OPENAI_DEPLOYMENT_NAME": "DeepSeek-R1",
    
    "AZURE_SEARCH_ENDPOINT": "https://your-search.search.windows.net",
    "AZURE_SEARCH_KEY": "your-search-key",
    "AZURE_SEARCH_INDEX_TEAMS": "teams-index",
    
    "AZURE_STORAGE_CONNECTION_STRING": "your-storage-connection",
    "AZURE_STORAGE_CONTAINER_NAME": "analysis-pdfs",
    
    "DYNAMICS_ENVIRONMENT_URL": "https://your-org.crm2.dynamics.com"
  }
}
```

### 2. Azure AI Search Index

Sube los datos de equipos a Azure AI Search:

```bash
python upload_teams_data.py
```

### 3. Power Automate

Configura un flujo en Power Automate:

1. **Trigger**: "When a row is added" (Dataverse - Opportunity table)
2. **Action**: HTTP POST a tu Azure Function
3. **Body**: El contenido de la oportunidad

## 🚀 Despliegue

### Despliegue con Azure Functions Core Tools

```bash
# Login en Azure
az login

# Crear Function App (si no existe)
az functionapp create \
  --resource-group tu-resource-group \
  --consumption-plan-location westus2 \
  --runtime python \
  --runtime-version 3.12 \
  --functions-version 4 \
  --name agente-analisis-inteligente \
  --storage-account tu-storage-account

# Desplegar
func azure functionapp publish agente-analisis-inteligente
```

### Configurar Variables en Azure

```bash
az functionapp config appsettings set \
  --name agente-analisis-inteligente \
  --resource-group tu-resource-group \
  --settings \
    AZURE_OPENAI_ENDPOINT="https://..." \
    AZURE_OPENAI_KEY="..." \
    # ... resto de variables
```

## 📨 Uso

### Endpoint

```
POST https://agente-analisis-inteligente.azurewebsites.net/api/analyze
```

### Payload de Ejemplo

```json
{
  "opportunityid": "2f1511d1-0b08-42bc-aeea-62f0f539194b",
  "name": "Implementación de Sistema de IA",
  "description": "El cliente requiere un sistema de inteligencia artificial...",
  "cr807_descripciondelrequerimientofuncional": "Se necesita desarrollar...",
  "estimatedclosedate": "2026-06-30",
  "estimatedvalue": 150000,
  "statecode": 0,
  "SdkMessage": "Create"
}
```

### Respuesta

```json
{
  "success": true,
  "opportunity_id": "2f1511d1-0b08-42bc-aeea-62f0f539194b",
  "opportunity_name": "Implementación de Sistema de IA",
  "analysis": {
    "executive_summary": "...",
    "required_towers": ["Torre IA", "Torre DATA", "Torre FULLSTACK"],
    "team_recommendations": [...],
    "overall_risk_level": "Medio",
    "timeline_estimate": {...},
    "effort_estimate": {...}
  },
  "outputs": {
    "adaptive_card": {...},
    "pdf_url": "https://storage.blob.../analysis.pdf"
  }
}
```

## 🏢 Torres Disponibles

| Torre | Especialidad |
|-------|-------------|
| Torre IA | Machine Learning, NLP, IA Generativa |
| Torre DATA | Data Engineering, BI, Analytics |
| Torre CIBERSEGURIDAD | Security, SOC, Compliance |
| Torre RPA | Automatización, Bots, Workflows |
| Torre FULLSTACK | Web Development, APIs, Microservices |
| Torre QA | Testing, Quality Assurance |
| Torre PMO | Project Management, Agile |
| Torre MOBILE | iOS, Android, React Native |
| Torre SAP | SAP ERP, S/4HANA, ABAP |
| Torre INTEGRACION | APIs, ESB, Middleware |
| Torre PORTALES | CMS, SharePoint, Intranet |
| Torre SOPORTE Y MANTENIMIENTO | IT Support, ITIL |
| Torre DEVOPS | CI/CD, Kubernetes, IaC |

## 🧠 Modelo de IA

Este proyecto utiliza **DeepSeek-R1** desplegado en Azure AI Foundry:

- Modelo de razonamiento avanzado
- Optimizado para análisis técnico
- Soporte para español e inglés

## 📄 Licencia

Uso interno - Todos los derechos reservados.

## 👥 Contribuidores

- Desarrollado por el equipo de IA

---

*Última actualización: Febrero 2026*
