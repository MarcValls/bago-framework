#!/usr/bin/env python3
"""
bago_banner.py — Cartel de activación BAGO
Muestra logotipo ASCII + estado del pack al arrancar.

Uso:
  python3 .bago/tools/bago_banner.py
  python3 .bago/tools/bago_banner.py --mini   (sin estado)
  python3 .bago/tools/bago_banner.py --plain  (sin colores)
"""

import json, re, subprocess, sys
from datetime import datetime
from pathlib import Path

# ─── Rutas ────────────────────────────────────────────────────────────────────
BAGO_ROOT = Path(__file__).resolve().parent.parent
STATE     = BAGO_ROOT / "state"
TOOLS     = BAGO_ROOT / "tools"

# ─── Colores ANSI ─────────────────────────────────────────────────────────────
# Auto-plain si no es TTY o se pasa --plain
USE_COLOR = sys.stdout.isatty() and "--plain" not in sys.argv

def _c(code, text):
    if not USE_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"

CYAN   = lambda t: _c("1;36", t)
BLUE   = lambda t: _c("1;34", t)
GREEN  = lambda t: _c("1;32", t)
RED    = lambda t: _c("1;31", t)
YELLOW = lambda t: _c("1;33", t)
BOLD   = lambda t: _c("1",    t)
DIM    = lambda t: _c("2",    t)

# ─── Logo (sin espacios leading — se añaden fuera del ANSI) ───────────────────
# Dividido en top (cyan) y bottom (azul)
LOGO_TOP = [
    "██████╗  █████╗  ██████╗  ██████╗",
    "██╔══██╗██╔══██╗██╔════╝ ██╔═══██╗",
    "██████╔╝███████║██║  ███╗██║   ██║",
    "██╔══██╗██╔══██║██║   ██║██║   ██║",
]
LOGO_BOT = [
    "██████╔╝██║  ██║╚██████╔╝╚██████╔╝",
    "╚═════╝ ╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ",
]

# ─── Caja ─────────────────────────────────────────────────────────────────────
BOX_INNER = 56  # caracteres visibles entre los bordes ║ y ║

def _strip_ansi(s):
    """Elimina secuencias ANSI para medir la anchura visible."""
    return re.sub(r'\033\[[0-9;]*m', '', s)

def _box(content=""):
    """Línea de caja: ║{content}{relleno}║ con anchura visible = BOX_INNER."""
    vis = len(_strip_ansi(content))
    pad = max(0, BOX_INNER - vis)
    return f"║{content}{' ' * pad}║"

TOP    = "╔" + "═" * BOX_INNER + "╗"
SEP    = "╠" + "═" * BOX_INNER + "╣"
BOT    = "╚" + "═" * BOX_INNER + "╝"
INDENT = "   "  # 3 espacios de margen izquierdo dentro de la caja

# ─── Datos del pack ───────────────────────────────────────────────────────────

def _pack_version():
    try:
        return json.loads((BAGO_ROOT / "pack.json").read_text()).get("version", "?")
    except Exception:
        return "?"

def _validate():
    try:
        r = subprocess.run(
            ["python3", str(TOOLS / "validate_pack.py")],
            capture_output=True, text=True, cwd=str(BAGO_ROOT.parent)
        )
        ok = any("GO pack" in l for l in r.stdout.splitlines())
        reason = next((l.strip() for l in r.stdout.splitlines()
                       if l.strip().startswith("KO") or "does not match" in l), "")
        return ok, reason
    except Exception:
        return False, "error"

def _inventory():
    try:
        gs = json.loads((STATE / "global_state.json").read_text())
        inv = gs.get("inventory", {})
        return inv.get("sessions", 0), inv.get("changes", 0), inv.get("evidences", 0)
    except Exception:
        return 0, 0, 0

def _active_scenarios():
    try:
        gs = json.loads((STATE / "global_state.json").read_text())
        sc = gs.get("active_scenarios", [])
        return sc if sc else None
    except Exception:
        return None

def _working_mode():
    try:
        r = subprocess.run(
            ["python3", str(TOOLS / "repo_context_guard.py"), "check"],
            capture_output=True, text=True, cwd=str(BAGO_ROOT.parent)
        )
        data = json.loads(r.stdout)
        return data.get("current", {}).get("working_mode", "self")
    except Exception:
        return "?"

def _detector_verdict():
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "context_detector", TOOLS / "context_detector.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        result = mod.evaluate()
        return result.get("verdict", "CLEAN"), result.get("score", 0), result.get("max_score", 2)
    except Exception:
        return None, 0, 2

