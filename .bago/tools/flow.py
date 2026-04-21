#!/usr/bin/env python3
"""
bago flow — visualiza el pipeline de un workflow como flowchart ASCII.

Carga los archivos W*.md del pack y extrae la estructura de fases/pasos
para renderizarlos como diagramas de flujo en la terminal.

Uso:
    bago flow                   → listar workflows disponibles
    bago flow W2                → mostrar flowchart de W2
    bago flow all               → mostrar todos los workflows
    bago flow --list            → listar sin renderizar
    bago flow --test            → tests integrados
"""

import argparse
import json
import sys
import re
from pathlib import Path

BAGO_ROOT = Path(__file__).parent.parent


WORKFLOW_COLORS = {
    "W0": "\033[90m",   # gray
    "W1": "\033[36m",   # cyan
    "W2": "\033[32m",   # green
    "W3": "\033[31m",   # red
    "W4": "\033[33m",   # yellow
    "W5": "\033[35m",   # magenta
    "W6": "\033[34m",   # blue
    "W7": "\033[96m",   # bright cyan
    "W8": "\033[93m",   # bright yellow
    "W9": "\033[95m",   # bright magenta
}
RESET = "\033[0m"


def _find_workflow_files() -> dict:
    """Returns {W_CODE: path} mapping."""
    wf_files = {}
    for f in BAGO_ROOT.rglob("W*.md"):
        if f.is_file():
            m = re.match(r"W(\d+)_", f.name)
            if m:
                code = f"W{m.group(1)}"
                if code not in wf_files:
                    wf_files[code] = f
    return dict(sorted(wf_files.items()))


def _extract_phases(content: str) -> list:
    """Extract phase headers and their first bullet from markdown."""
    phases = []
    lines = content.split("\n")
    current_phase = None
    current_bullets = []

    for line in lines:
        # H2/H3 headers as phases
        m2 = re.match(r"^#{2,3}\s+(.+)", line)
        if m2:
            if current_phase:
                phases.append((current_phase, current_bullets[:3]))
            current_phase = m2.group(1).strip()
            current_bullets = []
            continue

        # Bullet points
        if current_phase and re.match(r"^\s*[-*•]\s+(.+)", line):
            text = re.sub(r"^\s*[-*•]\s+", "", line).strip()
            if text and len(text) > 2:
                current_bullets.append(text[:60])

    if current_phase:
        phases.append((current_phase, current_bullets[:3]))

    return phases


def _render_flowchart(wf_code: str, wf_file: Path) -> str:
    content = wf_file.read_text()
    phases = _extract_phases(content)

    color = WORKFLOW_COLORS.get(wf_code, "")

    lines = []
    title = wf_file.stem.replace("_", " ")
    lines.append(f"\n{color}  ╔══ {title} ══╗{RESET}")
    lines.append(f"{color}  ║ {wf_code} Pipeline{RESET}")
    lines.append(f"{color}  ╚{'═' * (len(title) + 6)}╝{RESET}")
    lines.append("")

    if not phases:
        # Try to extract numbered list items as phases
        for line in content.split("\n"):
            m = re.match(r"^\d+\.\s+\*?\*?(.+?)\*?\*?$", line)
            if m:
                phases.append((m.group(1).strip()[:50], []))

    if not phases:
        lines.append(f"  (sin estructura de fases detectada)")
        lines.append("")
        return "\n".join(lines)

    # Render as vertical flowchart
    for i, (phase, bullets) in enumerate(phases):
        is_last = (i == len(phases) - 1)

        # Phase box
        box_width = min(len(phase) + 4, 50)
        lines.append(f"  {color}┌{'─' * box_width}┐{RESET}")
        lines.append(f"  {color}│ {phase[:box_width-2]:<{box_width-2}} │{RESET}")
        lines.append(f"  {color}└{'─' * box_width}┘{RESET}")

        # Bullets as indented steps
        for b in bullets[:2]:
            lines.append(f"  {color}│{RESET}  · {b[:55]}")

        # Connector
        if not is_last:
            lines.append(f"  {color}│{RESET}")
            lines.append(f"  {color}▼{RESET}")

    lines.append("")
    return "\n".join(lines)


