# Guía de mantenimiento del pack · BAGO 2.3-clean

> Referencia operativa para mantener el pack sano entre sesiones y al distribuirlo.
> Responde a: ¿qué toco?, ¿cuándo?, ¿qué nunca debo tocar directamente?

---

## 1. Ciclo de vida normal de una sesión

```
[bootstrap]     → W1_COLD_START o repo_context_guard check
[planificación] → ./ideas o make WF
[ejecución]     → W2 / W3 / W4 según el tipo de tarea
[cierre]        → W5_CIERRE_Y_CONTINUIDAD
[validación]    → validate_pack.py → GO
```

Nunca saltar de ejecución a validación sin pasar por cierre (W5). Las sesiones sin cerrar formalmente degradan la métrica de **Protocolo** en el radar de evolución.

---

## 2. Cuándo regenerar TREE.txt y CHECKSUMS.sha256

**Siempre** que se modifique cualquier archivo dentro de `.bago/`, incluyendo:

- Añadir o borrar archivos en `state/`, `docs/`, `roles/`, `core/`, `tools/`
- Modificar `pack.json` o `global_state.json`
- Actualizar `ESTADO_BAGO_ACTUAL.md`

**Comando canónico** (ejecutar desde el directorio padre de `.bago/`):

```bash
cd /ruta/al/proyecto  # directorio que contiene .bago/
python3 -c "
from pathlib import Path
import hashlib
root = Path('.bago')
entries = sorted(
    str(p.relative_to(root)) + ('/' if p.is_dir() else '')
    for p in root.rglob('*')
)
(root/'TREE.txt').write_text('\n'.join(entries)+'\n')
lines = []
for p in sorted(root.rglob('*')):
    if p.is_file() and p.name != 'CHECKSUMS.sha256':
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        lines.append(f'{digest}  {p.relative_to(root)}')
(root/'CHECKSUMS.sha256').write_text('\n'.join(lines)+'\n')
"
python3 .bago/tools/validate_pack.py
```

**Nunca** editar TREE.txt o CHECKSUMS.sha256 a mano. Son artefactos generados.

---

## 3. Ciclo de vida de sesiones, cambios y evidencias

### Sesiones (`state/sessions/`)

| Estado | Significado | Acción de mantenimiento |
|---|---|---|
| `open` | Sesión activa en curso | Cerrar con W5 al terminar el bloque |
| `closed` | Completada formalmente | Solo lectura |
| `completed` | Variante legacy de closed | Migrar a `closed` si se reabre para editar |
| `blocked` | No puede avanzar | Documentar motivo en `summary`; cerrar si no hay acción pendiente |

**Límite recomendado**: no más de 1 sesión en estado `open` simultáneamente.

### Cambios (`state/changes/`)

- Cada cambio debe tener `status: applied` al cerrar la sesión que lo generó.
- No borrar cambios antiguos — forman la historia auditable del sistema.
- Los IDs siguen el patrón `BAGO-CHG-NNN`; el siguiente disponible se calcula con:

```bash
python3 -c "
from pathlib import Path
import re
ids = [int(m.group(1)) for f in Path('.bago/state/changes').glob('BAGO-CHG-???.json')
       if (m := re.search(r'CHG-(\d+)', f.stem))]
print('Siguiente CHG:', f'BAGO-CHG-{max(ids)+1:03d}' if ids else 'BAGO-CHG-001')
"
```

### Evidencias (`state/evidences/`)

- Misma lógica que cambios. IDs `BAGO-EVD-NNN`.
- Deben tener `content` no vacío; una evidencia sin contenido no tiene valor.

---

## 4. Actualizar el inventario declarado

Después de añadir sesiones, cambios o evidencias, actualizar `global_state.json → inventory`:

```bash
python3 -c "
from pathlib import Path
for d in ['sessions','changes','evidences']:
    n = len(list(Path('.bago/state').joinpath(d).glob('*.json')))
    print(d, n)
"
```

Editar manualmente los valores en `global_state.json` para que coincidan. Luego ejecutar `bago sync` y validar.

---

## 5. Qué NO modificar directamente

| Archivo | Por qué |
|---|---|
| `TREE.txt` | Generado; edición manual → CHECKSUMS mismatch inmediato |
| `CHECKSUMS.sha256` | Generado; edición manual → validate_pack KO |
| `pack.json → review_role` | Solo admite `role_vertice`; cambiar rompe validate_state |
| Sesiones en estado `closed` | Cambiar el pasado rompe la trazabilidad de auditoría |
| `core/canon/` | Documentos de referencia canónica; solo Vértice puede modificarlos |

---

## 6. Distribuir una nueva versión del pack

1. Verificar GO pack: `python3 .bago/tools/validate_pack.py`
2. Crear directorio de distribución: `mkdir -p .bago/dist/source/`
3. Empaquetar (excluir archivos volátiles y de desarrollo):

```bash
FECHA=$(date +%Y%m%d_%H%M%S)
VERSION=$(python3 -c "import json; print(json.loads(open('.bago/pack.json').read())['bago_version'].replace(' ','_'))")
zip -r ".bago/dist/source/BAGO_${VERSION}_${FECHA}.zip" .bago/ \
  --exclude "*.pyc" --exclude "*/__pycache__/*" --exclude "*.DS_Store" \
  --exclude ".bago/sandbox/runtime/*" --exclude ".bago/sandbox/runtime-vm/*"
echo "Paquete generado: BAGO_${VERSION}_${FECHA}.zip"
```

4. Regenerar TREE+CHECKSUMS (el nuevo ZIP forma parte del árbol).
5. `validate_pack.py` → GO antes de compartir.

---

## 7. Señales de que el pack necesita mantenimiento

| Señal | Acción |
|---|---|
| `validate_pack` = KO por CHECKSUMS | Ejecutar `bago sync` y commitear |
| `validate_state` = KO por inventario | Recontar y actualizar `global_state.json → inventory` |
| Sesión en `open` desde hace > 24h | Cerrar o marcar como `blocked` con explicación |
| `ESTADO_BAGO_ACTUAL.md` desactualizado (fecha > 7 días) | Actualizar tras la siguiente sesión con W5 |
| `repo_context_guard check` = `mismatch` | Ejecutar `repo_context_guard sync` y luego W1 |
| Radar bago-viewer muestra "Protocolo" < 5/10 | Revisar sesiones no cerradas; usar W5 en las próximas |

---

## 8. Mantenimiento del bago-viewer (CAJAFISICA)

El viewer en `bago-viewer/` es un proyecto independiente. Para mantenerlo:

- Servidor: `cd bago-viewer && python3 app.py < /dev/null` (o `./start.sh`)
- Si el servidor cae con `Bad file descriptor`: lanzar con `< /dev/null` para aislar stdin
- Al modificar templates Flask: reiniciar el servidor (no hay hot-reload en modo producción)
- Al añadir dimensiones al radar: actualizar `compute_evolution()` en `app.py`

---

## 9. Cronograma mínimo recomendado

| Frecuencia | Acción |
|---|---|
| Cada sesión | `repo_context_guard check` + `validate_pack` al inicio y al cierre |
| Cada sprint | Actualizar `ESTADO_BAGO_ACTUAL.md` + regenerar ZIP de distribución |
| Al detectar deriva | Activar `role_vertice` + W3/W4 según gravedad |
| Al distribuir | Auditoría completa con `AUDITORIA_COHERENCIA.md` |
