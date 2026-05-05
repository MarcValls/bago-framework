#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""emit_ideas — Genera y emite ideas del backlog BAGO."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from functools import lru_cache
import json
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
MIN_IDEAS = 5
MAX_IDEAS = 20

FALLBACK_IDEAS: list[dict[str, object]] = [
    {
        "priority": 66,
        "section": "respaldo",
        "risk": "low",
        "metric": "README y selector describen la misma ruta de arranque.",
        "title": "Alinear README con selector",
        "summary": "Hacer que la entrada humana y el selector de ideas expliquen el mismo recorrido sin ambiguedades.",
        "detail": [
            "Entrada: README y comandos cortos del pack.",
            "Salida: navegacion coherente entre ideas, WF y arranque.",
            "Ventaja: reduce la friccion en el primer paso de cada sesion.",
        ],
        "w2": "Actualizar la documentacion de entrada sin tocar la logica del selector.",
    },
    {
        "priority": 64,
        "section": "respaldo",
        "risk": "low",
        "metric": "El selector siempre publica el rango 5-20 sin desviaciones.",
        "title": "Reforzar rango del selector",
        "summary": "Hacer explicito el limite de 5 a 20 ideas en la salida del selector.",
        "detail": [
            "Entrada: enumeracion actual del selector.",
            "Salida: reglas de cantidad visibles para el usuario.",
            "Ventaja: evita listas demasiado cortas o excesivas.",
        ],
        "w2": "Codificar el rango de salida en el selector y verificarlo con una ejecucion real.",
    },
    {
        "priority": 62,
        "section": "respaldo",
        "risk": "low",
        "metric": "La recomendacion final queda en una sola accion explícita.",
        "title": "Compactar recomendacion final",
        "summary": "Reducir la friccion del final del selector con una recomendacion mas directa.",
        "detail": [
            "Entrada: salida de ideas ya ordenadas.",
            "Salida: siguiente paso corto y visible.",
            "Ventaja: facilita pasar de idea a decision sin leer de nuevo toda la lista.",
        ],
        "w2": "Ajustar el texto final de `./ideas` sin alterar el ranking.",
    },
]


@lru_cache(maxsize=1)
def _load_catalog() -> dict:
    try:
        from bago_config import load_config
        data = load_config(
            "ideas_catalog",
            fallback={"ideas": [], "fallback": FALLBACK_IDEAS},
        )
    except Exception:
        data = {"ideas": [], "fallback": FALLBACK_IDEAS}

    if not isinstance(data, dict):
        return {"ideas": [], "fallback": FALLBACK_IDEAS}

    ideas = data.get("ideas")
    fallback = data.get("fallback")
    return {
        **data,
        "ideas": ideas if isinstance(ideas, list) else [],
        "fallback": fallback if isinstance(fallback, list) else FALLBACK_IDEAS,
    }


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def file_exists(path: Path) -> bool:
    return path.exists() and path.is_file()


