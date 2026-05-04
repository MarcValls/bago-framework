# ESTADO_BAGO_ACTUAL

> **Nota:** este archivo describe el estado del pack BAGO como sistema.
> Última actualización: **2026-05-01T17:25:00Z** (BAGO auto — self-heal run)

## Versión activa

**BAGO v2.5-stable** — Structured AI Work Framework

## Estado de validadores

| Validador | Estado |
|-----------|--------|
| `validate_manifest` | ✅ GO |
| `validate_state` | ✅ GO |
| `validate_pack` | ✅ GO |
| `purity_check` | ✅ OK |
| `stale_detector` | ✅ OK |
| `sincerity` | ✅ 0 errores / 0 warnings (175 .md escaneados) |
| `stability` | ⚠️ WARN — sandbox unavailable; validators canónicos en verde |
| `tool_guardian` | 🔴 0% health — 33 E001 / 29 E002 / 18 W001 / 2 W002 |

## Health Score

**ok** — Validadores canónicos en GO. Sistema operativo y coherente.
Health score numérico permanece estático hasta primer `bago cosecha` cerrado.

## Inventario declarado

| Recurso | Cantidad |
|---|---|
| Sesiones cerradas | 0 |
| Cambios (CHG) | 0 |
| Evidencias (EVD) | 0 |
| Commits en repo | 3 |

## Último commit registrado

| Campo | Valor |
|---|---|
| SHA | `da5f367` |
| Fecha | 2026-04-23T17:27:11+02:00 |
| Mensaje | `feat: auto session-close artefact on show_task --done (CHG-001, 4/4 tests)` |

## ✅ Resuelto en esta sesión auto

| Item | Resolución |
|---|---|
| `stash@{0}` — partial auto-rename validate_*.py | Descartado — cambios ya en commit `7967d86` |
| `stash@{1}` — commit_readiness.py local edit | Descartado — cambios ya en commit `7967d86` |

## 🔴 Hallazgo crítico — tool-guardian (0% health)

`tool-guardian` detecta que **ninguno de los 44 tools operativos** supera los estándares mínimos del framework.

| Código | Descripción | Afecta |
|---|---|---|
| GUARD-E001 | Sin flag `--test` implementado | 33 tools |
| GUARD-E002 | No registrado en `integration_tests.py` | 29 tools |
| GUARD-W001 | Sin routing en `bago` script | 18 tools |
| GUARD-W002 | Sin docstring de módulo | 2 tools (`emit_ideas.py`, `generate_bago_evolution_report.py`) |

**Dead reference detectada:** `intent_router.py` referencia `legacy-fix` como tool del intent `self_heal`, pero ese comando no existe en el script `bago`.

## ⏳ Tarea pendiente declarada — CHG-002

**Objetivo:** añadir `--test` a los tools core y registrarlos en `integration_tests.py`
**Prioridad:** tools del ciclo canónico primero: `validate_manifest`, `validate_state`, `validate_pack`, `show_task`, `cosecha`, `health_score`, `stale_detector`
**Workflow recomendado:** W2_IMPLEMENTACION_CONTROLADA
**Activar con:** `bago session` + W7_FOCO_SESION → preflight → implementar por batches de 5

## Modo de trabajo

`working_mode: self` — BAGO opera sobre su propio directorio host (`/Users/INTELIA_Manager/bago-framework`)

## Notas

BAGO auto 2026-05-01 — Sistema operativo. Stashes obsoletos resueltos. Guardian revela deuda técnica sistémica en cobertura de tests. Próxima sesión: CHG-002.

## Versión activa

**BAGO v2.5-stable** — Structured AI Work Framework

## Estado de validadores

| Validador | Estado |
|-----------|--------|
| `validate_manifest` | ✅ GO |
| `validate_state` | ✅ GO |
| `validate_pack` | ✅ GO |
| `purity_check` | ✅ OK |
| `stale_detector` | ✅ OK |
| `sincerity` | ✅ 0 errores / 0 warnings |
| `stability` | ⚠️ WARN — sandbox unavailable; validators canónicos en verde |

## Health Score

**ok** — Todos los validadores canónicos en GO. Sistema operativo y coherente.
Health score numérico permanecerá estático hasta primer `bago cosecha` cerrado.

## Inventario declarado

| Recurso | Cantidad |
|---|---|
| Sesiones cerradas | 0 |
| Cambios (CHG) | 0 |
| Evidencias (EVD) | 0 |
| Commits en repo | 3 |

## Último commit registrado

| Campo | Valor |
|---|---|
| SHA | `da5f367` |
| Fecha | 2026-04-23T17:27:11+02:00 |
| Mensaje | `feat: auto session-close artefact on show_task --done (CHG-001, 4/4 tests)` |

## ⚠️ Items no resueltos

| ID | Tipo | Descripción | Acción recomendada |
|---|---|---|---|
| STASH-0 | Git stash | `partial auto-rename (incoherent)` en `validate_{manifest,state}.py` | Revisar, integrar o `git stash drop` |
| STASH-1 | Git stash | `commit_readiness.py` local edit | Revisar, integrar o `git stash drop` |

## Modo de trabajo

`working_mode: self` — BAGO opera sobre su propio directorio host (`/Users/INTELIA_Manager/bago-framework`)

## Notas

Update 2026-05-01 — Sistema en estado operativo. Sin sesiones BAGO cerradas aún.
Próximo paso recomendado: abrir primera sesión real con **W7_FOCO_SESION** y cerrar con `bago cosecha`.
