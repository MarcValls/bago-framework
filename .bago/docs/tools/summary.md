# bago summary — Resumen ejecutivo Markdown

> Genera un resumen ejecutivo Markdown de una sesión o sprint.

## Descripción

`bago summary` produce un resumen ejecutivo conciso en Markdown, orientado a comunicación rápida. A diferencia de `bago review` (informe completo), el summary es breve y centrado en los puntos clave: qué se decidió, qué se produjo, cuál es el estado.

## Uso

```bash
bago summary                   → resumen de la sesión activa o última cerrada
bago summary --sprint ID       → resumen de un sprint específico
bago summary --session ID      → resumen de una sesión específica
bago summary --out FILE        → guarda en archivo
bago summary --json            → output JSON
bago summary --test            → valida dependencias y sale con "OK"
```

## Opciones

| Opción | Descripción |
|--------|-------------|
| `--sprint ID` | Resumen del sprint indicado |
| `--session ID` | Resumen de la sesión indicada |
| `--out FILE` | Guarda el resumen en el archivo |
| `--json` | Output JSON |
| `--test` | Modo test |

## Ejemplos

```bash
# Resumen de la última sesión
bago summary

# Resumen del sprint activo
bago summary --sprint SPRINT-004

# Guardar resumen en archivo
bago summary --sprint SPRINT-004 --out SPRINT-004-SUMMARY.md
```

## Casos de uso

- **Cuándo usarlo:** Al cerrar una sesión o sprint para tener un documento de referencia rápido, para compartir en comunicaciones de equipo, o para incluir en el CHANGELOG.
- **Qué produce:** Markdown de 1-2 páginas con secciones: Resumen, Decisiones, Artefactos, Métricas, Próximos pasos.
- **Integración con otros comandos:** Más compacto que `bago review`. `bago report` para informes con filtros. Los summaries se pueden concatenar para informes de mayor alcance.
