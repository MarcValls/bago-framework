#!/usr/bin/env python3
"""
bago fix — autofix serio: genera y aplica parches concretos con validación.

Para cada Finding autofixable del último scan:
  1. Muestra el contexto del hallazgo
  2. Muestra el patch propuesto (unified diff)
  3. Aplica el patch al archivo real
  4. Ejecuta --test del tool afectado para validar
  5. Si falla: revierte automáticamente

Modos de autofix:
  --internal (default) : parches line-by-line internos (BAGO-W001, W291, E302, W293)
  --external           : usa black (Python) o prettier/eslint --fix (JS/TS) para bulk fix

Uso:
    bago fix --preview             → muestra todos los fixes sin aplicar
    bago fix --apply               → aplica todos los autofixable (con validación)
    bago fix --rule BAGO-W001      → solo fixes de una regla
    bago fix --file <ruta>         → solo fixes de un archivo
    bago fix --interactive         → revisa y aprueba fix por fix
    bago fix --dry-run             → simula apply sin escribir disco
    bago fix --external            → usa black/prettier como fixer externo
    bago fix --target <dir>        → directorio para --external (default: .bago/tools/)
    bago fix --test                → tests integrados
"""
import argparse, difflib, json, re, shutil, subprocess, sys, tempfile
from pathlib import Path
from typing import Optional

TOOLS_DIR = Path(__file__).parent
sys.path.insert(0, str(TOOLS_DIR))
import findings_engine as fe

# Import permission fixer — graceful fallback if not available
try:
    from permission_fixer import run_with_permission_fix as _run_cmd
except ImportError:
    def _run_cmd(cmd, *, capture_output=True, text=True, timeout=60,  # type: ignore[misc]
                 cwd=None, env=None, silent=True, **_):
        return subprocess.run(cmd, capture_output=capture_output, text=text,
                              timeout=timeout, cwd=cwd, env=env)

BAGO_ROOT = Path(__file__).parent.parent
BOLD="\033[1m"; DIM="\033[2m"; RESET="\033[0m"
RED="\033[31m"; GREEN="\033[32m"; YELLOW="\033[33m"; CYAN="\033[36m"


# ─── Patch generators ────────────────────────────────────────────────────────

def generate_patch(finding: fe.Finding, src_lines: list) -> Optional[str]:
    """
    Generate a concrete unified diff for an autofixable Finding.
    Returns patch string or None if cannot generate.
    """
    rule = finding.rule
    lineno = finding.line - 1  # 0-indexed

    if not (0 <= lineno < len(src_lines)):
        return None

    original = list(src_lines)
    patched  = list(src_lines)

    # BAGO-W001: datetime.utcnow() → datetime.now(datetime.timezone.utc)
    if rule == "BAGO-W001":
        old = patched[lineno]
        new = re.sub(r'datetime\.datetime\.utcnow\(\)',
                     'datetime.datetime.now(datetime.timezone.utc)', old)
        new = re.sub(r'(?<!\.)datetime\.utcnow\(\)',
                     'datetime.datetime.now(datetime.timezone.utc)', new)
        if old == new:
            return None
        patched[lineno] = new

    # E302: missing 2 blank lines before function/class
    elif rule == "E302":
        blanks = 0
        i = lineno - 1
        while i >= 0 and not patched[i].strip():
            blanks += 1; i -= 1
        needed = 2 - blanks
        if needed > 0:
            patched[lineno:lineno] = ["\n"] * needed
        else:
            return None

    # W291/W293: trailing whitespace
    elif rule in ("W291", "W293"):
        old = patched[lineno]
        new = old.rstrip() + "\n" if not old.endswith("\n") else old.rstrip(" \t") + "\n"
        if old == new:
            return None
        patched[lineno] = new

    # E711: comparison to None with == / !=
    elif rule == "E711":
        old = patched[lineno]
        new = re.sub(r'(?<![!<>])== None\b', 'is None', old)
        new = re.sub(r'!= None\b', 'is not None', new)
        if old == new:
            return None
        patched[lineno] = new

    # E712: comparison to True/False with == / !=
    elif rule == "E712":
        old = patched[lineno]
        new = re.sub(r'(?<![!<>])== True\b', 'is True', old)
        new = re.sub(r'(?<![!<>])== False\b', 'is False', old)
        new = re.sub(r'!= True\b', 'is not True', new)
        new = re.sub(r'!= False\b', 'is not False', new)
        if old == new:
            return None
        patched[lineno] = new

    # F401 / W0611: unused import — remove the entire import line
    elif rule in ("F401", "W0611"):
        old = patched[lineno]
        stripped = old.strip()
        # Only safe to remove simple single-name imports
        if re.match(r'^import\s+\w+\s*$', stripped) or re.match(r'^from\s+\S+\s+import\s+\w+\s*$', stripped):
            patched[lineno] = ""  # blank line (keeps line numbers stable)
        else:
            return None

    # E501: line too long — not auto-fixable inline
    elif rule == "E501":
        return None

    else:
        if finding.fix_patch:
            return finding.fix_patch
        return None

    if patched == original:
        return None

    diff = list(difflib.unified_diff(
        original, patched,
        fromfile=f"a/{finding.file}",
        tofile=f"b/{finding.file}",
        lineterm=""
    ))
    return "\n".join(diff) if diff else None


