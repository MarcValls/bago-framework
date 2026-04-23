#!/usr/bin/env python3
"""
permission_fixer — auto-detect and fix file/command permission errors.

Applies the maximum permission correction possible for the current user
(chmod, pip --user, npm prefix) and retries once.  Never escalates to sudo.

Usage:
    from permission_fixer import run_with_permission_fix, ensure_executable
    result = run_with_permission_fix(["npx", "acorn", "file.js"], ...)
"""

import os
import re
import stat
import subprocess
import sys
from pathlib import Path
from typing import Optional

CYAN   = "\033[36m"
YELLOW = "\033[33m"
RESET  = "\033[0m"

# Patterns that indicate a permission error in stderr/stdout
_PERM_RE = re.compile(
    r"(?:Permission denied|EACCES|Operation not permitted"
    r"|cannot open|cannot execute|Access is denied|not permitted)",
    re.IGNORECASE,
)

# Extract file paths mentioned alongside permission errors
_PATH_RE = re.compile(
    r"(?:Permission denied|EACCES)[^\n]*?['\"]?(/[\w./\-_~@]+)['\"]?",
    re.IGNORECASE,
)


# ─── Low-level helpers ────────────────────────────────────────────────────────

def _owned_by_user(path: str) -> bool:
    """Return True if the current user owns the file."""
    try:
        return Path(path).stat().st_uid == os.getuid()
    except Exception:
        return False


def _fix_file_permission(path: str) -> Optional[str]:
    """chmod the file to add the minimum bits needed (owned files only)."""
    try:
        p = Path(path)
        if not p.exists() or not _owned_by_user(path):
            return None
        mode = p.stat().st_mode
        new_mode = mode
        # Executables (scripts, binaries): add +x for user+group
        if p.suffix in (".py", ".sh", ".bash", ".rb", "") and not (mode & stat.S_IXUSR):
            new_mode |= stat.S_IXUSR | stat.S_IXGRP
        # Read: always needed
        if not (mode & stat.S_IRUSR):
            new_mode |= stat.S_IRUSR | stat.S_IRGRP
        # Write: only for directories that need it
        if p.is_dir() and not (mode & stat.S_IWUSR):
            new_mode |= stat.S_IWUSR
        if new_mode != mode:
            os.chmod(path, new_mode)
            bits = ""
            if new_mode & stat.S_IXUSR and not (mode & stat.S_IXUSR): bits += "x"
            if new_mode & stat.S_IRUSR and not (mode & stat.S_IRUSR): bits += "r"
            if new_mode & stat.S_IWUSR and not (mode & stat.S_IWUSR): bits += "w"
            return f"chmod +{bits} {p.name}"
    except Exception:
        pass
    return None


def _fix_npm_acces(cmd: list, stderr: str) -> bool:
    """Route npm/npx to ~/.npm-global prefix to avoid system-dir EACCES."""
    if cmd[0] not in ("npm", "npx"):
        return False
    if "EACCES" not in stderr and "permission denied" not in stderr.lower():
        return False
    npm_global = Path.home() / ".npm-global"
    npm_global.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["npm", "config", "set", "prefix", str(npm_global)],
        capture_output=True,
    )
    # Ensure ~/.npm-global/bin is on PATH for this process
    bin_dir = str(npm_global / "bin")
    if bin_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
    return True


def _fix_pip_user(cmd: list) -> list:
    """Add --user to pip install if missing and permission was denied."""
    exe = Path(cmd[0]).name
    if exe not in ("pip", "pip3") and not exe.startswith("pip"):
        return cmd
    if "install" in cmd and "--user" not in cmd:
        idx = cmd.index("install")
        return cmd[:idx + 1] + ["--user"] + cmd[idx + 1:]
    return cmd


def _extract_denied_paths(text: str) -> list:
    paths = []
    for m in _PATH_RE.finditer(text):
        p = m.group(1).strip("'\"")
        if Path(p).exists():
            paths.append(p)
    return list(set(paths))


# ─── Public API ───────────────────────────────────────────────────────────────

def ensure_executable(path: str) -> bool:
    """Ensure a file owned by the current user has execute permission.

    Returns True if a fix was applied.
    """
    p = Path(path)
    if not p.exists() or not _owned_by_user(path):
        return False
    mode = p.stat().st_mode
    if not (mode & stat.S_IXUSR):
        try:
            os.chmod(path, mode | stat.S_IXUSR | stat.S_IXGRP)
            return True
        except Exception:
            pass
    return False


