#!/usr/bin/env python3
"""
bago permission-check — Verifica y corrige permisos de todos los ejecutables BAGO.

Garantiza que todos los tools, scripts y ejecutables del framework tengan
los permisos mínimos necesarios para ejecutarse correctamente.

Checks:
  - .bago/tools/*.py   → chmod +x (755)
  - .bago/tools/*.js   → chmod +x (755)
  - bago (script)      → chmod +x (755)
  - .bago/tools/*.sh   → chmod +x (755)  (si existen)
  - *.command          → chmod +x (755)  (macOS launchers)

Usage:
    bago permission-check           verificar y aplicar permisos
    bago permission-check --check   solo verificar (sin aplicar)
    bago permission-check --verbose  mostrar todos los archivos
    bago permission-check --test    ejecutar self-tests
"""
from __future__ import annotations

import argparse
import os
import stat
import sys
from pathlib import Path

BAGO_ROOT = Path(__file__).resolve().parent.parent
PACK_ROOT = BAGO_ROOT.parent
TOOLS     = BAGO_ROOT / "tools"

# ── ANSI ─────────────────────────────────────────────────────────────────────
_TTY   = sys.stdout.isatty()
GREEN  = "\033[32m" if _TTY else ""
YELLOW = "\033[33m" if _TTY else ""
RED    = "\033[31m" if _TTY else ""
BOLD   = "\033[1m"  if _TTY else ""
DIM    = "\033[2m"  if _TTY else ""
RESET  = "\033[0m"  if _TTY else ""

# ── Targets ───────────────────────────────────────────────────────────────────

def _collect_targets() -> list:
    """Return list of (Path, description) that should be executable."""
    targets = []

    # Main bago script
    bago_script = PACK_ROOT / "bago"
    if bago_script.exists():
        targets.append((bago_script, "bago script principal"))

    # All .py and .js in tools/
    for pattern in ("*.py", "*.js", "*.sh"):
        for p in sorted(TOOLS.glob(pattern)):
            targets.append((p, f"tool {p.name}"))

    # macOS launcher .command files
    for p in sorted(PACK_ROOT.glob("*.command")):
        targets.append((p, f"launcher {p.name}"))

    # setup scripts
    for name in ("setup-launcher.sh", "_finish_session.sh"):
        p = PACK_ROOT / name
        if p.exists():
            targets.append((p, f"script {name}"))

    return targets


def _is_executable(path: Path) -> bool:
    """Return True if the file has +x bit for owner."""
    s = path.stat()
    return bool(s.st_mode & stat.S_IXUSR)


def _make_executable(path: Path) -> None:
    """Add +x for owner, group, others."""
    s = path.stat()
    new_mode = s.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    os.chmod(path, new_mode)


# ── Main logic ────────────────────────────────────────────────────────────────

def run_check(check_only: bool = False, verbose: bool = False) -> dict:
    """Scan targets and optionally fix permissions.

    Returns {ok, fixed, failed, already_ok}.
    """
    targets = _collect_targets()
    results = {"ok": 0, "fixed": 0, "failed": 0, "already_ok": 0, "details": []}

    for path, desc in targets:
        executable = _is_executable(path)
        if executable:
            results["already_ok"] += 1
            results["ok"] += 1
            if verbose:
                results["details"].append(("ok", path, desc))
        elif check_only:
            results["failed"] += 1
            results["details"].append(("missing", path, desc))
        else:
            try:
                _make_executable(path)
                results["fixed"] += 1
                results["ok"] += 1
                results["details"].append(("fixed", path, desc))
            except OSError as e:
                results["failed"] += 1
                results["details"].append(("error", path, f"{desc} — {e}"))

    return results


