# BAGO Framework

> Sistema operativo de trabajo técnico para programación con IA

![health](https://img.shields.io/badge/health-%F0%9F%9F%A2%20100%2F100-brightgreen) ![tests](https://img.shields.io/badge/tests-%E2%9C%85%20102%2F102-brightgreen) ![tools](https://img.shields.io/badge/tools-136-blue) ![version](https://img.shields.io/badge/versión-3.0-blue) ![langs](https://img.shields.io/badge/languages-py%20%7C%20js%20%7C%20go%20%7C%20rust-orange)

**`health 🟢 100/100`** · **`tests ✅ 102/102`** · **`tools 🔧 136`** · **`versión 3.0`** · 12 workflows · Auto-gobernanza e inteligencia de intent integrada

---

## 🎯 ¿Qué hace BAGO?

BAGO amplifica el trabajo con IA resolviendo:

- ❌ Pérdida de contexto entre iteraciones → ✅ Estado persistente
- ❌ Arranques improvisados → ✅ Workflows definidos
- ❌ Cambios sin trazabilidad → ✅ Protocolo de evidencias
- ❌ Deriva entre código y documentación → ✅ Sincronización automática

**BAGO = B**alanceado · **A**daptativo · **G**enerativo · **O**rganizativo

---

## ⚡ Quick Start — 5 pasos

```bash
# 1. Instala BAGO y sincroniza el entorno
./bago setup

# 2. Verifica la salud del pack (esperado: 100/100 🟢)
./bago health

# 3. Abre o gestiona el sprint activo
./bago sprint status

# 4. Abre una sesión de trabajo con contexto precargado
./bago session

# 5. Cosecha el trabajo realizado (protocolo W9)
./bago detector       # ¿Hay contexto acumulado para cosechar?
./bago cosecha        # Inicia el protocolo W9
```

> **¿Primera vez?** → `./bago start`  
> **¿Diagnosticar?** → `./bago doctor`  
> **¿Ver todos los comandos?** → `./bago help --all`

---

## 📚 Tabla de comandos por fase

### Comandos principales (siempre visibles)

| Comando | Herramienta | Descripción |
|---------|-------------|-------------|
| `bago start` | `bago_start.py` | Menú interactivo — empieza aquí |
| `bago ideas` | `emit_ideas.py` | Ver y aceptar ideas priorizadas |
| `bago session` | `session_opener.py` | Abrir sesión con contexto precargado |
| `bago status` | `quick_status.py` | Estado rápido del proyecto |

### Gobernanza y validación

| Comando | Herramienta | Descripción |
|---------|-------------|-------------|
| `bago health` | `health_score.py` | Score 0-100 con 5 dimensiones |
| `bago audit` | `audit_v2.py` | Auditoría integral del pack |
| `bago validate` | `validate_pack.py` | Validación profunda del pack |
| `bago stale` | `stale_detector.py` | Detector de reporting stale |
| `bago workflow` | `workflow_selector.py` | Selector interactivo W0-W9 |
| `bago v2` | `v2_close_checklist.py` | Checklist GO/KO de cierre V2 |
| `bago cosecha` | `cosecha.py` | Protocolo W9 de cosecha contextual |
| `bago detector` | `context_detector.py` | Detector de contexto acumulado |

### Fase 1 — Análisis y productividad (S1–S7)

| Comando | Herramienta | Descripción |
|---------|-------------|-------------|
| `bago sprint` | `sprint_manager.py` | Gestión de sprints SPRINT-NNN.json |
| `bago search` | `bago_search.py` | Full-text search sobre sessions/changes |
| `bago timeline` | `timeline.py` | Timeline ASCII semanal con workflows |
| `bago report` | `report_generator.py` | Reportes Markdown con filtros temporales |
| `bago metrics` | `metrics_trends.py` | Tendencias rolling + sparklines ASCII |
| `bago doctor` | `doctor.py` | Diagnóstico integral del pack |
| `bago git` | `git_context.py` | Contexto git (branch/log/autores) + inject |

### Fase 2 — Exportación y estado (S8–S15)

| Comando | Herramienta | Descripción |
|---------|-------------|-------------|
| `bago export` | `export.py` | HTML dark-theme + CSV con SVG chart |
| `bago watch` | `watch.py` | Monitor en tiempo real del estado BAGO |
| `bago test` | `integration_tests.py` | Suite de integración (55/55 tests) |
| `bago changelog` | `changelog.py` | CHANGELOG desde BAGO-CHG-*.json |
| `bago snapshot` | `snapshot.py` | ZIP point-in-time de state/ |
| `bago diff` | `diff.py` | Delta de state/ vs último snapshot |
| `bago session-stats` | `session_details.py` | Top sesiones por producción (alias: `ss`) |
| `bago compare` | `compare.py` | Comparativa wf/periodo/rol lado a lado |

### Fase 3 — Organización (S16–S20)

| Comando | Herramienta | Descripción |
|---------|-------------|-------------|
| `bago goals` | `goals.py` | Gestión de objetivos con link/close/progress |
| `bago lint` | `lint.py` | Linter de calidad del pack |
| `bago summary` | `summary.py` | Resumen ejecutivo Markdown de sesión/sprint |
| `bago tags` | `tags.py` | Etiquetado con índice y búsqueda rápida |
| `bago flow` | `flow.py` | Flowchart ASCII de pipelines W0-W9 |

### Fase 4 — Subtools internos (S21–S23)

> Herramientas de soporte sin comando CLI propio. Son consumidas internamente por otras tools y no están expuestas directamente al usuario.

#### Motor de análisis estático (soporte para `scan` / `hotspot` / `fix` / `gh`)

| Herramienta | Descripción |
|-------------|-------------|
| `findings_engine.py` | Motor de hallazgos unificado: parsing de linters, modelo canónico de Finding (id, severity, file, line, rule, fix_suggestion, autofixable, fix_patch) |
| `risk_matrix.py` | Matriz de riesgo: categorías Security / Reliability / Maintainability / VelocityDrag × Probabilidad/Impacto → Exposición cuantificada |
| `debt_ledger.py` | Ledger de deuda técnica: cuantifica en horas y € con cuadrantes Reckless/Prudent × Deliberate/Inadvertent |
| `impact_engine.py` | Motor de impacto: traduce health score y deuda técnica en métricas de negocio (multiplicador de velocidad, €/trimestre) |

#### Gestión de estado y contexto

| Herramienta | Descripción |
|-------------|-------------|
| `state_store.py` | Capa de abstracción de almacenamiento: desacopla las tools del backend concreto |
| `context_collector.py` | Recolecta y resume contexto operativo de uno o varios directorios |
| `context_map.py` | Mapa de contexto distribuido: descubre instalaciones `.bago/` bajo una raíz y construye mapa jerárquico |
| `reconcile_state.py` | Reconcilia el inventario en `global_state.json` con los archivos reales en `state/` |
| `artifact_counter.py` | Mide la producción de artefactos útiles por sesión (excluye artefactos de protocolo) |

#### Validación y contratos

| Herramienta | Descripción |
|-------------|-------------|
| `validate_manifest.py` | Valida integridad y esquema del manifiesto `pack.json` |
| `validate_state.py` | Valida consistencia del estado: sessions / changes / evidences |
| `contracts.py` | Sistema de contratos de estado verificables con deadline y auditoría |
| `session_preflight.py` | Preflight W7: verifica reglas ESCENARIO-001 antes de abrir sesión |

#### Gobernanza y utilidades compartidas

| Herramienta | Descripción |
|-------------|-------------|
| `repo_context_guard.py` | Guard de contexto: detecta `match` / `mismatch` / `new` al cambiar de repo |
| `target_selector.py` | Selector seguro de directorio objetivo con candidatos priorizados y opción manual |
| `vertice_activator.py` | Evaluador de señales para activar revisión Vértice (sesiones W0 sin decisiones, etc.) |
| `bago_utils.py` | Utilidades compartidas: print_ok / fail / skip, runner de tests inline para todos los tools |
| `session_stats.py` | Estadísticas agregadas de sesiones por tipo de tarea, workflow y rol |
| `stability_summary.py` | Resume informes de sandbox (smoke/VM/soak) y validadores canónicos |
| `efficiency_meter.py` | Compara métricas de salud y productividad entre cleanversions |

### Fase 5 — Inteligencia y rutinas (S24–S33)

| Comando | Herramienta | Descripción |
|---------|-------------|-------------|
| `bago insights` | `insights.py` | Motor de insights automáticos (5 categorías) |
| `bago config` | `config.py` | Gestión de configuración del pack.json |
| `bago check` | `check.py` | Checklist pre-sesión personalizable |
| `bago archive` | `archive.py` | Archivado de sesiones cerradas antiguas |
| `bago stats` | `stats.py` | Dashboard agregado con sparklines de actividad |
| `bago remind` | `remind.py` | Recordatorios con due-date y sprint_ref |
| `bago habit` | `habit.py` | Detector de hábitos positivos/mejora/patrones |
| `bago review` | `review.py` | Informe de revisión periódica Markdown |

### Fase 6 — Velocidad y continuidad (S34–S35+)

| Comando | Herramienta | Estado | Descripción |
|---------|-------------|--------|-------------|
| `bago velocity` | `velocity.py` | ✅ Activo | Métricas de velocidad por período con proyección |
| `bago patch` | `patch.py` | ✅ Activo | Corrección automática de inconsistencias |
| `bago notes` | `notes.py` | ✅ Activo | Notas ligeras por sesión: add/list/show/delete |
| `bago template` | `template.py` | ✅ Activo | Plantillas para nuevas sesiones con campos prefilled |
| `bago scan` | `scan.py` | ✅ Activo | Análisis estático multi-linter con hallazgos unificados |
| `bago hotspot` | `hotspot.py` | ✅ Activo | Detección de hotspots de complejidad |
| `bago fix` | `autofix.py` | ✅ Activo | Autofix con validación y parches concretos |
| `bago gh` | `gh_integration.py` | ✅ Activo | Integración GitHub: check runs y comentarios en PRs |

### Fase 7 — Análisis estático de código (S36–S42) ← v3.0

| Comando | Herramienta | Descripción |
|---------|-------------|-------------|
| `bago api-check` | `api_check.py` | Valida consistencia de APIs: paths, params, auth, versioning |
| `bago coverage-gate` | `coverage_gate.py` | Gate de cobertura de tests: bloquea merge si baja del umbral |
| `bago naming-check` | `naming_check.py` | Verifica convenciones de nombres: snake_case, max length, constantes |
| `bago type-check` | `type_check.py` | Valida type hints Python: funciones sin anotación, retornos implícitos |
| `bago license-check` | `license_check.py` | Verifica cabeceras de licencia/copyright con `--add-header` auto-repair |
| `bago dep-audit` | `dep_audit.py` | Auditoría de requirements.txt/pyproject.toml: CVEs, rangos abiertos |
| `bago readme-check` | `readme_check.py` | Valida estructura del README: secciones, links rotos, placeholders |

### Fase 8 — Auto-gobernanza del framework (S43–S49) ← v3.0

| Comando | Herramienta | Descripción |
|---------|-------------|-------------|
| `bago ci-report` | `ci_report.py` | Reporte CI agregado: 10 scanners, score 0-100, markdown para PR |
| `bago tool-guardian` | `tool_guardian.py` | Valida coherencia del framework: tests, routing, integración, docstrings |
| `bago pre-push` | `pre_push_guard.py` | Guard pre-push: CHECKSUMS, suite, version sync en un comando |
| `bago tool-search` | `tool_search.py` | Búsqueda semántica sobre los 136 tools: `bago tool-search "secretos"` |
| `bago legacy-fix` | `legacy_fixer.py` | Scaffolding de `--test` en tools legacy sin auto-tests |
| `bago commit-ready` | `commit_readiness.py` | Gate pre-commit: syntax, secrets, merge conflicts, debug prints, size |
| `bago auto-register` | `auto_register.py` | Registra un tool en integration_tests + bago script + CHECKSUMS en 1 cmd |
| `bago intent` | `intent_router.py` | NLP intent → ejecución automática del tool correcto (12 intents) |
| `bago orchestrate` | `orchestrator.py` | Workflows encadenados: preprod, security, quality, selfcheck, onboarding |
| `bago auto-heal` | `auto_heal.py` | BAGO detecta y repara su propia incoherencia (R001-R005) |
| `bago config` | `bago_config.py` | Config centralizada compartida: thresholds, rutas, preferencias por tool |

> Ver docs individuales: [`.bago/docs/tools/`](.bago/docs/tools/)

---

## 🌐 Interfaz web (BAGO Viewer)

Abre `menu.html` en tu navegador para acceder al panel visual:

- 📦 Explorador de proyectos BAGO
- 📈 Evolución y línea de tiempo
- 📊 Métricas y KPIs
- 🎛 Orquestador en tiempo real

```bash
# Iniciar servidor (opcional, para live data)
python3 .bago/tools/bago_chat_server.py
# Luego abre: http://localhost:5050
```

---

## 🔄 Flujos de trabajo típicos

### 🆕 Nueva idea → implementación

```bash
./bago ideas                # 1. Lista ideas
./bago ideas --accept 3     # 2. Acepta idea #3
./bago session              # 3. Abre sesión con contexto
# [haces cambios]
./bago task --done          # 4. Marca completada
```

### 🔍 Verificar salud del proyecto

```bash
./bago status               # Dashboard rápido
./bago validate             # Validación profunda
./bago stability            # Smoke + VM + soak tests
```

### 🌾 Cosechar trabajo realizado

```bash
./bago detector             # Ver si hay contexto acumulado
./bago cosecha              # Protocolo W9 de cosecha
```

---

## 📖 Documentación

- **Para usuarios:** [`.bago/README.md`](.bago/README.md) — Visión técnica del sistema
- **Para agentes IA:** [`.bago/AGENT_START.md`](.bago/AGENT_START.md) — Punto de entrada canónico
- **Workflows:** [`.bago/workflows/`](.bago/workflows/) — W0 a W9
- **Prompts reutilizables:** [`.bago/prompts/`](.bago/prompts/) — Bootstrap, análisis, tareas

---

## 🎨 Cuándo usar qué

| Situación | Herramienta recomendada |
|-----------|-------------------------|
| Proyecto nuevo con BAGO | `prompts/00_BOOTSTRAP_PROYECTO.md` |
| Trabajo día a día | `./bago start` → opción 1 |
| Inspección/debugging | `./bago status` |
| Sesión exploratoria | `./bago session` (sin idea previa) |
| Revisar progreso | BAGO Viewer (`menu.html`) |

---

## 🛠 Arquitectura

### Visión de alto nivel

```
bago-framework/
├── bago                          # Script CLI principal (punto de entrada)
├── menu.html                     # Interfaz web (BAGO Viewer)
├── Makefile                      # Targets: banner, pack, validate, install
├── .bago/
│   ├── tools/                    # 136 herramientas Python/JS (un archivo por comando)
│   │   ├── health_score.py       # bago health
│   │   ├── audit_v2.py           # bago audit
│   │   ├── insights.py           # bago insights
│   │   ├── velocity.py           # bago velocity
│   │   └── ...                   # un .py por cada subcomando
│   ├── workflows/                # W0-W9 workflows canónicos (Markdown)
│   ├── prompts/                  # Prompts reutilizables para IA
│   ├── state/                    # Estado persistente (JSON + Markdown)
│   │   ├── sessions/             # SES-*.json — una por sesión
│   │   ├── changes/              # BAGO-CHG-*.json — registro de cambios
│   │   ├── sprints/              # SPRINT-*.json — gestión de sprints
│   │   ├── goals/                # GOAL-*.json — objetivos y progreso
│   │   ├── reminders/            # REM-*.json — recordatorios
│   │   └── snapshots/            # SNAP-*.zip — snapshots point-in-time
│   ├── core/                     # Contratos y cerebro del sistema
│   ├── config/                   # Configuración: pack.json, checklist.json
│   ├── docs/                     # Documentación técnica
│   │   ├── tools/                # Doc por cada herramienta
│   │   ├── CHANGELOG.md          # Historial de versiones
│   │   ├── ARCHITECTURE.md       # Este documento
│   │   └── CONTRIBUTING.md       # Guía de contribución
│   └── extensions/               # Extensiones Copilot CLI
└── cleanversion/                 # Versiones empaquetadas (ZIP)
```

### Capas del sistema

| Capa | Componente | Responsabilidad |
|------|-----------|-----------------|
| **CLI** | `bago` script | Despacha subcomandos → herramientas Python |
| **Tools** | `.bago/tools/*.py` | Lógica de cada comando, lee/escribe state/ |
| **State** | `.bago/state/` | Fuente de verdad: sesiones, cambios, sprints |
| **Docs** | `.bago/docs/` | Documentación técnica y referencia |
| **Config** | `.bago/config/` | pack.json con modo, idioma, preferencias |
| **Viewer** | `menu.html` | Interfaz web que consume el servidor `bago chat` |

### Flujo de datos típico

```
bago session → session_opener.py → crea SES-*.json en state/sessions/
bago task --done → show_task.py → actualiza pending_w2_task.json
bago cosecha → cosecha.py → genera BAGO-CHG-*.json + BAGO-EVD-*.json
bago health → health_score.py → lee state/ y calcula score 0-100
bago insights → insights.py → analiza SES-*.json + CHG-*.json → 5 categorías
bago velocity → velocity.py → rolling windows sobre SES-*.json → proyección
```

### Formatos de datos en state/

| Archivo | Descripción |
|---------|-------------|
| `SES-*.json` | Sesión de trabajo: workflow, decisiones, artefactos, métricas |
| `BAGO-CHG-*.json` | Cambio registrado: tipo, descripción, evidencias, archivos |
| `SPRINT-*.json` | Sprint: nombre, objetivo, fechas, velocidad, items |
| `GOAL-*.json` | Objetivo: título, criterio, progreso, sesiones vinculadas |
| `REM-*.json` | Recordatorio: texto, due-date, sprint_ref, estado |
| `SNAP-*.zip` | Snapshot ZIP point-in-time del directorio state/ |

---

## 🔗 Integración GitHub — Operativo ✅

Pipeline completo de análisis de código con integración directa en GitHub, **producción-ready** con soporte multi-lenguaje (Python, JS/TS, Go, Rust):

| Comando | Herramienta | Estado | Descripción |
|---------|-------------|--------|-------------|
| `./bago scan` | `scan.py` | ✅ Activo | Análisis multi-linter (flake8/pylint/mypy/ESLint/golangci/clippy) con hallazgos unificados |
| `./bago hotspot` | `hotspot.py` | ✅ Activo | Hotspots: frecuencia de cambios + errores + complejidad + historial CI |
| `./bago fix` | `autofix.py` | ✅ Activo | Autofix: parches concretos (E711/E712/F401/W291/BAGO-W001) + black/prettier bulk |
| `./bago bago-lint` | `bago_lint_cli.py` | ✅ Activo | Linter Python sin deps: 7 reglas, --fix, --preview, --json, --since (baseline diff) |
| `./bago multi-scan` | `multi_scan.py` | ✅ Activo | Scanner simultáneo de todos los lenguajes: py/js/go/rust, --since, --summary |
| `./bago ast-scan` | `js_ast_scanner.js` | ✅ Activo | Linter JS/TS basado en AST (acorn): 10 reglas, noqa, supera regex 80% |
| `./bago gh` | `gh_integration.py` | ✅ Activo | GitHub Check Runs + PR review agrupado por archivo, retry en 429/5xx |
| `./bago permission-check` | `permission_check.py` | ✅ Activo | Verifica y corrige permisos +x en todos los ejecutables BAGO |
| `./bago install-deps` | `install_deps.py` | ✅ Activo | Verifica e instala dependencias opcionales (flake8, eslint, acorn, golangci-lint…) |

### Pipeline operativo

```bash
# Analiza el proyecto (auto-detecta py/js/go/rust)
bago scan ./ --lang auto

# Escanea TODOS los lenguajes a la vez
bago multi-scan ./ --summary

# Linter Python zero-deps con diff contra baseline
bago bago-lint --json > baseline.json   # guardar baseline
bago bago-lint --since baseline.json   # solo errores NUEVOS (exit 1 si nuevos)

# Linter JS/TS basado en AST (acorn) — supera el 80% regex
bago ast-scan ./src --json

# Identifica los archivos más problemáticos (commits + errores + CI)
bago hotspot ./ --ci --heatmap

# Aplica fixes automáticos con validación post-fix
bago fix --apply
bago fix --external --target ./src   # black / prettier

# Verifica dependencias opcionales disponibles
bago install-deps --check

# Instala las que falten (pip/npm automáticamente)
bago install-deps --install

# Publica en GitHub
bago gh checks                       # Check Run con anotaciones
bago gh pr 42 --min-severity error   # PR review agrupado por archivo
```

### Lenguajes soportados

| Lenguaje | Scanner | Hotspot | Autofix externo |
|----------|---------|---------|----------------|
| Python   | flake8 + pylint + mypy + bandit + bago-lint | ✅ AST nativo | `black` |
| JS / TS  | ESLint (via npx) | ✅ AST real ² | `prettier` + `eslint --fix` |
| Go       | golangci-lint | ✅ regex | — |
| Rust     | cargo clippy | ✅ regex ¹ | — |
| Java     | checkstyle | — | — |
| C#       | dotnet build | — | — |
| Ruby     | rubocop | — | — |
| PHP      | phpcs + phpstan | — | — |
| Swift    | swiftlint | — | — |
| Kotlin   | ktlint | — | — |
| Shell    | shellcheck | — | — |
| Terraform | tflint | — | — |
| YAML     | yamllint | — | — |

> ¹ Rust hotspot: git history + findings + regex complexity (pub/priv fns, structs; test fns excluidos)  
> ² JS usa **acorn** (AST real, ecma2022); TS/TSX usa **@typescript-eslint/typescript-estree** (AST real con soporte de tipos, genéricos y decoradores). Ambos requieren Node.js + `npm install` (automático con `bago setup`).

---

## 🤝 Integración con GitHub Copilot

BAGO funciona especialmente bien conversando con Copilot:

1. Los prompts en `.bago/prompts/` están diseñados para ser copiados en chat
2. Las extensiones CLI se instalan automáticamente con `./bago setup`
3. El estado persistente permite retomar contexto entre sesiones

---

## 📦 Cleanversions

Sistema de versiones empaquetadas para distribuir configuraciones:

```bash
./bago versions             # Lista cleanversions disponibles
```

Cada cleanversion incluye su propio pack BAGO con modo de distribución específico.

---

## ⚙️ Requisitos

- Python 3.9+
- Git (para `bago hotspot --ci` y `bago git`)
- Navegador moderno (para BAGO Viewer)
- Terminal con soporte ANSI (para colores)
- Opcional: `black`, `prettier`, `golangci-lint`, `cargo` para fixers externos

---

## 🔗 Enlaces

- **Documentación técnica:** [`.bago/README.md`](.bago/README.md)
- **GitHub:** [MarcValls/bago-framework](https://github.com/MarcValls/bago-framework)
- **Versión actual:** 3.0 (v3.0 tag en git)

---

**¿No sabes por dónde empezar?** → `./bago start`
