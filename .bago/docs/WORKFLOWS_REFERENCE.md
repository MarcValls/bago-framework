# WORKFLOWS REFERENCE — BAGO v3.0

> Generado automáticamente | Estado: `{'SPRINT-001': 'closed', 'SPRINT-002': 'closed', 'SPRINT-003': 'closed', 'SPRINT-004': 'closed', 'SPRINT-005': 'closed', 'SPRINT-006': 'closed', 'SPRINT-007': 'open', 'SPRINT-008': 'closed'}` | Tests: `114/114` | CHG: `98`

## Resumen

| ID | Nombre | Uso principal |
|----|--------|---------------|
| `W0` | [FREE_SESSION](../workflows/W0_FREE_SESSION.md) | Control para sesiones off — solo ESCENARIO-002 (competición on/off) |
| `W1` | [COLD_START](../workflows/W1_COLD_START.md) | Arrancar desde un repo desconocido |
| `W2` | [IMPLEMENTACION_CONTROLADA](../workflows/W2_IMPLEMENTACION_CONTROLADA.md) | Implementar sin dispersión ni pérdida de trazabilidad |
| `W3` | [REFACTOR_SENSIBLE](../workflows/W3_REFACTOR_SENSIBLE.md) | Refactorizar sin romper contratos ni introducir deriva |
| `W4` | [DEBUG_MULTICAUSA](../workflows/W4_DEBUG_MULTICAUSA.md) | Diagnosticar fallos con causas plausibles múltiples |
| `W5` | [CIERRE_Y_CONTINUIDAD](../workflows/W5_CIERRE_Y_CONTINUIDAD.md) | Cerrar una sesión con continuidad y siguiente paso claro |
| `W6` | [IDEACION_APLICADA](../workflows/W6_IDEACION_APLICADA.md) | Analizar el repo y devolver ideas concretas priorizadas por implementabilidad y estabilidad |
| `W7` | [FOCO_SESION](../workflows/W7_FOCO_SESION.md) | Arrancar una sesión con objetivo único, máximo 2 roles y artefactos pre-declarados |
| `W8` | [EXPLORACION](../workflows/W8_EXPLORACION.md) | Sesión exploratoria ligera — preflight mínimo, ≥1 artefacto, ≥1 decisión |
| `W9` | [COSECHA](../workflows/W9_COSECHA.md) | Cosecha contextual post-exploración — 3 preguntas, ≤5 min |

---

## W0 — FREE_SESSION

> Control para sesiones off — solo ESCENARIO-002 (competición on/off). No usar en producción.

→ [Ver workflow completo](.bago/workflows/W0_FREE_SESSION.md)

---

## W1 — COLD_START

> Arrancar desde un repo desconocido. Mapeo inicial, contexto útil, baseline establecido.

**Objetivo:** Convertir un repositorio desconocido en un contexto operativo utilizable.

→ [Ver workflow completo](.bago/workflows/W1_COLD_START.md)

---

## W2 — IMPLEMENTACION_CONTROLADA

> Implementar sin dispersión ni pérdida de trazabilidad. CHG + EVD por cada cambio.

**Objetivo:** Implementar una tarea técnica sin dispersión ni pérdida de trazabilidad.

→ [Ver workflow completo](.bago/workflows/W2_IMPLEMENTACION_CONTROLADA.md)

---

## W3 — REFACTOR_SENSIBLE

> Refactorizar sin romper contratos ni introducir deriva. Gate pre/post de tests y detector.

**Objetivo:** Refactorizar sin romper contratos ni introducir deriva.

→ [Ver workflow completo](.bago/workflows/W3_REFACTOR_SENSIBLE.md)

---

## W4 — DEBUG_MULTICAUSA

> Diagnosticar fallos con causas plausibles múltiples. Mínimo 3 hipótesis antes de actuar.

**Objetivo:** Investigar y resolver fallos donde hay varias causas plausibles.

→ [Ver workflow completo](.bago/workflows/W4_DEBUG_MULTICAUSA.md)

---

## W5 — CIERRE_Y_CONTINUIDAD

> Cerrar una sesión con continuidad y siguiente paso claro. Cierre formal con sesión y EVD.

**Objetivo:** Dejar la sesión retocable y retomable.

→ [Ver workflow completo](.bago/workflows/W5_CIERRE_Y_CONTINUIDAD.md)

---

## W6 — IDEACION_APLICADA

> Analizar el repo y devolver ideas concretas priorizadas por implementabilidad y estabilidad.

**Objetivo:** Analizar el repo y proponer ideas contextualizadas, priorizadas por implementabilidad y estabilidad.

→ [Ver workflow completo](.bago/workflows/W6_IDEACION_APLICADA.md)

---

## W7 — FOCO_SESION

> Arrancar una sesión con objetivo único, máximo 2 roles y artefactos pre-declarados. Workflow estándar productivo.

→ [Ver workflow completo](.bago/workflows/W7_FOCO_SESION.md)

---

## W8 — EXPLORACION

> Sesión exploratoria ligera — preflight mínimo, ≥1 artefacto, ≥1 decisión. W7-lite sin objetivo previo.

→ [Ver workflow completo](.bago/workflows/W8_EXPLORACION.md)

---

## W9 — COSECHA

> Cosecha contextual post-exploración — 3 preguntas, ≤5 min. Genera sesión harvest + CHG + EVD automáticamente.

→ [Ver workflow completo](.bago/workflows/W9_COSECHA.md)

---

## Orden recomendado de uso

```
Nueva sesión productiva  →  W7_FOCO_SESION
Exploración sin objetivo →  W8_EXPLORACION  →  W9_COSECHA
Repo desconocido         →  W1_COLD_START
Implementar feature       →  W2_IMPLEMENTACION_CONTROLADA
Refactor                  →  W3_REFACTOR_SENSIBLE
Debug complejo            →  W4_DEBUG_MULTICAUSA
Cierre de sesión          →  W5_CIERRE_Y_CONTINUIDAD
Generar ideas             →  W6_IDEACION_APLICADA  (o: bago ideas)
Control off               →  W0_FREE_SESSION  (solo ESCENARIO-002)
```

## Herramientas clave por workflow

| Workflow | Herramientas BAGO |
|----------|-------------------|
| W7/W8    | `bago health` · `bago validate` · `context_detector` |
| W9       | `bago cosecha` · `emit_ideas` · `reconcile_state` |
| W2/W3    | `bago validate` · `bago audit` · `risk_matrix` |
| W6       | `emit_ideas` · `debt_ledger` · `IDEAS_BACKLOG.json` |
| General  | `bago dashboard` · `metrics_dashboard` · `integration_tests` |

---
*Actualizado: 2026-04-23 | BAGO v3.0 | Autor: BAGO-AUTONOMOUS-002*