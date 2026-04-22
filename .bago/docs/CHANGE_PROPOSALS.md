# BAGO CHANGE PROPOSALS
_Generado por el Agente Lector+Propositor — 2026-04-22_
_Basado en: análisis directo de fuentes (.bago/tools/ — 81 archivos Python)_

---

## RESUMEN DE PROPUESTAS

| ID | Categoría | Archivos afectados | Prioridad | Impacto |
|----|-----------|--------------------|-----------|---------|
| PROPUESTA-001 | Naive datetimes en datos persistidos | 4 archivos (9 líneas) | 🔴 ALTA | Timestamps sin zona horaria mezclados con ISO-UTC |
| PROPUESTA-002 | `datetime.utcnow()` — solo en strings de test | 3 archivos | 🟡 MEDIA | Detector demasiado amplio; patch incompleto |
| PROPUESTA-003 | Función `fail()` duplicada | 26 archivos | 🟡 MEDIA | ~100 líneas repetidas; fragmentación de convención |
| PROPUESTA-004 | Tools sin routing en script `bago` | 14 tools | 🔴 ALTA | Tools inaccesibles vía CLI |
| PROPUESTA-005 | Docstrings de módulo faltantes | 10 archivos | 🟢 BAJA | Documentación inconsistente |
| PROPUESTA-006 | Mejoras a `findings_engine.py` | 1 archivo | 🟡 MEDIA | Tests incompletos; tipos incorrectos; edge cases |
| PROPUESTA-007 | `str | None` requiere Python 3.10+ | 1 archivo | 🟡 MEDIA | Regresión si se ejecuta en Python 3.9 |

---

## PROPUESTA-001: Corregir `datetime.now()` sin timezone (datetimes naivos en JSON)

**Categoría:** Bug / Consistencia de datos  
**Prioridad:** 🔴 ALTA — timestamps naivos almacenados en JSON mezclan con timestamps UTC  
**Archivos afectados:** `goals.py`, `snapshot.py`, `remind.py`, `auto_mode.py`

### Explicación

Varios tools usan `datetime.datetime.now()` (sin argumento de timezone) para generar timestamps que luego se persisten en archivos JSON bajo claves como `created_at`, `updated_at`, `done_at`. Estos timestamps naivos son inconsistentes con el resto del pack, donde la convención es UTC (`datetime.now(timezone.utc).isoformat()`). Mezclar ambos formatos rompe ordenaciones cronológicas y comparaciones entre sesiones.

En Python 3.12+ `datetime.now()` emite `DeprecationWarning` cuando se usa en contextos que esperan timezone-aware.

El reemplazo correcto (sin cambio de import, ya que estos archivos tienen `import datetime` al nivel de módulo):
- `datetime.datetime.now()` → `datetime.datetime.now(datetime.timezone.utc)`

---

### Patches por archivo

#### FILE: `.bago/tools/goals.py` (líneas 85, 168, 201, 273, 274)

```
OLD (línea 85):     now = datetime.datetime.now().isoformat()
NEW (línea 85):     now = datetime.datetime.now(datetime.timezone.utc).isoformat()

OLD (línea 168):     g["updated_at"] = datetime.datetime.now().isoformat()
NEW (línea 168):     g["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

OLD (línea 201):     g["updated_at"] = datetime.datetime.now().isoformat()
NEW (línea 201):     g["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

OLD (línea 273):             "created_at": datetime.datetime.now().isoformat(),
NEW (línea 273):             "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),

OLD (línea 274):             "updated_at": datetime.datetime.now().isoformat(),
NEW (línea 274):             "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
```
NOTA: El import existente `import datetime` (línea 21) es suficiente; no se necesita cambio de import.

---

#### FILE: `.bago/tools/snapshot.py` (línea 58)

```
OLD (línea 58):     now = datetime.datetime.now()
NEW (línea 58):     now = datetime.datetime.now(datetime.timezone.utc)
```
NOTA: La variable `now` se usa para `now.strftime("%Y%m%d_%H%M%S")` y `ts = now.strftime(...)`. El cambio a UTC hace que los snapshot IDs sean deterministas independientemente del TZ del sistema. El import existente `import datetime` (línea 22) es suficiente.