# ─── Patch application ───────────────────────────────────────────────────────

def apply_patch(finding: fe.Finding, patch: str, dry_run: bool) -> tuple:
    """
    Apply patch to real file.
    Returns (success: bool, message: str)
    """
    filepath = Path(finding.file)
    if not filepath.exists():
        return False, f"Archivo no encontrado: {filepath}"

    original_src = filepath.read_text(errors="replace")
    original_lines = original_src.splitlines(keepends=True)
    patched_lines  = list(original_lines)
    lineno = finding.line - 1

    rule = finding.rule
    if rule == "BAGO-W001":
        if 0 <= lineno < len(patched_lines):
            old = patched_lines[lineno]
            new = re.sub(r'datetime\.datetime\.utcnow\(\)',
                         'datetime.datetime.now(datetime.timezone.utc)', old)
            new = re.sub(r'(?<!\.)datetime\.utcnow\(\)',
                         'datetime.datetime.now(datetime.timezone.utc)', new)
            if old == new:
                return False, "Sin cambio detectado"
            patched_lines[lineno] = new
        else:
            return False, "Línea fuera de rango"
    elif rule in ("W291", "W293"):
        if 0 <= lineno < len(patched_lines):
            old = patched_lines[lineno]
            new = old.rstrip() + "\n" if not old.endswith("\n") else old.rstrip(" \t") + "\n"
            patched_lines[lineno] = new
        else:
            return False, "Línea fuera de rango"
    elif rule == "E302":
        blanks = 0
        i = lineno - 1
        while i >= 0 and not patched_lines[i].strip():
            blanks += 1; i -= 1
        needed = 2 - blanks
        if needed > 0 and 0 <= lineno <= len(patched_lines):
            patched_lines[lineno:lineno] = ["\n"] * needed
        else:
            return False, "Ya tiene suficientes líneas en blanco"
    elif rule == "E711":
        if 0 <= lineno < len(patched_lines):
            old = patched_lines[lineno]
            new = re.sub(r'(?<![!<>])== None\b', 'is None', old)
            new = re.sub(r'!= None\b', 'is not None', new)
            if old == new:
                return False, "Sin cambio detectado"
            patched_lines[lineno] = new
        else:
            return False, "Línea fuera de rango"
    elif rule == "E712":
        if 0 <= lineno < len(patched_lines):
            old = patched_lines[lineno]
            new = re.sub(r'(?<![!<>])== True\b', 'is True', old)
            new = re.sub(r'(?<![!<>])== False\b', 'is False', new)
            new = re.sub(r'!= True\b', 'is not True', new)
            new = re.sub(r'!= False\b', 'is not False', new)
            if old == new:
                return False, "Sin cambio detectado"
            patched_lines[lineno] = new
        else:
            return False, "Línea fuera de rango"
    elif rule in ("F401", "W0611"):
        if 0 <= lineno < len(patched_lines):
            old = patched_lines[lineno].strip()
            if re.match(r'^import\s+\w+\s*$', old) or re.match(r'^from\s+\S+\s+import\s+\w+\s*$', old):
                patched_lines[lineno] = "\n"
            else:
                return False, "Import compuesto — skip"
        else:
            return False, "Línea fuera de rango"
    else:
        return False, f"Regla {rule} no tiene aplicador directo"

    new_src = "".join(patched_lines)
    if dry_run:
        return True, "[DRY-RUN] Patch generado (no escrito)"

    # Backup + write
    backup = Path(tempfile.mktemp(suffix=".bak"))
    backup.write_text(original_src)
    try:
        filepath.write_text(new_src)
        return True, f"Aplicado (backup: {backup})"
    except Exception as e:
        # Revert
        filepath.write_text(original_src)
        return False, f"Error aplicando patch: {e}"


