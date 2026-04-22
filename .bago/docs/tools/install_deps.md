# `install_deps.py` — Verificador e instalador de dependencias opcionales

**Command:** `bago install-deps`
**File:** `.bago/tools/install_deps.py`
**Category:** Tooling del framework — Setup
**Tool #:** 95

## Description

`install_deps.py` comprueba la disponibilidad de todas las dependencias opcionales que usan las herramientas de análisis estático de BAGO: linters Python (flake8, pylint, mypy, bandit, black), herramientas JS/Node (eslint via npx, acorn, acorn-walk), y toolchains de Go y Rust (golangci-lint, cargo/clippy).

Las dependencias requeridas (como `node`) se marcan como no opcionales — si faltan, el comando devuelve exit code 1. Las dependencias opcionales se reportan pero no bloquean. Con `--install` la herramienta intenta instalar los paquetes faltantes que tienen un comando de instalación definido (pip para Python, npm para JS), y muestra el resultado por dependencia.

El output `--json` devuelve un objeto con claves `available` y `missing`, útil para integrar en pipelines de CI o scripts de bootstrap.

## Usage

```bash
bago install-deps [options]
```

## Options

| Flag | Descripción |
|------|-------------|
| `--check` | Solo verificar disponibilidad (sin instalar) |
| `--install` | Instalar los paquetes faltantes que tienen sugerencia |
| `--json` | Output JSON (`{available: [...], missing: [...]}`) |
| `--test` | Ejecutar self-tests y salir |

## Examples

```bash
# Verificar qué dependencias están disponibles
bago install-deps --check

# Instalar las que falten
bago install-deps --install

# Output JSON para scripts de CI
bago install-deps --json
```

## Dependencias verificadas (14 total)

| Dependencia | Tipo | Instalación sugerida |
|-------------|------|----------------------|
| flake8 | Python | `pip install flake8` |
| pylint | Python | `pip install pylint` |
| mypy | Python | `pip install mypy` |
| bandit | Python | `pip install bandit` |
| black | Python | `pip install black` |
| node | Node.js | (requerido, instalación manual) |
| npm | Node.js | (incluido con node) |
| npx | Node.js | (incluido con node) |
| eslint | JS | `npx eslint` |
| acorn | JS | `npm install acorn` |
| acorn-walk | JS | `npm install acorn-walk` |
| golangci-lint | Go | (instalación manual) |
| cargo | Rust | (instalación manual) |
| clippy | Rust | `rustup component add clippy` |

## Self-tests

```bash
python3 .bago/tools/install_deps.py --test
```

→ 5/5 tests pasan: `check_all_returns_all`, `result_fields`, `node_detection`, `acorn_check_exists`, `json_output`
