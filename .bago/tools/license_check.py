#!/usr/bin/env python3
"""license_check.py — Herramienta #122: Validador de cabeceras de licencia/copyright.

Detecta archivos Python (y opcionalmente JS/TS) que no tienen ninguna mención
a licencia o copyright en las primeras 10 líneas.

Reglas:
    LIC-W001  Archivo sin cabecera de licencia/copyright
    LIC-W002  Cabecera incompleta (copyright sin licencia o viceversa)
    LIC-I001  Cabecera detectada (informativo)

Uso:
    bago license-check [FILE|DIR]
        [--format text|md|json]
        [--add-header "MIT|Apache-2.0|GPL-3.0|custom=<text>"]
        [--owner "Nombre"]
        [--year YYYY]
        [--ext py,js,ts]
        [--out FILE]
        [--test]
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

_GRN  = "\033[0;32m"
_YEL  = "\033[0;33m"
_RED  = "\033[0;31m"
_CYN  = "\033[0;36m"
_RST  = "\033[0m"
_BOLD = "\033[1m"

SKIP_DIRS   = {"__pycache__", ".git", "venv", ".venv", "node_modules"}
HEADER_SCAN = 10  # primeras N líneas

COPYRIGHT_KEYWORDS = {"copyright", "©", "(c)"}
LICENSE_KEYWORDS   = {
    "license", "licence", "mit", "apache", "gpl", "bsd",
    "mozilla", "lgpl", "agpl", "unlicense", "proprietary",
}

STANDARD_HEADERS = {
    "MIT": lambda owner, year: (
        f"# Copyright (c) {year} {owner}\n"
        "# Licensed under the MIT License.\n"
        "# See LICENSE file in project root for full license information.\n"
    ),
    "Apache-2.0": lambda owner, year: (
        f"# Copyright (c) {year} {owner}\n"
        "# Licensed under the Apache License, Version 2.0.\n"
        "# See LICENSE file in project root for full license information.\n"
    ),
    "GPL-3.0": lambda owner, year: (
        f"# Copyright (c) {year} {owner}\n"
        "# This program is free software: you can redistribute it and/or modify\n"
        "# it under the terms of the GNU General Public License v3.\n"
    ),
}


def _scan_header(filepath: str) -> tuple[bool, bool]:
    """Retorna (has_copyright, has_license)."""
    try:
        lines = Path(filepath).read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return False, False
    header_text = " ".join(lines[:HEADER_SCAN]).lower()
    has_copy    = any(kw in header_text for kw in COPYRIGHT_KEYWORDS)
    has_lic     = any(kw in header_text for kw in LICENSE_KEYWORDS)
    return has_copy, has_lic


def analyze_file(filepath: str, ignore: set[str] = None) -> list[dict]:
    if ignore is None:
        ignore = set()
    findings: list[dict] = []
    has_copy, has_lic = _scan_header(filepath)

    if not has_copy and not has_lic:
        if "LIC-W001" not in ignore:
            findings.append({
                "rule": "LIC-W001", "severity": "warning",
                "file": filepath, "line": 1,
                "message": "Sin cabecera de licencia ni copyright",
            })
    elif has_copy and not has_lic:
        if "LIC-W002" not in ignore:
            findings.append({
                "rule": "LIC-W002", "severity": "warning",
                "file": filepath, "line": 1,
                "message": "Copyright detectado pero sin mención de licencia",
            })
    elif not has_copy and has_lic:
        if "LIC-W002" not in ignore:
            findings.append({
                "rule": "LIC-W002", "severity": "warning",
                "file": filepath, "line": 1,
                "message": "Licencia detectada pero sin copyright",
            })
    else:
        if "LIC-I001" not in ignore:
            findings.append({
                "rule": "LIC-I001", "severity": "info",
                "file": filepath, "line": 1,
                "message": "Cabecera de licencia correcta",
            })
    return findings


def analyze_directory(directory: str, extensions: list[str],
                       ignore: set[str] = None) -> list[dict]:
    all_findings: list[dict] = []
    for ext in extensions:
        for f in sorted(Path(directory).rglob(f"*.{ext}")):
            if any(d in f.parts for d in SKIP_DIRS):
                continue
            all_findings.extend(analyze_file(str(f), ignore))
    return all_findings


def add_header_to_file(filepath: str, header_text: str) -> bool:
    try:
        original = Path(filepath).read_text(encoding="utf-8", errors="ignore")
        # Preserve shebang on first line
        if original.startswith("#!"):
            shebang_end = original.index("\n") + 1
            new_content = original[:shebang_end] + header_text + original[shebang_end:]
        else:
            new_content = header_text + original
        Path(filepath).write_text(new_content, encoding="utf-8")
        return True
    except Exception:
        return False


def generate_text(findings: list[dict], verbose: bool = False) -> str:
    issues = [f for f in findings if f["severity"] != "info"]
    ok     = [f for f in findings if f["severity"] == "info"]
    if not issues:
        return f"{_GRN}✅ Todos los archivos tienen cabecera de licencia — {len(ok)} OK{_RST}"
    lines = [f"{_BOLD}License Check — {len(issues)} archivo(s) sin licencia válida{_RST}", ""]
    for f in issues:
        color = _YEL if f["rule"] == "LIC-W002" else _RED
        lines.append(
            f"  {color}[{f['rule']}]{_RST} {Path(f['file']).name}  {f['message']}"
        )
    lines.append(f"\n  {_GRN}OK: {len(ok)}{_RST}  {_RED}Issues: {len(issues)}{_RST}")
    return "\n".join(lines)


def generate_markdown(findings: list[dict]) -> str:
    issues = [f for f in findings if f["severity"] != "info"]
    ok     = [f for f in findings if f["severity"] == "info"]
    lines  = [
        f"# License Check — {len(issues)} issues, {len(ok)} OK", "",
        "| Regla | Archivo | Mensaje |",
        "|-------|---------|---------|",
    ]
    for f in sorted(findings, key=lambda x: x["severity"]):
        lines.append(f"| `{f['rule']}` | `{Path(f['file']).name}` | {f['message']} |")
    lines += ["", "---", "*Generado con `bago license-check`*"]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    target     = "./"
    fmt        = "text"
    out_file   = None
    add_header = None
    owner      = "Authors"
    year       = str(date.today().year)
    extensions = ["py"]
    ignore: set[str] = set()

    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--format" and i + 1 < len(argv):
            fmt = argv[i + 1]; i += 2
        elif a == "--out" and i + 1 < len(argv):
            out_file = argv[i + 1]; i += 2
        elif a == "--add-header" and i + 1 < len(argv):
            add_header = argv[i + 1]; i += 2
        elif a == "--owner" and i + 1 < len(argv):
            owner = argv[i + 1]; i += 2
        elif a == "--year" and i + 1 < len(argv):
            year = argv[i + 1]; i += 2
        elif a == "--ext" and i + 1 < len(argv):
            extensions = argv[i + 1].split(","); i += 2
        elif a == "--ignore" and i + 1 < len(argv):
            ignore = set(argv[i + 1].split(",")); i += 2
        elif not a.startswith("--"):
            target = a; i += 1
        else:
            i += 1

    target_path = Path(target)
    if not target_path.exists():
        print(f"No existe: {target}", file=sys.stderr); return 1

    if target_path.is_file():
        findings = analyze_file(target, ignore)
    else:
        findings = analyze_directory(target, extensions, ignore)

    # Acción --add-header
    if add_header:
        if add_header in STANDARD_HEADERS:
            header_text = STANDARD_HEADERS[add_header](owner, year)
        elif add_header.startswith("custom="):
            header_text = add_header[7:].replace("\\n", "\n")
        else:
            print(f"Licencia desconocida: {add_header}. Usar MIT|Apache-2.0|GPL-3.0|custom=<text>")
            return 1

        fixed = 0
        for f_info in findings:
            if f_info["rule"] in {"LIC-W001", "LIC-W002"}:
                if add_header_to_file(f_info["file"], header_text):
                    print(f"  Añadida cabecera a {Path(f_info['file']).name}")
                    fixed += 1
        print(f"Cabecera añadida a {fixed} archivo(s).")
        return 0

    if fmt == "json":
        content = json.dumps(findings, indent=2)
    elif fmt == "md":
        content = generate_markdown(findings)
    else:
        content = generate_text(findings)

    if out_file:
        Path(out_file).write_text(content, encoding="utf-8")
        print(f"Guardado: {out_file}", file=sys.stderr)
    else:
        print(content)

    issues = [f for f in findings if f["severity"] != "info"]
    return 1 if issues else 0


def _self_test() -> None:
    import tempfile
    print("Tests de license_check.py...")
    fails: list[str] = []
    def ok(n): print(f"  OK: {n}")
    def fail(n, m): fails.append(n); print(f"  FAIL: {n}: {m}")

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)

        # T1 — archivo sin cabecera → LIC-W001
        (root / "no_lic.py").write_text('def foo(): pass\n')
        f1 = analyze_file(str(root / "no_lic.py"))
        if f1 and f1[0]["rule"] == "LIC-W001":
            ok("license_check:no_header")
        else:
            fail("license_check:no_header", f"findings={f1}")

        # T2 — sólo copyright, sin licencia → LIC-W002
        (root / "copy_only.py").write_text('# Copyright (c) 2025 Test Inc.\ndef foo(): pass\n')
        f2 = analyze_file(str(root / "copy_only.py"))
        if f2 and f2[0]["rule"] == "LIC-W002":
            ok("license_check:copyright_no_license")
        else:
            fail("license_check:copyright_no_license", f"findings={f2}")

        # T3 — cabecera completa → LIC-I001
        (root / "full.py").write_text(
            '# Copyright (c) 2025 Test Inc.\n# MIT License.\ndef foo(): pass\n'
        )
        f3 = analyze_file(str(root / "full.py"))
        if f3 and f3[0]["rule"] == "LIC-I001":
            ok("license_check:full_header_ok")
        else:
            fail("license_check:full_header_ok", f"findings={f3}")

        # T4 — --add-header genera texto correcto
        header = STANDARD_HEADERS["MIT"]("TestOwner", "2025")
        if "Copyright" in header and "MIT" in header and "TestOwner" in header:
            ok("license_check:generate_mit_header")
        else:
            fail("license_check:generate_mit_header", header)

        # T5 — directorio: detecta múltiples archivos
        (root / "sub").mkdir()
        (root / "sub" / "a.py").write_text('def a(): pass\n')
        (root / "sub" / "b.py").write_text('# MIT License\n# Copyright 2025\ndef b(): pass\n')
        dir_findings = analyze_directory(str(root), ["py"])
        rules = {f["rule"] for f in dir_findings}
        if "LIC-W001" in rules and "LIC-I001" in rules:
            ok("license_check:directory_mixed")
        else:
            fail("license_check:directory_mixed", f"rules={rules}")

        # T6 — markdown output
        md = generate_markdown(f1)
        if "License Check" in md and "LIC-W001" in md:
            ok("license_check:markdown_output")
        else:
            fail("license_check:markdown_output", md[:80])

    total = 6; passed = total - len(fails)
    print(f"\n  {passed}/{total} tests pasaron")
    if fails: sys.exit(1)


if __name__ == "__main__":
    if "--test" in sys.argv:
        _self_test()
    else:
        sys.exit(main(sys.argv[1:]))
