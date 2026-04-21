# bago tags — Etiquetado con índice y búsqueda

> Gestiona etiquetas sobre sesiones y cambios con índice y búsqueda rápida.

## Descripción

`bago tags` permite añadir etiquetas a sesiones y cambios para organizarlos por tema o categoría. Mantiene un índice de tags en state/ para búsquedas rápidas. Útil para agrupar trabajo por área funcional, cliente o tipo de actividad.

## Uso

```bash
bago tags                      → lista todos los tags y frecuencia
bago tags add <ID> <tag>       → añade tag a sesión o cambio
bago tags search <tag>         → busca sesiones/cambios con ese tag
bago tags remove <ID> <tag>    → elimina tag de un elemento
bago tags --json               → output JSON del índice de tags
bago tags --test               → valida dependencias y sale con "OK"
```

## Opciones

| Opción | Descripción |
|--------|-------------|
| `add <ID> <tag>` | Añade un tag al elemento indicado |
| `search <tag>` | Lista elementos con el tag indicado |
| `remove <ID> <tag>` | Elimina un tag del elemento |
| `--json` | Output JSON del índice completo |
| `--test` | Modo test |

## Ejemplos

```bash
# Ver todos los tags usados
bago tags

# Etiquetar una sesión
bago tags add SES-SPRINT-2026-04-22-001 sprint180

# Buscar todo lo relacionado con "github"
bago tags search github

# Ver tags en JSON
bago tags --json
```

## Casos de uso

- **Cuándo usarlo:** Para organizar el trabajo por temas transversales que no se capturan en los workflows, o para facilitar la búsqueda de sesiones relacionadas.
- **Qué produce:** Actualiza metadatos de SES-*.json o BAGO-CHG-*.json con el campo `tags`. Mantiene un índice de tags en state/.
- **Integración con otros comandos:** Complementa `bago search` (búsqueda por texto). Los tags se pueden usar como filtros en `bago report`.
