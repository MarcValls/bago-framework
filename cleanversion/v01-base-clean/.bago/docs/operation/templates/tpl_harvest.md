# Plantilla · Sesión Harvest (W9)

> Usar con: `python3 .bago/tools/cosecha.py`  
> Esta plantilla documenta manualmente una cosecha si el script no está disponible.

---

**session_id:** SES-HARVEST-[FECHA]-[NNN]  
**task_type:** harvest  
**workflow:** w9_cosecha  
**roles:** role_auditor  
**escenario:** ESCENARIO-003  
**fecha:** [YYYY-MM-DD]  

---

## Pregunta 1 — ¿Qué decidiste?

> La decisión principal de esta exploración. Qué elegiste y por qué.

[respuesta]

---

## Pregunta 2 — ¿Qué descartaste y por qué?

> Qué opción o camino quedó fuera. La razón del descarte.

[respuesta]

---

## Pregunta 3 — ¿Cuál es el próximo paso concreto?

> El siguiente artefacto a producir o acción a ejecutar.

[respuesta]

---

## Ficheros afectados

> Lista de ficheros modificados durante la exploración que se formalizan en esta cosecha.

- [fichero 1]
- [fichero 2]

---

## JSON de sesión generado

```json
{
  "session_id": "SES-HARVEST-[FECHA]-[NNN]",
  "task_type": "harvest",
  "selected_workflow": "w9_cosecha",
  "roles_activated": ["role_auditor"],
  "status": "closed",
  "decisions": [
    "DECISIÓN: [respuesta pregunta 1]",
    "DESCARTE: [respuesta pregunta 2]"
  ],
  "next_step": "[respuesta pregunta 3]",
  "summary": "Harvest W9. Decisión: [resumen]. Próximo: [próximo paso]."
}
```
