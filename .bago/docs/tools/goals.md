# bago goals — Gestión de objetivos

> Crea, vincula, actualiza y cierra objetivos de trabajo con seguimiento de progreso.

## Descripción

`bago goals` gestiona los objetivos del proyecto guardados como GOAL-*.json en state/goals/. Cada objetivo tiene un criterio de éxito medible, un porcentaje de progreso y puede vincularse a sesiones específicas. Permite hacer seguimiento de hacia dónde va el trabajo sin perder la vista de alto nivel.

## Uso

```bash
bago goals                     → lista todos los objetivos activos
bago goals new "<título>"      → crea nuevo objetivo
bago goals link <GOAL-ID> <SES-ID>  → vincula objetivo a sesión
bago goals close <GOAL-ID>     → cierra un objetivo como completado
bago goals progress <GOAL-ID> <N>   → actualiza progreso (0-100)
bago goals --json              → output JSON con todos los objetivos
bago goals --test              → valida dependencias y sale con "OK"
```

## Opciones

| Opción | Descripción |
|--------|-------------|
| `new "<título>"` | Crea un nuevo objetivo |
| `link <GOAL> <SES>` | Vincula una sesión a un objetivo |
| `close <GOAL>` | Marca el objetivo como completado |
| `progress <GOAL> N` | Actualiza el porcentaje de progreso (0-100) |
| `--json` | Output JSON |
| `--test` | Modo test |

## Ejemplos

```bash
# Ver todos los objetivos activos
bago goals

# Crear nuevo objetivo
bago goals new "Implementar pipeline GitHub completo"

# Actualizar progreso
bago goals progress GOAL-001 75

# Cerrar objetivo completado
bago goals close GOAL-001
```

## Casos de uso

- **Cuándo usarlo:** Para mantener claridad sobre los objetivos de alto nivel mientras se trabaja en sesiones individuales. Especialmente útil al inicio de sprint.
- **Qué produce:** Archivos GOAL-*.json en state/goals/. En terminal: tabla de objetivos con progreso visual.
- **Integración con otros comandos:** Los objetivos se vinculan a sesiones con `bago goals link`. `bago review` muestra el estado de los goals. `bago sprint` puede referenciar goals.
