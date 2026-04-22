# Migración de BAGO AMTEC V.0 a V1

## Objetivo

Migrar sin romper la lógica mental de V.0 y añadiendo estructura donde V.0 era demasiado implícito.

## Cambios principales

| Tema                   | V.0                          | V1                                          |
| ---------------------- | ---------------------------- | ------------------------------------------- |
| Manifiesto             | no existía                   | `pack.json` canónico                        |
| Estado                 | plantilla y estado mezclados | modelo en `core/` + estado vivo en `state/` |
| Activación de roles    | implícita                    | matriz explícita                            |
| Trazabilidad de cambio | débil                        | `state/cambios/`                            |
| Rutas                  | mezcla `bago/` y `.bago/`    | solo `.bago/`                               |

## Pasos de migración

1. Copiar la nueva carpeta `.bago/` en una rama o entorno de prueba.
2. Revisar `pack.json`.
3. Adaptar `state/ESTADO_BAGO_ACTUAL.md` al repo real.
4. Reescribir referencias antiguas `bago/` → `.bago/`.
5. Ejecutar un arranque completo con `AGENT_START.md`.
6. Registrar el primer cambio estructural aceptado.

## Compatibilidad conceptual preservada

Se mantiene:

- el ciclo BAGO,
- la idea de roles operativos,
- la supervisión evolutiva no permanente,
- el arranque basado en repo real.
