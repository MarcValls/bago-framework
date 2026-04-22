# bago review — Informe de revisión periódica

> Genera un informe Markdown consolidado de sesiones, cambios, insights y hábitos.

## Descripción

`bago review` produce un informe de revisión completo en Markdown para un período de tiempo determinado. Consolida sesiones realizadas, cambios registrados, insights detectados y hábitos observados. Útil para revisiones semanales, mensuales o retrospectivas de sprint.

## Uso

```bash
bago review                    → revisión semanal (últimos 7 días)
bago review --period monthly   → revisión mensual (últimos 30 días)
bago review --period N         → últimos N días
bago review --out FILE         → guarda el informe en FILE
bago review --json             → output JSON estructurado
bago review --test             → valida dependencias y sale con "OK"
```

## Opciones

| Opción | Descripción |
|--------|-------------|
| `--period monthly` | Período mensual (30 días) |
| `--period N` | Últimos N días |
| `--out FILE` | Guarda el informe en el archivo indicado |
| `--json` | Output JSON con secciones del informe |
| `--test` | Modo test |

## Secciones del informe

1. **Resumen ejecutivo** — sesiones, cambios, decisiones del período
2. **Sesiones activas** — listado con workflow, artefactos, estado
3. **Cambios registrados** — CHGs del período con descripción y severity
4. **Insights del período** — resumen de `bago insights`
5. **Hábitos observados** — resumen de `bago habit`
6. **Recordatorios vencidos** — si los hay
7. **Próximos pasos sugeridos** — basados en el análisis

## Ejemplos

```bash
# Revisión semanal rápida
bago review

# Revisión mensual guardada en archivo
bago review --period monthly --out REVIEW-2026-04.md

# Revisión de los últimos 14 días
bago review --period 14

# Exportar para procesado externo
bago review --json | jq '.summary'
```

## Casos de uso

- **Cuándo usarlo:** Al final de cada semana o sprint, antes de una reunión de planificación, o en retrospectivas.
- **Qué produce:** Informe Markdown listo para leer o compartir, o JSON con todas las secciones.
- **Integración con otros comandos:** Combina `bago insights`, `bago habit`, `bago stats` y `bago remind` en un único informe. Complementa `bago summary` (más ejecutivo) y `bago report` (más filtrable).