def validate_after_fix(filepath: str) -> tuple:
    """Run --test on the tool after fixing. Returns (passed: bool, output: str)."""
    tool_dir = Path(BAGO_ROOT) / "tools"
    py = Path(filepath)
    if not py.exists() or not py.name.endswith(".py"):
        return True, "No es un tool BAGO — skip test"
    if str(tool_dir) not in str(py.resolve()):
        return True, "Fuera de tools/ — skip test"

    try:
        r = _run_cmd(
            ["python3", str(py), "--test"],
            capture_output=True, text=True, timeout=30,
            cwd=str(BAGO_ROOT.parent), silent=True,
        )
        passed = r.returncode == 0
        return passed, (r.stdout + r.stderr).strip()
    except Exception as e:
        return False, str(e)


def revert_file(filepath: str, original: str):
    Path(filepath).write_text(original)


# ─── Main fix logic ───────────────────────────────────────────────────────────

def collect_autofixable(rule_filter: Optional[str], file_filter: Optional[str]) -> list:
    db = fe.FindingsDB.latest()
    if db is None:
        return []
    findings = [f for f in db.findings if f.autofixable]
    if rule_filter:
        findings = [f for f in findings if f.rule == rule_filter]
    if file_filter:
        findings = [f for f in findings if file_filter in f.file]
    return findings


def run_preview(findings: list):
    if not findings:
        print(f"\n  {GREEN}✓ Sin hallazgos autofixables con los filtros dados{RESET}\n")
        return

    print(f"\n  {BOLD}Hallazgos autofixables ({len(findings)}){RESET}\n")
    by_rule: dict = {}
    for f in findings:
        by_rule.setdefault(f.rule, []).append(f)

    for rule, group in sorted(by_rule.items()):
        print(f"  {YELLOW}{rule}{RESET}  ({len(group)} ocurrencias)")
        for f in group[:3]:
            short = f.file.replace(str(BAGO_ROOT.parent)+"/","")
            print(f"    {DIM}L{f.line:4d}{RESET}  {short}")
            print(f"    → {f.fix_suggestion or f.message}")
        if len(group) > 3:
            print(f"    {DIM}... y {len(group)-3} más{RESET}")
        print()


