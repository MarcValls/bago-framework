# bago remind — Recordatorios con due-date

> Gestiona recordatorios vinculables a sprints, guardados en state/reminders/.

## Descripción

`bago remind` permite crear recordatorios con fecha límite y referencia a sprint. Los recordatorios se guardan como `REM-*.json` en `state/reminders/`. Al ejecutar `bago remind` sin argumentos se muestran los pendientes y vencidos. Útil para no olvidar acciones que deben hacerse en fechas concretas.

## Uso

```bash
bago remind                             → muestra pendientes y vencidos
bago remind add "<texto>"               → crea recordatorio
bago remind add "<texto>" --due YYYY-MM-DD  → con fecha límite
bago remind add "<texto>" --sprint ID   → vinculado a sprint
bago remind done <REM-ID>               → marca como completado
bago remind list                        → lista activos
bago remind list --all                  → lista todos (incluye completados)
bago remind --test                      → valida dependencias y sale con "OK"
```

## Opciones

| Opción | Descripción |
|--------|-------------|
| `add "<texto>"` | Crea un nuevo recordatorio |
| `--due YYYY-MM-DD` | Fecha límite del recordatorio |
| `--sprint ID` | Vincula al sprint indicado (ej: SPRINT-004) |
| `done <ID>` | Marca el recordatorio como completado |
| `list` | Lista recordatorios activos |
| `--all` | Incluye completados en el listado |
| `--test` | Modo test |

## Ejemplos

```bash
# Ver recordatorios pendientes y vencidos
bago remind

# Crear recordatorio simple
bago remind add "Revisar health antes del sprint review"

# Recordatorio con fecha límite
bago remind add "Actualizar CHANGELOG.md" --due 2026-04-30

# Recordatorio vinculado a sprint
bago remind add "Demo final Sprint 180" --due 2026-04-25 --sprint SPRINT-004

# Marcar como hecho
bago remind done REM-001

# Ver historial completo
bago remind list --all
```

## Casos de uso

- **Cuándo usarlo:** Para recordar acciones futuras concretas sin interrumpir el flujo de trabajo actual. Especialmente útil antes de cerrar una sesión.
- **Qué produce:** Archivos `REM-*.json` en `state/reminders/`. En terminal: lista de recordatorios con estado y días restantes/vencidos.
- **Integración con otros comandos:** Los recordatorios vinculados a sprint aparecen en `bago sprint --detail`. `bago review` incluye los recordatorios vencidos en el informe.
