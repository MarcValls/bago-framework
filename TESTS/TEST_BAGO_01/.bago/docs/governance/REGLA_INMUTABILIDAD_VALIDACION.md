# REGLA DE INMUTABILIDAD EN VALIDACIÓN

**Versión**: 1.0  
**Ámbito**: BAGO Framework — herramientas CLI  
**Estado**: ACTIVO

---

## La regla

> **Validar nunca modifica. Sincronizar nunca valida por debajo salvo lectura.**

---

## Contratos por familia de comando

| Prefijo / nombre | Puede leer | Puede escribir | Ejemplos |
|-----------------|:----------:|:--------------:|---------|
| `validate_*`    | ✅ | ❌ | `validate_pack.py`, `validate_manifest.py`, `validate_state.py` |
| `check_*`       | ✅ | ❌ | `check_validate_purity.py` |
| `report_*` / diagnóstico | ✅ | ❌ | `health_score.py`, `audit_v2.py`, `stale_detector.py` |
| `sync_*`        | ✅ | ✅ metadatos derivados | `sync_pack_metadata.py` |
| `fix_*`         | ✅ | ✅ estado o estructura | — (futuros) |
| `cosecha`, `session`, `task --done` | ✅ | ✅ explícito | artefactos de sesión |

**Regla de naming**: si un comando escribe en disco, su nombre debe anunciarlo.  
Un comando llamado `validate_*`, `check_*`, `health_*`, `audit_*` o `stale_*`
**nunca** debe dejar diff en el repositorio.

---

## Archivos canónicos (no los genera ningún comando)

Estos archivos son fuente de verdad y se editan manualmente o vía PR:

- `pack.json`
- `AGENT_START.md`
- `state/global_state.json`
- `state/ESTADO_BAGO_ACTUAL.md`
- `core/00_CEREBRO_BAGO.md`

---

## Artefactos generados (producidos por `sync_*`)

Estos archivos **no se editan manualmente**. Se regeneran con `bago sync`:

- `TREE.txt`
- `CHECKSUMS.sha256` *(excluye `state/repo_context.json` — archivo volátil de runtime)*

El archivo `state/repo_context.json` es generado por el launcher en cada invocación y
se excluye de `CHECKSUMS.sha256` por ser volátil.

---

## Cómo se hace cumplir

### 1. Test estático (CI — job: `validate-purity-static`)

```
python3 .bago/tools/check_validate_purity.py
```

Escanea todos los `tools/validate_*.py` buscando llamadas de escritura
(`write_text`, `write_bytes`, `json.dump`, `open` en modo escritura, `unlink`, `mkdir`, `shutil`).
Sale con código 1 si encuentra alguna. **Bloquea el merge si falla.**

### 2. Test de no side-effects (CI — job: `no-side-effects`)

```bash
python3 bago validate
python3 bago health
python3 bago audit
git diff --exit-code -- ':(exclude).bago/state/'
```

Si cualquier comando de lectura deja diff en archivos fuente, el PR no puede mergearse.

### 3. Test de metadatos sincronizados (CI — job: `metadata-in-sync`)

```bash
python3 bago sync
git diff --exit-code .bago/TREE.txt .bago/CHECKSUMS.sha256
```

Fuerza al desarrollador a ejecutar `bago sync` y commitear el resultado
antes de que el PR pueda mergearse.

> **Nota de activación**: el workflow completo está en `.github/workflows/validation-purity.yml`.
> Requiere un PAT con scope `workflow` para publicarse en GitHub Actions.
> Mientras tanto, ejecutar los 3 tests manualmente antes de cada PR.

---

## Flujo de trabajo correcto para un PR

```
1. Hacer cambios en el código
2. python3 bago sync          ← regenerar metadatos derivados
3. git add .bago/TREE.txt .bago/CHECKSUMS.sha256
4. python3 bago validate      ← verificar sin efectos laterales
5. python3 bago audit         ← diagnóstico completo sin efectos laterales
6. git commit && git push
```

CI verifica automáticamente los pasos 2, 4 y 5.

---

## Violaciones conocidas (históricas, ya corregidas)

| Archivo | Problema | Corrección |
|---------|----------|-----------|
| `validate_pack.py` (pre-PR#15) | Regeneraba `TREE.txt` y `CHECKSUMS.sha256` | Extraído a `sync_pack_metadata.py` (PR#15) |
| `audit_v2.py` (pre-PR#15) | Llamaba `sync_pack_metadata` internamente | Eliminado — audit es lectura pura (PR#17) |
