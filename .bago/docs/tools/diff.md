# bago diff — Delta de state/ vs último snapshot

> Muestra los cambios en state/ desde el último snapshot.

## Descripción

`bago diff` compara el estado actual de `state/` con el último snapshot ZIP disponible en `state/snapshots/`. Muestra qué archivos se añadieron, modificaron o eliminaron desde que se tomó el snapshot. Útil para revisar exactamente qué ha cambiado antes de hacer commit o al volver de una ausencia.

## Uso

```bash
bago diff                      → delta vs último snapshot
bago diff --snapshot SNAP-ID   → delta vs snapshot específico
bago diff --json               → output JSON con listas de archivos por estado
bago diff --test               → valida dependencias y sale con "OK"
```

## Opciones

| Opción | Descripción |
|--------|-------------|
| `--snapshot SNAP-ID` | Compara vs snapshot específico (ver `bago snapshot --list`) |
| `--json` | Output JSON con arrays: added, modified, deleted |
| `--test` | Modo test |

## Ejemplos

```bash
# Ver cambios desde el último snapshot
bago diff

# Comparar contra un snapshot específico
bago diff --snapshot SNAP-20260420_120000

# Ver diff en JSON para scripting
bago diff --json | jq '.modified[]'
```

## Casos de uso

- **Cuándo usarlo:** Antes de hacer commit para revisar qué cambió en state/, después de una sesión larga para entender el alcance de los cambios, o antes de crear un nuevo snapshot.
- **Qué produce:** Lista de archivos con estado (added/modified/deleted) y resumen de cambios.
- **Integración con otros comandos:** Requiere que exista al menos un snapshot de `bago snapshot`. Complementa `bago changelog` que muestra los cambios a nivel semántico.
