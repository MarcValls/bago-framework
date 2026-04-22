# bago stats — Dashboard agregado de actividad

> Muestra un dashboard con métricas agregadas y sparklines de actividad del pack.

## Descripción

`bago stats` consolida datos de sesiones, cambios, sprints, goals y actividad temporal en un único dashboard visual. Usa sparklines ASCII para mostrar tendencias. Ideal para una visión de conjunto rápida sin entrar en detalles.

## Uso

```bash
bago stats                     → dashboard completo (todas las secciones)
bago stats --section sessions  → solo sección de sesiones
bago stats --section changes   → solo sección de cambios
bago stats --section sprints   → solo sección de sprints
bago stats --section goals     → solo sección de objetivos
bago stats --section activity  → solo sparkline de actividad
bago stats --json              → output JSON con todas las métricas
bago stats --test              → valida dependencias y sale con "OK"
```

## Opciones

| Opción | Descripción |
|--------|-------------|
| `--section S` | Muestra solo la sección indicada |
| `--json` | Output JSON con todas las métricas |
| `--test` | Modo test |

## Secciones del dashboard

| Sección | Contenido |
|---------|-----------|
| `sessions` | Total, por estado, por workflow más usado |
| `changes` | Total CHGs, por tipo, por severity |
| `sprints` | Sprints activos/cerrados, velocidad media |
| `goals` | Goals por estado, progreso medio |
| `activity` | Sparkline semanal de sesiones por día (últimas 4 semanas) |

## Ejemplos

```bash
# Dashboard completo de un vistazo
bago stats

# Solo actividad reciente
bago stats --section activity

# Exportar métricas para dashboard externo
bago stats --json > stats_snapshot.json
```

## Casos de uso

- **Cuándo usarlo:** Para revisiones rápidas de estado, en reuniones de equipo, o antes de una sesión de planificación.
- **Qué produce:** Dashboard en terminal con tablas, contadores y sparklines ASCII.
- **Integración con otros comandos:** Similar a `bago dashboard` pero más compacto. Para más detalle sobre sesiones específicas usar `bago session-stats`. Para métricas con tendencias usar `bago metrics`.
