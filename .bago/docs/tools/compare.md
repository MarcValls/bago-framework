# bago compare — Comparativa lado a lado

> Compara workflows, períodos o roles de forma paralela para identificar diferencias.

## Descripción

`bago compare` genera tablas de comparación lado a lado entre diferentes dimensiones: workflows, períodos de tiempo o roles. Útil para evaluar qué configuración de trabajo produce mejores resultados, o para comparar el rendimiento de distintos períodos.

## Uso

```bash
bago compare --wf WF1 WF2      → compara dos workflows
bago compare --period P1 P2    → compara dos períodos (ej: --period 7 14)
bago compare --rol R1 R2       → compara dos roles
bago compare --json            → output JSON con tablas de comparación
bago compare --test            → valida dependencias y sale con "OK"
```

## Opciones

| Opción | Descripción |
|--------|-------------|
| `--wf WF1 WF2` | Compara dos workflows por métricas |
| `--period P1 P2` | Compara dos períodos en días |
| `--rol R1 R2` | Compara dos roles de trabajo |
| `--json` | Output JSON |
| `--test` | Modo test |

## Ejemplos

```bash
# Comparar workflow W7 vs W0
bago compare --wf w7_foco_sesion w0_free_session

# Comparar últimas 2 semanas vs 2 semanas anteriores
bago compare --period 7 14
```

## Casos de uso

- **Cuándo usarlo:** En retrospectivas para evaluar qué workflow ha sido más efectivo, o para comparar la productividad de dos períodos distintos.
- **Qué produce:** Tabla comparativa con métricas clave: sesiones, artefactos, decisiones, score medio.
- **Integración con otros comandos:** Combina datos de `bago session-stats` y `bago metrics`. Para análisis detallado por sesión usar `bago session-stats --id`.
