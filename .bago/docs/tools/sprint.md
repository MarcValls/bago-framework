# bago sprint — Gestión de sprints

> Crea, visualiza y gestiona sprints de trabajo en formato SPRINT-NNN.json.

## Descripción

`bago sprint` permite organizar el trabajo en sprints con objetivos, fechas y métricas de velocidad. Los sprints se guardan como archivos JSON en `state/sprints/`. Facilita la planificación iterativa y el seguimiento de progreso dentro del framework BAGO.

## Uso

```bash
bago sprint                    → muestra sprint activo (o mensaje si no hay ninguno)
bago sprint new "<nombre>"     → crea nuevo sprint
bago sprint list               → lista todos los sprints
bago sprint close              → cierra el sprint activo
bago sprint --detail           → detalle completo del sprint activo
bago sprint --json             → output JSON del sprint activo
bago sprint --test             → valida dependencias y sale con "OK"
```

## Opciones

| Opción | Descripción |
|--------|-------------|
| `new "<nombre>"` | Crea un nuevo sprint con nombre indicado |
| `list` | Lista todos los sprints (abiertos y cerrados) |
| `close` | Cierra el sprint activo |
| `--detail` | Información detallada del sprint activo |
| `--json` | Output JSON |
| `--test` | Modo test |

## Ejemplos

```bash
# Ver estado del sprint actual
bago sprint

# Crear nuevo sprint
bago sprint new "Sprint 181 — Integración GitHub"

# Ver lista de sprints
bago sprint list

# Cerrar sprint activo
bago sprint close
```

## Casos de uso

- **Cuándo usarlo:** Para organizar el trabajo en ciclos iterativos y tener trazabilidad de qué se hizo en cada período.
- **Qué produce:** Archivos SPRINT-*.json en state/sprints/. Muestra en terminal el estado del sprint con métricas de velocidad.
- **Integración con otros comandos:** `bago velocity` mide la velocidad dentro del sprint. `bago remind` puede vincularse a un sprint. `bago summary` genera resumen del sprint al cerrarlo.
