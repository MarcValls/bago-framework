# BAGO — Planes de implementación por slot
> Generado automáticamente desde `bago.db`. Orden de ejecución recomendado: slot 1→3 primero (cadenas de 3 generaciones), luego 4→8 (independientes).

---

## SLOT 1 — Flujo de tarea completo

### GEN 1 · Handoff idea → W2
| Campo | Valor |
|---|---|
| **Feature gate** | `handoff_w2 = False` (idea visible hasta que se implemente) |
| **Extra-cond** | `always` |
| **Métrica** | El handoff contiene: objetivo, alcance, no-alcance, archivos candidatos, validación mínima |

**Objetivo:** Cuando el usuario acepta una idea, producir automáticamente una plantilla W2 lista para pegar en `pending_w2_task.json`.

**Archivos a modificar:**
- `.bago/tools/emit_ideas.py` — añadir flag `--accept <N>` que llame a `_generate_w2_handoff(idea)` y escriba el JSON en `.bago/state/pending_w2_task.json`.

**Pasos:**
1. Añadir argumento `--accept N` al argparse de `emit_ideas.py`.
2. Implementar `_generate_w2_handoff(idea: dict) -> dict` que rellene los campos W2 estándar.
3. Escribir el resultado en `pending_w2_task.json`.
4. Marcar `feat[handoff_w2] = True` en `detect_implemented_features()` (verificar que el archivo existe y contiene los campos).

**Validación mínima:**
```
python bago ideas --accept 1
cat .bago/state/pending_w2_task.json  # debe tener objetivo, alcance, archivos
```

---

### GEN 2 · Opener de sesión desde task
| Campo | Valor |
|---|---|
| **Requiere** | `handoff_w2 = True` |
| **Feature gate** | `session_opener = False` |
| **Métrica** | `bago session` lanza `session_preflight` con campos pre-rellenados |

**Objetivo:** Al iniciar sesión, leer la tarea pendiente y pre-poblar el preflight con su contexto.

**Archivos a modificar / crear:**
- `.bago/tools/session_opener.py` (crear o ampliar) — leer `pending_w2_task.json`, llamar a `session_preflight.py` pasando objetivo y artefactos.
- `bago` (script raíz) — registrar `session` como comando que delega en `session_opener.py`.

**Pasos:**
1. Crear `session_opener.py` con `open_session(task_path)`.
2. Leer `pending_w2_task.json`; si no existe → mostrar "No hay task activa."
3. Llamar a `session_preflight.py` con args `--objetivo "..." --roles "..."`.
4. Registrar feat en `detect_implemented_features()`.

**Validación mínima:**
```
python bago session  # debe mostrar el objetivo de la task activa
```

---

### GEN 3 · Cierre automático de sesión
| Campo | Valor |
|---|---|
| **Requiere** | `handoff_w2 = True`, `session_opener = True` |
| **Métrica** | `bago task --done` genera y persiste el artefacto de cierre |

**Objetivo:** Al marcar una tarea como terminada, generar automáticamente el artefacto de cierre (CHG/EVD).

**Archivos a modificar:**
- `.bago/tools/show_task.py` — extender `--done` para llamar a `_generate_session_close()`.
- `.bago/tools/db_init.py` — insertar registro en `implemented_ideas` si la tarea viene de una idea.

**Pasos:**
1. En `show_task.py --done`: recolectar archivos modificados y descripción.
2. Generar `session_close_<timestamp>.md` en `.bago/state/`.
3. Actualizar `global_state.json` y limpiar `pending_w2_task.json`.
4. Insertar en tabla `implemented_ideas` de `bago.db`.

**Validación mínima:**
```
python bago task --done  # genera .bago/state/session_close_*.md
```

---

## SLOT 2 — Visibilidad del sistema

### GEN 1 · Resumen único de estabilidad
| Campo | Valor |
|---|---|
| **Feature gate** | `stability_cmd = False` |
| **Métrica** | Un bloque muestra smoke + VM + soak con semáforo |

