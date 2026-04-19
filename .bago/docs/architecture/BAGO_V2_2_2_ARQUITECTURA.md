# Arquitectura · BAGO AMTEC V2.2.2 Revisión Canónica

## Resumen

La 2.2.2 no abre una nueva línea. Formaliza la revisión canónica de la 2.2.1 y consolida como baseline oficial los endurecimientos aplicados sobre validación, estado, taxonomía de roles y tooling de performance.

## Principios activos

1. manifiesto único,
2. estado estructurado,
3. arranque repo-first oficial,
4. activación mínima suficiente,
5. validación obligatoria,
6. `.bago/` autocontenida,
7. trazabilidad nativa de evolución.

## Cambio principal respecto a 2.2.1

La 2.2.1 ya había consolidado:

- repo-first como ruta oficial,
- instalación interna autocontenida,
- integración de bootstrap y prompting en el núcleo.

La 2.2.2 añade:

- validación estructural más estricta de workflows, estado y roles,
- coherencia obligatoria entre `family` lógica y carpeta física de roles,
- stress real sobre `github_models` con backoff y limitador global,
- reporte enriquecido con reintentos, errores por tipo y throughput por ventana,
- documentación canónica de presets operativos de performance.

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

### Tooling de performance

- `tools/perf/stress_bago_agents.py`
- `tools/perf/render_perf_charts.py`
- `state/metrics/runs/*`

## Resultado esperado

La 2.2.2 debe comportarse como una baseline operativa más estable y medible: menos contradicción interna, mejor validación material y mejor capacidad de repetir pruebas de stress sin depender de ráfaga libre ni interpretación manual.
