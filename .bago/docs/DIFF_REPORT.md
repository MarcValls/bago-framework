# BAGO DIFF REPORT
> Generado: 2026-04-22 · AGENTE DIFFER v1.0
> Directorio: `/Users/INTELIA_Manager/Desktop/BAGO_CAJAFISICA`

---

## Estado general

> ⚠️ **Issues menores** — routing con 4 tools faltantes + 5 instancias de `utcnow()` deprecado + 1 inconsistencia de ID en CHG-077. Nada crítico en runtime actual, pero los comandos `scan`, `hotspot`, `fix`, `gh` fallarán si se invocan.

---

## 1. Resumen de cambios Git

### Último commit (HEAD)
```
ea54a82 Merge pull request #43 — feat: bago start/status + menu.html Quick Start
```

**Archivos modificados en HEAD~1 → HEAD (5 ficheros, +734 líneas):**

| Archivo | +/- |
|---|---|
| `.bago/tools/bago_start.py` | +195 (nuevo) |
| `.bago/tools/quick_status.py` | +146 (nuevo) |
| `README.md` | +176 |
| `bago` | +44 / -9 |
| `menu.html` | +182 (nuevo) |

### Working tree (no commiteado)
**42 archivos modificados — 3048 inserciones / 562 eliminaciones.** Los más relevantes:

| Archivo | Cambio |
|---|---|
| `bago-viewer/templates/orchestrator.html` | +609 / -... |
| `bago-viewer/app.py` | +498 |
| `.bago/tools/emit_ideas.py` | +400 |
| `.bago/docs/analysis/BAGO_EVOLUCION_SISTEMA.html` | +339 |
| `bago` | +225 |
| `.bago/state/ESTADO_BAGO_ACTUAL.md` | +161 |
| `.bago/tools/bago_banner.py` | +102 |
| `.bago/CHECKSUMS.sha256` | +155 |

**Archivos nuevos sin trackear (selección relevante):**
- `.bago/tools/` — 40+ tools nuevos (ver sección 3)
- `.bago/state/changes/BAGO-CHG-059..077.json` — 19 CHGs nuevos
- `.bago/state/evidences/BAGO-EVD-060..070.json`
- `.bago/state/sessions/SES-HARVEST-*.json`, `SES-W1-*.json`, `SES-W7-*.json`
- `.bago/state/snapshots/`, `.bago/state/sprints/`, `.bago/state/goals/`

### Snapshot diff (`bago diff`)
```
BAGO Diff — vs SNAP-20260422_000017
  Cambios: +3 -0 ~3  (6 total)

  + state/changes/BAGO-CHG-077.json
  + state/notes/NOTE-001.json
  + state/snapshots/SNAP-20260422_000017.zip
  ~ state/ESTADO_BAGO_ACTUAL.md
  ~ state/global_state.json
  ~ state/repo_context.json
```

---

## 2. Tabla de consistencia: routing `bago` ↔ archivos en `.bago/tools/`

### 2a. Tools referenciados en `bago` → estado en disco

