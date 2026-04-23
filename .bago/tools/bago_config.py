#!/usr/bin/env python3
"""bago_config.py — Configuración centralizada compartida entre todos los tools BAGO.

El problema actual: cada tool tiene thresholds hardcodeados.
complexity.py asume max_complexity=10 sin consultar al equipo.
lint_report.py asume max_line_length=100 sin opción de overrride.
secret_scan.py no puede añadir patrones custom sin editar el código.

Este tool crea y gestiona `.bago/config.json` — fuente de verdad
para todas las preferencias del framework.

Uso:
    python3 bago_config.py                        # muestra config actual
    python3 bago_config.py --get complexity.max   # lee un valor
    python3 bago_config.py --set complexity.max 15  # escribe un valor
    python3 bago_config.py --reset                # vuelve a defaults
    python3 bago_config.py --export               # exporta JSON completo
    python3 bago_config.py --validate             # valida estructura
    python3 bago_config.py --test                 # self-tests

Códigos: CFG-I001 (valor leído/escrito), CFG-W001 (valor no encontrado),
         CFG-E001 (validación fallida), CFG-I002 (reset aplicado)
"""
import sys
import json
from pathlib import Path
from typing import Any, Optional

BAGO_ROOT = Path(__file__).parent.parent
CONFIG_FILE = BAGO_ROOT / "config.json"

