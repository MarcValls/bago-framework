# BAGO V2 — Contrato de Cierre de Escenario

> Versión: V2.0 | Pack: 2.4-v2rc | Fecha: 2026-04-18

---

## 1. Propósito

Define el **contrato técnico y de gobernanza** que debe cumplirse para declarar un escenario como cerrado en BAGO V2. El objetivo es eliminar escenarios "semivivos": formalmente activos pero sin actividad real, con evaluación final ya producida, o con estado contradictorio entre el archivo MD y `global_state.json`.

---

## 2. Definición de escenario en BAGO

Un **escenario** es una unidad de trabajo de medio-largo plazo que agrupa sesiones, cambios y evidencias bajo un objetivo común. No es una sesión ni una tarea — es el contenedor de contexto de un experimento, implementación o investigación que puede durar días o semanas.

Los escenarios se registran en:
- `state/scenarios/ESCENARIO-{ID}-{NOMBRE}.md` — archivo descriptor
- `state/global_state.json → active_scenarios[]` — lista de activos

---

## 3. Criterios obligatorios de cierre

Un escenario puede cerrarse **solo si se cumplen los 5 criterios siguientes**:

### 3.1 Evaluación final presente (EVAL)
- Debe existir un archivo `state/scenarios/EVAL-{ESCENARIO-ID}-*.md`
- El archivo debe contener:
  - Resumen del escenario
  - Métricas o resultados observados
  - Decisiones tomadas
  - Veredicto: ÉXITO / PARCIAL / ABANDONADO

### 3.2 Estado "CERRADO" en el descriptor del escenario
- El archivo `ESCENARIO-{ID}-*.md` debe contener la línea:
  ```
  Estado: CERRADO ✅
  ```
- O equivalente aceptable: `estado: cerrado`, `STATUS: CLOSED`
- No se acepta "en revisión" o "pendiente de cierre" como estado de cierre

### 3.3 Eliminado de active_scenarios en global_state.json
- `global_state.json → active_scenarios[]` **no debe contener** el ID del escenario
- Verificación: `stale_detector.py` debe pasar sin ERRORs relacionados con este escenario

### 3.4 Al menos 1 evidencia tipo `closure` asociada
- Debe existir al menos 1 archivo en `state/evidences/` de tipo `closure` que referencie el escenario
- El tipo se declara en el campo `"type"` o `"evidence_type"` del JSON
- Alternativa aceptable: evidencia tipo `handoff` si el escenario se transfiere a otro contexto

### 3.5 Cambio de tipo `governance` o `architecture` registrado
- Debe existir al menos 1 CHG en `state/changes/` de tipo `governance` o `architecture`
- El CHG debe referenciar el escenario en su campo `"context"` o `"notes"`
- Justificación: el cierre de un escenario siempre implica una decisión estructural

---

## 4. Protocolo de cierre (paso a paso)

```
1. Producir EVAL-{ID}-FINAL.md en state/scenarios/
   → Incluir métricas, decisiones, veredicto

2. Actualizar ESCENARIO-{ID}-*.md
   → Cambiar Estado: ACTIVO → CERRADO ✅
   → Añadir fecha de cierre

3. Crear EVD tipo "closure"
   → Referenciar escenario, enlazar EVAL
   → Registrar en state/evidences/

4. Crear CHG tipo "governance"
   → Describir la decisión de cierre
   → Registrar en state/changes/

5. Actualizar global_state.json
   → Eliminar escenario de active_scenarios[]
   → Actualizar last_completed_evidence_id, last_completed_change_id

6. Verificar con stale_detector.py
   → Debe pasar sin ERRORs ni contradicciones para este escenario
```

---

## 5. Escenarios no completados: estados especiales

| Estado | Descripción | Criterios especiales |
|---|---|---|
| **ABANDONADO** | El escenario no completará su objetivo | EVAL con veredicto ABANDONADO + EVD closure |
| **TRANSFERIDO** | El contexto pasa a otro escenario o repo | EVD tipo handoff + referencia al destino |
| **PAUSADO** | Activo pero sin actividad planificada | Permanecer en active_scenarios con nota de pausa |
| **CERRADO PARCIAL** | Objetivo parcialmente conseguido | EVAL con veredicto PARCIAL es válido |

---

## 6. Verificación automática

El script `stale_detector.py` detecta automáticamente violaciones de este contrato:

- Escenario en `active_scenarios` con EVAL presente → contradicción (ERROR)
- Escenario con "Estado: CERRADO" en MD pero en `active_scenarios` → contradicción (ERROR)

La `v2_close_checklist.py` incluye verificación de escenarios coherentes como criterio de GO V2.

---

## 7. Historial de escenarios

| ID | Nombre | Estado | Cierre |
|---|---|---|---|
| ESCENARIO-001 | — | CERRADO | — |
| ESCENARIO-002 | — | CERRADO | — |
| ESCENARIO-003 | COSECHA-CONTEXTUAL | CERRADO | 2026-04-18 |

---

*Documento parte del ecosistema BAGO V2 — ver también: `V2_POLITICA_TRANSICION.md`, `V2_PLAYBOOK_OPERATIVO.md`*
