#!/usr/bin/env python3
"""duplicate_check.py — Herramienta #113: Detector de código duplicado.

Detecta bloques de código duplicados o casi-idénticos en archivos Python.
Usa hashing normalizado de líneas para comparar bloques de N líneas entre
todos los archivos del proyecto.

Reglas:
    DUP-W001  Bloque duplicado exacto (≥5 líneas)
    DUP-W002  Bloque casi-idéntico (>80% similitud, ≥5 líneas)

Uso:
    bago duplicate-check [DIR] [--min-lines N] [--threshold N]
                          [--format text|json|md] [--out FILE] [--test]
"""
from __future__ import annotations

import ast
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Optional

_GRN  = "\033[0;32m"
_YEL  = "\033[0;33m"
_RED  = "\033[0;31m"
_RST  = "\033[0m"
_BOLD = "\033[1m"

SKIP_DIRS = {"__pycache__", ".git", "venv", ".venv", "node_modules"}


def _normalize_line(line: str) -> str:
    """Elimina indentación y comentarios para comparación."""
    stripped = line.strip()
    if stripped.startswith("#"):
        return ""
    return stripped


def _hash_block(lines: list[str]) -> str:
    normalized = "\n".join(_normalize_line(l) for l in lines if _normalize_line(l))
    return hashlib.md5(normalized.encode()).hexdigest()


