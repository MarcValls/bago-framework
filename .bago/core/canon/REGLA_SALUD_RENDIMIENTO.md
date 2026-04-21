# REGLA CANÓNICA: Salud del Código como Activo Comercial
**ID:** BAGO-RULE-CDTR-001  
**Versión:** 1.0.0  
**Tipo:** Gobernanza técnica permanente  
**Fecha de vigencia:** 2026-04-21  
**Precedencia:** Canon nivel 2 (después de CANON.md, antes de workflows)

---

## Principio

> La salud del código no es una métrica técnica interna.  
> Es un multiplicador de la velocidad de entrega, un generador de deuda financiera  
> y una fuente de riesgo comercial cuantificable.  
> **Tratarla como dato de ingeniería y no como dato de negocio es una decisión reckless.**

---

## Definiciones operativas

| Concepto | Definición BAGO |
|----------|----------------|
| **Health score** | Puntuación 0–100 que refleja la condición técnica del sistema |
| **Velocity multiplier** | Factor `(health/100)^0.6` que pondera la capacidad de entrega |
| **Deuda activa** | Horas estimadas para liquidar todos los hallazgos actuales |
| **Arrastre comercial** | €/trimestre = coste deuda + waste hotspot + riesgo seguridad/4 |

---

## Condiciones de activación (enforcement)

### NIVEL 1 — Bloqueo en validate (KO)
El sistema **no puede declararse GO** si:
- Existen hallazgos de seguridad `severity=critical` sin plan de resolución documentado
  (`state/findings/ACK-*.json` con fecha < 7 días)
- El health score ha caído **>20 puntos** en los últimos 3 sprints sin CHG registrado

### NIVEL 2 — GO con reservas (GO_WITH_RESERVATIONS)
El sistema **debe declarar reservas** si:
- `health_score < 70` y no existe sprint activo con objetivo de mejora
- `total_quarterly_drag > €5000` sin plan de paydown en el sprint activo
- `riesgo_seguridad = ALTO o CRÍTICO` sin evidencia de triage activo

### NIVEL 3 — Advisory (solo aviso)
El sistema **recomienda acción** si:
- Deuda técnica crece entre scans consecutivos
- Top hotspot score > 50 sin cambios en >30 días
- Porcentaje de autofixables no aplicados > 80%

---

## Obligaciones del equipo

1. **Por sesión:** `bago impact` debe ejecutarse al inicio de cualquier sesión de trabajo  
2. **Por sprint:** El arrastre comercial debe registrarse como métrica en el CHG de cierre  
3. **Por trimestre:** El plan de paydown de deuda debe documentarse en un sprint dedicado  
4. **Ante incidente:** Todo hallazgo `severity=critical` genera automáticamente evidencia en `state/evidences/`

---

## Métricas de cumplimiento

La regla se considera cumplida si:
- `health_score >= 70` O existe sprint activo con goal de mejora
- `total_quarterly_drag < €10000` O existe plan documentado
- Ningún hallazgo crítico de seguridad sin acknowledge > 7 días

---

## Fundamento

Esta regla incorpora la evidencia de DORA Research (2023), McKinsey Developer Productivity  
y el modelo FAIR para cuantificación de riesgo. El multiplicador de velocidad y el modelo  
de pérdida esperada están implementados en `tools/impact_engine.py`.

---

## Verificación

```bash
bago impact          # arrastre comercial actual
bago risk            # matriz de riesgo oculto
bago debt            # ledger de deuda con cuadrantes
bago validate        # enforcement automático de esta regla
```

---

*Esta regla es permanente. Solo puede modificarse con CHG de tipo `governance` y severidad `major`  
con decisión humana explícita documentada.*
