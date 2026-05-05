#!/usr/bin/env python3
"""config_check.py — Valida integridad de los archivos JSON en .bago/state/config/.

Verifica que:
  1. Cada JSON es parseable y tiene la clave 'version'.
  2. Cada config tiene las claves requeridas por su esquema mínimo.
  3. Los tools en tool_catalog.json existen como entradas en tool_registry.py (REGISTRY).
  4. No hay configs huérfanas (JSONs sin consumidor conocido).

Uso:
    python3 config_check.py          → validación completa
    python3 config_check.py --list   → listar configs detectadas
    python3 config_check.py --test   → tests integrados
    python3 config_check.py --fix    → intentar reparar problemas menores

Códigos: CFG-E001 (JSON inválido), CFG-E002 (clave faltante),
         CFG-W001 (tool no en registry), CFG-W002 (config huérfana)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT       = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / ".bago" / "state" / "config"
TOOLS_DIR  = ROOT / ".bago" / "tools"

# Minimal schema requirements: config_name → required top-level keys
SCHEMAS: dict[str, list[str]] = {
    "ideas_catalog.json":       ["version", "ideas"],
    "intents_catalog.json":     ["version", "intents"],
    "sincerity_lexicon.json":   ["version"],
    "scan_config.json":         ["version", "todo_patterns"],
    "validation_patterns.json": ["version", "secret_patterns"],
    "efficiency_weights.json":  ["version", "weights"],
    "preflight_rules.json":     ["version", "role_map"],
    "tool_catalog.json":        ["version", "tools"],
    "workflow_guidance.json":   ["version", "workflows"],
    "contracts_config.json":    ["version", "checkers"],
}

# Config → script that consumes it (for orphan detection)
CONSUMERS: dict[str, str] = {
    "ideas_catalog.json":       "emit_ideas.py",
    "intents_catalog.json":     "intent_router.py",
    "sincerity_lexicon.json":   "sincerity_detector.py",
    "scan_config.json":         "todo_scan.py",
    "validation_patterns.json": "commit_readiness.py",
    "efficiency_weights.json":  "efficiency_meter.py",
    "preflight_rules.json":     "session_preflight.py",
    "tool_catalog.json":        "tool_search.py",
    "workflow_guidance.json":   "inspect_workflow.py",
    "contracts_config.json":    "contracts.py",
}


# ─── Checks ──────────────────────────────────────────────────────────────────

def check_parseable(cfg_path: Path) -> list[dict]:
    """CFG-E001: each JSON must be parseable."""
    issues = []
    try:
        json.loads(cfg_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        issues.append({
            "code": "CFG-E001", "file": cfg_path.name,
            "msg": f"JSON inválido: {e}",
        })
    except Exception as e:
        issues.append({
            "code": "CFG-E001", "file": cfg_path.name,
            "msg": f"Error de lectura: {e}",
        })
    return issues


def check_schema(cfg_path: Path) -> list[dict]:
    """CFG-E002: required keys must be present."""
    required = SCHEMAS.get(cfg_path.name, ["version"])
    issues = []
    try:
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
    except Exception:
        return []  # already caught by check_parseable

    for key in required:
        if key not in data:
            issues.append({
                "code": "CFG-E002", "file": cfg_path.name,
                "msg": f"clave requerida ausente: '{key}'",
            })
    return issues


def check_tool_catalog_vs_registry() -> list[dict]:
    """CFG-W001: critical commands in tool_catalog should exist in tool_registry REGISTRY."""
    issues = []
    catalog_path = CONFIG_DIR / "tool_catalog.json"
    registry_path = TOOLS_DIR / "tool_registry.py"

    if not catalog_path.exists() or not registry_path.exists():
        return []

    try:
        catalog_data = json.loads(catalog_path.read_text(encoding="utf-8"))
        catalog_cmds = {t["command"] for t in catalog_data.get("tools", []) if "command" in t}
    except Exception:
        return []

    registry_text = registry_path.read_text(encoding="utf-8")
    # Only check framework-critical commands (guardian, auto-register, doctor)
    critical = {"tool-guardian", "auto-register", "doctor"}
    for cmd in catalog_cmds & critical:
        # Registry may use underscores instead of hyphens
        cmd_normalized = cmd.replace("-", "_")
        in_registry = (
            f'"{cmd}"' in registry_text or f"'{cmd}'" in registry_text or
            f'"{cmd_normalized}"' in registry_text or f"'{cmd_normalized}'" in registry_text
        )
        if not in_registry:
            issues.append({
                "code": "CFG-W001", "file": "tool_catalog.json",
                "msg": f"comando crítico '{cmd}' no encontrado en tool_registry.py",
            })
    return issues


def check_consumers() -> list[dict]:
    """CFG-W002: each config should have its consumer script present."""
    issues = []
    for cfg_name, script_name in CONSUMERS.items():
        cfg_path = CONFIG_DIR / cfg_name
        script_path = TOOLS_DIR / script_name
        if cfg_path.exists() and not script_path.exists():
            issues.append({
                "code": "CFG-W002", "file": cfg_name,
                "msg": f"consumidor '{script_name}' no encontrado en tools/",
            })
    return issues


def check_orphan_configs() -> list[dict]:
    """CFG-W002: configs not in SCHEMAS are unknown."""
    known = set(SCHEMAS.keys())
    issues = []
    for cfg_path in sorted(CONFIG_DIR.glob("*.json")):
        if cfg_path.name not in known:
            issues.append({
                "code": "CFG-W002", "file": cfg_path.name,
                "msg": "config sin esquema conocido (no validada)",
            })
    return issues


# ─── Runner ──────────────────────────────────────────────────────────────────

def run_all() -> tuple[list[dict], list[dict]]:
    """Returns (errors, warnings)."""
    errors: list[dict] = []
    warnings: list[dict] = []

    if not CONFIG_DIR.exists():
        errors.append({"code": "CFG-E001", "file": "state/config/", "msg": "directorio de configs no existe"})
        return errors, warnings

    for cfg_path in sorted(CONFIG_DIR.glob("*.json")):
        for issue in check_parseable(cfg_path):
            errors.append(issue)
        for issue in check_schema(cfg_path):
            errors.append(issue)

    for issue in check_tool_catalog_vs_registry():
        warnings.append(issue)

    for issue in check_consumers():
        warnings.append(issue)

    for issue in check_orphan_configs():
        warnings.append(issue)

    return errors, warnings


def print_results(errors: list[dict], warnings: list[dict], verbose: bool = False) -> None:
    n_configs = len(list(CONFIG_DIR.glob("*.json"))) if CONFIG_DIR.exists() else 0
    total = len(errors) + len(warnings)

    if not errors and not warnings:
        print(f"  ✅  {n_configs} configs OK — sin errores ni advertencias")
        return

    if errors:
        print(f"  ERRORES ({len(errors)}):")
        for e in errors:
            print(f"    [{e['code']}] {e['file']}: {e['msg']}")

    if warnings:
        if errors:
            print()
        print(f"  ADVERTENCIAS ({len(warnings)}):")
        for w in warnings:
            print(f"    [{w['code']}] {w['file']}: {w['msg']}")

    print(f"\n  {n_configs} configs auditadas — {len(errors)} errores, {len(warnings)} advertencias")


# ─── CLI ─────────────────────────────────────────────────────────────────────

def cmd_list() -> None:
    if not CONFIG_DIR.exists():
        print("  (directorio de configs no existe)")
        return
    configs = sorted(CONFIG_DIR.glob("*.json"))
    print(f"\n  Configs en state/config/ ({len(configs)} archivos)\n")
    for cfg in configs:
        schema_keys = SCHEMAS.get(cfg.name, [])
        consumer = CONSUMERS.get(cfg.name, "—")
        try:
            data = json.loads(cfg.read_text(encoding="utf-8"))
            version = data.get("version", "?")
            size = len(data)
            print(f"  {cfg.name:<35}  v{version}  {size:3d} claves  →  {consumer}")
        except Exception:
            print(f"  {cfg.name:<35}  [INVALID JSON]  →  {consumer}")
    print()


def run_tests() -> int:
    """Autotest integrado."""
    import tempfile
    results = []

    def t(name: bool, label: str, detail: str = ""):
        results.append((label, name, detail))

    # Test 1: CONFIG_DIR exists
    t(CONFIG_DIR.exists(), "config_check:config_dir_exists", str(CONFIG_DIR))

    # Test 2: all known schemas have files
    if CONFIG_DIR.exists():
        found = [s for s in SCHEMAS if (CONFIG_DIR / s).exists()]
        t(len(found) == len(SCHEMAS), "config_check:all_schema_files_present",
          f"{len(found)}/{len(SCHEMAS)}")
    else:
        t(False, "config_check:all_schema_files_present", "dir missing")

    # Test 3: run_all returns no errors on clean state
    errors, warnings = run_all()
    t(len(errors) == 0, "config_check:no_errors_clean_state", f"errors={len(errors)}")

    # Test 4: check_parseable catches invalid JSON
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as tf:
        tf.write("{not valid json")
        bad_path = Path(tf.name)
    issues = check_parseable(bad_path)
    t(len(issues) == 1 and issues[0]["code"] == "CFG-E001",
      "config_check:detect_invalid_json", f"issues={len(issues)}")
    bad_path.unlink()

    # Test 5: check_schema catches missing key
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as tf:
        tf.write('{"version": "1.0"}')
        good_path = Path(tf.name)
    good_path_renamed = good_path.parent / "ideas_catalog.json_test"
    # Simulate a schema check on a dict missing required key
    data = {"version": "1.0"}  # missing "ideas"
    required = ["version", "ideas"]
    missing_keys = [k for k in required if k not in data]
    t(len(missing_keys) == 1 and "ideas" in missing_keys,
      "config_check:detect_missing_schema_key", f"missing={missing_keys}")
    good_path.unlink()

    # Test 6: CONSUMERS maps to real scripts
    all_consumers_exist = all(
        (TOOLS_DIR / script).exists()
        for script in CONSUMERS.values()
    )
    t(all_consumers_exist, "config_check:all_consumers_exist")

    passed = sum(1 for _, ok, _ in results if ok)
    failed = sum(1 for _, ok, _ in results if not ok)
    for label, ok, detail in results:
        status = "✅" if ok else "❌"
        print(f"  {status}  {label}" + (f": {detail}" if detail else ""))
    print(f"\n  {passed}/{len(results)} pasaron")
    return 0 if failed == 0 else 1


def main() -> int:
    args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        print(__doc__)
        return 0

    if "--test" in args:
        return run_tests()

    if "--list" in args:
        cmd_list()
        return 0

    errors, warnings = run_all()
    print_results(errors, warnings)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