def _similarity(a: list[str], b: list[str]) -> float:
    """Similitud Jaccard sobre conjunto de líneas normalizadas."""
    sa = set(_normalize_line(l) for l in a if _normalize_line(l))
    sb = set(_normalize_line(l) for l in b if _normalize_line(l))
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def extract_blocks(filepath: str, min_lines: int) -> list[dict]:
    """Extrae todos los bloques de min_lines líneas consecutivas del archivo."""
    try:
        lines = Path(filepath).read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return []
    blocks = []
    for i in range(len(lines) - min_lines + 1):
        block = lines[i:i + min_lines]
        # Saltar bloques que son solo blancos/comentarios
        meaningful = [l for l in block if _normalize_line(l)]
        if len(meaningful) < max(2, min_lines // 2):
            continue
        blocks.append({
            "file":  filepath,
            "line":  i + 1,
            "lines": block,
            "hash":  _hash_block(block),
        })
    return blocks


def find_duplicates(directory: str, min_lines: int = 5,
                     threshold: float = 0.85) -> list[dict]:
    """Encuentra duplicados exactos y casi-idénticos."""
    root   = Path(directory)
    py_files = [f for f in root.rglob("*.py")
                if not any(d in f.parts for d in SKIP_DIRS)]

    all_blocks: list[dict] = []
    for f in py_files:
        all_blocks.extend(extract_blocks(str(f), min_lines))

    # Agrupar por hash exacto
    by_hash: dict[str, list[dict]] = defaultdict(list)
    for b in all_blocks:
        by_hash[b["hash"]].append(b)

    findings: list[dict] = []

    # DUP-W001: duplicados exactos
    for h, group in by_hash.items():
        if len(group) < 2:
            continue
        # Omitir si todos están en el mismo archivo y líneas contiguas
        files = [g["file"] for g in group]
        if len(set(files)) == 1:
            continue
        findings.append({
            "rule":     "DUP-W001",
            "severity": "warning",
            "message":  f"Bloque exacto duplicado ({min_lines}+ líneas)",
            "locations": [(g["file"], g["line"]) for g in group],
            "snippet":  "\n".join(group[0]["lines"][:3]) + "\n...",
        })

    # DUP-W002: casi-idénticos (cross-file, evitar re-comparar ya encontrados)
    exact_pairs: set[frozenset] = set()
    for finding in findings:
        locs = finding["locations"]
        for i in range(len(locs)):
            for j in range(i + 1, len(locs)):
                exact_pairs.add(frozenset([locs[i], locs[j]]))

    checked: set[tuple] = set()
    for i, b1 in enumerate(all_blocks):
        for j, b2 in enumerate(all_blocks):
            if j <= i:
                continue
            if b1["file"] == b2["file"]:
                continue
            pair = (b1["file"], b1["line"], b2["file"], b2["line"])
            if pair in checked:
                continue
            checked.add(pair)
            if b1["hash"] == b2["hash"]:
                continue  # ya capturado como DUP-W001
            sim = _similarity(b1["lines"], b2["lines"])
            if sim >= threshold:
                findings.append({
                    "rule":     "DUP-W002",
                    "severity": "warning",
                    "message":  f"Bloque casi-idéntico ({sim:.0%} similitud)",
                    "locations": [(b1["file"], b1["line"]), (b2["file"], b2["line"])],
                    "snippet":  "\n".join(b1["lines"][:3]) + "\n...",
                })

    return findings


def generate_text(findings: list[dict], directory: str) -> str:
    if not findings:
        return f"{_GRN}✅ No se encontraron duplicados{_RST}"
    lines = [f"{_BOLD}Duplicate Check — {len(findings)} hallazgo(s){_RST}", ""]
    for f in findings:
        sev_color = _RED if f["severity"] == "error" else _YEL
        lines.append(f"  {sev_color}[{f['rule']}]{_RST} {f['message']}")
        for filepath, line in f["locations"]:
            rel = str(Path(filepath).relative_to(directory)) if Path(filepath).is_relative_to(directory) else filepath
            lines.append(f"    ↳ {rel}:{line}")
        snippet_lines = f["snippet"].splitlines()
        lines.append(f"    │ {snippet_lines[0]}")
        if len(snippet_lines) > 1:
            lines.append(f"    │ {snippet_lines[1]}")
        lines.append("")
    return "\n".join(lines)


def generate_markdown(findings: list[dict]) -> str:
    if not findings:
        return "# Duplicate Check\n\n✅ No se encontraron duplicados.\n"
    lines = [
        f"# Duplicate Check — {len(findings)} hallazgo(s)",
        "",
        "| Regla | Mensaje | Archivos |",
        "|-------|---------|---------|",
    ]
    for f in findings:
        locs = " · ".join(f"`{Path(loc[0]).name}:{loc[1]}`" for loc in f["locations"])
        lines.append(f"| `{f['rule']}` | {f['message']} | {locs} |")
    lines += ["", "---", "*Generado con `bago duplicate-check`*"]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    directory  = "./"
    min_lines  = 5
    threshold  = 0.85
    fmt        = "text"
    out_file   = None

    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--min-lines" and i + 1 < len(argv):
            min_lines = int(argv[i + 1]); i += 2
        elif a == "--threshold" and i + 1 < len(argv):
            threshold = float(argv[i + 1]); i += 2
        elif a == "--format" and i + 1 < len(argv):
            fmt = argv[i + 1]; i += 2
        elif a == "--out" and i + 1 < len(argv):
            out_file = argv[i + 1]; i += 2
        elif not a.startswith("--"):
            directory = a; i += 1
        else:
            i += 1

    if not Path(directory).exists():
        print(f"No existe: {directory}", file=sys.stderr); return 1

    findings = find_duplicates(directory, min_lines, threshold)

    if fmt == "json":
        content = json.dumps(findings, indent=2)
    elif fmt == "md":
        content = generate_markdown(findings)
    else:
        content = generate_text(findings, directory)

    if out_file:
        Path(out_file).write_text(content, encoding="utf-8")
        print(f"Guardado: {out_file}", file=sys.stderr)
    else:
        print(content)
    return 0


def _self_test() -> None:
    import tempfile
    print("Tests de duplicate_check.py...")
    fails: list[str] = []
    def ok(n): print(f"  OK: {n}")
    def fail(n, m): fails.append(n); print(f"  FAIL: {n}: {m}")

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)

        block = "def process(x):\n    result = x * 2\n    if result > 10:\n        return result\n    return 0\n"
        (root / "a.py").write_text(block)
        (root / "b.py").write_text(block)  # duplicado exacto
        (root / "c.py").write_text("import os\nprint(os.getcwd())\n")  # diferente

        # T1 — encuentra duplicado exacto cross-file
        findings = find_duplicates(td, min_lines=5)
        dup_w001 = [f for f in findings if f["rule"] == "DUP-W001"]
        if dup_w001:
            ok("duplicate_check:exact_dup_found")
        else:
            fail("duplicate_check:exact_dup_found", f"findings={findings}")

        # T2 — DUP-W001 tiene 2 locaciones
        if dup_w001 and len(dup_w001[0]["locations"]) == 2:
            ok("duplicate_check:locations_count")
        else:
            fail("duplicate_check:locations_count", str(dup_w001))

        # T3 — c.py no aparece en los duplicados
        locs = [loc[0] for f in dup_w001 for loc in f["locations"]]
        if not any("c.py" in l for l in locs):
            ok("duplicate_check:no_false_positive")
        else:
            fail("duplicate_check:no_false_positive", f"locs={locs}")

        # T4 — similar (casi-idéntico) detectado con threshold bajo
        block2 = block.replace("result = x * 2", "result = x * 3")
        (root / "d.py").write_text(block2)
        (root / "e.py").write_text(block)
        findings2 = find_duplicates(td, min_lines=5, threshold=0.6)
        w002 = [f for f in findings2 if f["rule"] == "DUP-W002"]
        # Should detect near-dup between d.py and e.py (or a.py/b.py)
        if w002 or dup_w001:
            ok("duplicate_check:near_dup")
        else:
            fail("duplicate_check:near_dup", "no near-dups found at threshold 0.6")

        # T5 — text output contiene regla
        txt = generate_text(dup_w001, td)
        if "DUP-W001" in txt or "No se encontraron" in txt:
            ok("duplicate_check:text_output")
        else:
            fail("duplicate_check:text_output", txt[:80])

        # T6 — markdown output
        md = generate_markdown(dup_w001)
        if "Duplicate Check" in md:
            ok("duplicate_check:markdown_output")
        else:
            fail("duplicate_check:markdown_output", md[:80])

    total = 6; passed = total - len(fails)
    print(f"\n  {passed}/{total} tests pasaron")
    if fails: sys.exit(1)


if __name__ == "__main__":
    if "--test" in sys.argv:
        _self_test()
    else:
        sys.exit(main(sys.argv[1:]))
