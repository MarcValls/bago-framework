#!/usr/bin/env python3
"""
bago summary — genera un resumen ejecutivo Markdown de una sesion o sprint.

Listo para copiar en documentacion, PR descriptions, notas de reunion.

Uso:
    bago summary session SES-ID     → resumen de una sesion
    bago summary sprint SPRINT-001  → resumen de un sprint
    bago summary last               → resumen de la ultima sesion
    bago summary sprint last        → resumen del sprint mas reciente
    bago summary --out FILE         → guarda a fichero
    bago summary --test             → tests integrados
"""

import argparse
import json
import sys
import datetime
from pathlib import Path

BAGO_ROOT = Path(__file__).parent.parent
SESSIONS_DIR = BAGO_ROOT / "state" / "sessions"
SPRINTS_DIR = BAGO_ROOT / "state" / "sprints"


def _load_session(sid: str) -> dict:
    if sid == "last":
        sessions = sorted(SESSIONS_DIR.glob("SES-*.json"))
        if not sessions:
            print("  ERROR: no hay sesiones")
            raise SystemExit(1)
        return json.loads(sessions[-1].read_text())

    # Try exact match
    p = SESSIONS_DIR / f"{sid}.json"
    if p.exists():
        return json.loads(p.read_text())

    # Try prefix match
    matches = list(SESSIONS_DIR.glob(f"{sid}*.json"))
    if matches:
        return json.loads(matches[0].read_text())

    print(f"  ERROR: sesión no encontrada: {sid}")
    raise SystemExit(1)


def _load_sprint(sprint_id: str) -> dict:
    if sprint_id == "last":
        sprints = sorted(SPRINTS_DIR.glob("SPRINT-*.json"))
        if not sprints:
            print("  ERROR: no hay sprints")
            raise SystemExit(1)
        return json.loads(sprints[-1].read_text())

    p = SPRINTS_DIR / f"{sprint_id}.json"
    if not p.exists():
        matches = list(SPRINTS_DIR.glob(f"{sprint_id}*.json"))
        if matches:
            p = matches[0]
        else:
            print(f"  ERROR: sprint no encontrado: {sprint_id}")
            raise SystemExit(1)
    return json.loads(p.read_text())


def _session_summary_md(s: dict) -> str:
    sid = s.get("session_id", "?")
    wf = s.get("selected_workflow", "?")
    goal = str(s.get("user_goal", "")).strip() or "(no especificado)"
    status = s.get("status", "?")
    created = str(s.get("created_at", ""))[:19]
    mode = s.get("bago_mode", "?")
    roles = s.get("roles_activated", [])
    arts = s.get("artifacts", [])
    decs = s.get("decisions", [])
    bugs = s.get("bugs_found", [])
    summary_text = str(s.get("summary", "")).strip()

    lines = []
    lines.append(f"## Sesión: `{sid}`")
    lines.append("")
    lines.append(f"| Campo | Valor |")
    lines.append(f"|-------|-------|")
    lines.append(f"| Workflow | `{wf}` |")
    lines.append(f"| Estado | {status} |")
    lines.append(f"| Modo BAGO | {mode} |")
    lines.append(f"| Creada | {created} |")
    lines.append(f"| Roles | {', '.join(roles) if roles else '(ninguno)'} |")
    lines.append("")
    lines.append(f"### Objetivo")
    lines.append(f"> {goal}")
    lines.append("")

    if arts:
        lines.append(f"### Artefactos ({len(arts)})")
        for a in arts:
            lines.append(f"- `{a}`")
        lines.append("")

    if decs:
        lines.append(f"### Decisiones ({len(decs)})")
        for i, d in enumerate(decs, 1):
            lines.append(f"{i}. {d}")
        lines.append("")

    if bugs:
        lines.append(f"### Bugs encontrados ({len(bugs)})")
        for b in bugs:
            lines.append(f"- ⚠️ {b}")
        lines.append("")

    if summary_text:
        lines.append(f"### Resumen")
        lines.append(summary_text)
        lines.append("")

    return "\n".join(lines)


def _sprint_summary_md(sp: dict) -> str:
    sprint_id = sp.get("sprint_id", "?")
    name = sp.get("name", "?")
    status = sp.get("status", "?")
    created = str(sp.get("created_at", ""))[:19]
    closed = str(sp.get("closed_at", "")).strip()
    arts = sp.get("artifacts", [])
    sessions = sp.get("sessions", [])
    summary_text = str(sp.get("summary", "")).strip()

    lines = []
    lines.append(f"## Sprint: `{sprint_id}` — {name}")
    lines.append("")
    lines.append(f"| Campo | Valor |")
    lines.append(f"|-------|-------|")
    lines.append(f"| Estado | {status} |")
    lines.append(f"| Creado | {created} |")
    if closed:
        lines.append(f"| Cerrado | {closed[:19]} |")
    lines.append(f"| Sesiones | {len(sessions)} |")
    lines.append(f"| Artefactos | {len(arts)} |")
    lines.append("")

    if sessions:
        lines.append(f"### Sesiones vinculadas ({len(sessions)})")
        for s in sessions:
            lines.append(f"- `{s}`")
        lines.append("")

    if arts:
        lines.append(f"### Artefactos ({len(arts)})")
        for a in arts:
            lines.append(f"- `{a}`")
        lines.append("")

    if summary_text:
        lines.append(f"### Notas")
        lines.append(summary_text)
        lines.append("")

    return "\n".join(lines)


