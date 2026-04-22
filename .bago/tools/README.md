# tools

Esta carpeta contiene **90 herramientas** Python del framework BAGO.

> **Inventario completo:** ver `.bago/docs/tools/` (31 archivos de documentación individual).
> **Referencia rápida:** ver `.bago/docs/BAGO_REFERENCIA_COMPLETA.md`.
> **Tests:** `python3 .bago/tools/integration_tests.py` → 55/55 ALL PASS.

## Herramientas por categoría (90 total)

### Validación y salud del pack
- `validate_manifest.py` — Integridad y esquema de `pack.json`
- `validate_state.py` — Coherencia del estado (sessions/changes/evidences)
- `validate_pack.py` — Verificación compuesta (TREE.txt, CHECKSUMS, refs)
- `health_score.py` — Score 0-100 con 5 dimensiones
- `doctor.py` — Diagnóstico integral del pack
- `lint.py` — Linter de calidad del pack (0 errores)
- `reconcile_state.py` — Reconcilia inventario disco vs estado (`--fix`)
- `audit_v2.py` — Auditoría integral en un comando (`bago audit`)
- `stale_detector.py` — Detector de reporting stale (WARN/ERROR)
- `v2_close_checklist.py` — Checklist GO/KO de cierre V2
- `contracts.py` — Contratos de estado verificables con deadline y auditoría

### Análisis estático y calidad de código
- `scan.py` — Análisis estático multi-linter con hallazgos unificados
- `hotspot.py` — Hotspots: archivos con más cambios + fallos + complejidad
- `autofix.py` — Autofix con generación y aplicación de parches validados
- `findings_engine.py` — Motor de hallazgos: parsing linters, modelo canónico Finding
- `risk_matrix.py` — Matriz de riesgo cuantificada (Security/Reliability/Maintainability)
- `debt_ledger.py` — Ledger de deuda técnica en horas y € (cuadrantes Reckless/Prudent)
- `impact_engine.py` — Impacto de negocio: velocidad, €/trimestre
- `patch.py` — Corrección automática de inconsistencias (3 parches)

### Integración GitHub y CI
- `gh_integration.py` — Check runs y comentarios en PRs GitHub
- `ci_generator.py` — Generación GitHub Actions + GitLab CI + pre-commit hook
- `git_context.py` — Contexto git (branch/log/autores) + inject

### Gestión de sesiones y estado
- `bago_on.py` — Activa explícitamente el modo BAGO sobre el host
- `bago_start.py` — Menú interactivo con selector de workspace
- `session_opener.py` — Abre sesión W2 con preflight desde handoff
- `session_preflight.py` — Preflight W7: verifica ESCENARIO-001 antes de sesión
- `session_details.py` — Top sesiones por producción (alias: `ss`)
- `session_stats.py` — Estadísticas agregadas de sesiones por tipo/workflow/rol
- `show_task.py` — Muestra y gestiona la tarea W2 registrada
- `generate_task_closure.py` — Cierre automático de tareas W2
- `quick_status.py` — Estado rápido del proyecto

### Sprints, objetivos y planificación
- `sprint_manager.py` — Gestión de sprints SPRINT-NNN.json
- `goals.py` — Gestión de objetivos con link/close/progress
- `timeline.py` — Timeline ASCII semanal con workflows
- `velocity.py` — Métricas de velocidad por período con sparklines y proyección
- `metrics_trends.py` — Tendencias rolling + sparklines ASCII
- `efficiency_meter.py` — Compara métricas entre cleanversions

### Dashboards y visualización
- `pack_dashboard.py` — Dashboard v2 cockpit con health ring, inventory, risks
- `dashboard_v2.py` — Dashboard con semáforos + KPIs V2
- `flow.py` — Flowchart ASCII de pipelines W0-W9
- `stats.py` — Dashboard agregado con sparklines de actividad
- `stability_summary.py` — Resume informes sandbox (smoke/VM/soak) y validadores
- `insights.py` — Motor de insights automáticos (5 categorías)

