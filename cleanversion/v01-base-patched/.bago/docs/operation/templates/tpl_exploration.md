# Plantilla — Sesión de Exploración (W8)

> Copiar este archivo al abrir una sesión W8. Rellenar antes de empezar.

---

## Datos de sesión

```json
{
  "session_id": "SES-W8-YYYY-MM-DD-001",
  "task_type": "analysis",
  "selected_workflow": "w8_exploracion",
  "bago_mode": "on",
  "roles_activated": ["role_auditor"],
  "user_goal": "<área de exploración: qué quieres entender mejor>",
  "status": "open",
  "created_at": "<ISO8601>",
  "artifacts_planned": ["<artefacto orientativo — puede cambiar>"],
  "preflight_resultado": "GO",
  "artifacts": [],
  "decisions": [],
  "summary": ""
}
```

---

## Preflight

- [ ] `validate_pack.py` → GO
- [ ] `pack_dashboard.py` → leer producción y estado

---

## Área de exploración

**¿Qué zona del pack quiero entender mejor?**

> _[escribir el área aquí]_

**¿Qué síntoma o pregunta me trajo aquí?**

> _[escribir la señal aquí]_

---

## Lo que encontré

> _[notas durante la exploración]_

**Gap principal identificado:**

> _[descripción concreta del gap]_

**¿Es accionable en esta sesión?**
- [ ] Sí → resolverlo y documentar en `artifacts`
- [ ] No (scope grande) → abrir sesión W7 con objetivo concreto

---

## Artefactos producidos

_(completar al cerrar)_

| Artefacto | Tipo | Valor |
|-----------|------|-------|
| | | |

---

## Decisiones

_(completar al cerrar — mínimo 1)_

1. 

---

## Cierre

- [ ] ≥1 artefacto útil real en `artifacts`
- [ ] ≥1 decisión en `decisions`
- [ ] `status: "closed"`
- [ ] `summary` completado
- [ ] CHG + EVD creados
- [ ] `global_state.json` actualizado
- [ ] `validate_pack.py` → GO
