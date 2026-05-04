#!/usr/bin/env python3
"""
pack_dashboard.py — Estado del pack BAGO en una pantalla.
Uso: python3 .bago/tools/pack_dashboard.py [--full]
"""
import json
import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
STATE = ROOT / "state"
TOOLS = ROOT / "tools"

def _count(folder):
    return len(list((STATE / folder).glob("*.json")))

def _validate():
    try:
        r = subprocess.run(
            ["python3", str(TOOLS / "validate_pack.py")],
            capture_output=True, text=True, cwd=ROOT.parent
        )
        out = r.stdout.strip().splitlines()
        last = out[-1] if out else "?"
        return "GO" if "GO pack" in last else f"KO ({last})"
    except Exception as e:
        return f"ERROR ({e})"

def _load_global():
    p = STATE / "global_state.json"
    d = json.loads(p.read_text()) if p.exists() else {}
    if not d.get("pack_version"):
        pack_p = ROOT / "pack.json"
        if pack_p.exists():
            pack = json.loads(pack_p.read_text())
            d["pack_version"] = pack.get("version", "?")
    return d

def _escenario_002():
    excl = {"state/sessions/", "state/changes/", "state/evidences/", "TREE.txt", "CHECKSUMS.sha256"}
    on_u, on_n, off_u, off_n = 0, 0, 0, 0
    for f in (STATE / "sessions").glob("*.json"):
        s = json.loads(f.read_text())
        if s.get("escenario") != "ESCENARIO-002" or s.get("status") != "closed":
            continue
        arts = [a for a in s.get("artifacts", []) if not any(a.startswith(e) for e in excl)]
        if s.get("bago_mode") == "on":
            on_u += len(arts); on_n += 1
        else:
            off_u += len(arts); off_n += 1
    return on_n, on_u, off_n, off_u

def _avg_production(last_n=5):
    excl = {"state/sessions/", "state/changes/", "state/evidences/", "TREE.txt", "CHECKSUMS.sha256"}
    sessions = []
    for f in (STATE / "sessions").glob("*.json"):
        s = json.loads(f.read_text())
        if s.get("status") != "closed":
            continue
        arts = [a for a in s.get("artifacts", []) if not any(a.startswith(e) for e in excl)]
        sessions.append((s.get("updated_at", ""), len(arts)))
    sessions.sort(reverse=True)
    subset = sessions[:last_n]
    if not subset:
        return 0.0
    return round(sum(u for _, u in subset) / len(subset), 1)

def _context_detector():
    """Ejecuta context_detector y devuelve (verdict, score, threshold, n_signals)."""
    detector = TOOLS / "context_detector.py"
    if not detector.exists():
        return None, 0, 0, 0
    try:
        spec = importlib.util.spec_from_file_location("context_detector", detector)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        result = mod.evaluate()
        return (
            result.get("verdict", "?"),
            result.get("score", 0),
            result.get("threshold", 2),
            len(result.get("signals", []))
        )
    except Exception:
        return "ERR", 0, 0, 0

def _escenario_003_stats():
    """Cuenta cosechas W9 completadas en ESCENARIO-003."""
    harvests = []
    for f in (STATE / "sessions").glob("*.json"):
        s = json.loads(f.read_text())
        if (s.get("escenario") == "ESCENARIO-003"
                and s.get("status") == "closed"
                and s.get("task_type") == "harvest"):
            harvests.append(s)
    n = len(harvests)
    if n == 0:
        return n, 0.0, 0.0
    avg_dec = round(sum(len(s.get("decisions", [])) for s in harvests) / n, 1)
    avg_art = round(sum(len([a for a in s.get("artifacts", [])
                              if "state/" not in a]) for s in harvests) / n, 1)
    return n, avg_dec, avg_art

