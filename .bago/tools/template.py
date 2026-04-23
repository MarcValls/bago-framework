#!/usr/bin/env python3
"""
bago template — plantillas para nuevas sesiones con campos prefilled.

Uso:
    bago template list                     → plantillas disponibles
    bago template show <nombre>            → ver plantilla
    bago template new <nombre>             → crea sesión a partir de plantilla
    bago template create <nombre>          → define nueva plantilla interactivamente
    bago template delete <nombre>          → elimina plantilla
    bago template --test                   → tests integrados
"""
import argparse, json, sys, datetime
from pathlib import Path

BAGO_ROOT   = Path(__file__).parent.parent
TMPL_DIR    = BAGO_ROOT / "state" / "templates"
SESS_DIR    = BAGO_ROOT / "state" / "sessions"
TMPL_DIR.mkdir(parents=True, exist_ok=True)

BOLD  = "\033[1m"
DIM   = "\033[2m"
CYAN  = "\033[36m"
GREEN = "\033[32m"
RESET = "\033[0m"

# Plantillas de fábrica incluidas con el framework
BUILTIN_TEMPLATES = {
    "sprint": {
        "name": "sprint",
        "description": "Sesión de sprint productivo con objetivos claros",
        "user_goal": "Implementar [OBJETIVO] para [PROPÓSITO]",
        "roles": ["role_architect", "role_generator", "role_validator"],
        "workflow": "W7_FOCO_SESION",
        "tags": ["sprint", "generativo"],
        "artifacts_expected": ["tools/<nombre>.py", "state/changes/BAGO-CHG-XXX.json"],
        "decisions_expected": ["Elegir approach para [OBJETIVO]"],
        "checklist": [
            "Revisar bago health antes de empezar",
            "Definir criterio de done antes de codificar",
            "Tests --test al final de cada herramienta",
        ],
    },
    "analysis": {
        "name": "analysis",
        "description": "Sesión de análisis y diagnóstico del sistema",
        "user_goal": "Analizar [COMPONENTE] para identificar [PROBLEMA/OPORTUNIDAD]",
        "roles": ["role_analyst", "role_auditor"],
        "workflow": "W2_IMPLEMENTACION_CONTROLADA",
        "tags": ["analisis", "diagnostico"],
        "artifacts_expected": ["docs/ANALYSIS-<fecha>.md"],
        "decisions_expected": ["Diagnóstico de [COMPONENTE]"],
        "checklist": [
            "Ejecutar bago doctor antes de analizar",
            "Documentar hallazgos en docs/",
            "Registrar decisiones en la sesión",
        ],
    },
    "hotfix": {
        "name": "hotfix",
        "description": "Corrección urgente de bug o inconsistencia crítica",
        "user_goal": "Corregir [BUG] en [COMPONENTE] para restaurar funcionamiento",
        "roles": ["role_validator", "role_generator"],
        "workflow": "W2_IMPLEMENTACION_CONTROLADA",
        "tags": ["hotfix", "critico"],
        "artifacts_expected": ["state/changes/BAGO-CHG-XXX.json"],
        "decisions_expected": ["Root cause de [BUG]", "Fix aplicado"],
        "checklist": [
            "Reproducir el bug antes de tocar código",
            "bago validate antes y después del fix",
            "bago test para confirmar no hay regresión",
        ],
    },
    "review": {
        "name": "review",
        "description": "Revisión periódica del estado del pack",
        "user_goal": "Revisar estado de [PERÍODO] y planificar próximos pasos",
        "roles": ["role_analyst", "role_auditor"],
        "workflow": "W9_COSECHA",
        "tags": ["revision", "organizativo"],
        "artifacts_expected": ["docs/REVIEW-<fecha>.md"],
        "decisions_expected": ["Balance del período", "Prioridades siguiente período"],
        "checklist": [
            "Ejecutar bago review --period week",
            "Ejecutar bago stats para métricas",
            "Ejecutar bago velocity para tendencias",
        ],
    },
}


