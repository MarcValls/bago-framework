# CHANGELOG

*Generado automáticamente — 2026-04-22*

---


## [Unreleased] — 2026-04-22

### ✨ Nuevas Funcionalidades

- chart_engine dynamic interactive charts (Chart.js) (`09970d6`) — MarcValls
  > Tool #112 — chart_engine.py: motor de gráficas interactivas con Chart.js
  > - gauge, bar, line, doughnut, heatmap charts
  > - self-contained HTML snippets, CDN Chart.js 4.4
  > - hover tooltips, animated, responsive, dark-mode compatible
  > Upgrades: health_report + doc_coverage + changelog_gen HTML dinámico
  > Integration: 79/79 tests ✅
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- tools #105-107 env-check/watch/size-track (75/75 ✅) (`9d50cf5`) — MarcValls
  > - env_check.py (#105): verificador de variables de entorno
  > Detecta: missing, empty, placeholder (CHANGEME/TODO/etc)
  > Ofusca valores SECRET/KEY/TOKEN, --strict, --json, .env.required
  > - file_watcher.py (#106): vigilante de cambios en archivos
  > Snapshot SHA-256, diff added/removed/modified
  > --once para CI (compare baseline), --cmd para ejecutar al detectar cambio
  > Watch loop continuo con Ctrl+C limpio
  > - size_tracker.py (#107): tracking de tamaño de archivos
  > Top-N por tamaño, sparkline bar visual, --ext filter, --min-kb
  > save/compare baseline, detecta archivos que crecen >50% y >10KB
  > Integration: 75/75 ✅ (62 grupos)
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- tool #103 branch-check + tool #104 complexity (72/72 ✅) (`4cb0699`) — MarcValls
  > - branch_check.py: validador de nombres de rama git
  > 5 estilos: gitflow/simple/jira/numeric/bago + --pattern custom
  > --ci mode (exit 1 sin output), --json, sugerencia de nombre válido
  > Integrado como 'bago branch-check [BRANCH] [--style STYLE]'
  > - complexity.py: complejidad ciclomática por función (Python AST)
  > Mccabe: 1-5 SIMPLE / 6-10 MEDIA / 11+ ALTA (refactor candidato)
  > Sparkline bar visual, métodos de clase, --sort, --min/--max
  > Sin deps externas — usa ast stdlib
  > Integrado como 'bago complexity [TARGET] [--sort] [--min N]'
  > Integration: 72/72 ✅ (59 grupos)
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- tool #101 changelog-gen + tool #102 dead-code (70/70 ✅) (`4e0d401`) — MarcValls
  > - changelog_gen.py: CHANGELOG.md/HTML desde git log
  > Conventional commits (feat/fix/docs/chore…), agrupación por versión/tag
  > Breaking changes destacados, --since TAG|SHA|DATE, --format html
  > Integrado como 'bago changelog-gen'
  > - dead_code.py: detector de código muerto en Python via AST
  > DC-W001: imports no usados | DC-W002: funciones no llamadas
  > DC-W003: FIXME/HACK | DC-I001: TODO | DC-I002: código comentado
  > Sin deps externas — usa ast stdlib
  > Integrado como 'bago dead-code [TARGET] [--json] [--severity]'
  > Integration: 70/70 ✅ (57 grupos)
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- tool #99 ci_baseline + tool #100 health-report (68/68 ✅) (`b08e806`) — MarcValls
  > - ci_baseline.py: save/compare/diff/status para baseline de findings CI
  > save → snapshot JSON, compare → exit 1 si regresión, diff → new/fixed/persistent
  > Integrado como 'bago ci-baseline'
  > - health_report.py (milestone #100): reporte integral Markdown + HTML
  > Combina config-check + bago-lint + git-info + score 0-100 (EXCELENTE/BUENO/MEJORABLE/CRÍTICO)
  > Secciones: score, pack.json, top-rules, top-files, recomendaciones priorizadas
  > Integrado como 'bago health-report [TARGET] [--format html] [--out FILE]'
  > Integration: 68/68 ✅ (55 grupos)
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- bago config-check (tool #98) — validador de pack.json (`1269eb6`) — MarcValls
  > New tool: config_check.py (#98)
  > - Valida pack.json contra esquema BAGO canónico
  > - CFG-E001: campo requerido ausente
  > - CFG-E002: tipo incorrecto
  > - CFG-E003/E004: archivo no encontrado / JSON inválido
  > - CFG-W001: campo requerido vacío
  > - CFG-W002: tipo opcional incorrecto
  > - CFG-W003: clave obsoleta (tools/plugins/legacy_mode)
  > - CFG-W004: versión no sigue semver
  > - CFG-W005: referencia a archivo inexistente
  > - CFG-I001: clave desconocida (extensión custom)
  > - --strict: falla en warnings (modo CI)
  > - --fix: elimina claves obsoletas automáticamente
  > - --json: output estructurado para scripting
  > - 7/7 self-tests pass — pack.json real: 0 errores críticos
  > integration_tests.py: T53 — 66/66 ✅
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- bago lint-report (tool #97) — informe Markdown de resultados bago-lint (`20f36f2`) — MarcValls
  > New tool: lint_report.py (#97)
  > - Convierte JSON de bago-lint/multi-scan → informe Markdown estructurado
  > - Secciones: resumen ejecutivo, estado (FALLOS/ADVERTENCIAS/LIMPIO),
  > top reglas por ocurrencias, hallazgos por archivo con tabla
  > - --stdin: pipe directo desde bago bago-lint --json
  > - --title: título personalizado
  > - --out FILE: escribe a archivo
  > - --no-details: solo resumen (sin tabla por archivo)
  > - Compatible con formato bago-lint y multi-scan --json
  > - 6/6 self-tests pass
  > integration_tests.py: T52 test_lint_report — 65/65 ✅
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- bago rule-catalog (tool #96) — catálogo completo de reglas BAGO-* y JS-* (`a9f386a`) — MarcValls
  > New tool: rule_catalog.py (#96)
  > - 17 reglas documentadas: 7 Python (BAGO-E/W/I) + 10 JS/TS (JS-E/W/I)
  > - Cada regla: código, severidad, categoría, descripción, ejemplo bad/good
  > - --format md  → Markdown con índice tabla + detalles por sección
  > - --format html → HTML standalone (tabla + cards con estilos)
  > - --filter PREFIX → filtra por prefijo (ej: BAGO-W, JS-E)
  > - --out FILE → escribe a archivo en vez de stdout
  > - 6/6 self-tests pass
  > bago script: 'bago rule-catalog' routing + help entry
  > integration_tests.py: T51 — 64/64 ✅
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- bago install-deps (tool #95) — verificar e instalar dependencias opcionales (`3fcd9a3`) — MarcValls
  > New tool: install_deps.py (#95)
  > - Verifica 14 dependencias: flake8, pylint, mypy, bandit, black, node,
  > npm, npx, eslint (npx), acorn, acorn-walk, golangci-lint, cargo, clippy
  > - --check: solo verificar sin instalar
  > - --install: instalar los ausentes via pip/npm
  > - --json: output estructurado para CI/scripting
  > - Detección acorn/acorn-walk via node_modules/ (ya instalados)
  > - Sugerencias coloreadas para deps sin install_cmd
  > - 5/5 self-tests pass
  > - Integration suite: T50 — 63/63 ✅
  > README updates:
  > - .bago/tools/README.md: count 91→95, nuevas herramientas #91-#95
  > - README.md: 87→95 en tree, tabla de comandos expandida,
  > pipeline operativo con multi-scan/bago-lint/ast-scan/install-deps
  > - bago script: 'bago install-deps' routing + help entry
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- bago permission-check (tool #94) — auto-fix ejecutables del framework (`199a1fd`) — MarcValls
  > New tool: permission_check.py (#94)
  > - Detecta y corrige permisos +x de todos los ejecutables BAGO
  > - Cubre: bago script, tools/*.py, tools/*.js, tools/*.sh, *.command
  > - --check: solo verificar sin modificar
  > - --verbose: mostrar todos los archivos procesados
  > - Resumen con conteo de ya-correctos / corregidos / con-problemas
  > - 5/5 self-tests pass
  > - Run result: 100 archivos — 99 ya correctos, 1 corregido
  > bago script: 'bago permission-check' routing + help entry
  > integration_tests.py: T49 test_permission_check — 62/62 pass ✅
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- js_ast_scanner.js (tool #93) — AST-based JS/TS linter via acorn (`47244ad`) — MarcValls
  > New tool: js_ast_scanner.js (#93)
  > - Detects issues that regex misses: arrow fn params, obj methods, decorators
  > - JS-E001  eval()/Function() constructor — security (AST-precise, zero FP)
  > - JS-W001  console.log in non-test files
  > - JS-W002  debugger statement
  > - JS-W003  loose equality == / !=
  > - JS-W004  setTimeout/setInterval with string arg (implicit eval)
  > - JS-W005  empty catch block
  > - JS-I001  TODO/FIXME/HACK comments
  > - JS-I002  arrow function >5 params
  > - JS-I003  nested ternary
  > - // noqa: JS-Wxxx suppression support
  > - test file auto-detection (skips console.log checks)
  > - 10/10 self-tests pass
  > findings_engine.py:
  > - parse_ast_js(): parser for js_ast_scanner JSON output
  > - run_js_ast_scan(): Python wrapper (runs node, returns Finding list, never raises)
  > scan.py: JS/TS scan now also runs bago_ast scanner after ESLint
  > multi_scan.py: _scan_js() now runs bago_ast scanner (works without ESLint)
  > bago script: 'bago ast-scan' command + help entry
  > integration_tests.py: T48 test_js_ast_scanner — 61/61 total pass ✅
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- bago multi-scan (tool #92) — multi-language scanner in one pass (`bda2ef8`) — MarcValls
  > New tool: multi_scan.py (#92)
  > - Detects ALL languages in a project (not just dominant)
  > - Runs appropriate linter per language: py/js/go/rust
  > - Aggregates all findings in a single report with per-lang breakdown
  > - --langs py,js     force specific languages
  > - --summary         per-language counts table
  > - --since FILE      diff mode (reuses diff_findings from findings_engine)
  > - --json            machine-readable output for CI pipelines
  > - --min-severity    filter threshold: error/warning/info
  > - 5/5 self-tests pass
  > Routing: 'bago multi-scan' added to bago script + help entry
  > Integration: T47 test_multi_scan added — 60/60 tests pass
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- **findings**: diff_findings() + bago bago-lint --since snapshot diff (`36098ab`) — MarcValls
  > findings_engine.py:
  > - diff_findings(before, after) -> {new, fixed, persistent}
  > - Identity key: (file, line, rule) — stable across re-scans
  > - T8d: 12/12 self-tests pass
  > bago_lint_cli.py:
  > - --since FILE: diff current scan vs JSON snapshot from prior run
  > - Shows new/fixed/persistent counts with colour output
  > - Exit code 1 only if NEW errors introduced (CI-friendly)
  > - T5 (cli:diff_since): 5/5 self-tests pass
  > integration_tests.py:
  > - T46 test_diff_findings: verifies new/fixed/persistent grouping
  > - Full suite: 59/59 ✅
  > CI workflow: bago bago-lint --json > baseline.json
  > (make changes)
  > bago bago-lint --since baseline.json
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- bago bago-lint CLI (tool #91) — zero-dep code linter with autofix (`c82a282`) — MarcValls
  > New tool: bago_lint_cli.py (#91)
  > - CLI for run_bago_lint with clean output, colors, and autofix
  > - Commands: bago bago-lint [path] --fix --preview --rule --json --summary
  > - --fix: applies patches in-place for BAGO-E001 and BAGO-W001 (autofixable rules)
  > - --preview: dry-run, shows what --fix would do without modifying files
  > - --json: machine-readable output for CI pipelines
  > - --summary: rule breakdown with autofixable counts
  > - 4/4 self-tests pass
  > Integration: added T45 to integration_tests.py (58/58 total)
  > Routing: 'bago bago-lint' added to bago script + help entry
  > README: tool #91 added, count updated 90→91
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- **bago-lint**: noqa suppression + BAGO-W004 + false positive cleanup (`5333868`) — MarcValls
  > New features:
  > - # noqa suppression mechanism (flake8-compatible)
  > - 'except: # noqa: BAGO-W003' suppresses specific rule
  > - bare '# noqa' suppresses all rules for the line
  > - BAGO-W004: detects hardcoded /Users/, /home/, C:\Users\ paths
  > fix suggestion: use Path.home() or os.path.expanduser('~')
  > False positive cleanup:
  > - All 10 BAGO-W001 false positives annotated with # noqa: BAGO-W001
  > (pattern references in docstrings, condition strings, test write_text calls)
  > - All 5 BAGO-W002 false positives annotated in findings_engine.py
  > - findings_engine.py W004 test line annotated
  > - Framework self-scan: 118 real findings (0 false positives for W001/W002/W004)
  > Tests: 11/11 findings_engine, 57/57 integration all pass
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- **bago-lint**: add BAGO-W004 — hardcoded absolute path detection (`78e99b2`) — MarcValls
  > BAGO-W004 detects hardcoded user paths in string literals:
  > - /Users/<name>/... (macOS)
  > - /home/<name>/...  (Linux)
  > - C:\Users\...     (Windows)
  > Fix suggestion: use Path.home() or os.path.expanduser('~')
  > Rule skips test files (is_test=True) to avoid false positives.
  > Tests: 10/10 findings_engine, 57/57 integration (T43 updated for W004)
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- **bago-lint**: 4 new lint rules — BAGO-E001 BAGO-W002 BAGO-W003 BAGO-I002 (`c0bef23`) — MarcValls
  > New rules in run_bago_lint():
  > BAGO-E001  bare except: → auto-fixable to 'except Exception:' with patch
  > BAGO-W002  eval()/exec() usage — security risk, not auto-fixable
  > BAGO-W003  os.system() — should use subprocess, not auto-fixable
  > BAGO-I002  TODO/FIXME/HACK comments — technical debt markers
  > Added _make_bare_except_patch() helper for BAGO-E001 autofixes.
  > Extended test suite: T8a + T8b — 9/9 core + 13 parser tests all passing.
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- **hotspot**: Rust real complexity analysis + all languages complete (`46b8ece`) — MarcValls
  > - hotspot.py: analyze_rust_complexity() — regex-based LOC+funcs+structs for Rust
  > - Counts pub fn, async fn, unsafe fn (all variants)
  > - Excludes test_ functions from complexity score
  > - Counts pub struct + private struct as 'classes' proxy
  > - _analyze_file() now routes lang='rust' to analyze_rust_complexity()
  > - T11 test: 3 fns (process/fetch/helper), 2 structs, test_helper excluded ✅
  > - All 11 hotspot tests pass (5 core + 6 multi-lang)
  > - README.md: Rust hotspot updated to 'regex' (was no complexity, now has it)
  > Go: 'regex' label added for clarity
  > - autofix.py checksums updated
  > Language coverage summary:
  > Python  → AST nativo (ast.parse)
  > JS      → acorn AST real (ecma2022)
  > TS/TSX  → @typescript-eslint/typescript-estree AST real
  > Go      → regex (reliable, regular syntax)
  > Rust    → regex (pub/priv fns + structs + LOC)
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- permission_fixer in autofix.py; update README TS AST; regen checksums (`e29ef3c`) — MarcValls
  > - autofix.py: all 4 subprocess.run calls replaced with _run_cmd (permission_fixer)
  > - run_tool_test(), run_external_fix_py(), run_external_fix_js() now auto-fix
  > chmod/EACCES/pip-user errors and retry; 8/8 tests pass
  > - README.md: language table updated — JS uses acorn AST, TS/TSX uses
  > @typescript-eslint/typescript-estree (real AST, supports generics/decorators)
  > - CHECKSUMS.sha256: regenerated (92 tools including ts_ast.js)
  > - TREE.txt: regenerated (739 entries)
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- **hotspot**: TypeScript real AST via @typescript-eslint/typescript-estree (`bcbb324`) — MarcValls
  > - ts_ast.js: new Node.js script that parses .ts/.tsx using typescript-estree
  > and outputs ESTree-compatible JSON for Python to walk
  > - hotspot.py: _ts_node_ast() uses node ts_ast.js instead of falling back to
  > regex for TypeScript files; _count_ts_ast_nodes() handles TS-specific nodes
  > (skips TSMethodSignature/TSFunctionType — no executable body)
  > - hotspot.py: T10 test verifies 5 fns + 1 class from TS source (AST mode)
  > - package.json: added @typescript-eslint/typescript-estree ^8.0.0 + typescript ^5.0.0
  > - Result: .ts/.tsx files now get real AST analysis (was: regex fallback only)
  > Test coverage: 10/10 hotspot tests passing (5 core + 5 multi-lang)
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- **testgen**: add Go+Rust self-tests; update tool count to 90 (`9d6f280`) — MarcValls
  > - testgen.py: Tests 5+6 cover analyze_go_file, generate_go_test_file,
  > analyze_rust_file, generate_rust_test_file — 6/6 passing
  > - ESTADO_BAGO_ACTUAL.md: 89 → 90 herramientas (permission_fixer.py added)
  > - tools/README.md: 89 → 90 count
  > - CHECKSUMS.sha256: regenerated (92 tools)
  > - TREE.txt: regenerated (738 entries)
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- integrate permission_fixer.py across findings_engine, hotspot, bago setup (`2c3f21b`) — MarcValls
  > - findings_engine.py: run_linter() now uses run_with_permission_fix() to auto-fix
  > chmod/npm-prefix/pip-user errors and retry failed linter commands
  > - hotspot.py: _js_node_ast() uses run_with_permission_fix for npx acorn calls;
  > graceful fallback if permission_fixer not importable
  > - bago script: npm install in setup uses _run_cmd with auto-fix; imports
  > ensure_executable from permission_fixer
  > - All 6 permission_fixer tests pass, 9/9 hotspot tests pass, findings_engine tests pass
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- acorn JS AST via npx + package.json + bago setup npm install (`a45c693`) — MarcValls
  > hotspot.py:
  > - _js_node_ast: switch from temp-file approach to 'npx --yes acorn' CLI
  > Same auto-download mechanism as ESLint in scan.py — no manual install
  > Skips .ts/.tsx files (acorn doesn't support TypeScript, regex handles them)
  > - _count_js_ast_nodes: simplified to count at FunctionExpression level only
  > Eliminates double-counting of class methods and object literal methods
  > - _node_available() + node_setup_hint(): helpful message if Node.js missing
  > Shows OS-specific install command (brew/apt/nodejs.org)
  > package.json (new):
  > - acorn ^8.14.0 as devDependency
  > - 'npm install' installs acorn locally for faster/offline use
  > - node_modules/ already in .gitignore
  > bago setup:
  > - Now runs 'npm install' if package.json exists
  > - Reports success or fallback message on npm failure
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- improve JS/TS complexity analysis — AST via acorn + enhanced regex (`89d2c93`) — MarcValls
  > - Add _js_node_ast(): uses Node.js + acorn for accurate AST analysis
  > Detects: FunctionDeclaration, FunctionExpression, ArrowFunctionExpression,
  > MethodDefinition (method), Property with function values, Class nodes
  > Falls back gracefully if node/acorn not available
  > - Rewrite analyze_js_complexity() with two-tier approach:
  > 1. Primary: Node.js AST (accurate, no false positives)
  > 2. Fallback: enhanced regex covering previously missed patterns:
  > - Arrow functions without braces: const f = x => x + 1
  > - Object literal method shorthand: { method() {} }
  > - Class getters/setters: get prop() {} / set prop() {}
  > - Classes now counted separately (classes key, not mixed into functions)
  > - Update test T6 to verify all 3 previously missed patterns
  > - 9/9 tests passing
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- add multi-language support to scan, findings_engine, and repo_runner (`bb929b3`) — copilot-swe-agent[bot]
  > - findings_engine.py: add parsers for Checkstyle (Java), dotnet build (C#),
  > RuboCop (Ruby), PHPCS + PHPStan (PHP), SwiftLint (Swift), ktlint (Kotlin),
  > ShellCheck (Shell), tflint (Terraform), yamllint (YAML); add 10 new tests
  > (T11-T20) covering all new parsers; import xml.etree.ElementTree for Checkstyle
  > - scan.py: extend _detect_lang() with manifest-based detection (pom.xml,
  > build.gradle, *.csproj, Gemfile, composer.json, Package.swift) and extension
  > counts for all 13 new language types; add run_scan() blocks for each new lang;
  > extend --lang argparse choices to include all new languages
  > - repo_runner.py: add _java_operation (Maven/Gradle), _kotlin_operation (Gradle),
  > _dotnet_operation (dotnet CLI), _ruby_operation (Bundler/RuboCop/rspec/rake),
  > _php_operation (phpcs/phpunit/composer), _swift_operation (swiftlint/swift);
  > extend _run_operation() to detect new manifests
  > - ci_generator.py: add language-specific linter install comments to both
  > GitHub Actions and GitLab CI templates
  > Agent-Logs-Url: https://github.com/MarcValls/bago-framework/sessions/0569701e-f86f-4de6-8aa9-a727ddbd579f
  > Co-authored-by: MarcValls <26687410+MarcValls@users.noreply.github.com>
- **tools**: CHG-082 — 4 PRÓXIMO tools 100% multi-lang production-ready (`2d92d8a`) — MarcValls
  > findings_engine.py:
  > - Add parse_eslint (JSON format, fix field → autofixable)
  > - Add parse_golangci (JSON Issues format, linter-based severity)
  > - Add parse_clippy (streaming NDJSON, spans for file/line)
  > - Tests T8-T10 for new parsers (10/10 pass)
  > scan.py:
  > - Auto-detect dominant language (_detect_lang)
  > - Multi-lang run_scan: py/js/ts/go/rust support
  > - ESLint via npx --yes with fallback, golangci-lint, cargo clippy
  > - --lang CLI flag (auto/py/js/ts/go/rust)
  > - Python 3.9 compat (Optional[X] throughout)
  > hotspot.py:
  > - _detect_lang, _glob_by_lang (skip node_modules/vendor)
  > - analyze_js_complexity + analyze_go_complexity (regex-based)
  > - ci_failures_by_file(): scores files failing in last 20 scans
  > - compute_hotspots: lang + include_ci params, ci×8 in formula
  > - render_hotspots: CI failures column, lang badge, CI risk summary
  > - main(): --lang and --ci flags
  > - Tests T6-T9 for JS/Go/CI (9/9 pass)
  > autofix.py:
  > - New rules: E711 (== None → is None), E712 (== True → is True)
  > - F401/W0611: remove simple single-name unused imports
  > - run_external_fix_python: black --check/write
  > - run_external_fix_js: prettier --write + eslint --fix fallback
  > - run_external_fix: auto-detect lang, dispatch to correct fixer
  > - --external and --target flags in main()
  > - Optional[X] Python 3.9 compat
  > - Tests T6-T8 for new rules (8/8 pass)
  > gh_integration.py:
  > - Fix shebang/import ordering (Optional before shebang was broken)
  > - _request: retry on 429 (Retry-After header) and 5xx (3 attempts)
  > - group_findings_by_file(): dict of {path: [Finding]}
  > - findings_to_file_summary(): grouped Markdown block per file
  > - cmd_pr: one inline comment per file (not per finding)
  > - cmd_pr: includes grouped summary with error/warning counts
  > - pr subcommand: --min-severity alias alongside --severity
  > - Tests T7-T8 for group/summary functions (8/8 pass)
  > Total: 37/37 tests across 5 tools
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- Sprint 180 — 86 tools, pipeline salud→rendimiento, contratos C001-C003, testgen, ci_generator, bago_ask (`57d2574`) — MarcValls
  > ## Sprint 180 Máxima Iteración — Completado al 100%
  > ### Nuevas herramientas (40+ en este sprint)
  > - S34 velocity.py — métricas de velocidad con sparklines y proyección 30d
  > - S35 patch.py — corrección de inconsistencias legacy en estado BAGO
  > - S36 notes.py — sistema de notas por sesión/sprint
  > - S37 template.py — 4 plantillas builtin + custom para nuevas sesiones
  > - F1 findings_engine.py — modelo unificado de hallazgos (Finding dataclass, FindingsDB, parsers flake8/pylint/mypy/bandit/bago)
  > - F2 scan.py — runner unificado de linters con salida JSON
  > - F3 hotspot.py — mapa de calor git+findings+AST complexity
  > - F4 autofix.py — generación, aplicación y validación de patches
  > - F5 gh_integration.py — GitHub Check Runs + PR inline review comments
  > - risk_matrix.py — taxonomía de riesgos, matriz probabilidad×impacto
  > - debt_ledger.py — deuda técnica en cuadrantes + €/hr + ROI
  > - impact_engine.py — salud→€/trimestre (modelo FAIR, velocidad DORA)
  > - contracts.py — sistema de contratos verificables con deadline (C001/C002/C003)
  > - bago_utils.py — utilidades compartidas (ok/fail/skip, load_json, format_timedelta)
  > - testgen.py — genera tests para repos desconocidos (Python AST + JS regex, 570 placeholders)
  > - ci_generator.py — GitHub Actions + GitLab CI + pre-commit hook con validación crítica
  > - bago_ask.py — búsqueda en lenguaje natural sobre 166 docs BAGO
  > ### Governance
  > - RULE-CDTR-001: código saludable = activo comercial medible (regla canónica permanente)
  > - CONTRACT-001 (baseline) / CONTRACT-002 (T+2h) / CONTRACT-003 (T+4h) verificados
  > - SPRINT-004 cerrado con evidencia completa → SPRINT-005 abierto
  > - CHG-078 + CHG-079 registrados
  > ### Correcciones
  > - datetime.now() sin timezone corregido en 9 archivos
  > - Routing: 37 → 71 entradas (bago script)
  > - Tests: 44 → 55/55 ALL PASS
  > ### Estado final
  > - Health: 100/100
  > - Validate: GO (manifest + state + pack)
  > - Tests: 55/55 ALL PASS
  > - Tools: 86 archivos .py
  > - Changes: 62 registrados
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- workspace selector at startup + iteration tracker for evolution (`0327886`) — copilot-swe-agent[bot]
  > Agent-Logs-Url: https://github.com/MarcValls/bago-framework/sessions/ac0fd3c6-b7e1-473a-9ba5-0425cfce3734
  > Co-authored-by: MarcValls <26687410+MarcValls@users.noreply.github.com>
- add bago start/status commands, improve help, add Quick Start to menu.html and README (`47c84de`) — copilot-swe-agent[bot]
  > Agent-Logs-Url: https://github.com/MarcValls/bago-framework/sessions/a0889367-d36c-4b17-9466-100482b3eb96
  > Co-authored-by: MarcValls <26687410+MarcValls@users.noreply.github.com>
- menú estático standalone + launcher macOS (`8c51429`) — MarcValls
  > - menu.html en raíz del proyecto — HTML puro, no requiere servidor Flask
  > - Detección automática de servidor: img-tag trick sobre /static/ping.png
  > (funciona desde file:// → http://localhost sin problemas CORS)
  > - Prueba puertos 5050-5054, usa el primero activo
  > - Estado: Buscando… / ✅ Activo en :PORT / ❌ No encontrado
  > - Botón Abrir desactivado hasta confirmar servidor activo
  > - 4 tarjetas de sección (Packs, Evolución, Métricas, Orquestador)
  > deshabilitadas hasta detectar servidor, habilitadas con el puerto correcto
  > - Instrucciones START si servidor no encontrado + botón Copiar comando
  > - Reintento automático cada 10 s mientras servidor está caído
  > - start-viewer.command (macOS): doble clic en Finder inicia el servidor
  > y abre http://localhost:5050/ directamente en el navegador
  > - bago-viewer/static/ping.png — 1x1 PNG para detección sin CORS
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- **bago-viewer**: main menu como landing page / (`8710552`) — MarcValls
  > - Nueva home.html con 4 tarjetas: Packs, Evolución, Métricas, Orquestador
  > - Cada tarjeta muestra ruta, descripción detallada y pills de qué verás
  > - Status bar en hero: health dot, sesiones, versión BAGO en tiempo real
  > - Hover con gradiente de color por sección + animación flecha →
  > - Ruta / → home; packs movido a /packs (todos los redirects actualizados)
  > - Logo BAGO·Viewer en nav ahora es enlace a /
  > - Añadido enlace 📦 Packs en nav
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- **bago-viewer**: panel orquestador con polling en tiempo real (`3c0e9ad`) — MarcValls
  > - Nueva página /orchestrator con layout de 2 columnas inspirado en PANEL_ORQUESTADOR
  > - Endpoint /orchestrator-data (JSON) que lee estado real del .bago/state/
  > - Sesión activa: goal, workflow, roles, elapsed timer live (tick cada 1s)
  > - Artefactos planificados de la sesión activa
  > - 8 sesiones recientes con workflow badge y duración
  > - Sprint status con pills visuales (DONE / ACTIVO / PENDIENTE / BLOQUEADO)
  > - Ideas detectadas por proyecto con conteos pending/done/en progreso
  > - Inventario KPIs (sessions/changes/evidences)
  > - Notas de sistema y última acción completada
  > - Barra de progreso de refresh (5 s ciclo), status bar con health dot y live badge
  > - Nav link 🎛 Orquestador añadido a base.html
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- **viewer**: metrics dashboard HTML — /metrics page (`6043d27`) — MarcValls
  > - Add bago-viewer/templates/metrics.html
  > · Hero with KPI cards (sessions, success rate, artifacts ratio, avg duration)
  > · Section 01: calidad semántica (chart + stat card)
  > · Section 02: tiempo bootstrap (chart + distribution card)
  > · Section 03: éxito por workflow (chart + table with color-coded rate pills)
  > · Section 04: reales vs TLS (chart + affected sessions list)
  > · Section 05: valor roles (table + chart, artifacts/session & decisions/session)
  > · Section 06: evolución acumulada (full-width chart)
  > · Responsive 2-col grid, dark theme consistent with existing viewer
  > - Update bago-viewer/app.py
  > · Add _collect_metrics_data() — reads real session JSONs, computes KPIs
  > · Derives duration from created_at→updated_at timestamps
  > · Uses correct field names: artifacts, artifacts_planned, roles_activated
  > · Add /metrics route
  > · Add /metrics-img/<filename> route serving docs/metrics/*.png
  > - Update bago-viewer/templates/base.html
  > · Add 📊 Métricas nav link
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- state_store abstraction layer + auto_mode dir picker + metrics charts (`6d1942c`) — MarcValls
  > - Add .bago/tools/state_store.py: JSON→SQLite abstraction layer
  > · CollectionStore (sessions/changes/evidences) with get/list/save/create/count
  > · SingletonStore (global_state/repo_context/pending_task/user_profile)
  > · Transaction context manager for batch-write
  > · SqliteCollectionBackend skeleton (locked until full migration)
  > · CLI: python3 state_store.py --inventory --list sessions
  > - Migrate .bago/tools/generate_task_closure.py to StateStore
  > · Atomic writes via transaction()
  > · Inventory from real counts, not manual fields
  > · Removes direct JSON file manipulation
  > - Update .bago/tools/auto_mode.py: dynamic directory picker on activation
  > · Shows recently used directories from context_map.json + repo_context.json
  > · Prompts for selection or custom path before running auto mode
  > · Syncs repo_context.json + regenerates context_map on selection
  > - Add docs/metrics/: 6 evolution charts (PNG) + raw report
  > · 01_calidad_semantica.png — useful vs filler artifacts ratio
  > · 02_tiempo_bootstrap.png — session duration distribution
  > · 03_exito_workflow.png   — success rate and duration per workflow
  > · 04_reales_vs_tls.png    — real sessions vs TLS/rate-limit affected
  > · 05_valor_roles.png      — incremental value of activating roles
  > · 06_evolucion_inventario.png — cumulative inventory growth
  > · BAGO_METRICS_REPORT.md  — full raw report with tables
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- update BAGO from GitHub (v2.5 → 6 new commits) (`724c15f`) — MarcValls
  > - bago script: add 'auto' subcommand dispatch + refactor
  > - .bago/tools/auto_mode.py: nuevo modo automático BAGO
  > - .bago/tools/cosecha.py: modo no-interactivo (--que-decidiste / --yes)
  > - .github/copilot-instructions.md: reglas de coherencia para agente
  > - .bago/extensions/bash-runner/extension.mjs: actualizado desde framework
  > Upstream: MarcValls/bago-framework@4f3d8ae
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- **extensions**: bash-runner compatible con Windows (`18a26cf`) — MarcValls
  > - Windows: powershell.exe para exec, cmd/ps1/bat para scripts
  > - macOS/Linux: comportamiento anterior sin cambios
  > - run_script auto-detecta .ps1/.bat/.sh según extensión
  > - bago_run usa 'python' en Windows, 'python3' en Unix
  > - Output incluye 'platform' para diagnóstico
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- **extensions**: bash-runner BAGO-nativo integrado en setup (`c26ed6f`) — MarcValls
  > - Fuente en .bago/extensions/bash-runner/extension.mjs
  > - bago setup instala automáticamente extensiones → .github/extensions/
  > - bago extensions lista el estado de instalación
  > - Nuevo tool bash-runner_bago_run (auto-detecta BAGO_ROOT)
  > - Replicado en v02-template-seed para distribución
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>

### 🐛 Correcciones

- hotspot Rust lang support — correct .rs glob + expand language table (`a3168e3`) — MarcValls
  > - hotspot.py: _glob_by_lang now correctly globs *.rs for lang=rust
  > (previously fell through to else → glob .py files — silent bug)
  > - hotspot.py: update header comment for Rust support
  > - README.md: expand language table to show all 13 supported languages
  > Java(checkstyle), C#, Ruby, PHP, Swift, Kotlin, Shell, Terraform, YAML
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- prevent IndexError on empty counters, silence log action output (`3bf9850`) — copilot-swe-agent[bot]
  > Agent-Logs-Url: https://github.com/MarcValls/bago-framework/sessions/ac0fd3c6-b7e1-473a-9ba5-0425cfce3734
  > Co-authored-by: MarcValls <26687410+MarcValls@users.noreply.github.com>
- improve webbrowser error handling and replace alert() with toast notification (`4fc7bf2`) — copilot-swe-agent[bot]
  > Agent-Logs-Url: https://github.com/MarcValls/bago-framework/sessions/a0889367-d36c-4b17-9466-100482b3eb96
  > Co-authored-by: MarcValls <26687410+MarcValls@users.noreply.github.com>

### 📝 Documentación

- documentación herramientas #91–#97 (análisis estático avanzado) [v2.6] (`b31285d`) — MarcValls
  > - CHANGELOG.md: entrada v2.6 con herramientas #91–#97
  > - BAGO_REFERENCIA_COMPLETA.md: sección 8 ampliada con tabla de tools #91–#97
  > - ESTADO_BAGO_ACTUAL.md: contadores actualizados 90→95 tools, 55/55→64/64 tests
  > - .bago/tools/README.md: añadidos rule_catalog.py (#96) y lint_report.py (#97); tests 63→64
  > - README.md: badges actualizados 89→95 tools, 55/55→64/64 tests, versión 2.5-stable→2.6
  > - docs/tools/: 7 nuevos archivos (bago_lint_cli.md, multi_scan.md, js_ast_scanner.md,
  > permission_check.md, install_deps.md, rule_catalog.md, lint_report.md)
  > - docs/RULE_CATALOG.md + RULE_CATALOG.html: catálogos generados (17 reglas: 7 BAGO-* + 10 JS-*)
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- describe subtools internos de Fase 4 en CHANGELOG y README (`42c1cd6`) — copilot-swe-agent[bot]
  > Agent-Logs-Url: https://github.com/MarcValls/bago-framework/sessions/142efb0c-8a4f-4ca5-b538-a97f402817d5
  > Co-authored-by: MarcValls <26687410+MarcValls@users.noreply.github.com>
- update README — 4 GitHub tools now ✅ Active, 87 tools, multi-lang (`02f97da`) — MarcValls
  > - Mark scan/hotspot/fix/gh as ✅ Activo (was 🔜 Próximo)
  > - Add multi-language support table (py/js/ts/go/rust)
  > - Expand GitHub Integration section with working pipeline + usage examples
  > - Update badges: tests 37/37, tools 87
  > - Update Python requirement to 3.9+ (compatibility baseline)
  > - Add optional deps for external fixers (black, prettier, golangci-lint, cargo)
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- sync operational documentation from bago-framework GitHub (`437467e`) — MarcValls
  > Sources (unmerged branches from MarcValls/bago-framework):
  > - docs/sync-operational-docs (b133761): fix validate/sync distinction in
  > TROUBLESHOOTING.md, GUIA_OPERADOR.md, MANTENIMIENTO.md,
  > V2_PLAYBOOK_OPERATIVO.md — bago sync regenerates, validate is read-only
  > - docs/manual-nuevo-usuario (dc308db): add MANUAL_NUEVO_USUARIO.md —
  > complete Spanish onboarding guide (409 lines): CLI commands, workflows,
  > session flow, AI integration, key concepts, FAQ
  > TREE.txt and CHECKSUMS.sha256 regenerated after new file addition.
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>

### ♻️  Refactor

- address code review feedback on multi-language support (`8ab4cf9`) — copilot-swe-agent[bot]
  > - scan.py: use next() instead of any(rglob()) for early exit in Kotlin detection;
  > expand .kt file list explicitly before calling ktlint subprocess (shell glob
  > expansion doesn't apply to subprocess args)
  > - repo_runner.py: extract _is_not_found() helper to deduplicate command-not-found
  > check across PHP and Ruby operations; use next() instead of any(rglob()) for
  > Kotlin detection in _run_operation
  > - findings_engine.py: add inline comments to yamllint regex explaining the
  > non-greedy message group and [^)] rule group design
  > Agent-Logs-Url: https://github.com/MarcValls/bago-framework/sessions/0569701e-f86f-4de6-8aa9-a727ddbd579f
  > Co-authored-by: MarcValls <26687410+MarcValls@users.noreply.github.com>

### 🧪 Tests

- **integration**: 44 → 57 tests — bago_lint T43+T44 integration coverage (`c76debe`) — MarcValls
  > Added test_bago_lint_rules (T43) and test_bago_lint_autofix (T44):
  > T43: verifies BAGO-E001/W002/W003/I002 all detected in problematic Python file
  > T44: verifies bare except + utcnow produce autofixable patches with diffs
  > Full suite: 57/57 passed (was 55/55 before this sprint cycle).
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>

### 🔧 Chore / Mantenimiento

- actualizar estado BAGO — 97 tools, 65/65 tests, sprint activo (`7fde00e`) — MarcValls
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- chmod +x todos los tools del framework (`c09d5ef`) — MarcValls
  > Aplica permisos de ejecución a todos los archivos de herramientas.
  > Resultado de bago permission-check: 100 archivos procesados.
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- comprehensive audit — update docs, fix obsolete refs, sync tool inventory (`df92cc7`) — MarcValls
  > - README.md: tools 87→89, tests 37/37→55/55 (badges + text + table)
  > - CHANGELOG.md: scan/hotspot/fix/gh ✅ Activo (era Pendiente/próximamente)
  > + Added CHG-079/CHG-080 entries, tests 36→55
  > - ESTADO_BAGO_ACTUAL.md: scan/hotspot/fix/gh ✅ Implementado (era 🔜 Próximo)
  > + Tests 36/36→55/55, tool count 33+→89, pipeline hallazgos ✅
  > - CONTRIBUTING.md: 36/36→55/55
  > - .bago/tools/README.md: reescrito con inventario completo de 89 herramientas
  > por categoría (era doc obsoleto de 6 tools)
  > - TREE.txt + CHECKSUMS.sha256: regenerados por validate_pack (GO ✅)
  > - Python syntax: 89/89 tools OK
  > - integration_tests: 55/55 ALL PASS ✅
  > - health_score: 100/100 🟢
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- add scan results, TESTS/TEST_BAGO_01 and workflow artifacts (`ad197b9`) — MarcValls
  > - .bago/state/findings/SCAN-20260422_023341.json: latest scan run
  > - TESTS/TEST_BAGO_01: new test environment with BAGO framework copy
  > - W2_IMPLEMENTACION_CONTROLADA, W9_COSECHA, ideas, stability-summary: workflow artifacts
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- cierre de sesión — repo_context sync, backup excluido de git (`1fbff43`) — MarcValls
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- **state**: reset estado BAGO — v2_status stable, campos activos vacíos (`ceb897d`) — MarcValls
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>

### 🗂️  Otros

- tools #123-124: dep_audit + readme_check (`ebc6ec1`) — MarcValls
  > Tool #123 — dep_audit.py: auditoría de dependencias Python
  > DEP-W001 (sin version), DEP-W002 (rango abierto), DEP-W003 (dup)
  > DEP-E001 offline CVE list (pyyaml,pillow,requests,urllib3,cryptography...)
  > DEP-E002 pip-audit integration opcional (--pip-audit)
  > Parsea requirements*.txt y pyproject.toml. 6/6 ✅
  > Tool #124 — readme_check.py: validador estructura README.md
  > README-W001 (secciones faltantes configurable --sections)
  > README-W002 (placeholders TODO/FIXME/<YOUR_>)
  > README-W003 (enlaces internos rotos #fragment)
  > README-I001 (README muy corto <20 líneas)
  > README-I002 (sin badge shields.io)
  > 6/6 ✅
  > Integration: 78 grupos integration_tests 91/91 ✅
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- tools #121-122: type_check + license_check (`128456c`) — MarcValls
  > Tool #121 — type_check.py: valida anotaciones de tipo Python
  > TYPE-W001 (sin return), TYPE-W002 (params sin tipo),
  > TYPE-W003 (uso de Any), TYPE-I001 (privadas en --strict)
  > Sin dependencias externas — usa stdlib ast. 6/6 ✅
  > Tool #122 — license_check.py: verifica cabeceras de licencia/copyright
  > LIC-W001 (sin header), LIC-W002 (header incompleto), LIC-I001 (ok)
  > --add-header MIT|Apache-2.0|GPL-3.0|custom=<text> autorepara
  > Soporta --ext py,js,ts,... 6/6 ✅
  > Integration: 76 grupos integration_tests 89/89 ✅
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- tools #118-120: api_check + coverage_gate + naming_check (`5f4a60e`) — MarcValls
  > Tool #118 — api_check.py: valida Flask/FastAPI/OpenAPI — API-W001..E001
  > (sin doc, dup routes, path params sin tipado, OpenAPI validation)
  > Tool #119 — coverage_gate.py: quality gate pytest-cov con regresión baseline
  > (parse TOTAL line, threshold, save/compare baseline, CI exit codes)
  > Tool #120 — naming_check.py: PEP 8 naming conventions — NAME-W001..I002
  > (snake_case, PascalCase, UPPER_SNAKE, short vars, generic names)
  > Integration: 74 grupos integration_tests 87/87 ✅
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- tools #116-117: code_review + refactor_suggest (`e027a66`) — MarcValls
  > Tool #116 — code_review.py: reporte CI agregado con score 0-100
  > (lint + complexity + secrets + dead_code + duplicates → MERGE OK/NO)
  > Tool #117 — refactor_suggest.py: RF-W001..RF-I002
  > (funciones largas, alta complejidad, bool params, big classes, try amplios)
  > Integration: routing bago + help + 71 grupos integration_tests 84/84 ✅
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- tools #111-115: doc_coverage + dup_check + pre_commit_gen + metrics_export (`ad0324c`) — MarcValls
  > Tool #111 — doc_coverage.py: cobertura de docstrings 0-100%, --format html/md/json
  > Tool #113 — duplicate_check.py: DUP-W001/W002 bloques duplicados/casi-idénticos
  > Tool #114 — pre_commit_gen.py: genera .pre-commit-config.yaml con hooks BAGO+estándar
  > Tool #115 — metrics_export.py: exporta métricas en Prometheus / JSON / CSV
  > Integration: routing bago + help + 69 grupos integration_tests 82/82 ✅
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- tools #108-110: secret_scan + test_gen + impact_map (`9598aa3`) — MarcValls
  > Tool #108 — secret_scan.py: escaneo de credenciales con 12 patrones
  > (passwords, API keys, AWS, GitHub PAT, OpenAI, PEM, MongoDB, Stripe)
  > Tool #109 — test_gen.py: generador de stubs pytest/unittest via AST
  > Tool #110 — impact_map.py: mapa de dependencias + impacto de cambio
  > (dependentes directos, dependencias, transitivos, salida md/json/dot)
  > Integración: routing en bago + help entries + 65 grupos integration_tests 78/78 ✅
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- Merge pull request #47 from MarcValls/copilot/implement-compatibilidad-lenguajes (`71102ea`) — Marc Valls Sanvictor
  > feat: multi-language support for scan, repo_runner, and findings engine
- Merge pull request #46 from MarcValls/copilot/resuelve-conflictos-pull-request (`eb6f20f`) — Marc Valls Sanvictor
  > merge: resolve bago script conflicts to unblock PR #44
- merge: resolve conflicts with origin/master — keep workspace selector + iteration logger (`f8bef21`) — copilot-swe-agent[bot]
  > Co-authored-by: MarcValls <26687410+MarcValls@users.noreply.github.com>
- merge: resolve new conflicts with origin/master (bago, README.md, CHANGELOG.md) (`8ef8630`) — copilot-swe-agent[bot]
  > Agent-Logs-Url: https://github.com/MarcValls/bago-framework/sessions/4c09111a-95d4-490f-a668-e152d896de39
  > Co-authored-by: MarcValls <26687410+MarcValls@users.noreply.github.com>
- merge: resolve conflicts with origin/master — keep iteration logger + workspace selector (`5908032`) — copilot-swe-agent[bot]
  > Agent-Logs-Url: https://github.com/MarcValls/bago-framework/sessions/23fc2a8f-413b-4ff1-9420-a7dba48b80c6
  > Co-authored-by: MarcValls <26687410+MarcValls@users.noreply.github.com>
- Merge pull request #45 from MarcValls/copilot/nueva-orientacion-fase4 (`c9f5463`) — Marc Valls Sanvictor
  > docs: describe Fase 4 internal subtools in CHANGELOG and README
- SPRINT-005 PROXIMO: Python 3.9 compat, dashboard v2, auto_mode fix, CDTR-001, watch, testgen Go/Rust, IDEAS scoring dinámico (`f4dc0dc`) — MarcValls
  > [CHG-080] 7 mejoras implementadas:
  > - Python 3.9 compat: Optional[str] en gh_integration, contracts, auto_mode
  > - auto_mode._detector(): leer score correcto de context_detector (era high_signals)
  > - pack_dashboard v2: cockpit 460 líneas, health ring, deuda, velocity sparkline, contratos countdown
  > - validate_state: RULE-CDTR-001 enforcement (CDTR-E01 blocking, CDTR-E02 advisory)
  > - bago_watch.py: nuevo tool — polling SHA256, delta findings, health post-change
  > - testgen: Go + Rust (analyze+generate+dispatch en main loop)
  > - emit_ideas: _title_similarity + apply_dynamic_scoring + register_implemented_idea
  > bago validate → GO state | inventory.changes=63
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- Merge pull request #43 from MarcValls/copilot/add-interactive-bago-start-command (`ea54a82`) — Marc Valls Sanvictor
  > feat: UX overhaul — add `bago start`/`bago status`, Quick Start panel, and README
- Initial plan (`43a5468`) — copilot-swe-agent[bot]
- repo-*: usar repo activo automáticamente tras repo-on (`f3f9471`) — MarcValls
  > - bago: unir fragmentos de path con espacios para repo-* cmds
  > - repo_runner.py: nargs='*' + join para tolerar paths con espacios
  > - _default_repo_target() ya lee repo_context.json (working_mode=external)
  > Flujo: bago repo-on /path → bago repo-debug (sin path) ✓
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- bago_debug: git grep en lugar de rg para conflict markers (`8183231`) — MarcValls
  > - git grep -l: solo busca en archivos tracked, muy rápido
  > - fallback a rg si git no está disponible
  > - captura FileNotFoundError Y TimeoutExpired en ambos casos
  > - elimina grep -r que podía tardar minutos en repos grandes
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- repo_on.py: tolerar paths con espacios sin comillas (`1eeebcc`) — MarcValls
  > Cambia nargs='?' → nargs='*' y une los fragmentos con join.
  > Así 'bago repo-on /path/con espacio' funciona igual que
  > 'bago repo-on "/path/con espacio"'.
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- bago: auto-instala LaunchBAGO.app si no existe (`9b06ccd`) — MarcValls
  > _ensure_launcher() comprueba al inicio de cada invocación
  > si LaunchBAGO.app existe; si no, ejecuta setup-launcher.sh
  > automáticamente antes de continuar con el comando pedido.
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- terminal launch: URL scheme bago-launch:// via LaunchBAGO.app (`ff6bc4a`) — MarcValls
  > - setup-launcher.sh: compila LaunchBAGO.app con osacompile y registra
  > el URL scheme bago-launch:// en LaunchServices (ejecutar 1 vez)
  > - menu.html: botón usa href=bago-launch://start (funciona en todos
  > los navegadores, no solo Safari)
  > - LaunchBAGO.app añadido a .gitignore (artefacto binario local)
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- menu.html: remove copy-command UI, single terminal launch button (`00c3907`) — MarcValls
  > - Removed START_CMD const and copyCommand() function
  > - Removed .start-instructions HTML/CSS (.cmd-row, .cmd-text, .copy-btn)
  > - setStateFound(): hides launch-btn, shows open-btn
  > - setStateNotFound(): shows launch-btn + retry-btn, hides open-btn
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>


## [bago-v2.4-v2rc-template-seed] — 2026-04-19

### ✨ Nuevas Funcionalidades

- version tracking + empaquetado para tester (`4efae5f`) — MarcValls
  > - bago versions: nuevo comando en root y v02-template-seed
  > - VERSION_INFO.json en cada cleanversion (slug, descripcion, modo, notas)
  > - Renombradas cleanversions a slugs legibles: v01-base-clean, v01-base-patched, v02-template-seed
  > - TESTER_README.md en v02-template-seed con checklist de pruebas
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- **bago-viewer**: radar de evolución + UI refactor (`291093d`) — MarcValls
  > - compute_evolution(): radar 6 dimensiones (diversidad, protocolo,
  > alcance, foco, producción, rigor) con denominadores adaptativos
  > - pack.html: UI limpiada, sección evolución, badges simplificados
  > - base.html: Chart.js 4.4.0 + annotation plugin
  > - start.sh: fix stdin bad file descriptor
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- bootstrap CAJAFISICA — bago-viewer web dashboard (`b7cfe8b`) — MarcValls
  > Página web (Flask) para seleccionar, inspeccionar y medir packs .bago.
  > Incluye escaneo automático, métricas de esfuerzo, validadores GO/KO
  > y selector de carpeta nativo macOS.
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>

### 🔧 Chore / Mantenimiento

- versionar pack BAGO completo + cleanversions (`0a1cdc3`) — MarcValls
  > - .bago/ (39 CHG): pack evolucionado activo — copia de trabajo del framework
  > - Makefile + bago: runner y comandos del framework
  > - docs/: auditoría, patch, propuesta V2
  > - cleanversion/...161154: snapshot base (0 CHG) + intermedio (3 CHG)
  > - cleanversion/...161154 3: nueva cleanversion con bago script v2
  > · Añade distribution_mode: template_seed en global_state.json
  > · Al primer arranque sin args pregunta: [1] evolucionar framework
  > o [2] proyecto nuevo (destino = dir actual si se omite ruta)
  > · Prompt solo con TTY; auto-sync después del prompt
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
- añadir .gitignore (`6961733`) — MarcValls
  > Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>


---
*Generado con `bago changelog-gen`*

