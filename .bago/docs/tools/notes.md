# bago notes — Notas ligeras por sesión

> Añade, lista, muestra y elimina notas vinculadas a sesiones o sprints. Almacenadas en `state/notes/NOTE-*.json`.

---

## Descripción

`bago notes` es un sistema de notas rápidas que permite capturar observaciones, recordatorios o ideas durante una sesión sin necesidad de abrir un editor. Cada nota queda vinculada opcionalmente a una sesión (`SES-*`) o sprint (`SPRINT-*`), y puede buscarse después por texto libre.

Las notas **no son decisiones ni artefactos**: son apuntes ligeros de trabajo. Para capturar decisiones importantes, usa el protocolo de sesión o `bago cosecha`.

---

## Uso

```bash
bago notes add "texto"                        → nueva nota (sin vínculo)
bago notes add "texto" --session SES-X        → nota ligada a sesión
bago notes add "texto" --sprint SPRINT-004    → nota ligada a sprint
bago notes list                               → listar todas las notas
bago notes list --session SES-X              → notas de una sesión
bago notes show NOTE-001                     → ver nota completa
bago notes delete NOTE-001                   → borrar nota
bago notes search <término>                  → buscar en contenido de notas
bago notes --test                            → ejecutar tests integrados
```

---

## Opciones

| Opción | Descripción |
|--------|-------------|
| `add <texto>` | Crea una nueva nota con el texto indicado |
| `--session SES-X` | Vincula la nota a una sesión específica |
| `--sprint SPRINT-X` | Vincula la nota a un sprint específico |
| `list` | Lista todas las notas pendientes |
| `list --session SES-X` | Filtra notas por sesión |
| `show NOTE-XXX` | Muestra el contenido completo de una nota |
| `delete NOTE-XXX` | Elimina una nota por su ID |
| `search <término>` | Búsqueda de texto en el contenido de notas |
| `--test` | Ejecuta los tests integrados de la herramienta |

---

## Ejemplos

```bash
# Añadir una nota durante la sesión actual
bago notes add "Revisar que patch legacy-status no afecte sesiones en curso"

# Vincular a un sprint específico
bago notes add "Pendiente: actualizar ARCHITECTURE.md con el pipeline scan→gh" --sprint SPRINT-004

# Listar todas las notas
bago notes list

# Buscar notas que mencionen 'pipeline'
bago notes search pipeline

# Ver una nota concreta
bago notes show NOTE-003

# Eliminar nota ya resuelta
bago notes delete NOTE-003
```

---

## Formato de datos

Las notas se guardan como JSON en `.bago/state/notes/NOTE-NNN.json`:

```json
{
  "id": "NOTE-001",
  "text": "Revisar que patch legacy-status no afecte sesiones en curso",
  "session_ref": "SES-SPRINT-2026-04-22-001",
  "sprint_ref": null,
  "created_at": "2026-04-22T10:15:00",
  "deleted": false
}
```

---

## Casos de uso

- **Cuándo usarlo:** Cuando tienes un apunte rápido que no quieres perder durante una sesión, pero que no justifica abrir una decisión formal.
- **Qué produce:** `NOTE-NNN.json` en `state/notes/`.
- **Diferencia con `bago remind`:** `remind` tiene `due_date` y gestión de pendientes. `notes` es un cuaderno de notas sin gestión de estados.
- **Integración:** Las notas vinculadas a una sesión aparecen al ejecutar `bago session-stats` para esa sesión.
