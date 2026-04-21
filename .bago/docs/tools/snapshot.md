# bago snapshot — Snapshot point-in-time

> Crea un archivo ZIP con una copia point-in-time del directorio state/.

## Descripción

`bago snapshot` genera un archivo ZIP del directorio `state/` completo, guardado como `SNAP-YYYYMMDD_HHMMSS.zip` en `state/snapshots/`. Permite recuperar el estado exacto del pack en un momento determinado. Los snapshots son la base para `bago diff`.

## Uso

```bash
bago snapshot                  → crea snapshot del state/ actual
bago snapshot --list           → lista snapshots existentes
bago snapshot --test           → valida dependencias y sale con "OK"
```

## Opciones

| Opción | Descripción |
|--------|-------------|
| `--list` | Lista snapshots existentes con fecha y tamaño |
| `--test` | Modo test |

## Ejemplos

```bash
# Crear snapshot antes de un cambio importante
bago snapshot

# Ver snapshots disponibles
bago snapshot --list
```

## Casos de uso

- **Cuándo usarlo:** Antes de operaciones que modifiquen state/ (como `bago patch --apply` o `bago archive run`), antes de migrar a una nueva versión, o al final de cada sprint.
- **Qué produce:** Archivo ZIP en `state/snapshots/SNAP-YYYYMMDD_HHMMSS.zip` con todos los archivos JSON y Markdown de state/.
- **Integración con otros comandos:** `bago diff` compara el estado actual con el último snapshot. `bago check` verifica que existe un snapshot reciente (< 7 días).
