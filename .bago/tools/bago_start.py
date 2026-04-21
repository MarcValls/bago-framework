#!/usr/bin/env python3
"""
bago_start.py — Menú interactivo principal de BAGO
Punto de entrada amigable para usuarios.

Uso:
  python3 .bago/tools/bago_start.py
  ./bago start
"""

import json, subprocess, sys, webbrowser
from pathlib import Path

BAGO_ROOT = Path(__file__).resolve().parent.parent
TOOLS     = BAGO_ROOT / "tools"

# ─── Workspace selector (importación dinámica) ────────────────────────────────
def _select_workspace() -> None:
    """Llama al selector de workspace antes de mostrar el menú principal."""
    import importlib.util
    sel_path = TOOLS / "workspace_selector.py"
    if not sel_path.exists():
        return
    spec = importlib.util.spec_from_file_location("workspace_selector", sel_path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.select(skip_if_set=False)

# ─── Colores ANSI ─────────────────────────────────────────────────────────────
USE_COLOR = sys.stdout.isatty()

def _c(code, text):
    if not USE_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"

CYAN   = lambda t: _c("1;36", t)
BLUE   = lambda t: _c("1;34", t)
GREEN  = lambda t: _c("1;32", t)
YELLOW = lambda t: _c("1;33", t)
BOLD   = lambda t: _c("1",    t)
DIM    = lambda t: _c("2",    t)

# ─── Menú ─────────────────────────────────────────────────────────────────────

MENU = """
╔══════════════════════════════════════════════════════╗
║         BAGO · ¿Qué quieres hacer hoy?              ║
╠══════════════════════════════════════════════════════╣
║  1. 🚀 Ver ideas y comenzar trabajo                  ║
║  2. 📊 Dashboard y estado del proyecto               ║
║  3. 🔍 Validar salud del pack                        ║
║  4. 🌐 Abrir BAGO Viewer (web)                       ║
║  5. 📝 Listar comandos disponibles                   ║
║  6. ⚙️  Configuración y setup                         ║
║  0. Salir                                            ║
╚══════════════════════════════════════════════════════╝
"""

def show_menu():
    print()
    print(CYAN(MENU))
    choice = input(DIM("Tu elección") + " → ").strip()
    return choice

def run_command(cmd_list, cwd=None):
    """Ejecuta comando y retorna True si fue exitoso"""
    try:
        result = subprocess.run(cmd_list, cwd=cwd or str(BAGO_ROOT.parent))
        return result.returncode == 0
    except Exception as e:
        print(f"{_c('1;31', '❌ Error')}: {e}")
        return False

def option_1():
    """Ver ideas y comenzar trabajo"""
    print()
    print(GREEN("🚀 Ideas priorizadas"))
    print(DIM("─" * 54))
    run_command(["python3", str(TOOLS / "emit_ideas.py")])
    print()
    print(DIM("💡 Tip: Usa") + " " + CYAN("./bago ideas --accept N") + " " + DIM("para aceptar una idea"))
    print(DIM("      Luego") + " " + CYAN("./bago session") + " " + DIM("para abrir sesión de trabajo"))

def option_2():
    """Dashboard y estado"""
    print()
    print(GREEN("📊 Dashboard del proyecto"))
    print(DIM("─" * 54))
    run_command(["python3", str(TOOLS / "pack_dashboard.py")])

def option_3():
    """Validar salud"""
    print()
    print(GREEN("🔍 Validación de salud"))
    print(DIM("─" * 54))

    print(BOLD("1. Validación del pack:"))
    run_command(["python3", str(TOOLS / "validate_pack.py")])

    print()
    print(BOLD("2. Resumen de estabilidad:"))
    run_command(["python3", str(TOOLS / "stability_summary.py")])

def option_4():
    """Abrir BAGO Viewer"""
    print()
    print(GREEN("🌐 Abriendo BAGO Viewer"))
    print(DIM("─" * 54))

    menu_html = BAGO_ROOT.parent / "menu.html"
    if menu_html.exists():
        opened = webbrowser.open(str(menu_html))
        if opened:
            print(CYAN("✓") + " Abriendo menu.html en tu navegador...")
        else:
            print(YELLOW("⚠") + " No se pudo abrir el navegador automáticamente.")
            print(DIM("  Abre manualmente:") + " " + CYAN(str(menu_html)))
        print()
        print(DIM("💡 Para datos en vivo, ejecuta en otra terminal:"))
        print(CYAN("   python3 .bago/tools/bago_chat_server.py"))
    else:
        print(f"{_c('1;31', '❌')} No se encontró menu.html")

def option_5():
    """Listar comandos"""
    print()
    print(GREEN("📝 Comandos disponibles"))
    print(DIM("─" * 54))

    main_cmds = [
        ("bago start",   "menú interactivo (este)"),
        ("bago ideas",   "ver y aceptar ideas priorizadas"),
        ("bago session", "abrir sesión de trabajo"),
        ("bago status",  "estado rápido del proyecto"),
    ]

    print()
    print(BOLD("Comandos principales:"))
    for cmd, desc in main_cmds:
        print(f"  {CYAN(cmd):20s} → {DIM(desc)}")

    print()
    print(DIM("Usa") + " " + CYAN("bago help --all") + " " + DIM("para ver todos los comandos"))

def option_6():
    """Setup y configuración"""
    print()
    print(GREEN("⚙️  Setup y configuración"))
    print(DIM("─" * 54))

    print(BOLD("1. Sincronizando contexto del repo..."))
    run_command(["python3", str(TOOLS / "repo_context_guard.py"), "sync"])

    print()
    print(BOLD("2. Instalando extensiones Copilot..."))
    ext_dir = BAGO_ROOT / "extensions"
    if ext_dir.exists() and any(ext_dir.iterdir()):
        print(CYAN("✓") + " Extensiones encontradas en .bago/extensions/")
        print(DIM("  Ejecuta") + " " + CYAN("./bago setup") + " " + DIM("desde el directorio raíz para instalar"))
    else:
        print(DIM("  No hay extensiones para instalar"))

    print()
    print(GREEN("✓ Setup completado"))

def main():
    # Banner breve
    print()
    print(BOLD(CYAN("BAGO")))
    print(DIM("Sistema operativo de trabajo técnico con IA"))

    # Selección de workspace antes de mostrar el menú
    _select_workspace()

    while True:
        choice = show_menu()

        if choice == "0":
            print()
            print(DIM("👋 Hasta pronto!"))
            print()
            break
        elif choice == "1":
            option_1()
        elif choice == "2":
            option_2()
        elif choice == "3":
            option_3()
        elif choice == "4":
            option_4()
        elif choice == "5":
            option_5()
        elif choice == "6":
            option_6()
        else:
            print()
            print(f"{_c('1;33', '⚠')} Opción no válida: {choice}")

        # Preguntar si quiere continuar
        print()
        again = input(DIM("¿Otra cosa?") + " (s/n) → ").strip().lower()
        if again not in ("s", "y", "yes", "sí", "si", ""):
            print()
            print(DIM("👋 Hasta pronto!"))
            print()
            break

if __name__ == "__main__":
    main()
