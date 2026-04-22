# Guía de Contribución al Framework BAGO

> Cómo añadir herramientas, registrar cambios y mantener la calidad del pack.

---

## 1. Cómo añadir un nuevo comando `bago <cmd>`

Cada nuevo subcomando requiere 4 pasos en orden:

### Paso 1 — Crear la herramienta Python

Crea el archivo `.bago/tools/<nombre>.py`. Estructura mínima obligatoria:

```python
#!/usr/bin/env python3
"""
bago <nombre> — Título corto del comando

Descripción de una o dos frases explicando qué hace y cuándo usarlo.

Uso:
    bago <nombre>              → descripción acción por defecto
    bago <nombre> --opcion     → descripción opción
    bago <nombre> --json       → output JSON estructurado
    bago <nombre> --test       → valida dependencias y sale (para tests)
"""

import argparse
import json
import sys
from pathlib import Path

# Ruta estándar al state/
STATE_DIR = Path(__file__).parent.parent / "state"


def main():
    parser = argparse.ArgumentParser(
        description="bago <nombre> — Título corto"
    )
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--test", action="store_true", help="Modo test: valida y sale")
    args = parser.parse_args()

    # Modo test: solo validar dependencias, sin efectos secundarios
    if args.test:
        print("OK")
        sys.exit(0)

    # Lógica principal aquí
    result = run_logic()

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_human_output(result)


def run_logic():
    """Lógica principal del comando."""
    # Lee de STATE_DIR, nunca escribe directamente (usa helpers)
    return {}


def print_human_output(result):
    """Formatea el resultado para lectura humana en terminal."""
    pass


if __name__ == "__main__":
    main()
```

**Convenciones obligatorias:**
- El flag `--test` siempre debe estar presente y hacer `print("OK"); sys.exit(0)`
- El flag `--json` debe producir JSON válido en stdout
- No usar `print()` con colores ANSI sin verificar soporte de terminal
- No importar librerías externas que no estén en stdlib Python 3.8+
- El docstring del módulo sigue el formato mostrado arriba

### Paso 2 — Registrar en el script `bago`

Edita el archivo `bago` (en la raíz del proyecto). Añade la entrada en la tabla de comandos correspondiente:

```bash
# En la sección COMMANDS_ADVANCED o la sección de sprint correspondiente:
"<nombre>") python3 "$TOOLS_DIR/<nombre>.py" "${@:2}" ;;
```

Si el comando tiene alias:
```bash
"<nombre>"|"<alias>") python3 "$TOOLS_DIR/<nombre>.py" "${@:2}" ;;
```

### Paso 3 — Añadir tests de integración

Edita `.bago/tools/integration_tests.py`. Añade un test para el nuevo comando:

```python
def test_nombre():
    """Test básico de bago nombre."""
    result = run_cmd(["python3", TOOLS_DIR / "nombre.py", "--test"])
    assert result.returncode == 0, f"nombre --test falló: {result.stderr}"
    assert "OK" in result.stdout

    # Test de output JSON si aplica
    result_json = run_cmd(["python3", TOOLS_DIR / "nombre.py", "--json"])
    assert result_json.returncode == 0
    data = json.loads(result_json.stdout)
    assert isinstance(data, dict)
```

Verifica que la suite siga pasando:
```bash
./bago test
```

### Paso 4 — Documentar en `.bago/docs/tools/`

Crea `.bago/docs/tools/<nombre>.md` con la plantilla:

```markdown
# bago <nombre> — Título corto

> Una línea de descripción.

## Descripción

Párrafo explicando qué hace y cuándo usarlo.

## Uso

\`\`\`bash
bago <nombre>           → acción por defecto
bago <nombre> --opcion  → descripción
\`\`\`

## Opciones

| Opción | Descripción |
|--------|-------------|
| `--json` | Output JSON estructurado |
| `--test` | Modo test (valida dependencias) |

## Ejemplos

\`\`\`bash
# Caso de uso típico
bago <nombre>

# Output JSON para scripting
bago <nombre> --json
\`\`\`

## Casos de uso

- **Cuándo usarlo:** ...
- **Qué produce:** ...
- **Integración con otros comandos:** ...
```

---

## 2. Convenciones de código Python

### Naming

| Elemento | Convención | Ejemplo |
|----------|-----------|---------|
| Archivos | `snake_case.py` | `velocity_meter.py` |
| Funciones | `snake_case()` | `calculate_velocity()` |
| Clases | `PascalCase` | `SprintManager` |
| Constantes | `UPPER_SNAKE_CASE` | `STATE_DIR`, `DEFAULT_PERIOD` |
| Variables | `snake_case` | `sessions_per_day` |
| Parámetros argparse | `--kebab-case` | `--rolling`, `--top-n` |

### Argparse — flags estándar

Todos los comandos DEBEN soportar estos flags:

| Flag | Comportamiento |
|------|---------------|
| `--test` | Valida que las dependencias existen y sale con código 0 e imprime "OK" |
| `--json` | Output JSON estructurado en stdout (válido para `jq`) |

Flags opcionales recomendados cuando aplique:

