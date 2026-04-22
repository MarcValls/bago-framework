# BAGO READER REPORT
_Generado por el Agente Lector — 2026-04-22 00:31 CEST_

---

## 1. Inventario de Tools

> **74 archivos .py** en `.bago/tools/` (72 en raíz + 2 en `perf/`).
> El archivo `findings_engine.py` **no aparece en `find` estándar** pero sí en glob `*.py` — posible atributo oculto o nombre con caracter especial; verificar con `ls -la` en el directorio.

| Archivo | LOC | Funciones | Clases | --test | Docstring módulo |
|---------|-----|-----------|--------|--------|-----------------|
| archive.py | 206 | 9 | 0 | ✅ | ✅ Archiva sesiones cerradas antiguas |
| artifact_counter.py | 139 | 5 | 0 | ❌ | ✅ Mide producción de artefactos por sesión |
| audit_v2.py | 182 | 5 | 0 | ❌ | ✅ Auditoría integral BAGO V2 |
| auto_mode.py | 441 | 16 | 0 | ❌ | ✅ Modo automático, evalúa y ejecuta pasos |
| bago_banner.py | 311 | 14 | 0 | ❌ | ✅ Banner ASCII + estado del pack |
| bago_chat_server.py | 1253 | 21 | 1 | ❌ | ✅ Chat web con Ollama |
| bago_debug.py | 538 | 21 | 0 | ❌ | ✅ Auditoría y reparación de bugs del pack |
| bago_on.py | 101 | 4 | 0 | ❌ | ✅ Activa modo BAGO sobre el host |
| bago_search.py | 324 | 13 | 0 | ✅ | ✅ Motor de búsqueda full-text |
| bago_start.py | 205 | 11 | 0 | ❌ | ✅ Menú interactivo principal |
| changelog.py | 279 | 8 | 0 | ✅ | ✅ Genera CHANGELOG desde CHG JSONs |
| check.py | 280 | 8 | 0 | ✅ | ✅ Checklist pre-sesión personalizable |
| compare.py | 260 | 12 | 0 | ✅ | ✅ Comparativa períodos/workflows/roles |
| competition_report.py | 186 | 10 | 0 | ❌ | ✅ Reporte ESCENARIO-002 W7 vs W0 |
| config.py | 232 | 11 | 0 | ✅ | ✅ Gestión de pack.json |
| context_collector.py | 277 | 8 | 0 | ❌ | ✅ Recolecta contexto de directorios |
| context_detector.py | 323 | 10 | 0 | ❌ | ✅ Detecta señales HARVEST/WATCH/CLEAN |
| context_map.py | 240 | 7 | 0 | ❌ | ✅ Mapa de instalaciones .bago/ |
| cosecha.py | 281 | 8 | 0 | ❌ | ✅ Protocolo W9: sesión harvest |
| dashboard_v2.py | 216 | 11 | 0 | ❌ | ✅ Dashboard estado V2 |
| diff.py | 248 | 10 | 0 | ✅ | ✅ Delta state/ desde último snapshot |
| doctor.py | 392 | 15 | 0 | ✅ | ✅ Diagnóstico integral del pack |
| efficiency_meter.py | 422 | 12 | 0 | ❌ | ✅ Medidor de eficiencia inter-versiones |
| emit_ideas.py | 738 | 20 | 0 | ❌ | ❌ Sin docstring de módulo |
| export.py | 411 | 11 | 0 | ✅ | ✅ Exporta sesiones a HTML/CSV |
| **findings_engine.py** | **459** | **21** | **2** | **✅** | ✅ Motor de hallazgos unificado |
| flow.py | 260 | 9 | 0 | ✅ | ✅ Flowchart ASCII de workflows |
| generate_bago_evolution_report.py | 919 | 19 | 0 | ❌ | ❌ Sin docstring de módulo |
| generate_task_closure.py | 144 | 4 | 0 | ❌ | ✅ Genera artefactos de cierre W2 |
| git_context.py | 357 | 15 | 0 | ✅ | ✅ Contexto git del repo activo |
| goals.py | 388 | 14 | 0 | ✅ | ✅ Gestor de objetivos del pack |
| habit.py | 351 | 13 | 1 | ✅ | ✅ Detector de hábitos de trabajo |
| health_score.py | 207 | 9 | 0 | ❌ | ✅ Score 0-100 de salud del pack |
| insights.py | 448 | 17 | 1 | ✅ | ✅ Motor de insights automáticos |
| inspect_workflow.py | 192 | 3 | 0 | ❌ | ❌ Sin docstring de módulo |
| integration_tests.py | 531 | 26 | 0 | ✅ | ✅ Suite de integración (22+ tests) |
| lint.py | 320 | 11 | 1 | ✅ | ✅ Linter de calidad del pack |
| metrics_trends.py | 350 | 15 | 0 | ✅ | ✅ Tendencias con sparklines ASCII |
| notes.py | 225 | 13 | 0 | ✅ | ✅ Notas ligeras por sesión/sprint |
| pack_dashboard.py | 206 | 8 | 0 | ❌ | ✅ Estado del pack en una pantalla |
| patch.py | 279 | 12 | 0 | ✅ | ✅ Corrección de inconsistencias |
| personality_panel.py | 259 | 12 | 0 | ❌ | ❌ Sin docstring de módulo |
| quick_status.py | 146 | 8 | 0 | ❌ | ✅ Dashboard compacto |
| reconcile_state.py | 103 | 4 | 0 | ❌ | ✅ Reconcilia estado vs disco |
| remind.py | 258 | 11 | 0 | ✅ | ✅ Gestión de recordatorios |
| repo_context_guard.py | 172 | 10 | 0 | ❌ | ❌ Sin docstring de módulo |
| repo_on.py | 308 | 10 | 0 | ❌ | ✅ Activa repo externo como objetivo |
| repo_runner.py | 205 | 9 | 0 | ❌ | ✅ Ejecuta operaciones sobre repo intervenido |
| report_generator.py | 285 | 8 | 0 | ✅ | ✅ Generador de reportes Markdown |
| review.py | 260 | 9 | 0 | ✅ | ✅ Informe de revisión periódica |
| session_details.py | 262 | 9 | 0 | ✅ | ✅ Estadísticas detalladas de sesiones |
| session_opener.py | 140 | 4 | 0 | ❌ | ✅ Abre sesión W2 desde handoff |
| session_preflight.py | 183 | 6 | 0 | ❌ | ✅ Validador de reglas W7 pre-sesión |
| session_stats.py | 110 | 4 | 0 | ❌ | ✅ Resumen estadístico de sesiones |
| show_task.py | 249 | 6 | 0 | ✅ | ✅ Muestra tarea W2 registrada |
| snapshot.py | 277 | 9 | 0 | ✅ | ✅ ZIP point-in-time del estado BAGO |
| sprint_manager.py | 351 | 18 | 0 | ✅ | ✅ Gestor de sprints |
| stability_summary.py | 128 | 4 | 0 | ❌ | ✅ Resumen de estabilidad operacional |
| stale_detector.py | 163 | 6 | 0 | ❌ | ✅ Detector de artefactos desactualizados |
| **state_store.py** | **654** | **60** | **14** | **❌** | ✅ Capa de abstracción de estado BAGO |
| stats.py | 312 | 19 | 0 | ✅ | ✅ Dashboard agregado de estadísticas |
| summary.py | 306 | 8 | 0 | ✅ | ✅ Resumen ejecutivo Markdown |
| tags.py | 299 | 10 | 0 | ✅ | ✅ Sistema de etiquetas |
| target_selector.py | 277 | 10 | 0 | ❌ | ✅ Selección segura de directorio objetivo |
| template.py | 304 | 11 | 0 | ✅ | ✅ Plantillas para nuevas sesiones |
| timeline.py | 267 | 10 | 0 | ✅ | ✅ Timeline ASCII de sesiones |
| v2_close_checklist.py | 138 | 8 | 0 | ❌ | ✅ Checklist de cierre V2 |
| validate_manifest.py | 55 | 2 | 0 | ❌ | ❌ Sin docstring de módulo |
| validate_pack.py | 107 | 1 | 0 | ❌ | ❌ Sin docstring de módulo |
| validate_state.py | 300 | 4 | 0 | ❌ | ❌ Sin docstring de módulo |
| velocity.py | 239 | 11 | 0 | ✅ | ✅ Métricas de velocidad de trabajo |
| vertice_activator.py | 179 | 8 | 0 | ❌ | ✅ Evaluador de revisión Vértice |
| watch.py | 245 | 12 | 0 | ✅ | ✅ Monitor en tiempo real |
| workflow_selector.py | 180 | 7 | 0 | ❌ | ✅ Selector formal de workflow |
| perf/render_perf_charts.py | — | — | — | — | (subdir perf/, no catalogado) |
| perf/stress_bago_agents.py | — | — | — | — | (subdir perf/, no catalogado) |

