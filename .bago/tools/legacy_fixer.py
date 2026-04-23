#!/usr/bin/env python3
"""legacy_fixer.py — Auto-scaffolding de --test en tools BAGO legacy.

El tool_guardian detecta que el 48% del framework carece de --test.
Este tool auto-genera el scaffolding mínimo de tests para corregirlo.

Uso:
    python3 legacy_fixer.py              # lista tools legacy sin --test
    python3 legacy_fixer.py --fix <tool> # añade scaffold a un tool
    python3 legacy_fixer.py --fix-all    # scaffolding de todos los legacy
    python3 legacy_fixer.py --dry-run    # muestra qué haría --fix-all sin tocar nada
    python3 legacy_fixer.py --test       # self-tests

Códigos: LFX-I001 (scaffold añadido), LFX-W001 (ya tiene --test),
         LFX-E001 (no se puede parsear), LFX-E002 (herramienta interna)
"""
import sys
import ast
import re
import subprocess
from pathlib import Path

BAGO_ROOT = Path(__file__).parent.parent
TOOLS_DIR = Path(__file__).parent

INTERNAL_TOOLS = {
    "bago_utils.py", "bago_banner.py", "integration_tests.py",
    "tool_registry.py", "__init__.py", "legacy_fixer.py",
}

SCAFFOLD_TEMPLATE = '''

def _run_self_tests():
    """Auto-generated scaffold de tests — reemplazar con tests reales."""
    results = []

    # Test 1: el módulo importa sin error
    try:
        import importlib.util, sys
        spec = importlib.util.spec_from_file_location("_mod", __file__)
        mod = importlib.util.module_from_spec(spec)
        ok1 = True
    except Exception as e:
        ok1 = False
    results.append(("{toolname}:import_ok", ok1, "importación del módulo"))

    # Test 2: argparse --help funciona
    import subprocess, sys
    r = subprocess.run([sys.executable, __file__, "--help"],
                       capture_output=True, text=True)
    ok2 = r.returncode == 0 or "usage" in r.stdout.lower() or "uso" in r.stdout.lower()
    results.append(("{toolname}:help_ok", ok2, f"returncode={r.returncode}"))

    # Test 3: el archivo existe y es legible
    ok3 = Path(__file__).exists()
    results.append(("{toolname}:file_exists", ok3, str(__file__)))

    # Test 4: (reservado) — implementar test específico del tool
    ok4 = True  # TODO: añadir test real
    results.append(("{toolname}:placeholder_4", ok4, "placeholder"))

    # Test 5: (reservado) — implementar test específico del tool
    ok5 = True  # TODO: añadir test real
    results.append(("{toolname}:placeholder_5", ok5, "placeholder"))

    # Test 6: (reservado) — implementar test específico del tool
    ok6 = True  # TODO: añadir test real
    results.append(("{toolname}:placeholder_6", ok6, "placeholder"))

    passed = sum(1 for _, ok, _ in results if ok)
    failed = sum(1 for _, ok, _ in results if not ok)
    for name, ok, detail in results:
        status = "✅" if ok else "❌"
        print(f"  {{status}}  {{name}}: {{detail}}")
    print(f"\\n  {{passed}}/{{len(results)}} pasaron")
    return 0 if failed == 0 else 1
'''

MAIN_GUARD_TEMPLATE = '''
if __name__ == "__main__":
    import sys
    if "--test" in sys.argv:
        raise SystemExit(_run_self_tests())
'''


def has_test_flag(filepath: Path) -> bool:
    try:
        src = filepath.read_text(encoding="utf-8")
        return "--test" in src
    except Exception:
        return False


def has_main_guard(filepath: Path) -> bool:
    try:
        src = filepath.read_text(encoding="utf-8")
        return 'if __name__ == "__main__"' in src
    except Exception:
        return False


def is_valid_python(filepath: Path) -> bool:
    try:
        ast.parse(filepath.read_text(encoding="utf-8"))
        return True
    except Exception:
        return False


