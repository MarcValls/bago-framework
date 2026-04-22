#!/usr/bin/env python3
"""readme_check.py — Herramienta #124: Validador de estructura de README.md.

Verifica que el README tenga las secciones esenciales para un proyecto bien
documentado. Detecta secciones faltantes, placeholders sin reemplazar y
enlaces rotos (hrefs internos al archivo).

Reglas:
    README-W001  Sección requerida faltante (configurable vía --sections)
    README-W002  Placeholder sin reemplazar (TODO, FIXME, <YOUR_>, TBD)
    README-W003  Enlace interno roto (fragmento #section no encontrado)
    README-I001  README muy corto (< 20 líneas)
    README-I002  Sin badge (shields.io / img.shields.io)

Uso:
    bago readme-check [FILE|DIR]
        [--sections "Installation,Usage,License"]
        [--format text|md|json]
        [--out FILE]
        [--test]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_GRN  = "\033[0;32m"
_YEL  = "\033[0;33m"
_CYN  = "\033[0;36m"
_RST  = "\033[0m"
_BOLD = "\033[1m"

DEFAULT_SECTIONS = [
    "installation", "usage", "license",
]

PLACEHOLDER_RE = re.compile(
    r'\b(TODO|FIXME|TBD|PLACEHOLDER|YOUR[_\-]|<your[_\-]|<nombre|<name)\b',
    re.IGNORECASE,
)
INTERNAL_LINK_RE = re.compile(r'\[.*?\]\(#([^)]+)\)')
BADGE_RE         = re.compile(r'shields\.io|img\.shields', re.IGNORECASE)


def _heading_to_anchor(heading: str) -> str:
    """Convierte un heading Markdown a su anchor fragment."""
    s = heading.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'\s+', '-', s)
    return s.strip('-')


def analyze_file(filepath: str,
                  required_sections: list[str] | None = None,
                  ignore: set[str] = None) -> list[dict]:
    if required_sections is None:
        required_sections = DEFAULT_SECTIONS
    if ignore is None:
        ignore = set()

    findings: list[dict] = []
    try:
        text  = Path(filepath).read_text(encoding="utf-8", errors="ignore")
        lines = text.splitlines()
    except Exception:
        return findings

    # Extraer headings del documento
    headings = []
    for line in lines:
        m = re.match(r'^(#{1,6})\s+(.*)', line)
        if m:
            headings.append(_heading_to_anchor(m.group(2)))

    # README-W001 — secciones faltantes
    if "README-W001" not in ignore:
        for section in required_sections:
            section_anchor = _heading_to_anchor(section)
            found = any(section_anchor in h for h in headings)
            if not found:
                findings.append({
                    "rule": "README-W001", "severity": "warning",
                    "file": filepath, "line": 0,
                    "message": f"Sección faltante: '{section}'",
                })

    # README-W002 — placeholders
    if "README-W002" not in ignore:
        for i, line in enumerate(lines, 1):
            m = PLACEHOLDER_RE.search(line)
            if m:
                findings.append({
                    "rule": "README-W002", "severity": "warning",
                    "file": filepath, "line": i,
                    "message": f"Placeholder sin reemplazar: '{m.group()}'",
                })

    # README-W003 — enlaces internos rotos
    if "README-W003" not in ignore:
        for i, line in enumerate(lines, 1):
            for match in INTERNAL_LINK_RE.finditer(line):
                fragment = match.group(1)
                if fragment not in headings:
                    findings.append({
                        "rule": "README-W003", "severity": "warning",
                        "file": filepath, "line": i,
                        "message": f"Enlace interno roto: '#{fragment}'",
                    })

    # README-I001 — README muy corto
    if "README-I001" not in ignore and len(lines) < 20:
        findings.append({
            "rule": "README-I001", "severity": "info",
            "file": filepath, "line": 1,
            "message": f"README muy corto ({len(lines)} líneas, mínimo recomendado: 20)",
        })

    # README-I002 — sin badge
    if "README-I002" not in ignore:
        if not BADGE_RE.search(text):
            findings.append({
                "rule": "README-I002", "severity": "info",
                "file": filepath, "line": 1,
                "message": "Sin badge (shields.io) — considera añadir build/coverage/version",
            })

    return findings


def find_readme(directory: str) -> str | None:
    for name in ["README.md", "readme.md", "Readme.md", "README.rst"]:
        p = Path(directory) / name
        if p.exists():
            return str(p)
    return None


def generate_text(findings: list[dict]) -> str:
    issues = [f for f in findings if f["severity"] != "info"]
    infos  = [f for f in findings if f["severity"] == "info"]
    if not issues and not infos:
        return f"{_GRN}✅ README correcto{_RST}"
    lines = [f"{_BOLD}README Check — {len(issues)} issue(s), {len(infos)} info(s){_RST}", ""]
    for f in issues:
        lines.append(f"  {_YEL}[{f['rule']}]{_RST} L{f['line']}  {f['message']}")
    for f in infos:
        lines.append(f"  {_CYN}[{f['rule']}]{_RST}  {f['message']}")
    return "\n".join(lines)


def generate_markdown(findings: list[dict]) -> str:
    issues = [f for f in findings if f["severity"] != "info"]
    infos  = [f for f in findings if f["severity"] == "info"]
    lines  = [
        f"# README Check — {len(issues)} issues, {len(infos)} infos", "",
        "| Regla | L | Severidad | Mensaje |",
        "|-------|---|-----------|---------|",
    ]
    for f in findings:
        lines.append(
            f"| `{f['rule']}` | {f['line']} | {f['severity']} | {f['message']} |"
        )
    lines += ["", "---", "*Generado con `bago readme-check`*"]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    target   = "./"
    sections = list(DEFAULT_SECTIONS)
    fmt      = "text"
    out_file = None
    ignore: set[str] = set()

    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--sections" and i + 1 < len(argv):
            sections = [s.strip() for s in argv[i + 1].split(",")]; i += 2
        elif a == "--format" and i + 1 < len(argv):
            fmt = argv[i + 1]; i += 2
        elif a == "--out" and i + 1 < len(argv):
            out_file = argv[i + 1]; i += 2
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
        filepath = target
    else:
        filepath = find_readme(target)
        if not filepath:
            print("No se encontró README.md en el directorio.")
            return 1

    findings = analyze_file(filepath, sections, ignore)

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

    issues = [f for f in findings if f["severity"] == "warning"]
    return 1 if issues else 0


def _self_test() -> None:
    import tempfile
    print("Tests de readme_check.py...")
    fails: list[str] = []
    def ok(n): print(f"  OK: {n}")
    def fail(n, m): fails.append(n); print(f"  FAIL: {n}: {m}")

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)

        # T1 — README sin sección installation → README-W001
        (root / "README.md").write_text(
            "# My Project\n\n## Usage\nHello\n\n## License\nMIT\n"
        )
        f1 = analyze_file(str(root / "README.md"))
        w001 = [f for f in f1 if f["rule"] == "README-W001"]
        if w001 and "installation" in w001[0]["message"].lower():
            ok("readme_check:missing_section")
        else:
            fail("readme_check:missing_section", f"findings={f1}")

        # T2 — placeholder → README-W002
        (root / "README_TODO.md").write_text(
            "# Project\nTODO: complete this section\n\n## Installation\nfoo\n\n## Usage\nbar\n\n## License\nMIT\n"
        )
        f2 = analyze_file(str(root / "README_TODO.md"))
        w002 = [f for f in f2 if f["rule"] == "README-W002"]
        if w002:
            ok("readme_check:placeholder")
        else:
            fail("readme_check:placeholder", f"findings={f2}")

        # T3 — enlace interno roto → README-W003
        (root / "README_LINK.md").write_text(
            "# Project\n[Ver](#noexiste)\n\n## Installation\nfoo\n\n## Usage\nbar\n\n## License\nMIT\n"
        )
        f3 = analyze_file(str(root / "README_LINK.md"))
        w003 = [f for f in f3 if f["rule"] == "README-W003"]
        if w003:
            ok("readme_check:broken_link")
        else:
            fail("readme_check:broken_link", f"findings={f3}")

        # T4 — README corto → README-I001
        (root / "SHORT.md").write_text("# Project\nHello\n")
        f4 = analyze_file(str(root / "SHORT.md"))
        i001 = [f for f in f4 if f["rule"] == "README-I001"]
        if i001:
            ok("readme_check:too_short")
        else:
            fail("readme_check:too_short", f"findings={f4}")

        # T5 — find_readme funciona
        (root / "sub_dir").mkdir()
        (root / "sub_dir" / "README.md").write_text("# hello\n")
        found = find_readme(str(root / "sub_dir"))
        if found and "README.md" in found:
            ok("readme_check:find_readme")
        else:
            fail("readme_check:find_readme", f"found={found}")

        # T6 — markdown output
        md = generate_markdown(w001)
        if "README Check" in md and "README-W001" in md:
            ok("readme_check:markdown_output")
        else:
            fail("readme_check:markdown_output", md[:80])

    total = 6; passed = total - len(fails)
    print(f"\n  {passed}/{total} tests pasaron")
    if fails: sys.exit(1)


if __name__ == "__main__":
    if "--test" in sys.argv:
        _self_test()
    else:
        sys.exit(main(sys.argv[1:]))
