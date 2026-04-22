# AGENT_START · BAGO AMTEC V1

## Objetivo

Definir el arranque único y obligatorio de cualquier sesión sobre un repositorio que use BAGO AMTEC V1.

Este archivo evita tres fallos típicos de V.0:

- arranques sin manifiesto,
- estado desactualizado o mezclado con la plantilla,
- activación prematura de demasiados roles.

---

## Precondición de entrada

Antes de producir cambios relevantes, el agente debe confirmar la existencia de:

- `.bago/pack.json`
- `.bago/core/00_CEREBRO_BAGO.md`
- `.bago/core/03_ESTADO_BAGO.md`
- `.bago/state/ESTADO_BAGO_ACTUAL.md`

Si falta alguno, la sesión debe tratarse como **bootstrap incompleto**.

### Arranque automático recomendado

Para ejecutar esta validación de forma automática desde terminal:

```text
pnpm bago:start
```

Modo validación sin escritura:

```text
pnpm bago:start:check
```

---

## Secuencia de arranque obligatoria

### Fase 1 · Carga canónica

1. Leer `.bago/pack.json`.
2. Leer `.bago/README.md`.
3. Leer `.bago/core/00_CEREBRO_BAGO.md`.
4. Leer `.bago/core/03_ESTADO_BAGO.md`.
5. Leer `.bago/core/05_GOBERNANZA_DE_SESION.md`.
6. Leer `.bago/core/06_MATRIZ_DE_ACTIVACION.md`.
7. Leer `.bago/state/ESTADO_BAGO_ACTUAL.md`.

### Fase 2 · Adaptación al proyecto

1. Inspeccionar el repositorio real.
2. Identificar propósito, stack, módulos, restricciones y riesgos.
3. Actualizar `.bago/state/ESTADO_BAGO_ACTUAL.md`.
4. Si hay hallazgos estructurales, registrar un apunte en `state/cambios/`.

### Fase 3 · Arranque del maestro

1. Activar `MAESTRO_BAGO`.
2. Declarar objetivo actual.
3. Declarar modo predominante.
4. Seleccionar solo los roles necesarios según la matriz.
5. Dejar el siguiente paso operativo visible.

### Fase 4 · Ejecución normal

1. Ejecutar el ciclo BAGO.
2. Actualizar el estado vivo al cerrar cada bloque relevante.
3. Registrar decisiones congeladas y cambios aceptados.

### Fase 5 · Supervisión evolutiva

Activar `GUIA_VERTICE` solo con evidencia suficiente, siguiendo:

```text
.bago/workflows/06_revision_evolutiva.md
```

---

## Salida mínima esperada tras el arranque

- resumen del proyecto,
- objetivo actual,
- modo predominante,
- roles activos,
- restricciones,
- decisiones congeladas vigentes,
- siguiente paso sugerido.

---

## Prohibiciones de arranque

El agente no debe:

- empezar implementación extensa sin estado vivo actualizado,
- tratar `core/03_ESTADO_BAGO.md` como si fuera el estado real de la sesión,
- usar rutas `bago/` sin el prefijo canónico `.bago/`,
- activar `GUIA_VERTICE` por rutina,
- mezclar pendientes con decisiones congeladas.