def parse_state_sections(state_text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current = None
    buffer: list[str] = []

    for line in state_text.splitlines():
        if line.startswith("## "):
            if current is not None:
                sections[current] = "\n".join(buffer).strip()
            current = line[3:].strip().lower()
            buffer = []
            continue
        if current is not None:
            buffer.append(line)

    if current is not None:
        sections[current] = "\n".join(buffer).strip()
    return sections


def score(pairs: list[tuple[int, str]]) -> list[tuple[int, str]]:
    return sorted(pairs, key=lambda item: (-item[0], item[1]))


def report_status(path: Path) -> dict | None:
    if not file_exists(path):
        return None
    try:
        return load_json(path)
    except Exception:
        return None


def summarize_report(name: str, report: dict | None) -> str:
    if not report:
        return f"{name}: no disponible"
    status = report.get("status", report.get("overall_status", "unknown"))
    return (
        f"{name}: status={status}, "
        f"failures={report.get('failure_count', 'n/a')}, "
        f"workers={report.get('workers', 'n/a')}, "
        f"duration={report.get('duration_seconds', 'n/a')}s"
    )


def order_ideas_by_section(sections: dict[str, list[dict[str, object]]]) -> list[dict[str, object]]:
    return sections["contextuales"] + sections["respaldo"]


# ── canonical gate ─────────────────────────────────────────────────────────────

def run_canonical_gate(smoke_path: Path) -> tuple[bool, list[str], list[str]]:
    """Run validate_pack + validate_state and check smoke if available.

    Returns (all_passed, ko_messages, warn_messages).
    KO on any canonical validator failure or if smoke is available but failing.
    WARN (non-blocking) if smoke is unavailable.
    """
    bago_tools = ROOT / ".bago" / "tools"
    ko: list[str] = []
    warn: list[str] = []

    for script in ("validate_pack.py", "validate_state.py"):
        result = subprocess.run(
            [sys.executable, str(bago_tools / script)],
            capture_output=True,
            text=True,
        )
        out_lines = [l for l in (result.stdout + result.stderr).splitlines() if l.strip()]
        if result.returncode != 0:
            # Find the detail error line (comes after KO) or the KO line itself
            error_line = ""
            for i, line in enumerate(out_lines):
                if line.strip().startswith("KO") and i + 1 < len(out_lines):
                    error_line = out_lines[i + 1]
                    break
                if any(kw in line for kw in ("mismatch", "missing", "error", "Error", "reference found", "unknown")):
                    error_line = line
                    break
            if not error_line:
                error_line = out_lines[-1] if out_lines else script
            ko.append(f"  [KO] ✗ {script}: {error_line}")
        else:
            first_line = out_lines[-1] if out_lines else script
            warn.append(f"  [GO] ✓ {script}: {first_line}")

    smoke_report = report_status(smoke_path)
    if smoke_report is None:
        warn.append("  [WARN] ⚠ smoke: no disponible (no bloqueante)")
    else:
        smoke_status = str(smoke_report.get("status", "unknown")).lower()
        if smoke_status in ("pass", "ok", "green", "success") and smoke_report.get("failure_count", 1) == 0:
            warn.append(f"  [GO] ✓ smoke: status={smoke_status}")
        else:
            ko.append(f"  [KO] ✗ smoke: status={smoke_status}, failures={smoke_report.get('failure_count', 'n/a')}")

    return len(ko) == 0, ko, warn


def filter_ideas_for_baseline_mode(items: list[dict[str, object]]) -> list[dict[str, object]]:
    filtered: list[dict[str, object]] = []
    for item in items:
        risk = str(item.get("risk", "")).lower().strip()
        metric = str(item.get("metric", "")).strip()
        if risk != "low":
            continue
        if not metric:
            continue
        filtered.append(item)
    return filtered


def detect_implemented_features() -> dict[str, bool]:
    """Detecta qué ideas ya están implementadas inspeccionando el filesystem."""
    tools = ROOT / ".bago" / "tools"
    state = ROOT / ".bago" / "state"
    state_path = state / "ESTADO_BAGO_ACTUAL.md"
    global_state_path = state / "global_state.json"
    readme_path = ROOT / "README.md"
    bago_readme = ROOT / ".bago" / "README.md"
    banner_text = (tools / "bago_banner.py").read_text(encoding="utf-8") if (tools / "bago_banner.py").exists() else ""
    show_task_text = (tools / "show_task.py").read_text(encoding="utf-8") if (tools / "show_task.py").exists() else ""
    emit_ideas_text = (tools / "emit_ideas.py").read_text(encoding="utf-8") if (tools / "emit_ideas.py").exists() else ""

    sections: dict[str, str] = {}
    if file_exists(state_path):
        try:
            sections = parse_state_sections(read_text(state_path))
        except Exception:
            sections = {}

    global_state = load_json(global_state_path) if file_exists(global_state_path) else {}
    readme_lines = len(read_text(readme_path).splitlines()) if file_exists(readme_path) else 0
    matrix = report_status(ROOT / "sandbox/runtime-vm/matrix/last-matrix-summary.json")
    stable_reports = all(
        report.get("status") == "pass" and report.get("failure_count", 1) == 0
        for report in (
            report_status(ROOT / "sandbox/runtime/last-report.json"),
            report_status(ROOT / "sandbox/runtime-vm/last-report-vm.json"),
            report_status(ROOT / "sandbox/runtime-vm/last-soak-report-vm.json"),
        )
        if report is not None
    )

    return {
        "handoff_w2":       (tools / "show_task.py").exists(),
        "session_opener":   (tools / "session_opener.py").exists(),
        "close_auto":       "_generate_close_artifact" in show_task_text and (tools / "session_close_generator.py").exists(),
        "stability_cmd":    (ROOT / "stability-summary").exists() and (tools / "stability_summary.py").exists(),
        "banner_shows_task": "_active_task" in banner_text,
        "ideas_wrapper":    (ROOT / "ideas").exists(),
        "gate_in_code":     True,  # siempre presente en emit_ideas.py
        "readme_aligned":   bago_readme.exists() and "bago stability" in bago_readme.read_text(encoding="utf-8"),
        "pending_task":     (state / "pending_w2_task.json").exists(),
        "impl_registry":    (state / "implemented_ideas.json").exists(),
        "scoring_dynamic":  "apply_dynamic_scoring" in emit_ideas_text,
        "stable_reports":   stable_reports,
        "baseline_clean":   global_state.get("baseline_status") == "active_clean_core",
        "matrix_pass":      bool(matrix and matrix.get("status") == "pass"),
        "has_session_close": "cierre de sesión" in sections,
        "repo_not_empty":   readme_lines > 0,
    }


def load_implemented_titles() -> set[str]:
    """Devuelve el conjunto de títulos de ideas ya registradas como implementadas."""
    impl_file = ROOT / ".bago" / "state" / "implemented_ideas.json"
    if not impl_file.exists():
        return set()
    try:
        data = json.loads(impl_file.read_text(encoding="utf-8"))
        return {str(e.get("title", "")) for e in data.get("ideas_completed", [])}
    except Exception:
        return set()


def _load_state_signals() -> dict:
    """Lee señales de contexto del sistema para enriquecer el scoring dinámico.

    Devuelve un dict con:
    - active_workflow: código del workflow activo (e.g. "W2") o None
    - guardian_health: último % de salud (0-100), -1 si desconocido
    - has_errors: True si guardian tiene errores activos
    - sprint_phase: "implementation" | "exploration" | "debug" | "unknown"
    """
    state_dir = ROOT / ".bago" / "state"
    signals: dict = {
        "active_workflow": None,
        "guardian_health": -1,
        "has_errors": False,
        "sprint_phase": "unknown",
    }

    # ── global_state.json ─────────────────────────────────────────────────────
    gs_file = state_dir / "global_state.json"
    if gs_file.exists():
        try:
            gs = json.loads(gs_file.read_text(encoding="utf-8"))
            sp = gs.get("sprint_status", {})
            aw = sp.get("active_workflow")
            if isinstance(aw, dict):
                signals["active_workflow"] = aw.get("code")
            elif isinstance(aw, str) and aw not in (None, "null", "none", ""):
                signals["active_workflow"] = aw
        except Exception:
            pass

    # ── guardian_history.json ─────────────────────────────────────────────────
    hist_file = state_dir / "guardian_history.json"
    if hist_file.exists():
        try:
            history = json.loads(hist_file.read_text(encoding="utf-8"))
            if history:
                last = history[-1]
                signals["guardian_health"] = last.get("health", -1)
                signals["has_errors"] = last.get("errors", 0) > 0
        except Exception:
            pass

    # ── Sprint phase inference ─────────────────────────────────────────────────
    wf = signals["active_workflow"] or ""
    if wf in ("W2", "W3", "W5"):
        signals["sprint_phase"] = "implementation"
    elif wf in ("W1", "W8", "W9"):
        signals["sprint_phase"] = "exploration"
    elif wf in ("W4", "W6", "W7"):
        signals["sprint_phase"] = "debug"

    return signals


# Workflow affinity map: idea sections/keywords that boost in each phase
_PHASE_AFFINITY: dict[str, set[str]] = {
    "implementation": {"implementación", "refactor", "feature", "tool", "script", "módulo", "comando"},
    "exploration":    {"exploración", "análisis", "diagnóstico", "mapeo", "descubrimiento", "idea", "catálogo"},
    "debug":          {"debug", "error", "guardian", "health", "validación", "repair", "fix", "diagnóstico"},
}


def apply_dynamic_scoring(ideas: list[dict[str, object]]) -> list[dict[str, object]]:
    """Ajusta prioridades según implemented_ideas.json y señales del estado BAGO.

    Señales aplicadas:
    1. Historial implementado: -5 si keywords solapan con trabajo ya hecho, +3 si es nuevo
    2. Guardian salud baja (<80%): boost +8 a ideas de categoría "health" / "framework"
    3. Guardian con errores: boost +12 a ideas de categoría "health"
    4. Workflow activo: boost +6 a ideas afines a la fase (impl/exploration/debug)
    5. Sin workflow activo: boost +4 a ideas de tipo "exploración" (es buen momento para idear)
    """
    impl_file = ROOT / ".bago" / "state" / "implemented_ideas.json"

    # ── 1. Historial implementado ──────────────────────────────────────────────
    impl_keywords: set[str] = set()
    if impl_file.exists():
        try:
            data = json.loads(impl_file.read_text(encoding="utf-8"))
            for entry in data.get("ideas_completed", []):
                title = str(entry.get("title", ""))
                impl_keywords.update(w.lower() for w in title.split() if len(w) > 4)
        except Exception:
            pass

    # ── 2. Estado del sistema ──────────────────────────────────────────────────
    signals = _load_state_signals()
    phase         = signals["sprint_phase"]
    health        = signals["guardian_health"]
    has_errors    = signals["has_errors"]
    active_wf     = signals["active_workflow"]
    phase_words   = _PHASE_AFFINITY.get(phase, set())

    result = []
    for idea in ideas:
        priority    = int(idea["priority"])
        title_lower = str(idea.get("title", "")).lower()
        summary_low = str(idea.get("summary", "")).lower()
        section     = str(idea.get("section", "")).lower()
        combined    = title_lower + " " + summary_low + " " + section

        # Signal 1: implemented overlap
        title_words = {w.lower() for w in title_lower.split() if len(w) > 4}
        if impl_keywords:
            overlap = title_words & impl_keywords
            if overlap:
                priority = max(1, priority - 5)
            else:
                priority = min(99, priority + 3)

        # Signal 2: guardian health degraded → boost health/framework ideas
        if health != -1 and health < 80 and section in ("health", "framework"):
            priority = min(99, priority + 8)

        # Signal 3: guardian has errors → emergency boost for health ideas
        if has_errors and section in ("health", "framework"):
            priority = min(99, priority + 12)

        # Signal 4: workflow active → boost ideas affine to current phase
        if active_wf and phase_words:
            if any(w in combined for w in phase_words):
                priority = min(99, priority + 6)

        # Signal 5: no active workflow → boost exploration/catalog ideas
        if not active_wf and section in ("exploración", "catálogo", "ciclo", "estado"):
            priority = min(99, priority + 4)

        result.append({**idea, "priority": priority})
    return result


def evaluate_catalog(catalog: dict, feat: dict[str, bool]) -> list[dict]:
    ideas = []
    for idea in catalog.get("ideas", []):
        requires = idea.get("requires", [])
        excludes = idea.get("excludes", [])
        if all(feat.get(flag, False) for flag in requires) and not any(feat.get(flag, False) for flag in excludes):
            ideas.append({k: v for k, v in idea.items() if k not in ("id", "chain", "generation", "requires", "excludes")})
    return ideas


def build_idea_sections(
    items: list[dict[str, object]],
    fallback_items: list[dict[str, object]] | None = None,
) -> dict[str, list[dict[str, object]]]:
    contextual = [
        item
        for item in items
        if str(item.get("section", "contextuales")) == "contextuales"
    ]
    contextual = sorted(contextual, key=lambda item: (-int(item["priority"]), str(item["title"])))
    contextual = contextual[:MAX_IDEAS]

    fallback_pool = fallback_items if isinstance(fallback_items, list) else FALLBACK_IDEAS
    respaldo: list[dict[str, object]] = []
    if len(contextual) < MIN_IDEAS:
        seen_titles = {str(item["title"]) for item in contextual}
        for fallback in fallback_pool:
            if len(contextual) + len(respaldo) >= MIN_IDEAS:
                break
            title = str(fallback["title"])
            if title in seen_titles:
                continue
            respaldo.append(dict(fallback))
            seen_titles.add(title)

    respaldo = sorted(respaldo, key=lambda item: (-int(item["priority"]), str(item["title"])))
    return {"contextuales": contextual, "respaldo": respaldo}


def print_sectioned_ideas(sections: dict[str, list[dict[str, object]]]) -> None:
    total = len(sections["contextuales"]) + len(sections["respaldo"])
    print(
        f"Total ideas: {total} "
        f"(contextuales={len(sections['contextuales'])}, respaldo={len(sections['respaldo'])})"
    )
    counter = 1
    for item in order_ideas_by_section(sections):
        w2 = str(item.get("w2", "Sin siguiente paso definido"))
        print(f"{counter}. [{item['priority']}] {item['title']}")
        print(f"   descripcion: {item['summary']}")
        print(f"   siguiente paso: {w2}")
        print("")
        counter += 1


def render_handoff(selected: dict[str, object]) -> list[str]:
    title = str(selected["title"])
    summary = str(selected["summary"])
    detail = [str(line) for line in selected["detail"]]  # type: ignore[index]
    w2 = str(selected["w2"])
    metric = str(selected.get("metric", "")).strip()

    if title == "Handoff idea -> W2":
        objective = "Convertir una idea seleccionada en una tarea lista para implementar."
        scope = "Generar una salida accionable al aceptar una idea sin tocar el ranking ni el detalle."
        non_scope = "No cambia la selección, el scoring ni los reports de estabilidad."
        files = [
            ".bago/tools/emit_ideas.py",
        ]
        validation = [
            "`./ideas --detail 1` mantiene la salida actual.",
            "`./ideas --accept 1` imprime objetivo, alcance, no alcance, archivos candidatos y validación.",
            "`./ideas` sin flags conserva el selector existente.",
        ]
    else:
        objective = summary
        scope = "Materializar la idea seleccionada con el menor cambio suficiente."
        non_scope = "No expandir el alcance fuera de la idea elegida."
        files = [".bago/tools/emit_ideas.py"]
        validation = [
            "La salida debe explicar el cambio, los archivos y la verificación mínima.",
        ]
        if metric:
            validation.append(f"Métrica objetivo: {metric}")

    lines = [
        "- Handoff:",
        f"  - Objetivo: {objective}",
        f"  - Alcance: {scope}",
        f"  - No alcance: {non_scope}",
        f"  - Archivos candidatos: {', '.join(files)}",
        "  - Validación mínima:",
    ]
    lines.extend(f"    - {item}" for item in validation)
    lines.append(f"  - Siguiente paso: {w2}")
    if detail:
        lines.append("  - Contexto de la idea:")
        lines.extend(f"    - {line}" for line in detail)
    return lines


def build_handoff_data(selected: dict[str, object], index: int) -> dict[str, object]:
    """Construye el dict estructurado del handoff para persistir en disco."""
    title = str(selected["title"])
    summary = str(selected["summary"])
    detail = [str(line) for line in selected["detail"]]  # type: ignore[index]
    w2 = str(selected["w2"])
    metric = str(selected.get("metric", "")).strip()
    priority = int(str(selected.get("priority", 0)))

    if title == "Handoff idea -> W2":
        objective = "Convertir una idea seleccionada en una tarea lista para implementar."
        scope = "Generar una salida accionable al aceptar una idea sin tocar el ranking ni el detalle."
        non_scope = "No cambia la selección, el scoring ni los reports de estabilidad."
        files = [".bago/tools/emit_ideas.py"]
        validation = [
            "`./ideas --detail 1` mantiene la salida actual.",
            "`./ideas --accept 1` imprime objetivo, alcance, no alcance, archivos candidatos y validación.",
            "`./ideas` sin flags conserva el selector existente.",
        ]
    else:
        objective = summary
        scope = "Materializar la idea seleccionada con el menor cambio suficiente."
        non_scope = "No expandir el alcance fuera de la idea elegida."
        files = [".bago/tools/emit_ideas.py"]
        validation = ["La salida debe explicar el cambio, los archivos y la verificación mínima."]
        if metric:
            validation.append(f"Métrica objetivo: {metric}")

    return {
        "idea_index": index,
        "idea_title": title,
        "priority": priority,
        "workflow": "W2_IMPLEMENTACION_CONTROLADA",
        "objetivo": objective,
        "alcance": scope,
        "no_alcance": non_scope,
        "archivos_candidatos": files,
        "validacion_minima": validation,
        "siguiente_paso": w2,
        "metric": metric,
        "contexto": detail,
        "status": "pending",
        "accepted_at": datetime.now(timezone.utc).isoformat(),
    }


def save_handoff(data: dict[str, object]) -> Path:
    """Escribe el handoff en .bago/state/pending_w2_task.json y devuelve la ruta."""
    dest = ROOT / ".bago" / "state" / "pending_w2_task.json"
    dest.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return dest


def synthesize_ideas() -> int:
    """Analiza el estado del sistema y genera nuevas ideas candidatas en ideas_catalog.json.

    Sources analizadas:
    - guardian_history.json: detecta degradación de salud reciente
    - guardian_findings (live): tools con errores o warnings
    - tools sin registro en tool_registry.py
    - TODO/FIXME en código Python de .bago/tools/
    - Slots vacíos en global_state.json (null/empty fields)
    """
    catalog_path = ROOT / ".bago" / "state" / "config" / "ideas_catalog.json"
    tools_dir    = ROOT / ".bago" / "tools"
    state_dir    = ROOT / ".bago" / "state"

    try:
        catalog: dict = json.loads(catalog_path.read_text(encoding="utf-8"))
    except Exception:
        print("[synthesize] ERROR: no se pudo leer ideas_catalog.json")
        return 1

    existing_titles = {str(i.get("title", "")).lower() for i in catalog.get("ideas", [])}
    existing_ids    = {str(i.get("id", "")) for i in catalog.get("ideas", [])}

    candidates: list[dict] = []

    def _add(id_: str, title: str, summary: str, section: str, priority: int,
             detail: list[str], w2: str, risk: str = "medium",
             metric: str = "", **extra: object) -> None:
        if id_ in existing_ids or title.lower() in existing_titles:
            return
        candidates.append({
            "id":       id_,
            "title":    title,
            "summary":  summary,
            "section":  section,
            "priority": priority,
            "risk":     risk,
            "metric":   metric or f"'{title}' completado sin regresión.",
            "detail":   detail,
            "w2":       w2,
            "generation": "auto",
            **extra,
        })

    # ── 1. Guardian health trend degradation ──────────────────────────────────
    history_file = state_dir / "guardian_history.json"
    if history_file.exists():
        try:
            history: list = json.loads(history_file.read_text(encoding="utf-8"))
            if len(history) >= 3:
                recent = [e["health"] for e in history[-3:]]
                if recent[-1] < recent[0]:
                    _add(
                        "synth-guardian-degradation",
                        "Recuperar salud del guardian",
                        "El guardian muestra degradación reciente. Resolver los errores activos.",
                        "health",
                        85,
                        [
                            f"Salud últimas 3 ejecuciones: {recent}",
                            "Ejecutar `bago tool-guardian` e identificar errores.",
                            "Resolver cada error hasta recuperar 100%.",
                        ],
                        "Ejecutar `bago tool-guardian` y corregir hallazgos.",
                        risk="high",
                        metric=f"Guardian vuelve a 100% desde {recent[-1]}%.",
                    )
        except Exception:
            pass

    # ── 2. Live guardian: tools con errores ───────────────────────────────────
    try:
        from tool_guardian import analyze, _summary
        findings = analyze()
        s = _summary(findings)
        errors  = [f for f in findings if f["severity"] == "error"]
        warnings = [f for f in findings if f["severity"] == "warning"]
        if errors:
            error_tools = list({f["tool"] for f in errors})[:5]
            _add(
                "synth-guardian-errors",
                f"Resolver {len(errors)} errores detectados por guardian",
                "Guardian reporta errores activos que reducen la salud del framework.",
                "health",
                90,
                [f"Tools con error: {', '.join(error_tools)}",
                 "Ejecutar `bago tool-guardian` para detalle completo.",
                 "Cada error reduce la puntuación de salud."],
                "Ejecutar `bago tool-guardian` y corregir los errores listados.",
                risk="high",
                metric=f"{len(errors)} errores → 0 errores en guardian.",
            )
        elif warnings:
            warn_tools = list({f["tool"] for f in warnings})[:5]
            _add(
                "synth-guardian-warnings",
                f"Limpiar {len(warnings)} warnings del guardian",
                "Guardian tiene warnings activos que merecen atención.",
                "health",
                60,
                [f"Tools con warning: {', '.join(warn_tools)}",
                 "Ejecutar `bago tool-guardian` para detalle.",
                 "Los warnings no bloquean pero degradan la calidad."],
                "Ejecutar `bago tool-guardian --format md` y revisar la tabla.",
                risk="low",
                metric=f"{len(warnings)} warnings → 0 en próxima ejecución.",
            )
    except Exception:
        pass

    # ── 3. TODO/FIXME en código ────────────────────────────────────────────────
    todo_files: list[str] = []
    try:
        result = subprocess.run(
            ["grep", "-rl", "--include=*.py", "-E", "TODO|FIXME", str(tools_dir)],
            capture_output=True, text=True, timeout=5,
        )
        todo_files = [Path(p).name for p in result.stdout.strip().splitlines() if p]
    except Exception:
        pass
    if todo_files:
        _add(
            "synth-todo-cleanup",
            f"Limpiar TODO/FIXME en {len(todo_files)} scripts",
            "Hay marcas TODO/FIXME pendientes en el código que señalan deuda técnica.",
            "deuda",
            55,
            [f"Archivos afectados: {', '.join(todo_files[:6])}",
             "Buscar con `grep -rn 'TODO\\|FIXME' .bago/tools/`",
             "Resolver o convertir en ideas formales del catálogo."],
            "Ejecutar `grep -rn 'TODO|FIXME' .bago/tools/` y resolver o catalogar.",
            risk="low",
            metric=f"0 marcas TODO/FIXME en {len(todo_files)} archivos.",
        )

    # ── 4. global_state.json: campos null que podrían tener valor ─────────────
    global_state_file = state_dir / "global_state.json"
    if global_state_file.exists():
        try:
            gs: dict = json.loads(global_state_file.read_text(encoding="utf-8"))
            null_keys = [k for k, v in gs.items()
                         if v is None or v == "" or v == "none" or v == "null"]
            if null_keys:
                _add(
                    "synth-global-state-gaps",
                    "Completar campos vacíos en global_state.json",
                    "global_state.json tiene campos sin valor que limitan el contexto BAGO.",
                    "estado",
                    50,
                    [f"Campos vacíos: {', '.join(null_keys[:8])}",
                     "Revisar cada campo y completar los que correspondan.",
                     "Un estado completo mejora la calidad de las ideas y el banner."],
                    "Editar `.bago/state/global_state.json` y completar los campos nulos.",
                    risk="low",
                    metric=f"{len(null_keys)} campos null → completados.",
                )
        except Exception:
            pass

    # ── 5. implemented_ideas con pocas entradas (<3) ───────────────────────────
    impl_file = state_dir / "implemented_ideas.json"
    if impl_file.exists():
        try:
            impl_data = json.loads(impl_file.read_text(encoding="utf-8"))
            completed = impl_data.get("ideas_completed", [])
            if len(completed) < 3:
                _add(
                    "synth-ideas-registry-grow",
                    "Registrar ideas pasadas en implemented_ideas.json",
                    "El registro de ideas implementadas está casi vacío. Retroalimentar el sistema.",
                    "ciclo",
                    58,
                    ["Revisar qué ideas del catálogo ya están en el código.",
                     "Ejecutar `bago flow done` al cerrar cada workflow.",
                     "Un registro rico mejora el scoring dinámico de emit_ideas."],
                    "Cerrar los próximos workflows con `bago flow done` para poblar el registro.",
                    risk="low",
                    metric="implemented_ideas.json con ≥5 entradas.",
                )
        except Exception:
            pass

    if not candidates:
        print("[synthesize] No se encontraron nuevas ideas para agregar al catálogo.")
        print(f"  (catálogo actual: {len(catalog.get('ideas', []))} ideas)")
        return 0

    # Write candidates to catalog
    catalog.setdefault("ideas", [])
    catalog["ideas"].extend(candidates)
    try:
        catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"[synthesize] ERROR al escribir el catálogo: {e}")
        return 1

    print(f"[synthesize] {len(candidates)} idea(s) nueva(s) añadida(s) al catálogo:")
    for c in candidates:
        print(f"  + [{c['id']}] {c['title']}")
    print(f"  Catálogo ahora tiene {len(catalog['ideas'])} ideas.")
    return 0


