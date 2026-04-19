# Instrucciones para Copilot en BAGO

## Idioma

Toda comunicación con el usuario (respuestas, resúmenes, confirmaciones, mensajes de tarea completada) debe estar en **español**.

---

## Regla 0: determinar el contexto ANTES de actuar

Al arrancar cualquier sesión, lo primero es identificar sobre qué se está trabajando:

| Modo | Señal | Qué significa |
|------|-------|---------------|
| **`self`** | CWD es `.bago/` o el usuario pide cambiar el sistema BAGO | Se trabaja sobre el pack BAGO mismo |
| **`external`** | CWD es un proyecto con `.bago/` instalado (ej. TPV Contabilidad) | Se usa BAGO como herramienta sobre ese proyecto |

**Si el contexto no es evidente, preguntar al usuario antes de ejecutar nada.**

Ejemplo de pregunta: *"¿Trabajamos sobre el sistema BAGO en sí, o sobre [nombre del proyecto]?"*

### Separación estricta de contextos

Los dos modos **nunca se mezclan**:

- En modo `self`: el estado, cambios y evidencias van a `.bago/state/` del pack.
- En modo `external`: el estado del proyecto externo va a su propio espacio; el pack BAGO **no registra progreso del proyecto externo** en `global_state.json` ni en `ESTADO_BAGO_ACTUAL.md`.

`ESTADO_BAGO_ACTUAL.md` describe siempre el estado del pack BAGO, **nunca** el progreso de un proyecto externo.

### Detección de señales de evolución

Si durante trabajo `external` el agente detecta que BAGO necesita una mejora (un workflow que no existe, un validador que falla, una herramienta que falta), **sugerir explícitamente**:

> "Esto requiere un cambio en el sistema BAGO. ¿Quieres que cambiemos al modo `self` para implementarlo antes de continuar con [proyecto]?"

No implementar mejoras del pack mientras se está en modo `external`.

---

## Arquitectura del pack

`.bago/` es un sistema operativo de trabajo técnico autónomo.

| Capa | Archivos clave | Propósito |
|------|---------------|-----------|
| Manifiesto | `pack.json` | Declaración del pack, versión, roles activos |
| Estado canónico | `state/global_state.json` | Inventario, sesión activa, última validación |
| Snapshot legible | `state/ESTADO_BAGO_ACTUAL.md` | Estado del pack BAGO, no del repo externo |
| Contexto de repo | `state/repo_context.json` | Puntero al último repo externo intervenido |
| Validadores | `tools/validate_manifest.py`, `tools/validate_state.py`, `tools/validate_pack.py` | Integridad del pack |
| Árbol/checksums | `TREE.txt`, `CHECKSUMS.sha256` | Comparados por `validate_pack.py` |

---

## Bootstrap obligatorio

El bootstrap depende del modo detectado en Regla 0:

**Modo `self` (trabajando sobre el pack BAGO):**

Leer en orden desde dentro de `.bago/`:
1. `pack.json`
2. `core/00_CEREBRO_BAGO.md`
3. `state/global_state.json`
4. Ejecutar `python3 tools/repo_context_guard.py check`
5. `state/ESTADO_BAGO_ACTUAL.md`

**Modo `external` (usando BAGO en un proyecto externo):**

Leer en orden desde la raíz del proyecto:
1. `.bago/pack.json`
2. `.bago/core/00_CEREBRO_BAGO.md`
3. `.bago/state/global_state.json`
4. Ejecutar `python3 .bago/tools/repo_context_guard.py check`
5. Si el guard devuelve `new` o `mismatch`, ejecutar W1 (`workflow_bootstrap_repo_first`) antes de cualquier otro workflow y tratar `ESTADO_BAGO_ACTUAL` previo como histórico.
6. Leer contexto del proyecto externo (README, estructura, estado propio).

---

## Regla crítica: TREE.txt y CHECKSUMS.sha256

**Solo aplica en modo `self`.** Cualquier cambio a ficheros dentro de `.bago/` debe terminar con:

```bash
cd /Users/INTELIA_Manager/Desktop
python3 -c "
from pathlib import Path, hashlib as hl
import hashlib

root = Path('.bago')
entries = sorted(
    str(p.relative_to(root)) + ('/' if p.is_dir() else '')
    for p in root.rglob('*')
)
(root / 'TREE.txt').write_text('\n'.join(entries) + '\n')

lines = []
for p in sorted(root.rglob('*')):
    if p.is_file() and p.name != 'CHECKSUMS.sha256':
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        lines.append(f'{digest}  {p.relative_to(root)}')
(root / 'CHECKSUMS.sha256').write_text('\n'.join(lines) + '\n')
"
python3 .bago/tools/validate_pack.py
```

`validate_pack.py` compara TREE.txt y CHECKSUMS.sha256 contra el árbol real. Si no se regeneran, el resultado es **KO pack** aunque el resto del estado sea correcto.

---

## Inventario en global_state.json

**Solo aplica en modo `self`.** Al crear cualquier archivo `.json` en estas carpetas, **incrementar el contador correspondiente** en `state/global_state.json → inventory`:

| Carpeta | Campo |
|---------|-------|
| `state/sessions/*.json` | `inventory.sessions` |
| `state/changes/*.json` | `inventory.changes` |
| `state/evidences/*.json` | `inventory.evidences` |

El conteo incluye los archivos `*-MIG-*.json`. Verificar siempre con:

```bash
python3 -c "
from pathlib import Path
for d in ['sessions','changes','evidences']:
    n = len(list(Path('.bago/state').joinpath(d).glob('*.json')))
    print(d, n)
"
```

---

## Identidad del rol Vértice

El único identificador canónico es **`role_vertice`**.

- `GUIA_VERTICE` → alias deprecado (no usar en código nuevo)
- `role_structural_reviewer` → alias deprecado (no usar en código nuevo)

`pack.json → review_role` debe ser `"role_vertice"`. `validate_state.py` verifica que `review_role` resuelva a un rol real en `roles/`.

---

## Modo de trabajo: self vs. external

`tools/repo_context_guard.py` calcula `working_mode` automáticamente:

- **`self`**: `repo_root == ROOT` (el directorio padre de `.bago/` no es un proyecto git distinto)
- **`external`**: `repo_root != ROOT` (`.bago/` está instalado dentro de otro proyecto)

`validate_state.py` bloquea (KO) si `working_mode == "external"` y `last_completed_task_type` es productivo (`feature_implementation`, `bug_fix`, `hotfix`, `sprint`, `feature_sprint`). Esto evita que sesiones del proyecto externo contaminen el estado del pack.

---

## Flujo de trabajo post-bootstrap

Tras confirmar W1/bootstrap como completado, **no re-proponer W1**. Avanzar al objetivo de trabajo con:

```bash
./ideas          # lista ideas priorizadas (bloquea si validate_pack falla)
./ideas --detail N   # amplía descripción de la idea N
./ideas --accept N   # genera handoff W2 para la idea N
make workflow-tactical NAME=W2
```

---

## Validación

Ejecutar después de cualquier cambio estructural:

```bash
python3 .bago/tools/validate_manifest.py   # GO manifest
python3 .bago/tools/validate_state.py      # GO state
python3 .bago/tools/validate_pack.py       # GO pack (incluye los dos anteriores + TREE/CHECKSUMS)
```

Los tres deben retornar GO antes de cerrar una sesión o cambio.