### Reporting y exportación
- `report_generator.py` — Reportes Markdown con filtros temporales
- `export.py` — HTML dark-theme + CSV con SVG chart
- `snapshot.py` — ZIP point-in-time de state/
- `diff.py` — Delta de state/ vs último snapshot
- `compare.py` — Comparativa wf/periodo/rol lado a lado
- `summary.py` — Resumen ejecutivo Markdown de sesión/sprint
- `review.py` — Informe de revisión periódica Markdown
- `changelog.py` — CHANGELOG desde BAGO-CHG-*.json (Keep a Changelog)

### Búsqueda y contexto
- `bago_ask.py` — Búsqueda en lenguaje natural sobre 166 docs BAGO
- `bago_search.py` — Full-text search sobre sessions/changes
- `context_detector.py` — Detector de contexto acumulado
- `context_collector.py` — Recolecta y resume contexto de directorios
- `context_map.py` — Mapa de contexto distribuido: descubre instalaciones `.bago/`
- `state_store.py` — Capa de abstracción de almacenamiento

### Notas, etiquetas y recordatorios
- `notes.py` — Notas ligeras por sesión: add/list/show/delete/search
- `tags.py` — Etiquetado con índice y búsqueda rápida
- `remind.py` — Recordatorios con due-date y sprint_ref
- `template.py` — Plantillas para nuevas sesiones (4 built-in + custom)
- `habit.py` — Detector de hábitos positivos/mejora/patrones

### Monitorización y watch
- `watch.py` — Monitor en tiempo real del estado BAGO
- `bago_watch.py` — Monitor de estado con polling SHA256 y health check
- `bago_debug.py` — Debug del pack y del repo externo

### Generación de tests y CI
- `integration_tests.py` — Suite de integración (55/55 tests — todos los tools)
- `testgen.py` — Generación de tests Python, Go y Rust
- `inspect_workflow.py` — Inspección de workflows BAGO

### Selección y configuración
- `workspace_selector.py` — Selector de workspace (framework/padre/ruta externa)
- `workflow_selector.py` — Selector interactivo W0/W7/W8/W9
- `target_selector.py` — Selección segura de directorio objetivo
- `config.py` — Gestión de configuración del pack.json con validación de tipos
- `personality_panel.py` — Panel de personalidad, idioma y vocabulario contextual

### Gobernanza y trazabilidad
- `cosecha.py` — Protocolo W9 de cosecha contextual
- `archive.py` — Archivado de sesiones cerradas antiguas
- `iteration_logger.py` — Registra silenciosamente invocaciones de comandos
- `artifact_counter.py` — Producción de artefactos útiles por sesión
- `vertice_activator.py` — Evaluador de señales para activar revisión Vértice
- `emit_ideas.py` — Lista ideas priorizadas con scoring dinámico
- `competition_report.py` — Comparativa bago/on vs bago/off
- `repo_context_guard.py` — Guard de contexto: detecta match/mismatch/new al cambiar de repo
- `repo_on.py` — Activa BAGO sobre un repo externo
- `repo_runner.py` — Ejecuta lint/test/build sobre el repo intervenido
- `generate_bago_evolution_report.py` — Análisis de iteraciones y evolución del sistema
- `check.py` — Checklist pre-sesión personalizable desde checklist.json

### Utilidades compartidas
- `bago_utils.py` — Utilidades: print_ok/fail/skip, runner de tests inline
- `bago_banner.py` — Banner BAGO con menú de comandos
- `bago_chat_server.py` — Servidor de chat para sesiones interactivas

- `validate_manifest.py`:
  comprueba que las rutas declaradas en `pack.json` existen,
  que no escapan fuera del pack
  y que la declaración de `workflow_bootstrap_repo_first`
  está alineada con el manifiesto.
