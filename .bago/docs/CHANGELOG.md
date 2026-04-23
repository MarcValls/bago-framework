# Changelog — bago_amtec

> Formato: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
> Generado por `bago changelog` el 2026-04-23

---

## [3.0] — Sprint 005 (2026-04-23)

### Added

- `bago watch-state` → `bago_watch.py` — Smart watcher con delta findings: polling SHA-256 sobre `state/changes/`, `state/sessions/`, `state/findings/`; health check automático post-cambio; `--once` para CI
- `dashboard_v2.py` — Motor del dashboard V2: health_ring con semáforo, riesgo cuantificado, ledger de deuda técnica en horas y €, sparkline de velocity; consumido por `pack_dashboard.py`

### Changed

- `testgen.py` — Python 3.9 compat: `Optional[X]` en lugar de union syntax `X | Y`; Go: subtests con `t.Run` y función anónima; Rust: patrón AAA (Arrange/Act/Assert) en tests generados
- `validate_state.py` — RULE-CDTR-001 v2: CDTR-E01 blocking (findings críticos sin reconocer >7 días bloquean merge); CDTR-E02 advisory (health < 70 sin sprint de mejora activo)

---

## [2.6] — Sprint 180 (2026-04-22)

### Added

**Herramientas #91–#97 — Análisis estático avanzado y tooling del framework**
- Tool #91: `bago bago-lint` → `bago_lint_cli.py` — CLI dedicado bago-lint con 7 reglas, `--fix`, `--preview`, `--json`, `--since`
- Tool #92: `bago multi-scan` → `multi_scan.py` — Scanner multi-lenguaje simultáneo (py/js/go/rust), `--since`, `--summary`
- Tool #93: `js_ast_scanner.js` — Linter AST JS/TS vía acorn: 10 reglas, noqa, más preciso que regex
- Tool #94: `bago permission-check` → `permission_check.py` — Verifica y corrige +x en todos los ejecutables BAGO
- Tool #95: `bago install-deps` → `install_deps.py` — Verifica e instala dependencias opcionales (pip/npm/go/rust)
- Tool #96: `bago rule-catalog` → `rule_catalog.py` — Catálogo Markdown/HTML de todas las reglas BAGO-* y JS-* (17 total)
- Tool #97: `bago lint-report` → `lint_report.py` — Convierte JSON de bago-lint / multi-scan en informe Markdown estructurado
- Documentación individual para cada tool en `.bago/docs/tools/` (7 nuevos archivos)
- `.bago/docs/RULE_CATALOG.md` y `.bago/docs/RULE_CATALOG.html` — catálogos generados automáticamente

### Changed

- `README.md`: contadores actualizados — 95 herramientas, 64/64 tests, versión 2.6
- Suite de integración: **64/64 ✅ ALL PASS**
- `BAGO_REFERENCIA_COMPLETA.md`: sección 8 ampliada con herramientas #91–#97
- `ESTADO_BAGO_ACTUAL.md`: actualizado a 95 tools, 64/64 tests, Sprint 180 Fase 7

### Fixed

- Permisos +x aplicados automáticamente en todos los ejecutables BAGO via `permission_check.py`

---

## [2.5-stable] — Sprint 180 (2026-04-22)

### Added

**Fase 1 — Sprint 180 (S1–S7)**
- `bago sprint` → `sprint_manager.py` — Gestión de sprints SPRINT-NNN.json
- `bago search` → `bago_search.py` — Full-text search sobre sessions/changes
- `bago timeline` → `timeline.py` — Timeline ASCII semanal con workflows
- `bago report` → `report_generator.py` — Reportes Markdown con filtros temporales
- `bago metrics` → `metrics_trends.py` — Tendencias rolling + sparklines ASCII
- `bago doctor` → `doctor.py` — Diagnóstico integral del pack
- `bago git` → `git_context.py` — Contexto git (branch/log/autores) + inject

**Fase 2 — Sprint 180 (S8–S15)**
- `bago export` → `export.py` — HTML dark-theme + CSV con SVG chart
- `bago watch` → `watch.py` — Monitor en tiempo real del estado BAGO
- `bago test` → `integration_tests.py` — Suite de integración (inicio: 22 tests)
- `bago changelog` → `changelog.py` — CHANGELOG desde BAGO-CHG-*.json (Keep a Changelog)
- `bago snapshot` → `snapshot.py` — ZIP point-in-time de state/
- `bago diff` → `diff.py` — Delta de state/ vs último snapshot
- `bago session-stats` (alias: `ss`) → `session_details.py` — Top sesiones por producción
- `bago compare` → `compare.py` — Comparativa wf/periodo/rol lado a lado

