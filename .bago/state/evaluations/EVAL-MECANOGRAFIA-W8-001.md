# EVAL-MECANOGRAFIA-W8-001 · Exploración Aplicada — MECANOGRAFIA.html

**Sesión:** SES-W8-2026-04-18-001  
**Fecha:** 2026-04-18  
**Archivo analizado:** `cleanversion/BAGO_2.4-v2rc_clean_20260418_161154/MECANOGRAFIA.html`  
**Líneas:** 543 · Dependencias externas: 0 · Idiomas: ES, CA

---

## 1. DIAGNÓSTICO DEL ESTADO ACTUAL

### ✅ Qué funciona bien

| Área | Detalle | Líneas |
|------|---------|--------|
| Arquitectura | Standalone HTML/CSS/JS, cero dependencias, portable | — |
| Diseño visual | Dark glass-morphism con CSS custom properties limpias | 8–79 |
| Teclado visual | 8 dedos con color coding, highlight de tecla activa | 211–238 |
| Input robusto | `beforeinput` + `input` + `keydown` fallback para ñ/ç/acentos | 415–440 |
| Normalización | `normChar()` NFD + preserva 'ç' correctamente | 150–158 |
| Audio | Web Audio API beeps sin archivos, 3 tonos distintos | 162–167 |
| Progresión | 10 lecciones por idioma, home keys → filas → sílabas → palabras | 179–201 |
| localStorage | Récord por lección+idioma, persistente entre sesiones | 262–268 |
| FX | Canvas confetti + toast banners | 327–351 |
| Bilingüismo | Layout, lecciones y vocabulario separados por idioma | 170–206 |
| `ignoreAccents` | Toggle para hacer acentos opcionales en la comparación | 154–156 |

### ⚠️ Limitaciones identificadas

#### Bug A — Double-fire en `handleChar` (crítico en algunos navegadores)
**Líneas 415–440.** Los tres listeners (`beforeinput`, `input`, `keydown`) pueden llamar `handleChar` para el mismo golpe de tecla. `beforeinput` llama `ev.preventDefault()`, pero `keydown` no comprueba si `beforeinput` ya actuó. En Firefox desktop y algunos navegadores móviles, ambos disparan, contando **un carácter dos veces** (inflando `state.total` y potencialmente `state.correct`).

```js
// PROBLEMA: no hay guard de deduplicación entre handlers
els.ghost.addEventListener('beforeinput', ev => { ... handleChar(data); });
els.ghost.addEventListener('input', ev => { ... handleChar(data); });        // fallback
document.addEventListener('keydown', e => { ... handleChar(e.key); });      // fallback
```

#### Bug B — WPM cuenta tiempo de pausa
**Línea 322.** `elapsedMin = (now() - state.startTime) / 60000` no descuenta el tiempo pausado. Pausar 5 minutos divide el WPM a la mitad artificialmente. Fix: acumular `pausedMs` en `pause()`.

#### Limitación C — L9 sílabas ignora la progresión aprendida
**Líneas 275–288.** `makeSyllable()` usa `cons` (23 consonantes) y `voc` (5 vocales) fijos, sin importar qué teclas se aprendieron en L1–L8. Un alumno en L9 puede recibir `py`, `wö`, `zú` — combinaciones con teclas nunca practicadas. Debería filtrar al pool acumulado de L1–L8.

#### Limitación D — Vocabulario extremadamente reducido
**Líneas 205–206.** Solo 15 palabras por idioma. En L10, la misma palabra aparece estadísticamente cada ~15 intentos. No hay repetición controlada, ni weighting por frecuencia, ni variedad.

#### Limitación E — Modo `palabras` no implementado correctamente
**Líneas 98–101, 494–499.** El `<select id="mode">` tiene la opción `palabras` pero el handler `onchange` solo deshabilita el selector de lección. `pickTarget()` (línea 284) no distingue el modo `palabras` — si la lección activa es L1, sigue generando 'f'/'j'. El modo promete palabras pero no las fuerza.

#### Limitación F — Sin historial de WPM
Solo se persiste `best` (mejor precisión). No se guarda historial de sesiones, ni WPM récord, ni tendencia de mejora. El usuario no puede ver si progresa en velocidad.

#### Limitación G — Tira de errores recientes sin contexto
**Líneas 474–481.** `pushRecent()` muestra el badge del carácter tecleado, coloreado verde/rojo. Pero no muestra qué carácter se esperaba en un error. Imposible saber si tecleaste 'd' cuando se esperaba 'f'.

