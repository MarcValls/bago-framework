# BAGO Rule Catalog

> **17 reglas** (7 Python + 10 JS/TS)

## Índice rápido

| Código | Severidad | Categoría | Título | Autofix |
|--------|-----------|-----------|--------|---------|
| `BAGO-E001` | 🔴 error | Fiabilidad | Bare except clause | ✅ |
| `BAGO-W001` | 🟡 warning | Fiabilidad | datetime.utcnow() deprecated | ✅ |
| `BAGO-W002` | 🟡 warning | Seguridad | eval() / exec() usage | — |
| `BAGO-W003` | 🟡 warning | Fiabilidad | os.system() — use subprocess | — |
| `BAGO-W004` | 🟡 warning | Fiabilidad | Hardcoded absolute path | — |
| `BAGO-I001` | 🔵 info | Mantenibilidad | sys.exit(1) without visible message | — |
| `BAGO-I002` | 🔵 info | Mantenibilidad | TODO/FIXME/HACK comment | — |
| `JS-E001` | 🔴 error | Seguridad | eval() / Function() constructor | — |
| `JS-W001` | 🟡 warning | Mantenibilidad | console.log() en código de producción | — |
| `JS-W002` | 🟡 warning | Mantenibilidad | debugger statement | — |
| `JS-W003` | 🟡 warning | Fiabilidad | Loose equality == / != | — |
| `JS-W004` | 🟡 warning | Seguridad | setTimeout/setInterval con string | — |
| `JS-W005` | 🟡 warning | Fiabilidad | Empty catch block | — |
| `JS-I001` | 🔵 info | Mantenibilidad | TODO/FIXME comment | — |
| `JS-I002` | 🔵 info | Mantenibilidad | Arrow function con >5 parámetros | — |
| `JS-I003` | 🔵 info | Mantenibilidad | Ternario anidado | — |
| `JS-I004` | 🔵 info | Mantenibilidad | Async function sin await | — |

---

## Referencia detallada


## Python (bago-lint)

### `BAGO-E001` — Bare except clause

**Severidad:** 🔴 `error`  
**Categoría:** Fiabilidad  
**Fuente:** `bago`  
**Autofix:** ✅ soportado  
**Suprimir:** `# noqa: BAGO-E001`


La cláusula `except:` sin tipo captura `SystemExit` y `KeyboardInterrupt`, lo que impide interrumpir el programa con Ctrl-C y oculta errores inesperados.

**❌ Incorrecto:**
```python
try:
    risky()
except:
    pass
```

**✅ Correcto:**
```python
try:
    risky()
except Exception as e:
    log(e)
```

---

### `BAGO-W001` — datetime.utcnow() deprecated

**Severidad:** 🟡 `warning`  
**Categoría:** Fiabilidad  
**Fuente:** `bago`  
**Autofix:** ✅ soportado  
**Suprimir:** `# noqa: BAGO-W001`


`datetime.utcnow()` devuelve un `datetime` naive en UTC, lo que induce confusión con zonas horarias. Deprecated desde Python 3.12.

**❌ Incorrecto:**
```python
ts = datetime.utcnow()
```

**✅ Correcto:**
```python
ts = datetime.now(timezone.utc)
```

---

### `BAGO-W002` — eval() / exec() usage

**Severidad:** 🟡 `warning`  
**Categoría:** Seguridad  
**Fuente:** `bago`  
**Suprimir:** `# noqa: BAGO-W002`


`eval()` y `exec()` ejecutan código arbitrario. Si la entrada proviene de fuentes externas, es una vulnerabilidad crítica RCE.

**❌ Incorrecto:**
```python
result = eval(user_input)
```

**✅ Correcto:**
```python
# Usa ast.literal_eval() para datos estructurados
result = ast.literal_eval(data)
```

---

### `BAGO-W003` — os.system() — use subprocess

**Severidad:** 🟡 `warning`  
**Categoría:** Fiabilidad  
**Fuente:** `bago`  
**Suprimir:** `# noqa: BAGO-W003`


`os.system()` no captura stdout/stderr, no permite control de código de retorno y es más vulnerable a inyección de shell.

**❌ Incorrecto:**
```python
os.system("ls -la")
```

**✅ Correcto:**
```python
subprocess.run(["ls", "-la"], check=True)
```

---

### `BAGO-W004` — Hardcoded absolute path

**Severidad:** 🟡 `warning`  
**Categoría:** Fiabilidad  
**Fuente:** `bago`  
**Suprimir:** `# noqa: BAGO-W004`


Rutas absolutas hardcodeadas (`/Users/`, `/home/`, `C:\\`) impiden portabilidad entre máquinas y entornos CI.

**❌ Incorrecto:**
```python
config = "/Users/marc/project/config.json"
```

**✅ Correcto:**
```python
config = Path(__file__).parent / "config.json"
```

---

### `BAGO-I001` — sys.exit(1) without visible message

**Severidad:** 🔵 `info`  
**Categoría:** Mantenibilidad  
**Fuente:** `bago`  
**Suprimir:** `# noqa: BAGO-I001`


Salir con código 1 sin mensaje previo dificulta el diagnóstico en CI/CD. El usuario/operador no sabe qué falló.

**❌ Incorrecto:**
```python
sys.exit(1)
```

**✅ Correcto:**
```python
print("ERROR: no se encontró config.json", file=sys.stderr)
sys.exit(1)
```

---

### `BAGO-I002` — TODO/FIXME/HACK comment

**Severidad:** 🔵 `info`  
**Categoría:** Mantenibilidad  
**Fuente:** `bago`  
**Suprimir:** `# noqa: BAGO-I002`


