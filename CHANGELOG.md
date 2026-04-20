# CHANGELOG

All notable changes to BAGO are documented here.
Format: `[version] — date · summary · efficiency index`

---

## [2.5-stable · post-release patches] — 2026-04-20

### Summary
Governance hardening and launcher UX fix applied on top of 2.5-stable. Fully backward-compatible.

### Governance hardening (PRs #17–#22)
- `docs/governance/REGLA_INMUTABILIDAD_VALIDACION.md` — formal rule: `validate_*` commands are side-effect free; `sync_*` are the only ones allowed to write
- `make check-pure` — local validation purity check (mirrors CI)
- `.github/workflows/validation-purity.yml` — CI enforces that `validate` and `health` leave no diff in the working tree
- `bago` launcher: skip `_auto_sync()` for `validate` and `health` commands — state/ remains fully untouched
- `tools/check_validate_purity.py` — static checker for write ops inside `validate_*.py` files
- Documentation fully synchronized: all references to "validate regenerates checksums/TREE" replaced with correct behavior (`bago sync`)

### Launcher UX fix (PR #23)
- First-run `[2] Iniciar proyecto nuevo` now shows a numbered list of candidate project directories (terminal CWD + parent folders of the framework)
- Never silently defaults to the framework directory itself
- Requires explicit `[s]` confirmation if the user selects the framework directory anyway
- New helper `_candidate_dirs()` in the launcher

---

## [2.5-stable] — 2026-04-19 · Efficiency Index: 100/100

### Summary
First fully stable release with complete self-evolution chain, task lifecycle, and efficiency measurement. Built using BAGO itself across 40+ registered changes.

### New CLI Commands
- `python3 bago efficiency` — Cross-version efficiency metrics with weighted index
- `python3 bago task` — Active task management (start, done, clear)
- `python3 bago stability` — Full stability report (smoke + VM + soak + validators)
- `python3 bago session` — Session opener with context bootstrapping

### New Tools (11 added)
- `audit_v2.py` — Full session audit trail
- `dashboard_v2.py` — System overview dashboard
- `efficiency_meter.py` — Inter-version efficiency comparison
- `health_score.py` — Composite health score (0–100) across 5 dimensions
- `reconcile_state.py` — State ↔ reality reconciliation
- `session_opener.py` — Structured session bootstrap
- `show_task.py` — Task viewer and lifecycle manager
- `stale_detector.py` — Detects stale tasks (>3 days)
- `v2_close_checklist.py` — Session closure checklist
- `vertice_activator.py` — Vértice role activation
- `workflow_selector.py` — Context-aware workflow selection

### Implemented Ideas (9 registered)
1. Handoff automático idea → W2
2. Resumen único de estabilidad
3. Gate canónico de validación
4. Opener de sesión desde task
5. Banner muestra task activa
6. Registro de ideas implementadas
7. Ideas baseline documentation
8. Alinear README con selector
9. Medidor de eficiencia inter-versiones

### Metrics
| Metric | Value |
|---|---|
| CLI Commands | 13 |
| Tools | 30 |
| Docs | 74 |
| Workflows | 12 |
| Registered CHGs | 40 |
| Efficiency Index | 100/100 |
| Health Score | 100/100 |

---

## [2.4-v2rc] — 2026-04-18 · Efficiency Index: 89.3/100

### Summary
Dynamic BAGO release introducing the v2 bootstrap prompt (template seed), role activation system, and expanded toolset. Introduced session-level governance and first structured task management.

### New Features
- Bootstrap prompt: first run asks whether to evolve framework or start new project
- v2 close checklist for session closure discipline
- Vértice role for sensitive change review
- Reconcile state tool for inventory validation
- Session opener with structured context

### New Tools (8 added vs 2.3)
`audit_v2.py` · `dashboard_v2.py` · `health_score.py` · `reconcile_state.py` · `session_opener.py` · `show_task.py` · `stale_detector.py` · `v2_close_checklist.py` · `vertice_activator.py` · `workflow_selector.py`

### Metrics
| Metric | Value |
|---|---|
| CLI Commands | 10 |
| Tools | 27 |
| Docs | 73 |
| Workflows | 12 |
| Efficiency Index | 89.3/100 |

---

## [2.3-clean] — 2026-04-18 · Efficiency Index: 78.6/100 *(baseline)*

### Summary
Clean baseline release. Establishes the core BAGO operational layer: 10 workflows, fundamental tools, and the three-validator system (manifest + state + pack).

### Core capabilities
- 10 CLI commands via `python3 bago`
- 3 validators: `validate_manifest.py`, `validate_state.py`, `validate_pack.py`
- 12 structured workflows (W0–W9 + WORKFLOW_MAESTRO + WORKFLOWS_INDEX)
- Session lifecycle: open → work → cosecha → close
- Ideas system with scored selector
- Health monitoring via `bago health`
- Context drift detection

### Metrics
| Metric | Value |
|---|---|
| CLI Commands | 10 |
| Tools | 19 |
| Docs | 68 |
| Workflows | 12 |
| Efficiency Index | 78.6/100 |

---

*Growth summary: 2.3 → 2.5 = +27.2% efficiency · +3 CLI commands · +11 tools · +6 docs*
