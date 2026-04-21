#!/usr/bin/env python3
"""
bago scan — análisis unificado de código con modelo de hallazgos canónico.

Ejecuta todos los linters disponibles sobre el directorio objetivo,
agrega los resultados en un modelo Finding unificado y los persiste.

Uso:
    bago scan                          → escanea .bago/tools/ con todos los linters disponibles
    bago scan <ruta>                   → escanea directorio específico
    bago scan --severity error         → filtra por severidad mínima
    bago scan --source flake8          → solo un linter
    bago scan --rule E302              → filtra por regla
    bago scan --file <ruta>            → filtra por archivo
    bago scan --summary                → solo resumen sin detalle
    bago scan --json                   → output JSON completo
    bago scan --last                   → muestra el último scan guardado
    bago scan --autofixable            → muestra solo hallazgos con autofix disponible
    bago scan --test                   → tests integrados
"""

import argparse, json, subprocess, sys
from pathlib import Path

TOOLS_DIR = Path(__file__).parent
sys.path.insert(0, str(TOOLS_DIR))
import findings_engine as fe

BAGO_ROOT    = Path(__file__).parent.parent
SEVERITY_ORD = {"error": 0, "warning": 1, "info": 2, "hint": 3}
SEV_COLOR    = {"error":"\033[31m","warning":"\033[33m","info":"\033[36m","hint":"\033[2m"}
BOLD  = "\033[1m"; RESET = "\033[0m"; DIM = "\033[2m"; GREEN = "\033[32m"


def run_scan(target: str, sources: list | None = None) -> fe.FindingsDB:
    db = fe.FindingsDB()
    db.meta["target"] = target

    # Always run BAGO's own lint (no external deps)
    bago_findings = fe.run_bago_lint(target)
    db.add(bago_findings)
    db.meta["sources"].append("bago")

    linters = sources or ["flake8", "pylint", "mypy", "bandit"]

    if "flake8" in linters:
        findings, err = fe.run_linter(
            ["python3", "-m", "flake8", "--max-line-length=120",
             "--format=%(path)s:%(row)d:%(col)d: %(code)s %(text)s", target],
            fe.parse_flake8, cwd=str(BAGO_ROOT.parent)
        )
        if not err:
            db.add(findings); db.meta["sources"].append("flake8")

    if "pylint" in linters:
        findings, err = fe.run_linter(
            ["python3", "-m", "pylint", "--output-format=json",
             "--disable=C0114,C0115,C0116,R0903", target],
            fe.parse_pylint, cwd=str(BAGO_ROOT.parent)
        )
        if not err:
            db.add(findings); db.meta["sources"].append("pylint")

    if "mypy" in linters:
        findings, err = fe.run_linter(
            ["python3", "-m", "mypy", "--ignore-missing-imports",
             "--no-error-summary", target],
            fe.parse_mypy, cwd=str(BAGO_ROOT.parent)
        )
        if not err:
            db.add(findings); db.meta["sources"].append("mypy")

    if "bandit" in linters:
        findings, err = fe.run_linter(
            ["python3", "-m", "bandit", "-r", "-f", "json", "-q", target],
            fe.parse_bandit, cwd=str(BAGO_ROOT.parent)
        )
        if not err:
            db.add(findings); db.meta["sources"].append("bandit")

    db.save()
    return db


def filter_findings(findings: list, severity: str | None, source: str | None,
                    rule: str | None, file_filter: str | None,
                    autofixable_only: bool) -> list:
    out = findings
    if severity:
        ord_min = SEVERITY_ORD.get(severity, 3)
        out = [f for f in out if SEVERITY_ORD.get(f.severity, 3) <= ord_min]
    if source:
        out = [f for f in out if f.source == source]
    if rule:
        out = [f for f in out if f.rule == rule]
    if file_filter:
        out = [f for f in out if file_filter in f.file]
    if autofixable_only:
        out = [f for f in out if f.autofixable]
    return out


def render_findings(db: fe.FindingsDB, findings: list, summary_only: bool, as_json: bool):
    if as_json:
        print(json.dumps({
            "scan_id":  db.scan_id,
            "summary":  db._summary(),
            "findings": [f.to_dict() for f in findings],
        }, indent=2, ensure_ascii=False))
        return

    s = db._summary()
    print(f"\n  {BOLD}BAGO Scan{RESET}  [{db.scan_id}]")
    print(f"  Target: {DIM}{db.meta.get('target','')}{RESET}")
    print(f"  Sources: {', '.join(db.meta.get('sources', []))}\n")

    # Summary table
    total = s["total"]
    af    = s["autofixable"]
    errs  = s["by_severity"].get("error", 0)
    warns = s["by_severity"].get("warning", 0)
    infos = s["by_severity"].get("info", 0)
    hints = s["by_severity"].get("hint", 0)

    print(f"  {BOLD}Resumen{RESET}")
    print(f"    Total:       {total}")
    print(f"    {SEV_COLOR['error']}Errores:{RESET}     {errs}")
    print(f"    {SEV_COLOR['warning']}Warnings:{RESET}    {warns}")
    print(f"    {SEV_COLOR['info']}Info:{RESET}        {infos}")
    print(f"    {SEV_COLOR['hint']}Hints:{RESET}       {hints}")
    print(f"    {GREEN}Autofixable:{RESET} {af}")

    if s["top_files"]:
        print(f"\n  {BOLD}Top archivos afectados:{RESET}")
        for fpath, count in s["top_files"][:5]:
            short = fpath.replace(str(BAGO_ROOT.parent) + "/", "")
            print(f"    {count:4d}  {short}")

    if summary_only:
        print()
        return

    # Detail
    if not findings:
        print(f"\n  {GREEN}✓ Sin hallazgos con los filtros aplicados{RESET}\n")
        return

    print(f"\n  {BOLD}Hallazgos ({len(findings)}){RESET}\n")
    cur_file = None
    for f in sorted(findings, key=lambda x: (x.file, x.line)):
        if f.file != cur_file:
            short = f.file.replace(str(BAGO_ROOT.parent) + "/", "")
            print(f"  {BOLD}{short}{RESET}")
            cur_file = f.file
        color = SEV_COLOR.get(f.severity, RESET)
        fix_mark = f"  {GREEN}[autofix]{RESET}" if f.autofixable else ""
        print(f"    {color}{f.severity:8s}{RESET} L{f.line:4d}  {DIM}[{f.rule}]{RESET}  {f.message}{fix_mark}")
        if f.fix_suggestion:
            print(f"             {DIM}→ {f.fix_suggestion}{RESET}")
    print()


