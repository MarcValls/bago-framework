# `rule_catalog.py` — Catálogo de reglas BAGO-* y JS-*

**Command:** `bago rule-catalog`
**File:** `.bago/tools/rule_catalog.py`
**Category:** Tooling del framework — Documentación
**Tool #:** 96

## Description

`rule_catalog.py` genera un catálogo completo y navegable de todas las reglas de análisis estático definidas en el framework BAGO. Cubre las 7 reglas Python (`BAGO-E001`…`BAGO-I002`) y las 10 reglas JS/TS (`JS-E001`…`JS-I004`), con descripciones, ejemplos de código incorrecto/correcto, información de autofix y supresión vía `noqa`.

El catálogo se genera en formato Markdown (con tabla de índice rápido + secciones detalladas por regla) o en HTML autónomo con estilos CSS integrados — listo para servir como página de referencia estática. Ambos formatos incluyen badges de severidad (🔴/🟡/🔵), categoría (seguridad/fiabilidad/mantenibilidad) y si la regla tiene autofix disponible.

Con `--filter PREFIX` se puede generar un catálogo parcial — por ejemplo solo las reglas de seguridad (`BAGO-W`, `JS-E`) o solo las informativas.

## Usage

```bash
bago rule-catalog [options]
```

## Options

| Flag | Descripción |
|------|-------------|
| `--format md\|html` | Formato de salida (default: `md`) |
| `--out FILE` | Escribir a archivo en lugar de stdout |
| `--filter PREFIX` | Solo reglas con ese prefijo (ej: `BAGO-W`, `JS-E`) |
| `--test` | Ejecutar self-tests y salir |

## Examples

```bash
# Generar catálogo Markdown en docs/
bago rule-catalog --format md --out .bago/docs/RULE_CATALOG.md

# Generar catálogo HTML navegable
bago rule-catalog --format html --out .bago/docs/RULE_CATALOG.html

# Solo reglas de seguridad en stdout
bago rule-catalog --filter BAGO-W --format md

# Reglas JS de error solamente
bago rule-catalog --filter JS-E
```

## Reglas catalogadas (17 total)

| Código | Severidad | Categoría | Autofix |
|--------|-----------|-----------|---------|
| `BAGO-E001` | 🔴 error | Fiabilidad | ✅ |
| `BAGO-W001` | 🟡 warning | Fiabilidad | ✅ |
| `BAGO-W002` | 🟡 warning | Seguridad | — |
| `BAGO-W003` | 🟡 warning | Fiabilidad | — |
| `BAGO-W004` | 🟡 warning | Fiabilidad | — |
| `BAGO-I001` | 🔵 info | Mantenibilidad | — |
| `BAGO-I002` | 🔵 info | Mantenibilidad | — |
| `JS-E001` | 🔴 error | Seguridad | — |
| `JS-W001` | 🟡 warning | Mantenibilidad | — |
| `JS-W002` | 🟡 warning | Mantenibilidad | — |
| `JS-W003` | 🟡 warning | Fiabilidad | — |
| `JS-W004` | 🟡 warning | Seguridad | — |
| `JS-W005` | 🟡 warning | Fiabilidad | — |
| `JS-I001` | 🔵 info | Mantenibilidad | — |
| `JS-I002` | 🔵 info | Mantenibilidad | — |
| `JS-I003` | 🔵 info | Mantenibilidad | — |
| `JS-I004` | 🔵 info | Mantenibilidad | — |

## Archivos generados

- `.bago/docs/RULE_CATALOG.md` — catálogo Markdown navegable
- `.bago/docs/RULE_CATALOG.html` — catálogo HTML con CSS integrado

## Self-tests

```bash
python3 .bago/tools/rule_catalog.py --test
```

→ 6/6 tests pasan: `rules_count`, `valid_severities`, `markdown_output`, `html_output`, `filter_prefix`, `autofix_flags`