def cmd_list(args):
    wf_files = _find_workflow_files()
    if not wf_files:
        print("  (sin archivos de workflow encontrados)")
        return

    print(f"\n  Workflows BAGO ({len(wf_files)} encontrados)\n")
    for code, path in wf_files.items():
        name = path.stem.replace("_", " ")
        print(f"  {code:4s}  {name}")
    print(f"\n  Usa: bago flow {list(wf_files.keys())[0]} para ver el pipeline\n")


def cmd_flow(wf_code: str):
    wf_files = _find_workflow_files()

    if wf_code.upper() == "ALL":
        for code, path in wf_files.items():
            print(_render_flowchart(code, path))
        return

    # Find by code
    code = wf_code.upper()
    if code not in wf_files:
        # Try partial match
        matches = [k for k in wf_files if wf_code.upper() in k]
        if matches:
            code = matches[0]
        else:
            print(f"  Workflow '{wf_code}' no encontrado. Disponibles: {', '.join(wf_files.keys())}")
            return

    print(_render_flowchart(code, wf_files[code]))


def run_tests():
    print("Ejecutando tests de flow.py...")
    errors = 0

    def ok(name):
        print(f"  OK: {name}")

    def fail(name, msg):
        nonlocal errors
        errors += 1
        print(f"  FAIL: {name} — {msg}")

    # Test 1: find workflow files
    wf_files = _find_workflow_files()
    if len(wf_files) > 0:
        ok("flow:find_workflow_files")
    else:
        fail("flow:find_workflow_files", "no files found")

    # Test 2: extract phases from mock content
    mock_md = """
## Fase 1 — Inicio
- Leer pack.json
- Cargar estado

## Fase 2 — Ejecución
- Ejecutar tarea
- Registrar resultados

## Fase 3 — Cierre
- Generar CHG
- Actualizar estado
"""
    phases = _extract_phases(mock_md)
    if len(phases) == 3:
        ok("flow:extract_phases")
    else:
        fail("flow:extract_phases", f"expected 3 got {len(phases)}: {phases}")

    # Test 3: render flowchart from mock
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as tf:
        tf.write(mock_md)
        tf_path = pathlib.Path(tf.name)
    chart = _render_flowchart("W9", tf_path)
    if "W9" in chart and "Fase 1" in chart:
        ok("flow:render_chart")
    else:
        fail("flow:render_chart", chart[:200])
    tf_path.unlink()

    # Test 4: render a real workflow
    if wf_files:
        code, path = next(iter(wf_files.items()))
        try:
            chart = _render_flowchart(code, path)
            if code in chart:
                ok("flow:render_real_workflow")
            else:
                fail("flow:render_real_workflow", f"code not in chart: {chart[:100]}")
        except Exception as e:
            fail("flow:render_real_workflow", str(e))

    # Test 5: WORKFLOW_COLORS has entries
    if len(WORKFLOW_COLORS) >= 5:
        ok("flow:colors_defined")
    else:
        fail("flow:colors_defined", f"only {len(WORKFLOW_COLORS)} colors")

    total = 5
    passed = total - errors
    print(f"\n  {passed}/{total} tests pasaron")
    if errors:
        sys.exit(1)

import pathlib

def main():
    parser = argparse.ArgumentParser(prog="bago flow", add_help=False)
    parser.add_argument("workflow", nargs="?", default=None, help="W0..W9 o 'all'")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--help", action="store_true")
    args = parser.parse_args()

    if args.test:
        run_tests()
    elif args.list or args.workflow is None:
        cmd_list(args)
    elif args.help:
        parser.print_help()
    else:
        cmd_flow(args.workflow)


if __name__ == "__main__":
    main()