---

#### FILE: `.bago/tools/remind.py` (líneas 61, 82)

```
OLD (línea 61):         "created_at": datetime.datetime.now().isoformat(),
NEW (línea 61):         "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),

OLD (línea 82):         rem["done_at"] = datetime.datetime.now().isoformat()
NEW (línea 82):         rem["done_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
```
NOTA: Import existente `import datetime` (línea 21) es suficiente.

---

#### FILE: `.bago/tools/auto_mode.py` (línea 398)

```
OLD (línea 398):             "ts": datetime.now().isoformat()
NEW (línea 398):             "ts": datetime.now(timezone.utc).isoformat()
```
NOTA: Este archivo usa `from datetime import datetime, timezone` (línea 21). La variable `datetime` ya es la clase, no el módulo; la corrección usa `timezone` ya importado.

---

### Casos de display-only (menor prioridad, no almacenados en JSON)

Los siguientes usos de `datetime.now()` sin timezone son para mostrar en terminal (no se persisten en JSON), por lo que su impacto es solo visual pero también conviene uniformizarlos:

| Archivo | Línea | Uso actual | Corrección sugerida |
|---------|-------|------------|---------------------|
| `bago_banner.py` | 203 | `datetime.now().strftime("%Y-%m-%d  %H:%M")` | `datetime.now(timezone.utc).strftime(...)` |
| `context_detector.py` | 315 | `datetime.now().strftime('%H:%M:%S')` | `datetime.now(timezone.utc).strftime(...)` |
| `cosecha.py` | 53, 114 | `datetime.now().strftime(...)` | `datetime.now(timezone.utc).strftime(...)` |
| `export.py` | 394, 402, 406 | `datetime.now().strftime(...)` | `datetime.now(timezone.utc).strftime(...)` |
| `quick_status.py` | 98 | `datetime.now().strftime("%Y-%m-%d %H:%M")` | `datetime.now(timezone.utc).strftime(...)` |

---

## PROPUESTA-002: `datetime.utcnow()` — revisar detector y patch generator en findings_engine.py

**Categoría:** Lógica de detección / Exactitud  
**Prioridad:** 🟡 MEDIA — detector demasiado amplio y patch incompleto  
**Archivos afectados:** `.bago/tools/findings_engine.py`

### Contexto

Los tools del pack **NO usan `datetime.utcnow()`** en código de producción. Las únicas apariciones en `.bago/tools/` son:
- `findings_engine.py:248` — detección del patrón en código de usuarios
- `findings_engine.py:424`, `scan.py:174`, `autofix.py:306,326` — strings de test para probar los detectores

Por lo tanto, no hay correcciones de `utcnow()` que aplicar a los tools mismos. Sin embargo, la lógica de detección y corrección tiene dos defectos:

### Defecto 2.1: Detección demasiado amplia (línea 248)

```
FILE: .bago/tools/findings_engine.py (línea 248 — dentro de run_bago_lint)

OLD:                 if "datetime.utcnow()" in line or ".utcnow()" in line:
NEW:                 if "datetime.utcnow()" in line or "datetime.datetime.utcnow()" in line:
```
RAZÓN: `.utcnow()` captura cualquier objeto con ese método (por ejemplo, `pd.Timestamp.utcnow()`, `arrow.utcnow()`), generando falsos positivos. La detección debe limitarse a `datetime.utcnow()` y `datetime.datetime.utcnow()`.

### Defecto 2.2: `_make_utcnow_patch` no cubre el patrón `.utcnow()` genérico (líneas 278-282)

```
FILE: .bago/tools/findings_engine.py (función _make_utcnow_patch, líneas 278-289)
```

La función `_make_utcnow_patch` aplica dos `re.sub` encadenados:
1. `datetime.datetime.utcnow()` → `datetime.datetime.now(datetime.timezone.utc)`
2. `datetime.utcnow()` → `datetime.datetime.now(datetime.timezone.utc)`

Pero **no genera patch** si la línea contiene solo `.utcnow()` sin el prefijo `datetime.`. Dado que el detector (línea 248) también captura esos casos (antes de aplicar el fix del Defecto 2.1), el resultado es `autofixable=True` pero `fix_patch=""`. Esto es inconsistente.

