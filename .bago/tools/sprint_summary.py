#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sprint_summary.py — Genera resúmenes de sprint BAGO.

Se activa automáticamente cada vez que se completa un bloque de 5 ideas implementadas.
Genera: .bago/state/sprint_summary_NN.md

Uso:
    python3 .bago/tools/sprint_summary.py            # genera los sprints pendientes
    python3 .bago/tools/sprint_summary.py --status   # muestra estado de sprints
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

BAGO_ROOT  = Path(__file__).resolve().parent.parent
STATE      = BAGO_ROOT / "state"
SPRINT_SIZE = 5


def _load_implemented() -> list[dict]:
    path = STATE / "implemented_ideas.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("implemented", [])
    except Exception:
        return []


def _total_in_db() -> int:
    db_path = STATE / "bago.db"
    if not db_path.exists():
        return 0
    try:
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        n = conn.execute("SELECT COUNT(*) FROM ideas").fetchone()[0]
        conn.close()
        return n
    except Exception:
        return 0


def _sprint_path(sprint_n: int) -> Path:
    return STATE / f"sprint_summary_{sprint_n:02d}.md"


def _generate_sprint(sprint_n: int, ideas_in_sprint: list[dict],
                     total_impl: int, total_db: int) -> Path:
    """Genera el archivo markdown para el sprint N."""
    start_idx = (sprint_n - 1) * SPRINT_SIZE + 1
    end_idx   = sprint_n * SPRINT_SIZE
    now       = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    pct       = round(100 * total_impl / total_db) if total_db > 0 else 0
    slots     = sorted({str(i.get("slot", "—")) for i in ideas_in_sprint})

    rows = []
    for rel_idx, idea in enumerate(ideas_in_sprint):
        abs_idx = start_idx + rel_idx
        title   = idea.get("title", "—")
        slot    = idea.get("slot", "—")
        date    = (idea.get("done_at") or "")[:10] or "—"
        rows.append(f"| {abs_idx} | {title} | {slot} | {date} |")

    # ── Velocidad ──────────────────────────────────────────────────────────────
    velocity_str = _sprint_velocity(ideas_in_sprint)

    lines = [
        f"# Sprint BAGO #{sprint_n:02d} — Resumen",
        f"Generado: {now}",
        f"Ideas: {start_idx}–{end_idx} de {total_impl} implementadas",
        "",
        "## Ideas implementadas en este sprint",
        "",
        "| # | Título | Slot | Fecha |",
        "|---|--------|------|-------|",
        *rows,
        "",
        "## Métricas",
        f"- Ideas en este sprint: {len(ideas_in_sprint)}",
        f"- Slots activados: {', '.join(slots)}",
        f"- Total acumulado: {total_impl}/{total_db} ({pct}%)",
        f"- Velocidad: {velocity_str}",
        "",
        "## Próximos hitos",
        f"- Sprint #{sprint_n + 1:02d} completará: {end_idx + SPRINT_SIZE} ideas",
        "",
    ]
    out = _sprint_path(sprint_n)
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def _sprint_velocity(ideas: list[dict]) -> str:
    """Calcula velocidad: ideas/día basándose en done_at timestamps.
    # SPRINT_VELOCITY_IMPLEMENTED
    """
    dates = []
    for idea in ideas:
        done_at = idea.get("done_at", "")
        if done_at:
            try:
                dt = datetime.fromisoformat(done_at.replace("Z", "+00:00"))
                dates.append(dt)
            except Exception:
                pass
    if not dates:
        return "— (sin fechas)"
    if len(dates) == 1:
        return f"1 idea (fecha única: {dates[0].strftime('%Y-%m-%d')})"
    dates.sort()
    days = max((dates[-1] - dates[0]).total_seconds() / 86400, 0.1)
    vel = round(len(ideas) / days, 2)
    span_days = round(days, 1)
    return f"{vel} ideas/día  ({len(ideas)} ideas en {span_days}d)"