def _load_templates() -> dict:
    templates = dict(BUILTIN_TEMPLATES)
    for f in TMPL_DIR.glob("*.json"):
        try:
            t = json.loads(f.read_text())
            templates[t["name"]] = t
        except Exception:
            pass
    return templates


def _next_session_id() -> str:
    existing = sorted(SESS_DIR.glob("SES-2*.json"))
    if not existing:
        return "SES-2026-001"
    # Extract last number
    import re
    nums = []
    for f in existing:
        m = re.search(r"SES-(\d{4})-(\d+)", f.stem)
        if m:
            nums.append(int(m.group(2)))
    n = max(nums) + 1 if nums else 1
    year = datetime.date.today().year
    return f"SES-{year}-{n:03d}"


def cmd_list():
    templates = _load_templates()
    print(f"\n  {BOLD}Plantillas disponibles ({len(templates)}){RESET}\n")
    for name, t in templates.items():
        builtin = "  [builtin]" if name in BUILTIN_TEMPLATES else ""
        print(f"  {CYAN}{name:15s}{RESET}  {t.get('description','')}{DIM}{builtin}{RESET}")
    print()


def cmd_show(name: str):
    templates = _load_templates()
    if name not in templates:
        print(f"Plantilla '{name}' no encontrada.")
        raise SystemExit(1)
    t = templates[name]
    print(f"\n  {BOLD}{t['name']}{RESET}  {DIM}{t.get('description','')}{RESET}")
    print(f"\n  user_goal:  {t.get('user_goal','')}")
    print(f"  workflow:   {t.get('workflow','')}")
    print(f"  roles:      {', '.join(t.get('roles', []))}")
    print(f"  tags:       {', '.join(t.get('tags', []))}")
    if t.get("artifacts_expected"):
        print(f"\n  Artefactos esperados:")
        for a in t["artifacts_expected"]: print(f"    - {a}")
    if t.get("checklist"):
        print(f"\n  Checklist:")
        for c in t["checklist"]: print(f"    □ {c}")
    print()


def cmd_new(name: str, dry_run: bool = False):
    templates = _load_templates()
    if name not in templates:
        print(f"Plantilla '{name}' no encontrada.")
        raise SystemExit(1)
    t = templates[name]
    now = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    sid = _next_session_id()
    session = {
        "id":          sid,
        "status":      "open",
        "user_goal":   t.get("user_goal", ""),
        "roles":       t.get("roles", []),
        "workflow":    t.get("workflow", ""),
        "tags":        t.get("tags", []),
        "artifacts":   [],
        "decisions":   [],
        "template":    name,
        "created_at":  now,
        "updated_at":  now,
        "checklist":   t.get("checklist", []),
        "artifacts_expected": t.get("artifacts_expected", []),
    }
    if not dry_run:
        out = SESS_DIR / f"{sid}.json"
        out.write_text(json.dumps(session, indent=2, ensure_ascii=False) + "\n")
        print(f"\n  {GREEN}✓{RESET} Sesión {BOLD}{sid}{RESET} creada desde plantilla '{name}'")
    else:
        print(f"\n  {DIM}[DRY-RUN]{RESET} Sesión {BOLD}{sid}{RESET} (no creada)")
    print(f"  user_goal: {session['user_goal']}")
    print(f"  workflow:  {session['workflow']}")
    print(f"\n  Checklist de arranque:")
    for c in session.get("checklist", []):
        print(f"    □ {c}")
    print()
    return session


def cmd_create(name: str):
    """Crear plantilla custom desde stdin."""
    print(f"\n  Creando plantilla '{name}'")
    description = input("  Descripción: ").strip()
    user_goal   = input("  user_goal template: ").strip()
    workflow    = input("  Workflow (e.g. W7_FOCO_SESION): ").strip()
    t = {
        "name": name, "description": description,
        "user_goal": user_goal, "workflow": workflow,
        "roles": [], "tags": [name], "artifacts_expected": [], "checklist": [],
    }
    (TMPL_DIR / f"{name}.json").write_text(json.dumps(t, indent=2, ensure_ascii=False) + "\n")
    print(f"  {GREEN}✓{RESET} Plantilla '{name}' guardada.\n")