# ─────────────────────────────────────────────────────────────────────────────
# DEFAULT CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
DEFAULTS = {
    "version": "1.0",
    "complexity": {
        "max_cyclomatic": 10,
        "max_cognitive": 15,
        "max_function_lines": 50,
        "max_class_lines": 300,
    },
    "lint": {
        "max_line_length": 100,
        "ignore_codes": ["E402", "W503"],
        "max_blank_lines": 2,
    },
    "secret_scan": {
        "extra_patterns": [],
        "whitelist_files": [".bago/tools/bago_config.py"],
        "min_secret_length": 8,
    },
    "doc_coverage": {
        "min_coverage_pct": 60,
        "require_module_docstring": True,
        "require_class_docstring": True,
        "require_function_docstring": False,
    },
    "coverage_gate": {
        "min_coverage_pct": 70,
        "fail_on_missing": True,
    },
    "naming": {
        "style": "snake_case",
        "max_name_length": 40,
        "allow_single_letter_vars": True,
    },
    "dep_audit": {
        "fail_on_open_ranges": False,
        "fail_on_no_version": True,
        "extra_cve_packages": [],
    },
    "readme": {
        "required_sections": ["Installation", "Usage", "License"],
        "min_lines": 20,
    },
    "ci_report": {
        "min_score_merge": 80,
        "min_score_review": 50,
    },
    "tool_guardian": {
        "require_test_flag": True,
        "require_docstring": True,
        "require_routing": False,
    },
    "orchestrator": {
        "default_timeout_seconds": 90,
        "fail_fast_by_default": False,
    },
    "commit_readiness": {
        "max_file_size_kb": 500,
        "fail_on_debug_prints": False,
        "fail_on_todos": False,
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# SCHEMA VALIDATION
# ─────────────────────────────────────────────────────────────────────────────
SCHEMA = {
    "complexity.max_cyclomatic": (int, 1, 100),
    "complexity.max_cognitive": (int, 1, 200),
    "complexity.max_function_lines": (int, 10, 1000),
    "lint.max_line_length": (int, 60, 300),
    "doc_coverage.min_coverage_pct": (int, 0, 100),
    "coverage_gate.min_coverage_pct": (int, 0, 100),
    "ci_report.min_score_merge": (int, 0, 100),
    "ci_report.min_score_review": (int, 0, 100),
    "orchestrator.default_timeout_seconds": (int, 10, 600),
    "commit_readiness.max_file_size_kb": (int, 10, 10000),
}


def load_config() -> dict:
    """Carga config.json, merge con defaults para valores faltantes."""
    if not CONFIG_FILE.exists():
        return dict(DEFAULTS)
    try:
        stored = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        # Deep merge: stored overrides defaults
        merged = _deep_merge(dict(DEFAULTS), stored)
        return merged
    except Exception:
        return dict(DEFAULTS)


def _deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def save_config(config: dict) -> bool:
    try:
        CONFIG_FILE.write_text(
            json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return True
    except Exception:
        return False


def get_value(config: dict, key: str) -> tuple:
    """Navega por clave punteada. Retorna (found, value)."""
    parts = key.split(".")
    cur = config
    for part in parts:
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return False, None
    return True, cur


def set_value(config: dict, key: str, value: Any) -> dict:
    """Escribe valor en clave punteada. Retorna config modificado."""
    parts = key.split(".")
    cur = config
    for part in parts[:-1]:
        if part not in cur:
            cur[part] = {}
        cur = cur[part]
    # Auto-cast to match schema type
    schema_entry = SCHEMA.get(key)
    if schema_entry:
        typ = schema_entry[0]
        try:
            value = typ(value)
        except (ValueError, TypeError):
            pass
    cur[parts[-1]] = value
    return config


def validate_config(config: dict) -> list:
    """Valida valores contra el schema. Retorna lista de errores."""
    errors = []
    for key, (typ, min_val, max_val) in SCHEMA.items():
        found, val = get_value(config, key)
        if not found:
            continue
        if not isinstance(val, typ):
            errors.append(f"CFG-E001: {key} debe ser {typ.__name__}, es {type(val).__name__}")
        elif isinstance(val, (int, float)):
            if val < min_val or val > max_val:
                errors.append(f"CFG-E001: {key}={val} fuera de rango [{min_val}, {max_val}]")
    return errors


def print_config(config: dict, prefix: str = ""):
    """Muestra config de forma legible."""
    for k, v in config.items():
        if k == "version":
            continue
        if isinstance(v, dict):
            print(f"  [{k}]")
            for sk, sv in v.items():
                if isinstance(sv, list):
                    sv_str = json.dumps(sv) if sv else "[]"
                    print(f"    {sk:35s} = {sv_str}")
                else:
                    print(f"    {sk:35s} = {sv}")
        else:
            print(f"  {k:40s} = {v}")


def cmd_show():
    config = load_config()
    src = "config.json" if CONFIG_FILE.exists() else "defaults"
    print(f"\n  BAGO Config — {src}")
    print("  " + "─" * 54)
    print_config(config)
    print()


def cmd_get(key: str) -> int:
    config = load_config()
    found, val = get_value(config, key)
    if not found:
        print(f"  [CFG-W001] Clave no encontrada: {key}")
        return 1
    print(f"  [CFG-I001] {key} = {json.dumps(val)}")
    return 0


def cmd_set(key: str, value: str) -> int:
    config = load_config()
    config = set_value(config, key, value)
    errors = validate_config(config)
    if errors:
        for e in errors:
            print(f"  [{e}]")
        return 1
    if save_config(config):
        found, saved_val = get_value(config, key)
        print(f"  [CFG-I001] ✅ {key} = {json.dumps(saved_val)}")
        return 0
    print("  [CFG-E001] Error guardando config.json")
    return 1


def cmd_reset(dry_run: bool = False) -> int:
    if not dry_run:
        if save_config(DEFAULTS):
            print(f"  [CFG-I002] ✅ config.json restaurado a defaults")
            return 0
        print("  [CFG-E001] Error escribiendo config.json")
        return 1
    else:
        print("  [CFG-I002] DRY: config.json sería restaurado a defaults")
        return 0


def cmd_validate() -> int:
    config = load_config()
    errors = validate_config(config)
    if not errors:
        print("  [CFG-I001] ✅ config.json válido")
        return 0
    for e in errors:
        print(f"  {e}")
    return 1


def run_tests():
    import tempfile, os
    results = []

    # Test 1: load_config returns dict with defaults
    cfg = load_config()
    ok1 = "complexity" in cfg and "lint" in cfg
    results.append(("bago_config:load_defaults", ok1, f"keys={list(cfg.keys())[:4]}"))

    # Test 2: get_value with dotted key
    found, val = get_value(DEFAULTS, "complexity.max_cyclomatic")
    ok2 = found and val == 10
    results.append(("bago_config:get_dotted_key", ok2, f"val={val}"))

    # Test 3: get_value missing key
    found, val = get_value(DEFAULTS, "nonexistent.key")
    ok3 = not found and val is None
    results.append(("bago_config:get_missing_key", ok3, f"found={found}"))

    # Test 4: set_value with type coercion
    cfg = dict(DEFAULTS)
    cfg = set_value(cfg, "complexity.max_cyclomatic", "20")
    found, val = get_value(cfg, "complexity.max_cyclomatic")
    ok4 = found and val == 20 and isinstance(val, int)
    results.append(("bago_config:set_with_coercion", ok4, f"val={val} type={type(val).__name__}"))

    # Test 5: validate detects out-of-range
    cfg = dict(DEFAULTS)
    cfg = set_value(cfg, "ci_report.min_score_merge", 150)
    errors = validate_config(cfg)
    ok5 = len(errors) > 0
    results.append(("bago_config:validate_range_error", ok5, f"errors={len(errors)}"))

    # Test 6: deep_merge preserves nested overrides
    base = {"a": {"x": 1, "y": 2}, "b": 3}
    override = {"a": {"x": 99}, "c": 4}
    merged = _deep_merge(base, override)
    ok6 = merged["a"]["x"] == 99 and merged["a"]["y"] == 2 and merged["c"] == 4
    results.append(("bago_config:deep_merge", ok6,
                     f"x={merged['a']['x']} y={merged['a']['y']} c={merged.get('c')}"))

    passed = sum(1 for _, ok, _ in results if ok)
    failed = sum(1 for _, ok, _ in results if not ok)
    for name, ok, detail in results:
        status = "✅" if ok else "❌"
        print(f"  {status}  {name}: {detail}")
    print(f"\n  {passed}/{len(results)} pasaron")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    args = sys.argv[1:]

    if "--test" in args:
        sys.exit(run_tests())

    if "--help" in args or "-h" in args or not args:
        cmd_show()
        raise SystemExit(0)

    if "--get" in args:
        i = args.index("--get")
        key = args[i + 1] if i + 1 < len(args) else ""
        sys.exit(cmd_get(key))

    if "--set" in args:
        i = args.index("--set")
        key = args[i + 1] if i + 1 < len(args) else ""
        val = args[i + 2] if i + 2 < len(args) else ""
        sys.exit(cmd_set(key, val))

    if "--reset" in args:
        sys.exit(cmd_reset(dry_run="--dry-run" in args))

    if "--validate" in args:
        sys.exit(cmd_validate())

    if "--export" in args:
        config = load_config()
        print(json.dumps(config, indent=2))
        raise SystemExit(0)

    cmd_show()