Comentarios `TODO`, `FIXME` o `HACK` son deuda técnica visible. Documenta en un ticket y elimina el comentario o conviértelo en un issue rastreable.

**❌ Incorrecto:**
```python
# TODO: manejar el caso de archivo vacío
```

**✅ Correcto:**
```python
# Ver issue #123: manejar archivo vacío
```

---


## JS/TS (ast-scan)

### `JS-E001` — eval() / Function() constructor

**Severidad:** 🔴 `error`  
**Categoría:** Seguridad  
**Fuente:** `js_ast`  
**Suprimir:** `# noqa: JS-E001`


`eval()` y `new Function(string)` ejecutan JavaScript arbitrario en tiempo de ejecución. Equivalente a RCE si la cadena viene de una fuente externa.

**❌ Incorrecto:**
```js
const fn = new Function('return ' + userInput);
```

**✅ Correcto:**
```js
// Parsea JSON con JSON.parse(), usa funciones estáticas
```

---

### `JS-W001` — console.log() en código de producción

**Severidad:** 🟡 `warning`  
**Categoría:** Mantenibilidad  
**Fuente:** `js_ast`  
**Suprimir:** `# noqa: JS-W001`


Las llamadas a `console.log/debug/error` exponen información interna en producción. Usa un logger configurable.

**❌ Incorrecto:**
```js
console.log('Usuario:', user.id);
```

**✅ Correcto:**
```js
logger.debug('Usuario:', user.id);
```

---

### `JS-W002` — debugger statement

**Severidad:** 🟡 `warning`  
**Categoría:** Mantenibilidad  
**Fuente:** `js_ast`  
**Suprimir:** `# noqa: JS-W002`


La sentencia `debugger` pausa la ejecución en DevTools. Olvidarla en producción degrada la experiencia del usuario.

**❌ Incorrecto:**
```js
debugger;
```

**✅ Correcto:**
```js
// Eliminar antes del commit
```

---

### `JS-W003` — Loose equality == / !=

**Severidad:** 🟡 `warning`  
**Categoría:** Fiabilidad  
**Fuente:** `js_ast`  
**Suprimir:** `# noqa: JS-W003`


`==` aplica coerción de tipos (`'' == false // true`). Esto produce bugs sutiles. Usa siempre `===` y `!==`.

**❌ Incorrecto:**
```js
if (value == null) return;
```

**✅ Correcto:**
```js
if (value === null || value === undefined) return;
```

---

### `JS-W004` — setTimeout/setInterval con string

**Severidad:** 🟡 `warning`  
**Categoría:** Seguridad  
**Fuente:** `js_ast`  
**Suprimir:** `# noqa: JS-W004`


Pasar una cadena como primer argumento a `setTimeout` o `setInterval` es equivalente a `eval()` y comparte sus riesgos.

**❌ Incorrecto:**
```js
setTimeout("doSomething()", 100);
```

**✅ Correcto:**
```js
setTimeout(() => doSomething(), 100);
```

---

### `JS-W005` — Empty catch block

**Severidad:** 🟡 `warning`  
**Categoría:** Fiabilidad  
**Fuente:** `js_ast`  
**Suprimir:** `# noqa: JS-W005`


Un bloque `catch {}` vacío silencia errores completamente. Al menos loguea el error para facilitar el diagnóstico.

**❌ Incorrecto:**
```js
try { risky(); } catch (e) {}
```

**✅ Correcto:**
```js
try { risky(); } catch (e) { logger.error(e); }
```

---

### `JS-I001` — TODO/FIXME comment

**Severidad:** 🔵 `info`  
**Categoría:** Mantenibilidad  
**Fuente:** `js_ast`  
**Suprimir:** `# noqa: JS-I001`


Comentario de deuda técnica. Ver BAGO-I002 para guía.

**❌ Incorrecto:**
```js
// TODO: refactorizar esta función
```

**✅ Correcto:**
```js
// Ver issue #456
```

---

### `JS-I002` — Arrow function con >5 parámetros

**Severidad:** 🔵 `info`  
**Categoría:** Mantenibilidad  
**Fuente:** `js_ast`  
**Suprimir:** `# noqa: JS-I002`


Las arrow functions con muchos parámetros son difíciles de leer y testear. Considera agrupar parámetros en un objeto.

**❌ Incorrecto:**
```js
const fn = (a, b, c, d, e, f) => a + b;
```

**✅ Correcto:**
```js
const fn = ({ a, b, c, d, e, f }) => a + b;
```

---

### `JS-I003` — Ternario anidado

**Severidad:** 🔵 `info`  
**Categoría:** Mantenibilidad  
**Fuente:** `js_ast`  
**Suprimir:** `# noqa: JS-I003`


Los ternarios anidados (`a ? b : c ? d : e`) son difíciles de leer. Usa `if/else` o un `switch`.

**❌ Incorrecto:**
```js
const x = a ? b : c ? d : e;
```

**✅ Correcto:**
```js
let x;
if (a) { x = b; } else if (c) { x = d; } else { x = e; }
```

---

### `JS-I004` — Async function sin await

**Severidad:** 🔵 `info`  
**Categoría:** Mantenibilidad  
**Fuente:** `js_ast`  
**Suprimir:** `# noqa: JS-I004`


Una función marcada `async` que no contiene `await` es engañosa — devuelve una Promise innecesariamente.

**❌ Incorrecto:**
```js
async function getUser() { return db.find(id); }
```

**✅ Correcto:**
```js
function getUser() { return db.find(id); }
```

---
