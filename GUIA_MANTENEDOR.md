# 🛠️ Guía para el Mantenedor

> **Documento dirigido a quien tome este proyecto.** Aquí encontrarás todo lo necesario para entender el sistema, levantarlo en local, desplegarlo y operar en producción.
>
> Última actualización: Febrero 2026

---

## 1. Resumen del Sistema

El **Agente de Análisis Inteligente** es una **Azure Function (Python)** que:

1. Recibe una oportunidad comercial desde **Microsoft Dynamics 365** vía **Power Automate**
2. La analiza usando **Azure OpenAI (GPT-4o-mini / DeepSeek-R1)**
3. Busca los equipos/torres más adecuados usando **Azure AI Search**
4. Genera un **PDF** del análisis y lo sube a **Azure Blob Storage**
5. Genera y devuelve una **Adaptive Card** para **Microsoft Teams**
6. (Opcional) Persiste el análisis en **Azure Cosmos DB**

---

## 2. Arquitectura

```
Power Automate (Dynamics 365 trigger)
       |
       | HTTP POST /api/analyze
       ↓
┌──────────────────────────────────────┐
│  Azure Function: AnalyzeOpportunity  │  ← AnalyzeOpportunity/__init__.py
│  (HTTP Trigger, Python 3.12)         │
└──────────────┬───────────────────────┘
               │
               ↓
┌──────────────────────────────────────┐
│       OpportunityOrchestrator        │  ← shared/core/orchestrator.py
│  (coordina todos los servicios)      │
└────┬─────────┬──────────┬────────────┘
     │         │          │          │
     ↓         ↓          ↓          ↓
OpenAI     AI Search  Blob Storage  Cosmos DB
Service    Service    Service       Service
(análisis) (equipos)  (PDFs)        (histórico)
```

### Flujo completo (10 pasos del Orchestrator)

| Paso | Descripción |
|------|-------------|
| 1 | Validar y parsear payload con Pydantic |
| 2 | Preparar texto para IA (`format_for_analysis()`) |
| 3 | Buscar equipos relevantes en Azure AI Search |
| 4 | Analizar con IA → retorna JSON estructurado |
| 5 | Enriquecer recomendaciones con datos reales de equipos |
| 6 | Guardar en Cosmos DB (si está configurado) |
| 7 | Generar PDF y subir a Blob Storage |
| 8 | Generar Adaptive Card para Teams |
| 9 | Extraer líderes de torres únicos |
| 10 | Construir y retornar respuesta JSON |

---

## 3. Estructura del Proyecto

```
agente_analisis_inteligente_prod/
│
├── AnalyzeOpportunity/              # Azure Function principal (HTTP Trigger)
│   ├── __init__.py                  # Handler: recibe HTTP, llama al Orchestrator
│   └── function.json                # Configuración del trigger HTTP
│
├── shared/                          # Código compartido
│   ├── core/
│   │   └── orchestrator.py          # ⭐ Central: coordina todos los servicios
│   ├── models/
│   │   ├── opportunity.py           # Pydantic: modelo del payload de Dynamics
│   │   ├── analysis.py              # Pydantic: modelos de respuesta de análisis
│   │   └── cosmos_models.py         # Pydantic: modelos para Cosmos DB
│   ├── services/
│   │   ├── openai_service.py        # Llama a Azure OpenAI (GPT-4o-mini)
│   │   ├── search_service.py        # Busca equipos en Azure AI Search
│   │   ├── blob_storage_service.py  # Sube PDFs a Azure Blob Storage
│   │   └── cosmos_service.py        # Persiste análisis en Cosmos DB
│   └── generators/
│       ├── adaptive_card.py         # Genera Adaptive Card JSON para Teams
│       └── pdf_generator.py         # Genera PDF usando ReportLab
│
├── data/                            # Datos estáticos de torres/equipos
│   ├── torres_data_prod.json        # ⭐ Datos base de todos los equipos
│   ├── KN_TALLAJE_IA.json           # Tallaje de conocimiento: Torre IA
│   ├── KN_TALLAJE_DATA.json         # Tallaje de conocimiento: Torre DATA
│   ├── KN_TALLAJE_FULLSTACK.json    # Tallaje de conocimiento: Torre FULLSTACK
│   ├── KN_TALLAJE_CIBERSEGURIDAD.json
│   └── KN_TALLAJE_RPA.json
│
├── scripts/
│   ├── setup_search_index.py        # Crear/poblar índice Azure AI Search
│   └── test_connections.py          # Probar conexiones a servicios Azure
│
├── tests/                           # Tests unitarios (pytest)
│   ├── __init__.py
│   └── test_models.py               # Tests de modelos Pydantic
│
├── .flake8                          # Configuración de linter
├── host.json                        # Configuración de Azure Functions
├── local.settings.json.example      # Variables de entorno (plantilla)
├── requirements.txt                 # Dependencias Python
└── *.md                             # Documentación del proyecto
```

