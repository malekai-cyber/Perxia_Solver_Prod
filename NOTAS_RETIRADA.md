# 📋 Notas de Retirada y Traspaso del Proyecto

> **Documento de traspaso** — Preparado por el desarrollador original al momento del retiro.
> Fecha: Febrero 2026

---

## Estado Actual del Proyecto

### ✅ Completado y funcionando en producción

| Componente | Estado | Notas |
|-----------|--------|-------|
| Azure Function `AnalyzeOpportunity` | ✅ Deployada | `func-analyzer-prod.azurewebsites.net` |
| Azure AI Search | ✅ Índice creado y cargado | `search-analyzer-prod` |
| Azure Blob Storage | ✅ Operativo | Container `analysis-pdfs` |
| Azure OpenAI | ✅ Operativo | Deployment `gpt-4o-mini` (o DeepSeek-R1) |
| Cosmos DB | ✅ Configurado | Persistencia de análisis (opcional) |
| Integración Power Automate | ✅ Configurada | Trigger en Dynamics 365 Opportunities |
| Adaptive Card para Teams | ✅ Funcionando | Se genera y devuelve en cada análisis |
| Generación de PDF | ✅ Funcionando | Se sube automáticamente a Blob Storage |

---

## Decisiones de Diseño Importantes

### ¿Por qué Azure Functions y no un servidor tradicional?

- **Costo:** Se paga solo cuando se ejecuta (modelo serverless); las oportunidades no llegan de forma continua.
- **Escalabilidad automática:** Azure Functions escala automáticamente si hay pico de oportunidades.
- **Sin mantenimiento de servidor:** No hay que gestionar VMs ni contenedores.

### ¿Por qué GPT-4o-mini y no un modelo mayor?

- Excelente relación costo/calidad para análisis estructurado en español.
- Responde en JSON bien formateado de manera consistente.
- Tokens más baratos que GPT-4o o GPT-4 Turbo.
- Si se necesita más calidad, se puede cambiar `AZURE_OPENAI_DEPLOYMENT_NAME` a `gpt-4o`.

### ¿Por qué Azure AI Search para los equipos?

- Permite búsqueda semántica: una oportunidad sobre "automatización de procesos" encuentra la "Torre RPA" incluso sin coincidir exactamente.
- Los datos de equipos son pocos (< 20 torres) pero la búsqueda semántica mejora mucho la relevancia.
- Si se quiere eliminar la dependencia de AI Search, se puede cambiar `SearchService.get_all_teams()` para leer directamente de `data/torres_data_prod.json`.

### ¿Por qué Cosmos DB es opcional?

- Se agregó como historial pero no es crítico para el funcionamiento.
- Si Cosmos DB falla, el análisis se sigue devolviendo correctamente (degradación elegante).
- En el futuro podría usarse para: reportes, auditoría, reentrenamiento del modelo.

### Formato dual del payload

La función acepta dos formatos:
1. **Nuevo (estructurado):** `{ "body": {...}, "teams_id": "...", "channel_id": "..." }` — recomendado
2. **Legacy (flat):** `{ "opportunityid": "...", ... }` — para compatibilidad con versiones anteriores

No romper la compatibilidad con el formato legacy hasta que todos los flujos de Power Automate estén migrados.

---

## Lo que NO se hizo (Deuda Técnica)

| Item | Prioridad | Descripción |
|------|-----------|-------------|
| ❌ Autenticación con Managed Identity | Media | Actualmente usa API Keys, se debería migrar a Azure Managed Identity para mejor seguridad |
| ❌ Tests de integración | Media | Solo hay tests unitarios de modelos; no hay tests E2E automatizados |
| ❌ CI/CD pipeline | Media | No hay pipeline de GitHub Actions/Azure DevOps para deployment automático |
| ❌ Envío directo a Teams | Baja | La Adaptive Card se retorna a Power Automate pero no se envía directamente a Teams desde la función |
| ❌ Caché de equipos | Baja | En cada request se llama a AI Search; se podría cachear los resultados por N minutos |
| ❌ Versionado del índice de Search | Baja | Si se actualiza la estructura del índice, hay que borrarlo y recrearlo manualmente |
| ❌ Rate limiting | Baja | No hay protección contra llamadas masivas a la función |

---

## Archivos Importantes que NO deben eliminarse

| Archivo | Por qué es crítico |
|---------|-------------------|
| `data/torres_data_prod.json` | Fuente de verdad de todos los equipos; si se borra se pierden los datos del índice |
| `local.settings.json` | Configuración local (no está en git por seguridad; si se pierde, recrear desde `.example`) |
| `scripts/setup_search_index.py` | Único script para recrear/actualizar el índice de AI Search |
| `AnalyzeOpportunity/__init__.py` | Punto de entrada de la Azure Function |
| `shared/core/orchestrator.py` | Cerebro del sistema; contiene toda la lógica de orquestación |

---

## Archivos que se pueden limpiar (no son críticos)

Los siguientes archivos son artefactos de desarrollo y pueden archivarse o eliminarse:

- `AMBIENTE_PROD.md` / `AMBIENTE_PRODUCCION.md` — Notas de setup inicial (ya completado)
- `INSTRUCCIONES_FINALES.md` — Instrucciones de primer despliegue (ya ejecutadas)
- `PRUEBAS_PRODUCCION.md` — Notas de pruebas iniciales
- `test_*.json` — Payloads de prueba
- `*.ps1` (scripts PowerShell) — Solo se usaron para el setup inicial
- `create_index*.py` / `check_and_create_index.py` — Scripts de setup de índice (reemplazados por `scripts/setup_search_index.py`)

---

## Credenciales y Accesos

> ⚠️ **IMPORTANTE:** Todas las claves y credenciales deben transferirse de forma segura a través del canal establecido por el equipo. **Nunca compartir por email o Teams en texto plano.**

Los accesos necesarios para operar el sistema son:

1. **Azure Portal** — Acceso al Resource Group del proyecto
2. **GitHub** — Repositorio `malekai-cyber/Perxia_Solver_Prod`
3. **local.settings.json** — Archivo con todas las claves (no está en git)

---

## Cómo actualizar el modelo de IA

Si se necesita cambiar el modelo (ej: de GPT-4o-mini a GPT-4o):

1. En Azure Portal, crear un nuevo deployment en el recurso de Azure OpenAI
2. Actualizar la variable `AZURE_OPENAI_DEPLOYMENT_NAME` en la Function App:
   ```bash
   az functionapp config appsettings set \
     --name func-analyzer-prod \
     --resource-group <rg> \
     --settings AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o"
   ```
3. El prompt de análisis está en `shared/services/openai_service.py` (método `analyze_opportunity`); ajustar si el nuevo modelo requiere cambios.

---

## Cómo agregar una nueva Torre

1. Agregar la entrada en `data/torres_data_prod.json`
2. Re-ejecutar el script de setup:
   ```powershell
   .venv\Scripts\python.exe scripts/setup_search_index.py
   ```
3. Verificar que la torre aparece en el índice:
   ```powershell
   .venv\Scripts\python.exe verify_index.py
   ```

---

## Contacto del Desarrollador Original

Este proyecto fue desarrollado internamente. Para contexto adicional sobre decisiones de diseño, revisar:
- `HISTORIAL_DESARROLLO.md` — Historial completo de cambios y decisiones
- Commits del repositorio en GitHub

---

*Gracias por continuar este proyecto. Cualquier mejora o corrección bienvenida.*
