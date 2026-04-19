# state/changes

Esta carpeta contiene cambios nativos de la instalación corregida. Los cambios históricos migrados desde la v1 viven en `state/migrated_changes/`.

## Distinción importante

- `state/changes/` = cambios nacidos en esta instalación línea canónica previa corregida.
- `state/migrated_changes/` = cambios históricos heredados y traducidos.
- `docs/migration/legacy/original_bago_v1/state/cambios/` = markdowns originales preservados.

## Política

Un cambio nativo no debe presentarse como legado y un cambio legado no debe presentarse como nativo. Si una decisión moderna afecta a la interpretación del legado, debe registrarse como cambio nativo adicional, no sobrescribiendo el cambio original.

## Convención recomendada

Usar `BAGO-CHG-XXX.json` para cambios nuevos y mantener `source_path` cuando el cambio derive de otra versión.
