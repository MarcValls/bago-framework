#!/usr/bin/env python3
"""
pack_dashboard.py — BAGO Cockpit v2
Dashboard unificado: health ring, riesgos, deuda, velocity, contratos, hotspots.
Uso: python3 .bago/tools/pack_dashboard.py [--full] [--json] [--compact]
"""
import json, subprocess, sys, re, os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

ROOT   = Path(__file__).parent.parent
STATE  = ROOT / "state"
TOOLS  = ROOT / "tools"
W      = 62   # ancho total del panel

# ─── helpers visuales ─────────────────────────────────────────────────────────

def _bar(val, maxv=100, width=20, fill="█", empty="░"):
    n = max(0, min(width, int(width * val / max(maxv, 1))))
    return fill * n + empty * (width - n)

def _ring(score):
    """Semicírculo ASCII de salud."""
    if score >= 90: color = "🟢"
    elif score >= 70: color = "🟡"
    else: color = "🔴"
    return f"{color} {score:3d}/100"

def _sparkline(values):
    """Mini sparkline de 8 chars."""
    bars = " ▁▂▃▄▅▆▇█"
    if not values: return "—"
    mn, mx = min(values), max(values)
    span = mx - mn or 1
    return "".join(bars[max(0, min(8, int((v - mn) / span * 8)))] for v in values[-8:])

def _pad(text, width):
    """Pad/truncate text to exactly width chars."""
    text = str(text)
    visible = re.sub(r"\[[0-9;]*m", "", text)
    n = len(visible)
    if n < width:
        return text + " " * (width - n)
    return text[:width]

def _row(content, width=W):
    """Fila de dashboard con bordes."""
    inner = width - 4
    return f"║  {_pad(content, inner)}  ║"

def _divider():
    return "╠" + "═" * (W - 2) + "╣"

def _header(title):
    inner = W - 4
    t = title.center(inner)
    return f"║  {t}  ║"

def _top():
    return "╔" + "═" * (W - 2) + "╗"

def _bottom():
    return "╚" + "═" * (W - 2) + "╝"

# ─── cargadores de datos ──────────────────────────────────────────────────────

def _count(folder):
    d = STATE / folder
    return len(list(d.glob("*.json"))) if d.exists() else 0

def _load_global():
    p = STATE / "global_state.json"
    d = json.loads(p.read_text()) if p.exists() else {}
    if not d.get("pack_version"):
        pp = ROOT / "pack.json"
        if pp.exists():
            d["pack_version"] = json.loads(pp.read_text()).get("version", "?")
    return d

def _run_tool(args, timeout=10):
    try:
        r = subprocess.run(
            [sys.executable] + [str(a) for a in args],
            capture_output=True, text=True, timeout=timeout,
            cwd=ROOT.parent
        )
        return r.stdout.strip(), r.returncode
    except Exception as e:
        return str(e), -1

def _health():
    """Lee health via import directo (evita subprocess lento)."""
    try:
        sys.path.insert(0, str(TOOLS))
        import health_score as hs
        # score_* functions return (pts, max_pts, detail) → r[0]=earned, r[1]=max
        results = [
            hs.score_integridad(),
            hs.score_disciplina_workflow(),
            hs.score_captura_decisiones(),
            hs.score_estado_stale(),
            hs.score_consistencia_inventario(),
        ]
        total   = sum(r[0] for r in results)
        max_tot = sum(r[1] for r in results)
        label = "🟢 Excelente" if total >= 90 else ("🟡 Aceptable" if total >= 50 else "🔴 Crítico")
        return total, label
    except Exception:
        return 0, "?"

def _validate():
    out, rc = _run_tool([TOOLS / "validate_pack.py"])
    if "GO pack" in out: return "✅ GO"
    if rc == 0: return "✅ GO"
    return "❌ KO"

def _detector():
    try:
        sys.path.insert(0, str(TOOLS))
        from context_detector import evaluate
        r = evaluate()
        verdict = r.get("verdict", "CLEAN")
        score   = r.get("score", 0)
        thresh  = r.get("threshold", 2)
        return verdict, score, thresh
    except Exception:
        return "CLEAN", 0, 2