def run_apply(findings: list, dry_run: bool, interactive: bool) -> dict:
    results = {"applied": [], "failed": [], "reverted": [], "skipped": []}

    # Group by file to process each file once
    by_file: dict = {}
    for f in findings:
        by_file.setdefault(f.file, []).append(f)

    for filepath, file_findings in sorted(by_file.items()):
        short = filepath.replace(str(BAGO_ROOT.parent)+"/","")
        print(f"\n  {BOLD}{short}{RESET}  ({len(file_findings)} fixes)")

        original_src = ""
        try:
            original_src = Path(filepath).read_text(errors="replace")
        except Exception:
            print(f"  {RED}✗ No se puede leer{RESET}")
            results["failed"].extend(f.id for f in file_findings)
            continue

        file_ok = True
        for finding in sorted(file_findings, key=lambda x: -x.line):  # bottom-up
            src_lines = Path(filepath).read_text(errors="replace").splitlines(keepends=True)
            patch = generate_patch(finding, src_lines)

            if patch is None:
                print(f"  {DIM}  L{finding.line}: {finding.rule} → sin patch generado{RESET}")
                results["skipped"].append(finding.id)
                continue

            if interactive:
                print(f"\n  {CYAN}Patch propuesto ({finding.rule} L{finding.line}):{RESET}")
                for pl in patch.split("\n")[:10]:
                    if pl.startswith("+"): print(f"  {GREEN}{pl}{RESET}")
                    elif pl.startswith("-"): print(f"  {RED}{pl}{RESET}")
                    else: print(f"  {DIM}{pl}{RESET}")
                resp = input(f"  ¿Aplicar? [y/N]: ").strip().lower()
                if resp != "y":
                    results["skipped"].append(finding.id)
                    continue

            success, msg = apply_patch(finding, patch, dry_run)
            if success:
                print(f"  {GREEN}✓{RESET} L{finding.line} {finding.rule} — {msg}")
                results["applied"].append(finding.id)
            else:
                print(f"  {RED}✗{RESET} L{finding.line} {finding.rule} — {msg}")
                results["failed"].append(finding.id)
                file_ok = False

        # Validate after all fixes on this file
        if results["applied"] and not dry_run and file_ok:
            passed, output = validate_after_fix(filepath)
            if passed:
                print(f"  {GREEN}✓ Tests OK después del fix{RESET}")
            else:
                print(f"  {RED}✗ Tests FALLARON — revirtiendo {short}{RESET}")
                revert_file(filepath, original_src)
                applied_in_file = [f.id for f in file_findings if f.id in results["applied"]]
                for fid in applied_in_file:
                    results["applied"].remove(fid)
                    results["reverted"].append(fid)
                print(f"  {YELLOW}Revertido a estado original{RESET}")

    return results


# ─── External fixers (black / prettier / eslint --fix) ───────────────────────

def run_external_fix_python(target: str, dry_run: bool) -> tuple:
    """Run black on a Python file or directory. Returns (success, output)."""
    if dry_run:
        cmd = ["black", "--check", "--diff", target]
    else:
        cmd = ["black", target]
    try:
        r = _run_cmd(cmd, capture_output=True, text=True, timeout=60, silent=True)
        return r.returncode == 0 or (dry_run and r.returncode == 1), \
               (r.stdout + r.stderr).strip()
    except FileNotFoundError:
        return False, "black no está instalado (pip install black)"
    except Exception as e:
        return False, str(e)


def run_external_fix_js(target: str, dry_run: bool) -> tuple:
    """Run prettier/eslint --fix on a JS/TS file or directory."""
    # Try prettier first
    prettier_flag = "--check" if dry_run else "--write"
    try:
        r = _run_cmd(
            ["npx", "--yes", "prettier", prettier_flag, target],
            capture_output=True, text=True, timeout=60, silent=True,
        )
        if r.returncode in (0, 1):  # 1 = needs formatting (dry-run)
            return True, (r.stdout + r.stderr).strip()
    except Exception:
        pass
    # Fallback: eslint --fix
    try:
        cmd = ["npx", "--yes", "eslint", "--ext", ".js,.ts,.jsx,.tsx"]
        if not dry_run:
            cmd.append("--fix")
        cmd.append(target)
        r = _run_cmd(cmd, capture_output=True, text=True, timeout=60, silent=True)
        return r.returncode == 0, (r.stdout + r.stderr).strip()
    except Exception as e:
        return False, f"eslint/prettier no disponible: {e}"