---

## 4. Entorno Local (Desarrollo)

### Requisitos previos

| Herramienta | Versión mínima | Instalación |
|-------------|---------------|-------------|
| Python | 3.12 | [python.org](https://python.org) |
| Azure Functions Core Tools | v4 | `npm install -g azure-functions-core-tools@4` |
| Azure CLI | Cualquiera | [docs.microsoft.com/cli/azure/install-azure-cli](https://docs.microsoft.com/cli/azure/install-azure-cli) |
| VS Code + Azure Functions Extension | — | Marketplace de VS Code |

### Pasos

```powershell
# 1. Clonar repositorio
git clone https://github.com/malekai-cyber/Perxia_Solver_Prod.git
cd Perxia_Solver_Prod

# 2. Crear entorno virtual
python -m venv .venv
.venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Copiar y configurar variables de entorno
cp local.settings.json.example local.settings.json
# Editar local.settings.json con tus valores (ver Sección 6)

# 5. Levantar la función localmente
func start
```

La función quedará disponible en:
```
POST http://localhost:7071/api/analyze
```

---

## 5. Variables de Entorno

### Descripción completa

| Variable | Servicio | Descripción | Obligatoria |
|----------|---------|-------------|-------------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI | URL del endpoint (ej: `https://xxx.openai.azure.com/`) | ✅ |
| `AZURE_OPENAI_KEY` | Azure OpenAI | API Key | ✅ |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Azure OpenAI | Nombre del deployment del modelo | ✅ |
| `AZURE_SEARCH_ENDPOINT` | Azure AI Search | URL del servicio (ej: `https://xxx.search.windows.net`) | ✅ |
| `AZURE_SEARCH_KEY` | Azure AI Search | Admin key o query key | ✅ |
| `AZURE_SEARCH_INDEX_TEAMS` | Azure AI Search | Nombre del índice (default: `teams-index`) | ❌ |
| `AZURE_STORAGE_CONNECTION_STRING` | Blob Storage | Connection string completo | ✅ |
| `AZURE_STORAGE_CONTAINER_NAME` | Blob Storage | Nombre del container (default: `analysis-pdfs`) | ❌ |
| `COSMOS_ENDPOINT` | Cosmos DB | URL del endpoint | ❌ |
| `COSMOS_KEY` | Cosmos DB | Primary key | ❌ |
| `COSMOS_DATABASE_NAME` | Cosmos DB | Nombre de la base de datos | ❌ |
| `COSMOS_CONTAINER_NAME` | Cosmos DB | Nombre del container | ❌ |

> **Nota:** Las variables de Cosmos DB son opcionales. Si no se configuran, el sistema funciona sin persistencia histórica.

### Dónde encontrar los valores

1. **Azure Portal** → Recurso de cada servicio → "Keys" o "Connection strings"
2. **Azure CLI:**
   ```bash
   # Azure OpenAI
   az cognitiveservices account keys list --name <nombre> --resource-group <rg>
   # Storage
   az storage account show-connection-string --name <nombre> --resource-group <rg>
   ```

---

## 6. Datos de Equipos / Torres

Los datos de equipos que usa Azure AI Search viven en `data/torres_data_prod.json`.

### Actualizar datos de equipos

Si se agregan torres o cambian integrantes:

1. Editar `data/torres_data_prod.json` con la nueva información
2. Re-poblar el índice de Azure AI Search:
   ```powershell
   .venv\Scripts\python.exe scripts/setup_search_index.py
   ```

### Estructura de un equipo

```json
{
  "id": "torre_ia",
  "tower": "Torre IA",
  "team_name": "Torre IA",
  "team_lead": "Nombre del Líder",
  "team_lead_email": "lider@empresa.com",
  "skills": ["Machine Learning", "NLP", "IA Generativa"],
  "technologies": ["Python", "TensorFlow", "Azure ML"],
  "expertise_areas": ["Computer Vision", "LLMs", "RAG"],
  "frameworks": ["LangChain", "Hugging Face"],
  "description": "Equipo especializado en soluciones de inteligencia artificial..."
}
```

---

## 7. Despliegue en Azure

### Recursos de Azure necesarios

| Recurso | Nombre prod | Propósito |
|---------|-------------|-----------|
| Function App | `func-analyzer-prod` | Ejecutar la función |
| Azure OpenAI | (ver local.settings.json) | Modelo de IA |
| Azure AI Search | `search-analyzer-prod` | Búsqueda de equipos |
| Blob Storage | (ver connection string) | Almacenar PDFs |
| Cosmos DB | (opcional) | Histórico de análisis |

### Desplegar la función

```bash
# Login en Azure
az login

# Desplegar código
func azure functionapp publish func-analyzer-prod

# Actualizar variables de entorno en producción
az functionapp config appsettings set \
  --name func-analyzer-prod \
  --resource-group <tu-resource-group> \
  --settings \
    AZURE_OPENAI_ENDPOINT="https://..." \
    AZURE_OPENAI_KEY="..." \
    AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o-mini" \
    AZURE_SEARCH_ENDPOINT="https://..." \
    AZURE_SEARCH_KEY="..." \
    AZURE_STORAGE_CONNECTION_STRING="..."
```

### URL de producción

```
POST https://func-analyzer-prod.azurewebsites.net/api/analyze?code=<API_KEY>
```

> La API Key se encuentra en: Azure Portal → Function App → `AnalyzeOpportunity` → **Function keys**

---

## 8. Integración con Power Automate

El flujo de Power Automate debe:

1. **Trigger:** "When a row is added, modified or deleted" en Dataverse (tabla `Opportunity`)
2. **Acción HTTP:** POST a la URL de la función con este body:

```json
{
  "body": {
    "opportunityid": "@{triggerBody()?['opportunityid']}",
    "name": "@{triggerBody()?['name']}",
    "description": "@{triggerBody()?['description']}",
    "cr807_descripciondelrequerimientofuncional": "@{triggerBody()?['cr807_descripciondelrequerimientofuncional']}",
    "estimatedclosedate": "@{triggerBody()?['estimatedclosedate']}",
    "estimatedvalue": "@{triggerBody()?['estimatedvalue']}",
    "statecode": "@{triggerBody()?['statecode']}",
    "SdkMessage": "@{triggerOutputs()?['body/SdkMessage']}"
  },
  "teams_id": "<ID del equipo de Teams>",
  "channel_id": "<ID del canal de Teams>"
}
```

3. **Headers:** `Content-Type: application/json`
4. **Autenticación:** Usar la API Key en el query string (`?code=...`)

---

## 9. Monitoreo y Logs

### Azure Portal

- **Application Insights:** Monitoreo de performance, trazas y errores
  - Ir a: Function App → "Application Insights" → "Live Metrics"
- **Logs en tiempo real:**
  ```bash
  func azure functionapp logstream func-analyzer-prod
  ```

### Observar logs locales

La función emite logs estructurados con emojis para facilitar la lectura:
- `🚀` - Inicio de función
- `📥` - Payload recibido
- `🔍` - Búsqueda en AI Search
- `🧠` - Análisis con IA
- `📄` - Generación de PDF
- `💾` - Guardado en Cosmos DB
- `✅` - Paso completado
- `⚠️` - Advertencia (no es error fatal)
- `❌` - Error

### Métricas clave a monitorear

| Métrica | Umbral aceptable | Acción si se supera |
|---------|-----------------|---------------------|
| Tiempo de respuesta | < 30 s | Revisar latencia de OpenAI |
| Tasa de error | < 5 % | Revisar Application Insights |
| Errores de AI Search | 0 | Verificar índice y key |
| Errores de Blob Storage | 0 | Verificar connection string |

---

## 10. Problemas Comunes

### "No se encontraron equipos" en el análisis

**Causa:** El índice de Azure AI Search está vacío o no existe.  
**Solución:**
```powershell
.venv\Scripts\python.exe scripts/setup_search_index.py
# Luego verificar:
.venv\Scripts\python.exe verify_index.py
```

### La función tarda más de 30 segundos

**Causa:** El modelo de IA puede estar bajo carga alta.  
**Solución:** El timeout del trigger HTTP está configurado en `function.json`. Para aumentarlo, editar `host.json`:
```json
{
  "functionTimeout": "00:10:00"
}
```

### Error: "AZURE_OPENAI_ENDPOINT no configurado"

**Causa:** Las variables de entorno no están configuradas.  
**Solución local:** Revisar `local.settings.json`.  
**Solución producción:** `az functionapp config appsettings set ...`

### Error 429 de Azure OpenAI (Rate Limit)

**Causa:** Se han superado las cuotas del modelo.  
**Solución:** En el Azure Portal, ir al recurso de Azure OpenAI → "Manage deployments" → aumentar TPM (tokens per minute).

### El PDF no se genera

**Causa:** Falla al conectar con Blob Storage.  
**Solución:** Verificar `AZURE_STORAGE_CONNECTION_STRING` y que el container exista.  
> **Nota:** Esta falla no aborta el análisis. El resultado se devuelve sin `pdf_url`.

---

## 11. Tests

```powershell
# Correr todos los tests
.venv\Scripts\python.exe -m pytest tests/ -v

# Correr solo tests de modelos
.venv\Scripts\python.exe -m pytest tests/test_models.py -v

# Ver cobertura
.venv\Scripts\python.exe -m pytest tests/ --tb=short
```

Para probar contra la función en producción:
```powershell
.venv\Scripts\python.exe test_production.py
```

---

## 12. Glosario

| Término | Significado |
|---------|-------------|
| Torre | Equipo especializado dentro de la organización (ej: Torre IA, Torre DATA) |
| Líder de torre | Persona responsable de la torre/equipo |
| Adaptive Card | Tarjeta interactiva de Teams con el resumen del análisis |
| Orchestrator | Clase central que coordina todos los servicios para producir el análisis |
| Payload | Datos JSON que Power Automate envía a la función |
| Tallaje | Documento con las habilidades y capacidades de cada torre (`KN_TALLAJE_*.json`) |
| Azure AI Search | Servicio de búsqueda semántica sobre los datos de torres |
| Azure OpenAI | Servicio de IA generativa (aquí usa GPT-4o-mini o DeepSeek-R1) |

---

## 13. Contacto y Soporte

- **Repositorio:** https://github.com/malekai-cyber/Perxia_Solver_Prod
- **Desarrollador original:** Ver `HISTORIAL_DESARROLLO.md`
- Para dudas sobre la infraestructura Azure, revisar el portal en el Resource Group correspondiente.
