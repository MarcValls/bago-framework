# EVAL-WORKFLOWS-002 — Evaluación de Eficacia de Workflows

**Fecha:** 2026-04-18  
**Sesión:** SES-ON-2026-04-18-004  
**Tipo:** execution (actualización de artefacto existente)  
**Base:** 19 sesiones cerradas (vs 15 en EVAL-001)

---

## Cambios respecto a EVAL-001

| Métrica | EVAL-001 (15 ses) | EVAL-002 (19 ses) | Δ |
|---------|:-----------------:|:-----------------:|:---:|
| Útiles/sesión global | ~3.8 | **4.7** | +0.9 |
| w7_foco_sesion útiles/ses | 3.8 | **3.5** | −0.3 |
| w7_foco_sesion roles/ses | 2.0 | **2.0** | = |
| w0_free_session útiles/ses | 1.0 | **1.0** | = |
| w0_free_session roles/ses | 3.0 | **3.7** | +0.7 |

## Decisiones de esta evaluación

1. El patrón se mantiene: ON produce 2.75 útiles vs OFF 1.0. La brecha no se reduce con más rondas.
2. Los roles en OFF siguen aumentando (R1: 3, R2: 4, R3: 4). Tendencia esperada: sin preflight, la activación de roles es expansiva.
3. `w7_foco_sesion` baja 0.3 útiles/ses desde EVAL-001 porque las rondas del experimento son sesiones más acotadas que las sesiones históricas. No indica deterioro del workflow.
4. La métrica global sube (4.7 vs ~3.8) porque las sesiones ON del experimento siguen siendo productivas.

## Estado del experimento

- Rondas completadas: 3 de 5 (ON: R1, R2, R3 / OFF: R1, R2, R3)
- Veredicto parcial: ON gana en útiles (+1.75), foco (−1.67 roles) y decisiones (+2.75)
- Rondas restantes: R4 (execution) y R5 (system_change libre)
