# ACTA OFICIAL DE BASELINE

## BAGO AMTEC V2.2.2 OFICIAL

**Código de referencia:** `baseline_bago_amtec_2_2_2_oficial`  
**Versión oficial:** `2.2.2`  
**Denominación oficial:** `BAGO AMTEC V2.2.2 OFICIAL`  
**Estado:** `FROZEN / REFERENCE`  
**Fecha de adopción:** `2026-04-14`  
**Ámbito:** Sistema `.bago/` como capa operativa, canónica y auditable para trabajo sobre repositorios reales.

---

## 1. Objeto del acta

La presente acta declara formalmente la versión **BAGO AMTEC V2.2.2 OFICIAL** como **baseline oficial** del sistema BAGO AMTEC, a efectos de:

- referencia estable para evolución futura,
- comparación obligatoria de nuevas iteraciones,
- control de regresiones,
- validación de integridad estructural y semántica,
- uso operativo sobre proyectos y repositorios reales.

Esta baseline reemplaza a la **2.2.1 oficial** como referencia activa de comparación, preservando a la 2.2.1 como antecedente histórico congelado.

---

## 2. Declaración oficial

Se declara que la versión **BAGO AMTEC V2.2.2 OFICIAL** constituye la **baseline oficial estable** de la línea actual del sistema, al haber demostrado:

- integridad de manifiesto,
- integridad de estado,
- integridad del paquete completo,
- trazabilidad nativa de cambios, evidencias y sesiones,
- coherencia entre taxonomía lógica y estructura física,
- operación de stress endurecida para `github_models` con backoff, limitador global y reporte ampliado.

---

## 3. Evidencia de aceptación

La baseline queda aceptada sobre la base de las siguientes verificaciones operativas satisfactorias:

### 3.1 Validación del manifiesto

Resultado:

```text
GO manifest
```

### 3.2 Validación del estado

Resultado:

```text
GO state
```

### 3.3 Validación del paquete

Resultado:

```text
GO manifest
GO state
GO pack
```

---

## 4. Diferencia normativa respecto a 2.2.1

La 2.2.2 no abre una línea distinta. Formaliza una revisión canónica sobre la 2.2.1 y consolida:

- endurecimiento de workflows y validadores,
- alineación física y lógica de roles,
- arranque y documentación limpiados,
- tooling de stress real sobre `github_models`,
- presets operativos documentados para runs estables.

---

## 5. Efecto normativo

A partir de esta acta, toda evaluación comparativa, auditoría o nueva consolidación deberá tomar la **2.2.2 oficial** como punto oficial de referencia, salvo reemplazo expreso por una acta posterior.

---

## 6. Criterio de conservación

Esta baseline se conserva en estado congelado según [REGLA_INMUTABILIDAD_VALIDACION.md](REGLA_INMUTABILIDAD_VALIDACION.md). Puede ser distribuida, copiada y revisada, pero no debe mutarse in situ como si fuera una rama de trabajo ordinaria.
