# 🚀 Ambiente de Producción - Agente Análisis Inteligente
**Creado:** 6 febrero 2026  
**Estado:** ✅ OPERACIONAL

---

## 📋 Servicios Desplegados

### Azure Function App
- **Nombre:** `func-analyzer-prod`
- **Endpoint:** `https://func-analyzer-prod.azurewebsites.net`
- **Función:** `AnalyzeOpportunity`
- **URL API:** `https://func-analyzer-prod.azurewebsites.net/api/AnalyzeOpportunity`
- **API Key:** `<CONFIGURAR_EN_AZURE_PORTAL>`
- **Runtime:** Python 3.12
- **Plan:** Consumption (paga por uso)
- **Estado:** ✅ Deployado

### Storage Account
- **Nombre:** `stanalyzersolver`
- **Región:** East US 2
- **SKU:** Standard LRS
- **Contenedor:** `analysis-pdfs`
- **Propósito:** Almacenamiento de PDFs generados
- **Estado:** ✅ Creado

### Cosmos DB (Serverless)
- **Nombre:** `cosmos-analyzer-prod`
- **Región:** East US 2
- **Modo:** Serverless (sin throughput asignado)
- **Base de datos:** `opportunity-analysis`
- **Contenedor:** `analysis-records` (Partition Key: `/userId`)
- **Propósito:** Registros de análisis de oportunidades
- **Estado:** ✅ Creado y configurado

### Azure AI Search
- **Nombre:** `search-analyzer-prod`
- **Región:** East US 2
- **SKU:** Basic
- **Índice:** `torres-index`
- **Propósito:** Búsqueda inteligente de torres/equipos
- **Estado:** ✅ Creado

---

## 🔐 Credenciales & Configuración

### Variables de Entorno (Sincronizadas en Function App)
```
AZURE_OPENAI_ENDPOINT=https://oai-agente-perxia-dev.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2024-10-21

AZURE_SEARCH_ENDPOINT=https://search-analyzer-prod.search.windows.net
AZURE_SEARCH_INDEX_TEAMS=torres-index

AZURE_STORAGE_CONTAINER_NAME=analysis-pdfs

COSMOS_ENDPOINT=https://cosmos-analyzer-prod.documents.azure.com:443/
COSMOS_DATABASE_NAME=opportunity-analysis
COSMOS_CONTAINER_NAME=analysis-records
```

### Claves de Acceso
| Servicio | Clave | Almacenada |
|----------|-------|-----------|
| Storage Account | `<VER_EN_AZURE_PORTAL>` | ✅ Function App |
| Cosmos DB | `<VER_EN_AZURE_PORTAL>` | ✅ Function App |
| AI Search | `<VER_EN_AZURE_PORTAL>` | ✅ Function App |
| Function Key | `<VER_EN_AZURE_PORTAL>` | ✅ Azure Portal |

---

## 💰 Costo Estimado Mensual

| Servicio | Estimado |
|----------|----------|
| Function App (Consumption) | $1-3 |
| Storage Account (Standard LRS) | $1-2 |
| Cosmos DB (Serverless) | $25-30 |
| AI Search (Basic) | $15-20 |
| **TOTAL** | **$42-55/mes** |

---

## 🔗Cómo Invocar la Función

### Con API Key en Query
```bash
curl -X POST https://func-analyzer-prod.azurewebsites.net/api/AnalyzeOpportunity?code=<TU_FUNCTION_KEY> \
  -H "Content-Type: application/json" \
  -d '{
    "opportunity_description": "Descripción de la oportunidad",
    "torres_needed": ["IA", "DATA"],
    "priority": "high"
  }'
```

### Desde Power Automate
1. Agregar acción **HTTP**:
   - **Método:** POST
   - **URL:** `https://func-analyzer-prod.azurewebsites.net/api/AnalyzeOpportunity?code=<TU_FUNCTION_KEY>`
   - **Headers:** `Content-Type: application/json`
   - **Body:** Payload JSON

---

## 📊 Monitoreo & Logs

- **Application Insights:** `func-analyzer-prod` creado automáticamente
- **Acceso:** Azure Portal → Function App → Monitor → Logs
- **Live Metrics:** Disponibles en Azure Portal

---

## 🔄 Próximas Acciones Recomendadas

- [ ] Configurar alertas en Application Insights
- [ ] Crear backup automático de Cosmos DB
- [ ] Implementar Azure Key Vault para secretos
- [ ] Agregar políticas de acceso por rol (RBAC)
- [ ] Establecer procedimiento de rollback
- [ ] Documentar en Azure DevOps

---

## 📂 Archivos de Configuración Local

- `.env` → Variables de entorno (actualizado)
- `local.settings.json` → Settings locales (actualizado)
- `requirements.txt` → Dependencias Python

---

**Grupo de Recursos:** `rg_perxia_solver_prod`  
**Suscripción:** Microsoft Partner Network AI  
**Contacto:** danielgarcia@periferia-it.com
