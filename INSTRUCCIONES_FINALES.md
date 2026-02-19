# ✅ CONFIGURACIÓN FINAL - Azure AI Search Production

## 📋 Estado Actual

- ✅ Function App deployada: `func-analyzer-prod`
- ✅ Storage, Cosmos DB, AI Search creados
- ⚠️  **PENDIENTE:** Poblar índice de Azure AI Search con torres

---

## 🔧 PASO 1: Crear Índice y Poblar Torres

### Opción A: PowerShell (Recomendado)
Ejecuta el script que ya está creado:

```powershell
cd c:\Users\DanielGarca\Desktop\agente_analisis_inteligente_prod
.\create_search_index.ps1
```

### Opción B: Python
```powershell
cd c:\Users\DanielGarca\Desktop\agente_analisis_inteligente_prod
python create_index.py
```

### Opción C: Manual via Azure Portal
1. Ve a: https://portal.azure.com
2. Busca: `search-analyzer-prod`
3. Click en "Indexes" → "Add Index"
4. Nombre: `torres-index`
5. Define campos según el schema en `create_search_index.ps1`
6. Importa datos desde `data/torres_nuevas.json`

---

## 🧪 PASO 2: Probar la Función

### Test desde PowerShell:
```powershell
$payload = @{
    opportunityid = "test-prod-001"
    opportunity_description = "Proyecto de desarrollo de IA"
    torres_needed = @("IA", "DATA")
    priority = "high"
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "https://func-analyzer-prod.azurewebsites.net/api/analyze?code=<TU_FUNCTION_KEY>" `
  -Method POST `
  -Body $payload `
  -ContentType "application/json" `
  -TimeoutSec 120
```

### Resultado Esperado:
```json
{
  "statusCode": 200,
  "body": {
    "outputs": {
      "adaptive_card": { ... },
      "pdf_url": "https://..."
    },
    "analysis": { ... },
    "metadata": { ... }
  }
}
```

---

## 📊 URL FINAL PARA POWER AUTOMATE

### Endpoint:
```
https://func-analyzer-prod.azurewebsites.net/api/analyze
```

### API Key (en query string):
```
?code=<TU_FUNCTION_KEY>
```

### URL Completa:
```
https://func-analyzer-prod.azurewebsites.net/api/analyze?code=<TU_FUNCTION_KEY>
```

---

## 🔍 Verificar Índice Creado

### PowerShell:
```powershell
Invoke-RestMethod `
  -Uri "https://search-analyzer-prod.search.windows.net/indexes/torres-index/docs/`$count?api-version=2024-07-01" `
  -Headers @{"api-key"="<TU_SEARCH_KEY>"}
```

Debe retornar: `13` (número de torres)

---

## ⚙️ Configuración Power Automate

### 1. Acción HTTP
- **Método:** POST
- **URI:** `https://func-analyzer-prod.azurewebsites.net/api/analyze?code=<TU_FUNCTION_KEY>`
- **Headers:** `Content-Type: application/json`
- **Body:**
```json
{
  "opportunityid": "@{triggerOutputs()?['body/opportunityid']}",
  "opportunity_description": "@{triggerOutputs()?['body/description']}",
  "torres_needed": ["IA", "DATA"],
  "priority": "high"
}
```

### 2. Parse JSON
- **Content:** `@body('HTTP')`
- **Schema:** (simplificado)
```json
{
  "type": "object",
  "properties": {
    "statusCode": {"type": "integer"},
    "body": {
      "type": "object",
      "properties": {
        "outputs": {
          "type": "object",
          "properties": {
            "adaptive_card": {"type": "object"}
          }
        }
      }
    }
  }
}
```

### 3. Post Adaptive Card
- **Card:** `@{body('Parse_JSON')?['body']?['outputs']?['adaptive_card']}`
- **Recipients:** Mediante loop en `@{body('Parse_JSON')?['body']?['analysis']?['proposed_towers']}`

---

## 📝 Troubleshooting

### Si la función retorna 500:
1. Revisa logs en Azure Portal:
   - Function App → Monitor → Logs
   - Application Insights → Failures

### Si no encuentra torres:
1. Verifica que el índice tiene datos:
```powershell
Invoke-RestMethod `
  -Uri "https://search-analyzer-prod.search.windows.net/indexes/torres-index/docs?api-version=2024-07-01&search=*" `
  -Headers @{"api-key"="<TU_SEARCH_KEY>"}
```

### Si falla Cosmos DB:
1. Verifica que existe la base de datos `opportunity-analysis`
2. Verifica que existe el contenedor `analysis-records`

---

## ✅ Checklist Final

- [ ] Ejecutar `create_search_index.ps1` o `create_index.py`
- [ ] Verificar que índice tiene 13 documentos
- [ ] Probar función con payload de prueba
- [ ] Confirmar respuesta con adaptive_card
- [ ] Configurar Power Automate con URL correcta
- [ ] Probar desde Dynamics 365 end-to-end

---

**🎯 Una vez completados estos pasos, la función estará 100% operativa en producción.**