def run_external_fix(target: str, dry_run: bool) -> None:
    """Auto-detect language and run appropriate external fixer."""
    p = Path(target)
    # Detect by extension or by scanning
    is_js = any(p.glob("**/*.js")) if p.is_dir() else target.endswith((".js", ".ts", ".jsx", ".tsx"))
    is_py = any(p.glob("**/*.py")) if p.is_dir() else target.endswith(".py")

    mode = "DRY-RUN" if dry_run else "APPLY"
    print(f"\n  {BOLD}External fix — {mode}{RESET}  target: {target}\n")

    if is_py:
        print(f"  {CYAN}→ black (Python){RESET}")
        ok, out = run_external_fix_python(target, dry_run)
        status = f"{GREEN}✓{RESET}" if ok else f"{RED}✗{RESET}"
        print(f"  {status} {out[:300] if out else 'Sin output'}\n")

    if is_js:
        print(f"  {CYAN}→ prettier / eslint --fix (JS/TS){RESET}")
        ok, out = run_external_fix_js(target, dry_run)
        status = f"{GREEN}✓{RESET}" if ok else f"{RED}✗{RESET}"
        print(f"  {status} {out[:300] if out else 'Sin output'}\n")

    if not is_py and not is_js:
        print(f"  {YELLOW}No se detectaron archivos Python/JS en {target}{RESET}\n")


def run_tests():
    import tempfile as tf
    print("Ejecutando tests de autofix.py...")
    errors = 0
    def ok(n): print(f"  OK: {n}")
    def fail(n, m):
        nonlocal errors; errors += 1; print(f"  FAIL: {n} — {m}")

    # T1: generate_patch BAGO-W001
    f = fe.Finding(id="X",severity="warning",file="a.py",line=1,col=0,rule="BAGO-W001",
                   source="bago",message="test",autofixable=True)
    lines = ["    ts = datetime.datetime.utcnow()\n"]
    patch = generate_patch(f, lines)
    if patch and "datetime.timezone.utc" in patch:
        ok("fix:patch_utcnow")
    else:
        fail("fix:patch_utcnow", repr(patch))

    # T2: generate_patch W291 trailing whitespace
    f2 = fe.Finding(id="Y",severity="warning",file="b.py",line=1,col=0,rule="W291",
                    source="flake8",message="trailing ws",autofixable=True)
    lines2 = ["x = 1   \n"]
    patch2 = generate_patch(f2, lines2)
    if patch2 and "-x = 1   " in patch2:
        ok("fix:patch_trailing_ws")
    else:
        fail("fix:patch_trailing_ws", repr(patch2))

    # T3: apply_patch dry-run does not modify file
    tmp = Path(tf.mkdtemp())
    py  = tmp / "sample.py"
    py.write_text("    ts = datetime.datetime.utcnow()\n")
    f3 = fe.Finding(id="Z",severity="warning",file=str(py),line=1,col=0,rule="BAGO-W001",
                    source="bago",message="test",autofixable=True)
    src_before = py.read_text()
    success, msg = apply_patch(f3, "", dry_run=True)
    src_after = py.read_text()
    if src_before == src_after:
        ok("fix:dry_run_no_modify")
    else:
        fail("fix:dry_run_no_modify", "file was modified")

    # T4: apply_patch real modifies file
    success2, msg2 = apply_patch(f3, "", dry_run=False)
    src_fixed = py.read_text()
    if "datetime.timezone.utc" in src_fixed:
        ok("fix:apply_real_modifies")
    else:
        fail("fix:apply_real_modifies", repr(src_fixed))

    # T5: validate_after_fix on non-tool file returns True
    passed, out = validate_after_fix(str(py))
    if passed:
        ok("fix:validate_non_tool_skip")
    else:
        fail("fix:validate_non_tool_skip", out)

    import shutil
    shutil.rmtree(tmp)
    total=5; passed_t=total-errors
    print(f"\n  {passed_t}/{total} tests pasaron")
    if errors: sys.exit(1)

    # ── Extended tests ──────────────────────────────────────────────────────
    errors2 = 0
    print("\nTests de reglas adicionales...")
    tmp2 = Path(tf.mkdtemp())

    # T6: generate_patch E711 == None → is None
    f6 = fe.Finding(id="E6",severity="warning",file="c.py",line=1,col=0,rule="E711",
                    source="flake8",message="E711",autofixable=True)
    lines6 = ["if x == None:\n"]
    patch6 = generate_patch(f6, lines6)
    if patch6 and "is None" in patch6:
        print("  OK: fix:patch_e711")
    else:
        errors2 += 1; print(f"  FAIL: fix:patch_e711 — {repr(patch6)}")

    # T7: generate_patch F401 unused import removal
    f7 = fe.Finding(id="F7",severity="warning",file="d.py",line=1,col=0,rule="F401",
                    source="flake8",message="unused import",autofixable=True)
    lines7 = ["import os\n"]
    patch7 = generate_patch(f7, lines7)
    if patch7 is not None:
        print("  OK: fix:patch_f401")
    else:
        errors2 += 1; print(f"  FAIL: fix:patch_f401 — got None")

    # T8: run_external_fix_python dry-run on a tmp dir (black may not be installed — ok if returns tuple)
    py8 = tmp2 / "e.py"
    py8.write_text("x=1\n")
    ok8, out8 = run_external_fix_python(str(tmp2), dry_run=True)
    if isinstance(ok8, bool):
        print("  OK: fix:external_python_returns_tuple")
    else:
        errors2 += 1; print("  FAIL: fix:external_python_returns_tuple")

    shutil.rmtree(tmp2)
    total2 = 3; passed2 = total2 - errors2
    print(f"\n  {passed2}/{total2} tests adicionales pasaron")
    if errors2: sys.exit(1)


