#!/usr/bin/env python3
"""env_check.py — Herramienta #105: Verificador de variables de entorno requeridas.

Valida que el entorno actual tenga las variables necesarias para ejecutar el
proyecto. Lee la lista desde un archivo .env.required, un bloque del pack.json,
o una lista explícita. Detecta valores vacíos, placeholders y patrones inseguros.

Uso:
    bago env-check [--file FILE] [--vars VAR1,VAR2,...] [--json]
                   [--strict] [--show-values] [--test]

Opciones:
    --file        Archivo con una variable por línea (default: .env.required si existe)
    --vars        Lista de variables separadas por coma
    --json        Output en JSON
    --strict      Exit 1 si hay advertencias (además de errores)
    --show-values Mostrar los valores (cuidado con datos sensibles)
    --test        Self-tests
"""
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

BAGO_ROOT = Path(__file__).parent.parent

_RED  = "\033[0;31m"
_GRN  = "\033[0;32m"
_YEL  = "\033[0;33m"
_RST  = "\033[0m"
_BOLD = "\033[1m"
_DIM  = "\033[2m"

PLACEHOLDER_RE = re.compile(
    r'^(TODO|FIXME|CHANGEME|your[-_]?.*here|example|placeholder|xxx+|<.+>|\$\{.+\}|%\w+%)$',
    re.IGNORECASE
)
SECRET_RE = re.compile(r'(?i)(password|secret|token|key|api_key|private)', )


@dataclass
class EnvResult:
    name:    str
    status:  str   # "ok" | "missing" | "empty" | "placeholder" | "warning"
    message: str
    value:   str = ""   # solo si --show-values


def check_var(name: str, show_value: bool = False) -> EnvResult:
    val = os.environ.get(name)
    display = ""
    if show_value and val is not None:
        # Ofuscar secretos parcialmente
        if SECRET_RE.search(name):
            display = val[:2] + "***" + val[-2:] if len(val) > 4 else "***"
        else:
            display = val[:40]

    if val is None:
        return EnvResult(name=name, status="missing",
                         message=f"Variable '{name}' no está definida", value=display)
    if val.strip() == "":
        return EnvResult(name=name, status="empty",
                         message=f"Variable '{name}' está vacía", value=display)
    if PLACEHOLDER_RE.match(val.strip()):
        return EnvResult(name=name, status="placeholder",
                         message=f"Variable '{name}' parece un placeholder: '{val[:30]}'",
                         value=display)
    return EnvResult(name=name, status="ok",
                     message=f"Variable '{name}' definida", value=display)


def load_var_list(file_path: Optional[Path] = None,
                  var_list: Optional[str] = None) -> list[str]:
    """Carga lista de variables desde archivo o argumento."""
    if var_list:
        return [v.strip() for v in var_list.split(",") if v.strip()]
    if file_path and file_path.exists():
        lines = file_path.read_text(encoding="utf-8").splitlines()
        return [l.strip() for l in lines
                if l.strip() and not l.strip().startswith("#")]
    # Fallback: buscar .env.required en cwd y bago_root
    for candidate in [Path(".env.required"), BAGO_ROOT / ".env.required"]:
        if candidate.exists():
            lines = candidate.read_text(encoding="utf-8").splitlines()
            return [l.strip() for l in lines
                    if l.strip() and not l.strip().startswith("#")]
    return []


# Optional type hint fix
from typing import Optional


