# Perxia Solver — Análisis Inteligente de Oportunidades

Azure Function que recibe oportunidades comerciales desde **Dynamics 365 / Power Automate**
y genera automáticamente: resumen ejecutivo, recomendación de torres/equipos, evaluación de
riesgos, estimación de esfuerzo, Adaptive Card (Teams) y PDF.

---

## Arquitectura

```
Power Automate (Dataverse trigger)
       │  HTTP POST
       ▼
 AnalyzeOpportunity (Azure Function)
       │
       ▼
 OpportunityOrchestrator
       ├── OpenAI Service  ─► Azure OpenAI (GPT-4o-mini)
       ├── Search Service  ─► Azure AI Search (torres-index)
       ├── Blob Service    ─► Azure Blob Storage (PDFs)
       ├── Cosmos Service  ─► Azure Cosmos DB (historial, opcional)
       ├── Adaptive Card Generator
       └── PDF Generator (ReportLab)
```

## Estructura del Proyecto

```
├── AnalyzeOpportunity/           # Azure Function
│   ├── __init__.py               #   HTTP handler (entry point)
│   └── function.json             #   Trigger config: POST /api/analyze
├── shared/
│   ├── core/
│   │   └── orchestrator.py       # Orquestación de 10 pasos
│   ├── services/
│   │   ├── openai_service.py     # Cliente Azure OpenAI
│   │   ├── search_service.py     # Cliente Azure AI Search
│   │   ├── blob_storage_service.py
│   │   └── cosmos_service.py     # Opcional (fallo graceful)
│   ├── generators/
│   │   ├── adaptive_card.py      # JSON Adaptive Card para Teams
│   │   └── pdf_generator.py      # PDF con ReportLab
│   └── models/
│       ├── opportunity.py        # Pydantic: OpportunityPayload
│       ├── analysis.py           # Pydantic: modelos de análisis
│       └── cosmos_models.py      # Pydantic: registros Cosmos DB
├── tests/
│   └── test_models.py            # 22 tests unitarios (pytest)
├── scripts/
│   └── setup_search_index.py     # Crea/pobla el índice de AI Search
├── data/
│   └── torres_data_prod.json     # Datos de referencia para el índice
├── .github/workflows/
│   └── master_function-analyzer-perxia-solver.yml  # CI/CD
├── host.json                     # Timeout 10 min, logging
├── requirements.txt              # Dependencias Python 3.13
├── local.settings.json.example   # Plantilla de variables de entorno
├── .gitignore
├── .funcignore
└── .flake8                       # Linter config (max-line-length=120)
```

## Variables de Entorno

Copiar `local.settings.json.example` → `local.settings.json` y completar:

| Variable | Descripción |
|----------|-------------|
| `AZURE_OPENAI_ENDPOINT` | Endpoint de Azure OpenAI |
| `AZURE_OPENAI_KEY` | API Key de Azure OpenAI |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Nombre del deployment (`gpt-4o-mini`) |
| `AZURE_OPENAI_API_VERSION` | Versión de API (`2024-10-21`) |
| `AZURE_SEARCH_ENDPOINT` | Endpoint de Azure AI Search |
| `AZURE_SEARCH_KEY` | API Key de Azure AI Search |
| `AZURE_SEARCH_INDEX_TEAMS` | Nombre del índice (`torres-index`) |
| `AZURE_STORAGE_CONNECTION_STRING` | Connection string de Storage Account |
| `AZURE_STORAGE_CONTAINER_NAME` | Contenedor para PDFs (`analysis-pdfs`) |
| `COSMOS_ENDPOINT` | Endpoint de Cosmos DB |
| `COSMOS_KEY` | Clave de Cosmos DB |
| `COSMOS_DATABASE_NAME` | Base de datos (`opportunity-analysis`) |
| `COSMOS_CONTAINER_NAME` | Contenedor (`analysis-records`) |

Estas mismas variables están configuradas en el Application Settings de la Function App en Azure.

## Desarrollo Local

```bash
# 1. Crear entorno virtual
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux/Mac

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar local.settings.json (copiar del ejemplo)

# 4. Ejecutar
func start
```

## Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

Los tests validan los modelos Pydantic y la lógica interna del orquestador sin
necesidad de conexión a servicios de Azure.

## Despliegue (CI/CD)

El repositorio usa **GitHub Actions** con autenticación OIDC hacia Azure.

