# Migración de BAGO AMTEC V1 a BAGO AMTEC V2.1 CORREGIDA

## Objetivo

Corregir el salto de V1 a V2.1 sin perder la historia real de la instalación original y sin mantener las ambigüedades estructurales que motivaron la nueva versión.

## Material original preservado

Se ha preservado una copia navegable de la v1 original en:

`docs/migration/legacy/original_bago_v1/`

## Material traducido

- sesiones migradas: **3**
- cambios migrados: **5**

## Cambios aplicados respecto al pack auditado

1. `pack.json` usa rutas relativas coherentes.
2. se añade `workflow_history_migration`.
3. se incorporan `role.schema.json` y `workflow.schema.json`.
4. se preserva la v1 original dentro del pack.
5. se crean traducciones JSON del historial real de la v1.
6. se densifican prompts, plantillas y readmes.
7. se añaden herramientas ligeras de validación.

## Criterio de fidelidad

La migración se considera suficientemente fiel si:

- cada sesión migrada referencia su archivo fuente;
- cada cambio migrado conserva rastro de origen;
- el original sigue disponible;
- el estado actual no se contamina con legado;
- el sistema puede explicar qué es actual y qué es histórico.

## Limitaciones

No toda información del markdown legado puede normalizarse sin pérdida semántica fina. Por eso el original se conserva y el migrado no pretende sustituirlo completamente.

## Normalización de estados migrados

Los cambios migrados conservan ahora `legacy_status` y añaden `normalized_status`. Esto permite mantener la formulación histórica original sin romper la auditabilidad operativa de V2.1.2.