def _active_task():
    """Devuelve (title, status) si hay pending_w2_task.json, o None."""
    try:
        data = json.loads((STATE / "pending_w2_task.json").read_text(encoding="utf-8"))
        return data.get("idea_title", "—"), data.get("status", "pending")
    except Exception:
        return None

    try:
        gs = json.loads((STATE / "global_state.json").read_text())
        return gs.get("last_completed_session_id", ""), gs.get("last_completed_workflow", "")
    except Exception:
        return "", ""

# ─── Render ───────────────────────────────────────────────────────────────────

def print_banner(mini=False):
    version        = _pack_version()
    pack_ok, reason = _validate()
    ses, chg, evd  = _inventory()
    mode           = _working_mode()
    scenarios      = _active_scenarios()
    last_sid, last_wf = _last_session()
    verdict, score, max_score = _detector_verdict()
    active_task    = _active_task()
    now_str = datetime.now().strftime("%Y-%m-%d  %H:%M")

    print()
    print(TOP)

    # ── Logo top (cyan) ───────────────────────────────────────────────────────
    print(_box())
    for line in LOGO_TOP:
        print(_box(INDENT + CYAN(line)))
    # ── Logo bottom (azul) ────────────────────────────────────────────────────
    for line in LOGO_BOT:
        print(_box(INDENT + BLUE(line)))
    print(_box())

    # ── Tagline ───────────────────────────────────────────────────────────────
    tagline = (CYAN("B") + "·alanceado  " +
               CYAN("A") + "·daptativo  " +
               CYAN("G") + "·enerativo  " +
               CYAN("O") + "·rganizativo")
    print(_box(INDENT + tagline))

    print(SEP)

    # ── Estado ────────────────────────────────────────────────────────────────
    if pack_ok:
        status_str = GREEN("✅ GO") + "  " + BOLD(f"v{version}") + "  ·  modo: " + (CYAN("self") if mode == "self" else YELLOW("external"))
    else:
        status_str = RED("❌ KO") + "  " + DIM(reason)
    print(_box(INDENT + status_str))

    inv_str = (DIM("ses=") + BOLD(str(ses)) + "  " +
               DIM("chg=") + BOLD(str(chg)) + "  " +
               DIM("evd=") + BOLD(str(evd)) + "  " +
               DIM(now_str))
    print(_box(INDENT + inv_str))

    # ── Escenarios ────────────────────────────────────────────────────────────
    if scenarios:
        sc_str = "  ".join(YELLOW(s) for s in scenarios)
        print(_box(INDENT + DIM("escenarios: ") + sc_str))

    # ── Detector W9 ───────────────────────────────────────────────────────────
    if verdict is not None:
        if verdict == "HARVEST":
            v_str = GREEN("🌾 HARVEST") + "  " + DIM("→ bago cosecha")
        elif verdict == "WATCH":
            v_str = YELLOW(f"👁  WATCH [{score}/{max_score}]")
        else:
            v_str = DIM("✔  CLEAN")
        print(_box(INDENT + DIM("detector W9: ") + v_str))

    # ── Última sesión ─────────────────────────────────────────────────────────
    if last_sid:
        print(_box(INDENT + DIM("última ses: ") + DIM(last_sid) + "  " + DIM(last_wf)))

    # ── Task W2 activa ────────────────────────────────────────────────────────
    if active_task is not None:
        title, tstatus = active_task
        icon = "✅" if tstatus == "done" else "⏳"
        task_color = GREEN if tstatus == "done" else YELLOW
        print(_box(INDENT + DIM("task W2: ") + task_color(f"{icon} {title}")))

    if not mini:
        print(SEP)
        # ── Comandos ─────────────────────────────────────────────────────────
        cmds = [
            ("bago",            "muestra este cartel"),
            ("bago dashboard",  "pack_dashboard"),
            ("bago ideas",      "emit_ideas"),
            ("bago task",       "tarea W2 pendiente"),
            ("bago session",    "abre sesión W2 desde handoff"),
            ("bago stability",  "resumen estabilidad"),
            ("bago cosecha",    "protocolo W9"),
            ("bago detector",   "context_detector"),
            ("bago validate",   "validate_pack"),
        ]
        col_w = max(len(c) for c, _ in cmds)
        for cmd, desc in cmds:
            padded = cmd + " " * (col_w - len(cmd))
            print(_box(INDENT + CYAN(padded) + "  " + DIM("→ " + desc)))

    print(BOT)
    print()


if __name__ == "__main__":
    mini = "--mini" in sys.argv
    print_banner(mini=mini)