def _top_risks():
    """Returns (by_category_dict, total_exposure, items_count)."""
    try:
        out, _ = _run_tool([TOOLS / "risk_matrix.py", "--json"], timeout=8)
        data = json.loads(out)
        by_cat   = data.get("by_category", {})
        exposure = data.get("total_exposure", 0.0)
        items    = data.get("items", 0)
        return by_cat, exposure, items
    except Exception:
        return {}, 0.0, 0

def section_risks():
    by_cat, exposure, items = _top_risks()
    level = "BAJA" if exposure < 5 else ("MEDIA" if exposure < 20 else ("ALTA" if exposure < 100 else "CRÍTICA"))
    ico   = "🟢" if exposure < 5 else ("🟡" if exposure < 20 else ("🔴" if exposure < 100 else "🚨"))
    if items == 0 or not by_cat:
        return [_header("── RIESGOS ──"), _row(f"🟢 Sin riesgos activos — exposición 0.0 (BAJA)")]
    lines = [_header("── RIESGOS ──"), _row(f"{ico} Exposición total: {exposure:.1f} ({level})  |  {items} hallazgos")]
    cat_icons = {"Security": "🔴", "Reliability": "🟠", "Maintainability": "🟡", "VelocityDrag": "🔵"}
    for cat, stats in sorted(by_cat.items(), key=lambda x: x[1].get("total_exposure", 0), reverse=True)[:3]:
        cico  = cat_icons.get(cat, "⚪")
        cnt   = stats.get("count", 0)
        exp   = stats.get("total_exposure", 0.0)
        lines.append(_row(f"  {cico} {cat:<20} {cnt:>3} items  exp={exp:.1f}"))
    return lines

def _debt_summary():
    try:
        out, _ = _run_tool([TOOLS / "debt_ledger.py", "--json"], timeout=8)
        data = json.loads(out)
        total_h   = data.get("total_hours", 0)
        total_eur = data.get("total_cost", 0)
        items_cnt = data.get("items", 0)
        by_q      = data.get("by_quadrant", {})
        return total_h, total_eur, items_cnt, by_q
    except Exception:
        return 0, 0, 0, {}


def _production_score() -> float:
    """Reads artifact production score from artifact_counter.py output."""
    try:
        import re as _re, subprocess as _sp
        r = _sp.run(
            [sys.executable, str(TOOLS / "artifact_counter.py")],
            capture_output=True, text=True, timeout=10
        )
        m = _re.search(r"Score produc[^:]+:\s*([\d.]+)", r.stdout)
        return float(m.group(1)) if m else 0.0
    except Exception:
        return 0.0

def _velocity_data():
    """Lee velocity directo desde sesiones (sin subprocess)."""
    try:
        from datetime import timedelta
        sessions_dir = STATE / "sessions"
        closed = []
        for f in sessions_dir.glob("*.json"):
            try:
                d = json.loads(f.read_text())
                if d.get("status") == "closed":
                    closed.append(d)
            except Exception:
                pass
        if not closed:
            return {}
        # Sesiones por semana — últimas 4 semanas
        now = datetime.now(timezone.utc)
        weeks = []
        for w in range(4, 0, -1):
            w_start = now - timedelta(days=7 * w)
            w_end   = now - timedelta(days=7 * (w - 1))
            count = 0
            for d in closed:
                ts = d.get("closed_at") or d.get("created_at") or ""
                if ts:
                    try:
                        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                        if w_start <= dt < w_end:
                            count += 1
                    except Exception:
                        pass
            weeks.append(count)
        # Artefactos por sesión — últimas 10
        closed.sort(key=lambda d: d.get("created_at", ""), reverse=True)
        recent = closed[:10]
        arts   = [len(d.get("artifacts", [])) for d in recent][::-1]
        trend  = "↑" if len(arts) >= 2 and arts[-1] > arts[0] else ("↓" if len(arts) >= 2 and arts[-1] < arts[0] else "→")
        return {"artifacts_per_session": arts, "sessions_per_week": weeks, "trend": trend}
    except Exception:
        return {}

