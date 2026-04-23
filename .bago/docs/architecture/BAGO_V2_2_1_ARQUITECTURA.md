# Arquitectura · BAGO AMTEC V2.2.1 Consolidación

## Resumen

La 2.2.1 no abre una nueva línea. Consolida la 2.2 híbrida. El objetivo es cerrar la distancia entre la capa repo-first recuperada del enfoque flat y el núcleo canónico heredado de la línea 2.x (ver [docs/governance/REGLA_INMUTABILIDAD_VALIDACION.md](../governance/REGLA_INMUTABILIDAD_VALIDACION.md)).

## Principios activos

1. manifiesto único,
2. estado estructurado,
3. arranque repo-first oficial,
4. activación mínima suficiente,
5. validación obligatoria,
6. `.bago/` autocontenida.

## Cambio principal respecto a 2.2

La 2.2 ya tenía:

- bootstrap repo-first,
- agentes de arranque,
- fábrica de prompts.

La 2.2.1 añade:

- integración oficial en reglas, router y matriz,
- workflow propio de bootstrap,
- limpieza de identidad de versión,
- instalación canónica interna,
- validación contra restos operativos de línea canónica previa.x.

## Componentes clave

### Bootstrap

- `workflow_bootstrap_repo_first`
- `ADAPTADOR_PROYECTO`
- `INICIADOR_MAESTRO`

### Gobierno

- `CANON.md`
- `REGLAS_DE_ACTIVACION.md`
- `ORQUESTADOR_CENTRAL.md`
- `ROUTER_DE_ROLES.md`
- `MATRIZ_DE_ENRUTADO.md`

### Persistencia

- `state/global_state.json`
- `state/sessions/*`
- `state/changes/*`
- `state/evidences/*`

## Resultado esperado

La 2.2.1 debe dejar de parecer una línea canónica previa reforzada con un injerto flat y pasar a ser una instalación única, coherente y utilizable sobre trabajo real.
