# 🔍 Reporte de Pruebas - Function App en Producción
**Fecha:** 6 febrero 2026  
**Function:** func-analyzer-prod  
**Estado:** ⚠️ PARCIALMENTE FUNCIONAL

---

## ✅ Lo que FUNCIONA

1. **Despliegue Exitoso**
   - Código desplegado correctamente
   - Function App corriendo en Azure
   - Runtime Python 3.12 activo

2. **Endpoint Accesible**
   - URL correcta: `https://func-analyzer-prod.azurewebsites.net/api/analyze`
   - ⚠️ **NOTA:** Es `/api/analyze` NO `/api/AnalyzeOpportunity`
   - Autenticación con API Key funciona

3. **Validación de Payload**
   - Función valida que `opportunityid` sea requerido
   - Retorna errores descriptivos (400 cuando falta campo)

---

## ❌ Problema Detectado

**Error 500 - Internal Server Error** cuando se envía payload completo.

### Posibles Causas

1. **Variables de Entorno**
   - Alguna clave de Azure (OpenAI, Search, Cosmos, Storage) puede estar incorrecta
   - Verificar App Settings en Azure Portal

2. **Dependencias**
   - Algún módulo Python no se instaló correctamente
   - Verificar requirements.txt

3. **Configuración de Servicios**
   - Cosmos DB puede necesitar inicialización
   - Azure AI Search puede no tener índice creado
   - Storage Container puede no estar accesible

---

## 🔧 Cómo Diagnosticar

### 1. Ver Logs en Azure Portal
```
1. Ir a: https://portal.azure.com
2. Buscar: func-analyzer-prod
3. Click: Monitor → Logs
4. Query: traces | where timestamp > ago(30m) | order by timestamp desc
```

### 2. Ver Application Insights
```
1. Ir a Resource Group: rg_perxia_solver_prod
2. Click: Application Insights → func-analyzer-prod
3. Ver: Failures → Exceptions
```

### 3. Verificar App Settings
```powershell
az functionapp config appsettings list --name func-analyzer-prod --resource-group rg_perxia_solver_prod -o table
```

---

## 📋 Payload de Prueba

### Payload Mínimo (para testing)
```json
{
  "opportunityid": "test-001",
  "opportunity_description": "Proyecto de prueba",
  "torres_needed": ["IA"],
  "priority": "high"
}
```

### Payload Completo (producción)
```json
{
  "opportunityid": "guid-from-dynamics",
  "opportunity_description": "Descripción detallada",
  "torres_needed": ["IA", "DATA", "FULLSTACK"],
  "priority": "high",
  "client_name": "Nombre Cliente",
  "estimated_budget": 50000
}
```

---

## 🧪 Comando de Prueba

### PowerShell
```powershell
$payload = '{"opportunityid":"test-001","opportunity_description":"Test","torres_needed":["IA"],"priority":"high"}'

Invoke-RestMethod `
  -Uri "https://func-analyzer-prod.azurewebsites.net/api/analyze?code=<TU_FUNCTION_KEY>" `
  -Method POST `
  -Body $payload `
  -ContentType "application/json" `
  -TimeoutSec 120
```

### cURL (Windows)
```bash
curl.exe -X POST ^
  "https://func-analyzer-prod.azurewebsites.net/api/analyze?code=<TU_FUNCTION_KEY>" ^
  -H "Content-Type: application/json" ^
  -d "{\"opportunityid\":\"test-001\",\"opportunity_description\":\"Test\",\"torres_needed\":[\"IA\"],\"priority\":\"high\"}"
```

---

## 🛠️ Próximos Pasos para Resolver

1. **Revisar Logs en Azure Portal** (más urgente)
2. **Verificar que todos los servicios estén creados:**
   - Cosmos DB: Base de datos `opportunity-analysis` existe
   - Cosmos DB: Contenedor `analysis-records` existe
   - Storage: Contenedor `analysis-pdfs` existe
   - AI Search: Índice `torres-index` existe

3. **Posible solución rápida:**
   - Crear el índice de AI Search manualmente
   - Poblar datos de torres
   - Re-deploy con mejor manejo de errores

---

## 📊 Estado de Servicios

| Servicio | Creado | Configurado | Funcional |
|----------|--------|-------------|-----------|
| Function App | ✅ | ✅ | ⚠️ (Error 500) |
| Storage Account | ✅ | ✅ | ❓ Sin probar |
| Cosmos DB | ✅ | ✅ | ❓ Sin probar |
| AI Search | ✅ | ❌ | ❓ Índice vacío |
| App Insights | ✅ | ✅ | ✅ Logs activos |

---

## 💡 Recomendación Inmediata

**Opción 1: Debugging en Azure Portal**
- Ver logs en tiempo real
- Identificar error específico
- Corregir configuración faltante

**Opción 2: Test Local Primero**
- Probar función localmente: `func start`
- Asegurar que funciona 100%
- Luego re-deploy a Azure

**Opción 3: Crear Índice de Search**
Es probable que el error sea que el índice `torres-index` no tiene datos.
Necesitamos correr el script `setup_search_index.py`

---

**URL Correcta para Power Automate:**
```
https://func-analyzer-prod.azurewebsites.net/api/analyze?code=<TU_FUNCTION_KEY>
```

⚠️ **IMPORTANTE:** Falta inicializar el índice de Azure AI Search con los datos de torres.
