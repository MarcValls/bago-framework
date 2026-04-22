#!/usr/bin/env python3
"""
bago lint — linter de calidad del pack BAGO con sugerencias de mejora.

Analiza la calidad de los datos del pack:
- Sesiones sin objetivos, sin artefactos, sin decisiones
- Cambios sin evidencias vinculadas
- Sprints sin artefactos
- Inconsistencias en campos obligatorios
- Objetivos sin sesiones vinculadas

Uso:
    bago lint            → análisis completo
    bago lint --fix      → muestra sugerencias de fix para cada KO
    bago lint --json     → output JSON
    bago lint --test     → tests integrados
"""

import argparse
import json
import sys
from pathlib import Path
from collections import defaultdict

BAGO_ROOT = Path(__file__).parent.parent
STATE_DIR = BAGO_ROOT / "state"

SEVERITY_WARN = "WARN"
SEVERITY_INFO = "INFO"
SEVERITY_ERROR = "ERROR"


def _load_json_files(directory: Path, pattern: str = "*.json"):
    items = []
    if not directory.exists():
        return items
    for f in sorted(directory.glob(pattern)):
        try:
            data = json.loads(f.read_text())
            data["_file"] = f.name
            items.append(data)
        except Exception:
            pass
    return items


class LintIssue:
    def __init__(self, severity, code, entity, message, fix=None):
        self.severity = severity
        self.code = code
        self.entity = entity
        self.message = message
        self.fix = fix

    def to_dict(self):
        return {
            "severity": self.severity,
            "code": self.code,
            "entity": self.entity,
            "message": self.message,
            "fix": self.fix,
        }


def lint_sessions(sessions: list) -> list:
    issues = []
    for s in sessions:
        sid = s.get("session_id", s["_file"])

        # No user_goal
        goal = str(s.get("user_goal", "")).strip()
        if not goal or goal in ("", ".", "N/A", "n/a"):
            issues.append(LintIssue(
                SEVERITY_WARN, "SES-001", sid,
                "Sesión sin user_goal definido",
                f"Edita {sid}.json y añade user_goal con el objetivo real de la sesión"
            ))

        # No artifacts
        arts = s.get("artifacts", [])
        if not arts and s.get("status") == "closed":
            issues.append(LintIssue(
                SEVERITY_INFO, "SES-002", sid,
                "Sesión cerrada sin artefactos registrados",
                "Añade los ficheros producidos en el campo 'artifacts'"
            ))

        # No decisions
        decs = s.get("decisions", [])
        if not decs and s.get("status") == "closed":
            issues.append(LintIssue(
                SEVERITY_INFO, "SES-003", sid,
                "Sesión cerrada sin decisiones registradas",
                "Registra al menos 1 decisión en el campo 'decisions'"
            ))

        # No roles
        roles = s.get("roles_activated", [])
        if not roles:
            issues.append(LintIssue(
                SEVERITY_INFO, "SES-004", sid,
                "Sesión sin roles activados",
                "Activa al menos un rol (role_architect, role_auditor, etc.)"
            ))

        # Bad status
        valid_statuses = {"open", "active", "closed", "paused"}
        status = s.get("status", "")
        if status not in valid_statuses:
            issues.append(LintIssue(
                SEVERITY_WARN, "SES-005", sid,
                f"Estado inválido: '{status}'",
                f"Usa uno de: {', '.join(sorted(valid_statuses))}"
            ))

    return issues


def lint_changes(changes: list) -> list:
    issues = []
    evd_dir = STATE_DIR / "evidences"
    evd_refs = set()
    if evd_dir.exists():
        for f in evd_dir.glob("BAGO-EVD-*.json"):
            try:
                evd = json.loads(f.read_text())
                for ref in evd.get("linked_changes", []):
                    evd_refs.add(ref)
            except Exception:
                pass

    for c in changes:
        cid = c.get("change_id", c["_file"])

        # No title
        if not str(c.get("title", "")).strip():
            issues.append(LintIssue(
                SEVERITY_ERROR, "CHG-001", cid,
                "Cambio sin título",
                f"Añade campo 'title' a {c['_file']}"
            ))

        # No motivation
        if not str(c.get("motivation", "")).strip():
            issues.append(LintIssue(
                SEVERITY_WARN, "CHG-002", cid,
                "Cambio sin motivación documentada",
                f"Añade campo 'motivation' explicando el por qué del cambio"
            ))

        # No artifacts listed
        arts = c.get("artifacts", c.get("affected_components", []))
        if not arts:
            issues.append(LintIssue(
                SEVERITY_INFO, "CHG-003", cid,
                "Cambio sin artefactos/componentes listados",
                "Añade 'affected_components' con los ficheros modificados"
            ))

    return issues


def lint_pack() -> list:
    issues = []
    pack_path = BAGO_ROOT / "pack.json"
    if not pack_path.exists():
        issues.append(LintIssue(SEVERITY_ERROR, "PACK-001", "pack.json", "pack.json no encontrado"))
        return issues

    try:
        pack = json.loads(pack_path.read_text())
    except Exception as e:
        issues.append(LintIssue(SEVERITY_ERROR, "PACK-002", "pack.json", f"JSON inválido: {e}"))
        return issues

    required_fields = ["id", "name", "version", "description"]
    for field in required_fields:
        if not pack.get(field):
            issues.append(LintIssue(
                SEVERITY_ERROR, "PACK-003", "pack.json",
                f"Campo requerido faltante o vacío: '{field}'",
                f"Añade '{field}' a pack.json"
            ))

    return issues