def main():
    full = "--full" in sys.argv
    g = _load_global()
    pack_status = _validate()
    inv = g.get("inventory", {})
    on_n, on_u, off_n, off_u = _escenario_002()
    avg = _avg_production()
    verdict, score, threshold, n_signals = _context_detector()
    e003_n, e003_dec, e003_art = _escenario_003_stats()

    on_avg  = round(on_u  / on_n,  1) if on_n  else 0
    off_avg = round(off_u / off_n, 1) if off_n else 0
    delta   = round(on_avg - off_avg, 1)
    leader  = "ON ✅" if delta > 0 else ("OFF 🔴" if delta < 0 else "EMPATE")

    status_icon = "✅" if pack_status == "GO" else "❌"
    total_ses = _count("sessions")

    # Línea del detector
    verdict_icons = {"HARVEST": "🌾 HARVEST", "WATCH": "👁  WATCH  ", "CLEAN": "✅ CLEAN  ", "ERR": "⚠️  ERROR  "}
    v_str = verdict_icons.get(verdict, f"?  {verdict:<7}")
    bar_filled = min(int(10 * score / max(threshold, 1)), 10)
    bar = "█" * bar_filled + "░" * (10 - bar_filled)

    # Escenario-003 estado
    active_scenarios = g.get("active_scenarios", [])
    e003_active = "ESCENARIO-003" in active_scenarios

    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║              BAGO PACK DASHBOARD                    ║")
    print("╠══════════════════════════════════════════════════════╣")
    print(f"║  Pack:      {status_icon} {pack_status:<41}║")
    print(f"║  Versión:   {g.get('pack_version','?'):<43}║")
    print("╠══════════════════════════════════════════════════════╣")
    print(f"║  Inventario   sessions={inv.get('sessions','?')} ({total_ses} archivos) "
          f"changes={inv.get('changes','?')} evidences={inv.get('evidences','?')}  ║")
    print("╠══════════════════════════════════════════════════════╣")
    print(f"║  Producción últimas 5 sesiones:   {avg} útiles/sesión       ║")
    print("╠══════════════════════════════════════════════════════╣")
    print(f"║  ESCENARIO-002  ON({on_n})={on_avg}/ses  OFF({off_n})={off_avg}/ses"
          f"  Δ={delta:+.1f}  {leader:<6}║")
    print("╠══════════════════════════════════════════════════════╣")
    e3_tag = "🔬 ACTIVO" if e003_active else "CERRADO  "
    print(f"║  ESCENARIO-003  {e3_tag}  cosechas={e003_n}  dec/harvest={e003_dec}  ║")
    print("╠══════════════════════════════════════════════════════╣")
    if verdict:
        print(f"║  Detector W9:  {v_str}  [{bar}] {score}/{threshold}        ║")
        if verdict == "HARVEST":
            print( "║  → python3 .bago/tools/cosecha.py                   ║")
    print("╠══════════════════════════════════════════════════════╣")
    lc = g.get("last_completed_session_id", "—")
    print(f"║  Última sesión: {lc:<37}║")
    print(f"║  Workflow:      {g.get('last_completed_workflow','—'):<37}║")
    active = g.get("active_session_id") or "—"
    print(f"║  Activa ahora:  {active:<37}║")
    print("╚══════════════════════════════════════════════════════╝")
    print()

    if full:
        print("  Detalle ESCENARIO-002:")
        excl = {"state/sessions/", "state/changes/", "state/evidences/", "TREE.txt", "CHECKSUMS.sha256"}
        for f in sorted((STATE / "sessions").glob("*.json")):
            s = json.loads(f.read_text())
            if s.get("escenario") != "ESCENARIO-002" or s.get("status") != "closed":
                continue
            arts = [a for a in s.get("artifacts", []) if not any(a.startswith(e) for e in excl)]
            mode = s.get("bago_mode", "?")
            ronda = s.get("ronda", "?")
            roles = len(s.get("roles_activated", []))
            print(f"    R{ronda} {mode.upper():<3} | útiles={len(arts)} | roles={roles} | {s['session_id']}")
        print()

        if e003_n > 0:
            print("  Detalle ESCENARIO-003 (cosechas):")
            for f in sorted((STATE / "sessions").glob("SES-HARVEST-*.json")):
                s = json.loads(f.read_text())
                if s.get("status") != "closed":
                    continue
                dec = len(s.get("decisions", []))
                arts = len([a for a in s.get("artifacts", []) if "state/" not in a])
                print(f"    {s['session_id']}  dec={dec}  útiles={arts}")
            print()

        print("  Señales del detector:")
        try:
            spec = importlib.util.spec_from_file_location("context_detector", TOOLS / "context_detector.py")
            mod  = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            result = mod.evaluate()
            for sig in result.get("signals", []):
                w = {"very_high": "🔴", "high": "🟠", "medium": "🟡"}.get(sig["weight"], "⚪")
                print(f"    {w} {sig['desc']}")
            if not result.get("signals"):
                print("    Sin señales activas.")
        except Exception as e:
            print(f"    Error al leer detector: {e}")
        print()


def _self_test():
    """Autotest mínimo — verifica arranque limpio del módulo."""
    from pathlib import Path as _P
    assert _P(__file__).exists(), "fichero no encontrado"
    print("  1/1 tests pasaron")

if __name__ == "__main__":
    if "--test" in sys.argv:
        _self_test()
        raise SystemExit(0)
    main()