#### Limitación H — Canvas confetti monocromático
**Línea 340.** `ctx.fillStyle='white'` siempre. El confetti es solo puntos blancos. Las variables CSS `--l5..--r5` ya tienen 8 colores definidos; usarlos daría más vida visual.

#### Limitación I — Sin análisis de errores por tecla
No hay registro de qué teclas se fallan más. Sin heatmap de errores, el alumno no puede focalizar su práctica.

#### Limitación J — Sin número ni fila de símbolos
Filas numéricas (1–0) y caracteres especiales completamente ausentes del layout y las lecciones.

---

## 2. IDEAS DE MEJORA PRIORIZADAS

### 🔴 Categoría A — Contenido pedagógico

| Prioridad | Idea | Esfuerzo | Impacto |
|-----------|------|----------|---------|
| A1 | **Expandir vocabulario a 100–200 palabras** por idioma con palabras de frecuencia real | Bajo | Alto |
| A2 | **L9 adapts syllables al pool acumulado** (L1–L8 chars only) | Bajo | Alto |
| A3 | **Lecciones de tildes** (á é í ó ú ü) como L11-L12 opcionales | Medio | Medio |
| A4 | **Fila de números** como lecciones opcionales (L11+) | Medio | Medio |
| A5 | **Textos reales** en L10 (frases cortas) en lugar de palabras aisladas | Alto | Alto |

### 🟠 Categoría B — UX / Feedback al usuario

| Prioridad | Idea | Esfuerzo | Impacto |
|-----------|------|----------|---------|
| B1 | **Mostrar carácter esperado en errores** en la tira `recent` | Bajo | Alto |
| B2 | **Confetti multicolor** usando colores de dedos ya definidos | Mínimo | Medio |
| B3 | **Indicador de Caps Lock activo** (aviso cuando la entrada falla sistemáticamente) | Bajo | Medio |
| B4 | **Tooltip de atajo Escape = pausa** visible en el botón Pausa | Mínimo | Bajo |
| B5 | **Resaltar también la tecla Shift** cuando el target es mayúscula | Medio | Medio |

### 🟡 Categoría C — Métricas y progreso

| Prioridad | Idea | Esfuerzo | Impacto |
|-----------|------|----------|---------|
| C1 | **Corregir WPM durante pausa** (descontar `pausedMs`) | Mínimo | Alto |
| C2 | **Guardar WPM récord** por lección (además de precisión) | Bajo | Alto |
| C3 | **Heatmap de errores por tecla** en teclado visual (color de calor en teclas más falladas) | Medio | Alto |
| C4 | **Historial de sesiones** (gráfico sparkline: últimas N precisiones) | Alto | Alto |
| C5 | **Tiempo medio por carácter** como métrica secundaria | Bajo | Medio |

### 🔵 Categoría D — Funcionalidades nuevas

| Prioridad | Idea | Esfuerzo | Impacto |
|-----------|------|----------|---------|
| D1 | **Corregir modo `palabras`** para forzar vocab independientemente de lección | Mínimo | Alto |
| D2 | **Fix double-fire** en `handleChar` con guard de timestamp | Bajo | Alto (bug) |
| D3 | **Modo carrera**: N palabras en X segundos, score final | Medio | Alto |
| D4 | **Uppercase / shift practice** como toggle o lección dedicada | Medio | Medio |
| D5 | **Export de estadísticas** (JSON/CSV descargable) | Bajo | Bajo |

### ⚪ Categoría E — Calidad del código

| Prioridad | Idea | Esfuerzo | Impacto |
|-----------|------|----------|---------|
| E1 | **Separar datos de lógica** (mover lecciones/vocab a constantes top-level, ya está, pero podrían ir a un módulo `data.js`) | Medio | Bajo |
| E2 | **Desacoplar `state` de DOM** (actualmente `handleChar` mezcla lógica y render) | Alto | Bajo |
| E3 | **Añadir comentarios JSDoc** a funciones principales | Bajo | Bajo |

---

## 3. TOP 3 MEJORAS DE ALTO IMPACTO / BAJO ESFUERZO

### 🥇 #1 — Fix double-fire guard en `handleChar` (~10 líneas)

**Por qué primero:** Es un bug de correctness que afecta las métricas core (`state.total`, `state.correct`, WPM). Si un usuario usa Firefox o un browser mobile, sus estadísticas son incorrectas y el sistema de avance se corrompe.

