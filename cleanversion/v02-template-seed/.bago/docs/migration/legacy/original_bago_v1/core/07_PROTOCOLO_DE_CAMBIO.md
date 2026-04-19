# 07 · PROTOCOLO DE CAMBIO Y TRAZABILIDAD

## Objetivo

Formalizar cómo se registran y aceptan los cambios relevantes en BAGO AMTEC V1.

---

## 1. Qué debe registrarse

Registrar un cambio cuando afecte a:

- arquitectura del sistema BAGO,
- contratos de rol,
- criterios de activación,
- estado vivo por cambio estructural,
- revisión evolutiva con recomendación aceptada.

---

## 2. Formato mínimo de registro

```md
# CAMBIO BAGO

- **Cambio ID:**
- **Fecha:**
- **Motivo:**
- **Ámbito afectado:**
- **Situación previa:**
- **Cambio aplicado o aceptado:**
- **Impacto esperado:**
- **Riesgos asociados:**
- **Estado:** propuesto | aceptado | descartado
```

---

## 3. Regla de aceptación

Un cambio no se considera vigente hasta que:

1. esté descrito,
2. tenga impacto resumido,
3. el estado vivo refleje la parte operativa que corresponda.

---

## 4. Ubicación

Guardar cada cambio relevante en:

```text
.bago/state/cambios/
```
