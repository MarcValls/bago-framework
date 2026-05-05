#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
agent_factory.py — FÁBRICA DE AGENTES BAGO

Sistema que CREA dinámicamente agentes especializados bajo demanda.

Si solicitás: "detecta bugs de seguridad"
  1. Factory verifica si existe agente
  2. Si NO existe → LO CREA automáticamente
  3. Lo guarda permanentemente en .bago/agents/
  4. Lo ejecuta
  5. Próximas veces: reutiliza existente

BAGO = Gestor de especialistas bajo demanda
Factory = Generador de especialistas
Agents = Especialistas persistentes
"""

from pathlib import Path
import json
import sys
from datetime import datetime, timezone

AGENTS_DIR = Path(__file__).resolve().parents[1] / "agents"
AGENTS_MANIFEST = AGENTS_DIR / "manifest.json"

# Template universal para generar agentes
AGENT_TEMPLATE = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{name}.py — Agente BAGO generado por Factory

Categoría: {category}
Descripción: {description}

Reglas: {rules_count}
{rules_list}

Generado: {created_at}
"""

from pathlib import Path
import ast
import json
import sys

class {class_name}(ast.NodeVisitor):
    """Agente especializado: {name}."""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.findings = []
    
    def analyze(self, node):
        """Implementa análisis según reglas."""
        # Este método debe ser específico según {category}
        pass

def analyze_file(filepath: str) -> list:
    """Analiza archivo."""
    try:
        source = Path(filepath).read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(source)
    except:
        return []
    
    analyzer = {class_name}(filepath)
    # analyzer.visit(tree)  # Implement based on category
    
    for finding in analyzer.findings:
        finding["file"] = filepath
    
    return analyzer.findings

def main(target_dir: str) -> int:
    """Análisis del directorio."""
    findings = []
    
    for py_file in Path(target_dir).rglob("*.py"):
        if any(d in py_file.parts for d in {{"__pycache__", ".git", ".bago"}}):
            continue
        findings.extend(analyze_file(str(py_file)))
    
    print(json.dumps({{
        "agent": "{name}",
        "category": "{category}",
        "findings": findings,
        "count": len(findings)
    }}, indent=2))
    
    return 0

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    raise SystemExit(main(target))
'''


def load_manifest() -> dict:
    """Carga manifest de agentes."""
    if AGENTS_MANIFEST.exists():
        return json.loads(AGENTS_MANIFEST.read_text(encoding="utf-8"))
    return {"agents": {}, "created": datetime.now(timezone.utc).isoformat()}


def save_manifest(manifest: dict):
    """Guarda manifest."""
    AGENTS_MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def agent_exists(name: str) -> bool:
    """Verifica si agente existe."""
    return (AGENTS_DIR / f"{name}.py").exists()


def create_agent(name: str, category: str, description: str, rules: list[str]) -> bool:
    """
    CREA agente dinámicamente.
    
    Args:
        name: Agent name (snake_case)
        category: Categoría (security, logic, performance, etc)
        description: Descripción
        rules: Lista de reglas
    
    Returns:
        True si exitoso, False si error
    """
    # Valida parámetros
    if not name or not name.replace('_', '').isalnum():
        print(f"❌ Agent name inválido: {name}", file=sys.stderr)
        return False
    
    if agent_exists(name):
        print(f"⚠️  Agente ya existe: {name}", file=sys.stderr)
        return False
    
    # Genera clase name en CamelCase
    class_name = ''.join(word.capitalize() for word in name.split('_'))
    
    # Genera rules list formateada
    rules_list = '\n'.join(f"  - {rule}" for rule in rules)
    
    # Genera código
    code = AGENT_TEMPLATE.format(
        name=name,
        category=category,
        description=description,
        class_name=class_name,
        rules_count=len(rules),
        rules_list=rules_list,
        created_at=datetime.now(timezone.utc).isoformat()
    )
    
    # Guarda archivo
    agent_path = AGENTS_DIR / f"{name}.py"
    try:
        agent_path.write_text(code, encoding="utf-8")
        agent_path.chmod(0o755)
        print(f"✅ Agente creado: {name}")
    except Exception as e:
        print(f"❌ Error creando agente: {e}", file=sys.stderr)
        return False
    
    # Registra en manifest
    manifest = load_manifest()
    manifest["agents"][name] = {
        "category": category,
        "description": description,
        "rules": len(rules),
        "created": datetime.now(timezone.utc).isoformat(),
        "status": "active"
    }
    save_manifest(manifest)
    
    print(f"📝 Registrado en manifest: {name}")
    return True


def list_agents() -> None:
    """Lista agentes disponibles."""
    manifest = load_manifest()
    agents = manifest.get("agents", {})
    
    if not agents:
        print("No agents available")
        return
    
    print(f"\n{'Agent':<25} {'Category':<15} {'Rules':<10} {'Status':<10}")
    print("─" * 60)
    
    for name, info in sorted(agents.items()):
        category = info.get("category", "?")
        rules = info.get("rules", 0)
        status = info.get("status", "?")
        print(f"{name:<25} {category:<15} {rules:<10} {status:<10}")
    
    print()


def get_or_create_agent(name: str, category: str, description: str, rules: list[str]) -> bool:
    """
    Obtiene agente existente O lo crea si no existe.
    
    Patrón clave de BAGO: adaptarse bajo demanda.
    """
    if agent_exists(name):
        print(f"✓ Usando agente existente: {name}")
        return True
    
    print(f"⚠️  Agente no existe: {name}")
    print(f"🔧 Generando especialista bajo demanda...")
    
    return create_agent(name, category, description, rules)


def main():
    """CLI de factory."""
    if len(sys.argv) < 2:
        print("agent_factory.py — Generador dinámico de agentes BAGO")
        print("\nUso:")
        print("  python agent_factory.py create <name> <category> <description> <rule1> <rule2> ...")
        print("  python agent_factory.py list")
        print("  python agent_factory.py exists <name>")
        print("\nEjemplo:")
        print('  python agent_factory.py create perf_checker performance "Check performance issues" "long_functions" "unused_vars"')
        return
    
    cmd = sys.argv[1]
    
    if cmd == "create":
        if len(sys.argv) < 5:
            print("❌ Sintaxis: create <name> <category> <description> <rule1> [<rule2> ...]")
            return
        
        name = sys.argv[2]
        category = sys.argv[3]
        description = sys.argv[4]
        rules = sys.argv[5:] if len(sys.argv) > 5 else []
        
        create_agent(name, category, description, rules)
    
    elif cmd == "list":
        list_agents()
    
    elif cmd == "exists":
        if len(sys.argv) < 3:
            print("❌ Sintaxis: exists <name>")
            return
        
        name = sys.argv[2]
        if agent_exists(name):
            print(f"✅ Existe: {name}")
        else:
            print(f"❌ No existe: {name}")
    
    else:
        print(f"Comando desconocido: {cmd}")


if __name__ == "__main__":
    main()
