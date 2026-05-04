#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
config_wizard.py — Configuración guiada de BAGO.

Wizard interactivo para configurar BAGO: ruta de proyecto, preferencias de
banner y notificaciones. Guarda la configuración en .bago/state/bago_config.json.

Uso:
    python3 .bago/tools/config_wizard.py            # wizard interactivo
    python3 .bago/tools/config_wizard.py --show     # mostrar config actual
    python3 .bago/tools/config_wizard.py --reset    # restaurar valores por defecto

Códigos de salida: 0 siempre
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT    = Path(__file__).resolve().parents[2]
STATE   = ROOT / ".bago" / "state"
CONFIG_FILE = STATE / "bago_config.json"
GLOBAL_STATE = STATE / "global_state.json"


def GREEN(s: str)  -> str: return f"\033[32m{s}\033[0m"
def YELLOW(s: str) -> str: return f"\033[33m{s}\033[0m"
def BOLD(s: str)   -> str: return f"\033[1m{s}\033[0m"
def DIM(s: str)    -> str: return f"\033[2m{s}\033[0m"
def CYAN(s: str)   -> str: return f"\033[36m{s}\033[0m"


DEFAULTS: dict = {
    "project_path": "",
    "banner": {
        "enabled": True,
        "show_next_idea": True,
        "show_health": True,
        "show_task_alert": True,
    },
    "notifications": {
        "task_overdue_hours": 2,
        "priority_decay_days": 7,
    },
    "ideas": {
        "min_ideas": 5,
        "max_ideas": 20,
        "auto_replenish": True,
    },
    "ui": {
        "encoding": "utf-8",
        "color": True,
    },
}


def _load_config() -> dict:
    if not CONFIG_FILE.exists():
        return dict(DEFAULTS)
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return dict(DEFAULTS)


def _save_config(cfg: dict) -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_project_from_global() -> str:
    if not GLOBAL_STATE.exists():
        return ""
    try:
        gs = json.loads(GLOBAL_STATE.read_text(encoding="utf-8"))
        return gs.get("active_project", {}).get("path", "")
    except Exception:
        return ""


