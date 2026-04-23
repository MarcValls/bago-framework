#!/usr/bin/env python3
"""lint_report.py — Herramienta #97: Generador de informe Markdown de resultados de bago-lint.

Convierte la salida JSON de bago-lint (o multi-scan) en un informe
Markdown estructurado con secciones por severidad, archivos y resumen.

Uso:
    python3 lint_report.py [SCAN_JSON] [--title TITULO] [--out FILE] [--test]
    bago lint-report [SCAN_JSON] [--title TITULO] [--out FILE]

    # Pipe directo desde bago-lint:
    bago bago-lint --json | bago lint-report --stdin
    bago multi-scan ./ --json | bago lint-report --stdin --title "Sprint Review"

Opciones:
    SCAN_JSON         Archivo JSON de findings (de --json)
    --stdin           Leer JSON desde stdin
    --title TITULO    Título del informe (default: "Informe de Análisis Estático")
    --out FILE        Escribir a archivo en vez de stdout
    --no-details      Omitir detalles por archivo (solo resumen)
    --test            Ejecutar self-tests y salir
"""
from __future__ import annotations

import json
import sys
import datetime
from collections import defaultdict
from pathlib import Path
from typing import Optional

# ─── Parsing ───────────────────────────────────────────────────────────────

def load_findings(data: dict) -> list[dict]:
    """Acepta salida de bago-lint --json O multi-scan --json."""
    if "findings" in data:
        return data["findings"]          # bago-lint format
    elif "by_lang" in data:              # multi-scan format
        all_f = []
        for lang_findings in data.get("by_lang", {}).values():
            all_f.extend(lang_findings)
        return all_f
    elif isinstance(data, list):
        return data
    return []


# ─── Generador de Markdown ─────────────────────────────────────────────────

_SEV_ICON = {"error": "🔴", "warning": "🟡", "info": "🔵", "hint": "⚪"}
_SEV_ORDER = {"error": 0, "warning": 1, "info": 2, "hint": 3}


def generate_report(
    findings: list[dict],
    title: str = "Informe de Análisis Estático",
    include_details: bool = True,
    meta: Optional[dict] = None,
) -> str:
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M")
    lines = [f"# {title}\n"]
    lines.append(f"> Generado: {now}  ")
    if meta:
        for k, v in meta.items():
            lines.append(f"> **{k}:** {v}  ")
    lines.append("")

    # ── Resumen ejecutivo ──────────────────────────────────────────────
    by_sev: dict[str, int] = defaultdict(int)
    by_rule: dict[str, int] = defaultdict(int)
    by_file: dict[str, list[dict]] = defaultdict(list)

    for f in findings:
        sev = f.get("severity", "info")
        by_sev[sev] += 1
        if r := f.get("rule"):
            by_rule[r] += 1
        fp = f.get("file", "—")
        by_file[fp].append(f)

    total = len(findings)
    errors   = by_sev.get("error", 0)
    warnings = by_sev.get("warning", 0)
    infos    = by_sev.get("info", 0) + by_sev.get("hint", 0)

    lines.append("## Resumen ejecutivo\n")
    lines.append(f"| Métrica | Valor |")
    lines.append(f"|---------|-------|")
    lines.append(f"| Total hallazgos | **{total}** |")
    lines.append(f"| 🔴 Errores | {errors} |")
    lines.append(f"| 🟡 Advertencias | {warnings} |")
    lines.append(f"| 🔵 Informativas | {infos} |")
    lines.append(f"| Archivos afectados | {len(by_file)} |")
    lines.append("")

    # Estado global
    if errors > 0:
        lines.append("> ⛔ **Estado: FALLOS — hay errores que requieren atención inmediata.**\n")
    elif warnings > 0:
        lines.append("> ⚠️ **Estado: ADVERTENCIAS — revisar antes del próximo merge.**\n")
    else:
        lines.append("> ✅ **Estado: LIMPIO — sin errores ni advertencias críticas.**\n")

    if not findings:
        lines.append("_No se encontraron hallazgos._\n")
        return "\n".join(lines)

    # ── Top reglas ────────────────────────────────────────────────────
    lines.append("## Top reglas\n")
    lines.append("| Regla | Ocurrencias |")
    lines.append("|-------|-------------|")
    for rule, count in sorted(by_rule.items(), key=lambda x: -x[1])[:10]:
        lines.append(f"| `{rule}` | {count} |")
    lines.append("")

    # ── Detalle por archivo ───────────────────────────────────────────
    if include_details and by_file:
        lines.append("## Hallazgos por archivo\n")
        for fp in sorted(by_file.keys()):
            file_findings = sorted(
                by_file[fp],
                key=lambda x: (_SEV_ORDER.get(x.get("severity", "info"), 9), x.get("line", 0))
            )
            n_err  = sum(1 for f in file_findings if f.get("severity") == "error")
            n_warn = sum(1 for f in file_findings if f.get("severity") == "warning")
            badge = ""
            if n_err:
                badge += f" 🔴{n_err}"
            if n_warn:
                badge += f" 🟡{n_warn}"
            lines.append(f"### `{fp}`{badge}\n")
            lines.append("| Línea | Severidad | Regla | Mensaje |")
            lines.append("|-------|-----------|-------|---------|")
            for f in file_findings:
                sev   = f.get("severity", "info")
                icon  = _SEV_ICON.get(sev, "⚪")
                line  = f.get("line", "—")
                rule  = f.get("rule", "—")
                msg   = f.get("message", "").replace("|", "\\|")
                lines.append(f"| {line} | {icon} {sev} | `{rule}` | {msg} |")
            lines.append("")

    # ── Footer ────────────────────────────────────────────────────────
    lines.append("---")
    lines.append(f"\n_Informe generado por `bago lint-report` — BAGO Framework_")
    return "\n".join(lines)