- `validate_state.py`:
  comprueba presencia y coherencia del estado estructurado,
  workflows declarados, sesión activa o cerrada,
  inventario, referencias cruzadas
  y forma estructural de sesiones, cambios y evidencias.
- `validate_pack.py`:
  ejecuta una verificación compuesta,
  compara `TREE.txt` con el árbol real,
  verifica `CHECKSUMS.sha256`,
  detecta referencias operativas heredadas a `2.1.x`
  fuera de migración
  y comprueba que la carpeta física de cada rol
  coincide con su `family`.
- `personality_panel.py`:
  panel de configuración para personalizar estilo de personalidad,
  idioma principal y vocabulario contextual del usuario
  (incluyendo términos de círculo pequeño con significado y ejemplo).
  Soporta flujo guiado con `--flow-vocab`, usado desde `./personality-flow`.
- `repo_context_guard.py`:
  detecta si `.bago/` está operando sobre un repo distinto al contexto anterior.
  Si hay `new` o `mismatch`, obliga a arrancar por `W1/repo-first`
  para evitar bucles de estado heredado.
  En `check`, si `repo_context.json` declara un `external_repo_pointer`,
  expone ese contexto como efectivo para alinear banner y automatismos.
  En `sync`, resetea al contexto detectado real del host.
- `target_selector.py`:
  selección segura de directorio objetivo. Prioriza contexto operativo,
  baja la prioridad de rutas históricas o auxiliares (`TESTS/`, `RELEASE/`,
  `audit/`, `cleanversion/`, snapshots, backups), permite navegación con
  flechas y siempre ofrece `Ruta exacta…` como salida manual.

## Filosofía

Estas utilidades no sustituyen una auditoría humana completa,
pero sí evitan errores materiales repetitivos
y varias incoherencias canónicas de segundo nivel.

## Nota sobre checksums

`CHECKSUMS.sha256` cubre todos los archivos del pack
salvo el propio `CHECKSUMS.sha256`.
Esta exclusión es deliberada
para evitar la paradoja de autorreferencia.

## Nota específica de V2.2

Los validadores siguen centrados
en integridad canónica y coherencia del pack.
La capa repo-first y la fábrica de prompts
no cambian esa base; la hacen más usable.
Esta versión no valida semánticamente
un repositorio externo concreto:
valida que `.bago/` no se contradiga
mientras opera sobre él.

## Nota específica de V2.2.1

En esta release, los validadores además comprueban:

- coherencia entre `pack.json.version` y `state/global_state.json`,
- existencia del workflow repo-first y su declaración en el manifiesto,
- existencia de la sesión, cambio y evidencia de consolidación,
- ausencia de referencias operativas a `2.1.x` fuera de legado/migración,
- alineación entre `family` declarada en cada rol y su carpeta física bajo `roles/`.

## Herramientas de instalación (externas al pack)

Estas herramientas viven en el directorio padre de `.bago/`
y no forman parte del pack canónico, por lo que no están cubiertas
por `CHECKSUMS.sha256` ni por `TREE.txt`.
Se registran en `pack.json` bajo la clave `"installer"` a título informativo.

- `bago-make-installer.sh`:
  genera `BAGO_installer.sh` (macOS/Linux autocontenido)
  y `BAGO_installer_windows.zip` (paquete Windows).
  Ejecutar cada vez que se quiera redistribuir el pack.
- `bago-install.sh` / `bago-install.bat`:
  copia `.bago/` en un repositorio destino y valida la instalación.
  Disponible globalmente tras ejecutar el setup.
- `bago-setup.sh` / `bago-setup.bat`:
  registra el alias/comando `bago-install` de forma permanente en el PC.
  Ejecutar una sola vez por máquina.
- `BAGO_installer.sh`:
  instalador autocontenido para macOS/Linux.
  Único archivo a distribuir en entornos Unix.
- `BAGO_installer_windows.zip`:
  paquete para Windows. Extraer y ejecutar `install.bat`.
