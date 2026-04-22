# DECISIONES · BAGO 2.5-stable

## DEC-001

Mantener la línea 2.x auditada como tronco estable.

## DEC-002

Integrar repo-first en el núcleo mediante `workflow_bootstrap_repo_first`.

## DEC-003

Volver a hacer `.bago/` autocontenida moviendo la instalación canónica a `docs/operation/INSTALACION.md`.

## DEC-004

Endurecer validación para detectar:

- deriva de versión,
- referencias obsoletas a línea canónica previa.x fuera de legado/migración,
- workflows no declarados,
- estado inconsistente.

## DEC-005

Para `github_models`, el estrés canónico deja de apoyarse en ráfaga libre y pasa a operar con:

- backoff con reintentos ante `429` y `5xx`,
- limitador global opcional de `rps`,
- reporte endurecido con desglose de errores y reintentos.

Resultado operativo observado:

- sin limitador global, `10x30` produjo `429` masivos y `error_rate` alto;
- con `agents=3`, `iterations=20` y `global_rate_limit_rps` entre `0.5` y `1.0`, los runs recientes quedaron en `0%` de error.

Presets recomendados:

- `safe`: `global_rate_limit_rps=0.5`
- `balanced`: `global_rate_limit_rps=1.0`