**Objetivo:** Crear un resumen consolidado de estabilidad para decisión rápida.

**Archivos a modificar / crear:**
- `.bago/tools/stability_summary.py` — consolidar resultados de `smoke_test.py`, `vm_health.py`, `soak_test.py` en un bloque con íconos 🟢/🟡/🔴.

**Pasos:**
1. Crear/extender `stability_summary.py` con `summarize()` que lee los últimos resultados de cada subsistema.
2. Formatear salida: tabla de 3 filas (smoke/VM/soak) con estado y timestamp.
3. Devolver código de salida 0 si todo verde, 1 si alguno falla.
4. Registrar `feat[stability_cmd] = True`.

**Validación mínima:**
```
python bago stability  # muestra bloque con 3 estados
```

---

### GEN 2 · Banner muestra task activa
| Campo | Valor |
|---|---|
| **Requiere** | `stability_cmd = True` |
| **Feature gate** | `banner_shows_task = False` |
| **Métrica** | Banner muestra título y estado de tarea W2 activa |

**Objetivo:** El banner BAGO informa de un vistazo si hay tarea en progreso.

**Archivos a modificar:**
- `.bago/tools/bago_banner.py` — leer `pending_w2_task.json`; si existe, añadir línea `⏳ Task: <título> [<status>]`.

**Pasos:**
1. Al final de `render_banner()` intentar abrir `pending_w2_task.json`.
2. Si existe y `status != done`: añadir línea de tarea.
3. Si no existe: sin cambio en banner.
4. Registrar `feat[banner_shows_task] = True` (verificar que banner la imprime).

**Validación mínima:**
```
python bago banner  # con task activa → debe mostrar línea de task
```

---

### GEN 3 · Alerta de task obsoleta
| Campo | Valor |
|---|---|
| **Requiere** | `stability_cmd = True`, `banner_shows_task = True` |
| **Métrica** | Alerta visible cuando task supera 3 días sin completarse |

**Objetivo:** Evitar que tareas viejas pasen desapercibidas.

**Archivos a modificar:**
- `.bago/tools/bago_banner.py` — comparar `accepted_at` con `datetime.now()`.
- `.bago/tools/stability_summary.py` — mostrar el mismo aviso en el resumen de estabilidad.

**Pasos:**
1. Leer campo `accepted_at` (ISO 8601) de `pending_w2_task.json`.
2. Si `(now - accepted_at).days > 3` → imprimir `⚠️ Task lleva N días sin completarse`.
3. Misma lógica en `stability_summary.py`.
4. Asegurarse de que `emit_ideas.py` escribe `accepted_at` al hacer `--accept`.

**Validación mínima:**
```
# Modificar accepted_at en pending_w2_task.json a fecha >3 días atrás
python bago banner  # debe mostrar ⚠️
```

---

## SLOT 3 — Calidad del ciclo de ideas

### GEN 1 · Gate seguro antes de implementar
| Campo | Valor |
|---|---|
| **Feature gate** | `gate_in_code = False` |
| **Extra-cond** | `stable_reports` (el gate solo es relevante si hay informes) |
| **Métrica** | Ninguna idea avanza si smoke/validate_pack/validate_state fallan |

**Objetivo:** Garantizar que el sistema está estable antes de proponer cambios.

**Archivos a modificar:**
- `.bago/tools/emit_ideas.py` — completar `run_canonical_gate()`: añadir smoke_test al check. Devolver `(passed, reason)`.
- Bloquear la salida de ideas si gate falla.

**Pasos:**
1. En `run_canonical_gate()`: ejecutar `validate_pack`, `validate_state`, `smoke_test` como subprocesos.
2. Si alguno falla → imprimir motivo y salir con código 1.
3. Registrar `feat[gate_in_code] = True` en `detect_implemented_features()`.

**Validación mínima:**
```
# Romper algo en pack.json temporalmente
python bago ideas  # debe mostrar error de gate, no ideas
```

