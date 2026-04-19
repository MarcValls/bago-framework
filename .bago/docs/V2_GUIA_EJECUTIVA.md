# BAGO V2 — Guía Ejecutiva

> Versión: V2.0 | Fecha: 2026-04-18  
> Audiencia: Alguien que no conoce BAGO

---

## ¿Qué es BAGO V2?

**BAGO es el sistema operativo de trabajo técnico para programación y generación compleja.**

No es una metodología de gestión de proyectos ni un framework de desarrollo. Es la capa de gobierno que hace que el trabajo técnico avanzado — el que requiere contexto acumulado, decisiones en cadena y múltiples artefactos — sea **reproducible, auditable y medible**.

BAGO V2 es la versión estabilizada: un sistema adaptativo con gobierno de runtime, reporting vivo y métricas de salud integradas.

---

## ¿Qué resuelve?

### El problema que resuelve

El trabajo técnico complejo tiene un problema estructural: el **contexto se pierde entre sesiones**. Cada vez que se abre una nueva sesión de trabajo, el sistema operativo (el modelo o el desarrollador) no sabe qué se decidió antes, por qué se tomaron esas decisiones, qué está en marcha, qué está bloqueado.

El resultado son tres pérdidas reales:
1. **Pérdida de decisiones**: se retoman debates ya resueltos
2. **Pérdida de estado**: no se sabe qué hay que hacer ni en qué punto se está
3. **Pérdida de trazabilidad**: no se puede auditar por qué el sistema está como está

### La solución BAGO

BAGO formaliza el ciclo de trabajo técnico en tres capas:

| Capa | Qué registra | Cómo |
|---|---|---|
| **Sesiones** | Qué se hizo, con qué workflow, qué roles | JSON en `state/sessions/` |
| **Cambios (CHG)** | Qué cambió estructuralmente y por qué | JSON en `state/changes/` |
| **Evidencias (EVD)** | Qué se decidió, validó o midió | JSON en `state/evidences/` |

Esto hace que **cada sesión arranque con contexto completo** y cada cierre deje el sistema en estado auditable.

---

## Cómo se opera (3 pasos)

### Paso 1: Bootstrap

Al inicio de cada sesión, BAGO carga el estado:

```bash
./bago          # muestra banner con estado actual
./bago audit    # auditoría completa en < 30 segundos
```

Esto responde: ¿Qué está activo? ¿Está el pack sano? ¿Qué workflow es el adecuado?

### Paso 2: Trabajo en workflow

Se elige el workflow apropiado para el trabajo del día y se ejecuta dentro de ese marco:

- **W7** si hay una tarea técnica definida
- **W8** si hay que explorar o investigar  
- **W9** si hay contexto acumulado que formalizar
- **W0** si es una sesión libre
- **WSC** si se está modificando BAGO mismo

El workflow no es un proceso rígido — es un **contrato de atención**: qué artefactos se esperan, qué roles se activan, qué criterio de done aplica.

### Paso 3: Cierre

Al cerrar la sesión se registran:
- 1 CHG (qué cambió)
- 1 EVD (qué se decidió o midió)
- Estado actualizado en global_state.json

Y se valida:
```bash
./bago validate   # GO pack
./bago stale      # sin contradicciones
```

---

## Cómo se mide

### Health Score (0-100)

BAGO V2 tiene un score de salud calculado automáticamente:

```bash
./bago health

# Salida:
BAGO Health Score: 87/100  🟢
  Integridad:          25/25 ✅
  Disciplina workflow: 18/20 ✅
  Captura decisiones:  16/20 ✅
  Estado stale:        15/15 ✅
  Consistencia inv.:   13/20 ⚠️
```

| Score | Semáforo | Interpretación |
|---|---|---|
| 80-100 | 🟢 | Sistema sano y operativo |
| 50-79 | 🟡 | Señales de atención, revisar dimensiones bajas |
| < 50 | 🔴 | Problemas que requieren corrección antes de continuar |

### Auditoría en < 5 minutos

```bash
./bago audit
```

Produce un reporte de 6 dimensiones con veredicto GO/WATCH/KO. Es el comando de referencia para evaluar el estado del sistema antes de una sesión importante o para reportar salud a un stakeholder.

---

## Por qué es diferente a otras metodologías

| Característica | BAGO | Scrum/Kanban | GTD | PARA |
|---|---|---|---|---|
| **Unidad de trabajo** | Sesión + workflow + artefactos | Sprint / tarea | Acción siguiente | Proyecto |
| **Memoria entre sesiones** | Formal, en JSON + MD | Informal, en tickets | En listas | En carpetas |
| **Auditoría automática** | Sí (validate_pack, health_score) | No | No | No |
| **Adaptado a IA** | Sí (diseñado para agentes con contexto limitado) | No | No | No |
| **Orientado a decisiones** | Sí (EVD tipo decision, governance) | No (orientado a tareas) | No | No |
| **Score de salud** | Sí (5 dimensiones) | Velocity (1 dimensión) | No | No |

**La diferencia fundamental:** BAGO no gestiona listas de tareas. Gestiona **el contexto y las decisiones** que hacen que las tareas complejas sean reproducibles. Está diseñado específicamente para trabajo con agentes de IA, donde el contexto se resetea entre sesiones y la trazabilidad es la única garantía de continuidad.

---

## Recursos de referencia

| Documento | Propósito |
|---|---|
| `docs/V2_PLAYBOOK_OPERATIVO.md` | Guía técnica detallada para operadores |
| `docs/V2_POLITICA_TRANSICION.md` | Reglas de transición entre workflows |
| `docs/V2_CONTRATO_CIERRE_ESCENARIO.md` | Criterios de cierre de escenarios |
| `docs/V2_PROPUESTA.md` | Análisis y propuesta que originó esta versión |
| `core/00_CEREBRO_BAGO.md` | Documento conceptual fundacional |
| `AGENT_START.md` | Punto de entrada para agentes IA |

---

*BAGO V2 — Pack `2.4-v2rc` — Sistema operativo de trabajo técnico*