def cmd_delete(name: str):
    if name in BUILTIN_TEMPLATES:
        print(f"No se puede eliminar plantilla builtin '{name}'.")
        raise SystemExit(1)
    f = TMPL_DIR / f"{name}.json"
    if not f.exists():
        print(f"Plantilla '{name}' no encontrada.")
        raise SystemExit(1)
    f.unlink()
    print(f"  Plantilla '{name}' eliminada.")


def run_tests():
    import tempfile, shutil
    print("Ejecutando tests de template.py...")
    errors = 0
    def ok(name): print(f"  OK: {name}")
    def fail(name, msg):
        nonlocal errors; errors += 1; print(f"  FAIL: {name} — {msg}")

    # Test 1: builtin templates loaded
    templates = _load_templates()
    if set(BUILTIN_TEMPLATES.keys()).issubset(templates.keys()):
        ok("template:builtins_loaded")
    else:
        fail("template:builtins_loaded", str(templates.keys()))

    # Test 2: sprint template has required fields
    t = templates["sprint"]
    for k in ("user_goal","roles","workflow","checklist"):
        if k not in t:
            fail("template:sprint_fields", f"missing {k}"); break
    else:
        ok("template:sprint_fields")

    # Test 3: cmd_new dry-run creates session structure
    import tempfile as tmp_mod
    tmpdir = Path(tmp_mod.mkdtemp())
    orig_sess = globals().get("SESS_DIR")

    import importlib.util
    spec = importlib.util.spec_from_file_location("tmpl", Path(__file__))
    m    = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.SESS_DIR  = tmpdir
    m.TMPL_DIR  = tmpdir / "templates"
    m.TMPL_DIR.mkdir()

    sess = m.cmd_new("sprint", dry_run=True)
    if sess and sess.get("template") == "sprint" and "user_goal" in sess:
        ok("template:cmd_new_structure")
    else:
        fail("template:cmd_new_structure", str(sess))

    # Test 4: cmd_new creates file when not dry-run
    m.cmd_new("analysis", dry_run=False)
    files = list(tmpdir.glob("SES-*.json"))
    if len(files) == 1:
        ok("template:cmd_new_creates_file")
    else:
        fail("template:cmd_new_creates_file", str(files))

    # Test 5: custom template save/load
    custom = {"name":"mytest","description":"d","user_goal":"g","workflow":"W7",
              "roles":[],"tags":[],"artifacts_expected":[],"checklist":[]}
    (m.TMPL_DIR / "mytest.json").write_text(json.dumps(custom))
    loaded = m._load_templates()
    if "mytest" in loaded:
        ok("template:custom_load")
    else:
        fail("template:custom_load", str(loaded.keys()))

    shutil.rmtree(tmpdir)
    total = 5; passed = total - errors
    print(f"\n  {passed}/{total} tests pasaron")
    if errors: raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(prog="bago template", add_help=False)
    parser.add_argument("subcmd", nargs="?", default="list",
                        choices=["list","show","new","create","delete"])
    parser.add_argument("name", nargs="?", default=None)
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    if args.test:
        run_tests(); return
    if args.subcmd == "list" or (not args.subcmd):
        cmd_list()
    elif args.subcmd == "show":
        if not args.name: print("Uso: bago template show <nombre>"); raise SystemExit(1)
        cmd_show(args.name)
    elif args.subcmd == "new":
        if not args.name: print("Uso: bago template new <nombre>"); raise SystemExit(1)
        cmd_new(args.name)
    elif args.subcmd == "create":
        if not args.name: print("Uso: bago template create <nombre>"); raise SystemExit(1)
        cmd_create(args.name)
    elif args.subcmd == "delete":
        if not args.name: print("Uso: bago template delete <nombre>"); raise SystemExit(1)
        cmd_delete(args.name)

if __name__ == "__main__":
    main()