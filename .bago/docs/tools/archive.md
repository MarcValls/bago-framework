# bago archive — Archivado de sesiones antiguas

> Archiva sesiones cerradas con más de 30 días en state/sessions/archive/.

## Descripción

`bago archive` gestiona el archivado de sesiones de trabajo que ya están cerradas y llevan más de 30 días sin modificarse. Las sesiones archivadas se mueven a `state/sessions/archive/` para mantener el directorio principal limpio sin perder historial. Las sesiones archivadas pueden restaurarse en cualquier momento.

## Uso

```bash
bago archive list              → lista sesiones candidatas a archivar (closed, >30 días)
bago archive run               → archiva candidatas (pide confirmación)
bago archive run --days N      → candidatas con más de N días
bago archive run --yes         → archiva sin pedir confirmación
bago archive run --days N --yes → archiva N días o más, sin confirmación
bago archive restore <SES-ID>  → restaura una sesión archivada
bago archive --test            → valida dependencias y sale con "OK"
```

## Opciones

| Opción | Descripción |
|--------|-------------|
| `list` | Lista candidatas a archivar |
| `run` | Ejecuta el archivado (interactivo por defecto) |
| `--days N` | Umbral de días para considerar archivable (default: 30) |
| `--yes` | Confirma automáticamente sin preguntar |
| `restore <ID>` | Mueve la sesión de archive/ de vuelta a sessions/ |
| `--test` | Modo test |

## Ejemplos

```bash
# Ver qué sesiones serían archivadas
bago archive list

# Archivar con confirmación interactiva
bago archive run

# Archivar sesiones de más de 60 días sin confirmación
bago archive run --days 60 --yes

# Restaurar una sesión archivada
bago archive restore SES-SPRINT-2026-03-10-001
```

## Casos de uso

- **Cuándo usarlo:** Cuando `bago stats` o `bago metrics` empieza a mostrar muchas sesiones antiguas que ensucian el análisis, o cuando el directorio sessions/ tiene más de 50 archivos.
- **Qué produce:** Mueve archivos SES-*.json de `state/sessions/` a `state/sessions/archive/`. No borra nada.
- **Integración con otros comandos:** Después de archivar, `bago health` y `bago insights` operan con el conjunto activo más limpio. `bago snapshot` captura también el contenido de archive/.
