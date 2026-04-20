# Troubleshooting BAGO

**Propósito:** Diagnóstico y solución de los errores más frecuentes en el pack.

---

## E1 — `validate_pack.py` responde KO

### Síntoma
```
KO
<mensaje de error>
```

### Diagnóstico por mensaje

| Mensaje | Causa | Solución |
|---------|-------|----------|
| `TREE.txt does not match` | Se añadió/eliminó un archivo sin sincronizar | Ejecutar `bago sync` y commitear (ver sección R) |
| `checksum mismatch for X` | Se modificó un archivo sin sincronizar | Ejecutar `bago sync` |
| `last_completed_task_type does not match` | `global_state.last_completed_task_type` no coincide con el `task_type` de la sesión referenciada | Actualizar `last_completed_task_type` en `global_state.json` |
| `last_completed_workflow does not match` | Igual pero para `selected_workflow` | Actualizar `last_completed_workflow` en `global_state.json` |
| `last_completed_roles does not match` | Roles no coinciden | Actualizar `last_completed_roles` en `global_state.json` |
| `working_mode == external` con task_type productivo | Se usó `system_change`/`bug_fix` etc. en modo externo | No registrar sesiones productivas externas en el pack |
| `inventory mismatch` | Conteo declarado ≠ archivos reales | Reconteo manual y actualizar `inventory` en `global_state.json` |
| `review_role not found` | `review_role` en `pack.json` apunta a un rol inexistente | Verificar que `roles/role_vertice.md` existe |
| `workflow X not registered` | `selected_workflow` en una sesión no está en `pack.json` | Registrar el workflow en `pack.json → workflows` |

### Solución R — regenerar TREE+CHECKSUMS

```bash
python3 bago sync
python3 bago validate
```

---

## E2 — `validate_state.py` KO por `active_workflows`

### Síntoma
```
KO state
active_workflows must be [] when active_session_id is null
```

### Causa
Se cerró la sesión activa pero no se limpió `active_workflows` en `global_state.json`.

### Solución
```bash
python3 -c "
import json
p = '.bago/state/global_state.json'
d = json.loads(open(p).read())
d['active_session_id'] = None
d['active_workflows'] = []
open(p,'w').write(json.dumps(d, indent=2, ensure_ascii=False))
print('Corregido')
"
```

---

## E3 — Inventario desincronizado

### Síntoma
`validate_state.py` reporta `inventory mismatch` o los conteos no cuadran.

### Diagnóstico
```bash
python3 -c "
from pathlib import Path
base = Path('.bago/state')
for d in ['sessions','changes','evidences']:
    real = len(list((base/d).glob('*.json')))
    print(f'{d}: {real} archivos reales')
"
```

Comparar con los valores de `global_state.json → inventory`.

### Solución
```bash
python3 -c "
import json
from pathlib import Path
p = '.bago/state/global_state.json'
d = json.loads(open(p).read())
base = Path('.bago/state')
d['inventory'] = {
    'sessions':  len(list((base/'sessions').glob('*.json'))),
    'changes':   len(list((base/'changes').glob('*.json'))),
    'evidences': len(list((base/'evidences').glob('*.json')))
}
open(p,'w').write(json.dumps(d, indent=2, ensure_ascii=False))
print('Inventario actualizado:', d['inventory'])
"
```

---

## E4 — Workflow no reconocido en sesión

### Síntoma
```
KO state
workflow 'w7_foco_sesion' not registered in pack.json
```

### Causa
El `selected_workflow` de una sesión apunta a un ID que no existe en `pack.json → workflows`.

### Diagnóstico
```bash
python3 -c "
import json
pack = json.loads(open('.bago/pack.json').read())
print('Workflows registrados:', list(pack.get('workflows',{}).keys()))
"
```

### Solución
Registrar el workflow en `pack.json`:
```json
"workflows": {
  "w7_foco_sesion": "workflows/W7_FOCO_SESION.md",
  "w0_free_session": "workflows/W0_FREE_SESSION.md"
}
```

El ID debe coincidir con el bloque `## id` del archivo MD:
```markdown
## id
`w7_foco_sesion`
```

---

## E5 — EVD con `details` vacío

### Síntoma
`validate_state.py` reporta `evidence BAGO-EVD-XXX: details is empty`.

### Causa
El campo `details` existe pero es una cadena vacía `""` o `null`.

### Solución
Editar el JSON de la evidencia y añadir al menos una frase descriptiva real:
```json
"details": "Descripción concreta de lo que se hizo y se verificó."
```

---

## E6 — Session `open` bloqueando validación

### Síntoma
`active_session_id` apunta a una sesión que debería estar cerrada, o hay dos sesiones `open` a la vez.

### Diagnóstico
```bash
python3 -c "
import json
from pathlib import Path
for p in Path('.bago/state/sessions').glob('*.json'):
    d = json.loads(p.read_text())
    if d.get('status') != 'closed':
        print(p.name, '→', d.get('status','?'))
"
```

### Solución
Cerrar la sesión huérfana actualizando su `status` a `"closed"` y limpiar `global_state.active_session_id`.

---

## E7 — Agente de rol deprecado

### Síntoma
Un archivo de sesión referencia `GUIA_VERTICE` o `role_structural_reviewer`.

### Causa
Aliases deprecados. El identificador canónico es `role_vertice`.

### Solución
Reemplazar en el JSON de la sesión:
```
"GUIA_VERTICE" → "role_vertice"
"role_structural_reviewer" → "role_vertice"
```

---

## Referencia rápida de archivos clave

| Archivo | Propósito |
|---------|-----------|
| `state/global_state.json` | Estado canónico. Fuente de verdad para last_completed e inventory |
| `pack.json` | Workflows y roles válidos |
| `TREE.txt` | Árbol de archivos esperado |
| `CHECKSUMS.sha256` | Hashes esperados |
| `tools/validate_pack.py` | Validación completa (manifest + state + TREE/checksums) |
| `tools/validate_state.py` | Solo validación de estado |
| `tools/validate_manifest.py` | Solo validación de manifest/pack.json |