| Comando | Tool file | Estado |
|---|---|---|
| `bago start` | `bago_start.py` | ✅ |
| `bago ideas` | `emit_ideas.py` | ✅ |
| `bago session` | `session_opener.py` | ✅ |
| `bago status` | `quick_status.py` | ✅ |
| `bago on` | `bago_on.py` | ✅ |
| `bago dashboard` | `pack_dashboard.py` | ✅ |
| `bago debug` | `bago_debug.py` | ✅ |
| `bago cosecha` | `cosecha.py` | ✅ |
| `bago detector` | `context_detector.py` | ✅ |
| `bago validate` | `validate_pack.py` | ✅ |
| `bago health` | `health_score.py` | ✅ |
| `bago audit` | `audit_v2.py` | ✅ |
| `bago workflow` | `workflow_selector.py` | ✅ |
| `bago stale` | `stale_detector.py` | ✅ |
| `bago v2` | `v2_close_checklist.py` | ✅ |
| `bago task` | `show_task.py` | ✅ |
| `bago stability` | `stability_summary.py` | ✅ |
| `bago efficiency` | `efficiency_meter.py` | ✅ |
| `bago auto` | `auto_mode.py` | ✅ |
| `bago map` | `context_map.py` | ✅ |
| `bago recolecta` | `context_collector.py` | ✅ |
| `bago chat` | `bago_chat_server.py` | ✅ |
| `bago repo-on` | `repo_on.py` | ✅ |
| `bago repo-debug` | `bago_debug.py` | ✅ |
| `bago repo-lint` | `repo_runner.py` | ✅ |
| `bago repo-test` | `repo_runner.py` | ✅ |
| `bago repo-build` | `repo_runner.py` | ✅ |
| `bago search` | `bago_search.py` | ✅ |
| `bago archive` | `archive.py` | ✅ |
| `bago compare` | `compare.py` | ✅ |
| `bago config` | `config.py` | ✅ |
| `bago changelog` | `changelog.py` | ✅ |
| `bago check` | `check.py` | ✅ |
| `bago diff` | `diff.py` | ✅ |
| `bago doctor` | `doctor.py` | ✅ |
| `bago export` | `export.py` | ✅ |
| `bago flow` | `flow.py` | ✅ |
| `bago git` | `git_context.py` | ✅ |
| `bago goals` | `goals.py` | ✅ |
| `bago habit` | `habit.py` | ✅ |
| `bago insights` | `insights.py` | ✅ |
| `bago lint` | `lint.py` | ✅ |
| `bago metrics` | `metrics_trends.py` | ✅ |
| `bago notes` | `notes.py` | ✅ |
| `bago patch` | `patch.py` | ✅ |
| `bago remind` | `remind.py` | ✅ |
| `bago report` | `report_generator.py` | ✅ |
| `bago review` | `review.py` | ✅ |
| `bago session-details` | `session_details.py` | ✅ |
| `bago snapshot` | `snapshot.py` | ✅ |
| `bago sprint` | `sprint_manager.py` | ✅ |
| `bago stats` | `stats.py` | ✅ |
| `bago summary` | `summary.py` | ✅ |
| `bago tags` | `tags.py` | ✅ |
| `bago template` | `template.py` | ✅ |
| `bago timeline` | `timeline.py` | ✅ |
| `bago velocity` | `velocity.py` | ✅ |
| `bago watch` | `watch.py` | ✅ |
| `bago integration-tests` | `integration_tests.py` | ✅ |
| **`bago scan`** | **`scan.py`** | **❌ MISSING** |
| **`bago hotspot`** | **`hotspot.py`** | **❌ MISSING** |
| **`bago fix`** | **`autofix.py`** | **❌ MISSING** |
| **`bago gh`** | **`gh_integration.py`** | **❌ MISSING** |

### 2b. Tools en disco SIN entrada en el routing `bago`

Estos archivos existen en `.bago/tools/` pero no son accesibles via `bago <cmd>`. Son llamados internamente o son herramientas legadas:

| Tool file | Tipo |
|---|---|
| `artifact_counter.py` | ⚠️ interno / legado |
| `competition_report.py` | ⚠️ interno / legado |
| `dashboard_v2.py` | ⚠️ legado (reemplazado por `pack_dashboard.py`) |
| `generate_bago_evolution_report.py` | ⚠️ interno |
| `generate_task_closure.py` | ⚠️ interno |
| `inspect_workflow.py` | ⚠️ interno |
| `personality_panel.py` | ⚠️ legado |
| `reconcile_state.py` | ⚠️ interno |
| `session_preflight.py` | ⚠️ interno (llamado por `session_opener.py`) |
| `session_stats.py` | ⚠️ legado |
| `state_store.py` | ⚠️ librería compartida (no es tool directo) |
| `target_selector.py` | ⚠️ interno |
| `validate_manifest.py` | ⚠️ interno |
| `validate_state.py` | ⚠️ interno |
| `vertice_activator.py` | ⚠️ interno |

> **Nota:** `state_store.py` es una librería de abstracción, no un CLI tool — es correcto que no esté en el routing.

---

## 3. Drift CHG registrados ↔ tools implementados

### Resumen
- **Total CHG files**: 58 BAGO-CHG numerados (021–077) + 1 MIG + 2 CHG-0xx (010, 011) + 2 .md (012, 013)
- **Rango cubierto**: CHG-021 a CHG-077
- **CHG-001 a CHG-020**: ausentes en disco (migrados o pre-históricos)

### Hallazgos de drift

| Issue | Detalle |
|---|---|
| ⚠️ `BAGO-CHG-077.json` ID interno incorrecto | El archivo se llama `BAGO-CHG-077.json` pero su campo `change_id` dice `"BAGO-CHG-002"` — probable copy-paste al crear el CHG |
| ⚠️ CHG-069..077 sin campo `tool` | Usan `affected_components` en lugar de `tool` (cambio de schema en Sprint 180) |
| ✅ CHG-077 referencia `velocity.py`, `patch.py`, `notes.py`, `template.py` | Todos existen en disco |
| ✅ CHG-076 referencia `stats.py`, `remind.py`, `habit.py`, `review.py` | Todos existen en disco |
| ❌ `scan.py`, `hotspot.py`, `autofix.py`, `gh_integration.py` | En routing pero sin CHG que documente su creación y sin archivo en disco |

### Tools sin CHG asociado (nueva generación Sprint 180)
Los siguientes tools fueron creados en el Sprint 180 pero no tienen CHG individual propio (están agrupados en CHG-059..077):

