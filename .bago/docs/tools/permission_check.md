# `permission_check.py` — Verificador de permisos de ejecutables

**Command:** `bago permission-check`
**File:** `.bago/tools/permission_check.py`
**Category:** Tooling del framework — Mantenimiento
**Tool #:** 94

## Description

`permission_check.py` garantiza que todos los archivos ejecutables del framework BAGO tengan el bit `+x` necesario para funcionar correctamente. Un permiso faltante provoca errores silenciosos al invocar tools desde el CLI, especialmente tras un `git clone` o una copia manual del pack.

La herramienta escanea: el script principal `bago`, todos los archivos `.py`, `.js` y `.sh` en `.bago/tools/`, los launchers `.command` de macOS y los scripts de setup en la raíz del pack. Por defecto aplica los permisos faltantes (`chmod +x`) en modo silencioso — solo muestra los cambios realizados. Con `--check` solo verifica sin modificar, útil en pipelines de CI para detectar regresiones de permisos.

## Usage

```bash
bago permission-check [options]
```

## Options

| Flag | Descripción |
|------|-------------|
| `--check` | Solo verificar — no aplicar cambios (modo CI) |
| `--verbose` | Mostrar todos los archivos, no solo los modificados |
| `--test` | Ejecutar self-tests y salir |

## Examples

```bash
# Verificar y corregir permisos (uso habitual tras git clone)
bago permission-check

# Solo verificar — útil en CI
bago permission-check --check

# Ver estado completo de todos los archivos
bago permission-check --verbose
```

## Archivos comprobados

| Patrón | Descripción |
|--------|-------------|
| `bago` | Script CLI principal |
| `.bago/tools/*.py` | Todas las herramientas Python |
| `.bago/tools/*.js` | Todas las herramientas JS |
| `.bago/tools/*.sh` | Scripts shell si existen |
| `*.command` | Launchers macOS |
| `setup-launcher.sh`, `_finish_session.sh` | Scripts de setup raíz |

## Self-tests

```bash
python3 .bago/tools/permission_check.py --test
```

→ 5/5 tests pasan: `detect_non_executable`, `make_executable`, `check_only_no_fix`, `auto_fix`, `all_py_tools_targeted`