Con el fix del Defecto 2.1, el detector dejará de capturar `.utcnow()` genérico, eliminando también este problema de inconsistencia.

---

## PROPUESTA-003: Extraer función `fail()` duplicada a `bago_utils.py`

**Categoría:** Duplicación de código  
**Prioridad:** 🟡 MEDIA — 26 archivos con copia idéntica o casi idéntica  
**Archivos afectados:** `patch.py`, `tags.py`, `session_details.py`, `config.py`, `check.py`, `habit.py`, `goals.py`, `flow.py`, `review.py`, `notes.py`, `summary.py`, `stats.py`, `archive.py`, `template.py`, `diff.py`, `velocity.py`, `compare.py`, `snapshot.py`, `remind.py`, `lint.py`, `insights.py`, `gh_integration.py`, `findings_engine.py`, `scan.py`, `hotspot.py`, `autofix.py`

### Análisis de las implementaciones actuales

**Variante A** (21 archivos — 4 líneas):
```python
    def fail(name, msg):
        nonlocal errors
        errors += 1
        print(f"  FAIL: {name} — {msg}")
```

**Variante B** (5 archivos: `scan.py`, `hotspot.py`, `autofix.py`, `findings_engine.py`, `gh_integration.py` — 1 línea, parámetros `n, m`):
```python
    def fail(n, m):
        nonlocal errors; errors += 1; print(f"  FAIL: {n} — {m}")
```

Ambas variantes son cierres (closures) que modifican `nonlocal errors`. Esto impide extraerlas como funciones de módulo simples. La solución correcta es una clase `TestRunner`.

### Propuesta: crear `.bago/tools/bago_utils.py`

```python
"""bago_utils.py — Utilidades compartidas para tools BAGO."""
import sys


class TestRunner:
    """Ejecutor de tests inline con conteo automático de fallos."""

    def __init__(self) -> None:
        self.errors = 0

    def ok(self, name: str) -> None:
        print(f"  OK: {name}")

    def fail(self, name: str, msg: str) -> None:
        self.errors += 1
        print(f"  FAIL: {name} — {msg}")

    def summary(self, total: int) -> None:
        passed = total - self.errors
        print(f"\n  {passed}/{total} tests pasaron")
        if self.errors:
            sys.exit(1)
```

### Migración en cada archivo

Para cada uno de los 26 archivos, dentro de `run_tests()`:

```
AÑADIR al inicio del archivo (después de los imports existentes):
    from bago_utils import TestRunner

CAMBIAR dentro de run_tests():
OLD:
    errors = 0
    def ok(n): print(f"  OK: {n}")
    def fail(name, msg):
        nonlocal errors
        errors += 1
        print(f"  FAIL: {name} — {msg}")
    ...
    total = N; passed = total - errors
    print(f"\n  {passed}/{total} tests pasaron")
    if errors: sys.exit(1)

NEW:
    ts = TestRunner()
    def ok(n): ts.ok(n)
    def fail(name, msg): ts.fail(name, msg)
    ...
    ts.summary(N)
```

NOTA: Las funciones locales `ok()` y `fail()` dentro de `run_tests()` se mantienen como wrappers de una línea para no romper las 400+ llamadas existentes. En una segunda fase, pueden eliminarse y llamar `ts.ok()` / `ts.fail()` directamente.

---

## PROPUESTA-004: Routing incompleto en script `bago`

**Categoría:** Arquitectura / Accesibilidad  
**Prioridad:** 🔴 ALTA — 14 tools son inaccesibles vía `bago <comando>`  
**Archivos afectados:** `bago` (script principal)

### Clasificación de tools no routed

**Librerías importadas (no deben routarse — intencional):**
- `findings_engine.py` — importado por `scan.py`, `hotspot.py`, `autofix.py`, `gh_integration.py`, `risk_matrix.py`
- `state_store.py` — importado por `generate_task_closure.py` y otros
- `target_selector.py` — importado por `bago_debug.py`, `auto_mode.py`, `repo_on.py`

