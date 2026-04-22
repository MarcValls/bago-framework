# bago flow — Flowchart ASCII de pipelines W0-W9

> Muestra los diagramas de flujo ASCII de los workflows canónicos W0-W9.

## Descripción

`bago flow` genera diagramas de flujo en ASCII art para los pipelines de los workflows BAGO. Permite visualizar el proceso paso a paso de cada workflow sin necesidad de abrir los archivos Markdown de `.bago/workflows/`. Útil para elegir el workflow correcto o para recordar los pasos de un workflow poco frecuente.

## Uso

```bash
bago flow                      → muestra todos los workflows disponibles
bago flow <WORKFLOW>           → flowchart del workflow indicado
bago flow --all                → flowcharts de todos los workflows
bago flow --test               → valida dependencias y sale con "OK"
```

## Opciones

| Opción | Descripción |
|--------|-------------|
| `<WORKFLOW>` | Nombre del workflow: w0, w7, w8, w9, etc. |
| `--all` | Muestra todos los flowcharts |
| `--test` | Modo test |

## Workflows disponibles

| ID | Nombre |
|----|--------|
| `w0` | W0_FREE_SESSION — Sesión libre sin objetivo |
| `w7` | W7_FOCO_SESION — Sesión de foco con tarea definida |
| `w8` | W8_EXPLORACION — Sesión exploratoria |
| `w9` | W9_COSECHA — Protocolo de cosecha contextual |

## Ejemplos

```bash
# Ver lista de workflows
bago flow

# Flowchart del workflow W7
bago flow w7

# Ver el proceso completo de cosecha W9
bago flow w9
```

## Casos de uso

- **Cuándo usarlo:** Antes de iniciar una sesión para elegir el workflow correcto, o cuando no recuerdas los pasos de un workflow.
- **Qué produce:** Diagrama ASCII del flujo de pasos, decisiones y condiciones del workflow.
- **Integración con otros comandos:** Complementa `bago workflow` (selector interactivo). Los workflows mostrados corresponden a los archivos en `.bago/workflows/`.
