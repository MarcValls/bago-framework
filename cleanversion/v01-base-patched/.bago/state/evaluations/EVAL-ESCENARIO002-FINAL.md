# EVAL-ESCENARIO002-FINAL — Veredicto Final ESCENARIO-002

**Fecha:** 2026-04-18  
**Sesión:** SES-ON-2026-04-18-005 (Ronda 5 ON)  
**Experimento:** `.bago/on` vs `.bago/off` — 5 rondas (completadas)

---

## Resultados por ronda

| Ronda | Tipo | ON útiles | ON roles | OFF útiles | OFF roles |
|-------|------|:---------:|:--------:|:----------:|:---------:|
| 1 | system_change | 2 | 2 | 1 | 3 |
| 2 | analysis | 3 | 2 | 1 | 4 |
| 3 | system_change (docs) | 3 | 2 | 1 | 4 |
| 4 | execution | 3 | 2 | 1 | 4 |
| 5 | system_change libre | 4 | 2 | 1 | 4 |

---

## Métricas finales

| Grupo | N | Útiles/ses | Roles/ses | Decisiones/ses |
|-------|:---:|:---:|:---:|:---:|
| `.bago/ON` | 5 | **3.0** | **2.0** | **3.0** |
| `.bago/OFF` | 5 | 1.0 | 3.8 | 0.0 |
| **Δ** | — | **+2.0** | **−1.8** | **+3.0** |

---

## Veredicto

**`.bago/ON` gana el ESCENARIO-002 con diferencia clara.**

- Criterio de victoria: Δ útiles > 0.5 → **cumplido (Δ = 2.0)**
- Criterio de foco: Δ roles < 0 → **cumplido (−1.8)**
- Las sesiones OFF producen exactamente 1 útil en todas las rondas sin excepción.
- Las sesiones OFF no generan ninguna decisión documentada en ninguna ronda.
- Los roles en OFF se estabilizan en 4 (vs 2 en ON) — la activación por inercia es un patrón robusto.

---

## Interpretación

El protocolo W7 añade valor real:

1. **El preflight filtra objetivos vagos.** Las sesiones OFF trabajan sin objetivo concreto → producen notas genéricas.
2. **Declarar artefactos planificados fuerza concreción.** ON sabe qué va a crear antes de empezar.
3. **Limitar roles a ≤2 elimina dispersión.** 4 roles sin protocolo generan 4 perspectivas sin integrar.
4. **Sin protocolo, las decisiones no se documentan.** 0 decisiones en 5 sesiones OFF → el conocimiento se pierde.

---

## ¿El protocolo añade burocracia sin valor?

No. El overhead (preflight + JSON de sesión + CHG/EVD) tarda ~5 min y produce:
- +2.0 útiles por sesión
- +3.0 decisiones documentadas por sesión
- Integridad del pack verificable en todo momento

---

## Recomendaciones post-experimento

1. **Mantener W7 como workflow estándar.** La brecha es suficientemente grande para justificarlo.
2. **Reducir burocracia del cierre** (el overhead más costoso). Objetivo: ≤3 min de cierre con el PROTOCOLO_CIERRE_SESION.md.
3. **Revisar W7 para sesiones de exploration** — para sesiones sin objetivo previo, crear un W7-lite con preflight simplificado en lugar de usar W0.
4. **ESCENARIO-001** sigue activo: completar SES-4 y SES-5 para medir impacto de las plantillas.
