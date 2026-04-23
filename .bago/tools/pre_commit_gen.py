#!/usr/bin/env python3
"""pre_commit_gen.py — Herramienta #114: Generador de .pre-commit-config.yaml.

Genera un archivo .pre-commit-config.yaml para el repositorio actual,
incluyendo hooks BAGO (lint, secret-scan, complexity, branch-check) y
hooks estándar de la industria (trailing-whitespace, end-of-file-fixer,
check-yaml, check-merge-conflict, etc.).

Uso:
    bago pre-commit-gen [--bago-only] [--standard-only]
                        [--hooks HOOK1,HOOK2,...] [--out FILE]
                        [--dry-run] [--test]
"""
from __future__ import annotations

import sys
from pathlib import Path

_GRN  = "\033[0;32m"
_YEL  = "\033[0;33m"
_RST  = "\033[0m"
_BOLD = "\033[1m"

BAGO_ROOT = Path(__file__).parent.parent.parent

STANDARD_HOOKS = {
    "trailing-whitespace": {
        "id": "trailing-whitespace",
        "repo": "https://github.com/pre-commit/pre-commit-hooks",
        "rev": "v4.5.0",
        "args": [],
    },
    "end-of-file-fixer": {
        "id": "end-of-file-fixer",
        "repo": "https://github.com/pre-commit/pre-commit-hooks",
        "rev": "v4.5.0",
        "args": [],
    },
    "check-yaml": {
        "id": "check-yaml",
        "repo": "https://github.com/pre-commit/pre-commit-hooks",
        "rev": "v4.5.0",
        "args": [],
    },
    "check-merge-conflict": {
        "id": "check-merge-conflict",
        "repo": "https://github.com/pre-commit/pre-commit-hooks",
        "rev": "v4.5.0",
        "args": [],
    },
    "check-added-large-files": {
        "id": "check-added-large-files",
        "repo": "https://github.com/pre-commit/pre-commit-hooks",
        "rev": "v4.5.0",
        "args": ["--maxkb=500"],
    },
    "detect-private-key": {
        "id": "detect-private-key",
        "repo": "https://github.com/pre-commit/pre-commit-hooks",
        "rev": "v4.5.0",
        "args": [],
    },
}

BAGO_HOOKS = {
    "bago-lint": {
        "id": "bago-lint",
        "name": "BAGO lint",
        "entry": "bago lint",
        "language": "system",
        "types": ["python"],
        "pass_filenames": False,
    },
    "bago-secret-scan": {
        "id": "bago-secret-scan",
        "name": "BAGO secret scan",
        "entry": "bago secret-scan .",
        "language": "system",
        "pass_filenames": False,
    },
    "bago-complexity": {
        "id": "bago-complexity",
        "name": "BAGO complexity check",
        "entry": "bago complexity --max 10",
        "language": "system",
        "types": ["python"],
        "pass_filenames": False,
    },
    "bago-branch-check": {
        "id": "bago-branch-check",
        "name": "BAGO branch name check",
        "entry": "bago branch-check --ci",
        "language": "system",
        "pass_filenames": False,
        "stages": ["commit"],
    },
    "bago-dead-code": {
        "id": "bago-dead-code",
        "name": "BAGO dead code",
        "entry": "bago dead-code .",
        "language": "system",
        "types": ["python"],
        "pass_filenames": False,
    },
}

DEFAULT_STANDARD = ["trailing-whitespace", "end-of-file-fixer",
                     "check-yaml", "check-merge-conflict", "detect-private-key"]
DEFAULT_BAGO     = ["bago-lint", "bago-secret-scan", "bago-complexity"]


def _indent(text: str, n: int = 4) -> str:
    pad = " " * n
    return "\n".join(pad + line if line.strip() else line for line in text.splitlines())


