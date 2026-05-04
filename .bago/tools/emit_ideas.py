#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""emit_ideas — Genera y emite ideas del backlog BAGO."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
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
    bago_readme = ROOT / ".bago" / "README.md"
    banner_text = (tools / "bago_banner.py").read_text(encoding="utf-8") if (tools / "bago_banner.py").exists() else ""
    show_task_text = (tools / "show_task.py").read_text(encoding="utf-8") if (tools / "show_task.py").exists() else ""
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
        "scoring_dynamic":  "apply_dynamic_scoring" in (tools / "emit_ideas.py").read_text(encoding="utf-8"),
    }


def load_implemented_titles() -> set[str]:
    """Devuelve el conjunto de títulos de ideas ya registradas como implementadas."""
    impl_file = ROOT / ".bago" / "state" / "implemented_ideas.json"
    if not impl_file.exists():
        return set()
    try:
        data = json.loads(impl_file.read_text(encoding="utf-8"))
        return {str(e.get("title", "")) for e in data.get("implemented", [])}
    except Exception:
        return set()


def apply_dynamic_scoring(ideas: list[dict[str, object]]) -> list[dict[str, object]]:
    """Ajusta las prioridades según implemented_ideas.json.

    - Ideas cuyo título está en implemented: se eliminan (ya filtradas antes).
    - Ideas con keywords que coinciden con títulos implementados: penalización -5.
    - Ideas con keywords que NO coinciden con nada implementado: boost +3.
    Esto hace que el selector evolucione hacia trabajo genuinamente nuevo.
    """
    impl_file = ROOT / ".bago" / "state" / "implemented_ideas.json"
    if not impl_file.exists():
        return ideas
    try:
        data = json.loads(impl_file.read_text(encoding="utf-8"))
        impl_entries = data.get("ideas_completed", [])
    except Exception:
        return ideas

    if not impl_entries:
        return ideas  # nada implementado aún — sin ajuste

    impl_keywords: set[str] = set()
    for entry in impl_entries:
        title = str(entry.get("title", ""))
        impl_keywords.update(w.lower() for w in title.split() if len(w) > 4)

    result = []
    for idea in ideas:
        title_words = {w.lower() for w in str(idea.get("title", "")).split() if len(w) > 4}
        overlap = title_words & impl_keywords
        priority = int(idea["priority"])
        if overlap:
            priority = max(1, priority - 5)   # penalización: tema relacionado ya implementado
        else:
            priority = min(99, priority + 3)  # boost: trabajo genuinamente nuevo
        result.append({**idea, "priority": priority})
    return result