---

### GEN 2 · Registro de ideas implementadas
| Campo | Valor |
|---|---|
| **Requiere** | `gate_in_code = True` |
| **Feature gate** | `impl_registry = False` |
| **Métrica** | Selector nunca repite idea ya implementada |

**Objetivo:** Evitar resugerir ideas ya completadas.

**Archivos a modificar:**
- `.bago/tools/db_init.py` — tabla `implemented_ideas` ya existe; verificar que `show_task.py --done` inserta aquí.
- `.bago/tools/emit_ideas.py` — en `load_ideas_from_db()`, filtrar filas cuyo `title` ya esté en `implemented_ideas`.

**Pasos:**
1. En `load_ideas_from_db()`: `SELECT title FROM implemented_ideas` → set de títulos implementados.
2. Filtrar `ideas` resultantes excluyendo esos títulos.
3. Registrar `feat[impl_registry] = True`.

**Validación mínima:**
```
python bago db --add --title "Handoff idea -> W2" --implemented
python bago ideas  # esa idea no debe aparecer
```

---

### GEN 3 · Scoring dinámico por registro
| Campo | Valor |
|---|---|
| **Requiere** | `impl_registry = True` |
| **Métrica** | Ideas no implementadas suben en ranking respecto a similares ya hechas |

**Objetivo:** Hacer que el ranking refleje el estado real de avance.

**Archivos a modificar:**
- `.bago/tools/emit_ideas.py` — en `load_ideas_from_db()` y `_build_ideas_hardcoded()`: aplicar `+10` a ideas cuyo título no esté en `implemented_ideas`.

**Pasos:**
1. Tras cargar ideas, consultar `implemented_ideas` de DB.
2. Para cada idea: `if idea['title'] not in implemented_set: idea['priority'] += 10`.
3. Re-ordenar por `priority` descendente.
4. No modificar el valor en DB, calcular en memoria.

**Validación mínima:**
```
python bago ideas  # verificar que ideas nuevas aparecen antes que implementadas del mismo slot
```

---

## SLOT 4 — Selector por intención *(independiente)*
| Campo | Valor |
|---|---|
| **Extra-cond** | `matrix_pass` |
| **Métrica** | Usuario llega a workflow correcto en 1 paso de intención |

**Objetivo:** Dar al usuario un menú de intenciones en vez de que navegue workflows manualmente.

**Archivos a modificar / crear:**
- `.bago/tools/workflow_selector.py` (o nuevo `intent_selector.py`) — menú con 4 opciones: explorar idea / implementar / debug / cerrar sesión. Cada opción filtra y lanza el workflow correspondiente.
- `bago` (script raíz) — registrar `intent` como comando.

**Pasos:**
1. Crear menú interactivo (stdin o argumento `--intent <nombre>`).
2. Mapear intención → workflow: `idea→emit_ideas`, `implementar→show_task`, `debug→stability_summary`, `cerrar→session_opener --close`.
3. Ejecutar workflow seleccionado como subproceso.

**Validación mínima:**
```
python bago intent  # muestra menú de intenciones
python bago intent --intent idea  # ejecuta bago ideas directamente
```

---

## SLOT 5 — Ideas orientadas a baseline *(independiente)*
| Campo | Valor |
|---|---|
| **Extra-cond** | `baseline_clean` |
| **Métrica** | Solo ideas low-risk con métrica aparecen en modo baseline |

**Objetivo:** En modo baseline, proponer solo ideas seguras con impacto medible.

**Archivos a modificar:**
- `.bago/tools/emit_ideas.py` — la función `filter_ideas_for_baseline_mode()` ya existe; verificar que filtra por `risk=low` y `metric != ""`. Añadir mensaje en output `[modo baseline]`.

**Pasos:**
1. Revisar `filter_ideas_for_baseline_mode()`: confirmar que verifica `risk` y `metric`.
2. Si la DB no tiene columna `risk`: añadir en esquema y seed.
3. En salida de `bago ideas`: mostrar `🏗 Modo baseline: solo ideas de bajo riesgo`.