def generate_config(standard_hooks: list[str], bago_hooks: list[str]) -> str:
    """Genera el contenido YAML del .pre-commit-config.yaml."""
    lines = ["# .pre-commit-config.yaml — generado por bago pre-commit-gen",
             "# Instalar: pip install pre-commit && pre-commit install",
             "",
             "repos:"]

    # Standard hooks agrupados por repo
    std_selected = {k: v for k, v in STANDARD_HOOKS.items() if k in standard_hooks}
    if std_selected:
        first = next(iter(std_selected.values()))
        repo  = first["repo"]
        rev   = first["rev"]
        lines += [f"  - repo: {repo}", f"    rev: {rev}", "    hooks:"]
        for hook in std_selected.values():
            lines.append(f"      - id: {hook['id']}")
            if hook.get("args"):
                lines.append(f"        args: {hook['args']}")

    # BAGO hooks como local
    bago_selected = {k: v for k, v in BAGO_HOOKS.items() if k in bago_hooks}
    if bago_selected:
        lines += ["", "  - repo: local", "    hooks:"]
        for hook in bago_selected.values():
            lines.append(f"      - id: {hook['id']}")
            lines.append(f"        name: {hook['name']}")
            lines.append(f"        entry: {hook['entry']}")
            lines.append(f"        language: {hook['language']}")
            if "types" in hook:
                lines.append(f"        types: {hook['types']}")
            if "pass_filenames" in hook:
                lines.append(f"        pass_filenames: {str(hook['pass_filenames']).lower()}")
            if "stages" in hook:
                lines.append(f"        stages: {hook['stages']}")

    lines.append("")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    bago_only     = False
    standard_only = False
    hooks_filter  = None
    out_file      = ".pre-commit-config.yaml"
    dry_run       = False

    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--bago-only":
            bago_only = True; i += 1
        elif a == "--standard-only":
            standard_only = True; i += 1
        elif a == "--hooks" and i + 1 < len(argv):
            hooks_filter = argv[i + 1].split(","); i += 2
        elif a == "--out" and i + 1 < len(argv):
            out_file = argv[i + 1]; i += 2
        elif a == "--dry-run":
            dry_run = True; i += 1
        else:
            i += 1

    std_list  = [] if bago_only  else list(DEFAULT_STANDARD)
    bago_list = [] if standard_only else list(DEFAULT_BAGO)

    if hooks_filter:
        std_list  = [h for h in std_list  if h in hooks_filter]
        bago_list = [h for h in bago_list if h in hooks_filter]

    config = generate_config(std_list, bago_list)

    if dry_run:
        print(config)
        return 0

    out_path = Path(out_file)
    if out_path.exists():
        print(f"{_YEL}⚠  {out_file} ya existe — usa --dry-run para previsualizar{_RST}")
        print(f"   Sobrescribiendo...")
    out_path.write_text(config, encoding="utf-8")
    print(f"{_GRN}✅ Generado: {out_file}{_RST}")
    print(f"   Hooks estándar: {len(std_list)}  |  Hooks BAGO: {len(bago_list)}")
    print(f"   Siguiente paso: pip install pre-commit && pre-commit install")
    return 0


def _self_test() -> None:
    print("Tests de pre_commit_gen.py...")
    fails: list[str] = []
    def ok(n): print(f"  OK: {n}")
    def fail(n, m): fails.append(n); print(f"  FAIL: {n}: {m}")

    # T1 — config contiene sección repos
    cfg = generate_config(DEFAULT_STANDARD, DEFAULT_BAGO)
    if "repos:" in cfg:
        ok("pre_commit_gen:repos_section")
    else:
        fail("pre_commit_gen:repos_section", cfg[:80])

    # T2 — hooks estándar presentes
    cfg2 = generate_config(["trailing-whitespace", "detect-private-key"], [])
    if "trailing-whitespace" in cfg2 and "detect-private-key" in cfg2:
        ok("pre_commit_gen:standard_hooks")
    else:
        fail("pre_commit_gen:standard_hooks", cfg2[:120])

    # T3 — hooks BAGO como local
    cfg3 = generate_config([], ["bago-lint", "bago-secret-scan"])
    if "repo: local" in cfg3 and "bago-lint" in cfg3:
        ok("pre_commit_gen:bago_hooks_local")
    else:
        fail("pre_commit_gen:bago_hooks_local", cfg3[:120])

    # T4 — bago-only no incluye standard
    cfg4 = generate_config([], DEFAULT_BAGO)
    if "pre-commit-hooks" not in cfg4:
        ok("pre_commit_gen:bago_only")
    else:
        fail("pre_commit_gen:bago_only", "standard hooks found in bago-only config")

    # T5 — standard-only no incluye hooks BAGO (solo el comentario cabecera los menciona)
    cfg5 = generate_config(DEFAULT_STANDARD, [])
    bago_lines = [l for l in cfg5.splitlines() if "bago" in l.lower() and not l.startswith("#")]
    if not bago_lines:
        ok("pre_commit_gen:standard_only")
    else:
        fail("pre_commit_gen:standard_only", f"bago hooks found: {bago_lines}")

    # T6 — config YAML sintaxis válida (líneas bien formadas)
    lines = generate_config(DEFAULT_STANDARD, DEFAULT_BAGO).splitlines()
    bad_lines = [l for l in lines if l and not l.startswith(" ") and not l.startswith("-") and not l.startswith("#") and ":" not in l and l.strip() != ""]
    if not bad_lines:
        ok("pre_commit_gen:yaml_structure")
    else:
        fail("pre_commit_gen:yaml_structure", f"bad lines: {bad_lines[:3]}")

    total = 6; passed = total - len(fails)
    print(f"\n  {passed}/{total} tests pasaron")
    if fails: raise SystemExit(1)


if __name__ == "__main__":
    if "--test" in sys.argv:
        _self_test()
    else:
        raise SystemExit(main(sys.argv[1:]))
