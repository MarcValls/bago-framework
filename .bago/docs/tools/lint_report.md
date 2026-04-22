# `lint_report.py` — Generador de informes Markdown de bago-lint

**Command:** `bago lint-report`
**File:** `.bago/tools/lint_report.py`
**Category:** Reporting — Análisis estático
**Tool #:** 97

## Description

`lint_report.py` convierte la salida JSON de `bago bago-lint` o `bago multi-scan` en un informe Markdown estructurado y legible. El informe incluye un resumen ejecutivo con métricas por severidad, una tabla de las top reglas con más ocurrencias y una sección de detalle por archivo con severidad y mensaje de cada hallazgo.

El estado global del informe se determina automáticamente: ⛔ FALLOS si hay errores, ⚠️ ADVERTENCIAS si solo hay warnings, ✅ LIMPIO si no hay hallazgos. Con `--no-details` se genera solo el resumen ejecutivo — útil para notificaciones o comentarios en PRs. El flag `--title` permite personalizar el título del informe para cada contexto (sprint review, release, etc.).

La herramienta acepta tanto archivos JSON como entrada via stdin (`--stdin`), lo que permite pipelines encadenados directamente: `bago bago-lint --json | bago lint-report --stdin --title "Sprint Review"`.

## Usage

```bash
bago lint-report [SCAN_JSON] [options]

# Pipe directo desde bago-lint
bago bago-lint --json | bago lint-report --stdin

# Pipe desde multi-scan
bago multi-scan ./ --json | bago lint-report --stdin --title "Sprint Review"
```

## Options

| Flag | Descripción |
|------|-------------|
| `SCAN_JSON` | Archivo JSON de findings (de `--json`) |
| `--stdin` | Leer JSON desde stdin |
| `--title TITULO` | Título del informe (default: "Informe de Análisis Estático") |
| `--out FILE` | Escribir a archivo en lugar de stdout |
| `--no-details` | Omitir detalle por archivo (solo resumen ejecutivo) |
| `--test` | Ejecutar self-tests y salir |

## Examples

```bash
# Informe completo con detalle por archivo
bago bago-lint --json > findings.json
bago lint-report findings.json --out report.md

# Informe de sprint review desde multi-scan
bago multi-scan . --json | bago lint-report --stdin --title "Sprint 180 — Code Review"

# Solo resumen ejecutivo para comentario de PR
bago bago-lint --json | bago lint-report --stdin --no-details

# Informe a archivo
bago bago-lint --json | bago lint-report --stdin --out sprint_report.md
```

## Formatos de entrada soportados

| Formato | Origen | Estructura JSON |
|---------|--------|-----------------|
| bago-lint | `bago bago-lint --json` | Lista plana de findings |
| multi-scan | `bago multi-scan --json` | Dict `{by_lang: {py: [...], js: [...]}}` |

## Estructura del informe generado

1. **Título y estado global** (⛔ FALLOS / ⚠️ ADVERTENCIAS / ✅ LIMPIO)
2. **Resumen ejecutivo** — contadores por severidad (errores / warnings / info)
3. **Top reglas** — tabla de reglas con más ocurrencias
4. **Detalle por archivo** — agrupado por archivo, con severidad y mensaje (omitido con `--no-details`)

## Self-tests

```bash
python3 .bago/tools/lint_report.py --test
```

→ 6/6 tests pasan: `load_bago_format`, `load_multi_scan_format`, `generate_markdown_sections`, `estado_fallos_con_errores`, `estado_limpio_sin_findings`, `no_details_flag`
