# bago report — Generador de reportes Markdown

> Genera reportes Markdown filtrados por período, workflow o tipo de cambio.

## Descripción

`bago report` produce informes detallados en formato Markdown sobre la actividad del pack, con soporte para filtros temporales y por tipo. A diferencia de `bago review` (que es un informe completo), `report` es más configurable y orientado a exportar datos para su uso externo.

## Uso

```bash
bago report                    → reporte del período actual (7 días)
bago report --period N         → últimos N días
bago report --workflow WF      → filtra por workflow específico
bago report --type TYPE        → filtra por tipo de cambio
bago report --out FILE         → guarda en archivo
bago report --json             → output JSON
bago report --test             → valida dependencias y sale con "OK"
```

## Opciones

| Opción | Descripción |
|--------|-------------|
| `--period N` | Últimos N días (default: 7) |
| `--workflow WF` | Filtra sesiones por workflow (ej: w7_foco_sesion) |
| `--type TYPE` | Filtra cambios por tipo (feature, fix, docs, etc.) |
| `--out FILE` | Guarda el reporte en el archivo indicado |
| `--json` | Output JSON |
| `--test` | Modo test |

## Ejemplos

```bash
# Reporte semanal estándar
bago report

# Reporte del último mes
bago report --period 30

# Solo sesiones de workflow W7
bago report --workflow w7_foco_sesion

# Guardar reporte mensual en archivo
bago report --period 30 --out REPORTE-ABRIL-2026.md
```

## Casos de uso

- **Cuándo usarlo:** Para generar informes específicos con filtros, antes de presentaciones, o para archivar el estado de un período.
- **Qué produce:** Archivo Markdown o JSON con sesiones, cambios y métricas filtradas.
- **Integración con otros comandos:** Más flexible que `bago review`. Complementa `bago summary` (más ejecutivo). Para análisis visual usar `bago export`.
