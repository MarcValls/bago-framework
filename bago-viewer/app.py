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
    for f in sorted(sdir.glob("*.json")):
        try:
            sessions.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            pass
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
        # Compare with global_state updated_at
        if info["updated_at"]:
            try:
                state_ts = info["updated_at"].replace("Z", "+00:00")
                state_dt = datetime.fromisoformat(state_ts)
                info["report_stale"] = mtime_dt < state_dt
            except Exception:
                info["report_stale"] = None

    return info


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
