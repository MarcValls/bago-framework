# bago template — Plantillas para sesiones

> Lista, muestra, crea y aplica plantillas para arrancar nuevas sesiones con campos pre-rellenados.

---

## Descripción

`bago template` gestiona plantillas de sesión reutilizables que definen: objetivo, roles, workflow, artefactos esperados, decisiones esperadas y checklist de apertura. Al crear una sesión desde una plantilla (`template new <nombre>`), los campos quedan pre-rellenados en el JSON de sesión, acelerando el arranque y asegurando consistencia.

El framework incluye **plantillas de fábrica**: `sprint`, `analysis`, `hotfix`, `exploration`. También puedes definir las tuyas con `template create`.

---

## Uso

```bash
bago template list                    → listar plantillas disponibles (built-in + custom)
bago template show <nombre>           → ver contenido de una plantilla
bago template new <nombre>            → crear sesión a partir de la plantilla
bago template create <nombre>         → definir nueva plantilla interactivamente
bago template delete <nombre>         → eliminar plantilla custom
bago template --test                  → ejecutar tests integrados
```

---

## Opciones

| Opción | Descripción |
|--------|-------------|
| `list` | Muestra todas las plantillas disponibles con descripción |
| `show <nombre>` | Imprime el JSON completo de la plantilla |
| `new <nombre>` | Genera un `SES-*.json` pre-rellenado desde la plantilla |
| `create <nombre>` | Asistente interactivo para definir una nueva plantilla |
| `delete <nombre>` | Elimina una plantilla custom (las built-in no se pueden borrar) |
| `--test` | Ejecuta los tests integrados de la herramienta |

---

## Plantillas de fábrica

| Nombre | Workflow | Descripción |
|--------|----------|-------------|
| `sprint` | W7_FOCO_SESION | Sesión de sprint productivo con objetivos claros |
| `analysis` | W2_IMPLEMENTACION_CONTROLADA | Análisis y diagnóstico del sistema |
| `hotfix` | W7_FOCO_SESION | Corrección urgente con impacto controlado |
| `exploration` | W8_EXPLORACION | Exploración libre de ideas o territorio desconocido |

---

## Ejemplos

```bash
# Ver plantillas disponibles
bago template list

# Ver qué incluye la plantilla 'sprint'
bago template show sprint

# Arrancar una sesión de sprint desde plantilla
bago template new sprint
# → crea SES-SPRINT-2026-04-22-001.json pre-rellenado

# Crear plantilla custom para sesiones de revisión semanal
bago template create weekly-review

# Aplicar tu plantilla custom
bago template new weekly-review
```

---

## Formato de datos

Las plantillas custom se guardan en `.bago/state/templates/<nombre>.json`:

```json
{
  "name": "sprint",
  "description": "Sesión de sprint productivo con objetivos claros",
  "user_goal": "Implementar [OBJETIVO] para [PROPÓSITO]",
  "roles": ["role_architect", "role_generator", "role_validator"],
  "workflow": "W7_FOCO_SESION",
  "tags": ["sprint", "generativo"],
  "artifacts_expected": ["tools/<nombre>.py", "state/changes/BAGO-CHG-XXX.json"],
  "decisions_expected": ["Elegir approach para [OBJETIVO]"],
  "checklist": [
    "Revisar bago health antes de empezar",
    "Definir criterio de done antes de codificar",
    "Tests --test al final de cada herramienta"
  ]
}
```

---

## Casos de uso

- **Cuándo usarlo:** Cuando repites el mismo tipo de sesión (sprint, análisis, revisión) y quieres arrancar sin rellenar campos manualmente.
- **Qué produce:** Un `SES-*.json` en `state/sessions/` con campos pre-rellenados listos para editar.
- **Diferencia con `bago session`:** `session` usa `session_opener.py` para abrir una sesión interactiva genérica. `template new` genera el JSON de sesión desde un patrón definido.
- **Integración con `bago check`:** Al usar `template new sprint`, el checklist de la plantilla incluye `bago check` como paso 1.
