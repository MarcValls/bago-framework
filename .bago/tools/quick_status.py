#!/usr/bin/env python3
"""
quick_status.py — Dashboard compacto del proyecto
Muestra estado en una pantalla: validación, inventario, ideas, detector.

Uso:
  python3 .bago/tools/quick_status.py
  ./bago status
"""

import json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

BAGO_ROOT = Path(__file__).resolve().parent.parent
STATE     = BAGO_ROOT / "state"
TOOLS     = BAGO_ROOT / "tools"

# ─── Colores ANSI ─────────────────────────────────────────────────────────────
USE_COLOR = sys.stdout.isatty()

def _c(code, text):
    if not USE_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"

CYAN   = lambda t: _c("1;36", t)
GREEN  = lambda t: _c("1;32", t)
RED    = lambda t: _c("1;31", t)
YELLOW = lambda t: _c("1;33", t)
BOLD   = lambda t: _c("1",    t)
DIM    = lambda t: _c("2",    t)

# ─── Datos ────────────────────────────────────────────────────────────────────

def get_version():
    try:
        return json.loads((BAGO_ROOT / "pack.json").read_text()).get("version", "?")
    except Exception:
        return "?"

def get_validation():
    try:
        r = subprocess.run(
            ["python3", str(TOOLS / "validate_pack.py")],
            capture_output=True, text=True, cwd=str(BAGO_ROOT.parent), timeout=5
        )
        ok = "GO pack" in r.stdout
        return "OK" if ok else "KO"
    except Exception:
        return "?"

def get_inventory():
    try:
        gs = json.loads((STATE / "global_state.json").read_text())
        inv = gs.get("inventory", {})
        return inv.get("sessions", 0), inv.get("changes", 0), inv.get("evidences", 0)
    except Exception:
        return 0, 0, 0

def get_last_session():
    try:
        gs = json.loads((STATE / "global_state.json").read_text())
        return gs.get("last_completed_session_id", "N/A")
    except Exception:
        return "N/A"

def get_ideas_count():
    try:
        ideas_dir = BAGO_ROOT / "ideas"
        if ideas_dir.exists():
            return len(list(ideas_dir.glob("*.json")))
        return 0
    except Exception:
        return 0

def get_detector_verdict():
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "context_detector", TOOLS / "context_detector.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        result = mod.evaluate()
        return result.get("verdict", "CLEAN")
    except Exception:
        return "?"

# ─── Render ───────────────────────────────────────────────────────────────────

def main():
    version = get_version()
    validation = get_validation()
    ses, chg, evd = get_inventory()
    last_sid = get_last_session()
    ideas_count = get_ideas_count()
    verdict = get_detector_verdict()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

    print()
    print(BOLD(CYAN("BAGO")), BOLD(f"v{version}"))
    print(DIM("─" * 54))

    # Validación
    if validation == "OK":
        print(GREEN("✓ Pack válido"))
    elif validation == "KO":
        print(RED("✗ Pack inválido") + DIM(" (ejecuta 'bago validate' para detalles)"))
    else:
        print(YELLOW("? Estado desconocido"))

    # Inventario
    print()
    print(BOLD("Inventario:"))
    print(f"  Sesiones:   {CYAN(str(ses))}")
    print(f"  Cambios:    {CYAN(str(chg))}")
    print(f"  Evidencias: {CYAN(str(evd))}")

    # Ideas
    print()
    print(BOLD("Ideas:"), CYAN(str(ideas_count)), DIM("disponibles"))
    if ideas_count > 0:
        print(DIM("  → Usa 'bago ideas' para verlas"))

    # Detector
    print()
    print(BOLD("Detector W9:"), end=" ")
    if verdict == "HARVEST":
        print(GREEN("🌾 HARVEST") + DIM(" (ejecuta 'bago cosecha')"))
    elif verdict == "WATCH":
        print(YELLOW("👁 WATCH"))
    else:
        print(DIM("✔ CLEAN"))

    # Última sesión
    if last_sid != "N/A":
        print()
        print(BOLD("Última sesión:"), DIM(last_sid))

    # Timestamp
    print()
    print(DIM(f"Estado a {now}"))
    print()

if __name__ == "__main__":
    main()