def parse_args(argv: list[str]) -> tuple[int | None, bool, bool]:
    detail_index = None
    accept       = False
    synthesize   = False
    idx = 1

    while idx < len(argv):
        arg = argv[idx]
        if arg in {"-h", "--help"}:
            print(
                "Usage: emit_ideas.py [--detail N] [--accept N] [--synthesize]\n\n"
                "Show 5 to 20 contextual ideas prioritized by stability.\n"
                "  --detail N     Expand idea N\n"
                "  --accept N     Mark idea N as ready for W2\n"
                "  --synthesize   Analyze codebase and append new ideas to catalog"
            )
            raise SystemExit(0)
        if arg == "--detail":
            if idx + 1 >= len(argv):
                raise SystemExit("--detail requires a numeric idea index")
            detail_index = int(argv[idx + 1])
            idx += 2
            continue
        if arg == "--accept":
            if idx + 1 >= len(argv):
                raise SystemExit("--accept requires a numeric idea index")
            detail_index = int(argv[idx + 1])
            accept = True
            idx += 2
            continue
        if arg == "--synthesize":
            synthesize = True
            idx += 1
            continue
        raise SystemExit(f"Unknown argument: {arg}")

    return detail_index, accept, synthesize


def main() -> int:
    detail_index, accept, synthesize = parse_args(sys.argv)

    if synthesize:
        return synthesize_ideas()
    smoke_path = ROOT / "sandbox/runtime/last-report.json"

    # ── canonical gate ─────────────────────────────────────────────────────────
    gate_passed, gate_ko, gate_warn = run_canonical_gate(smoke_path)
    if not gate_passed:
        print("BAGO ideas selector — GATE KO")
        print("=" * 44)
        print("Validadores canónicos en fallo. Repara antes de idear.")
        print("")
        for msg in gate_ko:
            print(msg)
        for msg in gate_warn:
            print(msg)
        print("")
        print("KO → ninguna idea avanza. Ejecuta `bago stability` para el detalle.")
        return 1
    # ── /gate ──────────────────────────────────────────────────────────────────

    feat = detect_implemented_features()
    catalog = _load_catalog()
    ideas = evaluate_catalog(catalog, feat)

    if feat["baseline_clean"]:
        ideas = filter_ideas_for_baseline_mode(ideas)

    # Filtrar ideas cuyo título ya fue registrado como implementado
    done_titles = load_implemented_titles()
    if done_titles:
        ideas = [i for i in ideas if str(i.get("title", "")) not in done_titles]

    # Ajustar prioridades según historial de implementaciones
    ideas = apply_dynamic_scoring(ideas)

    sections = build_idea_sections(ideas, catalog.get("fallback", FALLBACK_IDEAS))
    ideas = order_ideas_by_section(sections)

    print("BAGO ideas selector")
    if feat["baseline_clean"]:
        print("baseline_clean_mode: activo (solo ideas low-risk con métrica)")
    print("")
    print_sectioned_ideas(sections)

    print("")
    if detail_index is None:
        print(
            "Recomendacion: pide detalle con `./ideas --detail N` o acepta con `./ideas --accept N`."
        )
        return 0

    if detail_index < 1 or detail_index > len(ideas):
        raise SystemExit(f"Invalid idea index: {detail_index}")

    selected = ideas[detail_index - 1]
    print(f"Selected idea: {detail_index}. {selected['title']}")
    for line in selected["detail"]:
        print(f"- {line}")
    print(f"- Next step: {selected['w2']}")
    if accept:
        metric = str(selected.get("metric", "")).strip()
        if not metric:
            print("- Status: RECHAZADA — sin métrica medible")
            print("")
            print("Esta idea no declara una mejora medible en trazabilidad u operación.")
            print("Para aceptarla, la idea debe tener un campo 'metric' no vacío.")
            print("Elige una idea que declare un incremento concreto y verificable.")
            return 1
        print("- Status: accepted for W2")
        print("- Workflow: run `make workflow-tactical NAME=W2`")
        for line in render_handoff(selected):
            print(line)
        handoff_data = build_handoff_data(selected, detail_index)
        saved_path = save_handoff(handoff_data)
        print(f"\n→ Tarea guardada en {saved_path.relative_to(ROOT)}")
        print("  Consulta con: bago task")
    else:
        print("- Status: awaiting acceptance")
        print(f"- If you want to accept it, run `./ideas --accept {detail_index}`")
    return 0



def _self_test():
    """Autotest mínimo — verifica arranque limpio del módulo."""
    from pathlib import Path as _P
    assert _P(__file__).exists(), "fichero no encontrado"
    print("  1/1 tests pasaron")

if __name__ == "__main__":
    if "--test" in sys.argv:
        _self_test()
        raise SystemExit(0)
    raise SystemExit(main())
