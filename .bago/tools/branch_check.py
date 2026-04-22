#!/usr/bin/env python3
"""branch_check.py — Herramienta #103: Validador de nombres de rama git.

Verifica que el nombre de la rama actual (o la indicada) cumpla las
convenciones de nomenclatura configuradas. Soporte para múltiples estilos
predefinidos o patrón personalizado.

Estilos predefinidos:
  gitflow   → feature/*, bugfix/*, hotfix/*, release/*, develop, main, master
  simple    → feat/*, fix/*, docs/*, chore/*, refactor/*, test/*
  jira      → PROJ-NNNN/*, PROJ-NNNN
  numeric   → task/NNN, issue/NNN, sprint/NNN-*
  bago      → S[0-9]+/*, W[0-9]+/*, bago-*, main, master, develop

Uso:
    bago branch-check [BRANCH] [--style STYLE] [--pattern REGEX]
                      [--ci] [--json] [--test]

Opciones:
    BRANCH      Nombre de rama (default: rama actual via git)
    --style     Estilo predefinido (gitflow|simple|jira|numeric|bago)
    --pattern   Regex personalizado (sobreescribe --style)
    --ci        Exit 1 si la rama no es válida (sin output extra)
    --json      Output en JSON
    --test      Self-tests
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

_RED  = "\033[0;31m"
_GRN  = "\033[0;32m"
_YEL  = "\033[0;33m"
_RST  = "\033[0m"
_BOLD = "\033[1m"

# Estilos predefinidos con sus patrones y ejemplos válidos/inválidos
STYLES: dict[str, dict] = {
    "gitflow": {
        "pattern": r'^(feature|bugfix|hotfix|release)/[\w\-\.]+$|^(develop|main|master|HEAD)$',
        "examples_ok":  ["feature/user-auth", "bugfix/fix-login", "hotfix/sec-patch", "release/2.5", "main"],
        "examples_bad": ["Feature/auth", "my-feature", "user_auth", "wip"],
        "description":  "Git Flow estándar",
    },
    "simple": {
        "pattern": r'^(feat|fix|docs|chore|refactor|test|perf|ci|style|revert)/[\w\-\.]+$|^(main|master|develop|HEAD)$',
        "examples_ok":  ["feat/add-login", "fix/null-ptr", "docs/readme", "chore/deps", "main"],
        "examples_bad": ["feature/auth", "Feature/auth", "my-feature"],
        "description":  "Conventional commits style",
    },
    "jira": {
        "pattern": r'^[A-Z][A-Z0-9]+-\d+(/[\w\-\.]+)?$|^(main|master|develop|HEAD)$',
        "examples_ok":  ["PROJ-123", "BAGO-456/add-feature", "MYAPP-1001", "main"],
        "examples_bad": ["proj-123", "jira/PROJ-123", "feature/auth"],
        "description":  "Jira ticket style (PROJ-NNN)",
    },
    "numeric": {
        "pattern": r'^(task|issue|sprint|ticket)/\d+(-[\w\-\.]+)?$|^(main|master|develop|HEAD)$',
        "examples_ok":  ["task/42", "issue/123-fix-login", "sprint/7-auth", "main"],
        "examples_bad": ["feature/auth", "task-42", "42/fix"],
        "description":  "Numeric ticket style",
    },
    "bago": {
        "pattern": r'^(S\d+|W\d+)/[\w\-\.]+$|^bago-[\w\-\.]+$|^(main|master|develop|HEAD)$',
        "examples_ok":  ["S7/git-context", "W3/sprint-manager", "bago-hotfix", "main"],
        "examples_bad": ["feature/auth", "sprint/7", "bago_hotfix"],
        "description":  "BAGO Framework style (S7/*, W3/*, bago-*)",
    },
}


def get_current_branch(cwd: str = ".") -> Optional[str]:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=10, cwd=cwd
        )
        return r.stdout.strip() or None
    except Exception:
        return None


def validate_branch(name: str, pattern: str) -> tuple[bool, str]:
    """Valida el nombre de rama contra el patrón. Devuelve (ok, reason)."""
    if not name:
        return False, "Nombre de rama vacío"
    try:
        if re.match(pattern, name):
            return True, "Nombre de rama válido"
        return False, f"No coincide con el patrón: {pattern}"
    except re.error as e:
        return False, f"Patrón regex inválido: {e}"


def _suggest_fix(name: str, style: str) -> str:
    """Sugiere un nombre válido basado en el estilo."""
    # Limpiar el nombre base
    clean = re.sub(r'[^a-zA-Z0-9\-]', '-', name.lower()).strip('-')
    sug_map = {
        "gitflow": f"feature/{clean}",
        "simple":  f"feat/{clean}",
        "bago":    f"S1/{clean}",
        "jira":    f"PROJ-001/{clean}",
        "numeric": f"task/1-{clean}",
    }
    return sug_map.get(style, f"fix/{clean}")


# ─── CLI ───────────────────────────────────────────────────────────────────

def main(argv: list[str]) -> int:
    branch  = None
    style   = "gitflow"
    pattern = None
    ci_mode = False
    as_json = False
    cwd     = "."

    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--style" and i + 1 < len(argv):
            style = argv[i + 1]; i += 2
        elif a == "--pattern" and i + 1 < len(argv):
            pattern = argv[i + 1]; i += 2
        elif a == "--ci":
            ci_mode = True; i += 1
        elif a == "--json":
            as_json = True; i += 1
        elif not a.startswith("--"):
            branch = a; i += 1
        else:
            i += 1

    if not branch:
        branch = get_current_branch(cwd)
    if not branch:
        if not ci_mode:
            print(f"{_YEL}⚠️  No se pudo obtener la rama actual{_RST}")
        return 1

    # Determinar patrón
    if not pattern:
        style_data = STYLES.get(style, STYLES["gitflow"])
        pattern = style_data["pattern"]
        style_desc = style_data["description"]
    else:
        style_desc = "personalizado"

    ok, reason = validate_branch(branch, pattern)
    suggestion = "" if ok else _suggest_fix(branch, style)

    if as_json:
        print(json.dumps({
            "branch": branch, "valid": ok, "reason": reason,
            "style": style, "pattern": pattern,
            "suggestion": suggestion if not ok else None,
        }, indent=2))
        return 0 if ok else 1

    if ci_mode:
        return 0 if ok else 1

    if ok:
        print(f"{_GRN}✅ Rama válida:{_RST} '{branch}'")
        print(f"   Estilo: {style} ({style_desc})")
    else:
        print(f"{_RED}❌ Rama inválida:{_RST} '{branch}'")
        print(f"   Motivo:     {reason}")
        print(f"   Estilo:     {style} ({style_desc})")
        if suggestion:
            print(f"   Sugerencia: {suggestion}")

    return 0 if ok else 1


# ─── Self-tests ────────────────────────────────────────────────────────────

def _self_test() -> None:
    print("Tests de branch_check.py...")
    fails: list[str] = []
    def ok(n: str): print(f"  OK: {n}")
    def fail(n, m): fails.append(n); print(f"  FAIL: {n}: {m}")

    # T1 — gitflow: rama válida
    v, _ = validate_branch("feature/user-auth", STYLES["gitflow"]["pattern"])
    if v: ok("branch_check:gitflow_valid")
    else: fail("branch_check:gitflow_valid", "feature/user-auth rechazada")

    # T2 — gitflow: rama inválida
    v, _ = validate_branch("my-feature", STYLES["gitflow"]["pattern"])
    if not v: ok("branch_check:gitflow_invalid")
    else: fail("branch_check:gitflow_invalid", "my-feature aceptada")

    # T3 — simple style
    v, _ = validate_branch("feat/add-login", STYLES["simple"]["pattern"])
    if v: ok("branch_check:simple_valid")
    else: fail("branch_check:simple_valid", "feat/add-login rechazada")

    # T4 — jira style
    v, _ = validate_branch("BAGO-123/add-feature", STYLES["jira"]["pattern"])
    if v: ok("branch_check:jira_valid")
    else: fail("branch_check:jira_valid", "BAGO-123/add-feature rechazada")

    # T5 — bago style
    v, _ = validate_branch("S7/git-context", STYLES["bago"]["pattern"])
    if v: ok("branch_check:bago_valid")
    else: fail("branch_check:bago_valid", "S7/git-context rechazada")

    # T6 — sugerencia cuando inválida
    sug = _suggest_fix("My Feature Branch!", "gitflow")
    if sug.startswith("feature/"):
        ok("branch_check:suggestion_gitflow")
    else:
        fail("branch_check:suggestion_gitflow", f"sug={sug}")

    total = 6; passed = total - len(fails)
    print(f"\n  {passed}/{total} tests pasaron")
    if fails: sys.exit(1)


if __name__ == "__main__":
    if "--test" in sys.argv:
        _self_test()
    else:
        sys.exit(main(sys.argv[1:]))