def _contracts():
    """Lee contratos desde state/contracts/ usando el campo 'met' de cada condición."""
    contracts_dir = STATE / "contracts"
    results = []
    for f in sorted(contracts_dir.glob("CONTRACT-*.json")):
        try:
            c = json.loads(f.read_text())
            cid   = c.get("contract_id", f.stem)
            conds = c.get("conditions", [])
            total = len(conds)
            met   = sum(1 for cond in conds if cond.get("met") is True)
            ddl   = c.get("deadline")
            status = "fulfilled" if met == total else "pending"
            results.append({
                "id": cid, "status": status,
                "conditions_met": met, "conditions_total": total,
                "deadline": ddl,
            })
        except Exception:
            pass
    return results

def _hotspots():
    try:
        out, _ = _run_tool([TOOLS / "hotspot.py", "--json", "--top", "3"], timeout=15)
        data = json.loads(out)
        # hotspot.py --json returns a list directly
        if isinstance(data, list):
            return data[:3]
        return data.get("hotspots", [])[:3]
    except Exception:
        return []

def _sprint():
    sdir = STATE / "sprints"
    open_s = []
    for f in sdir.glob("*.json"):
        try:
            d = json.loads(f.read_text())
            if d.get("status") == "open":
                open_s.append(d)
        except Exception:
            pass
    return open_s[-1] if open_s else None

def _last_session():
    gs = _load_global()
    sid = gs.get("last_completed_session_id", "—")
    wf  = gs.get("last_completed_workflow", "—")
    return sid, wf

# ─── secciones del dashboard ──────────────────────────────────────────────────

def section_header(gs):
    ver = gs.get("pack_version") or gs.get("bago_version", "?")
    val = _validate()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        _header(f"⚡ BAGO COCKPIT v2  —  {ver}"),
        _row(f"Pack: {val:<12}  Fecha: {now}"),
    ]
    return lines

def section_health():
    score, label = _health()
    bar  = _bar(score)
    ring = _ring(score)
    lines = [
        _header("── SALUD DEL SISTEMA ──"),
        _row(f"Score:  {ring}  [{bar}]"),
        _row(f"Estado: {label}"),
    ]
    return lines, score

def section_inventory():
    gs = _load_global()
    inv = gs.get("inventory", {})
    sessions  = inv.get("sessions", _count("sessions"))
    changes   = inv.get("changes", _count("changes"))
    evidences = inv.get("evidences", _count("evidences"))
    tools_dir = ROOT / "tools"
    tools_n   = len(list(tools_dir.glob("*.py")))
    return [
        _header("── INVENTARIO ──"),
        _row(f"Sesiones: {sessions:<6} Cambios: {changes:<6} Evidencias: {evidences}"),
        _row(f"Tools: {tools_n} .py  │  Sprints abiertos: {_count_open_sprints()}"),
    ]

def _count_open_sprints():
    return sum(1 for f in (STATE/"sprints").glob("*.json")
               if json.loads(f.read_text()).get("status") == "open")

def section_detector():
    verdict, score, thresh = _detector()
    icons = {"HARVEST": "🌾", "WATCH": "👁", "CLEAN": "✅"}
    icon  = icons.get(verdict, "?")
    bar   = _bar(score, maxv=thresh * 1.5 or 1, width=16)
    return [
        _header("── DETECTOR W9 ──"),
        _row(f"{icon} {verdict:<10} [{bar}]  {score}/{thresh} señales"),
    ]

def section_debt():
    total_h, total_eur, items_cnt, by_q = _debt_summary()
    lines = [
        _header("── DEUDA TÉCNICA ──"),
        _row(f"Coste estimado: {total_h:.1f} h/sem  │  Total: ~€{total_eur:.0f}"),
        _row(f"Ítems de deuda: {items_cnt}"),
    ]
    for q_name, q_data in list(by_q.items())[:2]:
        count = q_data.get("count", 0)
        hours = q_data.get("hours", 0)
        lines.append(_row(f"  · {q_name[:34]:<36} {count} ítem(s)  {hours:.1f}h"))
    return lines

def section_velocity():
    data = _velocity_data()
    if not data:
        return [_row("  (sin datos de velocidad — ejecuta bago velocity)")]
    sessions  = data.get("sessions_per_week", [])
    artifacts = data.get("artifacts_per_session", [])
    sp    = _sparkline(sessions)
    avg   = f"~{sum(sessions)/len(sessions):.1f}/sem" if sessions else "—"
    ap    = _sparkline(artifacts)
    trend = data.get("trend", "—")
    return [
        _header("── VELOCIDAD ──"),
        _row(f"Sesiones/sem:   {sp}  {avg}  (tendencia: {trend})"),
        _row(f"Artefactos/ses: {ap}"),
    ]

