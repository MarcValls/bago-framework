#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
repo_clone.py — Clone GitHub repositories with automatic BAGO setup

Integrates with workspace structure: C:\Marc_max_20gb\repos\

Uso:
  python3 repo_clone.py https://github.com/user/repo.git
  python3 repo_clone.py https://github.com/user/repo.git --name myrepo
  python3 repo_clone.py --list
"""

from pathlib import Path
import subprocess
import sys
import json
from datetime import datetime, timezone
import shutil

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]  # C:\Marc_max_20gb
REPOS_DIR = WORKSPACE_ROOT / "repos"
WORKSPACE_STATE = WORKSPACE_ROOT / ".bago" / "state" / "workspace.json"


def ensure_repos_dir():
    """Crea directorio repos/ si no existe."""
    REPOS_DIR.mkdir(parents=True, exist_ok=True)
    return REPOS_DIR


def get_repo_name(url):
    """Extrae nombre del repo desde URL."""
    name = url.split('/')[-1]
    if name.endswith('.git'):
        name = name[:-4]
    return name


def load_workspace_state():
    """Carga estado del workspace."""
    if WORKSPACE_STATE.exists():
        try:
            return json.loads(WORKSPACE_STATE.read_text(encoding="utf-8"))
        except:
            pass
    
    return {
        "version": "1.0",
        "created": datetime.now(timezone.utc).isoformat(),
        "repositories": {},
        "recent_repo": None
    }


def save_workspace_state(state):
    """Guarda estado del workspace."""
    WORKSPACE_STATE.parent.mkdir(parents=True, exist_ok=True)
    WORKSPACE_STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def clone_repo(url, custom_name=None):
    """Clona repositorio en repos/ con nombre."""
    ensure_repos_dir()
    
    repo_name = custom_name or get_repo_name(url)
    repo_path = REPOS_DIR / repo_name
    
    # Verificar que no exista ya
    if repo_path.exists():
        print(f"✗ Error: {repo_path} ya existe")
        return None
    
    print(f"\n══ Clonando repositorio ═══════════════════════════════════")
    print(f"URL:  {url}")
    print(f"Path: {repo_path}")
    print()
    
    # Clonar
    print("▪ Clonando...")
    try:
        result = subprocess.run(
            ["git", "clone", url, str(repo_path)],
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode != 0:
            print(f"✗ Clone failed: {result.stderr}")
            return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None
    
    print("▪ Clone exitoso")
    
    # Setup BAGO (copiar desde template o existente)
    print("▪ Configurando BAGO...")
    setup_bago_for_repo(repo_path)
    
    # Registrar en workspace state
    print("▪ Registrando en workspace...")
    state = load_workspace_state()
    state["repositories"][repo_name] = {
        "url": url,
        "path": str(repo_path),
        "cloned_at": datetime.now(timezone.utc).isoformat(),
        "status": "active"
    }
    state["recent_repo"] = repo_name
    save_workspace_state(state)
    
    print()
    print("════════════════════════════════════════════════════════════")
    print(f"✓ Repositorio clonado exitosamente: {repo_name}")
    print()
    print("Próximos pasos:")
    print(f"  1. cd {repo_path}")
    print(f"  2. bago audit")
    print(f"  3. bago ideas")
    print()
    
    return repo_path


def setup_bago_for_repo(repo_path):
    """Configura BAGO en el repositorio clonado."""
    bago_dest = repo_path / ".bago"
    bago_template = WORKSPACE_ROOT / "templates" / "bago_template"
    bago_source = WORKSPACE_ROOT / ".bago"
    
    # Usar template si existe, sino copiar del workspace
    if bago_template.exists():
        shutil.copytree(bago_template, bago_dest, dirs_exist_ok=True)
    elif bago_source.exists():
        # Copiar estructura básica (.bago/state/)
        bago_dest.mkdir(exist_ok=True)
        state_dest = bago_dest / "state"
        state_dest.mkdir(exist_ok=True)
        
        # Crear global_state.json
        global_state = {
            "version": "2.5-stable",
            "repo_name": repo_path.name,
            "workspace_root": str(WORKSPACE_ROOT),
            "mode": "project",
            "health_status": "initializing",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        (state_dest / "global_state.json").write_text(
            json.dumps(global_state, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )


def list_repos():
    """Lista repositorios clonados."""
    state = load_workspace_state()
    repos = state.get("repositories", {})
    
    if not repos:
        print("\n✓ Sin repositorios clonados aún")
        print("  Ejecuta: python repo_clone.py https://github.com/user/repo.git")
        return
    
    print("\n══ Repositorios clonados ════════════════════════════════════")
    for name, info in sorted(repos.items()):
        icon = "🟢" if info.get("status") == "active" else "⚪"
        url = info.get("url", "?")
        cloned = info.get("cloned_at", "?")[:10]
        print(f"  {icon} {name:20} | {url:40} | {cloned}")
    
    print()
    print(f"Total: {len(repos)} repositorios")
    print()


def main():
    if len(sys.argv) < 2:
        print("repo_clone.py — Clone GitHub repos con BAGO auto-setup")
        print("\nUso:")
        print("  python repo_clone.py <url>              → clona repositorio")
        print("  python repo_clone.py <url> --name <nom> → clona con nombre custom")
        print("  python repo_clone.py --list              → lista repos clonados")
        print("\nEjemplo:")
        print('  python repo_clone.py https://github.com/MarcValls/bago-framework.git')
        return
    
    cmd = sys.argv[1]
    
    if cmd == "--list":
        list_repos()
    elif cmd.startswith("http"):
        # URL de repositorio
        url = cmd
        custom_name = None
        
        if "--name" in sys.argv:
            idx = sys.argv.index("--name")
            if idx + 1 < len(sys.argv):
                custom_name = sys.argv[idx + 1]
        
        clone_repo(url, custom_name)
    else:
        print(f"Comando no reconocido: {cmd}")


if __name__ == "__main__":
    main()
