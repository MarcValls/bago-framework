# Plantilla de Auditoría de Coherencia · BAGO 2.4-v2rc

> **Uso**: ejecutar de arriba abajo al inicio de una sesión de auditoría formal
> o antes de empaquetar/distribuir el pack.
> Cada bloque tiene un resultado binario **PASS / FAIL**.
> Un solo FAIL en bloques marcados como `[CRÍTICO]` invalida el pack.

---

## BLOQUE 1 — Integridad del manifiesto `[CRÍTICO]`

```bash
python3 .bago/tools/validate_manifest.py
```

| Verificación | Criterio de PASS |
|---|---|
| `bago_version` en `pack.json` | Coincide con `canon_version` en `global_state.json` |
| `review_role` en `pack.json` | Resuelve a un archivo real en `roles/` |
| Workflows declarados | Todos existen como archivos en `core/workflows/` o `workflows/` |
| Roles declarados | Todos existen en `roles/` |

**Resultado esperado:** `GO manifest`

---

## BLOQUE 2 — Coherencia del estado `[CRÍTICO]`

```bash
python3 .bago/tools/validate_state.py
```

| Verificación | Criterio de PASS |
|---|---|
| `inventory.sessions` declarado | Coincide con `ls state/sessions/*.json | wc -l` |
| `inventory.changes` declarado | Coincide con `ls state/changes/*.json | wc -l` |
| `inventory.evidences` declarado | Coincide con `ls state/evidences/*.json | wc -l` |
| `last_completed_session_id` | El archivo JSON correspondiente existe en `state/sessions/` |
| `last_completed_change_id` | El archivo JSON correspondiente existe en `state/changes/` |
| `last_completed_evidence_id` | El archivo JSON correspondiente existe en `state/evidences/` |
| `working_mode` | Si `external`, `last_completed_task_type` NO es productivo (feature, sprint, bug_fix) |

**Resultado esperado:** `GO state`

---

## BLOQUE 3 — Integridad del árbol y checksums `[CRÍTICO]`

```bash
python3 .bago/tools/validate_pack.py
```

| Verificación | Criterio de PASS |
|---|---|
| `TREE.txt` | Refleja el árbol físico real (sin entradas fantasma) |
| `CHECKSUMS.sha256` | Todos los hashes coinciden con los archivos en disco |
| Resultado combinado | `GO pack` (incluye manifest + state + tree) |

**Si FAIL:** regenerar con el script canónico antes de continuar:
```bash
cd /Users/INTELIA_Manager/Desktop && python3 -c "
from pathlib import Path
import hashlib
root = Path('.bago')
entries = sorted(str(p.relative_to(root)) + ('/' if p.is_dir() else '') for p in root.rglob('*'))
(root/'TREE.txt').write_text('\n'.join(entries)+'\n')
lines = []
for p in sorted(root.rglob('*')):
    if p.is_file() and p.name != 'CHECKSUMS.sha256':
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        lines.append(f'{digest}  {p.relative_to(root)}')
(root/'CHECKSUMS.sha256').write_text('\n'.join(lines)+'\n')
"
```

---

## BLOQUE 4 — Separación de capas de estado

| Verificación | Criterio de PASS |
|---|---|
| `ESTADO_BAGO_ACTUAL.md` | Describe el estado del **pack BAGO**, no el progreso de un proyecto externo |
| `repo_context.json` | Solo contiene puntero al repo externo (`role: external_repo_pointer`) |
| `global_state.json` | Es la fuente canónica; contiene `inventory`, `sprint_status`, `last_validation` |
| Los tres documentos son coherentes entre sí | Misma versión, mismo `last_completed_session_id` |