def run_with_permission_fix(
    cmd: list,
    *,
    capture_output: bool = True,
    text: bool = True,
    timeout: int = 60,
    cwd: Optional[str] = None,
    env=None,
    silent: bool = False,
) -> subprocess.CompletedProcess:
    """Run cmd; on permission failure auto-fix and retry once.

    Fixes attempted (in order):
      1. chmod on files mentioned in the error output (owned by user only)
      2. chmod +x on cmd[0] if it is a script owned by the user
      3. npm prefix → ~/.npm-global  for npm/npx EACCES
      4. pip --user                  for pip install permission errors

    Never uses sudo — only applies fixes the current session can perform.
    Prints what was fixed (unless silent=True).

    Returns the CompletedProcess of the final attempt.
    """
    # First attempt
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=text,
            timeout=timeout,
            cwd=cwd,
            env=env,
        )
    except PermissionError as exc:
        # Command itself not executable — try to fix and retry
        target = cmd[0]
        fixed = ensure_executable(target)
        if fixed and not silent:
            print(f"  {CYAN}🔧 Permiso auto-corregido: chmod +x {Path(target).name}{RESET}")
        if fixed:
            try:
                result = subprocess.run(
                    cmd, capture_output=capture_output, text=text,
                    timeout=timeout, cwd=cwd, env=env,
                )
                if not silent:
                    _print_retry_result(result)
                return result
            except Exception:
                pass
        if not silent:
            _print_sudo_hint(cmd)
        raise

    if result.returncode == 0:
        return result

    # Check if exit was due to permissions
    combined = (result.stderr or "") + (result.stdout or "")
    if not _PERM_RE.search(combined) and result.returncode not in (13, 126, 127):
        return result  # Non-permission failure — return as-is

    if not silent:
        print(f"  {YELLOW}⚠  Permiso denegado ejecutando: {cmd[0]}{RESET}")

    fixes: list[str] = []
    modified_cmd = list(cmd)

    # Fix 1: chmod on explicitly mentioned paths
    for p in _extract_denied_paths(combined):
        fix = _fix_file_permission(p)
        if fix:
            fixes.append(fix)

    # Fix 2: chmod +x on the command itself
    if Path(cmd[0]).exists() and _owned_by_user(cmd[0]):
        if ensure_executable(cmd[0]):
            fixes.append(f"chmod +x {Path(cmd[0]).name}")

    # Fix 3: npm EACCES
    if _fix_npm_acces(cmd, combined):
        fixes.append("npm prefix → ~/.npm-global")

    # Fix 4: pip --user
    pip_cmd = _fix_pip_user(cmd)
    if pip_cmd != cmd:
        modified_cmd = pip_cmd
        fixes.append("pip --user")

    if not fixes:
        if not silent:
            _print_sudo_hint(cmd)
        return result

    if not silent:
        print(f"  {CYAN}🔧 Auto-corrigiendo: {', '.join(fixes)}{RESET}")

    # Retry
    result2 = subprocess.run(
        modified_cmd,
        capture_output=capture_output,
        text=text,
        timeout=timeout,
        cwd=cwd,
        env=env,
    )

    if not silent:
        _print_retry_result(result2)

    return result2


def _print_retry_result(r: subprocess.CompletedProcess) -> None:
    if r.returncode == 0:
        print(f"  {CYAN}✅ Reintento exitoso{RESET}")
    else:
        print(f"  {YELLOW}⚠  Reintento fallido — puede requerir privilegios adicionales{RESET}")


def _print_sudo_hint(cmd: list) -> None:
    exe = Path(cmd[0]).name
    print(
        f"  {YELLOW}ℹ  No auto-corregible sin sudo (no aplicado por seguridad).{RESET}\n"
        f"     Si necesitas privilegios: sudo {exe} {' '.join(cmd[1:3])} ..."
    )


# ─── Tests ────────────────────────────────────────────────────────────────────

def run_tests():
    import tempfile, shutil
    print("Ejecutando tests de permission_fixer.py...")
    errors = 0

    def ok(n):   print(f"  OK: {n}")
    def fail(n, m): nonlocal errors; errors += 1; print(f"  FAIL: {n} — {m}")

    tmp = Path(tempfile.mkdtemp())

    # T1: ensure_executable on a non-exec file
    f1 = tmp / "script.sh"
    f1.write_text("#!/bin/bash\necho hi\n")
    os.chmod(f1, 0o644)
    fixed = ensure_executable(str(f1))
    if fixed and (f1.stat().st_mode & stat.S_IXUSR):
        ok("perm:ensure_executable")
    else:
        fail("perm:ensure_executable", f"fixed={fixed}, mode={oct(f1.stat().st_mode)}")

    # T2: ensure_executable on already-exec file → no change reported
    fixed2 = ensure_executable(str(f1))
    if not fixed2:
        ok("perm:ensure_executable_noop")
    else:
        fail("perm:ensure_executable_noop", "should have been noop")

    # T3: run_with_permission_fix on a normal command → just runs it
    r = run_with_permission_fix(["echo", "hello"], silent=True)
    if r.returncode == 0 and "hello" in r.stdout:
        ok("perm:normal_command")
    else:
        fail("perm:normal_command", f"rc={r.returncode}")

    # T4: run_with_permission_fix auto-fix chmod on non-exec script
    script = tmp / "myscript.py"
    script.write_text("#!/usr/bin/env python3\nprint('ok')\n")
    os.chmod(script, 0o644)
    # Simulate: call with script as cmd[0], provide a workaround path
    # (we can't easily trigger PermissionError in test without being root)
    # Just verify _fix_file_permission works
    fix_desc = _fix_file_permission(str(script))
    if fix_desc and "x" in fix_desc and (script.stat().st_mode & stat.S_IXUSR):
        ok("perm:fix_file_permission")
    else:
        fail("perm:fix_file_permission", f"fix={fix_desc}, mode={oct(script.stat().st_mode)}")

    # T5: _fix_pip_user adds --user
    original = ["pip3", "install", "requests"]
    fixed_cmd = _fix_pip_user(original)
    if "--user" in fixed_cmd:
        ok("perm:pip_user_flag")
    else:
        fail("perm:pip_user_flag", str(fixed_cmd))

    # T6: _fix_pip_user is idempotent (already has --user)
    already = ["pip3", "install", "--user", "requests"]
    same = _fix_pip_user(already)
    if same.count("--user") == 1:
        ok("perm:pip_user_idempotent")
    else:
        fail("perm:pip_user_idempotent", str(same))

    shutil.rmtree(tmp)
    total = 6; passed = total - errors
    print(f"\n  {passed}/{total} tests pasaron")
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    if "--test" in sys.argv:
        run_tests()
    else:
        print("permission_fixer — uso: import run_with_permission_fix, ensure_executable")
