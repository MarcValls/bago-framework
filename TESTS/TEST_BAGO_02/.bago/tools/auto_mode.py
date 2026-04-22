#!/usr/bin/env python3
"""
auto_mode.py — BAGO Modo Automático
Evalúa el estado actual y ejecuta los pasos coherentes sin intervención humana.

Uso (via bago script):
  python3 bago auto
  python3 bago auto --dry-run     (muestra el plan sin ejecutar nada)
  python3 bago auto --steps N     (máximo N pasos, por defecto 5)
  python3 bago auto --json        (salida machine-readable)

O directo:
  python3 .bago/tools/auto_mode.py --dry-run
"""

import json
import sys
import subprocess
import argparse
from datetime import datetime
from pathlib import Path
import os

# ─── Rutas ────────────────────────────────────────────────────────────────────
# Este archivo vive en <project>/.bago/tools/auto_mode.py
# PACK_DIR = <project>/.bago
# PROJECT_ROOT = <project>
PACK_DIR     = Path(__file__).resolve().parent.parent   # .bago/
PROJECT_ROOT = PACK_DIR.parent                           # project root (donde está el script 'bago')
STATE_DIR    = PACK_DIR / "state"
TOOLS        = PACK_DIR / "tools"

# ─── Imports directos de herramientas BAGO ───────────────────────────────────
sys.path.insert(0, str(TOOLS))
os.chdir(str(PROJECT_ROOT))   # las herramientas asumen cwd = project root

# ─── Args ─────────────────────────────────────────────────────────────────────
def _parse():
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--dry-run",  action="store_true")
    p.add_argument("--json",     action="store_true", dest="as_json")
    p.add_argument("--steps",    type=int, default=5)
    args, _ = p.parse_known_args()
    return args

# ─── Estado ───────────────────────────────────────────────────────────────────
def _global_state():
    try:
        return json.loads((STATE_DIR / "global_state.json").read_text())
    except Exception:
        return {}

def _pending_task():
    try:
        t = json.loads((STATE_DIR / "pending_w2_task.json").read_text())
        return t if t.get("idea_title") else None
    except Exception:
        return None

def _health_score():
    try:
        from health_score import (score_integridad, score_disciplina_workflow,
                                   score_captura_decisiones, score_estado_stale,
                                   score_consistencia_inventario)
        total, max_total = 0, 0
        for fn in [score_integridad, score_disciplina_workflow,
                   score_captura_decisiones, score_estado_stale,
                   score_consistencia_inventario]:
            s, m, _ = fn()
            total += s; max_total += m
        return (total * 100 // max_total) if max_total else 0
    except Exception:
        return -1

def _detector():
    try:
        from context_detector import evaluate
        result = evaluate()
        verdict = result.get("verdict", "CLEAN")
        high    = len(result.get("high_signals", []))
        low     = len(result.get("low_signals", []))
        return verdict, high, low
    except Exception:
        return "CLEAN", 0, 0

def _validate():
    try:
        r1 = subprocess.run(
            [sys.executable, str(TOOLS / "validate_manifest.py")],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT)
        )
        r2 = subprocess.run(
            [sys.executable, str(TOOLS / "validate_state.py")],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT)
        )
        return r1.returncode == 0 and r2.returncode == 0
    except Exception:
        return False

def _stale_count():
    try:
        r = subprocess.run(
            [sys.executable, str(TOOLS / "stale_detector.py")],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT)
        )
        return sum(1 for l in r.stdout.splitlines() if "WARN" in l or "stale" in l.lower())
    except Exception:
        return 0

# ─── Decisión ─────────────────────────────────────────────────────────────────
def _decide(gs, health, verdict, high_signals, pack_ok, task, stale):
    """
    Prioridad:
      1. Pack roto          → validate (bloqueante)
      2. Health < 60        → audit
      3. Stale > 2          → stale
      4. Tarea W2 activa    → task (solo mostrar)
      5. HARVEST + high>=2  → cosecha (interactivo)
      6. HARVEST + high<2   → sugerencia sin ejecución
      7. Sin tarea          → ideas
      8. Siempre al final   → dashboard
    """
    steps = []

    if not pack_ok:
        steps.append({
            "id": "validate", "cmd": "validate",
            "label": "🔴 Pack dañado — revisar integridad",
            "reason": "validate_manifest o validate_state falla",
            "interactive": False, "blocking": True
        })
        return steps

    if health >= 0 and health < 60:
        steps.append({
            "id": "audit", "cmd": "audit",
            "label": f"🟠 Health bajo ({health}/100) — ejecutar audit",
            "reason": f"health_score = {health} < 60",
            "interactive": False, "blocking": False
        })

    if stale > 2:
        steps.append({
            "id": "stale", "cmd": "stale",
            "label": f"🟡 {stale} artefactos stale detectados",
            "reason": f"{stale} items stale en state/",
            "interactive": False, "blocking": False
        })

    if task:
        steps.append({
            "id": "task", "cmd": "task",
            "label": f"⏳ Tarea W2 activa: {task.get('idea_title','?')[:50]}",
            "reason": "pending_w2_task.json existe con tarea pendiente",
            "interactive": False, "blocking": False
        })

    if verdict == "HARVEST" and high_signals >= 2:
        steps.append({
            "id": "cosecha", "cmd": "cosecha",
            "label": "🌾 Detector W9: HARVEST — contexto listo para cosechar",
            "reason": f"detector=HARVEST con {high_signals} señales de peso alto",
            "interactive": True, "blocking": False
        })
    elif verdict == "HARVEST":
        steps.append({
            "id": "cosecha_hint", "cmd": None,
            "label": "🌾 Sugerencia: considera ejecutar bago cosecha",
            "reason": f"detector=HARVEST ({high_signals} señales altas — umbral mínimo: 2)",
            "interactive": False, "blocking": False
        })

    if not task and verdict != "HARVEST":
        steps.append({
            "id": "ideas", "cmd": "ideas",
            "label": "💡 Sin tarea activa — revisar ideas priorizadas",
            "reason": "no hay pending_w2_task.json ni problemas detectados",
            "interactive": False, "blocking": False
        })

    steps.append({
        "id": "dashboard", "cmd": "dashboard",
        "label": "📊 Dashboard — resumen del estado actual",
        "reason": "paso final de auto mode",
        "interactive": False, "blocking": False
    })

    return steps

