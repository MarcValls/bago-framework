# BAGO Tools Index — 135 herramientas

> Generado automáticamente el 2026-04-23. Fuente: `.bago/tools/*.py`

| # | Tool | Descripción |
|---|------|-------------|
| 95 | `install_deps.py` | Auto-instalador de dependencias opcionales de BAGO. |
| 96 | `rule_catalog.py` | Catálogo de reglas BAGO-* y JS-*. |
| 97 | `lint_report.py` | Generador de informe Markdown de resultados de bago-lint. |
| 98 | `config_check.py` | Validador de pack.json contra esquema BAGO. |
| 99 | `ci_baseline.py` | Gestión de baselines de findings para CI. |
| 100 | `health_report.py` | (milestone): Reporte integral de salud del proyecto. |
| 101 | `changelog_gen.py` | Generador de CHANGELOG desde git log. |
| 102 | `dead_code.py` | Detector de código muerto (Python). |
| 103 | `branch_check.py` | Validador de nombres de rama git. |
| 104 | `complexity.py` | Analizador de complejidad ciclomática (Python). |
| 105 | `env_check.py` | Verificador de variables de entorno requeridas. |
| 106 | `file_watcher.py` | Vigilante de cambios en archivos del proyecto. |
| 107 | `size_tracker.py` | Tracking de tamaño de archivos y directorio. |
| 108 | `secret_scan.py` | Escáner de secretos y credenciales hardcodeadas. |
| 109 | `test_gen.py` | Generador de tests unitarios para funciones Python. |
| 110 | `impact_map.py` | Mapa de impacto de cambios en archivos Python. |
| 111 | `doc_coverage.py` | Cobertura de docstrings en módulos Python. |
| 112 | `chart_engine.py` | Motor de gráficas interactivas con Chart.js. |
| 113 | `duplicate_check.py` | Detector de código duplicado. |
| 114 | `pre_commit_gen.py` | Generador de .pre-commit-config.yaml. |
| 115 | `metrics_export.py` | Exporta métricas BAGO como JSON/Prometheus. |
| 116 | `code_review.py` | Reporte CI agregado de todos los scanners BAGO. |
| 117 | `refactor_suggest.py` | Sugerencias concretas de refactorización. |
| 118 | `api_check.py` | Validador de estructura REST API. |
| 119 | `coverage_gate.py` | Quality gate de cobertura de tests. |
| 120 | `naming_check.py` | Validador de convenciones de nombres. |
| 121 | `type_check.py` | Validador de type hints Python. |
| 122 | `license_check.py` | Validador de cabeceras de licencia/copyright. |
| 123 | `dep_audit.py` | Auditoría de seguridad de dependencias Python. |
| 124 | `readme_check.py` | Validador de estructura de README.md. |
| 125 | `ci_report.py` | Reporte CI unificado listo para PRs. |
| 125 | `tool_guardian.py` | Guardian de coherencia del framework BAGO. |
| 126 | `pre_push_guard.py` | Guardián pre-commit/pre-push de BAGO. |
| — | `archive.py` | — |
| — | `artifact_counter.py` | — |
| — | `audit_v2.py` | — |
| — | `auto_heal.py` | auto_heal.py — BAGO detecta sus propios problemas y se repara solo. |
| — | `auto_mode.py` | Combina repo_context.json (actual) + nodos de context_map.json (recientes). |
| — | `auto_register.py` | auto_register.py — Registro automático de nuevos tools en el framework BAGO. |
| — | `autofix.py` | Run --test on the tool after fixing. Returns (passed: bool, output: str). |
| — | `bago_ask.py` | Load all searchable documents from BAGO state. |
| — | `bago_banner.py` | Elimina secuencias ANSI para medir la anchura visible. |
| — | `bago_chat_server.py` | Eres BAGO, agente de gobernanza técnica v2.5-stable. \ |
| — | `bago_config.py` | bago_config.py — Configuración centralizada compartida entre todos los tools BAGO. |
| — | `bago_debug.py` | — |
| — | `bago_lint_cli.py` | Apply autofixable patches in-place. Returns {applied, failed, skipped}. |
| — | `bago_on.py` | — |
| — | `bago_search.py` | Retorna True si todos los terminos estan en el texto (case insensitive). |
| — | `bago_start.py` | Llama al selector de workspace antes de mostrar el menú principal. |
| — | `bago_utils.py` | Print summary and return exit code. Call at end of --test block. |
| — | `bago_watch.py` | Returns {path: sha256} for all JSON files in dirs. |
| — | `changelog.py` | Carga todos los cambios BAGO-CHG-*.json. |
| — | `check.py` | Returns (passed: bool, detail: str) |
| — | `ci_generator.py` | \ |
| — | `commit_readiness.py` | commit_readiness.py — Evaluación rápida de preparación para commit. |
| — | `compare.py` | Parse 'YYYY-MM-DD..YYYY-MM-DD' into (start, end). |
| — | `competition_report.py` | Solo sesiones cerradas del ESCENARIO-002. |
| — | `config.py` | — |
| — | `context_collector.py` | — |
| — | `context_detector.py` | Ficheros modificados en el repo desde el último commit. |
| — | `context_map.py` | True si algún ancestro del directorio es ya un .bago/ |
| — | `contracts.py` | Run bago test and verify passing count >= min. |
| — | `cosecha.py` | Devuelve el siguiente ID disponible para CHG o EVD. |
| — | `dashboard_v2.py` | Devuelve (avg_roles, avg_artifacts, avg_decisions) últimas 10 sesiones. |
| — | `debt_ledger.py` | Load second-latest scan for trend comparison. Returns (FindingsDB|None, hours|None). |
| — | `diff.py` | Returns {arcname: md5hex} for all state/ files in the zip. |
| — | `doctor.py` | Verifica que todos los scripts Python tienen sintaxis valida. |
| — | `efficiency_meter.py` | Extrae las claves del dict COMMANDS del script bago. |
| — | `emit_ideas.py` | Run validate_pack + validate_state and check smoke if available. |
| — | `export.py` | Exporta sesiones a CSV. |
| — | `findings_engine.py` | Parse bandit JSON output. |
| — | `flow.py` | Returns {W_CODE: path} mapping. |
| — | `generate_bago_evolution_report.py` | <svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {h... |
| — | `generate_task_closure.py` | — |
| — | `gh_integration.py` | Returns 'owner/repo' string or None. |
| — | `git_context.py` | Ejecuta git y retorna stdout. Retorna '' en caso de error. |
| — | `goals.py` | — |
| — | `habit.py` | — |
| — | `health_score.py` | validate_pack GO = 25, KO = 0. |
| — | `hotspot.py` | Returns {filepath: commit_count} for all source files under target_dir. |
| — | `impact_engine.py` | € cost of carrying debt for one quarter (interest model: 15% per quarter). |
| — | `insights.py` | — |
| — | `inspect_workflow.py` | — |
| — | `integration_tests.py` | Ejecuta un tool Python y retorna (returncode, stdout, stderr). |
| — | `intent_router.py` | intent_router.py — Interpreta lenguaje natural y ejecuta los tools BAGO correctos. |
| — | `iteration_logger.py` | Registra una iteración de trabajo y la persiste en JSON. |
| — | `legacy_fixer.py` | legacy_fixer.py — Auto-scaffolding de --test en tools BAGO legacy. |
| — | `lint.py` | — |
| — | `metrics_dashboard.py` | <!DOCTYPE html> |
| — | `metrics_trends.py` | Agrupa sesiones por semana ISO. Retorna dict week_str -> list. |
| — | `multi_scan.py` | Return all languages present in target (not just the dominant one). |
| — | `notes.py` | — |
| — | `orchestrator.py` | orchestrator.py — Orquestador de workflows BAGO multi-tool. |
| — | `pack_dashboard.py` | Semicírculo ASCII de salud. |
| — | `patch.py` | Sesiones con status 'completed' → 'closed'. |
| — | `permission_check.py` | Return list of (Path, description) that should be executable. |
| — | `permission_fixer.py` | Return True if the current user owns the file. |
| — | `personality_panel.py` | — |
| — | `quick_status.py` | — |
| — | `reconcile_state.py` | Cuenta archivos en carpeta, excluyendo README.md. |
| — | `remind.py` | Muestra recordatorios vencidos o urgentes al inicio. |
| — | `repo_context_guard.py` | Return 'self' if BAGO is operating in its own host directory (no external project), |
| — | `repo_on.py` | — |
| — | `repo_runner.py` | Return True when subprocess output indicates the executable was not found. |
| — | `report_generator.py` | — |
| — | `review.py` | — |
| — | `risk_matrix.py` | Returns (category, probability, impact, consequence). |
| — | `scan.py` | Auto-detect dominant language from file extensions and manifests in target. |
| — | `session_details.py` | Detailed breakdown of a single session. |
| — | `session_opener.py` | — |
| — | `session_preflight.py` | — |
| — | `session_stats.py` | — |
| — | `show_task.py` | Añade el título de la idea a implemented_ideas.json. |
| — | `snapshot.py` | Generate snapshot index from zip contents. |
| — | `sprint_manager.py` | API programatica: anade artefacto a sprint activo/especificado. |
| — | `stability_summary.py` | Returns (status, output) where status is 'GO' or 'KO'. |
| — | `stale_detector.py` | Escenarios en active_scenarios con archivo EVAL- en state/scenarios/ → contradicción. |
| — | `state_store.py` | Error base de StateStore. |
| — | `stats.py` | Genera un sparkline ASCII de 8 posiciones. |
| — | `summary.py` | — |
| — | `tags.py` | Auto-suggest tags from session content. |
| — | `target_selector.py` | Descubre candidatos de proyecto priorizando el contexto operativo. |
| — | `template.py` | Crear plantilla custom desde stdin. |
| — | `testgen.py` | Returns 'func(arg1, arg2)' string from AST node. |
| — | `timeline.py` | Parsea YYYY-MM-DD o ISO datetime. |
| — | `tool_search.py` | tool_search.py — Busca el tool BAGO correcto para un problema dado. |
| — | `v2_close_checklist.py` | Ejecuta un script y devuelve (returncode, stdout). |
| — | `validate_manifest.py` | — |
| — | `validate_pack.py` | — |
| — | `validate_state.py` | — |
| — | `velocity.py` | — |
| — | `vertice_activator.py` | Carga todas las sesiones cerradas ordenadas por fecha. |
| — | `watch.py` | Retorna archivos en state/ modificados en los últimos N segundos. |
| — | `workflow_selector.py` | Pregunta sí/no, devuelve True si sí. |
| — | `workspace_selector.py` | Devuelve descripción legible del workspace activo. |

---

## Categorías

| Rango | Categoría |
|-------|-----------|
| #1–50 | Herramientas base de análisis y reporting |
| #51–100 | Herramientas de gobernanza, CI y calidad |
| #101–135 | Herramientas de inteligencia, orquestación y sprint |

## Uso

```bash
# Listar comandos disponibles
bago

# Buscar tool por nombre
bago search <keyword>

# Ver estado de registro de todos los tools
python3 .bago/tools/auto_register.py --check-all
```