**Validación mínima:**
```
python bago ideas --baseline  # solo muestra ideas low-risk con métrica definida
```

---

## SLOT 6 — Reabrir desde continuidad *(independiente)*
| Campo | Valor |
|---|---|
| **Extra-cond** | `has_session_close` |
| **Métrica** | Reapertura sin reconstrucción manual, menos pasos de arranque |

**Objetivo:** Al reabrir una sesión, restaurar contexto desde el artefacto de cierre anterior.

**Archivos a modificar:**
- `.bago/tools/session_opener.py` — añadir `--reopen`: leer el `session_close_*.md` más reciente de `.bago/state/`, extraer objetivo/artefactos/pendientes y pre-poblar el contexto actual.

**Pasos:**
1. `glob(".bago/state/session_close_*.md")` → tomar el más reciente.
2. Parsear secciones (objetivo, pendientes, próximo paso).
3. Imprimir resumen de continuidad y pre-poblar `current_context.json`.
4. Verificar que `pending_w2_task.json` coincide con lo abierto.

**Validación mínima:**
```
python bago session --reopen  # muestra resumen de sesión anterior
```

---

## SLOT 7 — Entrada rápida del repo *(independiente)*
| Campo | Valor |
|---|---|
| **Extra-cond** | `has_readme` |
| **Métrica** | Primera decisión del usuario llega a acción en 1 paso |

**Objetivo:** `bago start` como comando unificado de arranque: health + top idea + acción.

**Archivos a modificar:**
- `bago` (script raíz) — comando `start` que ejecuta: `bago health` → si OK, `bago ideas` → muestra top 1 → pregunta al usuario si quiere aceptarla (→ `--accept 1`) o ver más.
- `.bago/README.md` — añadir sección "Inicio rápido: `bago start`".

**Pasos:**
1. Registrar `start` en `tool_registry.py` → nuevo `quick_start.py` o inline en script raíz.
2. Flujo: health check → top idea → prompt de aceptación.
3. Si acepta → llamar `emit_ideas.py --accept 1`.
4. Actualizar README con sección de inicio rápido.

**Validación mínima:**
```
python bago start  # health + top idea + prompt de acción en una sola invocación
```

---

## SLOT 8 — Mejorar ranking de ideas *(independiente)*
| Campo | Valor |
|---|---|
| **Extra-cond** | `always` |
| **Métrica** | Ranking varía según estado real del sistema |

**Objetivo:** Ranking contextual en vez de estático: las señales de estado afectan el score.

**Archivos a modificar:**
- `.bago/tools/emit_ideas.py` — en `load_ideas_from_db()` / `_build_ideas_hardcoded()`: ajuste dinámico de score:
  - `+5` si no hay task activa (`pending_w2_task.json` no existe) → fomentar exploración.
  - `-10` si hay task activa y `risk=high` → no distraer.
  - `+5` si `section=contextuales` vs `section=respaldo`.

**Pasos:**
1. Detectar estado de tarea activa (leer `pending_w2_task.json`).
2. Para cada idea aplicar los ajustes indicados en memoria.
3. Re-ordenar después de ajustar.
4. Añadir columna `risk` en DB si aún no existe (default `medium`).

**Validación mínima:**
```
# Con y sin pending_w2_task.json → verificar que el orden cambia
python bago ideas  # ranking debe variar según estado
```

---

## Orden de ejecución recomendado

```
Fase A (núcleo del flujo de tarea):
  s1g1 → s1g2 → s1g3
  s2g1 → s2g2 → s2g3
  s3g1 → s3g2 → s3g3

Fase B (mejoras independientes, cualquier orden):
  s8g1  (ranking — mejora todo lo anterior)
  s4g1  (intent selector)
  s5g1  (baseline mode)
  s7g1  (quick start)
  s6g1  (reopen — requiere s1g3 completado)
```
