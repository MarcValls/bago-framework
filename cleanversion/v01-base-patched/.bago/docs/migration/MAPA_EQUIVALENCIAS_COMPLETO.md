# Mapa de equivalencias completo V1 → V2.1 CORREGIDA

## Ficheros base

- `AGENT_START.md` → AGENT_START.md
- `README.md` → README.md
- `core/00_CEREBRO_BAGO.md` → core/canon/CANON.md + core/orchestrator/ORQUESTADOR_CENTRAL.md
- `core/03_ESTADO_BAGO.md` → core/canon/CANON.md + state/schema/\* + state/global_state.json
- `core/05_GOBERNANZA_DE_SESION.md` → core/canon/REGLAS_DE_ACTIVACION.md + roles/gobierno/_ + roles/supervision/_
- `core/06_MATRIZ_DE_ACTIVACION.md` → core/orchestrator/MATRIZ_DE_ENRUTADO.md
- `core/07_PROTOCOLO_DE_CAMBIO.md` → core/canon/PROTOCOLO_DE_CAMBIO.md
- `docs/MIGRACION_V0_A_V1.md` → docs/migration/legacy/original_bago_v1/docs/MIGRACION_V0_A_V1.md
- `docs/ROADMAP_V1.md` → docs/migration/legacy/original_bago_v1/docs/ROADMAP_V1.md
- `manifest.json` → eliminado como manifiesto operativo; no se preserva como manifiesto activo
- `pack.json` → pack.json
- `prompts/00_BOOTSTRAP_PROYECTO.md` → prompts/activar_migracion_historial.md + AGENT_START.md + docs/migration/legacy/original_bago_v1/prompts/00_BOOTSTRAP_PROYECTO.md
- `prompts/03_TAREA_DE_PROYECTO.md` → prompts/activar_maestro.md + prompts/activar_orquestador.md + preservado legado
- `prompts/04_REVISION_EVOLUTIVA.md` → prompts/activar_revision_canonica.md + core/supervision/VERTICE.md + preservado legado
- `roles/ANALISTA_Contexto.md` → roles/produccion/ANALISTA.md
- `roles/ARQUITECTO_Soluciones.md` → roles/produccion/ARQUITECTO.md
- `roles/GENERADOR_Contenido.md` → roles/produccion/GENERADOR.md
- `roles/MAESTRO_BAGO.md` → roles/gobierno/MAESTRO_BAGO.md
- `roles/ORGANIZADOR_Entregables.md` → roles/produccion/ORGANIZADOR.md
- `state/ESTADO_BAGO_ACTUAL.md` → state/global_state.json + state/migrated_sessions/\* + preservado legado
- `state/cambios/2026-04-09__BAGO-CHG-001__fundacion-v1.md` → state/migrated_changes/BAGO-LEG-001.json + preservado legado
- `state/cambios/2026-04-09__BAGO-CHG-002__arranque-repo-real-tpv.md` → state/migrated_changes/BAGO-LEG-002.json + preservado legado
- `state/cambios/2026-04-10__BAGO-CHG-003__cierre-sprint-1b-compras-y-cierre-worktrees-swarm.md` → state/migrated_changes/BAGO-CHG-003.json + preservado legado
- `state/cambios/2026-04-10__BAGO-CHG-004__sprint-1b1-estabilizacion-a11y-ok-performance-bloqueado.md` → state/migrated_changes/BAGO-CHG-004.json + preservado legado
- `state/cambios/2026-04-11__BAGO-CHG-005__performance-web-lighthouse-90-y-a11y-recertificada.md` → state/migrated_changes/BAGO-CHG-005.json + preservado legado
- `state/cambios/README.md` → state/migrated_changes/README.md + docs/migration/legacy/original_bago_v1/state/cambios/README.md
- `state/sesiones/2026-04-09__start__sesion_start_20260409_100650.md` → state/migrated_sessions/SES-MIG-001.json + preservado legado
- `state/sesiones/2026-04-10__start__sesion_start_20260410_142038.md` → state/migrated_sessions/SES-MIG-002.json + preservado legado
- `state/sesiones/2026-04-10__start__sesion_start_20260410_215636.md` → state/migrated_sessions/SES-MIG-003.json + preservado legado
- `state/sesiones/README.md` → state/migrated_sessions/README.md + docs/migration/legacy/original_bago_v1/state/sesiones/README.md
- `supervision/GUIA_VERTICE.md` → roles/supervision/VERTICE.md + core/supervision/VERTICE.md
- `workflows/01_inicio_de_sesion.md` → AGENT_START.md + core/workflows/workflow_analisis.md
- `workflows/06_revision_evolutiva.md` → core/workflows/workflow_cambio_sistemico.md + core/supervision/VERTICE.md
