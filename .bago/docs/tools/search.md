# bago search — Búsqueda full-text

> Realiza búsqueda de texto completo sobre sesiones y cambios registrados.

## Descripción

`bago search` indexa y busca en el contenido de los archivos SES-*.json y BAGO-CHG-*.json de state/. Permite encontrar sesiones por descripción, decisiones tomadas, artefactos generados o cualquier texto registrado durante el trabajo.

## Uso

```bash
bago search "<término>"        → busca en sesiones y cambios
bago search "<término>" --sessions  → solo en sesiones
bago search "<término>" --changes   → solo en cambios
bago search "<término>" --json      → output JSON con resultados
bago search --test             → valida dependencias y sale con "OK"
```

## Opciones

| Opción | Descripción |
|--------|-------------|
| `"<término>"` | Texto a buscar (soporta múltiples palabras) |
| `--sessions` | Busca solo en SES-*.json |
| `--changes` | Busca solo en BAGO-CHG-*.json |
| `--json` | Output JSON con resultados |
| `--test` | Modo test |

## Ejemplos

```bash
# Buscar todas las sesiones que mencionen "velocity"
bago search "velocity"

# Buscar en cambios sobre "context_detector"
bago search "context_detector" --changes

# Encontrar sesiones donde se tomó una decisión sobre cosecha
bago search "cosecha" --sessions
```

## Casos de uso

- **Cuándo usarlo:** Para recuperar contexto de trabajo anterior sin navegar manualmente los archivos JSON.
- **Qué produce:** Lista de coincidencias con ID, tipo (sesión/cambio) y fragmento del texto encontrado.
- **Integración con otros comandos:** Complementa `bago timeline` (visual) con búsqueda por contenido. Útil antes de `bago session` para recuperar contexto relevante.
