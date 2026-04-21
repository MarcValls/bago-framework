#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bago-viewer — Dashboard web para inspeccionar packs .bago
"""
from __future__ import annotations

import json
import re
import shlex
import subprocess
import sys
import tempfile
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from flask import Flask, abort, jsonify, redirect, render_template, request, send_file

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
def home():
    """Main menu — landing page."""
    import json
    gs_path = Path(__file__).resolve().parent.parent / ".bago" / "state" / "global_state.json"
    gs = {}
    if gs_path.exists():
        try:
            gs = json.loads(gs_path.read_text())
        except Exception:
            pass
    return render_template(
        "home.html",
        health=gs.get("system_health", "unknown"),
        bago_version=gs.get("bago_version", "?"),
        inventory=gs.get("inventory", {"sessions": 0, "changes": 0, "evidences": 0}),
    )


@app.route("/packs")
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
            return redirect("/packs")

        chosen = Path(path)
        # El usuario pudo seleccionar directamente el .bago o el proyecto padre
        if (chosen / "pack.json").exists():
            return redirect(f"/pack?path={quote(str(chosen))}")
        elif (chosen / ".bago" / "pack.json").exists():
            return redirect(f"/pack?path={quote(str(chosen / '.bago'))}")
        else:
            return redirect(f"/packs?error=invalid_pack&chosen={quote(str(chosen))}")

    except subprocess.TimeoutExpired:
        return redirect("/packs")
    except Exception:
        return redirect("/packs")


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




# ---------------------------------------------------------------------------
# Evolution dashboard data
# ---------------------------------------------------------------------------

_EVO_BAGO_ROOT = Path(__file__).resolve().parent.parent / ".bago"
_EVO_REPO_ROOT = _EVO_BAGO_ROOT.parent
_EVO_CV_DIR    = _EVO_REPO_ROOT / "cleanversion"
_EVO_DIST_DIR  = _EVO_BAGO_ROOT / "dist" / "source"


def _evo_commands_from_bago(bago_path: Path) -> list[str]:
    if not bago_path.exists():
        return []
    txt = bago_path.read_text(encoding="utf-8", errors="ignore")
    return re.findall(r'"([a-z_-]+)"\s*:\s*\["python3"', txt)


def _evo_metrics_from_zip(zip_path: Path) -> dict:
    if not zip_path.exists():
        return {}
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        tools     = [n for n in names if "/tools/" in n and n.endswith(".py") and "__" not in n]
        workflows = [n for n in names if "/workflows/W" in n and n.endswith(".md")]
        docs      = [n for n in names if "/docs/" in n and n.endswith(".md")]
        version   = "?"
        for name in names:
            if name.endswith("pack.json"):
                try:
                    version = json.loads(zf.read(name)).get("version", "?")
                except Exception:
                    pass
                break
    return {
        "tools": len(tools),
        "tool_names": sorted(Path(t).name for t in tools),
        "workflows": len(workflows),
        "docs": len(docs),
        "version": version,
    }


def collect_evolution_data() -> dict:
    versions = []

    # ── ZIP fuentes disponibles ────────────────────────────────────────────
    zip_map = {}
    # Scan dist/source/ ZIPs (primary)
    if _EVO_DIST_DIR.exists():
        for z in sorted(_EVO_DIST_DIR.glob("BAGO_*.zip")):
            m = _evo_metrics_from_zip(z)
            ver = m.get("version", "?")
            m.update({
                "slug": f"src-{ver}",
                "label": ver,
                "source": "dist/",
                "commands": m.get("commands", 0),
                "cmd_names": [],
            })
            zip_map[ver] = m
    # Scan cleanversion/ ZIPs (secondary — fill gaps, don't overwrite)
    if _EVO_CV_DIR.exists():
        for z in sorted(_EVO_CV_DIR.glob("BAGO_*.zip")):
            fn_m = re.match(r"BAGO_([0-9]+\.[0-9]+-[a-z0-9]+)", z.name)
            if not fn_m:
                continue
            ver = fn_m.group(1)
            if ver in zip_map:
                continue  # dist/ wins
            m = _evo_metrics_from_zip(z)
            m["version"] = ver  # override pack.json "1.0.0" with filename version
            m.update({
                "slug": f"cv-{ver}",
                "label": ver,
                "source": "cleanversion/",
                "commands": 0,
                "cmd_names": [],
            })
            zip_map[ver] = m

    # ── Cleanversions ─────────────────────────────────────────────────────
    cv_meta = {
        "v01-base-clean":    {"ver": "2.3-clean",   "sprint": "Sprint 0"},
        "v01-base-patched":  {"ver": "2.4-v2rc",    "sprint": "Sprint 0+"},
        "v02-template-seed": {"ver": "2.4-v2rc",    "sprint": "Sprint 1"},
        "v03-template-seed": {"ver": "2.5-stable",  "sprint": "Sprint 2"},
    }
    for slug, meta in cv_meta.items():
        d = _EVO_CV_DIR / slug
        if not d.exists():
            continue
        cmds = _evo_commands_from_bago(d / "bago")
        info = {}
        info_file = d / "VERSION_INFO.json"
        if info_file.exists():
            try:
                info = json.loads(info_file.read_text())
            except Exception:
                pass
        # enrich with zip data if available
        zip_data = zip_map.get(info.get("bago_version", meta["ver"]), {})
        versions.append({
            "slug":      slug,
            "label":     info.get("display_name", slug),
            "version":   info.get("bago_version", meta["ver"]),
            "sprint":    meta["sprint"],
            "commands":  len(cmds),
            "cmd_names": cmds,
            "tools":     zip_data.get("tools"),
            "tool_names": zip_data.get("tool_names", []),
            "docs":      zip_data.get("docs"),
            "workflows": zip_data.get("workflows"),
            "source":    "cleanversion/",
        })

    # ── Estado activo ─────────────────────────────────────────────────────
    live_tools = sorted(
        p.name for p in (_EVO_BAGO_ROOT / "tools").rglob("*.py")
        if not p.name.startswith("__")
    ) if (_EVO_BAGO_ROOT / "tools").exists() else []
    live_workflows = list((_EVO_BAGO_ROOT / "workflows").glob("W*.md"))
    live_docs      = list((_EVO_BAGO_ROOT / "docs").rglob("*.md"))
    live_chgs      = list((_EVO_BAGO_ROOT / "state" / "changes").glob("BAGO-CHG-*.json")) \
                     if (_EVO_BAGO_ROOT / "state" / "changes").exists() else []
    live_cmds      = _evo_commands_from_bago(_EVO_REPO_ROOT / "bago")

    version_live = "?"
    state_file = _EVO_BAGO_ROOT / "state" / "global_state.json"
    if state_file.exists():
        try:
            version_live = json.loads(state_file.read_text()).get("bago_version", "?")
        except Exception:
            pass

    # Health score
    health = -1
    health_script = _EVO_BAGO_ROOT / "tools" / "health_score.py"
    if health_script.exists():
        try:
            proc = subprocess.run(
                [sys.executable, str(health_script)],
                capture_output=True, text=True, timeout=15,
                stdin=subprocess.DEVNULL, cwd=str(_EVO_REPO_ROOT)
            )
            for line in proc.stdout.splitlines():
                m2 = re.search(r"(\d+)/100", line)
                if m2:
                    health = int(m2.group(1))
                    break
        except Exception:
            pass

    # Ideas implementadas
    ideas_done = []
    impl_file = _EVO_BAGO_ROOT / "state" / "implemented_ideas.json"
    if impl_file.exists():
        try:
            data = json.loads(impl_file.read_text())
            ideas_done = data.get("implemented", [])
        except Exception:
            pass

    versions.append({
        "slug":      "live",
        "label":     f"ACTIVO ({version_live})",
        "version":   version_live,
        "sprint":    "Sprint 2 (activo)",
        "commands":  len(live_cmds),
        "cmd_names": live_cmds,
        "tools":     len(live_tools),
        "tool_names": live_tools,
        "docs":      len(live_docs),
        "workflows": len(live_workflows),
        "chgs":      len(live_chgs),
        "health":    health,
        "source":    "live",
    })

    # ── Detectar nuevas tools/cmds por versión ────────────────────────────
    for i, v in enumerate(versions):
        if i == 0:
            v["new_tools"] = v.get("tool_names", [])
            v["new_cmds"]  = v.get("cmd_names", [])
        else:
            prev = versions[i - 1]
            v["new_tools"] = sorted(set(v.get("tool_names", [])) - set(prev.get("tool_names", [])))
            v["new_cmds"]  = sorted(set(v.get("cmd_names", [])) - set(prev.get("cmd_names", [])))

    # ── Calcular índice de eficiencia ─────────────────────────────────────
    WEIGHTS = {"commands": 0.30, "tools": 0.35, "docs": 0.20, "workflows": 0.15}
    maxima  = {k: max((v.get(k) or 0 for v in versions), default=1) for k in WEIGHTS}
    for v in versions:
        score = sum(
            ((v.get(k) or 0) / max(maxima[k], 1)) * w * 100
            for k, w in WEIGHTS.items()
        )
        v["efficiency"] = round(score, 1)

    return {
        "versions":    versions,
        "ideas":       ideas_done,
        "live_health": health,
        "live_chgs":   len(live_chgs),
        "live_version": version_live,
    }


@app.route("/evolution")
def evolution():
    data = collect_evolution_data()
    return render_template("evolution.html", data=data)


# ---------------------------------------------------------------------------
# Metrics dashboard
# ---------------------------------------------------------------------------

METRICS_DIR = Path(__file__).parent.parent / "docs" / "metrics"

def _collect_metrics_data() -> dict:
    """Lee las sesiones reales y compila los KPIs para la vista de métricas."""
    bago_root = Path(__file__).parent.parent / ".bago"
    sessions_dir = bago_root / "state" / "sessions"
    changes_dir  = bago_root / "state" / "changes"
    evidences_dir = bago_root / "state" / "evidences"

    sessions = []
    for f in sorted(sessions_dir.glob("*.json")):
        try:
            sessions.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            pass
    sessions.sort(key=lambda s: s.get("created_at", ""))

    total_sessions = len(sessions)
    total_changes  = len(list(changes_dir.glob("*.json")))
    total_evidences = len(list(evidences_dir.glob("*.json")))

    # Éxito — status "completed" o "closed"
    completed = sum(1 for s in sessions if s.get("status") in ("completed", "closed"))
    success_rate = f"{(completed/total_sessions*100):.1f}%" if total_sessions else "—"

    # Artefactos — campo real es "artifacts"
    def _arts(s: dict) -> list:
        return s.get("artifacts") or s.get("artifacts_delivered") or []

    total_arts  = sum(len(_arts(s)) for s in sessions)
    planned_arts = sum(len(s.get("artifacts_planned") or []) for s in sessions)
    # "útiles" = entregados; "relleno" = planificados - entregados (si planned > delivered)
    filler = max(0, planned_arts - total_arts)
    useful_arts = total_arts
    useful_ratio = f"{(useful_arts/(useful_arts+filler)*100):.1f}%" if (useful_arts + filler) else "100%"

    # Duración — calculada desde created_at → updated_at
    def _dur_min(s: dict) -> float | None:
        c, u = s.get("created_at"), s.get("updated_at")
        if not c or not u or c == u:
            return None
        try:
            dt = (
                datetime.fromisoformat(u.replace("Z", "+00:00"))
                - datetime.fromisoformat(c.replace("Z", "+00:00"))
            ).total_seconds() / 60
            return round(dt, 1) if 0 < dt < 600 else None
        except Exception:
            return None

    durations = [d for s in sessions if (d := _dur_min(s)) is not None]
    avg_dur = f"{sum(durations)/len(durations):.1f} min" if durations else "—"
    sessions_u30 = sum(1 for d in durations if d <= 30)
    sessions_o60 = sum(1 for d in durations if d > 60)

    # TLS heuristic: duración < 5 min y sin artefactos
    tls_ids = [
        s.get("session_id", "?")
        for s in sessions
        if (_dur_min(s) or 999) < 5
        and len(_arts(s)) == 0
    ]
    real_sessions = total_sessions - len(tls_ids)
    real_pct = f"{(real_sessions/total_sessions*100):.0f}%" if total_sessions else "—"

    # Workflows
    wf_data: dict[str, dict] = {}
    for s in sessions:
        wf = s.get("task_type") or s.get("selected_workflow") or "desconocido"
        if wf not in wf_data:
            wf_data[wf] = {"count": 0, "ok": 0, "durations": []}
        wf_data[wf]["count"] += 1
        if s.get("status") in ("completed", "closed"):
            wf_data[wf]["ok"] += 1
        d = _dur_min(s)
        if d:
            wf_data[wf]["durations"].append(d)

    workflows = []
    for name, v in sorted(wf_data.items(), key=lambda x: -x[1]["count"]):
        pct = (v["ok"] / v["count"] * 100) if v["count"] else 0
        dur = f"{sum(v['durations'])/len(v['durations']):.0f} min" if v["durations"] else "—"
        workflows.append({
            "name": name,
            "count": v["count"],
            "success_pct": f"{pct:.0f}%",
            "avg_duration": dur,
        })

    # Roles
    role_data: dict[str, dict] = {}
    for s in sessions:
        arts = len(_arts(s))
        decs = len(s.get("decisions") or [])
        for r in s.get("roles_activated") or []:
            role_clean = r.replace("role_", "")
            if role_clean not in role_data:
                role_data[role_clean] = {"count": 0, "artifacts": 0, "decisions": 0}
            role_data[role_clean]["count"] += 1
            role_data[role_clean]["artifacts"] += arts
            role_data[role_clean]["decisions"] += decs

    roles = []
    for name, v in sorted(role_data.items(), key=lambda x: -x[1]["artifacts"]):
        c = v["count"]
        roles.append({
            "name": name,
            "count": c,
            "artifacts_per_session": v["artifacts"] / c if c else 0,
            "decisions_per_session": v["decisions"] / c if c else 0,
        })

    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total_sessions": total_sessions,
        "total_changes": total_changes,
        "total_evidences": total_evidences,
        "success_rate": success_rate,
        "total_artifacts": total_arts,
        "useful_artifacts": useful_arts,
        "filler_artifacts": filler,
        "useful_ratio": useful_ratio,
        "avg_duration": avg_dur,
        "sessions_with_duration": len(durations),
        "sessions_under_30": f"{sessions_u30} ({int(sessions_u30/len(durations)*100)}%)" if durations else "—",
        "sessions_over_60": f"{sessions_o60} ({int(sessions_o60/len(durations)*100)}%)" if durations else "—",
        "real_sessions": real_sessions,
        "real_sessions_pct": real_pct,
        "tls_affected": len(tls_ids),
        "tls_ids": tls_ids,
        "workflows": workflows,
        "roles": roles,
    }


@app.route("/metrics")
def metrics():
    data = _collect_metrics_data()
    return render_template("metrics.html", data=data)


@app.route("/metrics-img/<filename>")
def metrics_img(filename: str):
    """Sirve los PNGs de docs/metrics/."""
    safe = Path(filename).name
    img_path = METRICS_DIR / safe
    if not img_path.exists() or img_path.suffix not in (".png", ".jpg", ".svg"):
        abort(404)
    return send_file(img_path)


# ── ORCHESTRATOR ──────────────────────────────────────────────────────────
_ORCH_BAGO_ROOT = Path(__file__).resolve().parent.parent / ".bago"
_ORCH_PROJECT_ROOT = _ORCH_BAGO_ROOT.parent
_ORCH_BAGO_BIN = _ORCH_PROJECT_ROOT / "bago"
_ORCH_PRESETS_FILE = _ORCH_BAGO_ROOT / "state" / "orchestrator_presets.json"
_ORCH_HISTORY: list[dict] = []
_ORCH_HISTORY_MAX = 40

_ORCH_SIMPLE_COMMANDS = {
    "status": ["status"],
    "validate": ["validate"],
    "ideas": ["ideas"],
    "session-start": ["session"],
    "detector": ["detector"],
    "cosecha": ["cosecha"],
    "stability": ["stability"],
    "dashboard": ["dashboard"],
}

_ORCH_BUILTIN_PRESETS = {
    "preset_sesion_w2": {
        "label": "Sesión W2",
        "description": "status → ideas → session (orden fijo)",
        "steps": [
            {"mode": "serial", "commands": ["status", "ideas", "session-start"]},
        ],
    },
    "preset_guardia_pack": {
        "label": "Guardia Pack",
        "description": "validate → stability → detector",
        "steps": [
            {"mode": "serial", "commands": ["validate", "stability", "detector"]},
        ],
    },
    "preset_repo_qa": {
        "label": "QA Repo",
        "description": "repo-debug → (repo-lint || repo-test) → repo-build",
        "steps": [
            {"mode": "serial", "commands": ["repo-debug"]},
            {"mode": "parallel", "commands": ["repo-lint", "repo-test"]},
            {"mode": "serial", "commands": ["repo-build"]},
        ],
    },
}


def _orch_remember(entry: dict) -> None:
    _ORCH_HISTORY.append(entry)
    if len(_ORCH_HISTORY) > _ORCH_HISTORY_MAX:
        del _ORCH_HISTORY[: len(_ORCH_HISTORY) - _ORCH_HISTORY_MAX]


def _orch_command_catalog() -> list[dict]:
    return [
        {"id": "status", "label": "Status"},
        {"id": "validate", "label": "Validate"},
        {"id": "ideas", "label": "Ideas"},
        {"id": "session-start", "label": "Session Start"},
        {"id": "detector", "label": "Detector"},
        {"id": "cosecha", "label": "Cosecha"},
        {"id": "stability", "label": "Stability"},
        {"id": "dashboard", "label": "Dashboard"},
        {"id": "repo-on", "label": "Repo On"},
        {"id": "repo-debug", "label": "Repo Debug"},
        {"id": "repo-lint", "label": "Repo Lint"},
        {"id": "repo-test", "label": "Repo Test"},
        {"id": "repo-build", "label": "Repo Build"},
    ]


def _orch_allowed_command_ids() -> set[str]:
    return {c["id"] for c in _orch_command_catalog()}


def _orch_validate_steps(steps: list[dict]) -> list[dict]:
    if not isinstance(steps, list) or not steps:
        raise ValueError("steps debe ser una lista no vacía")
    clean = []
    allowed = _orch_allowed_command_ids()
    for i, step in enumerate(steps):
        if not isinstance(step, dict):
            raise ValueError(f"step[{i}] inválido")
        mode = str(step.get("mode", "serial")).strip().lower()
        if mode not in {"serial", "parallel"}:
            raise ValueError(f"step[{i}].mode inválido")
        cmds = step.get("commands", [])
        if not isinstance(cmds, list) or not cmds:
            raise ValueError(f"step[{i}].commands vacío")
        clean_cmds = []
        for c in cmds:
            cid = str(c).strip()
            if cid not in allowed:
                raise ValueError(f"Comando no permitido en step[{i}]: {cid}")
            clean_cmds.append(cid)
        clean.append({"mode": mode, "commands": clean_cmds})
    return clean


def _orch_load_custom_presets() -> dict:
    if not _ORCH_PRESETS_FILE.exists():
        return {}
    try:
        data = json.loads(_ORCH_PRESETS_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {}
        presets = data.get("presets", {})
        if not isinstance(presets, dict):
            return {}
        clean: dict = {}
        for pid, p in presets.items():
            if not isinstance(p, dict):
                continue
            try:
                steps = _orch_validate_steps(p.get("steps", []))
            except Exception:
                continue
            clean[str(pid)] = {
                "label": str(p.get("label", pid)),
                "description": str(p.get("description", "")),
                "steps": steps,
                "builtin": False,
            }
        return clean
    except Exception:
        return {}


def _orch_save_custom_presets(presets: dict) -> None:
    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "presets": presets,
    }
    _ORCH_PRESETS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _ORCH_PRESETS_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _orch_all_presets() -> dict:
    merged = {k: {**v, "builtin": True} for k, v in _ORCH_BUILTIN_PRESETS.items()}
    merged.update(_orch_load_custom_presets())
    return merged


def _orch_repo_commands(command_id: str, payload: dict) -> list[str] | None:
    repo_path = str(payload.get("repo_path", "")).strip()
    if command_id == "repo-on":
        if not repo_path:
            raise ValueError("Falta repo_path para repo-on")
        return ["repo-on", repo_path]

    if command_id in {"repo-debug", "repo-lint", "repo-test", "repo-build"}:
        args = [command_id]
        if repo_path:
            args.append(repo_path)
        return args
    return None


def _orch_resolve_command(command_id: str, payload: dict) -> list[str]:
    if command_id in _ORCH_SIMPLE_COMMANDS:
        return ["python3", str(_ORCH_BAGO_BIN), *_ORCH_SIMPLE_COMMANDS[command_id]]

    repo_args = _orch_repo_commands(command_id, payload)
    if repo_args is not None:
        return ["python3", str(_ORCH_BAGO_BIN), *repo_args]

    raise ValueError(f"Comando no permitido: {command_id}")


def _orch_run_command(command_id: str, payload: dict, timeout_sec: int = 240) -> dict:
    started = datetime.now(timezone.utc)
    argv = _orch_resolve_command(command_id, payload)
    try:
        proc = subprocess.run(
            argv,
            cwd=str(_ORCH_PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
        output = ((proc.stdout or "") + (proc.stderr or "")).strip()
        if len(output) > 12000:
            output = output[:12000] + "\n...[truncado]..."
        result = {
            "command_id": command_id,
            "argv": argv,
            "success": proc.returncode == 0,
            "returncode": proc.returncode,
            "output": output,
            "started_at": started.isoformat(),
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }
    except subprocess.TimeoutExpired:
        result = {
            "command_id": command_id,
            "argv": argv,
            "success": False,
            "returncode": 124,
            "output": f"Timeout > {timeout_sec}s",
            "started_at": started.isoformat(),
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }
    return result


def _orch_terminal_script_for_command(command_id: str, payload: dict) -> str:
    argv = _orch_resolve_command(command_id, payload)
    return " ".join(shlex.quote(a) for a in argv)


def _orch_terminal_script_for_preset(preset_id: str, payload: dict) -> str:
    preset = _orch_all_presets().get(preset_id)
    if not preset:
        raise ValueError(f"Preset no permitido: {preset_id}")

    pieces: list[str] = []
    for step in preset.get("steps", []):
        mode = step.get("mode", "serial")
        commands = step.get("commands", [])
        cmd_scripts = [_orch_terminal_script_for_command(cmd, payload) for cmd in commands]
        if not cmd_scripts:
            continue
        if mode == "parallel":
            # Mantiene el orden por etapa, pero ejecuta comandos de la etapa en paralelo.
            par = " ; ".join(f"({c}) &" for c in cmd_scripts) + " wait"
            pieces.append(par)
        else:
            pieces.append(" && ".join(cmd_scripts))
    return " && ".join(pieces)


def _orch_launch_in_terminal(shell_script: str) -> dict:
    script = f"cd {shlex.quote(str(_ORCH_PROJECT_ROOT))}\n{shell_script}\n"
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".command",
            prefix="bago_orch_",
            delete=False,
        ) as tf:
            tf.write("#!/bin/zsh\n")
            tf.write("set -e\n")
            tf.write(script)
            tf.write("\necho\n")
            tf.write('echo "[Orchestrator] Fin de ejecución."\n')
            tf.write('read -k 1 "?Pulsa una tecla para cerrar..."\n')
            temp_path = Path(tf.name)

        temp_path.chmod(0o755)
        proc = subprocess.run(
            ["open", "-a", "Terminal", str(temp_path)],
            cwd=str(_ORCH_PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=20,
        )
        ok = proc.returncode == 0
        output = ((proc.stdout or "") + (proc.stderr or "")).strip()
        return {
            "success": ok,
            "returncode": proc.returncode,
            "output": output or "Comando enviado a Terminal.app",
        }
    except Exception as e:
        return {
            "success": False,
            "returncode": 1,
            "output": f"No se pudo abrir Terminal.app: {e}",
        }


def _orch_execute_step(step: dict, payload: dict) -> dict:
    mode = step.get("mode", "serial")
    commands = step.get("commands", [])
    results: list[dict] = []
    success = True

    if mode == "parallel":
        with ThreadPoolExecutor(max_workers=min(len(commands), 4)) as ex:
            fut_map = {ex.submit(_orch_run_command, cmd, payload): cmd for cmd in commands}
            for fut in as_completed(fut_map):
                res = fut.result()
                results.append(res)
        order = {cmd: i for i, cmd in enumerate(commands)}
        results.sort(key=lambda x: order.get(x["command_id"], 999))
        success = all(r.get("success") for r in results)
    else:
        for cmd in commands:
            res = _orch_run_command(cmd, payload)
            results.append(res)
            if not res.get("success"):
                success = False
                break

    return {"mode": mode, "commands": commands, "results": results, "success": success}


def _orch_execute_preset(preset_id: str, payload: dict) -> dict:
    preset = _orch_all_presets().get(preset_id)
    if not preset:
        raise ValueError(f"Preset no permitido: {preset_id}")

    started = datetime.now(timezone.utc)
    steps_out = []
    success = True
    for step in preset.get("steps", []):
        step_out = _orch_execute_step(step, payload)
        steps_out.append(step_out)
        if not step_out.get("success"):
            success = False
            break

    return {
        "kind": "preset",
        "id": preset_id,
        "label": preset.get("label", preset_id),
        "description": preset.get("description", ""),
        "success": success,
        "started_at": started.isoformat(),
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "steps": steps_out,
    }

def _collect_orchestrator_data() -> dict:
    """Recopila todo el estado BAGO para el panel orquestador."""
    import json
    from datetime import datetime, timezone

    data: dict = {}

    # global_state
    gs_path = _ORCH_BAGO_ROOT / "state" / "global_state.json"
    gs = {}
    if gs_path.exists():
        try:
            gs = json.loads(gs_path.read_text())
        except Exception:
            pass

    data["bago_version"]             = gs.get("bago_version", "?")
    data["system_health"]            = gs.get("system_health", "unknown")
    data["sprint_status"]            = gs.get("sprint_status", {})
    data["inventory"]                = gs.get("inventory", {"sessions": 0, "changes": 0, "evidences": 0})
    data["last_validation"]          = gs.get("last_validation", {})
    data["notes"]                    = gs.get("notes", None)
    data["last_completed_session_id"]= gs.get("last_completed_session_id")
    data["last_completed_task_type"] = gs.get("last_completed_task_type")
    data["last_completed_workflow"]  = gs.get("last_completed_workflow")
    data["last_completed_roles"]     = gs.get("last_completed_roles", [])
    data["pack_path"]                = str(_ORCH_BAGO_ROOT)

    # sesión activa
    active_id = gs.get("active_session_id")
    active_session: dict = {"active": False}
    if active_id:
        sess_path = _ORCH_BAGO_ROOT / "state" / "sessions" / f"{active_id}.json"
        if sess_path.exists():
            try:
                sess = json.loads(sess_path.read_text())
                active_session = {
                    "active": True,
                    "session_id": active_id,
                    "goal":               sess.get("user_goal", "—"),
                    "workflow":           sess.get("selected_workflow", ""),
                    "roles":              sess.get("roles_activated", []),
                    "start_iso":          sess.get("created_at"),
                    "artifacts_planned":  sess.get("artifacts_planned", []),
                    "status":             sess.get("status", "active"),
                }
            except Exception:
                active_session = {"active": True, "session_id": active_id, "goal": "—"}
    data["active_session"] = active_session

    # sesiones recientes (últimas 8)
    sessions_dir = _ORCH_BAGO_ROOT / "state" / "sessions"
    recent = []
    total_sessions = 0
    if sessions_dir.exists():
        all_sess = sorted(sessions_dir.glob("*.json"),
                          key=lambda f: f.stat().st_mtime, reverse=True)
        total_sessions = len(all_sess)
        for sf in all_sess[:8]:
            try:
                s = json.loads(sf.read_text())
                # duration
                dur = None
                try:
                    ca = datetime.fromisoformat(s.get("created_at", "").replace("Z", "+00:00"))
                    ua = datetime.fromisoformat(s.get("updated_at", "").replace("Z", "+00:00"))
                    diff = (ua - ca).total_seconds() / 60
                    if 0.5 <= diff <= 600:
                        dur = round(diff, 1)
                except Exception:
                    pass
                recent.append({
                    "__total":          total_sessions,
                    "session_id":       s.get("session_id", sf.stem),
                    "user_goal":        s.get("user_goal", "—"),
                    "selected_workflow":s.get("selected_workflow", ""),
                    "status":           s.get("status", ""),
                    "duration_minutes": dur,
                })
            except Exception:
                pass
    data["recent_sessions"] = recent

    # ideas detectadas
    ideas_dir = _ORCH_BAGO_ROOT / "ideas"
    ideas_agg = []
    if ideas_dir.exists():
        for ideas_file in sorted(ideas_dir.glob("*.json")):
            try:
                content = json.loads(ideas_file.read_text())
                proj_name = content.get("project", ideas_file.stem)
                ideas_list = content.get("ideas", [])
                if not isinstance(ideas_list, list):
                    continue
                pending  = sum(1 for i in ideas_list if i.get("status") == "pending")
                done     = sum(1 for i in ideas_list if i.get("status") == "done")
                progress = sum(1 for i in ideas_list if i.get("status") == "in_progress")
                if ideas_list:
                    ideas_agg.append({
                        "project":  proj_name,
                        "total":    len(ideas_list),
                        "pending":  pending,
                        "done":     done,
                        "progress": progress,
                    })
            except Exception:
                pass
    data["ideas"] = ideas_agg

    # resumen ideas
    data["ideas_summary"] = {
        "projects": len(ideas_agg),
        "total": sum(i.get("total", 0) for i in ideas_agg),
        "pending": sum(i.get("pending", 0) for i in ideas_agg),
        "progress": sum(i.get("progress", 0) for i in ideas_agg),
        "done": sum(i.get("done", 0) for i in ideas_agg),
    }

    # actividad por ventana temporal (según timestamps UTC en state/)
    now_utc = datetime.now(timezone.utc)

    def _recent_count(folder: Path, field: str, seconds: int) -> int:
        if not folder.exists():
            return 0
        n = 0
        cutoff = now_utc.timestamp() - seconds
        for f in folder.glob("*.json"):
            try:
                record = json.loads(f.read_text())
                ts = record.get(field)
                if not ts:
                    continue
                t = datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
                if t >= cutoff:
                    n += 1
            except Exception:
                continue
        return n

    windows = {
        "24h": 24 * 3600,
        "7d": 7 * 24 * 3600,
        "30d": 30 * 24 * 3600,
    }
    activity_windows = {}
    for key, seconds in windows.items():
        activity_windows[key] = {
            "sessions": _recent_count(_ORCH_BAGO_ROOT / "state" / "sessions", "created_at", seconds),
            "changes": _recent_count(_ORCH_BAGO_ROOT / "state" / "changes", "created_at", seconds),
            "evidences": _recent_count(_ORCH_BAGO_ROOT / "state" / "evidences", "recorded_at", seconds),
        }

    data["activity_windows"] = activity_windows
    data["activity_24h"] = activity_windows["24h"]
    data["orchestrator_presets"] = _orch_all_presets()
    data["orchestrator_commands"] = _orch_command_catalog()
    data["orchestrator_history"] = _ORCH_HISTORY[-8:]

    return data


@app.route("/orchestrator")
def orchestrator():
    return render_template("orchestrator.html")


@app.route("/orchestrator-data")
def orchestrator_data():
    try:
        d = _collect_orchestrator_data()
        return jsonify(d)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/orchestrator-run", methods=["POST"])
def orchestrator_run():
    payload = request.get_json(silent=True) or {}
    kind = str(payload.get("kind", "command"))
    target_id = str(payload.get("id", "")).strip()
    terminal_mode = bool(payload.get("terminal"))

    if not target_id:
        return jsonify({"success": False, "error": "Falta id"}), 400

    try:
        if terminal_mode:
            started = datetime.now(timezone.utc).isoformat()
            if kind == "preset":
                shell_script = _orch_terminal_script_for_preset(target_id, payload)
            else:
                shell_script = _orch_terminal_script_for_command(target_id, payload)
            launch = _orch_launch_in_terminal(shell_script)
            result = {
                "kind": kind,
                "id": target_id,
                "success": launch.get("success", False),
                "terminal": True,
                "started_at": started,
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "steps": [{
                    "mode": "serial",
                    "commands": [target_id],
                    "results": [{
                        "command_id": target_id,
                        "success": launch.get("success", False),
                        "returncode": launch.get("returncode", 1),
                        "output": launch.get("output", ""),
                    }],
                    "success": launch.get("success", False),
                }],
            }
            _orch_remember(result)
            status = 200 if result["success"] else 500
            return jsonify(result), status

        if kind == "preset":
            result = _orch_execute_preset(target_id, payload)
        else:
            cmd_result = _orch_run_command(target_id, payload)
            result = {
                "kind": "command",
                "id": target_id,
                "success": cmd_result.get("success", False),
                "started_at": cmd_result.get("started_at", datetime.now(timezone.utc).isoformat()),
                "finished_at": cmd_result.get("finished_at", datetime.now(timezone.utc).isoformat()),
                "steps": [{
                    "mode": "serial",
                    "commands": [target_id],
                    "results": [cmd_result],
                    "success": cmd_result.get("success", False),
                }],
            }
        _orch_remember(result)
        return jsonify(result)
    except ValueError as e:
        err = {"success": False, "error": str(e), "kind": kind, "id": target_id}
        _orch_remember(err)
        return jsonify(err), 400
    except Exception as e:
        err = {"success": False, "error": f"Error ejecutando acción: {e}", "kind": kind, "id": target_id}
        _orch_remember(err)
        return jsonify(err), 500


@app.route("/orchestrator-presets", methods=["GET", "POST"])
def orchestrator_presets():
    if request.method == "GET":
        return jsonify({
            "presets": _orch_all_presets(),
            "commands": _orch_command_catalog(),
        })

    payload = request.get_json(silent=True) or {}
    preset_id = str(payload.get("id", "")).strip()
    if not preset_id:
        return jsonify({"success": False, "error": "Falta id"}), 400
    if not re.match(r"^[a-z0-9_-]{3,64}$", preset_id):
        return jsonify({"success": False, "error": "id inválido (usa a-z0-9_-)."}), 400
    if preset_id in _ORCH_BUILTIN_PRESETS:
        return jsonify({"success": False, "error": "No puedes sobrescribir un preset builtin."}), 400

    label = str(payload.get("label", preset_id)).strip() or preset_id
    description = str(payload.get("description", "")).strip()
    try:
        steps = _orch_validate_steps(payload.get("steps", []))
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400

    custom = _orch_load_custom_presets()
    custom[preset_id] = {
        "label": label,
        "description": description,
        "steps": steps,
        "builtin": False,
    }
    _orch_save_custom_presets(custom)
    return jsonify({"success": True, "preset": custom[preset_id], "id": preset_id})


@app.route("/orchestrator-presets/<preset_id>", methods=["DELETE"])
def orchestrator_preset_delete(preset_id: str):
    preset_id = str(preset_id).strip()
    if preset_id in _ORCH_BUILTIN_PRESETS:
        return jsonify({"success": False, "error": "No se puede borrar un preset builtin."}), 400
    custom = _orch_load_custom_presets()
    if preset_id not in custom:
        return jsonify({"success": False, "error": "Preset no encontrado."}), 404
    del custom[preset_id]
    _orch_save_custom_presets(custom)
    return jsonify({"success": True, "deleted": preset_id})



if __name__ == "__main__":
    port = 5050
    print(f"\n  BAGO Viewer  →  http://localhost:{port}\n")
    app.run(debug=False, port=port)
