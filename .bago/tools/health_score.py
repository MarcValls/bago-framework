#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
health_score.py — Score único de salud y valor del pack BAGO.

Calcula un score 0-100 compuesto de 5 dimensiones:
  Integridad          (25 pts): validate_pack GO = 25, KO = 0
  Disciplina workflow (20 pts): roles_medios_últimas_10 ≤ 2.0 → 20, hasta 5.0 → proporcional
  Captura decisiones  (20 pts): decisiones/sesión últimas 10 ≥ 2.0 → 20, proporcional
  Estado stale        (15 pts): stale_detector sin ERRORs = 15, cada ERROR = -5
  Consistencia inv.   (20 pts): reconcile_state sin diff = 20, diff = 0

Uso:
  python3 .bago/tools/health_score.py            # output completo
  python3 .bago/tools/health_score.py --score-only   # solo número (para otros scripts)
"""

from pathlib import Path
import json
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).parent))
from bago_utils import get_state_dir, get_bago_tools_dir

ROOT  = Path(__file__).resolve().parents[1]
STATE = get_state_dir()
TOOLS = get_bago_tools_dir()


def run_script(script: str, args: list = None) -> tuple[int, str]:
    cmd = [sys.executable, str(TOOLS / script)] + (args or [])
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=ROOT.parent)
        return r.returncode, (r.stdout + r.stderr).strip()
    except Exception as e:
        return 1, f"ERROR: {e}"


def score_integridad() -> tuple[int, int, str]:
    """validate_pack GO = 25, KO = 0."""
    rc, out = run_script("validate_pack.py")
    if rc == 0 and "GO pack" in out:
        return 25, 25, "GO pack ✅"
    # Extraer mensaje de error
    lines = out.splitlines()
    detail = lines[-1] if lines else "KO"
    return 0, 25, f"KO — {detail}"


def score_disciplina_workflow() -> tuple[int, int, str]:
    """roles_medios_últimas_10 ≤ 2.0 → 20, hasta 5.0 → proporcional, >5.0 → 0."""
    sessions_dir = STATE / "sessions"
    if not sessions_dir.exists():
        return 10, 20, "Sin datos (asumido 10/20)"

    sessions = []
    for f in sessions_dir.glob("*.json"):
        try:
            s = json.loads(f.read_text(encoding="utf-8"))
            if s.get("status") == "closed":
                sessions.append(s)
        except Exception:
            pass

    if not sessions:
        return 10, 20, "Sin sesiones cerradas (asumido 10/20)"

    def sort_key(s):
        return s.get("closed_at") or s.get("created_at") or ""
    sessions.sort(key=sort_key)
    recent = sessions[-10:]

    role_counts = []
    for s in recent:
        roles = s.get("roles_activated", s.get("roles", []))
        if isinstance(roles, list):
            role_counts.append(len(roles))
        else:
            role_counts.append(1)

    avg = sum(role_counts) / len(role_counts) if role_counts else 3.0

    if avg <= 2.0:
        pts = 20
    elif avg >= 5.0:
        pts = 0
    else:
        # Lineal entre 2.0 y 5.0
        pts = int(20 * (5.0 - avg) / 3.0)

    return pts, 20, f"roles_medios={avg:.1f} (últimas {len(recent)} ses)"


def score_captura_decisiones() -> tuple[int, int, str]:
    """decisiones/sesión últimas 10 ≥ 2.0 → 20, proporcional, 0 decisiones → 0."""
    sessions_dir = STATE / "sessions"
    if not sessions_dir.exists():
        return 10, 20, "Sin datos (asumido 10/20)"

    sessions = []
    for f in sessions_dir.glob("*.json"):
        try:
            s = json.loads(f.read_text(encoding="utf-8"))
            if s.get("status") == "closed":
                sessions.append(s)
        except Exception:
            pass

    if not sessions:
        return 10, 20, "Sin sesiones cerradas (asumido 10/20)"

    def sort_key(s):
        return s.get("closed_at") or s.get("created_at") or ""
    sessions.sort(key=sort_key)
    recent = sessions[-10:]

    dec_counts = []
    for s in recent:
        decs = s.get("decisions", [])
        if isinstance(decs, list):
            dec_counts.append(len(decs))
        else:
            dec_counts.append(0)

    avg = sum(dec_counts) / len(dec_counts) if dec_counts else 0

    if avg >= 2.0:
        pts = 20
    elif avg <= 0:
        pts = 0
    else:
        pts = int(20 * avg / 2.0)

    return pts, 20, f"decisiones_medias={avg:.1f} (últimas {len(recent)} ses)"


def score_estado_stale() -> tuple[int, int, str]:
    """stale_detector sin ERRORs = 15, cada ERROR = -5."""
    rc, out = run_script("stale_detector.py")
    if rc == 0 and "✅ Reporting limpio" in out:
        return 15, 15, "Reporting limpio ✅"

    # Contar ERRORs
    error_count = out.count("[ERROR]")
    warn_count = out.count("[WARN]")
    pts = max(0, 15 - error_count * 5)

    if error_count > 0:
        detail = f"{error_count} ERROR(s), {warn_count} WARN(s)"
    else:
        detail = f"{warn_count} WARN(s) (sin ERRORs)"
    return pts, 15, detail


def score_consistencia_inventario() -> tuple[int, int, str]:
    """reconcile_state sin diff = 20, con diff = 0."""
    rc, out = run_script("reconcile_state.py")
    if rc == 0:
        return 20, 20, "Inventario reconciliado ✅"
    # Hay diffs
    first = out.split("\n")[0] if out else "diff detectado"
    return 0, 20, f"Diff detectado — {first}"


def main():
    score_only = "--score-only" in sys.argv
    as_json    = "--json" in sys.argv

    dimensions = [
        ("Integridad",          score_integridad),
        ("Disciplina workflow", score_disciplina_workflow),
        ("Captura decisiones",  score_captura_decisiones),
        ("Estado stale",        score_estado_stale),
        ("Consistencia inv.",   score_consistencia_inventario),
    ]

    results = []
    for name, fn in dimensions:
        pts, max_pts, detail = fn()
        results.append((name, pts, max_pts, detail))

    total = sum(r[1] for r in results)
    max_total = sum(r[2] for r in results)

    if score_only:
        print(total)
        return 0

    if as_json:
        import json as _j
        checks = [
            {"name": name, "score": pts, "max": max_pts, "detail": detail}
            for name, pts, max_pts, detail in results
        ]
        print(_j.dumps({"score": total, "max": max_total, "checks": checks},
                       indent=2, ensure_ascii=False))
        return 0

    # Semáforo
    if total >= 80:
        semaforo = "🟢"
    elif total >= 50:
        semaforo = "🟡"
    else:
        semaforo = "🔴"

    print()
    print(f"BAGO Health Score: {total}/{max_total}  {semaforo}")
    print()
    for name, pts, max_pts, detail in results:
        pct = pts / max_pts if max_pts else 0
        icon = "✅" if pct >= 0.8 else ("⚠️ " if pct >= 0.4 else "❌")
        print(f"  {icon}  {name:<22} {pts:>3}/{max_pts:<3}  {detail}")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