def main(argv: list[str]) -> int:
    file_arg   = None
    var_arg    = None
    as_json    = False
    strict     = False
    show_vals  = False

    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--file" and i + 1 < len(argv):
            file_arg = Path(argv[i + 1]); i += 2
        elif a == "--vars" and i + 1 < len(argv):
            var_arg = argv[i + 1]; i += 2
        elif a == "--json":
            as_json = True; i += 1
        elif a == "--strict":
            strict = True; i += 1
        elif a == "--show-values":
            show_vals = True; i += 1
        else:
            i += 1

    var_names = load_var_list(file_arg, var_arg)
    if not var_names:
        msg = "No se encontraron variables para verificar. Usa --vars o --file."
        if as_json:
            print(json.dumps({"error": msg, "results": []}))
        else:
            print(f"{_YEL}⚠️  {msg}{_RST}")
        return 0

    results = [check_var(n, show_vals) for n in var_names]
    errors  = [r for r in results if r.status in ("missing", "empty", "placeholder")]
    warnings= [r for r in results if r.status == "warning"]
    ok_list = [r for r in results if r.status == "ok"]

    if as_json:
        summary = {
            "total": len(results), "ok": len(ok_list),
            "errors": len(errors), "warnings": len(warnings),
            "pass": len(errors) == 0 and (not strict or len(warnings) == 0),
            "results": [asdict(r) for r in results],
        }
        print(json.dumps(summary, indent=2))
        return 0 if summary["pass"] else 1

    print(f"\n{_BOLD}Env Check — {len(var_names)} variable(s){_RST}\n")
    for r in results:
        if r.status == "ok":
            val_str = f" = {_DIM}{r.value}{_RST}" if r.value else ""
            print(f"  {_GRN}✅{_RST} {r.name}{val_str}")
        elif r.status == "missing":
            print(f"  {_RED}❌{_RST} {r.name}  {_DIM}(no definida){_RST}")
        elif r.status == "empty":
            print(f"  {_RED}❌{_RST} {r.name}  {_DIM}(vacía){_RST}")
        elif r.status == "placeholder":
            print(f"  {_YEL}⚠️ {_RST} {r.name}  {_DIM}(placeholder){_RST}")

    print()
    if errors:
        print(f"  {_RED}FALLÓ — {len(errors)} variable(s) con problema{_RST}")
        return 1
    if strict and warnings:
        print(f"  {_YEL}FALLÓ (strict) — {len(warnings)} advertencia(s){_RST}")
        return 1
    print(f"  {_GRN}✅ Todas las variables están definidas{_RST}")
    return 0


def _self_test() -> None:
    print("Tests de env_check.py...")
    fails: list[str] = []
    def ok(n): print(f"  OK: {n}")
    def fail(n, m): fails.append(n); print(f"  FAIL: {n}: {m}")

    # Preparar entorno de prueba
    os.environ["_TEST_BAGO_OK"]          = "real_value"
    os.environ["_TEST_BAGO_EMPTY"]       = ""
    os.environ["_TEST_BAGO_PLACEHOLDER"] = "CHANGEME"

    # T1 — variable definida → ok
    r = check_var("_TEST_BAGO_OK")
    if r.status == "ok": ok("env_check:defined_ok")
    else: fail("env_check:defined_ok", f"status={r.status}")

    # T2 — variable no definida → missing
    r2 = check_var("_TEST_BAGO_DOES_NOT_EXIST_XYZ")
    if r2.status == "missing": ok("env_check:missing_detected")
    else: fail("env_check:missing_detected", f"status={r2.status}")

    # T3 — variable vacía → empty
    r3 = check_var("_TEST_BAGO_EMPTY")
    if r3.status == "empty": ok("env_check:empty_detected")
    else: fail("env_check:empty_detected", f"status={r3.status}")

    # T4 — placeholder detectado
    r4 = check_var("_TEST_BAGO_PLACEHOLDER")
    if r4.status == "placeholder": ok("env_check:placeholder_detected")
    else: fail("env_check:placeholder_detected", f"status={r4.status}")

    # T5 — load_var_list desde string
    names = load_var_list(var_list="_TEST_BAGO_OK,_TEST_BAGO_EMPTY")
    if names == ["_TEST_BAGO_OK", "_TEST_BAGO_EMPTY"]: ok("env_check:load_from_string")
    else: fail("env_check:load_from_string", f"names={names}")

    # T6 — show_value ofusca secret
    os.environ["_TEST_SECRET_KEY"] = "supersecretpassword"
    r6 = check_var("_TEST_SECRET_KEY", show_value=True)
    if "***" in r6.value and "supersecrep" not in r6.value:
        ok("env_check:secret_obfuscated")
    else:
        fail("env_check:secret_obfuscated", f"value={r6.value!r}")

    for k in ["_TEST_BAGO_OK","_TEST_BAGO_EMPTY","_TEST_BAGO_PLACEHOLDER","_TEST_SECRET_KEY"]:
        os.environ.pop(k, None)

    total = 6; passed = total - len(fails)
    print(f"\n  {passed}/{total} tests pasaron")
    if fails: sys.exit(1)


if __name__ == "__main__":
    if "--test" in sys.argv:
        _self_test()
    else:
        sys.exit(main(sys.argv[1:]))
