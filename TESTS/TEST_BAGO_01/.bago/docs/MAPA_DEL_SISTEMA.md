# MAPA DEL SISTEMA · BAGO 2.5-stable

```text
Usuario
  ↓
AGENT_START
  ↓
workflow_bootstrap_repo_first  (si hay repo real)
  ↓
ADAPTADOR_PROYECTO
  ↓
INICIADOR_MAESTRO
  ↓
MAESTRO_BAGO
  ↓
ORQUESTADOR_CENTRAL
  ↓
WORKFLOW principal
  ↓
ROLES
  ↓
VALIDADOR
  ↓
ESTADO + CAMBIO + EVIDENCIA
```

## Capas

### Entrada

- `AGENT_START.md`
- `docs/operation/INSTALACION.md`

### Núcleo cognitivo

- `core/00_CEREBRO_BAGO.md`
- `core/01_PLANTILLA_PROMPT.md`
- `core/02_FABRICA_PROMPTS.md`

### Bootstrap repo-first

- `core/workflows/workflow_bootstrap_repo_first.md`
- `agents/ADAPTADOR_PROYECTO.md`
- `agents/INICIADOR_MAESTRO.md`

### Gobierno

- `core/canon/*`
- `core/orchestrator/*`
- `core/workflows/*`

### Memoria y verificación

- `state/*`
- `tools/*`
- `docs/migration/*`

## Ejemplos enlazados

- `examples/prompts/ejemplo_prompt_arquitectura.md`
- `examples/sesiones/ejemplo_sesion_supervision.md`