**Totales:**
- LOC total (raíz): ~20.000+ líneas
- Archivos con `--test`: **38 / 72** (53 %)
- Archivos sin docstring de módulo: **10** (emit_ideas, generate_bago_evolution_report, inspect_workflow, personality_panel, repo_context_guard, validate_manifest, validate_pack, validate_state, findings_engine —sí tiene—, inspect_workflow)

---

## 2. Entry Point `bago` — Mapa de comandos

El script `bago` (496 líneas, Python) gestiona **61 comandos distintos** agrupados en tres categorías.

### 2.1 COMMANDS_MAIN (dict, visibles siempre)

| Comando | Tool | Existe |
|---------|------|--------|
| `start` | bago_start.py | ✅ |
| `ideas` | emit_ideas.py | ✅ |
| `session` | session_opener.py | ✅ |
| `status` | quick_status.py | ✅ |

### 2.2 COMMANDS_ADVANCED (dict, visibles con `--all`)

| Comando | Tool | Existe |
|---------|------|--------|
| `on` | bago_on.py | ✅ |
| `dashboard` | pack_dashboard.py | ✅ |
| `debug` | bago_debug.py | ✅ |
| `cosecha` | cosecha.py | ✅ |
| `detector` | context_detector.py | ✅ |
| `validate` | validate_pack.py | ✅ |
| `health` | health_score.py | ✅ |
| `audit` | audit_v2.py | ✅ |
| `workflow` | workflow_selector.py | ✅ |
| `stale` | stale_detector.py | ✅ |
| `v2` | v2_close_checklist.py | ✅ |
| `task` | show_task.py | ✅ |
| `stability` | stability_summary.py | ✅ |
| `efficiency` | efficiency_meter.py | ✅ |
| `auto` | auto_mode.py | ✅ |
| `map` | context_map.py | ✅ |
| `recolecta` | context_collector.py | ✅ |
| `chat` | bago_chat_server.py | ✅ |
| `repo-on` | repo_on.py | ✅ |
| `repo-debug` | bago_debug.py `--repo` | ✅ |
| `repo-lint` | repo_runner.py lint | ✅ |
| `repo-test` | repo_runner.py test | ✅ |
| `repo-build` | repo_runner.py build | ✅ |

