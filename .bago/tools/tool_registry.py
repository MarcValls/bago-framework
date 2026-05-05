#!/usr/bin/env python3
"""tool_registry.py — Registro central de herramientas BAGO.

Fuente ÚNICA de verdad para:
  - Mapping cmd → módulo Python (reemplaza COMMANDS dict en bago)
  - Descripción por herramienta
  - Pre-flight checks declarativos por comando
  - Lista canónica de tools internas (excluidas de guardian/manifest)

Importado por: bago (script), tool_guardian.py, auto_register.py,
               contracts.py, ci_generator.py

Uso:
    python3 tool_registry.py --list          # lista todos los comandos
    python3 tool_registry.py --json          # JSON del registro completo
    python3 tool_registry.py --test          # self-tests (7/7)
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

TOOLS_DIR = Path(__file__).parent
BAGO_ROOT = TOOLS_DIR.parent        # .bago/
REPO_ROOT = BAGO_ROOT.parent        # repo raíz


# ── Declarative pre-flight check ─────────────────────────────────────────────

@dataclass
class PreflightCheck:
    """A single declarative pre-flight condition."""
    kind: str       # "file" | "env" | "cmd"
    value: str      # path | env-var name | command name
    severity: str = "error"   # "error" | "warning"
    message: str = ""         # custom message (empty → auto-generated)


# ── Tool descriptor ───────────────────────────────────────────────────────────

@dataclass
class ToolEntry:
    """Full descriptor for a user-facing BAGO tool."""
    cmd: str                              # Public CLI command (bago <cmd>)
    module: str                           # Python module stem (without .py)
    description: str
    preflight: list[PreflightCheck] = field(default_factory=list)
    schema: dict = field(default_factory=dict)   # Arg schema (future use)


# ── Internal tools — excluded from guardian / manifest / integration_tests ────
# Single canonical source; all other files should import this set.
INTERNAL_TOOLS: frozenset[str] = frozenset({
    "tool_registry",
    "preflight",
    "session_logger",
    "integration_tests",
    "bago_utils",
    "bago_banner",
    "auto_register",
    "ci_generator",
    "tool_guardian",
    "contracts",
    "bago_start",
    "bago_on",
    "bago_debug",
    "bago_watch",
    "bago_chat_server",
    "bago_ask",
    "bago_lint_cli",
    "bago_search",
    "legacy_fixer",
    "bago_config",
})


# ── Canonical registry ────────────────────────────────────────────────────────
# Add new tools here; auto_register.py will append entries automatically.

REGISTRY: dict[str, ToolEntry] = {
    "dashboard": ToolEntry(
        cmd="dashboard", module="pack_dashboard",
        description="Muestra el dashboard del pack",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "pack_dashboard.py"))],
    ),
    "ideas": ToolEntry(
        cmd="ideas", module="emit_ideas",
        description="Emite ideas W2",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "emit_ideas.py"))],
    ),
    "cosecha": ToolEntry(
        cmd="cosecha", module="cosecha",
        description="Cosecha de artefactos del proyecto",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "cosecha.py"))],
    ),
    "detector": ToolEntry(
        cmd="detector", module="context_detector",
        description="Detector de contexto del repo",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "context_detector.py"))],
    ),
    "validate": ToolEntry(
        cmd="validate", module="validate_pack",
        description="Verifica el pack (solo lectura)",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "validate_pack.py"))],
    ),
    "sync": ToolEntry(
        cmd="sync", module="sync_pack_metadata",
        description="Regenera TREE.txt y CHECKSUMS",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "sync_pack_metadata.py"))],
    ),
    "check": ToolEntry(
        cmd="check", module="check_validate_purity",
        description="Chequeo estático de pureza",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "check_validate_purity.py"))],
    ),
    "health": ToolEntry(
        cmd="health", module="health_score",
        description="Health score del pack",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "health_score.py"))],
    ),
    "audit": ToolEntry(
        cmd="audit", module="audit_v2",
        description="Auditoría completa del framework BAGO",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "audit_v2.py"))],
    ),
    "workflow": ToolEntry(
        cmd="workflow", module="workflow_selector",
        description="Selector de workflow (interactivo)",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "workflow_selector.py"))],
    ),
    "stale": ToolEntry(
        cmd="stale", module="stale_detector",
        description="Detecta tools obsoletas o sin mantenimiento",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "stale_detector.py"))],
    ),
    "v2": ToolEntry(
        cmd="v2", module="v2_close_checklist",
        description="Checklist de cierre v2",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "v2_close_checklist.py"))],
    ),
    "task": ToolEntry(
        cmd="task", module="show_task",
        description="Muestra la tarea W2 pendiente",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "show_task.py"))],
    ),
    "stability": ToolEntry(
        cmd="stability", module="stability_summary",
        description="Resumen de estabilidad del pack",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "stability_summary.py"))],
    ),
    "session": ToolEntry(
        cmd="session", module="session_opener",
        description="Abre sesión W2 con preflight pre-rellenado",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "session_opener.py"))],
    ),
    "efficiency": ToolEntry(
        cmd="efficiency", module="efficiency_meter",
        description="Medidor de eficiencia inter-versiones",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "efficiency_meter.py"))],
    ),
    "sincerity": ToolEntry(
        cmd="sincerity", module="sincerity_detector",
        description="Centinela de sinceridad: detecta sincofancía en docs .md",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "sincerity_detector.py"))],
    ),
    "cabinet": ToolEntry(
        cmd="cabinet", module="cabinet_orchestrator",
        description="Gabinete BAGO: orquesta agentes en paralelo e informa unificado",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "cabinet_orchestrator.py"))],
    ),
    # ── Importadas desde BAGO_CAJAFISICA (evaluadas OK, cubren gaps reales) ──
    "git": ToolEntry(
        cmd="git", module="git_context",
        description="Contexto git (log/diff/brief) para workflows",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "git_context.py"))],
    ),
    "deps": ToolEntry(
        cmd="deps", module="dep_audit",
        description="Auditoría de dependencias (requirements/pyproject)",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "dep_audit.py"))],
    ),
    "naming": ToolEntry(
        cmd="naming", module="naming_check",
        description="Lint de convenciones de nombres",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "naming_check.py"))],
    ),
    "types": ToolEntry(
        cmd="types", module="type_check",
        description="Chequeo de tipos estáticos",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "type_check.py"))],
    ),
    "map": ToolEntry(
        cmd="map", module="context_map",
        description="Mapa de contexto del repositorio",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "context_map.py"))],
    ),
    "doctor": ToolEntry(
        cmd="doctor", module="doctor",
        description="Diagnóstico general con opción --fix",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "doctor.py"))],
    ),
    "report": ToolEntry(
        cmd="report", module="health_report",
        description="Health report en Markdown",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "health_report.py"))],
    ),
    "commit": ToolEntry(
        cmd="commit", module="commit_readiness",
        description="Evaluación de preparación para commit",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "commit_readiness.py"))],
    ),
    "flow": ToolEntry(
        cmd="flow", module="flow",
        description="Flowchart ASCII de workflows + gestión de estado activo (start/done/status)",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "flow.py"))],
    ),
    "find-tool": ToolEntry(
        cmd="find-tool", module="tool_search",
        description="Busca la herramienta BAGO adecuada para un problema",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "tool_search.py"))],
    ),
    "ask": ToolEntry(
        cmd="ask", module="intent_router",
        description="Router lenguaje natural → tools BAGO",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "intent_router.py"))],
    ),
    "rules": ToolEntry(
        cmd="rules", module="rule_catalog",
        description="Catálogo de reglas BAGO",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "rule_catalog.py"))],
    ),
    "peer": ToolEntry(
        cmd="peer", module="peer_link",
        description="Comunicacion peer-to-peer LAN (serve/discover/ping/send/chat)",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "peer_link.py"))],
    ),
    "banner": ToolEntry(
        cmd="banner", module="bago_banner",
        description="Muestra el banner animado de BAGO con estado actual",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "bago_banner.py"))],
    ),
    "session_close": ToolEntry(
        cmd="session_close", module="session_close_generator",
        description="Genera el informe de cierre de sesion BAGO",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "session_close_generator.py"))],
    ),
    "image_gen": ToolEntry(
        cmd="image_gen", module="image_gen",
        description="Generador de imagenes PNG local sin API",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "image_gen.py"))],
    ),
    "code-quality": ToolEntry(
        cmd="code-quality", module="code_quality_orchestrator",
        description="Orquestador de calidad de código — ejecuta agentes especializados",
        preflight=[
            PreflightCheck("file", str(TOOLS_DIR / "code_quality_orchestrator.py")),
            PreflightCheck("file", str(BAGO_ROOT / "agents" / "ANALISTA_Contexto.md"),
                           severity="warning", message="Agente ANALISTA_Contexto no encontrado en .bago/agents/"),
        ],
    ),
    "consistency": ToolEntry(
        cmd="consistency", module="bago_consistency_check",
        description="Guard anti-drift: valida CI, preflight, README y badge del framework",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "bago_consistency_check.py"))],
    ),
    "config-check": ToolEntry(
        cmd="config-check", module="config_check",
        description="Valida integridad de configs JSON en state/config/ y cruza con registry",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "config_check.py"))],
    ),
    "why": ToolEntry(
        cmd="why", module="why",
        description="Explica qué hace un comando BAGO, cuándo usarlo y sus relaciones",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "why.py"))],
    ),
    "db": ToolEntry(
        cmd="db", module="bago_db",
        description="Gestiona bago.db: estado de ideas, historial guardian, init/status/reset",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "bago_db.py"))],
    ),
    "hello": ToolEntry(
        cmd="hello", module="bago_hello",
        description="Guía de inicio para nuevos usuarios y recordatorio de comandos esenciales",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "bago_hello.py"))],
    ),
    "next": ToolEntry(
        cmd="next", module="bago_next",
        description="Meta-comando de ciclo mínimo: elige idea + acepta + inicia flujo en un paso",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "bago_next.py"))],
    ),
    "done": ToolEntry(
        cmd="done", module="show_task",
        description="Cierra la tarea actual y muestra el siguiente paso sugerido",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "show_task.py"))],
    ),
    "status": ToolEntry(
        cmd="status", module="flow",
        description="Estado actual: flujo activo, tarea pendiente y salud del sistema",
        preflight=[PreflightCheck("file", str(TOOLS_DIR / "flow.py"))],
    ),
}


# ── Public API ────────────────────────────────────────────────────────────────

def get_commands() -> dict[str, list[str]]:
    """Returns COMMANDS-compatible dict for the bago script.

    Format: {"cmd": ["python3", "/path/to/module.py", ...extra_args]}
    """
    _extra_args: dict[str, list[str]] = {
        "done":   ["--done"],
        "status": ["status"],
    }
    result = {}
    for name, entry in REGISTRY.items():
        cmd = ["python3", str(TOOLS_DIR / f"{entry.module}.py")]
        if name in _extra_args:
            cmd += _extra_args[name]
        result[name] = cmd
    return result


def get_cmd_names() -> list[str]:
    """Sorted list of all registered public command names."""
    return sorted(REGISTRY.keys())


def load_registry(registry_path: "Path | None" = None) -> "dict[str, ToolEntry]":
    """Load REGISTRY from an explicit path via importlib (no sys.path needed).

    Falls back to this module's REGISTRY if registry_path is None or missing.
    """
    import importlib.util
    path = registry_path or Path(__file__)
    if not path.exists():
        return REGISTRY
    spec = importlib.util.spec_from_file_location("_tool_registry_loaded", path)
    if spec is None:
        return REGISTRY
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return getattr(mod, "REGISTRY", REGISTRY)
    except Exception:
        return REGISTRY


# ── CLI ───────────────────────────────────────────────────────────────────────

def _cmd_list() -> None:
    print("  BAGO — Registro central de herramientas")
    print(f"  {'CMD':<18} {'MÓDULO':<28} DESCRIPCIÓN")
    print("  " + "─" * 76)
    for name, entry in sorted(REGISTRY.items()):
        print(f"  {name:<18} {entry.module:<28} {entry.description}")
    print(f"\n  Comandos registrados: {len(REGISTRY)}")
    print(f"  Herramientas internas: {len(INTERNAL_TOOLS)}")


def _cmd_json() -> None:
    out = {
        "total": len(REGISTRY),
        "internal_count": len(INTERNAL_TOOLS),
        "internal_tools": sorted(INTERNAL_TOOLS),
        "tools": {
            name: {
                "cmd": e.cmd,
                "module": e.module,
                "description": e.description,
                "preflight": [
                    {"kind": p.kind, "value": p.value, "severity": p.severity}
                    for p in e.preflight
                ],
            }
            for name, e in sorted(REGISTRY.items())
        },
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))


def _self_tests() -> None:
    results: list[dict] = []

    def _check(name: str, cond: bool, msg: str) -> None:
        results.append({"name": name, "passed": cond, "message": msg})
        print(f"  {'✅' if cond else '❌'} {name}: {msg}")

    # T1: REGISTRY non-empty
    _check("T1:registry-non-empty", len(REGISTRY) > 0,
           f"{len(REGISTRY)} entries in REGISTRY")

    # T2: every entry's cmd matches its dict key
    mismatches = [k for k, v in REGISTRY.items() if v.cmd != k]
    _check("T2:cmd-key-consistency", not mismatches,
           "all cmd == key" if not mismatches else f"mismatches: {mismatches}")

    # T3: no duplicate modules
    modules = [e.module for e in REGISTRY.values()]
    dupes = {m for m in modules if modules.count(m) > 1}
    _check("T3:no-duplicate-modules", not dupes,
           "no duplicate modules" if not dupes else f"duplicates: {dupes}")

    # T4: get_commands() returns python3 + .py format
    cmds = get_commands()
    fmt_ok = all(
        isinstance(v, list) and len(v) == 2
        and v[0] == "python3" and v[1].endswith(".py")
        for v in cmds.values()
    )
    _check("T4:get-commands-format", fmt_ok,
           f"{len(cmds)} commands with python3+.py format")

    # T5: INTERNAL_TOOLS are all strings and non-empty
    _check("T5:internal-tools-valid",
           bool(INTERNAL_TOOLS) and all(isinstance(t, str) for t in INTERNAL_TOOLS),
           f"{len(INTERNAL_TOOLS)} internal tools, all strings")

    # T6: new framework modules are in INTERNAL_TOOLS
    new_mods = {"preflight", "session_logger", "tool_registry"}
    ok = new_mods.issubset(INTERNAL_TOOLS)
    _check("T6:new-modules-in-internal", ok,
           f"{new_mods} ⊆ INTERNAL_TOOLS")

    # T7: get_cmd_names() == REGISTRY keys
    _check("T7:cmd-names-consistent",
           set(get_cmd_names()) == set(REGISTRY.keys()),
           "get_cmd_names() matches REGISTRY keys")

    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    print(f"\n  {passed}/{total} tests pasaron")
    print(json.dumps({"tool": "tool_registry", "status": "ok" if passed == total else "fail",
                      "checks": results}))
    sys.exit(0 if passed == total else 1)


def main() -> None:
    if "--test" in sys.argv:
        _self_tests()
    elif "--json" in sys.argv:
        _cmd_json()
    else:
        _cmd_list()


if __name__ == "__main__":
    main()
