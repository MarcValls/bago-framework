# 06 · MATRIZ DE ACTIVACIÓN DE ROLES

## Objetivo

Reducir solapes y activaciones innecesarias.

---

## 1. Matriz principal

| Fase               | Objetivo dominante            | Rol obligatorio | Roles opcionales                           | No activar salvo excepción          |
| ------------------ | ----------------------------- | --------------- | ------------------------------------------ | ----------------------------------- |
| [B] Balanceado     | entender problema y límites   | MAESTRO_BAGO    | ANALISTA_Contexto                          | GUIA_VERTICE                        |
| [A] Adaptativo     | decidir enfoque y secuencia   | MAESTRO_BAGO    | ANALISTA_Contexto, ARQUITECTO_Soluciones   | GENERADOR_Contenido masivo          |
| [G] Generativo     | producir artefactos           | MAESTRO_BAGO    | GENERADOR_Contenido, ARQUITECTO_Soluciones | GUIA_VERTICE                        |
| [O] Organizativo   | ordenar, empaquetar y validar | MAESTRO_BAGO    | ORGANIZADOR_Entregables                    | ANALISTA_Contexto profundo          |
| Revisión evolutiva | supervisar coherencia         | GUIA_VERTICE    | MAESTRO_BAGO, ANALISTA_Contexto            | GENERADOR_Contenido salvo evidencia |

---

## 2. Reglas rápidas

- Si falta claridad: entra `ANALISTA_Contexto`.
- Si el problema está claro pero el camino no: entra `ARQUITECTO_Soluciones`.
- Si ya existe diseño suficiente: entra `GENERADOR_Contenido`.
- Si hay que empaquetar o cerrar: entra `ORGANIZADOR_Entregables`.
- Si hay deriva o tensión estructural: evaluar `GUIA_VERTICE`.

---

## 3. Anti-patrones

No hacer esto:

- activar todos los roles “por si acaso”,
- meter `GUIA_VERTICE` en tareas rutinarias,
- mantener a `ANALISTA_Contexto` activo durante generación masiva sin necesidad,
- usar `ORGANIZADOR_Entregables` para rediseñar arquitectura.