### 2.3 Comandos via `elif` directo (no en dict)

| Comando | Tool | Existe |
|---------|------|--------|
| `sprint` | sprint_manager.py | ✅ |
| `search` | bago_search.py | ✅ |
| `timeline` | timeline.py | ✅ |
| `report` | report_generator.py | ✅ |
| `metrics` | metrics_trends.py | ✅ |
| `doctor` | doctor.py | ✅ |
| `git` | git_context.py | ✅ |
| `export` | export.py | ✅ |
| `watch` | watch.py | ✅ |
| `test` | integration_tests.py | ✅ |
| `changelog` | changelog.py | ✅ |
| `snapshot` | snapshot.py | ✅ |
| `diff` | diff.py | ✅ |
| `session-stats` / `ss` | session_details.py | ✅ |
| `compare` | compare.py | ✅ |
| `goals` | goals.py | ✅ |
| `lint` | lint.py | ✅ |
| `summary` | summary.py | ✅ |
| `tags` | tags.py | ✅ |
| `flow` | flow.py | ✅ |
| `insights` | insights.py | ✅ |
| `config` | config.py | ✅ |
| `check` | check.py | ✅ |
| `archive` | archive.py | ✅ |
| `stats` | stats.py | ✅ |
| `remind` | remind.py | ✅ |
| `habit` | habit.py | ✅ |
| `review` | review.py | ✅ |
| `velocity` | velocity.py | ✅ |
| `patch` | patch.py | ✅ |
| `notes` | notes.py | ✅ |
| `template` | template.py | ✅ |
| `scan` | **scan.py** | ❌ **FALTA** |
| `hotspot` | **hotspot.py** | ❌ **FALTA** |
| `fix` | **autofix.py** | ❌ **FALTA** |
| `gh` | **gh_integration.py** | ❌ **FALTA** |
| `setup` | repo_context_guard.py sync | ✅ |
| `versions` | `_cmd_versions()` inline | — |
| `extensions` | `_cmd_extensions()` inline | — |
| `help` / `--help` / `-h` | bago_banner.py `--mini` | ✅ |