**Fase 3 — Sprint 180 (S16–S20)**
- `bago goals` → `goals.py` — Gestión de objetivos con link/close/progress
- `bago lint` → `lint.py` — Linter calidad del pack (0 errores, 11 avisos)
- `bago summary` → `summary.py` — Resumen ejecutivo Markdown de sesion/sprint
- `bago tags` → `tags.py` — Etiquetado con índice y búsqueda rápida
- `bago flow` → `flow.py` — Flowchart ASCII de pipelines W0-W9

**Fase 4 — Sprint 180 (S21–S23)**
- `bago detector` → `context_detector.py` — Detector de contexto acumulado (ampliado)
- Subtools internos — motor de análisis estático (soporte para `scan`/`hotspot`/`fix`/`gh`):
  - `findings_engine.py` — Motor de hallazgos unificado: parsing de linters, modelo canónico de Finding (id, severity, file, line, rule, fix_suggestion, autofixable, fix_patch)
  - `risk_matrix.py` — Matriz de riesgo: categorías Security/Reliability/Maintainability/VelocityDrag × Probabilidad/Impacto → Exposición cuantificada
  - `debt_ledger.py` — Ledger de deuda técnica: cuantifica en horas y € con cuadrantes Reckless/Prudent × Deliberate/Inadvertent
  - `impact_engine.py` — Motor de impacto: traduce health score y deuda técnica en métricas de negocio (multiplicador de velocidad, €/trimestre)
- Subtools internos — gestión de estado y contexto:
  - `state_store.py` — Capa de abstracción de almacenamiento: desacopla las tools del backend concreto
  - `context_collector.py` — Recolecta y resume contexto operativo de uno o varios directorios
  - `context_map.py` — Mapa de contexto distribuido: descubre instalaciones `.bago/` bajo una raíz y construye un mapa jerárquico
  - `reconcile_state.py` — Reconcilia el inventario en `global_state.json` con los archivos reales en `state/`
  - `artifact_counter.py` — Mide la producción de artefactos útiles por sesión (excluye artefactos de protocolo)
- Subtools internos — validación y contratos:
  - `validate_manifest.py` — Valida integridad y esquema del manifiesto `pack.json`
  - `validate_state.py` — Valida consistencia del estado: sessions/changes/evidences
  - `contracts.py` — Sistema de contratos de estado verificables con deadline y auditoría
  - `session_preflight.py` — Preflight W7: verifica reglas ESCENARIO-001 antes de abrir sesión
- Subtools internos — gobernanza y utilidades:
  - `repo_context_guard.py` — Guard de contexto: detecta `match`/`mismatch`/`new` al cambiar de repo
  - `target_selector.py` — Selector seguro de directorio objetivo con candidatos priorizados y opción manual
  - `vertice_activator.py` — Evaluador de señales para activar revisión Vértice (sesiones W0 sin decisiones, etc.)
  - `bago_utils.py` — Utilidades compartidas: print_ok/fail/skip, runner de tests inline para todos los tools
  - `session_stats.py` — Estadísticas agregadas de sesiones por tipo de tarea, workflow y rol
  - `stability_summary.py` — Resume informes de sandbox (smoke/VM/soak) y validadores canónicos
  - `efficiency_meter.py` — Compara métricas de salud y productividad entre cleanversions

**Fase 5 — Sprint 180 (S24–S33)**
- `bago insights` → `insights.py` — Motor de insights automáticos (5 categorías: PRODUCCION/PATRON/RIESGO/TENDENCIA/RECOMENDACION)
- `bago config` → `config.py` — Gestión de configuración del pack.json con validación de tipos
- `bago check` → `check.py` — Checklist pre-sesión personalizable desde checklist.json
- `bago archive` → `archive.py` — Archivado de sesiones cerradas antiguas en state/sessions/archive/
- `bago stats` → `stats.py` — Dashboard agregado con sparklines de actividad
- `bago remind` → `remind.py` — Recordatorios con due-date y sprint_ref (REM-*.json)
- `bago habit` → `habit.py` — Detector de hábitos positivos/mejora/patrones desde sesiones
- `bago review` → `review.py` — Informe de revisión periódica Markdown
- `bago test` ampliado de 22 a **36 tests** (23 tools cubiertos)