**Tools de rendimiento (subdir `perf/`, posiblemente intencional):**
- `perf/render_perf_charts.py`
- `perf/stress_bago_agents.py`

**Tools con comando pero sin routing (⚠️ BUG):**

| Tool | Comando propuesto | Descripción (del docstring) |
|------|-------------------|-----------------------------|
| `artifact_counter.py` | `bago artifacts` | Mide producción de artefactos útiles por sesión |
| `competition_report.py` | `bago competition` | Compara sesiones bago/on vs bago/off del ESCENARIO-002 |
| `dashboard_v2.py` | `bago dashboard-v2` | Dashboard V2 (versión mejorada de pack_dashboard) |
| `generate_bago_evolution_report.py` | `bago evolution` | Reporte de evolución histórica del framework |
| `generate_task_closure.py` | `bago task-closure` | Genera artefactos de cierre para tarea W2 |
| `inspect_workflow.py` | `bago inspect` | Inspección de workflows BAGO |
| `personality_panel.py` | `bago personality` | Panel de personalidad/perfil del pack |
| `reconcile_state.py` | `bago reconcile` | Reconcilia estado vs disco |
| `risk_matrix.py` | `bago risk` | Matriz de riesgo oculto desde hallazgos de código |
| `session_preflight.py` | `bago preflight` | Validador de reglas W7 pre-sesión |
| `session_stats.py` | `bago session-summary` | Resumen estadístico de sesiones por tipo, workflow y rol |
| `validate_manifest.py` | `bago validate-manifest` | Validación del manifiesto BAGO |
| `validate_state.py` | `bago validate-state` | Validación del estado global |
| `vertice_activator.py` | `bago vertice` | Evaluador de activación de revisión Vértice |

### Patches propuestos para el script `bago`

**Sección 1: Añadir a `COMMANDS_ADVANCED` (lines 56-80)**

```
FILE: bago
DENTRO DE: COMMANDS_ADVANCED = { ... }
AÑADIR (antes del cierre `}`):

    "artifacts":       ["python3", str(TOOLS / "artifact_counter.py")],
    "competition":     ["python3", str(TOOLS / "competition_report.py")],
    "dashboard-v2":    ["python3", str(TOOLS / "dashboard_v2.py")],
    "evolution":       ["python3", str(TOOLS / "generate_bago_evolution_report.py")],
    "task-closure":    ["python3", str(TOOLS / "generate_task_closure.py")],
    "inspect":         ["python3", str(TOOLS / "inspect_workflow.py")],
    "personality":     ["python3", str(TOOLS / "personality_panel.py")],
    "reconcile":       ["python3", str(TOOLS / "reconcile_state.py")],
    "risk":            ["python3", str(TOOLS / "risk_matrix.py")],
    "preflight":       ["python3", str(TOOLS / "session_preflight.py")],
    "session-summary": ["python3", str(TOOLS / "session_stats.py")],
    "validate-manifest": ["python3", str(TOOLS / "validate_manifest.py")],
    "validate-state":  ["python3", str(TOOLS / "validate_state.py")],
    "vertice":         ["python3", str(TOOLS / "vertice_activator.py")],
```

**Sección 2: Añadir descripciones en `bago help --all` (líneas 446-483)**

```
FILE: bago
DENTRO DE: extra = { ... } (línea 446)
AÑADIR:

    "artifacts":       "conteo y reporte de artefactos útiles por sesión",
    "competition":     "comparativa sesiones on vs off del ESCENARIO-002",
    "dashboard-v2":    "dashboard BAGO V2 (versión extendida)",
    "evolution":       "reporte de evolución histórica del framework BAGO",
    "task-closure":    "genera artefactos de cierre para tarea W2",
    "inspect":         "inspección detallada de workflows",
    "personality":     "panel de perfil y personalidad del pack",
    "reconcile":       "reconcilia estado global vs disco",
    "risk":            "matriz de riesgo desde hallazgos de código",
    "preflight":       "validador de reglas W7 antes de abrir sesión",
    "session-summary": "estadísticas de sesiones por tipo, workflow y rol",
    "validate-manifest": "valida el manifiesto BAGO del pack",
    "validate-state":  "valida integridad del estado global",
    "vertice":         "evaluador de activación de revisión Vértice",
```