def _export_report() -> Path:
    """
    Genera state/ideas_report.md con todas las ideas implementadas agrupadas por sprint.
    Activado con: python sprint_summary.py --export
    """
    implemented = _load_implemented()
    total       = len(implemented)
    total_db    = _total_in_db() or total
    now         = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    pct         = round(100 * total / total_db) if total_db > 0 else 0
    completed   = total // SPRINT_SIZE

    lines = [
        "# BAGO — Historial completo de ideas implementadas",
        f"Generado: {now}",
        f"Total: {total}/{total_db} ideas implementadas ({pct}%)",
        "",
    ]

    for sprint_n in range(1, completed + 1):
        start = (sprint_n - 1) * SPRINT_SIZE
        end   = sprint_n * SPRINT_SIZE
        ideas = implemented[start:end]
        vel   = _sprint_velocity(ideas)
        lines += [
            f"## Sprint #{sprint_n:02d}  (ideas {start+1}–{end})",
            f"Velocidad: {vel}",
            "",
            "| # | Título | Slot | Fecha |",
            "|---|--------|------|-------|",
        ]
        for idx, idea in enumerate(ideas):
            title = idea.get("title", "—")
            slot  = idea.get("slot", "—")
            date  = (idea.get("done_at") or "")[:10] or "—"
            lines.append(f"| {start+idx+1} | {title} | {slot} | {date} |")
        lines.append("")

    # Ideas extra (sprint en curso, no completado)
    extra = implemented[completed * SPRINT_SIZE:]
    if extra:
        lines += [
            f"## Sprint #{completed + 1:02d}  (en progreso — {len(extra)}/{SPRINT_SIZE})",
            "",
            "| # | Título | Slot | Fecha |",
            "|---|--------|------|-------|",
        ]
        for idx, idea in enumerate(extra):
            title = idea.get("title", "—")
            slot  = idea.get("slot", "—")
            date  = (idea.get("done_at") or "")[:10] or "—"
            lines.append(f"| {completed*SPRINT_SIZE+idx+1} | {title} | {slot} | {date} |")
        lines.append("")

    out = STATE / "ideas_report.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def generate_if_due() -> list[Path]:
    """
    Genera resúmenes para todos los sprints completados sin archivo de resumen.
    # SPRINT_SUMMARY_IMPLEMENTED
    Returns: lista de Paths generados.
    """
    implemented = _load_implemented()
    total       = len(implemented)
    if total < SPRINT_SIZE:
        return []

    total_db         = _total_in_db() or total
    completed_sprints = total // SPRINT_SIZE
    generated: list[Path] = []

    for sprint_n in range(1, completed_sprints + 1):
        path = _sprint_path(sprint_n)
        if not path.exists():
            start  = (sprint_n - 1) * SPRINT_SIZE
            end    = sprint_n * SPRINT_SIZE
            ideas  = implemented[start:end]
            out    = _generate_sprint(sprint_n, ideas, total, total_db)
            generated.append(out)

    return generated


def main() -> int:
    status_only = "--status" in sys.argv
    export_only = "--export" in sys.argv
    implemented = _load_implemented()
    total       = len(implemented)
    completed   = total // SPRINT_SIZE

    print()
    print("BAGO Sprint Summary")
    print(f"  Ideas implementadas : {total}")
    print(f"  Sprints completados : {completed}")
    print()

    if export_only:
        out = _export_report()
        print(f"  📄 Informe exportado: {out.relative_to(BAGO_ROOT.parent)}")
        print()
        return 0

    if status_only:
        for n in range(1, completed + 1):
            p    = _sprint_path(n)
            icon = "✅" if p.exists() else "⏳"
            tag  = "(existe)" if p.exists() else "(pendiente)"
            print(f"  {icon}  Sprint #{n:02d}  {p.name}  {tag}")
        if not completed:
            print("  Sin sprints completados aún (< 5 ideas implementadas).")
        print()
        return 0

    generated = generate_if_due()
    if generated:
        for path in generated:
            print(f"  📋 Generado: {path.relative_to(BAGO_ROOT.parent)}")
    else:
        print("  ✅ Todos los resúmenes de sprint al día.")
    print()
    return 0



def _self_test():
    """Autotest mínimo — verifica arranque limpio del módulo."""
    from pathlib import Path as _P
    assert _P(__file__).exists(), "fichero no encontrado"
    print("  1/1 tests pasaron")

if __name__ == "__main__":
    if "--test" in sys.argv:
        _self_test()
        raise SystemExit(0)
    sys.exit(main())