### 2.4 Tools orphanos (existen en tools/ pero NO referenciados en bago)

Estos archivos son funcionales pero **no accesibles via `bago <cmd>`**:

| Archivo | Propósito |
|---------|-----------|
| artifact_counter.py | Contador de artefactos útiles |
| competition_report.py | Reporte ESCENARIO-002 |
| dashboard_v2.py | Dashboard V2 (¿reemplazado por pack_dashboard?) |
| findings_engine.py | Motor de hallazgos (¿usado por scan.py faltante?) |
| generate_bago_evolution_report.py | Reporte de evolución SVG |
| generate_task_closure.py | Cierre de tareas W2 (usado via cosecha) |
| inspect_workflow.py | Inspector de workflows |
| personality_panel.py | Panel de personalidad de usuario |
| reconcile_state.py | Reconciliador estado vs disco |
| session_preflight.py | Pre-flight W7 (llamado por session_opener) |
| session_stats.py | Stats de sesiones (¿reemplazado por session_details?) |
| state_store.py | Capa de abstracción (librería interna) |
| target_selector.py | Selector de directorio (librería interna) |
| validate_manifest.py | Validador de manifest |
| validate_state.py | Validador de estado |
| vertice_activator.py | Activador de revisión Vértice |

> **Nota**: `state_store.py`, `target_selector.py`, `session_preflight.py`, y `generate_task_closure.py` son **librerías internas** correctamente no expuestas como comandos. El resto merece revisión.

---

## 3. Estado Global

| Campo | Valor |
|-------|-------|
| `bago_version` | 2.5-stable |
| `canon_version` | 2.4-v2rc |
| `system_health` | stable |
| `active_session_id` | null |
| `inventory.sessions` | 50 |
| `inventory.changes` | **60** |
| `inventory.evidences` | 52 |
| `last_completed_session_id` | SES-HARVEST-2026-04-21-007 |
| `last_completed_change_id` | BAGO-CHG-069 |
| `last_completed_evidence_id` | BAGO-EVD-070 |
| `last_validation.pack` | GO |
| `last_validation.state` | GO |
| `last_validation.manifest` | GO |

### Verificación de inventario

```
global_state.json → inventory.changes = 60
state/changes/ archivos .json reales   = 60
```

**✅ COINCIDEN** — el inventario está sincronizado.

> `last_completed_change_id` = BAGO-CHG-069 pero `inventory.changes` = 60. Si los IDs son secuenciales esto implica que hay CHGs con IDs no consecutivos o que hubo eliminaciones. No es un error, pero vale verificar con `bago reconcile` si se sospecha inconsistencia.

---

## 4. Issues Detectados

### 4.1 `datetime.utcnow()` deprecado (Python ≥ 3.12)

`datetime.utcnow()` fue marcado deprecated en Python 3.12. La alternativa correcta es `datetime.now(timezone.utc)`.

| Archivo | Línea | Fragmento |
|---------|-------|-----------|
| notes.py | 69 | `"created_at": datetime.datetime.utcnow().isoformat() + "Z"` |
| patch.py | 52 | `data["updated_at"] = datetime.datetime.utcnow().isoformat() + "Z"` |
| patch.py | 77 | `data["updated_at"] = datetime.datetime.utcnow().isoformat() + "Z"` |
| patch.py | 99 | `data["updated_at"] = datetime.datetime.utcnow().isoformat() + "Z"` |
| template.py | 154 | `now = datetime.datetime.utcnow().isoformat() + "Z"` |

**Fix sugerido:**
```python
# Antes (deprecated):
datetime.datetime.utcnow().isoformat() + "Z"

# Después (correcto):
datetime.now(timezone.utc).isoformat()
# o si se quiere el sufijo "Z" explícito:
datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
```

