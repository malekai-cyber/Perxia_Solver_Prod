# Ambiente: PRODUCCIÓN

Este proyecto está configurado para ambiente de **PRODUCCIÓN**.

## Características:
- 🚀 Configuración productiva
- 📊 Logs controlados
- ⚙️ Recursos reales de PRODUCCIÓN
- 🔒 Acceso restringido y auditoría

## Recursos Asociados:
- **Azure Function**: `function-analyzer-perxia-solver` (Flex Consumption - PROD)
- **AI Search**: Índice de producción
- **Cosmos DB**: Base de datos de producción
- **Blob Storage**: Contenedor de producción
- **Power Automate**: Flujos de producción

## Archivos de Configuración:
- `.env` - Variables de entorno para PROD (claves y endpoints reales)
- `local.settings.json` - Configuración de producción

## Importante:
⚠️ **NO MODIFICAR SIN AUTORIZACIÓN**
- Los cambios aquí impactan directamente a usuarios finales
- Requiere testing previo en ambiente de DESARROLLO
- Versión de desarrollo disponible en: `agente_analisis_inteligente` (DEV)

## Procedimiento de Actualización:
1. Hacer cambios en DEV y validar
2. Probar en ambiente de staging
3. Solicitar aprobación
4. Actualizar PROD con cambios validados

---
**Fecha de creación**: 2026-02-06
**Propósito**: Ambiente productivo - Análisis inteligente de oportunidades
