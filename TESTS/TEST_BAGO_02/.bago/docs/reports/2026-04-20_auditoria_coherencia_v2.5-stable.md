# Auditoría de Coherencia — BAGO Framework v2.5-stable

> Fecha: 2026-04-20
> Tipo: Auditoría de coherencia
> Alcance: Repositorio público `MarcValls/bago-framework`
> Estado final: ✅ Limpio y coherente

---

## Contexto

El repositorio fue publicado como release pública `v2.5-stable`. Aunque el código funcionaba correctamente, contenía inconsistencias acumuladas entre la documentación, los nombres de archivos, las referencias cruzadas y el estado real de la instalación limpia.

Se realizaron **7 pasadas de corrección** en profundidad creciente, cada una como PR independiente mergeado a `master`.

---

## PR #4 — Naming básico y entrypoint del agente

| Archivo | Cambio |
|---------|--------|
| `.bago/agents/MAESTRO_BAGO.md` | H1 `COORDINADOR_BAGO` → `MAESTRO_BAGO` |
| `.bago/AGENT_START.md` | `Leer README.md` → `Leer ../README.md para capa pública` |

---

## PR #5 — Cabeceras de documentos obsoletas + JSON faltante

| Archivo | Cambio |
|---------|--------|
| `.bago/docs/BAGO_REFERENCIA_COMPLETA.md` | `2.4-v2rc` → `2.5-stable` |
| `.bago/docs/DECISIONES.md` | `V2.2.2` → `2.5-stable` |
| `.bago/docs/MAPA_DEL_SISTEMA.md` | `V2.2.2` → `2.5-stable` |
| `.bago/docs/operation/GUIA_DE_USO.md` | `V2.2.2` → `2.5-stable` |
| `.bago/docs/V2_PLAYBOOK_OPERATIVO.md` | `V2.0 / 2.4-v2rc` → `2.5-stable` |
| `.bago/docs/V2_POLITICA_TRANSICION.md` | `V2.0 / 2.4-v2rc` → `2.5-stable` |
| `.bago/docs/V2_CONTRATO_CIERRE_ESCENARIO.md` | `V2.0 / 2.4-v2rc` → `2.5-stable` |
| `.bago/docs/architecture/BAGO_V2_2_2_ARQUITECTURA.md` | Cabecera actualizada |
| `.bago/state/implemented_ideas.json` | **CREADO** como plantilla vacía |

---

## PR #6 — Coherencia de agentes y roles

| Archivo | Cambio |
|---------|--------|
| `.bago/roles/gobierno/MAESTRO_BAGO.md` | H1 `COORDINADOR BAGO` → `MAESTRO_BAGO` + versión → `2.5-stable` |
| 11 archivos en `.bago/roles/` | `version: 2.2.2` → `2.5-stable` |
| 6 stubs en `.bago/agents/` | Añadido puntero a definición canónica en `.bago/roles/` |
| `.bago/agents/GUIA_VERTICE.md` | Añadido aviso de deprecación |

---

## PR #7 — Auditoría profunda completa

Auditoría autónoma de 566 archivos con 52 llamadas a herramientas.

### IDs y nombres obsoletos

| Archivo | Cambio |
|---------|--------|
| `.bago/roles/gobierno/MAESTRO_BAGO.md` | `id: role_coordinator_bago` → `id: role_maestro_bago` |
| `.bago/prompts/activar_maestro.md` | H1 + cuerpo: `COORDINADOR BAGO` → `MAESTRO_BAGO` |
| `.bago/START_AGENT.md` | `BAGO AMTEC V2.2.2` → `BAGO 2.5-stable` |
| `.bago/tools/perf/README.md` | `(V2.2.2)` → `(2.5-stable)` |
| `.bago/core/00_CEREBRO_BAGO.md` | H1 `00_CORE_BAGO` → `00_CEREBRO_BAGO` |

### Rutas absolutas hardcodeadas (crítico)

| Archivo | Cambio |
|---------|--------|
| `.bago/docs/analysis/BAGO_EVOLUCION_SISTEMA.md` | Eliminadas 6 rutas `file:///Users/INTELIA_Manager/Documents/...` → referencias portables |

### Referencias a directorios inexistentes en instalación limpia

| Archivo | Cambio |
|---------|--------|
| `.bago/docs/operation/GUIA_ARTEFACTOS.md` | Nota: `state/metrics/` se crea en primer uso |
| `.bago/docs/architecture/BAGO_V2_2_2_ARQUITECTURA.md` | Nota: `state/metrics/runs/*` se crea en primer uso de perf |
| `.bago/tools/perf/README.md` | Nota: `state/metrics/runs/` se crea automáticamente |
| `.bago/docs/operation/templates/tpl_analysis.md` | Nota: `state/evaluations/` y `state/metrics/` se crean en primer uso |

### Normalización de H1 en workflows W1–W6

| Workflow | Antes | Después |
|----------|-------|---------|
| W1 | `# W1_COLD_START` | `# W1 · Cold Start` |
| W2 | `# W2_IMPLEMENTACION_CONTROLADA` | `# W2 · Implementación Controlada` |
| W3 | `# W3_REFACTOR_SENSIBLE` | `# W3 · Refactor Sensible` |
| W4 | `# W4_DEBUG_MULTICAUSA` | `# W4 · Debug Multicausa` |
| W5 | `# W5_CIERRE_Y_CONTINUIDAD` | `# W5 · Cierre y Continuidad` |
| W6 | `# W6_IDEACION_APLICADA` | `# W6 · Ideación Aplicada` |

---

## Resumen numérico

| Métrica | Valor |
|---------|-------|
| PRs mergeados | 7 |
| Archivos modificados | ~40 |
| Archivos creados | 2 (`implemented_ideas.json`, este informe) |
| Rutas absolutas eliminadas | 6 |
| Versiones actualizadas | 20+ |
| Workflows normalizados | 6 |
| IDs corregidos | 1 |
| Referencias COORDINADOR→MAESTRO | 5 instancias en 3 archivos |

---

## Estado final verificado

- ✅ `bago validate` pasa sin errores
- ✅ Sin referencias obsoletas a `V2.2.2` / `V2.0` / `2.4-v2rc` en documentos operativos
- ✅ Sin rutas absolutas a máquina local
- ✅ Sin referencias a `COORDINADOR BAGO` fuera de documentación histórica canónica
- ✅ Todos los workflows con H1 descriptivo uniforme (W0–W9)
- ✅ Capa de agentes y roles coherente entre sí
- ✅ `implemented_ideas.json` existe para instalación limpia
- ✅ Directorios runtime documentados como "creados en primer uso"
