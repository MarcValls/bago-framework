#!/usr/bin/env python3
"""
bago_shell.py — Shell interactivo persistente BAGO.

Se inicia con `bago` y se queda abierto, como `gh copilot`.
Escribe para filtrar · ↑↓ para navegar · Tab para completar · Enter para ejecutar
q o Ctrl+C para salir.

No requiere dependencias externas — solo stdlib (tty, termios, ANSI).
"""

import json
import re
import subprocess
import sys
import tty
import termios
from pathlib import Path

BAGO_ROOT = Path(__file__).resolve().parent.parent
STATE     = BAGO_ROOT / "state"
TOOLS     = BAGO_ROOT / "tools"
BAGO_BIN  = BAGO_ROOT.parent / "bago"

# ─── ANSI ─────────────────────────────────────────────────────────────────────

_ANSI_RE = re.compile(r"\033\[[0-9;]*m")

def _c(code: str, t: str) -> str:
    return f"\033[{code}m{t}\033[0m"

CYAN   = lambda t: _c("1;36", t)
GREEN  = lambda t: _c("1;32", t)
YELLOW = lambda t: _c("1;33", t)
RED    = lambda t: _c("1;31", t)
BOLD   = lambda t: _c("1", t)
DIM    = lambda t: _c("2", t)
INVERT = lambda t: _c("7", t)

def _vlen(s: str) -> int:
    return len(_ANSI_RE.sub("", s))


# ─── Catálogo de comandos ─────────────────────────────────────────────────────

# (cmd, descripción)
_CMDS: list[tuple[str, str]] = [
    ("next",        "Empezar nueva tarea — idea + acepta + inicia flujo"),
    ("done",        "Cerrar tarea actual — registra progreso"),
    ("status",      "Estado actual — flujo, tarea y salud del sistema"),
    ("ideas",       "Ver todas las ideas — motor de prioridades"),
    ("health",      "Salud del sistema — métricas y alertas"),
    ("hello",       "Guía y onboarding — recorrido interactivo"),
    ("flow start",  "Iniciar flujo de trabajo manualmente"),
    ("flow done",   "Cerrar flujo activo"),
    ("flow status", "Estado del flujo activo"),
    ("task",        "Ver tarea W2 pendiente"),
    ("dashboard",   "Dashboard — visión global del sistema"),
    ("stability",   "Resumen de estabilidad"),
    ("audit",       "Auditoría del proyecto"),
    ("history",     "Historial de sesiones"),
    ("help",        "Ayuda y todos los comandos disponibles"),
]


def _filter(text: str) -> list[tuple[str, str]]:
    """Filtra comandos por prefijo exacto primero, luego substring."""
    if not text:
        return _CMDS
    t = text.lower()
    exact   = [(c, d) for c, d in _CMDS if c.lower().startswith(t)]
    partial = [(c, d) for c, d in _CMDS if t in c.lower() and not c.lower().startswith(t)]
    return exact + partial


# ─── Contexto del sistema ─────────────────────────────────────────────────────

def _ctx() -> dict:
    c = {"health": -1, "workflow": None, "task": None}
    try:
        data = json.loads((STATE / "global_state.json").read_text("utf-8"))
        c["health"] = data.get("system_health", {}).get("overall_score", -1)
        aw = data.get("sprint_status", {}).get("active_workflow")
        if isinstance(aw, dict):
            c["workflow"] = aw.get("title") or aw.get("code")
    except Exception:
        pass
    try:
        t = json.loads((STATE / "pending_w2_task.json").read_text("utf-8"))
        if t.get("status") != "done":
            c["task"] = t.get("title") or t.get("task")
    except Exception:
        pass
    return c


def _recommend(c: dict) -> str:
    if c["health"] >= 0 and c["health"] < 55:
        return "health"
    if c["task"]:
        return "done"
    if c["workflow"]:
        return "status"
    return "next"


# ─── Input raw mode ───────────────────────────────────────────────────────────

def _getch() -> str:
    """Lee una tecla o secuencia de escape en modo raw. No bloquea el eco."""
    fd  = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        b = sys.stdin.buffer.read(1)
        ch = b.decode("utf-8", errors="replace")
        if ch == "\x1b":
            try:
                rest = sys.stdin.buffer.read(2).decode("utf-8", errors="replace")
                return ch + rest
            except Exception:
                return ch
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


# ─── Renderizado ──────────────────────────────────────────────────────────────

_W = 64  # ancho interior entre │ y │