**Workflow:** `.github/workflows/master_function-analyzer-perxia-solver.yml`

- **Trigger:** push a `master` o `main`
- **Build:** instala dependencias → ejecuta tests (pytest) → ejecuta linter (flake8)
- **Deploy:** login OIDC → deploy a Function App `function-analyzer-perxia-solver`

### Secrets requeridos en GitHub (Settings → Secrets → Actions)

| Secret | Valor |
|--------|-------|
| `AZUREAPPSERVICE_CLIENTID_5AA8D66009A24BACA827205041709E4D` | Client ID del Service Principal |
| `AZUREAPPSERVICE_TENANTID_92A8CA850E884A1D86EA714E35846371` | Tenant ID de Azure AD |
| `AZUREAPPSERVICE_SUBSCRIPTIONID_6783E925E1604ECC8364CE6D80B09918` | Subscription ID de Azure |

Estos valores se obtienen del App Registration configurado para OIDC en Azure Portal.

## Endpoint de Producción

```
POST https://func-analyzer-prod.azurewebsites.net/api/analyze?code=<FUNCTION_KEY>
Content-Type: application/json
```

La Function Key se obtiene en Azure Portal → Function App → Functions → App Keys.

### Payload de ejemplo

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
  "opportunity_id": "...",
  "opportunity_name": "...",
  "analysis": {
    "executive_summary": "...",
    "required_towers": ["Torre IA", "Torre DATA"],
    "team_recommendations": [...],
    "overall_risk_level": "Medio",
    "timeline_estimate": {...},
    "effort_estimate": {...}
  },
  "outputs": {
    "adaptive_card": {...},
    "pdf_url": "https://..."
  }
}
```

### Integración con Power Automate

1. Acción **HTTP** → Método `POST`
2. URI: `https://func-analyzer-prod.azurewebsites.net/api/analyze?code=<FUNCTION_KEY>`
3. Header: `Content-Type: application/json`
4. Body: JSON con los campos de la oportunidad de Dataverse

## Torres Disponibles

| Torre | Especialidad |
|-------|-------------|
| IA | Machine Learning, NLP, IA Generativa |
| DATA | Data Engineering, BI, Analytics |
| CIBERSEGURIDAD | Security, SOC, Compliance |
| RPA | Automatización, Bots, Workflows |
| FULLSTACK | Web, APIs, Microservicios |
| QA | Testing, Quality Assurance |
| PMO | Project Management, Agile |
| MOBILE | iOS, Android, React Native |
| SAP | SAP ERP, S/4HANA, ABAP |
| INTEGRACION | APIs, ESB, Middleware |
| PORTALES | CMS, SharePoint, Intranet |
| SOPORTE Y MANTENIMIENTO | IT Support, ITIL |
| DEVOPS | CI/CD, Kubernetes, IaC |

## Recrear el Índice de Azure AI Search

Si es necesario recrear el índice `torres-index`:

```bash
# Configurar la variable de entorno con la clave admin de AI Search
$env:AZURE_SEARCH_ADMIN_KEY = "<tu-clave>"    # PowerShell
export AZURE_SEARCH_ADMIN_KEY="<tu-clave>"     # Bash

python scripts/setup_search_index.py
```

Los datos de las torres están en `data/torres_data_prod.json`.

## Servicios de Azure en Producción

| Servicio | Recurso | Región |
|----------|---------|--------|
| Function App | `function-analyzer-perxia-solver` | — |
| Azure OpenAI | `oai-agente-perxia-dev` (GPT-4o-mini) | — |
| AI Search | `search-analyzer-prod` (Basic) | East US 2 |
| Storage Account | `stanalyzersolver` (Standard LRS) | East US 2 |
| Cosmos DB | `cosmos-analyzer-prod` (Serverless) | East US 2 |
| Resource Group | `rg_perxia_solver_prod` | — |

## Notas Técnicas

- **Timeout:** 10 minutos configurados en `host.json` — el análisis con GPT-4o-mini tarda ~15-45 segundos.
- **Cosmos DB es opcional:** si el servicio no está disponible, el orquestador continúa sin guardar historial.
- **Partition Key de Cosmos:** `/userId` en el contenedor `analysis-records`.
- **Formato del payload:** la función acepta tanto el formato estructurado (con `opportunityid`, `name`, etc.) como un formato legacy con campos anidados. Ver `OpportunityPayload` en `shared/models/opportunity.py`.

---

*Última actualización: Febrero 2026*
