#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bago-viewer — Dashboard web para inspeccionar packs .bago
"""
from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from flask import Flask, abort, redirect, render_template, request, send_file

app = Flask(__name__)

SCAN_ROOTS = [Path.home() / "Desktop", Path.home() / "Documents"]
SCAN_MAX_DEPTH = 3
SKIP_DIRS = {
    ".git", "node_modules", ".venv", "venv", "__pycache__",
    ".Trash", "Library", "Applications",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_bago_packs(roots: list[Path], max_depth: int = SCAN_MAX_DEPTH) -> list[Path]:
    """BFS acotado — busca directorios .bago con pack.json dentro."""
    found: list[Path] = []
    queue: list[tuple[Path, int]] = [(r, 0) for r in roots if r.is_dir()]
    visited: set[Path] = set()

    while queue:
        current, depth = queue.pop(0)
        try:
            real = current.resolve()
        except OSError:
            continue
        if real in visited:
            continue
        visited.add(real)

        try:
            entries = list(current.iterdir())
        except PermissionError:
            continue

        for entry in entries:
            if not entry.is_dir():
                continue
            if entry.name.startswith(".") and entry.name != ".bago":
                continue
            if entry.name in SKIP_DIRS:
                continue
            if entry.name == ".bago" and (entry / "pack.json").exists():
                found.append(entry)
            elif depth < max_depth:
                queue.append((entry, depth + 1))

    return found


def _count_json(directory: Path) -> int:
    if not directory.is_dir():
        return 0
    return len(list(directory.glob("*.json")))


def _load_sessions(bago: Path) -> list[dict]:
    sessions = []
    sdir = bago / "state" / "sessions"
    if not sdir.is_dir():
        return sessions
    for f in sdir.glob("*.json"):
        try:
            sessions.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            pass
    # Orden cronológico real (no por nombre de archivo)
    sessions.sort(key=lambda s: s.get("created_at", ""))
    return sessions


def read_pack_info(bago: Path) -> dict:
    info: dict = {
        "path": str(bago),
        "name": bago.parent.name,
        "health": "unknown",
        "version": "?",
        "inventory_declared": {},
        "inventory_real": {},
        "last_validation": {},
        "sprint_status": {},
        "notes": "",
        "updated_at": "",
        "sessions": [],
        "task_type_counts": {},
        "role_counts": {},
        "has_report": False,
        "report_mtime": None,
        "report_stale": None,
    }

    gs_path = bago / "state" / "global_state.json"
    if gs_path.exists():
        try:
            gs = json.loads(gs_path.read_text(encoding="utf-8"))
            info["health"] = gs.get("system_health", "unknown")
            info["version"] = gs.get("bago_version", "?")
            info["inventory_declared"] = gs.get("inventory", {})
            info["last_validation"] = gs.get("last_validation", {})
            info["sprint_status"] = gs.get("sprint_status", {})
            info["notes"] = gs.get("notes", "")
            info["updated_at"] = gs.get("updated_at", "")
        except Exception:
            pass

    info["inventory_real"] = {
        "sessions": _count_json(bago / "state" / "sessions"),
        "changes": _count_json(bago / "state" / "changes"),
        "evidences": _count_json(bago / "state" / "evidences"),
    }

    sessions = _load_sessions(bago)
    info["sessions"] = sessions
    info["task_type_counts"] = dict(Counter(s.get("task_type", "?") for s in sessions))
    role_counter: Counter = Counter()
    for s in sessions:
        for r in s.get("roles_activated", []):
            role_counter[r] += 1
    info["role_counts"] = dict(role_counter.most_common(8))

    html_report = bago / "docs" / "analysis" / "BAGO_EVOLUCION_SISTEMA.html"
    info["has_report"] = html_report.exists()
    if info["has_report"]:
        mtime_ts = html_report.stat().st_mtime
        mtime_dt = datetime.fromtimestamp(mtime_ts, tz=timezone.utc)
        info["report_mtime"] = mtime_dt.strftime("%Y-%m-%d %H:%M UTC")
        if info["updated_at"]:
            try:
                state_ts = info["updated_at"].replace("Z", "+00:00")
                state_dt = datetime.fromisoformat(state_ts)
                info["report_stale"] = mtime_dt < state_dt
            except Exception:
                info["report_stale"] = None

    info["evolution"] = compute_evolution(sessions)
    return info


def _dim(value: float, max_val: float) -> float:
    """Normaliza un valor a escala 0–10."""
    if max_val == 0:
        return 0.0
    return round(min(value / max_val * 10, 10), 1)


def compute_evolution(sessions: list[dict]) -> dict | None:
    """Calcula radar data (inicio vs ahora) y señales de evolución.

    Dimensiones — todas orientadas a "más = mejor":
      1. Diversidad    → tipos de tarea únicos / total en el pack
      2. Protocolo     → % sesiones cerradas formalmente (status=closed)
      3. Alcance       → workflows únicos usados / total en el pack
      4. Foco          → inverso de roles medios por sesión (menos roles = más foco)
      5. Producción    → artefactos medios por sesión (output tangible)
      6. Rigor         → decisiones medias por sesión (gobierno de calidad)
    """
    if len(sessions) < 4:
        return None

    mid = len(sessions) // 2
    early = sessions[:mid]
    late = sessions[mid:]

    # Denominadores adaptativos: basados en lo que realmente existe en el pack
    all_types = {s.get("task_type", "") for s in sessions} - {""}
    all_wfs   = {s.get("selected_workflow", "") for s in sessions} - {""}
    max_types = max(len(all_types), 1)
    max_wfs   = max(len(all_wfs), 1)

    # Max producción/rigor: el pico real del pack (no un techo arbitrario)
    all_arts = [len(s.get("artifacts", [])) for s in sessions]
    all_decs = [len(s.get("decisions", [])) for s in sessions]
    max_art  = max(max(all_arts), 1)
    max_dec  = max(max(all_decs), 1)
    MAX_ROLES = 8  # máx roles plausibles en una sesión bien orquestada

    def _score(group: list[dict]) -> dict:
        n = len(group)

        # 1. Diversidad (tipos únicos en el período / total del pack)
        types_used = len({s.get("task_type", "") for s in group} - {""})
        diversidad = _dim(types_used, max_types)

        # 2. Protocolo (% cerradas — señal de disciplina de cierre)
        closed = sum(1 for s in group if s.get("status") == "closed")
        protocolo = _dim(closed, n)

        # 3. Alcance (workflows únicos / total usados en el pack)
        wfs = len({s.get("selected_workflow", "") for s in group} - {""})
        alcance = _dim(wfs, max_wfs)

        # 4. Foco (sesiones más focalizadas = menos roles medios = mejor)
        avg_roles = sum(len(s.get("roles_activated", [])) for s in group) / n
        foco = round(max(0.0, 10.0 - _dim(avg_roles, MAX_ROLES)), 1)

        # 5. Producción (artefactos medios / pico real del pack)
        avg_art = sum(len(s.get("artifacts", [])) for s in group) / n
        produccion = _dim(avg_art, max_art)

        # 6. Rigor (decisiones medias / pico real del pack)
        avg_dec = sum(len(s.get("decisions", [])) for s in group) / n
        rigor = _dim(avg_dec, max_dec)

        return {
            "diversidad": diversidad,
            "protocolo": protocolo,
            "alcance": alcance,
            "foco": foco,
            "produccion": produccion,
            "rigor": rigor,
        }

    e = _score(early)
    l = _score(late)

    labels = ["Diversidad\ntareas", "Protocolo\ncierre", "Alcance\nworkflows",
              "Foco\nsesión", "Producción\nartefactos", "Rigor\ndecisiones"]
    keys   = ["diversidad", "protocolo", "alcance", "foco", "produccion", "rigor"]
    icons  = ["🔀", "✅", "🛠", "🎯", "📦", "⚖️"]

    signals = []
    for key, label, icon in zip(keys, labels, icons):
        diff = round(l[key] - e[key], 1)
        signals.append({
            "key": key,
            "label": label.replace("\n", " "),
            "icon": icon,
            "before": e[key],
            "now": l[key],
            "diff": diff,
            "trend": "up" if diff > 0.3 else ("down" if diff < -0.3 else "flat"),
        })

    # Serie temporal: un punto por sesión para el line chart
    timeline = []
    for i, s in enumerate(sessions):
        roles_n = len(s.get("roles_activated", []))
        foco_val = round(max(0.0, 10.0 - _dim(roles_n, MAX_ROLES)), 1)
        timeline.append({
            "index": i + 1,
            "label": s.get("session_id", f"#{i+1}"),
            "date":  s.get("created_at", "")[:10],
            "type":  s.get("task_type", "?"),
            "closed": 1 if s.get("status") == "closed" else 0,
            "arts":  len(s.get("artifacts", [])),
            "decs":  len(s.get("decisions", [])),
            "roles": roles_n,
            "foco":  foco_val,
        })

    return {
        "labels":      labels,
        "early":       [e[k] for k in keys],
        "late":        [l[k] for k in keys],
        "signals":     signals,
        "timeline":    timeline,
        "early_count": len(early),
        "late_count":  len(late),
    }


def run_validators(bago: Path) -> dict[str, dict]:
    results: dict[str, dict] = {}
    validators = [
        ("manifest", "validate_manifest.py"),
        ("state", "validate_state.py"),
        ("pack", "validate_pack.py"),
    ]
    for key, script in validators:
        vpath = bago / "tools" / script
        if not vpath.exists():
            results[key] = {"go": None, "output": "Script no encontrado", "label": script}
            continue
        try:
            proc = subprocess.run(
                [sys.executable, str(vpath)],
                capture_output=True, text=True, timeout=30,
                stdin=subprocess.DEVNULL,
                cwd=str(bago.parent),
            )
            output = (proc.stdout + proc.stderr).strip()
            go = proc.returncode == 0 and "GO" in output and "KO" not in output
            results[key] = {"go": go, "output": output, "label": script}
        except subprocess.TimeoutExpired:
            results[key] = {"go": False, "output": "Timeout (>30s)", "label": script}
        except Exception as e:
            results[key] = {"go": False, "output": str(e), "label": script}
    return results


def _validate_bago_path(path_str: str) -> Path:
    """Valida que el path sea un .bago real. Lanza abort si no."""
    if not path_str:
        abort(400, "Falta el parámetro path")
    bago = Path(path_str).resolve()
    if not bago.is_dir() or not (bago / "pack.json").exists():
        abort(404, "Pack .bago no encontrado")
    return bago


# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    packs = [read_pack_info(p) for p in find_bago_packs(SCAN_ROOTS)]
    error = request.args.get("error")
    chosen = request.args.get("chosen", "")
    return render_template("index.html", packs=packs, error=error, chosen=chosen)


@app.route("/pick-folder")
def pick_folder():
    """Abre el selector de carpeta nativo de macOS (Finder) y redirige al pack."""
    try:
        result = subprocess.run(
            [
                "osascript", "-e",
                'POSIX path of (choose folder with prompt '
                '"Selecciona la carpeta .bago o el proyecto que la contiene")',
            ],
            capture_output=True, text=True, timeout=120,
            stdin=subprocess.DEVNULL,
        )
        path = result.stdout.strip()
        if not path:
            return redirect("/")

        chosen = Path(path)
        # El usuario pudo seleccionar directamente el .bago o el proyecto padre
        if (chosen / "pack.json").exists():
            return redirect(f"/pack?path={quote(str(chosen))}")
        elif (chosen / ".bago" / "pack.json").exists():
            return redirect(f"/pack?path={quote(str(chosen / '.bago'))}")
        else:
            return redirect(f"/?error=invalid_pack&chosen={quote(str(chosen))}")

    except subprocess.TimeoutExpired:
        return redirect("/")
    except Exception:
        return redirect("/")


@app.route("/pack")
def pack_view():
    bago = _validate_bago_path(request.args.get("path", ""))
    info = read_pack_info(bago)
    return render_template("pack.html", info=info, run_validators=False)


@app.route("/validate")
def validate():
    bago = _validate_bago_path(request.args.get("path", ""))
    info = read_pack_info(bago)
    validators = run_validators(bago)
    return render_template("pack.html", info=info, validators=validators, run_validators=True)


@app.route("/pack-report")
def pack_report():
    """Sirve el HTML de evolución con paths de SVG corregidos."""
    bago = _validate_bago_path(request.args.get("path", ""))
    html_path = bago / "docs" / "analysis" / "BAGO_EVOLUCION_SISTEMA.html"
    if not html_path.exists():
        abort(404, "No hay informe generado para este pack")

    content = html_path.read_text(encoding="utf-8")
    encoded_path = quote(str(bago))
    content = content.replace(
        'src="figures/',
        f'src="/pack-asset?path={encoded_path}&file=figures/',
    ).replace(
        "src='figures/",
        f"src='/pack-asset?path={encoded_path}&file=figures/",
    )
    return content


@app.route("/pack-asset")
def pack_asset():
    """Sirve archivos estáticos desde docs/analysis/ de un pack."""
    bago = _validate_bago_path(request.args.get("path", ""))
    file_rel = request.args.get("file", "")
    if not file_rel or ".." in file_rel:
        abort(400)

    analysis_dir = (bago / "docs" / "analysis").resolve()
    target = (analysis_dir / file_rel).resolve()

    if not str(target).startswith(str(analysis_dir)):
        abort(403)
    if not target.exists():
        abort(404)

    return send_file(target)


if __name__ == "__main__":
    port = 5050
    print(f"\n  BAGO Viewer  →  http://localhost:{port}\n")
    app.run(debug=False, port=port)
