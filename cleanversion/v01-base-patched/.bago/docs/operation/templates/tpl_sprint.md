# Plantilla de sesión — `sprint`

> Para sesiones que agrupan múltiples entregables bajo un objetivo de sprint.  
> La producción esperada es la más alta de todos los tipos.

---

## Preflight checklist

```bash
python3 .bago/tools/session_preflight.py \
  --objetivo "TODO: Sprint N — [objetivo] para que [criterio de done del sprint]" \
  --roles "role_organizer,role_vertice" \
  --artefactos "TODO: lista de todos los entregables del sprint" \
  --task-type sprint
```

---

## Datos de sesión

| Campo | Valor |
|-------|-------|
| **session_id** | `SES-S<N>-YYYY-MM-DD-001` |
| **task_type** | `sprint` |
| **selected_workflow** | `w7_foco_sesion` o `workflow_ejecucion` |
| **roles** | `role_organizer` + `role_vertice` |
| **objetivo** | TODO |
| **sprint_number** | N |

---

## Artefactos planificados

Un sprint debería producir **todos** los entregables definidos en su objetivo, más los de cierre:

```
# Entregables del sprint (depende del objetivo)
<artefacto_1>
<artefacto_2>
<artefacto_3>

# Cierre del sprint
state/sessions/SES-S<N>-*.json
state/changes/BAGO-CHG-XXX.json
state/evidences/BAGO-EVD-XXX.json
```

---

## Plan de sprint (rellenar antes de ejecutar)

| # | Entregable | Tipo | Done cuando |
|---|-----------|------|-------------|
| 1 | … | tool/doc/workflow | … |
| 2 | … | tool/doc/workflow | … |
| 3 | … | tool/doc/workflow | … |

---

## Retrospectiva post-sprint (rellenar al cerrar)

| # | Entregable | Estado | Notas |
|---|-----------|--------|-------|
| 1 | … | ✅/❌ | … |
| 2 | … | ✅/❌ | … |

**Artefactos útiles producidos:** N  
**Score producción:** X/10  
**¿Se alcanzó el objetivo?** S/N  

---

## Decisiones del sprint

```
- Decisión 1: …
- Decisión 2: …
```

---

## Checklist de cierre

- [ ] Todos los entregables del plan marcados ✅ o justificada su omisión
- [ ] CHG + EVD con `sprint_number` en metadata
- [ ] `global_state.json` → `sprint_N: DONE`
- [ ] ESTADO_BAGO_ACTUAL.md actualizado
- [ ] TREE + CHECKSUMS → validate_pack GO
- [ ] ZIP de distribución generado (opcional)