def _render(buf: str, sel: int, ctx: dict) -> list[str]:
    cmds = _filter(buf)
    rec  = _recommend(ctx)
    out  = []

    def _row(txt: str = "") -> str:
        """Línea │ content │ con relleno hasta _W."""
        padded = txt + " " * max(0, _W - _vlen(txt))
        return f"  {CYAN('│')} {padded} {CYAN('│')}"

    # ── cabecera de estado ────────────────────────────────────────────────────
    h    = ctx["health"]
    hcol = (GREEN if h >= 80 else YELLOW if h >= 55 else RED) if h >= 0 else DIM
    hstr = hcol(f"{h}%") if h >= 0 else DIM("—")
    wstr = GREEN(ctx["workflow"][:20]) if ctx["workflow"] else DIM("ninguno")
    tstr = YELLOW(ctx["task"][:20])   if ctx["task"]     else DIM("—")

    out.append(f"  {CYAN('┌' + '─' * _W + '┐')}")
    out.append(_row(BOLD("BAGO Shell") + DIM("  ·  q o Ctrl+C para salir")))
    out.append(_row(f"  salud {hstr}   flujo {wstr}   tarea {tstr}"))
    out.append(f"  {CYAN('├' + '─' * _W + '┤')}")

    # ── lista de comandos ─────────────────────────────────────────────────────
    visible = cmds[:11]  # máximo 11 items para caber en pantalla

    for i, (cmd, desc) in enumerate(visible):
        is_sel = (i == sel)
        is_rec = (cmd == rec and not buf)
        star   = YELLOW("★") if is_rec else " "
        idx    = DIM(f"{i + 1:2d}")

        cmd_s   = f"bago {cmd}"
        cmd_w   = 18
        cmd_fmt = (BOLD(GREEN(f"{cmd_s:<{cmd_w}}"))
                   if is_sel else GREEN(f"{cmd_s:<{cmd_w}}"))

        desc_max = _W - cmd_w - 8
        plain_d  = desc if len(desc) <= desc_max else desc[:desc_max - 1] + "…"
        desc_fmt = (BOLD(plain_d) if is_sel else DIM(plain_d))

        inner = f" {star} {idx}  {cmd_fmt}  {desc_fmt}"
        padded = inner + " " * max(0, _W - _vlen(inner) + 1)
        if is_sel:
            padded = INVERT(padded)
        out.append(f"  {CYAN('│')}{padded}{CYAN('│')}")

    if not visible:
        out.append(_row(DIM(f"  (sin coincidencias para '{buf}')")))

    # ── prompt de entrada ─────────────────────────────────────────────────────
    out.append(f"  {CYAN('├' + '─' * _W + '┤')}")
    cursor_block = BOLD("█") if not buf else BOLD(GREEN("▌"))
    prompt_inner = f"  {CYAN('❯')} {GREEN(buf)}{cursor_block}"
    out.append(_row(prompt_inner))
    hint = DIM("  ↑↓ navegar · escribir para filtrar · Tab completar · Enter ejecutar")
    out.append(_row(hint))
    out.append(f"  {CYAN('└' + '─' * _W + '┘')}")

    return out


def _draw(lines: list[str], prev: int) -> int:
    if prev:
        sys.stdout.write(f"\033[{prev}A\033[J")
    for line in lines:
        sys.stdout.write(line + "\n")
    sys.stdout.flush()
    return len(lines)


# ─── Ejecución de comandos ────────────────────────────────────────────────────

def _run(cmd: str) -> None:
    """Ejecuta bago <cmd> como subproceso, heredando stdin/stdout."""
    parts = cmd.strip().split()
    if not parts:
        return
    subprocess.run([sys.executable, str(BAGO_BIN)] + parts)


# ─── Shell loop ───────────────────────────────────────────────────────────────

def _shell() -> int:
    buf      = []
    sel      = 0
    prev_rows = 0

    while True:
        context = _ctx()
        cmds    = _filter("".join(buf))
        sel     = min(sel, max(0, len(cmds) - 1))

        lines     = _render("".join(buf), sel, context)
        prev_rows = _draw(lines, prev_rows)

        key = _getch()

        # ── Navegación ────────────────────────────────────────────────────────
        if key == "\x1b[A":      # ↑
            sel = max(0, sel - 1)

        elif key == "\x1b[B":    # ↓
            sel = min(len(cmds) - 1, sel + 1)

        # ── Tab: completar con la selección actual ─────────────────────────
        elif key == "\t":
            if cmds:
                buf = list(cmds[sel][0])
                sel = 0

        # ── Enter: ejecutar ────────────────────────────────────────────────
        elif key in ("\r", "\n"):
            text = "".join(buf).strip()
            cmd  = cmds[sel][0] if cmds else text
            if not cmd:
                continue
            # Limpiar UI antes de ejecutar
            sys.stdout.write(f"\033[{prev_rows}A\033[J")
            sys.stdout.flush()
            prev_rows = 0
            print(f"\n  {CYAN('❯')} {BOLD(GREEN('bago ' + cmd))}\n")
            _run(cmd)
            # Reset para el siguiente ciclo
            buf = []
            sel = 0
            print()  # espacio entre output y el menú de vuelta

        # ── Backspace ─────────────────────────────────────────────────────
        elif key == "\x7f":
            if buf:
                buf.pop()
            sel = 0

        # ── Salir ─────────────────────────────────────────────────────────
        elif key in ("\x03", "\x04"):   # Ctrl+C / Ctrl+D
            sys.stdout.write(f"\033[{prev_rows}A\033[J")
            sys.stdout.flush()
            print(f"  {DIM('Saliendo de BAGO Shell.')}\n")
            return 0

        elif key.lower() == "q" and not buf:
            sys.stdout.write(f"\033[{prev_rows}A\033[J")
            sys.stdout.flush()
            print(f"  {DIM('Saliendo de BAGO Shell.')}\n")
            return 0

        # ── Texto normal ──────────────────────────────────────────────────
        elif key.isprintable() and len(key) == 1:
            buf.append(key)
            sel = 0


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    if not sys.stdin.isatty():
        # Sin TTY: lista plana
        print()
        for i, (cmd, desc) in enumerate(_CMDS):
            print(f"  {i + 1:2d}  bago {cmd:<18}  {desc}")
        print()
        return 0

    print()
    print(f"  {CYAN(BOLD('BAGO Shell'))} — {DIM('escribe, usa flechas ↑↓ o Tab · q para salir')}")
    print()
    return _shell()


if __name__ == "__main__":
    sys.exit(main())