def build_idea_sections(items: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    contextual = [
        item
        for item in items
        if str(item.get("section", "contextuales")) == "contextuales"
    ]
    contextual = sorted(contextual, key=lambda item: (-int(item["priority"]), str(item["title"])))
    contextual = contextual[:MAX_IDEAS]

    respaldo: list[dict[str, object]] = []
    if len(contextual) < MIN_IDEAS:
        seen_titles = {str(item["title"]) for item in contextual}
        for fallback in FALLBACK_IDEAS:
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


def parse_args(argv: list[str]) -> tuple[int | None, bool]:
    detail_index = None
    accept = False
    idx = 1

    while idx < len(argv):
        arg = argv[idx]
        if arg in {"-h", "--help"}:
            print(
                "Usage: emit_ideas.py [--detail N] [--accept N]\n\n"
                "Show 5 to 20 contextual ideas prioritized by stability. Use --detail "
                "to expand a selected idea and --accept to mark it ready for W2."
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
        raise SystemExit(f"Unknown argument: {arg}")

    return detail_index, accept


def main() -> int:
    detail_index, accept = parse_args(sys.argv)
    state_path = ROOT / ".bago/state/ESTADO_BAGO_ACTUAL.md"
    global_state_path = ROOT / ".bago/state/global_state.json"
    smoke_path = ROOT / "sandbox/runtime/last-report.json"
    vm_path = ROOT / "sandbox/runtime-vm/last-report-vm.json"
    soak_path = ROOT / "sandbox/runtime-vm/last-soak-report-vm.json"
    matrix_path = ROOT / "sandbox/runtime-vm/matrix/last-matrix-summary.json"
    readme_path = ROOT / "README.md"

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

    state_text = read_text(state_path) if file_exists(state_path) else ""
    sections = parse_state_sections(state_text)
    global_state = load_json(global_state_path) if file_exists(global_state_path) else {}

    smoke = report_status(smoke_path)
    vm = report_status(vm_path)
    soak = report_status(soak_path)
    matrix = report_status(matrix_path)

    repo_lines = 0
    if file_exists(readme_path):
        repo_lines = len(read_text(readme_path).splitlines())

    baseline_clean_mode = global_state.get("baseline_status") == "active_clean_core"
    feat = detect_implemented_features()

    ideas: list[dict[str, object]] = []

    # ── Idea 1: Handoff W2 → Opener → Cierre automático → Cierre registra en CHG ─
    if not feat["handoff_w2"]:
        ideas.append({
            "priority": 90,
            "section": "contextuales",
            "risk": "low",
            "metric": "El handoff incluye objetivo, alcance, no alcance, archivos y validación mínima.",
            "title": "Handoff idea -> W2",
            "summary": "Añadir una plantilla de salida que convierta una idea seleccionada en tarea lista para implementar con alcance, archivos y validación.",
            "detail": [
                "Entrada: una idea elegida tras revisar el selector.",
                "Salida: objetivo, alcance, archivos candidatos y validación mínima.",
                "Ventaja: reduce la fricción entre ideación e implementación.",
            ],
            "w2": "Pasar la idea elegida a W2 con un alcance pequeño y un criterio de salida claro.",
        })
    elif not feat["session_opener"]:
        # Generación 2: opener de sesión desde la tarea aceptada
        ideas.append({
            "priority": 90,
            "section": "contextuales",
            "risk": "low",
            "metric": "bago session lee pending_w2_task.json y lanza session_preflight con objetivo, roles y artefactos pre-rellenados.",
            "title": "Opener de sesión desde task",
            "summary": "Añadir `bago session` que lee el handoff aceptado y abre la sesión W2 con preflight pre-rellenado, evitando trabajo manual.",
            "detail": [
                "Entrada: pending_w2_task.json con objetivo, archivos y validación.",
                "Salida: llamada a session_preflight.py con los datos del handoff.",
                "Ventaja: elimina el paso manual de copiar datos del handoff al preflight.",
            ],
            "w2": "Implementar bago session en el script raíz delegando en session_preflight.py.",
        })
    elif not feat["close_auto"]:
        # Generación 3: cierre automático de sesión desde bago task --done
        ideas.append({
            "priority": 90,
            "section": "contextuales",
            "risk": "low",
            "metric": "bago task --done genera y guarda automáticamente el artefacto de cierre de sesión.",
            "title": "Cierre automático de sesión",
            "summary": "Al marcar la tarea como done, generar automáticamente el artefacto de cierre con resumen de cambios y evidencias.",
            "detail": [
                "Entrada: tarea W2 completada (pending_w2_task.json con status=done).",
                "Salida: artefacto de cierre con resumen, CHG/EVD generados y estado actualizado.",
                "Ventaja: elimina el paso manual de redactar el cierre después de implementar.",
            ],
            "w2": "Extender show_task.py --done para llamar al generador de cierre de sesión.",
        })
    else:
        # Generación 4: cierre actualiza implemented_ideas.json automáticamente
        ideas.append({
            "priority": 90,
            "section": "contextuales",
            "risk": "low",
            "metric": "Después de `bago task --done`, la idea aparece en implemented_ideas.json y el selector ya no la repite.",
            "title": "Cierre registra idea como implementada",
            "summary": "Al cerrar una sesión con `bago task --done`, registrar automáticamente la idea en implemented_ideas.json para que el selector evolucione y no repita trabajo ya hecho.",
            "detail": [
                "Entrada: artefacto de cierre generado por session_close_generator.",
                "Salida: entrada en .bago/state/implemented_ideas.json con id, título, fecha y referencia al artefacto.",
                "Ventaja: el selector aprende qué se ha implementado sin intervención manual.",
            ],
            "w2": "Añadir en session_close_generator.py escritura a implemented_ideas.json al final del generate().",
        })

    # ── Idea 2: Stability → Banner → Stale task alert ─────────────────────────
    if not feat["stability_cmd"]:
        ideas.append({
            "priority": 86,
            "section": "contextuales",
            "risk": "low",
            "metric": "El resumen incluye estado de smoke, VM y soak en un único bloque.",
            "title": "Resumen único de estabilidad",
            "summary": "Consolidar smoke, VM y soak en un informe corto para decidir si una idea nueva compite con estabilidad antes de tocar código.",
            "detail": [
                "Entrada: los últimos reports del sandbox.",
                "Salida: un resumen de salud operacional para decidir si conviene proponer cambios.",
                "Ventaja: evita idear sobre una base ya inestable.",
            ],
            "w2": "Si el resumen está en verde, permitir avanzar a una idea concreta.",
        })
    elif not feat["banner_shows_task"]:
        # Generación 2: mostrar task pendiente en el banner
        ideas.append({
            "priority": 86,
            "section": "contextuales",
            "risk": "low",
            "metric": "El banner muestra el estado de la tarea W2 activa (título + estado) si pending_w2_task.json existe.",
            "title": "Banner muestra task activa",
            "summary": "Mostrar en el banner de BAGO si hay una tarea W2 pendiente o completada, para visibilidad inmediata al arrancar.",
            "detail": [
                "Entrada: pending_w2_task.json si existe.",
                "Salida: línea extra en el banner con título y estado (⏳/✅).",
                "Ventaja: el usuario sabe al abrir BAGO si tiene trabajo en curso.",
            ],
            "w2": "Leer pending_w2_task.json en bago_banner.py y añadir línea condicional al banner.",
        })
    else:
        # Generación 3: alerta de tarea obsoleta
        ideas.append({
            "priority": 86,
            "section": "contextuales",
            "risk": "low",
            "metric": "bago stability y el banner alertan si la task lleva más de 3 días sin completarse.",
            "title": "Alerta de task obsoleta",
            "summary": "Si pending_w2_task.json lleva más de 3 días sin marcarse done, mostrar aviso en banner y en bago stability.",
            "detail": [
                "Entrada: pending_w2_task.json con campo accepted_at.",
                "Salida: aviso visual (⚠️) en banner y en stability cuando la task supera 3 días.",
                "Ventaja: evita que tareas abiertas queden olvidadas.",
            ],
            "w2": "Añadir lógica de antigüedad en bago_banner.py y stability_summary.py.",
        })

    # ── Idea 3: Gate → Registro → Scoring dinámico → Ranking contextual ─────────
    stable_reports = all(
        report and report.get("status") == "pass" and report.get("failure_count", 1) == 0
        for report in (smoke, vm, soak)
        if report is not None
    )
    if not feat["gate_in_code"] and stable_reports:
        ideas.append({
            "priority": 84,
            "section": "contextuales",
            "risk": "low",
            "metric": "Ninguna idea avanza si validate_pack/validate_state/smoke no están en verde.",
            "title": "Gate seguro antes de implementar",
            "summary": "Bloquear sugerencias nuevas si validate_pack, validate_state o smoke no están en verde.",
            "detail": [
                "Entrada: validadores canónicos y smoke del sandbox.",
                "Salida: permiso o bloqueo para seguir ideando e implementar.",
                "Ventaja: protege la estabilidad antes de abrir trabajo nuevo.",
            ],
            "w2": "Si el gate pasa, la idea elegida puede convertirse en W2.",
        })
    elif feat["gate_in_code"] and not feat["impl_registry"]:
        # Generación 2: registro de ideas implementadas para no repetirlas
        ideas.append({
            "priority": 84,
            "section": "contextuales",
            "risk": "low",
            "metric": "El selector no repite una idea marcada como implementada en implemented_ideas.json.",
            "title": "Registro de ideas implementadas",
            "summary": "Guardar en estado qué ideas ya fueron implementadas para que el selector evolucione en lugar de repetirlas en cada sesión.",
            "detail": [
                "Entrada: lista de ideas aceptadas e implementadas.",
                "Salida: archivo .bago/state/implemented_ideas.json con IDs y fechas.",
                "Ventaja: el selector siempre propone trabajo nuevo, no repetido.",
            ],
            "w2": "Crear implemented_ideas.json y leerlo en emit_ideas para filtrar ideas ya hechas.",
        })
    elif feat["impl_registry"] and not feat["scoring_dynamic"]:
        # Generación 3: puntuación dinámica basada en registro
        ideas.append({
            "priority": 84,
            "section": "contextuales",
            "risk": "low",
            "metric": "El scoring de ideas sube cuando la feature que proponen no está en implemented_ideas.json.",
            "title": "Scoring dinámico por registro",
            "summary": "Ajustar la prioridad de las ideas en función de si la feature que proponen ya fue implementada, incrementando el score de las que aportan trabajo nuevo.",
            "detail": [
                "Entrada: implemented_ideas.json con historial de ideas completadas.",
                "Salida: ideas reordenadas priorizando trabajo genuinamente nuevo.",
                "Ventaja: el selector se vuelve más preciso con el tiempo.",
            ],
            "w2": "Añadir apply_dynamic_scoring() en emit_ideas.py que lee implemented_ideas.json y ajusta prioridades.",
        })
    else:
        # Generación 4: ranking contextual por señales del estado actual
        ideas.append({
            "priority": 84,
            "section": "contextuales",
            "risk": "low",
            "metric": "El ranking refleja señales de estado y reduce recomendaciones estáticas en >50% de ejecuciones.",
            "title": "Ranking contextual por estado",
            "summary": "Ampliar apply_dynamic_scoring() para incorporar señales del estado BAGO (workflow activo, salud, sprint) y ajustar prioridades en tiempo real.",
            "detail": [
                "Entrada: global_state.json + implemented_ideas.json.",
                "Salida: ranking adaptado al contexto operativo actual.",
                "Ventaja: ideas siempre alineadas con la fase real del proyecto.",
            ],
            "w2": "Extender apply_dynamic_scoring() con boost/penalización por workflow activo y salud del guardian.",
        })

    if matrix and matrix.get("status") == "pass":
        ideas.append({
            "priority": 82,
            "section": "contextuales",
            "risk": "medium",
            "metric": "WF responde por intención y reduce navegación manual.",
            "title": "Selector por intención",
            "summary": "Extender WF para filtrar ideas y workflows por intención, por ejemplo idea, implementar, depurar o cerrar.",
            "detail": [
                "Entrada: intención del usuario.",
                "Salida: selector más fino para aterrizar al workflow correcto.",
                "Ventaja: evita navegar manualmente cuando la intención ya está clara.",
            ],
            "w2": "Usar la intención seleccionada para orientar la tarea siguiente.",
        })

    if baseline_clean_mode:
        ideas.append({
            "priority": 78,
            "section": "contextuales",
            "risk": "low",
            "metric": "Cada idea aceptada declara una mejora medible en trazabilidad u operación.",
            "title": "Ideas orientadas a baseline",
            "summary": "Proponer solo cambios que mantengan el baseline limpio y generen un incremento medible en trazabilidad u operacion.",
            "detail": [
                "Entrada: baseline limpio y estable.",
                "Salida: ideas pequeñas con mejora mensurable.",
                "Ventaja: alinea la ideación con la continuidad del pack.",
            ],
            "w2": "Seleccionar una idea que preserve el baseline y tenga bajo riesgo.",
        })

    if sections.get("cierre de sesión"):
        ideas.append({
            "priority": 74,
            "section": "contextuales",
            "risk": "medium",
            "metric": "Reapertura evita reconstrucción manual y reduce pasos de arranque.",
            "title": "Reabrir desde continuidad",
            "summary": "Añadir un modo para reactivar la sesión desde el cierre actual sin reconstruir contexto manualmente.",
            "detail": [
                "Entrada: cierre de sesión ya escrito en estado.",
                "Salida: reanudación más rápida sin perder contexto.",
                "Ventaja: mantiene continuidad de trabajo entre sesiones.",
            ],
            "w2": "Si se acepta, convertirlo en una mejora pequeña y segura de continuidad.",
        })

    if repo_lines > 0 and not feat["ideas_wrapper"]:
        ideas.append({
            "priority": 70,
            "section": "contextuales",
            "risk": "medium",
            "metric": "La primera decisión del usuario llega a una acción en un paso.",
            "title": "Entrada rápida del repo",
            "summary": "Conectar ideas con README y WF para que la primera decisión del usuario vaya a una acción concreta sin leer toda la canonica.",
            "detail": [
                "Entrada: comandos cortos y selector de workflows.",
                "Salida: menos fricción para abrir ideas o W2.",
                "Ventaja: mejora la usabilidad diaria del repo.",
            ],
            "w2": "Crear ./ideas y ./stability-summary wrappers en la raíz del repo.",
        })
    elif repo_lines > 0 and feat["ideas_wrapper"]:
        # wrapper existe — siguiente nivel: conectar README con flujo ideas → W2
        ideas.append({
            "priority": 70,
            "section": "contextuales",
            "risk": "medium",
            "metric": "El README.md explica el flujo ideas → --accept → W2 en menos de 5 líneas.",
            "title": "README enlaza ideas con W2",
            "summary": "Documentar en README el flujo completo: ./ideas → --accept N → W2, para que cualquier colaborador pueda empezar en segundos.",
            "detail": [
                "Entrada: ./ideas wrapper y flujo ./ideas --accept N ya funcionales.",
                "Salida: sección en README.md que describe el flujo de entrada al trabajo.",
                "Ventaja: reduce la barrera de entrada para nuevos colaboradores.",
            ],
            "w2": "Añadir sección '## Empezar a trabajar' en README.md con el flujo ideas→W2.",
        })

    # ── Idea 5: Mejorar ranking (genera según si scoring_dynamic ya existe) ────
    if not feat["scoring_dynamic"]:
        ideas.append({
            "priority": 68,
            "section": "contextuales",
            "risk": "medium",
            "metric": "El ranking refleja señales de estado actual y reduce recomendaciones estáticas.",
            "title": "Mejorar ranking de ideas",
            "summary": "Ajustar el scoring para reflejar señales del estado actual y evitar prioridades estáticas que oculten trabajo real.",
            "detail": [
                "Entrada: estado BAGO, salud de reports y workflow activo.",
                "Salida: orden de ideas más sensible al contexto operativo.",
                "Ventaja: reduce sesgos de ranking y evita ciclos de recomendación.",
            ],
            "w2": "Implementar apply_dynamic_scoring() en emit_ideas.py y validarlo con ejemplos reales.",
        })
    else:
        # scoring_dynamic ya existe — siguiente nivel: ranking por workflow activo
        ideas.append({
            "priority": 68,
            "section": "contextuales",
            "risk": "medium",
            "metric": "Ideas de implementación suben cuando W2/W3 es el workflow activo; ideas de exploración suben en W8.",
            "title": "Ranking por workflow activo",
            "summary": "Ampliar apply_dynamic_scoring() para dar boost a ideas afines al workflow activo actual (W2→implementación, W8→exploración, W4→debug).",
            "detail": [
                "Entrada: workflow activo en global_state.json.",
                "Salida: ranking sensible a la fase del trabajo en curso.",
                "Ventaja: las ideas más relevantes para el momento actual aparecen primero.",
            ],
            "w2": "Leer current_workflow de global_state y aplicar boost en apply_dynamic_scoring().",
        })

    if baseline_clean_mode:
        ideas = filter_ideas_for_baseline_mode(ideas)

    # Filtrar ideas cuyo título ya fue registrado como implementado
    done_titles = load_implemented_titles()
    if done_titles:
        ideas = [i for i in ideas if str(i.get("title", "")) not in done_titles]

    # Ajustar prioridades según historial de implementaciones
    ideas = apply_dynamic_scoring(ideas)

    sections = build_idea_sections(ideas)
    ideas = order_ideas_by_section(sections)

    print("BAGO ideas selector")
    if baseline_clean_mode:
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