def run_tests():
    print("Ejecutando tests de summary.py...")
    errors = 0

    def ok(name):
        print(f"  OK: {name}")

    def fail(name, msg):
        nonlocal errors
        errors += 1
        print(f"  FAIL: {name} — {msg}")

    # Test 1: session summary contains key sections
    fake_session = {
        "session_id": "SES-T001",
        "selected_workflow": "w2_impl",
        "user_goal": "Implementar feature X",
        "status": "closed",
        "created_at": "2026-04-21T12:00:00",
        "bago_mode": "on",
        "roles_activated": ["role_architect"],
        "artifacts": ["src/feature.py"],
        "decisions": ["Usar factory pattern"],
        "bugs_found": [],
        "summary": "Sesión productiva.",
    }
    md = _session_summary_md(fake_session)
    if "SES-T001" in md and "Artefactos" in md and "Decisiones" in md:
        ok("summary:session_md_sections")
    else:
        fail("summary:session_md_sections", md[:200])

    # Test 2: session with no artifacts/decisions still renders
    minimal = {
        "session_id": "SES-T002",
        "selected_workflow": "w9",
        "user_goal": "",
        "status": "open",
        "created_at": "2026-04-21",
        "bago_mode": "on",
        "roles_activated": [],
        "artifacts": [],
        "decisions": [],
        "bugs_found": [],
    }
    md2 = _session_summary_md(minimal)
    if "SES-T002" in md2 and "no especificado" in md2:
        ok("summary:session_minimal")
    else:
        fail("summary:session_minimal", md2[:200])

    # Test 3: sprint summary renders
    fake_sprint = {
        "sprint_id": "SPRINT-T01",
        "name": "Test Sprint",
        "status": "closed",
        "created_at": "2026-04-21",
        "closed_at": "2026-04-21",
        "sessions": ["SES-T001"],
        "artifacts": ["tools/test.py"],
        "summary": "Sprint de prueba.",
    }
    md3 = _sprint_summary_md(fake_sprint)
    if "SPRINT-T01" in md3 and "Artefactos" in md3 and "tools/test.py" in md3:
        ok("summary:sprint_md")
    else:
        fail("summary:sprint_md", md3[:200])

    # Test 4: load last session works
    try:
        s = _load_session("last")
        if s.get("session_id"):
            ok("summary:load_last_session")
        else:
            fail("summary:load_last_session", "no session_id")
    except SystemExit as e:
        fail("summary:load_last_session", f"raise SystemExit({e})")

    # Test 5: load last sprint works
    try:
        sp = _load_sprint("last")
        if sp.get("sprint_id"):
            ok("summary:load_last_sprint")
        else:
            fail("summary:load_last_sprint", "no sprint_id")
    except SystemExit as e:
        fail("summary:load_last_sprint", f"raise SystemExit({e})")

    total = 5
    passed = total - errors
    print(f"\n  {passed}/{total} tests pasaron")
    if errors:
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(prog="bago summary", add_help=False)
    parser.add_argument("entity", nargs="?", default=None, help="session|sprint|last")
    parser.add_argument("id", nargs="?", default=None, help="ID o 'last'")
    parser.add_argument("--out", default=None)
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--help", action="store_true")
    args = parser.parse_args()

    if args.test:
        run_tests()
        return

    if args.help:
        parser.print_help()
        return

    entity = args.entity
    eid = args.id

    if entity == "last" and eid is None:
        # bago summary last → session last
        md = _session_summary_md(_load_session("last"))
    elif entity == "session":
        sid = eid or "last"
        md = _session_summary_md(_load_session(sid))
    elif entity == "sprint":
        sid = eid or "last"
        md = _sprint_summary_md(_load_sprint(sid))
    elif entity is None:
        # default: last session
        md = _session_summary_md(_load_session("last"))
    else:
        # Treat entity as session ID
        md = _session_summary_md(_load_session(entity))

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(md)
        size_kb = out_path.stat().st_size / 1024
        print(f"  Resumen guardado en: {out_path} ({size_kb:.1f} KB)")
    else:
        print(md)


if __name__ == "__main__":
    main()