**Verificación manual:**
```bash
python3 -c "
import json
from pathlib import Path
gs = json.loads(Path('.bago/state/global_state.json').read_text())
rc = json.loads(Path('.bago/state/repo_context.json').read_text())
print('working_mode:', rc.get('previous',{}).get('working_mode','?'))
print('last_session:', gs.get('last_completed_session_id','?'))
print('health:', gs.get('system_health','?'))
print('sprints DONE:', sum(1 for v in gs.get('sprint_status',{}).values() if v=='DONE'))
"
```

---

## BLOQUE 5 — Roles operativos

| Verificación | Criterio de PASS |
|---|---|
| `role_vertice` | Existe en `roles/supervision/VERTICE.md` |
| Aliases deprecados | `GUIA_VERTICE` y `role_structural_reviewer` NO aparecen en `pack.json` ni en código nuevo |
| Roles en sesiones activas | `global_state.json → active_roles` está vacío si no hay sesión abierta |

---

## BLOQUE 6 — Ciclo de vida de artefactos

| Verificación | Criterio de PASS |
|---|---|
| Todas las sesiones tienen `status` | Ninguna queda sin campo `status` |
| No hay sesiones `open` > 7 días | Sesiones abiertas deben cerrarse o documentarse como bloqueadas |
| Cada `BAGO-CHG-*` tiene `status: applied` | No debe haber cambios en estado `draft` o sin status |
| Cada `BAGO-EVD-*` tiene `type` y `content` no vacíos | Evidencias sin contenido son artefactos huérfanos |

**Verificación rápida:**
```bash
python3 -c "
import json
from pathlib import Path
from datetime import datetime, timezone

issues = []
sdir = Path('.bago/state/sessions')
for f in sdir.glob('*.json'):
    s = json.loads(f.read_text())
    if not s.get('status'):
        issues.append(f'SIN STATUS: {f.name}')
    if s.get('status') == 'open':
        created = s.get('created_at','')[:10]
        issues.append(f'ABIERTA: {f.name} desde {created}')

cdir = Path('.bago/state/changes')
for f in cdir.glob('*.json'):
    c = json.loads(f.read_text())
    if c.get('status','') not in ('applied','superseded'):
        issues.append(f'CHG sin cerrar: {f.name} status={c.get(\"status\",\"?\")}')

if issues:
    for i in issues: print('⚠', i)
else:
    print('✓ Todos los artefactos en orden')
"
```

---

## BLOQUE 7 — Sprint status

| Verificación | Criterio de PASS |
|---|---|
| Todos los sprints completados tienen sesión asociada | Verificar que existe al menos una sesión por sprint marcado DONE |
| No hay sprints DONE sin evidencia en `state/` | Cada sprint completado debe tener al menos un CHG asociable |

**Verificación:**
```bash
python3 -c "
import json
from pathlib import Path
gs = json.loads(Path('.bago/state/global_state.json').read_text())
for sprint, status in gs.get('sprint_status', {}).items():
    print(f'{sprint}: {status}')
"
```

---

## BLOQUE 8 — Contexto de repo

```bash
python3 .bago/tools/repo_context_guard.py check
```

| Resultado | Acción |
|---|---|
| `match` | Continuar normalmente |
| `new` o `mismatch` | Ejecutar `W1_COLD_START` antes de cualquier trabajo productivo |

---

## Resultado final de la auditoría

| Bloque | Estado |
|---|---|
| 1. Manifiesto | ⬜ PASS / FAIL |
| 2. Estado | ⬜ PASS / FAIL |
| 3. Árbol/checksums | ⬜ PASS / FAIL |
| 4. Separación capas | ⬜ PASS / FAIL |
| 5. Roles | ⬜ PASS / FAIL |
| 6. Artefactos | ⬜ PASS / FAIL |
| 7. Sprint status | ⬜ PASS / FAIL |
| 8. Contexto repo | ⬜ PASS / FAIL |

**Veredicto:**
- **GO** — todos PASS
- **GO con reservas** — PASS en bloques críticos, FAIL en 6 o 7
- **KO** — cualquier FAIL en bloques 1, 2, 3 o 8