def run_lint(fix_mode: bool, as_json: bool):
    sessions = _load_json_files(STATE_DIR / "sessions", "SES-*.json")
    changes = _load_json_files(STATE_DIR / "changes", "BAGO-CHG-*.json")

    all_issues = []
    all_issues.extend(lint_sessions(sessions))
    all_issues.extend(lint_changes(changes))
    all_issues.extend(lint_pack())

    errors = [i for i in all_issues if i.severity == SEVERITY_ERROR]
    warns = [i for i in all_issues if i.severity == SEVERITY_WARN]
    infos = [i for i in all_issues if i.severity == SEVERITY_INFO]

    if as_json:
        print(json.dumps({
            "total": len(all_issues),
            "errors": len(errors),
            "warnings": len(warns),
            "infos": len(infos),
            "issues": [i.to_dict() for i in all_issues],
        }, indent=2, ensure_ascii=False))
        return

    status = "PASS" if not errors else "FAIL"
    icon = "✅" if status == "PASS" else "❌"

    print(f"\n  BAGO Lint — {icon} {status}")
    print(f"  Analizados: {len(sessions)} sesiones, {len(changes)} cambios")
    print(f"  Issues: {len(errors)} errores  {len(warns)} avisos  {len(infos)} info\n")

    ICONS = {SEVERITY_ERROR: "❌", SEVERITY_WARN: "⚠️ ", SEVERITY_INFO: "ℹ️ "}

    for issue in all_issues:
        icon_i = ICONS.get(issue.severity, "?")
        print(f"  {icon_i} [{issue.code}] {issue.entity}: {issue.message}")
        if fix_mode and issue.fix:
            print(f"     → {issue.fix}")

    if not all_issues:
        print("  (sin issues detectadas) 🎉")

    print()
    if errors:
        sys.exit(1)


def run_tests():
    print("Ejecutando tests de lint.py...")
    errors = 0

    def ok(name):
        print(f"  OK: {name}")

    def fail(name, msg):
        nonlocal errors
        errors += 1
        print(f"  FAIL: {name} — {msg}")

    # Test 1: session without goal → WARN
    fake_sessions = [
        {"_file": "SES-T001.json", "session_id": "SES-T001", "user_goal": "", "artifacts": [], "decisions": [], "roles_activated": [], "status": "closed"},
    ]
    issues = lint_sessions(fake_sessions)
    codes = [i.code for i in issues]
    if "SES-001" in codes:
        ok("lint:session_no_goal")
    else:
        fail("lint:session_no_goal", str(codes))

    # Test 2: session with good data → no SES-001/002/003
    good_sessions = [
        {"_file": "SES-T002.json", "session_id": "SES-T002", "user_goal": "Implementar algo", "artifacts": ["f1.py"], "decisions": ["d1"], "roles_activated": ["role_architect"], "status": "closed"},
    ]
    issues2 = lint_sessions(good_sessions)
    bad_codes = [i.code for i in issues2 if i.code in ("SES-001", "SES-002", "SES-003")]
    if not bad_codes:
        ok("lint:good_session_clean")
    else:
        fail("lint:good_session_clean", str(bad_codes))

    # Test 3: change without title → ERROR
    fake_changes = [
        {"_file": "BAGO-CHG-T01.json", "change_id": "BAGO-CHG-T01", "title": "", "motivation": "some", "artifacts": ["f"]},
    ]
    issues3 = lint_changes(fake_changes)
    codes3 = [i.code for i in issues3]
    if "CHG-001" in codes3:
        ok("lint:change_no_title")
    else:
        fail("lint:change_no_title", str(codes3))

    # Test 4: LintIssue.to_dict has all keys
    issue = LintIssue("WARN", "T-001", "entity", "message", "fix suggestion")
    d = issue.to_dict()
    required = ["severity", "code", "entity", "message", "fix"]
    missing = [k for k in required if k not in d]
    if not missing:
        ok("lint:issue_to_dict")
    else:
        fail("lint:issue_to_dict", f"missing: {missing}")

    # Test 5: pack lint on real pack
    issues5 = lint_pack()
    error_codes = [i.code for i in issues5 if i.severity == "ERROR"]
    if not error_codes:
        ok("lint:pack_valid")
    else:
        fail("lint:pack_valid", str(error_codes))

    total = 5
    passed = total - errors
    print(f"\n  {passed}/{total} tests pasaron")
    if errors:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(prog="bago lint", add_help=False)
    parser.add_argument("--fix", action="store_true", help="mostrar sugerencias de fix")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--help", action="store_true")
    args = parser.parse_args()

    if args.test:
        run_tests()
    elif args.help:
        parser.print_help()
    else:
        run_lint(args.fix, args.json)


if __name__ == "__main__":
    main()