`archive.py`, `bago_search.py`, `changelog.py`, `check.py`, `compare.py`, `config.py`, `diff.py`, `doctor.py`, `export.py`, `flow.py`, `git_context.py`, `goals.py`, `habit.py`, `insights.py`, `integration_tests.py`, `lint.py`, `metrics_trends.py`, `notes.py`, `patch.py`, `remind.py`, `report_generator.py`, `review.py`, `session_details.py`, `snapshot.py`, `sprint_manager.py`, `stats.py`, `summary.py`, `tags.py`, `template.py`, `timeline.py`, `velocity.py`, `watch.py`

> Esto es esperado — el Sprint 180 registró múltiples tools por CHG agrupado.

---

## 4. Patch set — correcciones menores

### PST-001: `datetime.datetime.utcnow()` → `datetime.datetime.now(datetime.UTC)`

`utcnow()` está deprecado desde Python 3.12. Las 5 instancias detectadas:

---

**PATCH PST-001-A**
```
FILE: .bago/tools/patch.py  (línea 52)
OLD:             data["updated_at"] = datetime.datetime.utcnow().isoformat() + "Z"
NEW:             data["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
REASON: datetime.utcnow() deprecated en Python 3.12 — produce DeprecationWarning
```

**PATCH PST-001-B**
```
FILE: .bago/tools/patch.py  (línea 77)
OLD:             data["updated_at"] = datetime.datetime.utcnow().isoformat() + "Z"
NEW:             data["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
REASON: mismo que PST-001-A
```

**PATCH PST-001-C**
```
FILE: .bago/tools/patch.py  (línea 99)
OLD:             data["updated_at"] = datetime.datetime.utcnow().isoformat() + "Z"
NEW:             data["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
REASON: mismo que PST-001-A
```

**PATCH PST-001-D**
```
FILE: .bago/tools/notes.py  (línea 69)
OLD:         "created_at": datetime.datetime.utcnow().isoformat() + "Z",
NEW:         "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
REASON: datetime.utcnow() deprecated en Python 3.12
```

**PATCH PST-001-E**
```
FILE: .bago/tools/template.py  (línea 154)
OLD:     now = datetime.datetime.utcnow().isoformat() + "Z"
NEW:     now = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
REASON: datetime.utcnow() deprecated en Python 3.12
```

---

### PST-002: Inconsistencia `change_id` en BAGO-CHG-077.json

```
FILE: .bago/state/changes/BAGO-CHG-077.json
OLD:   "change_id": "BAGO-CHG-002",
NEW:   "change_id": "BAGO-CHG-077",
REASON: El archivo se llama BAGO-CHG-077.json pero el campo interno dice BAGO-CHG-002
        (probable copy-paste al crear el CHG). Causa inconsistencia en bago check/audit.
```

---

### PST-003 (informativo): Commands en `bago` sin tool en disco

Los comandos `scan`, `hotspot`, `fix`, `gh` están declarados en el routing pero sus tools no existen.
Actualmente fallan con `FileNotFoundError` si se invocan.

**Opciones**:
1. Crear los stubs `scan.py`, `hotspot.py`, `autofix.py`, `gh_integration.py` (mínimos con `--help`)
2. Eliminar las entradas del routing hasta que se implementen

> No se genera patch automático — requiere decisión de diseño.

---

## 5. Tabla resumen

| Categoría | Estado | Detalle |
|---|---|---|
| Git commits | ✅ | HEAD limpio, merge PR #43 aplicado |
| Working tree | ⚠️ | 42 archivos modificados sin commitear |
| Routing → disco | ⚠️ | 4 tools en routing sin archivo (`scan`, `hotspot`, `autofix`, `gh_integration`) |
| Disco → routing | ⚠️ | 15 tools en disco sin ruta pública (mayormente internos/legados, aceptable) |
| CHG integridad | ⚠️ | CHG-077 tiene `change_id` incorrecto (`BAGO-CHG-002`) |
| utcnow() | ⚠️ | 5 instancias en `patch.py`, `notes.py`, `template.py` |
| Snapshot diff | ✅ | +3 nuevos, ~3 modificados desde último snapshot |
| Tools CHG cobertura | ✅ | Todos los tools referenciados en CHG recientes existen en disco |

---

## 6. Acciones recomendadas (por prioridad)

| # | Acción | Urgencia |
|---|---|---|
| 1 | Aplicar PST-001 (A–E): reemplazar `utcnow()` | Media |
| 2 | Aplicar PST-002: corregir `change_id` en CHG-077 | Baja |
| 3 | Decidir qué hacer con `scan`, `hotspot`, `fix`, `gh` (stubs o eliminar) | Media |
| 4 | Commitear los cambios del working tree | Alta |

---

*DIFF_REPORT generado por AGENTE DIFFER — BAGO Framework*
