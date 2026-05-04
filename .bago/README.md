# BAGO

Este es el `README` técnico de la capa BAGO. La entrada humana corta del repo está en [README.md](../README.md).

BAGO es un sistema operativo de trabajo técnico para programación, automatización y generación compleja.

## Qué resuelve

- Pérdida de contexto entre iteraciones.
- Arranques improvisados.
- Solape entre análisis, diseño, generación y cierre.
- Cambios sensibles sin rastro suficiente.
- Deriva entre estado y realidad del repositorio.

## Qué no es

- No es una narrativa.
- No es un sistema universal para todo tipo de tarea.
- No es un sustituto del juicio humano en cambios sensibles.

## Idea central

El sistema amplifica; la decisión crítica sigue siendo humana.

## Recorrido de arranque

```bash
# 1. Salud antes de idear
bago stability            # o ./stability-summary
                          # agrega smoke, VM, soak y validadores en un solo informe

# 2. Ideas y ejecución
bago ideas                # o ./ideas — lista ideas priorizadas
                          #   — bloquea con exit 1 si validate_pack o validate_state fallan
                          #   — en baseline_clean_mode solo muestra ideas low-risk con métrica
                          #   — filtra ideas ya marcadas como implementadas
bago ideas --detail N     # o ./ideas --detail N — amplía descripción y alcance de la idea N
bago ideas --accept N     # o ./ideas --accept N — genera handoff W2 para la idea N
                          #   — rechaza si la idea no declara una métrica medible
                          #   — escribe .bago/state/pending_w2_task.json

# 3. Consultar tarea W2 activa
bago task                 # muestra el handoff aceptado (objetivo/alcance/archivos/validación)
bago task --done          # marca la tarea como completada y la registra en implemented_ideas.json
bago task --clear         # elimina la tarea pendiente

# 4. Abrir sesión desde handoff
bago session              # lanza session_preflight.py con objetivo/roles/artefactos del handoff
bago session --dry        # muestra los args sin ejecutar
```

## Gates activos

| Gate     | Cuándo actúa                    | Efecto                                                         |
| -------- | ------------------------------- | -------------------------------------------------------------- |
| Canónico | Al invocar `./ideas`            | Bloquea si `validate_pack` o `validate_state` no son GO        |
| Smoke    | Al invocar `./ideas`            | WARN si no disponible; KO si disponible y falla                |
| Métrica  | Al invocar `./ideas --accept N` | Rechaza con exit 1 si la idea no tiene campo `metric` no vacío |

## Comandos de inspección

```bash
bago stability                         # informe de salud del pack (o ./stability-summary)
bago health                            # score 0-100 con 5 dimensiones
bago dashboard                         # dashboard con semáforos + KPIs
bago audit                             # auditoría integral
bago validate                          # validate_pack directo
python3 .bago/tools/validate_pack.py   # validación directa del pack
```