---

## PROPUESTA-005: Añadir docstrings de módulo donde faltan

**Categoría:** Documentación  
**Prioridad:** 🟢 BAJA  
**Archivos afectados:** 10 archivos

### Patches

#### FILE: `.bago/tools/emit_ideas.py` (insertar después del shebang, línea 1)
```
INSERTAR antes de la primera línea de imports:
"""emit_ideas.py — BAGO: muestra, prioriza y acepta ideas del backlog."""
```

#### FILE: `.bago/tools/generate_bago_evolution_report.py` (insertar después del shebang)
```
INSERTAR antes de la primera línea de imports:
"""generate_bago_evolution_report.py — BAGO: reporte de evolución histórica del framework."""
```

#### FILE: `.bago/tools/inspect_workflow.py` (insertar después del encoding comment)
```
INSERTAR antes de `from __future__ import annotations`:
"""inspect_workflow.py — BAGO: inspección detallada de workflows y sus estados."""
```

#### FILE: `.bago/tools/personality_panel.py` (insertar después del encoding comment)
```
INSERTAR antes de `from __future__ import annotations`:
"""personality_panel.py — BAGO: panel de perfil y personalidad del pack."""
```

#### FILE: `.bago/tools/repo_context_guard.py` (insertar después del encoding comment)
```
INSERTAR antes de `from __future__ import annotations`:
"""repo_context_guard.py — BAGO: sincroniza y protege el contexto del repositorio activo."""
```

#### FILE: `.bago/tools/validate_manifest.py` (insertar después del encoding comment)
```
INSERTAR antes de `from pathlib import Path`:
"""validate_manifest.py — BAGO: valida la estructura del manifiesto del pack."""
```

#### FILE: `.bago/tools/validate_pack.py` (insertar después del encoding comment)
```
INSERTAR antes de `from __future__ import annotations`:
"""validate_pack.py — BAGO: validación completa del pack (hashes, estructura, manifesto)."""
```

#### FILE: `.bago/tools/validate_state.py` (insertar después del encoding comment)
```
INSERTAR antes de `from pathlib import Path`:
"""validate_state.py — BAGO: valida la integridad del estado global del pack."""
```

#### FILE: `.bago/tools/perf/render_perf_charts.py` (insertar después del shebang)
```
INSERTAR antes de la primera línea de imports:
"""render_perf_charts.py — BAGO perf: renderiza gráficas de rendimiento de agentes."""
```

#### FILE: `.bago/tools/perf/stress_bago_agents.py` (insertar después del shebang)
```
INSERTAR antes de la primera línea de imports:
"""stress_bago_agents.py — BAGO perf: stress test de agentes BAGO en paralelo."""
```

---

## PROPUESTA-006: Mejoras a `findings_engine.py`

**Categoría:** Funcionalidad / Tests / Tipos  
**Prioridad:** 🟡 MEDIA  
**Archivo:** `.bago/tools/findings_engine.py`

---

### 6.1 Tests adicionales propuestos (actualmente hay 7; faltan al menos 9)