| Flag | Comportamiento |
|------|---------------|
| `--period N` | Últimos N días (por defecto 7) |
| `--all` | Incluye todos los registros (no solo activos/recientes) |
| `--yes` | Confirmación automática en operaciones destructivas |
| `--out FILE` | Guarda output en archivo en lugar de stdout |

### Formato de docstring de módulo

```python
"""
bago <cmd> — Título en una línea

Descripción de 1-2 frases sobre qué hace y para qué sirve.

Uso:
    bago <cmd>                  → acción principal
    bago <cmd> --sub            → subacción
    bago <cmd> --json           → output JSON
    bago <cmd> --test           → modo test
"""
```

### Acceso a state/

Usa siempre `Path(__file__).parent.parent / "state"` para localizar state/:

```python
STATE_DIR = Path(__file__).parent.parent / "state"
SESSIONS_DIR = STATE_DIR / "sessions"
CHANGES_DIR = STATE_DIR / "changes"
```

No hardcodees rutas absolutas. No escribas en state/ directamente desde herramientas que solo deben leer.

### Manejo de errores

```python
try:
    data = json.loads(path.read_text())
except (json.JSONDecodeError, FileNotFoundError) as e:
    print(f"ERROR: No se pudo leer {path}: {e}", file=sys.stderr)
    sys.exit(1)
```

En modo `--test`, los errores de estado vacío son aceptables (el pack puede estar vacío):
```python
if args.test:
    # Verificar solo que el módulo carga y el estado existe
    if not STATE_DIR.exists():
        print("ERROR: state/ no encontrado", file=sys.stderr)
        sys.exit(1)
    print("OK")
    sys.exit(0)
```

---

## 3. Cómo registrar un CHG en state/changes/

Cuando un cambio significativo se realiza en el pack BAGO, se registra como `BAGO-CHG-NNN.json`.

### Cuándo registrar un CHG

- Añadir una nueva herramienta CLI
- Modificar comportamiento existente de forma no trivial
- Corrección de bug relevante
- Cambio de documentación canónica (AGENT_START, pack.json, workflows)

### Formato BAGO-CHG-NNN.json

```json
{
  "id": "BAGO-CHG-078",
  "type": "feature",
  "description": "Descripción concisa del cambio en imperativo",
  "session_id": "SES-SPRINT-2026-04-22-001",
  "sprint_id": "SPRINT-004",
  "files": [
    "tools/nuevo_comando.py",
    "docs/tools/nuevo_comando.md"
  ],
  "severity": "minor",
  "timestamp": "2026-04-22T15:00:00Z",
  "tags": ["cli", "herramienta"]
}
```

**Campos obligatorios:** `id`, `type`, `description`, `timestamp`  
**Campos recomendados:** `session_id`, `files`, `severity`

**Valores de `type`:**
- `feature` — nueva funcionalidad
- `fix` — corrección de bug
- `docs` — solo documentación
- `refactor` — refactoring sin cambio funcional
- `governance` — cambio de configuración o política del pack

**Valores de `severity`:**
- `major` — cambio de comportamiento observable o ruptura de compatibilidad
- `minor` — nueva funcionalidad sin ruptura
- `patch` — corrección pequeña o cosmética

### Proceso recomendado

El método canónico para registrar un CHG es usar `bago cosecha` al final de una sesión. El protocolo W9 guía el proceso y crea automáticamente los archivos CHG y EVD.

```bash
./bago detector    # Verifica que hay contexto suficiente para cosechar
./bago cosecha     # Inicia el protocolo W9 (requiere 3 respuestas del usuario)
```

---

## 4. Cómo correr los tests

### Suite completa de integración

```bash
./bago test
```

Esto ejecuta `integration_tests.py` con los 55 tests definidos. Se espera:

```
✅ 55/55 tests pasando
```

### Tests individuales durante desarrollo

```bash
# Test rápido de una herramienta específica
python3 .bago/tools/<nombre>.py --test

# Espera: "OK" y exit code 0
```

### Validación de integridad del pack

```bash
./bago validate    # GO manifest/state/pack
./bago health      # Score 100/100 esperado
./bago lint        # 0 errores, N avisos aceptables
```

### Flujo de CI local recomendado antes de cada commit

```bash
./bago validate && ./bago health && ./bago test
```

Si alguno de estos falla, **no** hacer commit hasta resolver.

---

## 5. Checklist de contribución

Antes de considerar completa una contribución:

- [ ] Herramienta Python creada en `.bago/tools/<nombre>.py`
- [ ] Docstring en formato canónico (ver sección 2)
- [ ] Flag `--test` implementado (imprime "OK", exit 0)
- [ ] Flag `--json` implementado si aplica
- [ ] Registrado en el script `bago` (tabla correspondiente)
- [ ] Test añadido en `integration_tests.py`
- [ ] `./bago test` → 36+N/36+N pasando ✅
- [ ] `./bago validate` → GO ✅
- [ ] `./bago health` → 100/100 🟢
- [ ] Doc creada en `.bago/docs/tools/<nombre>.md`
- [ ] CHG registrado (vía `bago cosecha` o manualmente)
- [ ] CHANGELOG.md actualizado si es versión notable

---

*BAGO v2.5-stable · MarcValls/bago-framework*