def section_contracts():
    contracts = _contracts()
    if not contracts:
        return [_row("  (sin contratos — ejecuta bago contract create)")]
    lines = [_header("── CONTRATOS ──")]
    now = datetime.now(timezone.utc)
    for c in contracts[:3]:
        cid    = c.get("id", "?")
        status = c.get("status", "?")
        cond   = c.get("conditions_met", 0)
        total  = c.get("conditions_total", 0)
        ddl    = c.get("deadline")
        if ddl:
            try:
                dl = datetime.fromisoformat(ddl.replace("Z", "+00:00"))
                delta = dl - now
                h = int(delta.total_seconds() // 3600)
                secs_left = f"{h}h restantes" if delta.total_seconds() > 0 else "VENCIDO"
            except Exception:
                secs_left = ddl[:16]
        else:
            secs_left = "sin deadline"
        ico = "✅" if status == "fulfilled" else ("⚠️" if cond == total else "🔲")
        lines.append(_row(f"{ico} {cid:<14} {cond}/{total} cond  {secs_left}"))
    return lines

def section_hotspots():
    spots = _hotspots()
    if not spots:
        return [_header("── HOTSPOTS ──"), _row("  🟢 Sin hotspots críticos detectados")]
    lines = [_header("── HOTSPOTS ──")]
    max_score = max(h.get("score", 1) for h in spots) or 1
    for h in spots:
        f = h.get("file", "?")
        score = h.get("score", 0)
        commits = h.get("commits", 0)
        loc = h.get("loc", 0)
        fname = Path(f).name[:30]
        bar = _bar(score, maxv=max_score, width=8)
        lines.append(_row(f"  🔥 {fname:<32} [{bar}] sc={score}  {commits}c/{loc}l"))
    return lines

def section_sprint():
    sp = _sprint()
    if not sp:
        return [_row("  (sin sprint activo)")]
    name  = sp.get("name", sp.get("sprint_id", "?"))[:40]
    goals = sp.get("goals", [])
    total = len(goals)
    # Count done goals (strings starting with "✅" or dicts with status=done)
    done  = sum(1 for g in goals if (isinstance(g, str) and g.startswith("✅"))
                                 or (isinstance(g, dict) and g.get("status") == "done"))
    pct   = int(done / total * 100) if total else 0
    bar   = _bar(done, maxv=total or 1, width=10)
    lines = [
        _header("── SPRINT ACTIVO ──"),
        _row(f"{name}"),
        _row(f"  Progreso: {done}/{total} goals  [{bar}]  {pct}%"),
    ]
    for g in goals[:3]:
        lines.append(_row(f"  · {str(g)[:52]}"))
    return lines

def section_last_session():
    sid, wf = _last_session()
    return [
        _header("── ÚLTIMA SESIÓN ──"),
        _row(f"ID: {sid}"),
        _row(f"Workflow: {wf}"),
    ]


def section_recent_chgs(n=5):
    """Muestra los N CHGs más recientes por fecha de creación."""
    chgs_dir = STATE / "changes"
    files = sorted(chgs_dir.glob("BAGO-CHG-*.json"), reverse=True)
    items = []
    for f in files:
        try:
            d = json.loads(f.read_text())
            items.append(d)
        except Exception:
            continue
        if len(items) >= n:
            break
    lines = [_header(f"── ÚLTIMOS {n} CAMBIOS (CHGs) ──")]
    if not items:
        lines.append(_row("  (sin cambios registrados)"))
        return lines
    for d in items:
        chg_id  = d.get("change_id", d.get("id", "?"))
        title   = d.get("title", "")[:42]
        sev     = d.get("severity", "")
        sev_tag = "🔴" if sev == "major" else "⚪"
        lines.append(_row(f"  {sev_tag} {chg_id}  {title}"))
    return lines


def section_tool_coverage():
    """Coverage por módulo: % de tools con al menos un test en integration_tests.py."""
    tests_file = TOOLS / "integration_tests.py"
    lines = [_header("── COBERTURA DE TESTS ──")]
    if not tests_file.exists():
        lines.append(_row("  (integration_tests.py no encontrado)"))
        return lines

    # Extract test key names from ALL_TESTS
    content = tests_file.read_text(encoding="utf-8", errors="ignore")
    all_tests_start = content.find("ALL_TESTS = [")
    test_names: set[str] = set()
    if all_tests_start != -1:
        import re as _re
        block = content[all_tests_start:]
        bracket_end = block.find("]")
        if bracket_end != -1:
            block = block[:bracket_end]
        for m in _re.finditer(r'\(\s*\d+\s*,\s*"([^"]+)"', block):
            # Normalize: remove : suffix (e.g. "scan:purge" → "scan")
            raw = m.group(1).split(":")[0].split("_")[0]
            test_names.add(m.group(1))  # full name for mapping
            test_names.add(raw)         # stem only

    # List all tool .py files
    all_tools = sorted(TOOLS.glob("*.py"))
    total = len(all_tools)
    covered = 0
    covered_names: list[str] = []
    uncovered_names: list[str] = []

    for tool_path in all_tools:
        stem = tool_path.stem  # e.g. "sprint_manager"
        # Check if any test name covers this tool
        matched = any(
            stem in name or name.split(":")[0] in stem or stem.startswith(name.split(":")[0])
            for name in test_names
        )
        if matched:
            covered += 1
            covered_names.append(stem)
        else:
            uncovered_names.append(stem)

    pct = int(covered * 100 / max(total, 1))
    bar = _bar(pct, 100, 16)
    lines.append(_row(f"  Tools cubiertos: {covered}/{total}  [{bar}]  {pct}%"))

    # Show up to 5 uncovered tools as hints
    if uncovered_names:
        sample = uncovered_names[:5]
        hint = ", ".join(sample)
        if len(uncovered_names) > 5:
            hint += f" +{len(uncovered_names) - 5} más"
        lines.append(_row(f"  Sin test: {hint}"))
    else:
        lines.append(_row("  ✅ Todos los tools tienen cobertura"))

    return lines

# ─── render principal ─────────────────────────────────────────────────────────

def render(full=False, compact=False, as_json=False):
    gs = _load_global()

    health_lines, score = section_health()
    inv_lines = section_inventory()
    det_lines = section_detector()
    risks_lines = section_risks()
    debt_lines  = section_debt()
    vel_lines   = section_velocity()
    cont_lines  = section_contracts()
    hot_lines   = section_hotspots()
    sprint_lines = section_sprint()
    sess_lines  = section_last_session()
    chgs_lines  = section_recent_chgs()
    cov_lines   = section_tool_coverage()

    if as_json:
        # Machine-readable summary
        data = {
            "health_score": score,
            "production_score": _production_score(),
            "validate": _validate(),
            "detector": _detector()[0],
            "inventory": {
                "sessions": _count("sessions"),
                "changes":  _count("changes"),
                "evidences":_count("evidences"),
            },
            "top_risks": {"by_category": _top_risks()[0], "exposure": _top_risks()[1], "items": _top_risks()[2]},
            "debt_cost_per_hour": _debt_summary()[0],
            "contracts": _contracts(),
            "sprint": _sprint(),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        print(json.dumps(data, indent=2, ensure_ascii=False, default=str))
        return

    out = [_top()]
    out += section_header(gs)
    out.append(_divider())
    out += health_lines
    out.append(_divider())
    out += inv_lines

    if not compact:
        out.append(_divider())
        out += det_lines
        out.append(_divider())
        out += sprint_lines

    if full or not compact:
        out.append(_divider())
        out += risks_lines
        out.append(_divider())
        out += debt_lines
        out.append(_divider())
        out += vel_lines
        out.append(_divider())
        out += cont_lines

    if full:
        out.append(_divider())
        out += hot_lines

    out.append(_divider())
    out += sess_lines
    out.append(_divider())
    out += chgs_lines
    out.append(_divider())
    out += cov_lines
    out.append(_bottom())

    print("\n".join(out))


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="BAGO Cockpit Dashboard v2")
    p.add_argument("--full",    action="store_true", help="Muestra hotspots y secciones extra")
    p.add_argument("--compact", action="store_true", help="Solo salud + inventario")
    p.add_argument("--json",    action="store_true", help="Salida JSON machine-readable")
    args = p.parse_args()
    render(full=args.full, compact=args.compact, as_json=args.json)
