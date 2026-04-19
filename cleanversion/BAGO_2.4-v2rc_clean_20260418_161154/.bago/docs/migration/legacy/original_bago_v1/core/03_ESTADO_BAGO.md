# 03 · MODELO DE ESTADO BAGO · V1

Este archivo define el **modelo** y las reglas del estado BAGO.

El estado vivo de la sesión se guarda en:

```text
.bago/state/ESTADO_BAGO_ACTUAL.md
```

---

## 1. Propósito

Dar una estructura estable al estado compartido para que cualquier sesión pueda:

- continuar sin perder contexto,
- evitar contradicciones entre roles,
- separar hechos, decisiones y pendientes,
- y registrar cambios de forma comparable.

---

## 2. Campos obligatorios del estado vivo

### Metadatos

- **Sesión ID**
- **Versión del pack**
- **Última actualización**
- **Repositorio / ámbito**

### Núcleo operativo

- **Objetivo actual**
- **Modo predominante**
- **Fase actual**
- **Roles activos**
- **Entradas disponibles**
- **Contenido producido**
- **Pendientes**
- **Restricciones**
- **Decisiones congeladas**
- **Riesgos abiertos**
- **Siguiente paso**

---

## 3. Reglas de modelado

1. **Pendientes** no puede usarse para guardar decisiones ya cerradas.
2. **Decisiones congeladas** debe contener solo acuerdos vigentes.
3. **Contenido producido** debe listar resultados reales, no intenciones.
4. **Riesgos abiertos** debe reflejar incertidumbre viva.
5. **Siguiente paso** debe ser ejecutable y acotado.

---

## 4. Regla de actualización

El estado vivo debe actualizarse cuando ocurra al menos uno de estos eventos:

- cambio de objetivo,
- cambio de fase,
- activación o desactivación de roles,
- aceptación de una decisión estructural,
- generación de un entregable importante,
- apertura de una revisión evolutiva,
- cierre o aparición de un riesgo relevante.

---

## 5. Plantilla canónica del estado vivo

```md
# ESTADO BAGO ACTUAL

- **Sesión ID:**
- **Versión del pack:**
- **Última actualización:**
- **Repositorio / ámbito:**
- **Objetivo actual:**
- **Modo predominante:**
- **Fase actual:**
- **Roles activos:**
- **Entradas disponibles:**
- **Contenido producido:**
- **Pendientes:**
- **Restricciones:**
- **Decisiones congeladas:**
- **Riesgos abiertos:**
- **Siguiente paso:**
```
