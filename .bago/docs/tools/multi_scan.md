# `multi_scan.py` — Scanner multi-lenguaje simultáneo

**Command:** `bago multi-scan`
**File:** `.bago/tools/multi_scan.py`
**Category:** Análisis estático — Multi-lenguaje
**Tool #:** 92

## Description

`multi_scan.py` amplía `bago scan` con detección y análisis simultáneo de todos los lenguajes presentes en un proyecto. Mientras `bago scan` opera sobre el lenguaje dominante, `multi-scan` detecta automáticamente Python, JavaScript/TypeScript, Go y Rust, y ejecuta los linters apropiados para cada uno, devolviendo hallazgos aggregados en un único informe unificado.

Para Python ejecuta: bago-lint + flake8 + pylint + mypy + bandit. Para JS/TS ejecuta ESLint (vía npx) + el scanner AST nativo `js_ast_scanner.js`. Para Go usa golangci-lint y para Rust usa cargo clippy. Los linters opcionales se saltan graciosamente si no están instalados — bago-lint y js_ast_scanner siempre funcionan sin dependencias externas.

El flag `--since FILE` permite comparar la sesión actual contra un snapshot JSON anterior, mostrando solo los hallazgos nuevos (regresiones) y los ya resueltos — útil en pipelines de CI.

## Usage

```bash
bago multi-scan [path] [options]
```

## Options

| Flag | Descripción |
|------|-------------|
| `path` | Directorio a escanear (default: `.`) |
| `--langs py,js` | Forzar lenguajes (ignorar detección automática) |
| `--json` | Output JSON (snapshot para `--since`) |
| `--since FILE` | Diff contra snapshot JSON anterior |
| `--summary` | Solo resumen por lenguaje/regla, sin detalle |
| `--min-severity W` | Umbral mínimo: `error`, `warning`, `info` (default: `info`) |
| `--test` | Ejecutar self-tests y salir |

## Examples

```bash
# Escanear todo el proyecto (detección automática de lenguajes)
bago multi-scan

# Solo Python y JS, solo errores y warnings
bago multi-scan --langs py,js --min-severity warning

# Guardar snapshot y comparar después
bago multi-scan --json > snapshot_pre.json
# [hacer cambios]
bago multi-scan --since snapshot_pre.json

# Solo resumen por lenguaje
bago multi-scan --summary
```

## Lenguajes soportados

| Lenguaje | Linters usados | Siempre disponible |
|----------|----------------|--------------------|
| Python | bago-lint + flake8 + pylint + mypy + bandit | bago-lint ✅ |
| JS/TS | ESLint (npx) + js_ast_scanner | js_ast_scanner ✅ |
| Go | golangci-lint | — (opcional) |
| Rust | cargo clippy | — (opcional) |

## Self-tests

```bash
python3 .bago/tools/multi_scan.py --test
```

→ 5/5 tests pasan: `detect_python_only`, `detect_py_and_js`, `python_scan_finds_bago_rules`, `by_lang_keys`, `detect_single_file`