# ─── Ejecutor ─────────────────────────────────────────────────────────────────
def _run_step(step):
    cmd = step.get("cmd")
    if not cmd:
        return True
    bago_script = PROJECT_ROOT / "bago"
    result = subprocess.run(
        [sys.executable, str(bago_script), cmd],
        cwd=str(PROJECT_ROOT)
    )
    return result.returncode == 0

# ─── Formato ──────────────────────────────────────────────────────────────────
W = 56
TOP = "╔" + "═" * W + "╗"
MID = "╠" + "═" * W + "╣"
BOT = "╚" + "═" * W + "╝"

def _box(text=""):
    return f"║  {text:<{W-2}}║"

def _health_icon(h):
    if h < 0:   return "?"
    if h >= 80: return f"✅ {h}/100"
    if h >= 60: return f"🟠 {h}/100"
    return f"🔴 {h}/100"

def _print_header(health, verdict, pack_ok, task, dry_run):
    print()
    print(TOP)
    print(_box("BAGO · Modo Automático"))
    print(MID)
    print(_box(f"  Pack:     {'✅ GO' if pack_ok else '🔴 FAIL'}"))
    print(_box(f"  Health:   {_health_icon(health)}"))
    det_map = {"HARVEST": "🌾 HARVEST", "WATCH": "👁 WATCH", "CLEAN": "✅ CLEAN"}
    print(_box(f"  Detector: {det_map.get(verdict, verdict)}"))
    t_str = ("⏳ " + task.get("idea_title","?")[:40]) if task else "—"
    print(_box(f"  Tarea:    {t_str}"))
    if dry_run:
        print(MID)
        print(_box("  ⚠️  DRY-RUN — no se ejecuta nada"))
    print(BOT)
    print()

# ─── Entry point ──────────────────────────────────────────────────────────────
def run():
    args      = _parse()
    dry_run   = args.dry_run
    as_json   = args.as_json
    max_steps = args.steps

    gs                     = _global_state()
    health                 = _health_score()
    verdict, high, low     = _detector()
    pack_ok                = _validate()
    task                   = _pending_task()
    stale                  = _stale_count()

    steps = _decide(gs, health, verdict, high, pack_ok, task, stale)[:max_steps]

    if as_json:
        print(json.dumps({
            "state": {
                "health": health, "detector": verdict, "high_signals": high,
                "pack_ok": pack_ok,
                "pending_task": task.get("idea_title") if task else None,
                "stale": stale
            },
            "plan": [{"id": s["id"], "cmd": s.get("cmd"), "label": s["label"],
                       "interactive": s.get("interactive", False)} for s in steps],
            "dry_run": dry_run,
            "ts": datetime.now().isoformat()
        }, indent=2, ensure_ascii=False))
        return

    _print_header(health, verdict, pack_ok, task, dry_run)

    print("  Plan de pasos:")
    print()
    for i, s in enumerate(steps, 1):
        icon = "→" if s.get("cmd") else "·"
        tag  = "  [requiere input]" if s.get("interactive") else ""
        print(f"  [{i}] {icon}  {s['label']}{tag}")
        print(f"       ↳ {s['reason']}")
        print()

    if dry_run:
        return

    print("─" * (W + 4))
    print()
    for i, step in enumerate(steps, 1):
        if step.get("interactive"):
            print(f"  [{i}] {step['label']}")
            ans = input("       ¿Ejecutar ahora? [S/n] ").strip().lower()
            if ans == "n":
                print("       Saltado.\n")
                continue

        if step.get("cmd"):
            print(f"  [{i}] {step['label']}")

        ok = _run_step(step)
        print()

        if not ok and step.get("blocking"):
            print("  ❌ Paso bloqueante falló — deteniendo auto mode.")
            break

    print("  ✅ Auto mode completado.")
    print()


if __name__ == "__main__":
    run()
