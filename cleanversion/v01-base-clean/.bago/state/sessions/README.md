# state/sessions

Esta carpeta contiene sesiones nativas de la instalación línea canónica previa corregida. No debe mezclarse con sesiones migradas desde la v1.

## Diferencia con `migrated_sessions/`

- `sessions/` = sesiones nacidas en línea canónica previa.
- `migrated_sessions/` = traducciones estructuradas de snapshots v1 reales.
- `docs/migration/legacy/original_bago_v1/` = copias preservadas de los originales.

## Política

Si una sesión nació en V1, aunque se convierta a JSON, debe seguir indicando:

- su id legado,
- su ruta de origen,
- si el markdown original fue preservado.