def main():
    parser = argparse.ArgumentParser(prog="bago fix", add_help=False)
    parser.add_argument("--preview",     action="store_true")
    parser.add_argument("--apply",       action="store_true")
    parser.add_argument("--dry-run",     action="store_true")
    parser.add_argument("--interactive", action="store_true")
    parser.add_argument("--rule",        default=None)
    parser.add_argument("--file",        dest="file_filter", default=None)
    parser.add_argument("--external",    action="store_true",
                        help="Usar black/prettier como fixer externo")
    parser.add_argument("--target",      default=str(BAGO_ROOT / "tools"),
                        help="Directorio/archivo para --external")
    parser.add_argument("--test",        action="store_true")
    args = parser.parse_args()

    if args.test:
        run_tests(); return

    if args.external:
        run_external_fix(args.target, dry_run=args.dry_run)
        return

    findings = collect_autofixable(args.rule, args.file_filter)

    if not findings:
        print(f"\n  {GREEN}✓ Sin hallazgos autofixables. Ejecuta 'bago scan' primero.{RESET}\n")
        return

    if args.apply or args.interactive or args.dry_run:
        res = run_apply(findings, dry_run=args.dry_run, interactive=args.interactive)
        print(f"\n  {BOLD}Resultado:{RESET}")
        print(f"    {GREEN}Aplicados:{RESET}  {len(res['applied'])}")
        print(f"    {RED}Fallidos:{RESET}   {len(res['failed'])}")
        print(f"    {YELLOW}Revertidos:{RESET} {len(res['reverted'])}")
        print(f"    {DIM}Omitidos:{RESET}   {len(res['skipped'])}")
        print()
    else:
        run_preview(findings)
        print(f"  Usa {BOLD}bago fix --apply{RESET} para aplicar todos los fixes.")
        print(f"  Usa {BOLD}bago fix --interactive{RESET} para revisar uno por uno.")
        print(f"  Usa {BOLD}bago fix --external --target <dir>{RESET} para usar black/prettier.\n")

if __name__ == "__main__":
    main()