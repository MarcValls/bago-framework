# BOOTSTRAP_PROYECTO

## 1. Rol objetivo

**ROL:** ADAPTADOR_PROYECTO

## 2. Modo BAGO principal

[A] Adaptativo

## 3. Objetivo

Inspeccionar el repositorio actual y traducirlo a contexto inicial utilizable por BAGO.

## 4. Contexto relevante

Existe un repositorio abierto y una instalación `.bago/` operativa. Se necesita identificar estructura, stack, restricciones y objetivo probable sin rediseñar todavía.

## 5. Entradas concretas

- árbol del repo,
- configuración,
- documentación,
- scripts,
- tests,
- `.bago/`.

## 6. Instrucciones

1. Detecta lenguaje y stack.
2. Resume el propósito probable.
3. Identifica entradas principales.
4. Determina primero el directorio objetivo real antes de proponer cambios o ejecutar tooling.
5. Si hay varios candidatos plausibles, no asumas el primero: usa selector y ofrece `Ruta exacta…`.
6. Trata `TESTS/`, `RELEASE/`, `audit/`, `cleanversion/`, snapshots y backups como contexto secundario salvo instrucción explícita.
7. Señala restricciones y riesgos iniciales.
8. Propón objetivo de sesión.
9. Propón modo BAGO inicial.
10. Prepara el handoff al iniciador del maestro.

## 7. Salida esperada

- resumen del proyecto,
- restricciones,
- riesgos,
- objetivo sugerido,
- modo sugerido,
- roles iniciales recomendados.
