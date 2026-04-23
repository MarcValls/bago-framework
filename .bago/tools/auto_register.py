#!/usr/bin/env python3
"""auto_register.py — Registro automático de nuevos tools en el framework BAGO.

Cada tool nuevo requiere editar manualmente 3 archivos:
  1. integration_tests.py — añadir def test_X() + ALL_TESTS entry
  2. bago script — añadir elif cmd == "..." routing
  3. CHECKSUMS.sha256 — regen

Este tool automatiza los 3 pasos. Solo necesitas el nombre del tool.

Uso:
    python3 auto_register.py tool_name.py
    python3 auto_register.py tool_name.py --cmd "command-name" --desc "descripción"
    python3 auto_register.py --check tool_name.py     # verifica si ya está registrado
    python3 auto_register.py --check-all              # estado de todos los tools
    python3 auto_register.py --dry-run tool_name.py   # muestra qué haría
    python3 auto_register.py --test                   # self-tests

Códigos: REG-I001 (registrado), REG-W001 (ya registrado), REG-E001 (error)
"""
import sys
import re
import subprocess
from pathlib import Path

BAGO_ROOT = Path(__file__).parent.parent
TOOLS_DIR = Path(__file__).parent
BAGO_SCRIPT = BAGO_ROOT.parent / "bago"
INTEGRATION_TESTS = TOOLS_DIR / "integration_tests.py"
CHECKSUMS_FILE = BAGO_ROOT / "CHECKSUMS.sha256"
TREE_FILE = BAGO_ROOT / "TREE.txt"

INTERNAL_TOOLS = {
    "bago_utils.py", "bago_banner.py", "integration_tests.py",
    "tool_registry.py", "__init__.py", "auto_register.py",
    "legacy_fixer.py",
}


def tool_file_to_cmd(tool_file: str) -> str:
    """Convierte 'my_tool.py' → 'my-tool'."""
    return Path(tool_file).stem.replace("_", "-")


def tool_file_to_func(tool_file: str) -> str:
    """Convierte 'my_tool.py' → 'test_my_tool'."""
    return "test_" + Path(tool_file).stem


def tool_file_to_stem(tool_file: str) -> str:
    return Path(tool_file).stem


def is_in_integration_tests(tool_file: str) -> bool:
    """Verifica si el tool ya tiene entrada en integration_tests.py."""
    try:
        src = INTEGRATION_TESTS.read_text(encoding="utf-8")
        stem = tool_file_to_stem(tool_file)
        return f'"{stem}.py"' in src or f"test_{stem}" in src
    except Exception:
        return False


def is_in_bago_script(tool_file: str) -> bool:
    """Verifica si el tool ya tiene routing en el script bago."""
    try:
        src = BAGO_SCRIPT.read_text(encoding="utf-8")
        cmd = tool_file_to_cmd(tool_file)
        return f'cmd == "{cmd}"' in src
    except Exception:
        return False


def get_next_test_number(src: str) -> int:
    """Determina el siguiente número de test en ALL_TESTS."""
    nums = re.findall(r'^\s*\((\d+),\s*"', src, re.MULTILINE)
    if not nums:
        return 1
    return max(int(n) for n in nums) + 1


def generate_test_function(tool_file: str) -> str:
    """Genera la función test para integration_tests.py."""
    stem = tool_file_to_stem(tool_file)
    func_name = tool_file_to_func(tool_file)
    return f'''
def {func_name}():
    """{stem}.py --test pasa todos los tests."""
    rc, out, _ = _run("{stem}.py", ["--test"])
    if rc == 0 and "pasaron" in out:
        _record("{stem}:tests", PASS, out.strip().split("\\n")[-1] or "ok")
    else:
        _record("{stem}:tests", FAIL, f"rc={{rc}} {{out[-80:]}}")
'''