# ─── CLI ───────────────────────────────────────────────────────────────────

def main(argv: list[str]) -> int:
    title   = "Informe de Análisis Estático"
    out     = None
    use_stdin = False
    details   = True
    src_file  = None

    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--title" and i + 1 < len(argv):
            title = argv[i + 1]; i += 2
        elif a == "--out" and i + 1 < len(argv):
            out = argv[i + 1]; i += 2
        elif a == "--stdin":
            use_stdin = True; i += 1
        elif a == "--no-details":
            details = False; i += 1
        elif not a.startswith("--"):
            src_file = a; i += 1
        else:
            i += 1

    if use_stdin:
        try:
            data = json.load(sys.stdin)
        except json.JSONDecodeError as e:
            print(f"ERROR: JSON inválido en stdin: {e}", file=sys.stderr)
            return 1
    elif src_file:
        try:
            with open(src_file) as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 1
    else:
        print("ERROR: proporciona un archivo JSON o usa --stdin", file=sys.stderr)
        print("Ejemplo: bago bago-lint --json | bago lint-report --stdin", file=sys.stderr)
        return 1

    findings = load_findings(data)
    meta = {}
    if "target" in data:
        meta["Objetivo"] = data["target"]
    if "scan_time" in data:
        meta["Tiempo de análisis"] = data["scan_time"]

    report = generate_report(findings, title=title, include_details=details, meta=meta)

    if out:
        Path(out).write_text(report, encoding="utf-8")
        print(f"Informe escrito en: {out}  ({len(findings)} hallazgos)")
    else:
        print(report)

    return 0


# ─── Self-tests ────────────────────────────────────────────────────────────

def _self_test() -> None:
    print("Tests de lint_report.py...")
    fails: list[str] = []

    def ok(name: str) -> None:
        print(f"  OK: {name}")

    def fail(name: str, msg: str) -> None:
        fails.append(name)
        print(f"  FAIL: {name}: {msg}")

    SAMPLE_FINDINGS = [
        {"file": "src/main.py", "line": 10, "severity": "error",   "rule": "BAGO-E001", "message": "bare except"},
        {"file": "src/main.py", "line": 25, "severity": "warning", "rule": "BAGO-W001", "message": "utcnow deprecated"},
        {"file": "src/utils.py","line": 5,  "severity": "warning", "rule": "BAGO-W002", "message": "eval() used"},  # noqa: BAGO-W002
        {"file": "src/utils.py","line": 8,  "severity": "info",    "rule": "BAGO-I002", "message": "TODO comment"},
        {"file": "src/api.js",  "line": 30, "severity": "error",   "rule": "JS-E001",   "message": "eval detected"},
    ]

    # T1 — load_findings desde formato bago-lint
    data_bago = {"findings": SAMPLE_FINDINGS}
    loaded = load_findings(data_bago)
    if loaded == SAMPLE_FINDINGS:
        ok("lint_report:load_bago_format")
    else:
        fail("lint_report:load_bago_format", f"loaded {len(loaded)} findings")

    # T2 — load_findings desde formato multi-scan
    data_multi = {"by_lang": {"py": SAMPLE_FINDINGS[:3], "js": SAMPLE_FINDINGS[4:]}}
    loaded_multi = load_findings(data_multi)
    if len(loaded_multi) == 4:
        ok("lint_report:load_multi_scan_format")
    else:
        fail("lint_report:load_multi_scan_format", f"loaded {len(loaded_multi)}")

    # T3 — generate_report produce Markdown con secciones esperadas
    report = generate_report(SAMPLE_FINDINGS, title="Test Report")
    if (
        "Test Report" in report
        and "Resumen ejecutivo" in report
        and "BAGO-E001" in report
        and "src/main.py" in report
    ):
        ok("lint_report:generate_markdown_sections")
    else:
        fail("lint_report:generate_markdown_sections", "secciones faltantes")

    # T4 — estado FALLOS cuando hay errores
    if "FALLOS" in report:
        ok("lint_report:estado_fallos_con_errores")
    else:
        fail("lint_report:estado_fallos_con_errores", "Estado no indica FALLOS")

    # T5 — informe limpio cuando no hay findings
    clean = generate_report([])
    if "LIMPIO" in clean:
        ok("lint_report:estado_limpio_sin_findings")
    else:
        fail("lint_report:estado_limpio_sin_findings", "Estado no indica LIMPIO")

    # T6 — --no-details omite sección de archivos
    no_det = generate_report(SAMPLE_FINDINGS, include_details=False)
    if "Hallazgos por archivo" not in no_det and "Resumen ejecutivo" in no_det:
        ok("lint_report:no_details_flag")
    else:
        fail("lint_report:no_details_flag", "detalles no omitidos")

    total = 6
    passed = total - len(fails)
    print(f"\n  {passed}/{total} tests pasaron")
    if fails:
        raise SystemExit(1)


if __name__ == "__main__":
    if "--test" in sys.argv:
        _self_test()
    else:
        raise SystemExit(main(sys.argv[1:]))