---

### 4.2 `datetime.now()` naive (sin timezone)

**15+ ocurrencias** de `datetime.now()` sin `timezone.utc`. Esto crea timestamps en hora local del sistema que pueden causar inconsistencias en state JSONs (mezcla de UTC con hora local).

**Archivos más críticos** (los que persisten timestamps en JSON):

| Archivo | Líneas | Impacto |
|---------|--------|---------|
| goals.py | 85, 168, 201, 273, 274 | Guarda `created_at`/`updated_at` naive en GOAL JSONs |
| remind.py | 61, 82 | Guarda `created_at`/`done_at` naive en reminders |
| snapshot.py | 58 | Timestamp del ZIP de snapshot |
| cosecha.py | 53, 114 | Solo para string de fecha (bajo impacto) |
| auto_mode.py | 398 | Guarda `ts` en estado |

**Archivos de bajo impacto** (solo display):

| Archivo | Líneas | Uso |
|---------|--------|-----|
| bago_banner.py | 203 | Solo display `%Y-%m-%d  %H:%M` |
| context_detector.py | 315 | Solo display en terminal |
| export.py | 394, 402, 406 | Nombre de fichero de salida |
| quick_status.py | 98 | Solo display |

---

### 4.3 `sys.exit()` en lugares inesperados

El patrón `sys.exit(main())` (anti-patrón de propagación de código de retorno) aparece en **8 archivos**:

```python
# audit_v2.py:182
sys.exit(main())
# health_score.py:207
sys.exit(main())
# integration_tests.py:531
sys.exit(main())
# reconcile_state.py:103
sys.exit(main())
# stability_summary.py:128
sys.exit(main())
# stale_detector.py:163
sys.exit(main())
# v2_close_checklist.py:138
sys.exit(main())
# vertice_activator.py:179
sys.exit(main())
# workflow_selector.py:180
sys.exit(main())
```

> Este patrón es **aceptable** cuando `main()` retorna un int. El problema es que no es uniforme: otros tools llaman `main()` directamente en `if __name__ == "__main__":` sin `sys.exit()`.

**`sys.exit(1)` en flujos de error normales** (muestra alto acoplamiento con argparse en vez de excepciones):

Archivos con >4 ocurrencias de `sys.exit(1)`: `config.py` (7), `goals.py` (6), `template.py` (6), `snapshot.py` (5), `diff.py` (4).

**`bago_search.py:293`** — único `sys.exit(0)` que sale con éxito en flujo intermedio:
```python
# bago_search.py:293
sys.exit(0)  # sale limpiamente cuando --test pasa
```

---

### 4.4 Funciones largas (>50 líneas)

Ordenado por tamaño estimado:

| Archivo | Función | LOC aprox | Observación |
|---------|---------|-----------|-------------|
| bago_chat_server.py | `_run_bago(cmd)` | ~680 | Incluye `HTML_PAGE` string embebido de ~600 líneas |
| generate_bago_evolution_report.py | `main()` | ~371 | Monolito: lee datos + genera SVG + escribe |
| emit_ideas.py | `main()` | ~335 | Monolito: argparse + toda la lógica de ideas |
| cosecha.py | `run()` | ~169 | Flujo W9 completo en una función |
| bago_debug.py | `_scan_repo()` | ~121 | Análisis de estructura del repo |
| audit_v2.py | `main()` | ~111 | Secuencia de auditoría completa |
| bago_chat_server.py | `_load_bago_context()` | ~67 | Carga y formateo de contexto |
| generate_bago_evolution_report.py | `grouped_bar_chart()` | ~55 | SVG de gráfico agrupado |
| metrics_trends.py | `render_metrics()` | ~100 | Construcción de tabla de tendencias |
| report_generator.py | `generate_full_report()` | ~106 | Genera reporte Markdown completo |
| pack_dashboard.py | `main()` | ~100 | Dashboard principal |
| repo_on.py | `_workflow_analysis()` | ~83 | Análisis de workflows viables |
| auto_mode.py | `run()` | ~83 | Lógica de modo automático |
| check.py | `_run_check()` | ~83 | Ejecutor de un ítem de checklist |
| findings_engine.py | `fail()` interno | ~88 | Función de error (ver 4.5) |
| export.py | `export_html()` | ~93 | Generador HTML de sesiones |