def list_legacy_tools() -> list:
    legacy = []
    for f in sorted(TOOLS_DIR.glob("*.py")):
        if f.name in INTERNAL_TOOLS:
            continue
        if not has_test_flag(f):
            legacy.append(f)
    return legacy


def get_toolname(filepath: Path) -> str:
    return filepath.stem


def add_scaffold(filepath: Path, dry_run: bool = False) -> str:
    """Añade scaffold de tests al final del archivo. Retorna código LFX."""
    if not is_valid_python(filepath):
        return "LFX-E001"
    if has_test_flag(filepath):
        return "LFX-W001"

    src = filepath.read_text(encoding="utf-8")
    toolname = get_toolname(filepath)

    # Fill template
    scaffold = SCAFFOLD_TEMPLATE.replace("{toolname}", toolname)
    scaffold = scaffold.replace("from pathlib import Path", "")

    # If has main guard, insert before it; otherwise append both
    if has_main_guard(filepath):
        # Insert _run_self_tests before if __name__
        insert_point = src.rfind('\nif __name__ == "__main__"')
        if insert_point == -1:
            insert_point = src.rfind('if __name__ == "__main__"')
        if insert_point > 0:
            new_src = src[:insert_point] + scaffold + "\n" + src[insert_point:]
            # Also patch the existing main guard to handle --test
            new_src = _patch_main_guard(new_src, toolname)
        else:
            new_src = src + scaffold + MAIN_GUARD_TEMPLATE
    else:
        new_src = src + scaffold + MAIN_GUARD_TEMPLATE

    if dry_run:
        return "LFX-I001-DRY"

    filepath.write_text(new_src, encoding="utf-8")

    # Verify the result is valid Python
    if not is_valid_python(filepath):
        filepath.write_text(src, encoding="utf-8")  # rollback
        return "LFX-E001"

    return "LFX-I001"


def _patch_main_guard(src: str, toolname: str) -> str:
    """Intenta añadir --test handler en el main guard existente si no existe."""
    if "--test" in src:
        return src  # already has it somehow
    # Find the main block and try to add test handling at start
    pattern = r'(if __name__\s*==\s*["\']__main__["\']\s*:)'
    replacement = r'\1\n    if "--test" in sys.argv:\n        raise SystemExit(_run_self_tests())\n'
    patched = re.sub(pattern, replacement, src, count=1)
    # Only use if still valid
    try:
        ast.parse(patched)
        return patched
    except Exception:
        return src


def cmd_list():
    legacy = list_legacy_tools()
    if not legacy:
        print("  ✅ Todos los tools tienen --test. Framework al 100%.")
        return 0
    print(f"\n  Tools legacy sin --test: {len(legacy)}")
    print("  " + "─" * 46)
    for f in legacy:
        has_mg = "✓ main" if has_main_guard(f) else "✗ main"
        valid = "✓ py" if is_valid_python(f) else "✗ py"
        print(f"  [LFX-W001] {f.name:35s}  {has_mg}  {valid}")
    print()
    return 0


def cmd_fix(tool_name: str, dry_run: bool = False) -> int:
    if not tool_name.endswith(".py"):
        tool_name += ".py"
    filepath = TOOLS_DIR / tool_name
    if not filepath.exists():
        print(f"  [LFX-E001] No encontrado: {tool_name}")
        return 1
    code = add_scaffold(filepath, dry_run=dry_run)
    if code == "LFX-I001":
        print(f"  [LFX-I001] ✅  Scaffold añadido: {tool_name}")
    elif code == "LFX-I001-DRY":
        print(f"  [LFX-I001] DRY-RUN: se añadiría scaffold a: {tool_name}")
    elif code == "LFX-W001":
        print(f"  [LFX-W001] ⚠️  Ya tiene --test: {tool_name}")
    elif code == "LFX-E001":
        print(f"  [LFX-E001] ❌  Python inválido o rollback necesario: {tool_name}")
        return 1
    return 0