**Fase 6 — Sprint 180 (S34–S35+)**
- `bago velocity` → `velocity.py` — Métricas de velocidad por período con rolling windows y proyección de fin de mes
- `bago patch` → `patch.py` — Corrección automática de inconsistencias (3 parches: legacy-status, missing-tests, missing-goal)
- `bago notes` → `notes.py` — Notas ligeras por sesión: add/list/show/delete/search (almacenadas en `state/notes/NOTE-*.json`)
- `bago template` → `template.py` — Plantillas para nuevas sesiones con campos prefilled (4 built-in: sprint, analysis, hotfix, exploration)

### Changed

- Health score: mantenido en **100/100 🟢** durante todo el Sprint 180
- `bago test`: suite ampliada progresivamente de 22 → 55 tests pasando
- `bago_banner.py`: actualizado con nuevos comandos en el menú

### Added — Sprint 180 Fase 7 (CHG-079, CHG-080)

- `bago scan` → `scan.py` — ✅ Análisis estático multi-linter (hallazgos unificados)
- `bago hotspot` → `hotspot.py` — ✅ Hotspots: archivos con más cambios + fallos + complejidad
- `bago fix` → `autofix.py` — ✅ Autofix con generación y aplicación de parches validados
- `bago gh` → `gh_integration.py` — ✅ Integración GitHub: check runs y comentarios en PRs
- `bago ci` → `ci_generator.py` — ✅ Generación GitHub Actions + GitLab CI + pre-commit hook
- `bago ask` → `bago_ask.py` — ✅ Búsqueda en lenguaje natural sobre 166 docs BAGO
- `bago watch-state` → `bago_watch.py` — ✅ Monitor de estado con polling SHA256 y health check
- `bago testgen` (Go/Rust) → `testgen.py` ampliado — ✅ Generación tests Go y Rust

**BAGO-CHG-079** — Sprint 180 cierre: ci_generator, bago_ask, correcciones datetime tz, SPRINT-004 cerrado, **55/55 tests** ALL PASS, 71 routing entries.

**BAGO-CHG-080** — SPRINT-005: Python 3.9 compat (Optional[X]), dashboard v2 cockpit, auto_mode fix, RULE-CDTR-001 enforcement, bago_watch, testgen Go/Rust, IDEAS scoring dinámico.

---

## [April 2026]

### Changed