def register_in_integration_tests(tool_file: str, dry_run: bool = False) -> str:
    """Añade test function + ALL_TESTS entry en integration_tests.py."""
    if is_in_integration_tests(tool_file):
        return "REG-W001"
    try:
        src = INTEGRATION_TESTS.read_text(encoding="utf-8")
        func_name = tool_file_to_func(tool_file)
        stem = tool_file_to_stem(tool_file)

        # 1. Generate test function
        test_func = generate_test_function(tool_file)

        # 2. Insert test function before ALL_TESTS = [
        all_tests_pos = src.find("\nALL_TESTS = [")
        if all_tests_pos == -1:
            return "REG-E001"

        new_src = src[:all_tests_pos] + test_func + src[all_tests_pos:]

        # 3. Find last entry in ALL_TESTS and insert after it
        # Pattern: last "(N, "..." , test_...)" entry
        pattern = r'(\s*\(\d+,\s*"[^"]*",\s*\w+\),)\n(\])'
        next_num = get_next_test_number(new_src)
        new_entry = f'\n    ({next_num}, "{stem}", {func_name}),'
        # Insert before the closing ]
        end_of_list = new_src.rfind("\n]", new_src.find("ALL_TESTS = ["))
        if end_of_list == -1:
            return "REG-E001"
        new_src = new_src[:end_of_list] + new_entry + new_src[end_of_list:]

        if not dry_run:
            INTEGRATION_TESTS.write_text(new_src, encoding="utf-8")
        return "REG-I001"
    except Exception as e:
        return f"REG-E001:{e}"


def register_in_bago_script(tool_file: str, description: str = "", dry_run: bool = False) -> str:
    """Añade routing elif + help entry en el script bago."""
    if is_in_bago_script(tool_file):
        return "REG-W001"
    try:
        src = BAGO_SCRIPT.read_text(encoding="utf-8")
        stem = tool_file_to_stem(tool_file)
        cmd = tool_file_to_cmd(tool_file)

        # Routing block — insert before "elif cmd == "hotspot":"
        routing_anchor = '    elif cmd == "hotspot":'
        if routing_anchor not in src:
            # Try another anchor
            routing_anchor = '    elif cmd == "legacy-fix":'
        if routing_anchor not in src:
            return "REG-E001"

        new_routing = f'''    elif cmd == "{cmd}":
        subprocess.run(
            ["python3", str(TOOLS / "{stem}.py")] + rest,
            cwd=str(BAGO_ROOT.parent)
        )
'''
        src = src.replace(routing_anchor, new_routing + routing_anchor)

        # Help entry — find the last entry in the extra dict
        desc = description or f"tool {stem}: ver --help para uso"
        help_anchor = '"legacy-fix":'
        if help_anchor in src:
            insert_after = src.find(help_anchor)
            eol = src.find("\n", insert_after)
            new_help = f'\n                "{cmd}":        "{desc}",'
            src = src[:eol] + new_help + src[eol:]

        if not dry_run:
            BAGO_SCRIPT.write_text(src, encoding="utf-8")
        return "REG-I001"
    except Exception as e:
        return f"REG-E001:{e}"


def regen_checksums(dry_run: bool = False) -> bool:
    """Regenera CHECKSUMS.sha256 y TREE.txt."""
    if dry_run:
        return True
    try:
        py_files = sorted(TOOLS_DIR.glob("*.py"))
        js_files = sorted(TOOLS_DIR.glob("*.js"))
        all_files = py_files + js_files
        lines = []
        for f in all_files:
            import hashlib
            content = f.read_bytes()
            sha = hashlib.sha256(content).hexdigest()
            rel = f.relative_to(BAGO_ROOT)
            lines.append(f"{sha}  {rel}")
        CHECKSUMS_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")

        # TREE
        all_entries = sorted(BAGO_ROOT.rglob("*"))
        tree_lines = []
        for e in all_entries:
            if ".git" in str(e) or "node_modules" in str(e) or "__pycache__" in str(e):
                continue
            tree_lines.append(str(e.relative_to(BAGO_ROOT)))
        TREE_FILE.write_text("\n".join(tree_lines) + "\n", encoding="utf-8")
        return True
    except Exception:
        return False


def check_registration(tool_file: str) -> dict:
    return {
        "tool": tool_file,
        "integration": is_in_integration_tests(tool_file),
        "routing": is_in_bago_script(tool_file),
        "in_tools": (TOOLS_DIR / tool_file).exists(),
    }


def check_all() -> list:
    results = []
    for f in sorted(TOOLS_DIR.glob("*.py")):
        if f.name in INTERNAL_TOOLS:
            continue
        results.append(check_registration(f.name))
    return results