def main() -> int:
    p = argparse.ArgumentParser(
        description="BAGO permission-check — verifica y corrige permisos de ejecutables",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--check",   action="store_true", help="Solo verificar, no aplicar cambios")
    p.add_argument("--verbose", action="store_true", help="Mostrar todos los archivos, no solo cambios")
    p.add_argument("--test",    action="store_true", help="Ejecutar self-tests")
    args = p.parse_args()

    if args.test:
        return _run_tests()

    check_only = args.check
    results = run_check(check_only=check_only, verbose=args.verbose)

    # Print header
    mode_str = f"{YELLOW}CHECK{RESET} (solo verificar)" if check_only else f"{GREEN}FIX{RESET} (aplicando cambios)"
    print(f"\n  {BOLD}bago permission-check{RESET} — {mode_str}\n")

    # Print details
    for status, path, desc in results["details"]:
        if status == "ok":
            print(f"  {GREEN}✓{RESET} {DIM}{desc}{RESET}")
        elif status == "fixed":
            print(f"  {GREEN}+ chmod +x{RESET}  {path.name}  {DIM}({desc}){RESET}")
        elif status == "missing":
            print(f"  {YELLOW}⚠ sin +x{RESET}   {path.name}  {DIM}({desc}){RESET}")
        elif status == "error":
            print(f"  {RED}✗ error{RESET}     {path.name}  {DIM}({desc}){RESET}")

    # Summary
    total = results["ok"] + results["failed"]
    print(f"\n  {BOLD}Resumen:{RESET}  {total} archivos procesados")
    print(f"  {GREEN}✓ Ya correctos: {results['already_ok']}{RESET}")
    if not check_only:
        print(f"  {GREEN}+ Corregidos:   {results['fixed']}{RESET}")
    if results["failed"]:
        print(f"  {RED}✗ Con problemas:{results['failed']}{RESET}")
    print()

    return 1 if results["failed"] > 0 else 0


# ── Self-tests ────────────────────────────────────────────────────────────────

def _run_tests() -> int:
    import tempfile
    import shutil

    errors = 0
    print("\nTests de permission_check.py...")

    def ok(name: str)          -> None: print(f"  OK: {name}")
    def fail(name: str, d: str)-> None:
        nonlocal errors; errors += 1; print(f"  FAIL: {name} — {d}")

    # T1: _is_executable / _make_executable
    tmp = Path(tempfile.mkdtemp())
    f1 = tmp / "script.py"
    f1.write_text("#!/usr/bin/env python3\nprint('hi')\n")
    os.chmod(f1, 0o644)  # no +x
    if not _is_executable(f1):
        ok("perm:detect_non_executable")
    else:
        fail("perm:detect_non_executable", "chmod 644 but reported executable")
    _make_executable(f1)
    if _is_executable(f1):
        ok("perm:make_executable")
    else:
        fail("perm:make_executable", "still not executable after chmod")

    # T2: run_check --check-only (no changes)
    f2 = tmp / "noexec.py"
    f2.write_text("pass\n")
    os.chmod(f2, 0o600)

    # Monkey-patch _collect_targets for this test
    import permission_check as _self
    orig_collect = _self._collect_targets
    _self._collect_targets = lambda: [(f2, "test file")]

    res = _self.run_check(check_only=True)
    _self._collect_targets = orig_collect

    if res["failed"] == 1 and res["fixed"] == 0:
        ok("perm:check_only_no_fix")
    else:
        fail("perm:check_only_no_fix", str(res))

    # T3: run_check fixes permissions
    _self._collect_targets = lambda: [(f2, "test file")]
    res2 = _self.run_check(check_only=False)
    _self._collect_targets = orig_collect

    if res2["fixed"] == 1 and res2["failed"] == 0 and _is_executable(f2):
        ok("perm:auto_fix")
    else:
        fail("perm:auto_fix", str(res2))

    # T4: bago script is in target list
    real_targets = _collect_targets()
    bago_script = PACK_ROOT / "bago"
    if bago_script.exists():
        paths = [p for p, _ in real_targets]
        if bago_script in paths:
            ok("perm:bago_script_targeted")
        else:
            fail("perm:bago_script_targeted", "bago script not in collect_targets()")
    else:
        ok("perm:bago_script_targeted")  # skip if not present

    # T5: tools/*.py all in target list
    py_tools = list(TOOLS.glob("*.py"))
    if py_tools:
        real_paths = {p for p, _ in real_targets}
        covered = [t for t in py_tools if t in real_paths]
        if len(covered) == len(py_tools):
            ok("perm:all_py_tools_targeted")
        else:
            missing = [t.name for t in py_tools if t not in real_paths]
            fail("perm:all_py_tools_targeted", f"missing: {missing[:3]}")
    else:
        ok("perm:all_py_tools_targeted")

    shutil.rmtree(tmp, ignore_errors=True)

    total  = 5
    passed = total - errors
    print(f"\n  {passed}/{total} tests pasaron")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
