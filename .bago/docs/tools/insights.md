# bago insights — Motor de insights automáticos

> Analiza el estado del pack y genera insights priorizados en 5 categorías.

## Descripción

`bago insights` procesa las sesiones, cambios y sprints registrados en state/ para generar observaciones automáticas sobre el trabajo. Devuelve hasta N insights organizados por categoría y prioridad. Útil para obtener una visión rápida de qué está pasando en el proyecto sin revisar manualmente el estado.

## Uso

```bash
bago insights                  → todos los insights (5 categorías)
bago insights --cat CAT        → solo categoría específica
bago insights --top N          → top N insights por prioridad
bago insights --json           → output JSON estructurado
bago insights --test           → valida dependencias y sale
```

## Opciones

| Opción | Descripción |
|--------|-------------|
| `--cat CAT` | Filtra por categoría: PRODUCCION, PATRON, RIESGO, TENDENCIA, RECOMENDACION |
| `--top N` | Muestra solo los N insights de mayor prioridad |
| `--json` | Output JSON estructurado |
| `--test` | Modo test: valida que state/ existe y sale con "OK" |

## Categorías

| Categoría | Descripción |
|-----------|-------------|
| `PRODUCCION` | Métricas de producción: sesiones, artefactos, decisiones |
| `PATRON` | Patrones de comportamiento detectados en las sesiones |
| `RIESGO` | Alertas sobre stale, health bajo, falta de actividad |
| `TENDENCIA` | Evolución temporal: subida, bajada, estabilidad |
| `RECOMENDACION` | Acciones sugeridas basadas en el análisis |

## Ejemplos

```bash
# Ver todos los insights disponibles
bago insights

# Solo riesgos detectados
bago insights --cat RIESGO

# Top 3 más prioritarios
bago insights --top 3

# Exportar para procesado externo
bago insights --json | jq '.insights[] | select(.priority == "high")'
```

## Casos de uso

- **Cuándo usarlo:** Al inicio de una sesión para obtener contexto rápido, o después de un período sin actividad.
- **Qué produce:** Lista de insights en texto legible o JSON con campos: id, category, priority, title, description.
- **Integración con otros comandos:** Complementa `bago health` (estado numérico) y `bago review` (informe completo). Los insights de categoría RIESGO son los mismos que aparecen en `bago doctor`.