```python
# TEST T8: parse_pylint con formato JSON
def test_parse_pylint_json():
    sample = json.dumps([{
        "path": "a.py", "line": 5, "column": 0,
        "message-id": "C0114", "message": "Missing module docstring",
        "type": "convention"
    }])
    fs = parse_pylint(sample)
    assert len(fs) == 1 and fs[0].rule == "C0114" and fs[0].severity == "info"

# TEST T9: parse_pylint fallback texto cuando JSON inválido
def test_parse_pylint_text_fallback():
    sample = "a.py:10:0: C0114: Missing module docstring (missing-module-docstring)\n"
    # El regex del fallback espera "filepath:line:col: CODE: message"
    fs = parse_pylint(sample)
    # Actualmente el regex del fallback es r"^(.+?):(\d+):(\d+):\s+([A-Z]\d+):\s+(.+)$"
    # que SÍ captura este formato — verificar que retorna 1 finding
    assert len(fs) == 1 and fs[0].rule == "C0114"

# TEST T10: parse_bago_custom JSON válido
def test_parse_bago_custom():
    sample = json.dumps([{
        "file": "x.py", "line": 3, "rule": "BAGO-W999",
        "severity": "warning", "message": "Test", "autofixable": True
    }])
    fs = parse_bago_custom(sample)
    assert len(fs) == 1 and fs[0].rule == "BAGO-W999" and fs[0].autofixable

# TEST T11: run_bago_lint detecta BAGO-I001 (sys.exit sin mensaje)
def test_bago_lint_exit_without_message():
    import tempfile as tf2, shutil as sh2
    tmp = Path(tf2.mkdtemp())
    (tmp / "x.py").write_text("import sys\nsys.exit(1)\n")
    findings = run_bago_lint(str(tmp))
    i001 = [f for f in findings if f.rule == "BAGO-I001"]
    assert i001, f"expected BAGO-I001, got: {findings}"
    sh2.rmtree(tmp)

# TEST T12: FindingsDB.latest() retorna None cuando no hay scans
def test_db_latest_empty():
    import tempfile as tf3, shutil as sh3
    orig = FindingsDB.__init__.__globals__["FINDINGS_DIR"]
    # Monkeypatch via re-import (patrón ya usado en T4)
    # ... (mismo patrón que T4 pero directorio vacío)
    # assert FindingsDB.latest() is None

# TEST T13: deduplicación en FindingsDB.save()
def test_db_deduplication():
    # Añadir el mismo Finding dos veces y verificar que save() guarda solo uno
    f1 = Finding(id="DUP1", severity="warning", file="a.py", line=1, col=0,
                 rule="E302", source="flake8", message="dup")
    # ... (monkeypatch patrón T4)
    # assert len(db2.findings) == 1

# TEST T14: _make_id es determinista
def test_make_id_deterministic():
    id1 = _make_id("flake8", "a.py", 10, "E302")
    id2 = _make_id("flake8", "a.py", 10, "E302")
    assert id1 == id2 and id1.startswith("FIND-")

# TEST T15: _read_context con archivo existente
def test_read_context():
    import tempfile as tf4, shutil as sh4
    tmp = Path(tf4.mkdtemp())
    f = tmp / "c.py"
    f.write_text("\n".join(f"line{i}" for i in range(10)))
    ctx = _read_context(str(f), 5, radius=2)
    assert len(ctx) == 5 and "5" in ctx[1]
    sh4.rmtree(tmp)

# TEST T16: parse_flake8 con código de prefijo desconocido → severity "info"
def test_parse_flake8_unknown_prefix():
    sample = "a.py:1:1: X999 unknown code\n"
    fs = parse_flake8(sample)
    assert len(fs) == 1 and fs[0].severity == "info"
```

---

### 6.2 Bug: tipo `str | None` requiere Python 3.10+ (ver PROPUESTA-007)

Ver PROPUESTA-007 para el detalle.

---

### 6.3 Mejoras al modelo `Finding`

| Campo propuesto | Tipo | Valor por defecto | Justificación |
|-----------------|------|-------------------|---------------|
| `suppressed` | `bool` | `False` | Marcar findings como "won't fix" sin borrarlos del JSON |
| `timestamp` | `str` | `""` | Cuándo se generó el finding (ISO UTC); útil para tendencias temporales |
| `hash` | `str` | `""` | Hash del contenido de la línea; permite detectar si el finding sigue activo en re-scans |

Propuesta de campos adicionales en el dataclass:
```python
# Añadir en Finding (después de context_lines):
    suppressed:     bool = False   # marcado como won't-fix
    timestamp:      str  = ""      # ISO UTC cuando se generó
    hash:           str  = ""      # MD5 del contenido de línea (para re-scan diff)
```

---

### 6.4 Edge cases no cubiertos en parsers

