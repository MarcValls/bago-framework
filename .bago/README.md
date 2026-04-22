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

# 3. Consultar tarea W2 registrada
bago task                 # muestra el handoff aceptado o cerrado (objetivo/alcance/archivos/validación)
bago task --done --test-cmd "<cmd>" --human-check "<texto>"
                          # ejecuta gate de cierre (tests + validación humana) y marca completada
                          # requiere al menos un --test-cmd (se puede repetir) con exit 0
                          # requiere --human-check con mínimo 20 caracteres
bago task --clear         # elimina la tarea registrada

# 4. Abrir sesión desde handoff
bago session              # lanza session_preflight.py con objetivo/roles/artefactos del handoff
bago session --dry        # muestra los args sin ejecutar
                          # incluye chain de handoff de roles para continuidad sin cortes
```

## Gates activos

| Gate     | Cuándo actúa                    | Efecto                                                         |
| -------- | ------------------------------- | -------------------------------------------------------------- |
| Canónico | Al invocar `./ideas`            | Bloquea si `validate_pack` o `validate_state` no son GO        |
| Smoke    | Al invocar `./ideas`            | WARN si no disponible; KO si disponible y falla                |
| Métrica  | Al invocar `./ideas --accept N` | Rechaza con exit 1 si la idea no tiene campo `metric` no vacío |
| Cierre   | Al invocar `bago task --done`   | Bloquea cierre si falta `--test-cmd` (mínimo 1 y todos en verde) o si `--human-check` tiene menos de 20 caracteres |

## Alcances de comando

- `pack-only`: gobiernan `.bago` y el estado operativo del sistema.
- `dual-scope`: pueden operar sobre el pack o sobre el proyecto intervenido.
- `repo-only`: operan explícitamente sobre el proyecto intervenido.

## Comandos de inspección

### Pack-only

```bash
bago on                                # activa explícitamente el modo BAGO sobre el host
bago stability                         # informe de salud del pack (o ./stability-summary)
bago health                            # score 0-100 con 5 dimensiones
bago dashboard                         # dashboard con semáforos + KPIs
bago audit                             # auditoría integral
bago validate                          # validate_pack directo
python3 .bago/tools/validate_pack.py   # validación directa del pack
```

### Dual-scope

```bash
bago debug                             # detecta y repara bugs operativos y bugs silenciosos reparables del pack
bago debug --repo .                    # depura el proyecto intervenido en el repo actual
```

### Repo-only

```bash
bago repo-on /ruta/al/repo           # activa el repo externo y muestra comandos/workflows posibles
bago repo-debug .                      # alias explícito para depurar el proyecto intervenido
bago repo-lint .                       # ejecuta lint del proyecto intervenido
bago repo-test .                       # ejecuta tests del proyecto intervenido
bago repo-build .                      # ejecuta build del proyecto intervenido
```