def cmd_register(tool_file: str, description: str = "", dry_run: bool = False) -> int:
    if not tool_file.endswith(".py"):
        tool_file += ".py"
    filepath = TOOLS_DIR / tool_file
    if not filepath.exists():
        print(f"  [REG-E001] No existe: {tool_file}")
        return 1

    print(f"\n  Registrando: {tool_file}" + (" (DRY-RUN)" if dry_run else ""))
    print("  " + "─" * 46)

    # 1. Integration tests
    code = register_in_integration_tests(tool_file, dry_run=dry_run)
    if code == "REG-I001" or code.startswith("REG-I001"):
        print(f"  [REG-I001] ✅  integration_tests.py → test_{tool_file_to_stem(tool_file)}")
    elif code == "REG-W001":
        print(f"  [REG-W001] ⚠️  integration_tests.py → ya registrado")
    else:
        print(f"  [{code}] ❌  integration_tests.py")

    # 2. Bago script
    code2 = register_in_bago_script(tool_file, description, dry_run=dry_run)
    cmd = tool_file_to_cmd(tool_file)
    if code2 == "REG-I001":
        print(f"  [REG-I001] ✅  bago script → elif cmd == '{cmd}'")
    elif code2 == "REG-W001":
        print(f"  [REG-W001] ⚠️  bago script → ya registrado")
    else:
        print(f"  [{code2}] ❌  bago script")

    # 3. CHECKSUMS
    if not dry_run:
        ok = regen_checksums()
        print(f"  [REG-I001] {'✅' if ok else '❌'}  CHECKSUMS + TREE regenerados")
    else:
        print(f"  [REG-I001] DRY  CHECKSUMS sería regenerado")

    print()
    return 0


def cmd_check_all():
    results = check_all()
    total = len(results)
    fully = sum(1 for r in results if r["integration"] and r["routing"])
    print(f"\n  Tool Registration Status — {fully}/{total} completamente integrados")
    print("  " + "─" * 56)
    for r in results:
        it = "✅" if r["integration"] else "❌"
        rt = "✅" if r["routing"] else "❌"
        print(f"  {r['tool']:35s}  test:{it}  route:{rt}")
    print()


def run_tests():
    import tempfile, os
    results = []

    # Test 1: tool_file_to_cmd
    cmd = tool_file_to_cmd("my_awesome_tool.py")
    ok1 = cmd == "my-awesome-tool"
    results.append(("auto_register:file_to_cmd", ok1, f"cmd={cmd}"))

    # Test 2: tool_file_to_func
    fn = tool_file_to_func("dep_audit.py")
    ok2 = fn == "test_dep_audit"
    results.append(("auto_register:file_to_func", ok2, f"fn={fn}"))

    # Test 3: is_in_integration_tests for known tool
    ok3 = is_in_integration_tests("dep_audit.py")
    results.append(("auto_register:detect_registered", ok3, "dep_audit should be in suite"))

    # Test 4: is_in_bago_script for known routing
    ok4 = is_in_bago_script("dep_audit.py")
    results.append(("auto_register:detect_bago_routing", ok4, "dep_audit should have routing"))

    # Test 5: get_next_test_number
    fake_src = 'ALL_TESTS = [\n    (1, "a", test_a),\n    (2, "b", test_b),\n]'
    n = get_next_test_number(fake_src)
    ok5 = n == 3
    results.append(("auto_register:next_test_number", ok5, f"n={n}"))

    # Test 6: generate_test_function produces valid Python
    import ast
    func_src = generate_test_function("my_tool.py")
    try:
        ast.parse(func_src)
        ok6 = True
    except SyntaxError as e:
        ok6 = False
    results.append(("auto_register:generate_func_valid_python", ok6, ""))

    passed = sum(1 for _, ok, _ in results if ok)
    failed = sum(1 for _, ok, _ in results if not ok)
    for name, ok, detail in results:
        status = "✅" if ok else "❌"
        print(f"  {status}  {name}: {detail}")
    print(f"\n  {passed}/{len(results)} pasaron")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args or "--help" in args or "-h" in args:
        print(__doc__)
        raise SystemExit(0)

    if "--test" in args:
        sys.exit(run_tests())

    dry_run = "--dry-run" in args
    args_clean = [a for a in args if not a.startswith("--")]

    if "--check-all" in args:
        cmd_check_all()
        raise SystemExit(0)

    if "--check" in args:
        i = args.index("--check")
        tool = args[i + 1] if i + 1 < len(args) else ""
        if tool:
            r = check_registration(tool)
            print(f"\n  {tool}: test={r['integration']}  route={r['routing']}")
        raise SystemExit(0)

    if not args_clean:
        print("  Uso: auto_register.py <tool_file.py> [--cmd cmd-name] [--desc 'descripción']")
        raise SystemExit(1)

    tool_file = args_clean[0]
    description = ""
    if "--desc" in args:
        i = args.index("--desc")
        description = args[i + 1] if i + 1 < len(args) else ""

    sys.exit(cmd_register(tool_file, description=description, dry_run=dry_run))
