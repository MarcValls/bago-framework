# bago velocity — Métricas de velocidad

> Calcula la velocidad de trabajo por período con sparklines y proyección de fin de mes.

## Descripción

`bago velocity` analiza el ritmo de trabajo midiendo sesiones, artefactos y decisiones producidas por día. Permite comparar la semana actual con la anterior, calcular velocidades en ventanas rolling, y proyectar la producción esperada a fin de mes. Útil para detectar pérdida de ritmo o confirmar aceleración.

## Uso

```bash
bago velocity                  → velocidad última semana vs semana anterior
bago velocity --period N       → últimos N días (default: 7)
bago velocity --rolling        → velocidad en ventanas rolling de 7 días
bago velocity --json           → output JSON con todas las métricas
bago velocity --test           → valida dependencias y sale con "OK"
```

## Opciones

| Opción | Descripción |
|--------|-------------|
| `--period N` | Período en días (default 7) |
| `--rolling` | Muestra velocidad en ventanas rolling de 7 días |
| `--json` | Output JSON con métricas de velocidad |
| `--test` | Modo test |

## Métricas calculadas

| Métrica | Descripción |
|---------|-------------|
| `sessions/day` | Sesiones de trabajo por día |
| `artifacts/day` | Artefactos producidos por día |
| `decisions/day` | Decisiones registradas por día |
| `arts/session` | Artefactos promedio por sesión |
| `decs/session` | Decisiones promedio por sesión |
| Proyección | Estimación de producción a fin de mes al ritmo actual |

## Ejemplos

```bash
# Velocidad semanal estándar
bago velocity

# Velocidad en los últimos 14 días
bago velocity --period 14

# Análisis rolling para detectar tendencias
bago velocity --rolling

# Exportar métricas para tracking externo
bago velocity --json | jq '.current_period'
```

## Casos de uso

- **Cuándo usarlo:** Al inicio de sprint para fijar baseline, en retrospectiva para comparar con sprints anteriores, o cuando se percibe bajada de productividad.
- **Qué produce:** Tabla con métricas del período actual vs anterior, sparkline de tendencia, y proyección a fin de mes.
- **Integración con otros comandos:** Combinar con `bago habit` para correlacionar hábitos con velocidad. `bago metrics` ofrece métricas más generales; `bago velocity` se enfoca en ritmo de producción.
