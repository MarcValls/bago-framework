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
# 1. Contexto de repo
make repo-context-check   # detecta si el repo cambió; si da mismatch → W1 primero
make repo-context-sync    # registra el contexto actual

# 2. Salud antes de idear
./stability-summary       # agrega smoke, VM, soak y validadores en un solo informe

# 3. Ideas y ejecución
./ideas                   # lista ideas priorizadas
                          #   — bloquea con exit 1 si validate_pack o validate_state fallan
                          #   — en baseline_clean_mode solo muestra ideas low-risk con métrica
./ideas --detail N        # amplía descripción, alcance y prerequisitos de la idea N
./ideas --accept N        # genera handoff W2 para la idea N
                          #   — rechaza si la idea no declara una métrica medible
make workflow-tactical NAME=W2   # ejecuta el W2 con el handoff generado
```

## Gates activos

| Gate     | Cuándo actúa                    | Efecto                                                         |
| -------- | ------------------------------- | -------------------------------------------------------------- |
| Canónico | Al invocar `./ideas`            | Bloquea si `validate_pack` o `validate_state` no son GO        |
| Smoke    | Al invocar `./ideas`            | WARN si no disponible; KO si disponible y falla                |
| Métrica  | Al invocar `./ideas --accept N` | Rechaza con exit 1 si la idea no tiene campo `metric` no vacío |

## Comandos de inspección

```bash
./stability-summary              # informe de salud del pack
./workflow-info W1               # detalle de un workflow concreto
make WF                          # enumera workflows tácticos W1..W6
python3 .bago/tools/validate_pack.py   # validación directa del pack
```