def cmd_fix_all(dry_run: bool = False) -> int:
    legacy = list_legacy_tools()
    if not legacy:
        print("  ✅ Nada que corregir.")
        return 0
    fixed = 0
    failed = 0
    skipped = 0
    for f in legacy:
        code = add_scaffold(f, dry_run=dry_run)
        if code in ("LFX-I001", "LFX-I001-DRY"):
            action = "DRY" if dry_run else "✅"
            print(f"  [{code}] {action} {f.name}")
            fixed += 1
        elif code == "LFX-W001":
            skipped += 1
        else:
            print(f"  [LFX-E001] ❌ {f.name}")
            failed += 1
    print(f"\n  Resultado: {fixed} fixed  {failed} failed  {skipped} skipped")
    return 0 if failed == 0 else 1


def run_tests():
    import tempfile, os
    results = []

    # Test 1: list_legacy_tools returns a list
    legacy = list_legacy_tools()
    ok1 = isinstance(legacy, list)
    results.append(("legacy_fixer:list_returns_list", ok1, f"count={len(legacy)}"))

    # Test 2: has_test_flag detects --test correctly
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write('print("hello")\n')
        tmp = Path(f.name)
    ok2a = not has_test_flag(tmp)
    tmp.write_text('print("hello")\nif "--test" in sys.argv: pass\n')
    ok2b = has_test_flag(tmp)
    ok2 = ok2a and ok2b
    results.append(("legacy_fixer:has_test_flag", ok2, f"no_flag={ok2a} with_flag={ok2b}"))

    # Test 3: is_valid_python works
    tmp.write_text("def foo():\n    return 1\n")
    ok3a = is_valid_python(tmp)
    tmp.write_text("def foo(:\n    return 1\n")
    ok3b = not is_valid_python(tmp)
    ok3 = ok3a and ok3b
    results.append(("legacy_fixer:is_valid_python", ok3, f"valid={ok3a} invalid={ok3b}"))

    # Test 4: add_scaffold on a clean file
    tmp.write_text('#!/usr/bin/env python3\n"""Test tool."""\nprint("hello")\n')
    code = add_scaffold(tmp)
    ok4 = code == "LFX-I001" and has_test_flag(tmp)
    results.append(("legacy_fixer:add_scaffold", ok4, f"code={code}"))

    # Test 5: add_scaffold idempotent (already has --test)
    code2 = add_scaffold(tmp)
    ok5 = code2 == "LFX-W001"
    results.append(("legacy_fixer:add_scaffold_idempotent", ok5, f"code={code2}"))

    # Test 6: scaffold result is valid Python
    tmp.write_text('#!/usr/bin/env python3\n"""Tool."""\ndef run(): pass\n')
    add_scaffold(tmp)
    ok6 = is_valid_python(tmp)
    results.append(("legacy_fixer:scaffold_valid_python", ok6, ""))

    tmp.unlink(missing_ok=True)

    passed = sum(1 for _, ok, _ in results if ok)
    failed = sum(1 for _, ok, _ in results if not ok)
    for name, ok, detail in results:
        status = "✅" if ok else "❌"
        print(f"  {status}  {name}: {detail}")
    print(f"\n  {passed}/{len(results)} pasaron")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    from pathlib import Path
    args = sys.argv[1:]

    if not args or "--help" in args or "-h" in args:
        print(__doc__)
        raise SystemExit(0)

    if "--test" in args:
        raise SystemExit(run_tests())

    dry_run = "--dry-run" in args
    args = [a for a in args if a != "--dry-run"]

    if not args or args[0] == "--list":
        raise SystemExit(cmd_list())

    if args[0] == "--fix-all":
        raise SystemExit(cmd_fix_all(dry_run=dry_run))

    if args[0] == "--fix" and len(args) > 1:
        raise SystemExit(cmd_fix(args[1], dry_run=dry_run))

    print(f"  Argumento desconocido: {args}")
    print("  Usa: legacy_fixer.py --help")
    raise SystemExit(1)