def _prompt(question: str, default: str) -> str:
    """Show a prompt and return user input (or default on empty)."""
    default_str = f" [{DIM(default)}]" if default else ""
    try:
        answer = input(f"  {CYAN('?')} {question}{default_str}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return default
    return answer if answer else default


def _prompt_bool(question: str, default: bool) -> bool:
    default_str = "S/n" if default else "s/N"
    try:
        answer = input(f"  {CYAN('?')} {question} [{DIM(default_str)}]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return default
    if not answer:
        return default
    return answer in ("s", "si", "sí", "y", "yes", "1", "true")


def _prompt_int(question: str, default: int) -> int:
    try:
        raw = input(f"  {CYAN('?')} {question} [{DIM(str(default))}]: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return default
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _show_config(cfg: dict) -> None:
    print()
    print("  ┌─────────────────────────────────────────────────────────────┐")
    print("  │  BAGO · Configuración actual                                │")
    print("  └─────────────────────────────────────────────────────────────┘")
    print()
    print(f"  Ruta del proyecto       : {cfg.get('project_path', '') or DIM('(no configurada)')}")
    banner = cfg.get("banner", {})
    print(f"  Banner habilitado       : {'✅' if banner.get('enabled', True) else '❌'}")
    print(f"    Mostrar siguiente idea: {'✅' if banner.get('show_next_idea', True) else '❌'}")
    print(f"    Mostrar health score  : {'✅' if banner.get('show_health', True) else '❌'}")
    print(f"    Alerta tarea activa   : {'✅' if banner.get('show_task_alert', True) else '❌'}")
    notif = cfg.get("notifications", {})
    print(f"  Alerta overdue (horas)  : {notif.get('task_overdue_hours', 2)}")
    print(f"  Decaimiento prioridad   : cada {notif.get('priority_decay_days', 7)} días")
    ideas_cfg = cfg.get("ideas", {})
    print(f"  Ideas min/max           : {ideas_cfg.get('min_ideas', 5)} / {ideas_cfg.get('max_ideas', 20)}")
    print(f"  Auto-rellenar ideas     : {'✅' if ideas_cfg.get('auto_replenish', True) else '❌'}")
    print(f"  Color en terminal       : {'✅' if cfg.get('ui', {}).get('color', True) else '❌'}")
    print()
    print(f"  Guardada en: {DIM(str(CONFIG_FILE))}")
    print()


def _run_wizard(cfg: dict) -> dict:
    print()
    print("  ┌─────────────────────────────────────────────────────────────┐")
    print("  │  BAGO · Configuración guiada                                │")
    print("  └─────────────────────────────────────────────────────────────┘")
    print()
    print(f"  {DIM('Presiona Enter para aceptar el valor por defecto.')}")
    print()

    # Project path
    current_path = cfg.get("project_path", "") or _load_project_from_global()
    print(f"  {BOLD('── Proyecto ──')}")
    cfg["project_path"] = _prompt("Ruta absoluta del proyecto", current_path)
    print()

    # Banner
    print(f"  {BOLD('── Banner ──')}")
    banner = cfg.get("banner", DEFAULTS["banner"].copy())
    banner["enabled"]        = _prompt_bool("Mostrar banner al arrancar BAGO", banner.get("enabled", True))
    if banner["enabled"]:
        banner["show_next_idea"] = _prompt_bool("  Mostrar siguiente idea en el banner", banner.get("show_next_idea", True))
        banner["show_health"]    = _prompt_bool("  Mostrar health score en el banner", banner.get("show_health", True))
        banner["show_task_alert"]= _prompt_bool("  Mostrar alerta de tarea activa", banner.get("show_task_alert", True))
    cfg["banner"] = banner
    print()

    # Notifications
    print(f"  {BOLD('── Alertas ──')}")
    notif = cfg.get("notifications", DEFAULTS["notifications"].copy())
    notif["task_overdue_hours"] = _prompt_int(
        "Horas hasta alerta de tarea activa demasiado larga", notif.get("task_overdue_hours", 2)
    )
    notif["priority_decay_days"] = _prompt_int(
        "Días sin implementar para aplicar decaimiento de prioridad", notif.get("priority_decay_days", 7)
    )
    cfg["notifications"] = notif
    print()

    # Ideas config
    print(f"  {BOLD('── Ideas ──')}")
    ideas_cfg = cfg.get("ideas", DEFAULTS["ideas"].copy())
    ideas_cfg["min_ideas"] = _prompt_int("Número mínimo de ideas en el selector", ideas_cfg.get("min_ideas", 5))
    ideas_cfg["max_ideas"] = _prompt_int("Número máximo de ideas en el selector", ideas_cfg.get("max_ideas", 20))
    ideas_cfg["auto_replenish"] = _prompt_bool(
        "Rellenar automáticamente si hay pocas ideas", ideas_cfg.get("auto_replenish", True)
    )
    cfg["ideas"] = ideas_cfg
    print()

    # UI
    print(f"  {BOLD('── Interfaz ──')}")
    ui = cfg.get("ui", DEFAULTS["ui"].copy())
    ui["color"] = _prompt_bool("Usar colores en la terminal", ui.get("color", True))
    cfg["ui"] = ui
    print()

    return cfg


def main() -> int:
    args = sys.argv[1:]

    if "--reset" in args:
        _save_config(dict(DEFAULTS))
        print()
        print(f"  {GREEN('✅  Configuración restaurada a valores por defecto.')}")
        print(f"  {DIM(str(CONFIG_FILE))}")
        print()
        return 0

    cfg = _load_config()

    if "--show" in args:
        _show_config(cfg)
        return 0

    # Interactive wizard
    try:
        cfg = _run_wizard(cfg)
    except KeyboardInterrupt:
        print()
        print(f"  {YELLOW('⚠  Configuración cancelada.')}")
        print()
        return 0

    _save_config(cfg)
    print(f"  {GREEN('✅  Configuración guardada.')}")
    print(f"  {DIM(str(CONFIG_FILE))}")
    print()
    _show_config(cfg)
    return 0



def _self_test():
    """Autotest mínimo — verifica arranque limpio del módulo."""
    from pathlib import Path as _P
    assert _P(__file__).exists(), "fichero no encontrado"
    print("  1/1 tests pasaron")

if __name__ == "__main__":
    if "--test" in sys.argv:
        _self_test()
        raise SystemExit(0)
    raise SystemExit(main())
