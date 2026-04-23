#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
watch.py - Monitor en tiempo real del estado BAGO.

Muestra un snapshot del estado del pack que se actualiza automáticamente:
  - Sesión activa (si existe)
  - Últimas 5 sesiones
  - Sprint activo
  - Estado global (health, inventory)
  - Cambios recientes en state/ (file watcher)

Modos:
  python3 watch.py            # snapshot único (no-interactive)
  python3 watch.py --live     # actualización cada 3s (Ctrl+C para salir)
  python3 watch.py --interval 5  # actualizar cada 5s
  python3 watch.py --once     # snapshot único y salir (alias de default)
  python3 watch.py --test
"""
from __future__ import annotations
import argparse, json, os, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "state"

# ── helpers ──────────────────────────────────────────────────────────────────

def _load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _load_sessions(last=5):
    folder = STATE / "sessions"
    if not folder.exists():
        return []
    sessions = []
    for f in folder.glob("*.json"):
        s = _load_json(f)
        if s and s.get("created_at"):
            sessions.append(s)
    sessions.sort(key=lambda s: s.get("created_at", ""), reverse=True)
    return sessions[:last]


def _load_active_sprint():
    sprints_dir = STATE / "sprints"
    if not sprints_dir.exists():
        return None
    for f in sorted(sprints_dir.glob("*.json"), reverse=True):
        s = _load_json(f)
        if s.get("status") == "open":
            return s
    return None


def _load_global_state():
    return _load_json(STATE / "global_state.json")


def _artifacts_useful(session):
    excl = {"state/sessions/", "state/changes/", "state/evidences/",
            "TREE.txt", "CHECKSUMS.sha256"}
    return [a for a in session.get("artifacts", [])
            if not any(a.startswith(e) for e in excl)]


def _file_changes_since(seconds=60):
    """Retorna archivos en state/ modificados en los últimos N segundos."""
    cutoff = time.time() - seconds
    changed = []
    for f in STATE.rglob("*.json"):
        try:
            if f.stat().st_mtime > cutoff:
                changed.append(f.relative_to(ROOT))
        except Exception:
            pass
    return sorted(changed)


# ── render ────────────────────────────────────────────────────────────────────

def _clear():
    os.system("clear" if os.name == "posix" else "cls")  # noqa: BAGO-W003


def _wf_short(wf):
    mapping = {
        "w0_automode": "W0", "w1_cold_start": "W1", "w2_implementacion": "W2",
        "w3_debug": "W3", "w4_review": "W4", "w5_refactor": "W5",
        "w6_docs": "W6", "w7_foco_sesion": "W7", "w8_audit": "W8",
        "w9_cosecha": "W9", "workflow_system_change": "SC",
        "workflow_experiment": "EX", "workflow_analysis": "AN",
        "workflow_bootstrap": "BS", "workflow_role": "RL",
    }
    return mapping.get(wf, wf[:4].upper() if wf else "??")


def render_snapshot(live=False, interval=3):
    """Renderiza un snapshot del estado BAGO."""
    gs = _load_global_state()
    sessions = _load_sessions(last=6)
    sprint = _load_active_sprint()
    now = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")

    lines = []
    lines.append("")
    if live:
        lines.append("  BAGO Watch  [live, cada {}s — Ctrl+C para salir]  {}".format(interval, now))
    else:
        lines.append("  BAGO Watch  [snapshot]  {}".format(now))
    lines.append("  " + "─" * 58)

    # Global state
    health = gs.get("system_health", "?")
    bago_ver = gs.get("bago_version", "?")
    active_ses = gs.get("active_session_id")
    inv = gs.get("inventory", {})
    lines.append("")
    lines.append("  Pack     : {} v{}  health={}".format(
        ROOT.name, bago_ver, health))
    lines.append("  Inventario: ses={} chg={} evd={}".format(
        inv.get("sessions","?"), inv.get("changes","?"), inv.get("evidences","?")))

    # Active session
    lines.append("")
    if active_ses:
        lines.append("  SESION ACTIVA: {}".format(active_ses))
        open_changes = gs.get("open_changes", [])
        if open_changes:
            lines.append("  Cambios abiertos: {}".format(", ".join(open_changes[:3])))
    else:
        lines.append("  Sesion activa : ninguna")

    # Active sprint
    lines.append("")
    if sprint:
        items = sprint.get("items", {})
        n_arts = len(items.get("artifacts", []))
        n_chg  = len(items.get("changes", []))
        lines.append("  Sprint activo : {} — {}".format(
            sprint.get("sprint_id"), sprint.get("name", "?")))
        lines.append("  Sprint links  : arts={} chg={}".format(n_arts, n_chg))
    else:
        lines.append("  Sprint activo : ninguno")

    # Recent sessions
    lines.append("")
    lines.append("  Últimas sesiones:")
    lines.append("  {:<36}  {:<4}  {:<3}  {:<3}  {}".format(
        "ID", "WF", "Art", "Dec", "Estado"))
    lines.append("  " + "-" * 60)
    for s in sessions:
        sid = s.get("session_id", "")[:36]
        wf  = _wf_short(s.get("selected_workflow",""))
        arts = len(_artifacts_useful(s))
        decs = len(s.get("decisions", []))
        status = s.get("status", "?")
        marker = "●" if status == "open" else " "
        lines.append("  {}{:<36}  {:<4}  {:>3}  {:>3}  {}".format(
            marker, sid, wf, arts, decs, status))

    # Files changed recently
    if live:
        recent_files = _file_changes_since(interval * 2)
        if recent_files:
            lines.append("")
            lines.append("  Cambios recientes en state/:")
            for f in recent_files[:5]:
                lines.append("    ~ {}".format(f))

    lines.append("")
    return "\n".join(lines)


def run_live(interval=3):
    """Bucle de actualización en vivo."""
    try:
        while True:
            _clear()
            print(render_snapshot(live=True, interval=interval))
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n  Watch detenido.")


# ── tests ─────────────────────────────────────────────────────────────────────

def _run_tests():
    print("  Ejecutando tests de watch.py...")

    # Test render_snapshot no falla con datos reales
    snap = render_snapshot(live=False)
    assert "BAGO Watch" in snap, "Header faltante"
    assert "Pack" in snap, "Pack info faltante"
    assert "Últimas sesiones" in snap, "Sessions section faltante"

    # Test _wf_short
    assert _wf_short("w9_cosecha") == "W9"
    assert _wf_short("w1_cold_start") == "W1"
    assert _wf_short("workflow_system_change") == "SC"
    assert _wf_short("") == "??"

    # Test _load_sessions returns list
    sessions = _load_sessions(last=3)
    assert isinstance(sessions, list)
    if sessions:
        assert "session_id" in sessions[0]

    # Test _file_changes_since returns list
    changed = _file_changes_since(seconds=3600)
    assert isinstance(changed, list)

    print("  OK: todos los tests pasaron (4/4)")


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Monitor en tiempo real del estado BAGO")
    p.add_argument("--live", "-l", action="store_true",
                   help="Modo live (actualización continua)")
    p.add_argument("--interval", "-i", type=int, default=3,
                   help="Intervalo de actualización en segundos (default: 3)")
    p.add_argument("--once", action="store_true",
                   help="Snapshot único y salir (comportamiento por defecto)")
    p.add_argument("--test", action="store_true")
    args = p.parse_args()

    if args.test:
        _run_tests()
        return

    if args.live:
        run_live(interval=args.interval)
    else:
        print(render_snapshot(live=False))


if __name__ == "__main__":
    main()