def run_tests():
    import tempfile, shutil
    print("Ejecutando tests de scan.py...")
    errors = 0
    def ok(n): print(f"  OK: {n}")
    def fail(n, m):
        nonlocal errors; errors += 1; print(f"  FAIL: {n} — {m}")

    # T1: run_bago_lint finds utcnow issues in tools
    tmp = Path(tempfile.mkdtemp())
    (tmp / "sample.py").write_text(
        "import datetime\nts = datetime.datetime.utcnow()\n"
    )
    findings = fe.run_bago_lint(str(tmp))
    if any(f.rule == "BAGO-W001" for f in findings):
        ok("scan:bago_lint_detects_utcnow")
    else:
        fail("scan:bago_lint_detects_utcnow", str(findings))
    shutil.rmtree(tmp)

    # T2: filter_findings by severity
    f1 = fe.Finding(id="A",severity="error",file="a.py",line=1,col=0,rule="E1",source="flake8",message="e")
    f2 = fe.Finding(id="B",severity="info",file="b.py",line=2,col=0,rule="I1",source="bago",message="i")
    filtered = filter_findings([f1,f2],"error",None,None,None,False)
    if len(filtered)==1 and filtered[0].id=="A":
        ok("scan:filter_severity")
    else:
        fail("scan:filter_severity", str(filtered))

    # T3: filter_findings by source
    filtered2 = filter_findings([f1,f2],None,"bago",None,None,False)
    if len(filtered2)==1 and filtered2[0].source=="bago":
        ok("scan:filter_source")
    else:
        fail("scan:filter_source", str(filtered2))

    # T4: filter_findings autofixable
    f3 = fe.Finding(id="C",severity="warning",file="c.py",line=3,col=0,rule="W1",
                    source="flake8",message="w",autofixable=True)
    filtered3 = filter_findings([f1,f2,f3],None,None,None,None,True)
    if len(filtered3)==1 and filtered3[0].id=="C":
        ok("scan:filter_autofixable")
    else:
        fail("scan:filter_autofixable", str(filtered3))

    # T5: FindingsDB.save creates file
    import importlib.util as ilu
    spec = ilu.spec_from_file_location("fe2", Path(__file__).parent/"findings_engine.py")
    m = ilu.module_from_spec(spec); spec.loader.exec_module(m)
    tmp2 = Path(tempfile.mkdtemp())
    m.FINDINGS_DIR = tmp2
    db = m.FindingsDB("SCAN-TESTX")
    db.add([f1,f2,f3])
    path = db.save()
    if path.exists() and json.loads(path.read_text())["summary"]["total"] == 3:
        ok("scan:db_save_creates_file")
    else:
        fail("scan:db_save_creates_file", str(path))
    shutil.rmtree(tmp2)

    total=5; passed=total-errors
    print(f"\n  {passed}/{total} tests pasaron")
    if errors: sys.exit(1)


def main():
    parser = argparse.ArgumentParser(prog="bago scan", add_help=False)
    parser.add_argument("target", nargs="?", default=str(BAGO_ROOT / "tools"))
    parser.add_argument("--severity",    default=None)
    parser.add_argument("--source",      default=None)
    parser.add_argument("--rule",        default=None)
    parser.add_argument("--file",        dest="file_filter", default=None)
    parser.add_argument("--summary",     action="store_true")
    parser.add_argument("--json",        action="store_true")
    parser.add_argument("--last",        action="store_true")
    parser.add_argument("--autofixable", action="store_true")
    parser.add_argument("--test",        action="store_true")
    args = parser.parse_args()

    if args.test:
        run_tests(); return

    if args.last:
        db = fe.FindingsDB.latest()
        if db is None:
            print("Sin scans guardados. Ejecuta 'bago scan' primero.")
            sys.exit(1)
    else:
        print(f"  Escaneando {args.target} ...")
        db = run_scan(args.target)

    findings = filter_findings(
        db.findings,
        args.severity, args.source, args.rule,
        args.file_filter, args.autofixable
    )
    render_findings(db, findings, args.summary, args.json)

if __name__ == "__main__":
    main()