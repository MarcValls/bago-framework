# CANON · BAGO AMTEC línea canónica previa CORREGIDO

## Naturaleza

El canon es la capa normativa del sistema. En esta edición corregida tiene además una responsabilidad explícita: impedir que la mejora formal destruya la continuidad histórica o que la migración histórica degrade la claridad estructural.

## Principios canónicos

### 1. Manifiesto único y resoluble

`pack.json` es la única fuente de manifiesto operativo y sus rutas deben poder resolverse desde el directorio en que vive el propio archivo.

### 2. Separación de capas

Se distinguen sin mezcla estable:

- interfaz,
- orquestación,
- gobierno,
- producción,
- supervisión,
- persistencia,
- legado preservado,
- herramientas de validación.

### 3. Persistencia dual controlada

La operación actual vive en JSON estructurado; la memoria histórica preservada puede vivir en markdown legado, siempre identificada como legado y nunca como estado vivo dominante.

### 4. Activación mínima suficiente

Ningún rol se activa por costumbre. Se activa por necesidad y por frontera funcional.

### 5. Supervisión no ejecutiva

Auditor Canónico y Vértice observan, recomiendan y endurecen la coherencia, pero no colonizan la ejecución productiva.

### 6. Migración sin pérdida

Cuando una instalación evoluciona, la historia real no se sustituye por ejemplos. Se preserva, se traduce y se referencia.

### 7. Verificabilidad

Todo paquete serio debe poder auditar:

- su manifiesto,
- su estado,
- su árbol,
- su trazabilidad,
- su coherencia documental mínima.

## Fuentes de verdad por ámbito

| Ámbito             | Fuente                                                         |
| ------------------ | -------------------------------------------------------------- |
| manifiesto         | `pack.json`                                                    |
| norma del sistema  | `core/canon/*`                                                 |
| ruta de ejecución  | `core/workflows/*`                                             |
| estado vivo actual | `state/global_state.json` y sesiones JSON activas              |
| historia migrada   | `state/migrated_*` + `docs/migration/legacy/original_bago_v1/` |
| verificaciones     | `tools/*`                                                      |

## Regla de precedencia

1. `pack.json`
2. `CANON.md`
3. contratos
4. workflows
5. roles
6. estado estructurado actual
7. mapeos de migración
8. material legado preservado

## Invalidez canónica

Una propuesta es inválida si:

- introduce una segunda fuente de manifiesto,
- rompe resolubilidad de rutas,
- elimina o simula historia real sin declararlo,
- mezcla estado actual con legado sin distinguirlos,
- infla el sistema con archivos huecos declarados como operativos.

## Criterio de sistema sano

BAGO está sano si puede responder con precisión:

- qué archivo manda,
- qué tarea está abierta,
- qué historial es actual y cuál legado,
- qué roles se activaron y por qué,
- qué cambió y con qué validación.