**Dónde:** Añadir una variable `let _lastHandledAt = 0` y en `handleChar`:
```js
function handleChar(raw) {
  const t = performance.now();
  if (t - _lastHandledAt < 20) return;  // dedup window: 20ms
  _lastHandledAt = t;
  // ... resto igual
}
```
También limpiar el listener `input` redundante (ya cubierto por `beforeinput` + `keydown`).

---

### 🥈 #2 — Ampliar vocabulario + fix modo `palabras` (~20 líneas)

**Por qué segundo:** L10 con 15 palabras es la lección final del tutor. Un alumno que llega ahí tras completar L1–L9 merece un contenido más rico. Además el modo `palabras` está roto.

**Dónde:** 
- Expandir `wordsES` y `wordsCA` a ~80 palabras frecuentes sin tildes (o con `ignoreAccents`).  
- En `pickTarget()` (línea 284–288), añadir:
```js
if (state.mode === 'palabras') return vocab[rnd(0, vocab.length-1)];
```
antes del switch por `L.type`.

---

### 🥉 #3 — Fix WPM durante pausa + mostrar WPM récord en header (~15 líneas)

**Por qué tercero:** WPM es la métrica más motivadora para un alumno de mecanografía. Que sea incorrecta durante sesiones con pausa es desmotivador. Y no tener WPM récord (solo precisión récord) elimina la mitad del feedback de progreso.

**Dónde:**
```js
// En state (línea 252):
pausedMs: 0, pauseStarted: 0,

// En pause() (línea 376):
if (state.paused) state.pauseStarted = now();
else state.pausedMs += now() - state.pauseStarted;

// En updateStats() (línea 322):
const elapsedMin = Math.max(1/60, (now() - state.startTime - state.pausedMs) / 60000);
```
Y añadir `<b id="bestWpm">0 WPM</b>` al `.stat` de Ritmo, guardando en localStorage igual que precisión.

---

## 4. MEJORA AMBICIOSA — Sistema de Texto Fluido con NLP ligero

Si se quiere evolucionar el proyecto en serio, la mejora de mayor impacto es **sustituir el modelo de caracteres/palabras aislados por un sistema de texto fluido con análisis de errores en tiempo real**:

### Descripción técnica

**Estado actual:** el alumno teclea un carácter o una palabra a la vez. La unidad de medida es el prompt individual.

**Propuesta:** implementar un **runner de texto continuo** donde el alumno teclea un párrafo completo (estilo typeracer.com o keybr.com), con:

1. **Texto renderizado como spans** — cada carácter tiene su propio `<span>` con estado (`pending` / `correct` / `error` / `current`). El cursor avanza sobre el texto real.

2. **Vocabulario generativo por lección**: en lugar de 15 palabras estáticas, generar frases usando solo las letras aprendidas hasta la lección actual (algoritmo de "síntesis de texto pedagógico"). Ej: L4 genera frases como `"fad sal das fall fad"` con el pool `[a,s,d,f,j,k,l,ñ]`.

3. **Análisis de errores persistente**: `errorMap: Map<char, {hits:number, errors:number}>` actualizado en cada `handleChar`. Renderizar en el teclado visual un **gradiente de calor** (verde→amarillo→rojo) según tasa de error por tecla. Persistir en localStorage.

4. **Curva de dificultad adaptativa**: detectar las 3 teclas con más errores y sobre-representarlas en el próximo párrafo generado (weighted random selection).

5. **Dashboard de sesión al finalizar**: overlay con WPM, precisión, caracteres/min, top-3 teclas fallidas, comparativa con récord.

**Esfuerzo estimado:** 3–4 sesiones W7 (250–350 líneas nuevas). Mantiene el standalone HTML sin dependencias. El archivo podría crecer a ~900 líneas pero seguiría siendo portable.

**Referencias de código existentes a reutilizar:**
- `normChar()` (línea 150) — sin cambios
- `makeFingerMap()` (línea 211) — sin cambios  
- `buildKeyboard()` (línea 227) — extender con data-error-rate
- `beep()` (línea 162) — sin cambios
- `localStorage` pattern (líneas 263–265) — extender con `errorMap`

---

## 5. DECISIONES REGISTRADAS

1. **Los bugs A (double-fire) y B (WPM pausa) son prioridad 1** antes de cualquier feature nueva — afectan correctness de métricas.
2. **L9 debe filtrar por pool acumulado** — sin eso, la progresión pedagógica está rota a partir de L9.
3. **La mejora ambiciosa (texto fluido) es viable como proyecto standalone** — no requiere framework, el codebase actual es una buena base.
4. **El vocabulario de 15 palabras es el gap de contenido más fácil de resolver** — alto impacto, cero riesgo.