**Fragmento ilustrativo del problema en `bago_chat_server.py`:**
```python
# Línea 341: _run_bago empieza
def _run_bago(cmd: str) -> str:
    if cmd == "contexto":
        cmd = "context"
    if cmd == "context":
        # ~30 líneas de lógica
        ...

# Línea ~383: HTML_PAGE es módulo-nivel, pero sigue visualmente pegado:
HTML_PAGE = r"""<!DOCTYPE html>
<html lang="es">
...
"""  # ~600 líneas de HTML embebido
```
El HTML embebido en el módulo Python es el mayor contribuyente al LOC del archivo (1253 líneas).

---

### 4.5 Imports potencialmente no usados / duplicados

#### Doble import de `pathlib`

Tres archivos importan `pathlib` dos veces (una como módulo y otra con `from pathlib import Path`):

```python
# flow.py (líneas ~6 y ~240):
from pathlib import Path    # al inicio del archivo
...
import pathlib              # dentro de run_tests(), innecesario

# goals.py (líneas ~6 y ~338):
from pathlib import Path    # al inicio
import pathlib              # dentro de run_tests()

# tags.py (líneas ~5 y ~267):
from pathlib import Path    # al inicio
import pathlib  # ensure available in run_tests scope  # ← comentario que explica la intención
```

> `tags.py` documenta la intención (hack para que el scope de tests tenga `pathlib`). Los otros dos carecen de justificación. El correcto es eliminar el `import pathlib` tardío y usar `Path` donde sea necesario.

#### `import os` con uso mínimo

Archivos que importan `os` pero lo usan ≤2 veces (posiblemente innecesario o reemplazable con `pathlib`):

| Archivo | Usos de `os` |
|---------|-------------|
| context_collector.py | 1 |
| bago_debug.py | 2 |
| auto_mode.py | 2 |
| repo_context_guard.py | 1 |
| target_selector.py | 2 |

#### `importlib.util` en `pack_dashboard.py`

`pack_dashboard.py` importa `importlib.util` (línea 7) y lo usa en 4 lugares para cargar dinámicamente `context_detector.py`. Es **uso válido** pero crea acoplamiento frágil — si la ruta cambia, falla en runtime sin error en import.

---

### 4.6 Código duplicado / funciones similares

#### Patrón `def fail(name, msg)` — duplicado en 22 archivos

La función interna `fail()` (o `fail(name, msg)`) aparece definida **dentro de la función `main()`** en al menos 22 tools:

```
archive.py, compare.py, config.py, check.py, diff.py, findings_engine.py,
flow.py, goals.py, habit.py, insights.py, lint.py, notes.py, patch.py,
remind.py, review.py, session_details.py, snapshot.py, stats.py,
summary.py, tags.py, template.py, velocity.py
```

Ejemplo típico (de `compare.py`):
```python
def main():
    def fail(name, msg):
        print(f"  ❌ {name}: {msg}", file=sys.stderr)
        sys.exit(1)
    ...
```

Esta función es **idéntica o casi idéntica** en todos los archivos. Debería extraerse a un módulo utilitario `bago_utils.py` o similar.

#### `_read_global_state()` duplicada en 4 archivos

```python
# cosecha.py:61-63
def _read_global_state():
    p = BAGO_ROOT / "state" / "global_state.json"
    return json.loads(p.read_text())

# auto_mode.py: patrón equivalente inline
# bago_banner.py: patrón equivalente inline
# quick_status.py: patrón equivalente inline
```

`StateStore.global_state.get()` ya proporciona esta funcionalidad — todos estos deberían migrarse.

#### `_next_id()` duplicada en 2 archivos

```python
# cosecha.py:39-48 — genera IDs BAGO-CHG-NNN / BAGO-EVD-NNN
def _next_id(folder, prefix, pad=3):
    existing = [f.stem for f in folder.glob(f"BAGO-{prefix}-*.json")]
    ...

# notes.py: lógica similar para generar IDs de notas
```

`StateStore.changes.create()` ya maneja la asignación automática de IDs — cosecha.py debería delegarle esto.

#### Patrón de timestamp inconsistente