- ⚙️ **Reconstrucción limpia del canon BAGO** `BAGO-CHG-034` *major* — `AGENT_START.md`, `README.md`, `pack.json`
- ⚙️ **Corte de revisión canónica y oficialización de BAGO AMTEC 2.2.2** `BAGO-CHG-029` *major*
- 🏛 **Corrección del pack línea canónica previa según auditoría crítica** `BAGO-CHG-021` *major*
- ⚙️ **Sprint 180 — 7 nuevas herramientas CLI para el framework BAGO** `BAGO-CHG-070` *minor* — `sprint_manager.py`, `bago_search.py`, `timeline.py`
- ⚙️ **TEMP gate validation · cierre W2 automático** `BAGO-CHG-069` *minor* — `show_task.py`, `generate_task_closure.py`, `pending_w2_task.json`
- ⚙️ **Cosecha contextual W9: NECESITO BOOTSTRAP Y GENERACIÓN DE IDEAS** `BAGO-CHG-068` *minor* — `DECISIONES.md`, `00_BOOTSTRAP_PROYECTO.md`, `CONTRATO_FRONTERA_LLM.md`
- ⚙️ **Cosecha contextual W9: auditoria nuclear** `BAGO-CHG-067` *minor* — `BAGO-CHG-066.json`, `BAGO-EVD-067.json`, `SES-HARVEST-2026-04-21-005.json`
- ⚙️ **Cosecha contextual W9: "."** `BAGO-CHG-066` *minor* — `stability_summary.py`, `BAGO-CHG-064.json`, `BAGO-CHG-065.json`
- ⚙️ **Alerta de task obsoleta · cierre W2 automático** `BAGO-CHG-065` *minor* — `show_task.py`, `generate_task_closure.py`, `pending_w2_task.json`
- ⚙️ **Cosecha contextual W9: Corregir la desalineacion entre auto_mode.py y context_detec** `BAGO-CHG-064` *minor* — `ORIGEN_Y_ALCANCE.md`, `BAGO-CHG-063.json`, `BAGO-EVD-064.json`
- ⚙️ **Cosecha contextual W9: Automatizar el cierre de la tarea W2 al marcarla done** `BAGO-CHG-063` *minor* — `caos_game_ideas.json`, `BAGO-CHG-061.json`, `BAGO-CHG-062.json`
- ⚙️ **Cierre automático de sesión · cierre W2 automático** `BAGO-CHG-062` *minor* — `show_task.py`, `generate_task_closure.py`, `pending_w2_task.json`
- ⚙️ **Cosecha contextual W9: analizar el contexto analizar paquets, directorios, subdirec** `BAGO-CHG-061` *minor* — `extension.mjs`, `BAGO_2.4-v2rc_clean_20260418_161154_coherent.zip`, `BAGO_2.4-v2rc_clean_20260418_161154_patched.zip`
- ⚙️ **Cosecha contextual W9: Analisis completo** `BAGO-CHG-060` *minor* — `bago_banner.py`, `emit_ideas.py`, `bago`
- ⚙️ **Cosecha contextual W9: Se identificó y corrigió el KO de BAGO causado por mismatch ** `BAGO-CHG-059` *minor* — `CHECKSUMS.sha256`, `TREE.txt`, ``
- ⚙️ **Cosecha contextual W9: Decidimos que cosecha.py debe usar type:governance para CHG ** `BAGO-CHG-058` *minor* — `(exploración sin artefactos de fichero)`
- ⚙️ **Cosecha contextual W9: Decidimos que el dashboard debe integrarse con context_detec** `BAGO-CHG-057` *minor* — `(exploración sin artefactos de fichero)`
- ⚙️ **Cosecha contextual W9: Elegimos disparador por densidad de señal cognitiva: umbral ** `BAGO-CHG-056` *minor* — `app.py`, `start.sh`, `base.html`
- ⚙️ **ESCENARIO-003 F1: context_detector + cosecha + W9 + tpl_harvest** `BAGO-CHG-055` *minor* — `context_detector.py`, `cosecha.py`, `W9_COSECHA.md`
- ⚙️ **ESCENARIO-001 SES-5: BAGO_EVOLUCION_v2 + evaluación final E001 + cierre escenario** `BAGO-CHG-053` *minor* — `BAGO_EVOLUCION_SISTEMA_v2.md`, `EVAL-ESCENARIO001-FINAL.md`, `ESCENARIO-MEJORA-ARTEFACTOS-FOCO.md`
- ⚙️ **ESCENARIO-003: diseño cosecha contextual (standby activo + W9)** `BAGO-CHG-054` *minor* — `ESCENARIO-003-COSECHA-CONTEXTUAL.md`
- ⚙️ **ESCENARIO-001 SES-4: W8_EXPLORACION workflow + plantilla exploración** `BAGO-CHG-052` *minor* — `W8_EXPLORACION.md`, `tpl_exploration.md`, `WORKFLOWS_INDEX.md`
- ⚙️ **ESCENARIO-002 OFF Ronda 5: sesión libre mejora genérica sin objetivo** `BAGO-CHG-051` *minor* — `NOTAS_MEJORAS_GENERALES.md`
- ⚙️ **ESCENARIO-002 ON Ronda 5: pack_dashboard.py + evaluación final del experimento** `BAGO-CHG-050` *minor* — `pack_dashboard.py`, `GUIA_OPERADOR.md`, `EVAL-ESCENARIO002-FINAL.md`
- ⚙️ **ESCENARIO-002 OFF Ronda 4: sesión libre ejecutar/actualizar sin objetivo concreto** `BAGO-CHG-049` *minor* — `NOTAS_ACTUALIZACION.md`
- ⚙️ **ESCENARIO-002 ON Ronda 4: actualización metrics_snapshot e informe workflows con datos 19 sesiones** `BAGO-CHG-048` *minor* — `metrics_snapshot.json`, `INFORME_EFICACIA_WORKFLOWS.md`, `EVAL-WORKFLOWS-002.md`
- ⚙️ **ESCENARIO-002 OFF Ronda 3: notas sobre documentación sin estructura** `BAGO-CHG-047` *minor* — `NOTAS_DOCUMENTACION.md`
- ⚙️ **ESCENARIO-002 ON Ronda 3: documentación operativa esencial del pack** `BAGO-CHG-046` *minor* — `GUIA_OPERADOR.md`, `TROUBLESHOOTING.md`, `PROTOCOLO_CIERRE_SESION.md`
- ⚙️ **ESCENARIO-002 ON Ronda 2: informe eficacia workflows + evaluación** `BAGO-CHG-044` *minor* — `INFORME_EFICACIA_WORKFLOWS.md`, `EVAL-WORKFLOWS-001.md`, `metrics_snapshot.json`
- ⚙️ **ESCENARIO-002 OFF Ronda 2: sesión libre análisis sin estructura** `BAGO-CHG-045` *minor* — `OBSERVACIONES_PACK.md`
- ⚙️ **Sprint 4 · Consolidación: plantilla de auditoría, guía de mantenimiento, distribución** `BAGO-CHG-038` *minor* — `AUDITORIA_COHERENCIA.md`, `MANTENIMIENTO.md`, `BAGO_2_3_clean_sprint4_20260418_131747.zip`
- ⚙️ **ESCENARIO-002 ON Ronda 1: session_stats.py y WORKFLOWS_INDEX actualizado** `BAGO-CHG-042` *minor* — `session_stats.py`, `WORKFLOWS_INDEX.md`
- ⚙️ **ESCENARIO-002 OFF Ronda 1: sesión libre sin preflight** `BAGO-CHG-043` *minor* — `NOTAS_SESION_LIBRE.md`
- ⚙️ **ESCENARIO-002: competición .bago/on vs .bago/off — protocolo, W0 y herramienta de comparación** `BAGO-CHG-041` *minor* — `ESCENARIO-COMPETICION-BAGO.md`, `competition_report.py`, `W0_FREE_SESSION.md`
- ⚙️ **ESCENARIO-001 SES-2: sistema de producción máxima de artefactos** `BAGO-CHG-040` *minor* — `artifact_counter.py`, `GUIA_ARTEFACTOS.md`, `tpl_system_change.md`
- ⚙️ **ESCENARIO-001 SES-1: session_preflight.py — validador W7 de reglas de sesión** `BAGO-CHG-039` *minor* — `session_preflight.py`, `AGENT_START.md`, `W7_FOCO_SESION.md`
- ⚙️ **Reconciliación de inventario y referencias — intervención Vértice** `BAGO-CHG-036` *minor* — `global_state.json`, `ESTADO_BAGO_ACTUAL.md`, `repo_context.json`
- ⚙️ **Separación formal de capas de estado: pack vs. repo externo** `BAGO-CHG-037` *minor* — `03_ESTADO_BAGO.md`, `ESTADO_BAGO_ACTUAL.md`, `repo_context.json`
- ⚙️ **Consolidación oficial limpia en directorio dedicado** `BAGO-CHG-035` *minor* — ``, `global_state.json`, `SES-CONSOL-2026-04-15-001.json`
- ⚙️ **Alta de plantilla de evaluación brutal y enlace en guía de auditoría** `BAGO-CHG-033` *minor* — `plantilla_evaluacion_brutal.md`, `GUIA_DE_AUDITORIA.md`
- 🏛 **ZIP de despliegue rápido bago-deploy.zip** `BAGO-CHG-032` *minor* — `bago-deploy.zip`
- ⚙️ **Auditoría y corrección de documentos institucionales BAGO** `BAGO-CHG-031` *minor* — `DOCUMENTO_FORMAL_SISTEMA_BAGO.md`, `MANUAL INSTITUCIONAL DEL SISTEMA BAGO.md`
- 🏛 **Ecosistema de instaladores cross-platform y reorganización en dist/** `BAGO-CHG-030` *minor*
- ⚙️ **Actualización documental de resultados recientes y presets operativos de performance** `BAGO-CHG-028` *minor*
- ⚙️ **Validación automática de coherencia entre family declarada y carpeta física de roles** `BAGO-CHG-027` *minor*
- ⚙️ **Realineación física de roles de supervisión fuera de gobierno** `BAGO-CHG-026` *minor*
- ⚙️ **Endurecimiento estructural del estado nativo y de sus validaciones** `BAGO-CHG-025` *minor*
- ⚙️ **Oficialización de BAGO AMTEC V2.2.1 como baseline de referencia** `BAGO-CHG-024` *minor*
- 🏛 **Consolidación 2.2.1 del híbrido: integración repo-first en el núcleo** `BAGO-CHG-023` *minor*
- 🏛 **Síntesis híbrida v2.2: canon fuerte + repo-first + fábrica de prompts + pedagogía estructural** `BAGO-CHG-022` *minor*
- 🔄 **Normalización final de la migración histórica v1 -> línea canónica previa** `BAGO-CHG-MIG-001` *minor*