| Parser | Input problemático | Comportamiento actual | Corrección |
|--------|--------------------|-----------------------|------------|
| `parse_flake8` | Línea con path que contiene `:` (Windows o paths con timestamp) | El regex `(.+?)` hace match greedy mínimo, puede capturar path incorrecto | Usar `re.compile(r"^(.+?):(\d+):(\d+):\s+([A-Z]\d+)\s+(.+)$")` con `Path` validation |
| `parse_mypy` | Línea `note:` sin código entre `[]` | `code = code or "mypy"` — funciona, pero el grupo 5 es `None` y no se loguea | OK por ahora, documentar |
| `parse_bandit` | JSON con `"results": null` en lugar de `[]` | `for issue in data.get("results", [])` → `for issue in None` → `TypeError` | Añadir `or []`: `for issue in (data.get("results") or [])` |
| `run_bago_lint` | Archivos .py con encoding no-UTF8 | `read_text(errors="replace")` — cubierto | OK |
| `FindingsDB.load` | `scan_id` que no existe en disco | `db.path.exists()` → False → retorna DB vacía sin error | Documentar comportamiento o añadir warning |

#### Patch para parse_bandit (línea 167):

```
FILE: .bago/tools/findings_engine.py (línea 167)

OLD:         for issue in data.get("results", []):
NEW:         for issue in (data.get("results") or []):
```

---

### 6.5 Import style inconsistente en `findings_engine.py`

```
FILE: .bago/tools/findings_engine.py (línea 12)

OLD: import json, re, subprocess, sys, datetime, hashlib
```

El resto del módulo usa `datetime.datetime.now(datetime.timezone.utc)` (estilo módulo completo) que es válido. Sin embargo, `from typing import Optional` ya está importado (línea 15) y no se usa en el código actual (los tipos usan `str | None` — ver PROPUESTA-007). Esto es inconsistente.

```
NEW: import json, re, subprocess, sys, datetime, hashlib
     from typing import Optional  # ← ya existe; usar en vez de str | None (ver P-007)
```

No es necesario cambiar el estilo de import de `datetime` ya que el módulo lo usa coherentemente como `datetime.datetime.*`.

---

## PROPUESTA-007: `str | None` y `"FindingsDB | None"` requieren Python 3.10+

**Categoría:** Compatibilidad  
**Prioridad:** 🟡 MEDIA — regresión en Python 3.9 (aún en uso en macOS Ventura y muchos CIs)  
**Archivo:** `.bago/tools/findings_engine.py`

### Ocurrencias

#### FILE: `.bago/tools/findings_engine.py` (línea 296)
```
OLD:     def __init__(self, scan_id: str | None = None):
NEW:     def __init__(self, scan_id: Optional[str] = None):
```

#### FILE: `.bago/tools/findings_engine.py` (línea 358)
```
OLD:     def latest(cls) -> "FindingsDB | None":
NEW:     def latest(cls) -> Optional["FindingsDB"]:
```

NOTA: `Optional` ya está importado desde `typing` en línea 15. El cambio es inmediato y sin coste.

---

## ESTADO

| Métrica | Valor |
|---------|-------|
| Total de propuestas generadas | **7** |
| Total de archivos cubiertos | **45** (4 en P-001, 3 en P-002, 26+1 en P-003, 1+bago en P-004, 10 en P-005, 1 en P-006, 1 en P-007) |
| Líneas de producción a cambiar (P-001) | **9 líneas** en 4 archivos |
| Tools que ganarían routing (P-004) | **14 tools** |
| Tests nuevos propuestos (P-006) | **9 tests** |
| Propuestas 🔴 ALTA | **2** (P-001, P-004) |
| Propuestas 🟡 MEDIA | **4** (P-002, P-003, P-006, P-007) |
| Propuestas 🟢 BAJA | **1** (P-005) |

### Orden de ejecución recomendado

1. **P-001** — Corregir naive datetimes (9 cambios quirúrgicos, alto impacto, bajo riesgo)
2. **P-004** — Añadir routing en `bago` (14 entradas en COMMANDS_ADVANCED + help strings)
3. **P-007** — Corregir tipos Python 3.10+ en findings_engine (2 líneas, cero riesgo)
4. **P-002** — Afinar detector `.utcnow()` (1 línea, mejora precisión)
5. **P-006** — Mejoras findings_engine (tests + parse_bandit fix + campos Finding)
6. **P-003** — Extracción de `fail()` a bago_utils.py (requiere 27 archivos, hacer en rama separada)
7. **P-005** — Añadir docstrings faltantes (10 archivos, puramente documentación)