En el mismo codebase coexisten:
```python
datetime.now(timezone.utc).isoformat()  # ← correcto, timezone-aware
datetime.utcnow().isoformat() + "Z"      # ← deprecated
datetime.datetime.now().isoformat()      # ← naive (hora local)
```
Los tres producen strings diferentes y pueden causar problemas de ordenación si se comparan.

---

## 5. Mapa de Dependencias entre Tools

### 5.1 Dependencias directas (imports estáticos)

```
state_store.py ◄── generate_task_closure.py
                └── (pendientes de migración: 26 tools más)

target_selector.py ◄── auto_mode.py (choose_path)
                   ├── bago_debug.py (has_supported_manifest)
                   └── repo_on.py (choose_path, discover_project_candidates, has_supported_manifest)

repo_context_guard.py ◄── bago_on.py (detected_context, save_context)
                      └── repo_on.py (ROOT, STATE_PATH, repo_fingerprint)

bago_debug.py ◄── repo_on.py (_detect_package_manager, _find_conflict_markers, _git_status, _load_json)
              └── repo_runner.py (_default_repo_target, _detect_package_manager, _load_json, _run)
```

**Diagrama textual:**

```
[state_store.py]          ← librería central de estado
    ↑
[generate_task_closure.py]  ← único tool migrado

[target_selector.py]      ← librería de selección de paths
    ↑           ↑           ↑
[auto_mode] [bago_debug] [repo_on]

[repo_context_guard.py]   ← librería de contexto del host
    ↑               ↑
[bago_on.py]     [repo_on.py]

[bago_debug.py]           ← librería de diagnóstico de repo
    ↑           ↑
[repo_on.py]  [repo_runner.py]
```

### 5.2 Dependencias dinámicas (via `importlib.util`)

```
cosecha.py ──[importlib]──→ context_detector.py (función _unregistered_files)
pack_dashboard.py ──[importlib]──→ context_detector.py (módulo completo)
```

Estos dos loads son frágiles: si `context_detector.py` cambia su API interna, fallan en runtime sin error estático.

### 5.3 Tools autónomos (sin dependencias internas)

La mayoría de tools son **autónomos** — solo importan stdlib + leen JSONs directamente de disco:
`changelog.py`, `compare.py`, `config.py`, `diff.py`, `export.py`, `flow.py`, `goals.py`, `habit.py`, `insights.py`, `lint.py`, `notes.py`, `patch.py`, `remind.py`, `report_generator.py`, `review.py`, `session_details.py`, `snapshot.py`, `sprint_manager.py`, `stats.py`, `summary.py`, `tags.py`, `template.py`, `timeline.py`, `velocity.py`, `watch.py`, etc.

---

## 6. Observaciones Adicionales

### 6.1 `cosecha.py` marcada como ✅ MIGRADA pero no usa StateStore

En `state_store.py` (línea ~52), `cosecha.py` está listada como ✅ MIGRADA:
```python
#   MIGRADAS
#   ✅ generate_task_closure.py
#   ✅ cosecha.py  (delegado a generate_task_closure)
```

Sin embargo, `cosecha.py` **NO importa `StateStore`** y **NO llama a `generate_task_closure`**. Implementa su propia lógica de escritura JSON directamente:
```python
(SESSIONS / f"{session_id}.json").write_text(json.dumps(session, ...))
(CHANGES  / f"{chg_id}.json").write_text(json.dumps(chg, ...))
(EVIDENCES / f"{evd_id}.json").write_text(json.dumps(evd, ...))
```
El comentario "delegado a generate_task_closure" en state_store.py es **incorrecto** o hace referencia a una refactorización no ejecutada.

### 6.2 Modo de ejecución inconsistente en `if __name__ == "__main__"`

Coexisten tres patrones:

```python
# Patrón A — directo (mayoría de tools):
if __name__ == "__main__":
    main()

# Patrón B — con sys.exit para propagar código de retorno:
if __name__ == "__main__":
    sys.exit(main())

# Patrón C — custom (session_preflight.py):
if __name__ == "__main__":
    sys.exit(0 if all_ok else 1)
```

### 6.3 `validate_pack.py` invoca subprocesos masivamente

```python
def run(script: str):  # ~95 líneas
    subprocess.run(["python3", script, "--test"], ...)
```

