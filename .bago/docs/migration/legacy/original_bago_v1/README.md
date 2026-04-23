# `.bago/` · BAGO AMTEC V1

BAGO AMTEC V1 convierte la base documental de V.0 en un paquete operativo con:

- **punto de entrada único**,
- **manifiesto canónico**,
- **estado vivo separado del modelo**,
- **matriz de activación de roles**,
- **protocolo de cambio y trazabilidad**,
- **migración explícita desde V.0**.

## Qué cambia respecto a V.0

1. `pack.json` pasa a ser el manifiesto canónico del paquete.
2. El estado vivo ya no se confunde con el documento que explica el modelo.
3. La activación de roles deja de ser implícita y se rige por una matriz.
4. Toda revisión evolutiva debe dejar rastro en `state/cambios/`.
5. Se normaliza el uso de rutas con prefijo **`.bago/`**.

## Punto de entrada

```text
.bago/AGENT_START.md
```

## Orden mínimo de lectura

1. `.bago/AGENT_START.md`
2. `.bago/core/00_CEREBRO_BAGO.md`
3. `.bago/core/03_ESTADO_BAGO.md`
4. `.bago/state/ESTADO_BAGO_ACTUAL.md`
5. `.bago/core/05_GOBERNANZA_DE_SESION.md`
6. `.bago/core/06_MATRIZ_DE_ACTIVACION.md`
7. `.bago/core/07_PROTOCOLO_DE_CAMBIO.md`

## Regla práctica

- Para arrancar: `AGENT_START.md`
- Para entender el modelo: `core/`
- Para ver la sesión real: `state/ESTADO_BAGO_ACTUAL.md`
- Para revisar deriva o arquitectura: `workflows/06_revision_evolutiva.md`
- Para migrar desde V.0: `docs/MIGRACION_V0_A_V1.md`

## Criterio de uso correcto

BAGO AMTEC V1 se está usando bien cuando:

- el arranque parte de contexto real del repo,
- el estado vivo se actualiza tras cada bloque relevante,
- los roles se activan por necesidad y no por costumbre,
- la supervisión deja trazabilidad,
- las decisiones congeladas y los pendientes no se mezclan.
