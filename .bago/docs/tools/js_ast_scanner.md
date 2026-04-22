# `js_ast_scanner.js` — Linter AST para JavaScript/TypeScript

**Command:** invocado por `bago multi-scan` y `bago scan`
**File:** `.bago/tools/js_ast_scanner.js`
**Category:** Análisis estático — JS/TS
**Tool #:** 93

## Description

`js_ast_scanner.js` es un linter AST (Abstract Syntax Tree) para JavaScript y TypeScript basado en la librería `acorn`. Al analizar el árbol sintáctico en lugar de aplicar regex sobre texto plano, detecta patrones con precisión quirúrgica: no hay falsos positivos por strings que contienen keywords, ni falsos negativos por código ofuscado.

Implementa 10 reglas organizadas en tres severidades. Soporta supresión de reglas con `// noqa: JS-RULE` en la línea afectada (o `// noqa` para suprimir todas) y distingue automáticamente archivos de test (`.test.js`, `.spec.js`, `__tests__/`) para no reportar `console.log` en ellos.

Para TypeScript, el scanner aplica un strip básico de anotaciones de tipo antes del parseo con acorn, permitiendo analizar `.ts`/`.tsx` sin el compilador TypeScript completo. Archivos con sintaxis TS compleja que no se puedan parsear se saltan silenciosamente. Excluye directorios `node_modules/`, `dist/` y `build/` automáticamente.

## Usage

```bash
# Via BAGO (recomendado — integrado en multi-scan)
bago multi-scan --langs js

# Directo con Node.js
node .bago/tools/js_ast_scanner.js [path] [--json] [--summary] [--test]
```

## Options

| Flag | Descripción |
|------|-------------|
| `path` | Archivo o directorio a escanear (default: `.`) |
| `--json` | Output JSON estructurado |
| `--summary` | Solo resumen por regla |
| `--test` | Ejecutar self-tests y salir |

## Examples

```bash
# Escanear directorio src/
node .bago/tools/js_ast_scanner.js src/

# Output JSON para pipeline CI
node .bago/tools/js_ast_scanner.js . --json | node -e "const d=JSON.parse(require('fs').readFileSync('/dev/stdin','utf8')); console.log(d.filter(f=>f.severity==='error'))"

# Solo resumen
node .bago/tools/js_ast_scanner.js . --summary
```

## Dependencies

```bash
npm install acorn acorn-walk
```

Instalables también con `bago install-deps`.

## Rules detected

| Código | Severidad | Descripción |
|--------|-----------|-------------|
| `JS-E001` | 🔴 error | `eval()` / `Function()` constructor — riesgo RCE |
| `JS-W001` | 🟡 warning | `console.log/debug/error` en archivos no-test |
| `JS-W002` | 🟡 warning | Sentencia `debugger` |
| `JS-W003` | 🟡 warning | Operador `==` / `!=` (usar `===` / `!==`) |
| `JS-W004` | 🟡 warning | `setTimeout`/`setInterval` con string — eval implícito |
| `JS-W005` | 🟡 warning | Bloque `catch` vacío |
| `JS-I001` | 🔵 info | Comentarios TODO/FIXME/HACK |
| `JS-I002` | 🔵 info | Arrow function con >5 parámetros |
| `JS-I003` | 🔵 info | Ternario anidado |
| `JS-I004` | 🔵 info | Función `async` sin `await` |

## Noqa suppression

```js
const x = eval(code);  // noqa: JS-E001
console.log("debug");  // noqa
```

## Self-tests

```bash
node .bago/tools/js_ast_scanner.js --test
```

→ 10/10 tests pasan: `eval_detected`, `arrow_too_many_params`, `empty_catch`, `loose_equality`, `debugger`, `todo_comment`, `console_log`, `console_log_test_skip`, `noqa_suppression`, `collect_files_recursive`
