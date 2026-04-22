# `bago_lint_cli.py` — CLI dedicado para bago-lint

**Command:** `bago bago-lint`
**File:** `.bago/tools/bago_lint_cli.py`
**Category:** Análisis estático — Calidad de código Python
**Tool #:** 91

## Description

`bago_lint_cli.py` es el CLI dedicado del linter nativo de BAGO para código Python. Sin dependencias externas, escanea archivos `.py` en busca de 7 patrones problemáticos agrupados en tres niveles de severidad: errores (BAGO-E), warnings (BAGO-W) e informativos (BAGO-I).

Dos reglas son autofixables (`BAGO-E001`, `BAGO-W001`): el flag `--fix` aplica los parches en el fichero original, y `--preview` muestra exactamente qué cambiaría sin escribir nada. El output `--json` produce un snapshot que se puede usar con `--since` para ver solo los hallazgos nuevos o resueltos respecto al escaneo anterior.

Esta herramienta es invocada internamente por `bago scan` y `bago multi-scan`, pero también puede ejecutarse directamente como linter independiente de Python sin ninguna dependencia pip.

## Usage

```bash
bago bago-lint [path] [options]
```

## Options

| Flag | Descripción |
|------|-------------|
| `path` | Directorio o archivo a escanear (default: `.`) |
| `--fix` | Aplicar patches autofixables en los archivos originales |
| `--preview` | Mostrar qué haría `--fix` sin aplicar cambios (dry run) |
| `--rule RULE` | Filtrar solo a una regla concreta (ej: `BAGO-W001`) |
| `--json` | Output JSON — guarda snapshot para usar con `--since` |
| `--since FILE` | Diff contra snapshot JSON anterior (muestra nuevos y resueltos) |
| `--summary` | Solo contadores por regla, sin detalle por archivo |
| `--test` | Ejecutar self-tests internos y salir |

## Examples

```bash
# Escanear directorio actual
bago bago-lint

# Escanear ruta concreta filtrando solo BAGO-W001
bago bago-lint src/ --rule BAGO-W001

# Guardar snapshot y ver diferencias respecto al anterior
bago bago-lint --json > baseline.json
# [después de cambios]
bago bago-lint --since baseline.json

# Aplicar fixes autofixables y mostrar resumen
bago bago-lint --fix --summary
```

## Rules detected

| Código | Severidad | Autofixable | Descripción |
|--------|-----------|-------------|-------------|
| `BAGO-E001` | 🔴 error | ✅ | `bare except:` clause |
| `BAGO-W001` | 🟡 warning | ✅ | `datetime.utcnow()` deprecated |
| `BAGO-W002` | 🟡 warning | — | `eval()` / `exec()` — riesgo de seguridad |
| `BAGO-W003` | 🟡 warning | — | `os.system()` — usar subprocess |
| `BAGO-W004` | 🟡 warning | — | Ruta absoluta hardcodeada |
| `BAGO-I001` | 🔵 info | — | `sys.exit(1)` sin mensaje visible |
| `BAGO-I002` | 🔵 info | — | Comentarios TODO/FIXME/HACK |

## Dependencies

Ninguna dependencia pip requerida. Depende de `findings_engine.py` (incluido en el pack).

## Self-tests

```bash
python3 .bago/tools/bago_lint_cli.py --test
```

→ 5/5 tests pasan: `detect_all_rules`, `fix_applies_patch`, `preview_no_modify`, `json_structure`, `diff_since`