`validate_pack.py` delega en ~15 subprocesos secuenciales para validar el pack. Esto es lento y podría paralelizarse.

### 6.4 `bago_chat_server.py` tiene HTML embebido como string literal

El archivo `bago_chat_server.py` (1253 LOC) contiene una constante `HTML_PAGE` con ~600 líneas de HTML/CSS/JS embebidas como raw string. Esto infla el archivo e impide el linting del HTML/JS.

---

## 7. Recomendaciones para el Agente Escritor

Listado **priorizado** por impacto/esfuerzo:

### 🔴 CRÍTICO (bloquean funcionalidad)

1. **Crear los 4 tools faltantes**: `scan.py`, `hotspot.py`, `autofix.py`, `gh_integration.py` son invocados por `bago scan`, `bago hotspot`, `bago fix`, `bago gh` respectivamente. Ejecutarlos actualmente lanza `FileNotFoundError`. `findings_engine.py` ya existe y probablemente era la base para `scan.py`/`hotspot.py` — revisar su API antes de crear los nuevos.

2. **Corregir docstring en `state_store.py`**: La sección `MIGRADAS` lista `cosecha.py` como migrada a StateStore, pero el código no lo refleja. Actualizar el comentario con el estado real o ejecutar la migración.

### 🟡 MEDIO (afectan mantenibilidad y calidad)

3. **Reemplazar `datetime.utcnow()` (5 ocurrencias)**:
   - `notes.py:69`, `patch.py:52/77/99`, `template.py:154`
   - Sustitución directa: `datetime.datetime.utcnow()` → `datetime.now(timezone.utc)`

4. **Corregir `datetime.now()` naive en archivos que persisten JSON** (prioritarios):
   - `goals.py` (5 ocurrencias de timestamps guardados), `remind.py` (2), `snapshot.py` (1), `auto_mode.py` (1)
   - Añadir `timezone.utc` o importar y usar el patrón `datetime.now(timezone.utc)`

5. **Extraer `def fail()` a módulo utilitario** (`bago_utils.py`):
   - 22 archivos tienen la misma función definida inline
   - Crear `bago_utils.py` con `def print_error(name, msg)` y `def fail(name, msg)`
   - Importar desde cada tool: `from bago_utils import fail`

6. **Refactorizar `emit_ideas.py::main()` (335 líneas) y `generate_bago_evolution_report.py::main()` (371 líneas)**:
   - Extraer subfunciones temáticas (parse_args, load_data, render, save)
   - Añadir docstrings de módulo a ambos archivos

### 🟢 BAJO (deuda técnica / limpieza)

7. **Eliminar doble import `pathlib` en `flow.py` y `goals.py`**:
   - Eliminar `import pathlib` (el tardío, dentro de run_tests)
   - En `tags.py` el comentario explica la intención — mantener o limpiar con nota

8. **Migrar `cosecha.py` a StateStore**:
   - Reemplazar escritura directa JSON por `store.sessions.save()`, `store.changes.create()`, `store.evidences.create()`
   - Actualizar el docstring en `state_store.py`

9. **Priorizar migración a StateStore** (26 pendientes):
   - Alta prioridad: `auto_mode.py`, `emit_ideas.py`, `pack_dashboard.py`, `stale_detector.py`, `validate_state.py`
   - Criterio: los que más directamente leen/escriben state JSON

10. **Extraer HTML de `bago_chat_server.py`**:
    - Mover `HTML_PAGE` a `bago_chat.html` en `.bago/templates/`
    - El módulo Python pasa de 1253 a ~650 líneas

11. **Estandarizar patrón `if __name__ == "__main__"`**:
    - Adoptar Patrón B (`sys.exit(main())`) para todos los tools donde `main()` retorna int
    - Adoptar Patrón A (`main()`) donde `main()` no retorna nada significativo

12. **Añadir docstrings a archivos sin módulo-docstring**:
    - `emit_ideas.py`, `generate_bago_evolution_report.py`, `inspect_workflow.py`, `personality_panel.py`, `repo_context_guard.py`, `validate_manifest.py`, `validate_pack.py`, `validate_state.py`

---

_Fin del BAGO READER REPORT — v1.0 · 2026-04-22_
