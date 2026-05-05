# BAGO Bug Detection Suite

**Herramientas para detección integral de errores, duplicaciones y code smells**

## Herramientas

### 1. bug_detector.py — Detección de Bugs

Detecta errores lógicos, problemas de seguridad y code smells en código Python.

#### Categorías de Errores

**BUG (Errores Lógicos):**
- `BUG-E001` — Variable usada sin inicialización
- `BUG-E002` — Función sin return en algunos caminos
- `BUG-E003` — Dead code (statements después de return/raise)
- `BUG-E004` — Bare except (captura de excepción genérica)
- `BUG-E005` — Comparación innecesaria con True/False

**SEC (Problemas de Seguridad):**
- `SEC-W001` — Posible SQL injection
- `SEC-W002` — Credenciales hardcoded (passwords, tokens, keys)
- `SEC-W003` — Comando shell construido dinámicamente
- `SEC-W004` — Uso de `eval()` o `exec()`
- `SEC-W005` — Uso de `pickle.loads()` sin validación

**SMELL (Code Smells):**
- `SMELL-I001` — Función > 50 líneas (demasiado larga)
- `SMELL-I002` — Función > 5 parámetros (demasiados)
- `SMELL-I003` — Complejidad ciclomática > 10
- `SMELL-I004` — Múltiples niveles de anidamiento (>4)
- `SMELL-W001` — Variable no usada
- `SMELL-W002` — Función nunca llamada (privada)

#### Uso

```bash
# Analizar directorio actual
bago bug-detector

# Analizar archivo específico
bago bug-detector src/auth.py

# Solo warnings (no info)
bago bug-detector --severity warning

# Generar reporte JSON
bago bug-detector --format json --out report.json

# Ignorar reglas específicas
bago bug-detector --ignore BUG-E005,SMELL-I001
```

#### Formato de Salida

**Texto (default):**
```
Bug Detector — 8 hallazgo(s)

⚠️  Warnings (5)
  [SEC-W002] auth.py:42  Posible credencial hardcoded en 'password'
  [BUG-E005] models.py:18  Comparación innecesaria con False
  [SEC-W001] queries.py:35  Posible SQL injection
  
ℹ️  Info (3)
  [SMELL-I001] services.py:10  Función 'process_data' demasiado larga (120 líneas)
  [SMELL-I002] handlers.py:5  Función 'handle' tiene 8 parámetros (>5)
```

**JSON:**
```json
[
  {
    "rule": "SEC-W002",
    "severity": "warning",
    "file": "src/auth.py",
    "line": 42,
    "message": "Posible credencial hardcoded en 'password'"
  }
]
```

---

### 2. duplication_checker.py — Detección de Duplicaciones

Encuentra código duplicado, funciones similares e imports redundantes.

#### Categorías

- `DUP-W001` — Función casi idéntica a otra (similarity > 90%)
- `DUP-W002` — Bloque de código duplicado
- `DUP-I001` — Imports duplicados o redundantes
- `DUP-I002` — Constantes duplicadas

#### Uso

```bash
# Analizar directorio
bago duplication-checker

# Con threshold personalizado (default 90%)
bago duplication-checker --threshold 85

# Generar reporte Markdown
bago duplication-checker --format md --out duplicates.md

# Archivo específico
bago duplication-checker src/models.py
```

#### Ejemplos de Detección

**Funciones Similares:**
```
[DUP-W001] handlers.py:15  Función 'handle_user_creation' 
           es 95% similar a 'handle_user_update' en handlers.py:45
```

**Imports Duplicados:**
```
[DUP-I001] utils.py:2  Import duplicado: 'from os import path'
```

**Constantes Duplicadas:**
```
[DUP-I002] config.py:10  Constante duplicada: 'timeout=30' 
           (también en settings.py:45)
```

---

## Integración con bago audit

Los bugs y duplicaciones se incluyen automáticamente en `bago audit`:

```bash
bago audit
```

Mostrará:
- [3] INTEGRIDAD
- [4] BUGS & SMELLS
- [5] DUPLICACIONES
- etc.

---

## Workflow de Corrección

### Paso 1: Ejecutar Detección
```bash
cd repos/my-repo
bago bug-detector --format json --out bugs.json
bago duplication-checker --format json --out dups.json
```

### Paso 2: Revisar Hallazgos
```bash
# Warnings prioritarios (seguridad, errores)
bago bug-detector --severity warning

# Duplicaciones que frenan velocidad
bago duplication-checker --threshold 95
```

### Paso 3: Refactor
```bash
# Editar archivos para:
# - Remover credenciales hardcoded
# - Consolidar funciones similares
# - Eliminar imports redundantes
# - Reducir complejidad
```

### Paso 4: Verificar Corrección
```bash
bago bug-detector
# → Debería mostrar menos hallazgos
```

---

## Casos de Uso

### 1. Auditoría de Seguridad
```bash
bago bug-detector --severity warning --ignore SMELL-I001,SMELL-I002
```
Muestra solo warnings (seguridad, errores), sin code smells informativos.

### 2. Detección de Refactor Oportunidades
```bash
bago duplication-checker --threshold 80
```
Encuentra código altamente similar que debería consolidarse.

### 3. Quality Gate (CI/CD)
```bash
bago bug-detector
if [ $? -eq 0 ]; then
  echo "✓ Código sin bugs detectados"
fi
```

### 4. Code Review Assistant
```bash
# Generar reporte antes de PR
bago bug-detector --format md --out CODE_QUALITY.md
```
Adjunta el reporte a la PR para revisar.

---

## Reglas Configurables

### Ignorar Reglas
```bash
# Una regla
bago bug-detector --ignore BUG-E005

# Múltiples reglas
bago bug-detector --ignore BUG-E005,SMELL-I001,SMELL-I002
```

### Filtrar por Severidad
```bash
# Solo warnings
bago bug-detector --severity warning

# Solo informativo
bago duplication-checker --severity info
```

### Threshold de Similitud
```bash
# Detectar solo muy similares (95%+)
bago duplication-checker --threshold 95

# Detectar también parcialmente similares
bago duplication-checker --threshold 70
```

---

## Limitaciones & Notas

### Soportado
- ✅ Python 3.7+
- ✅ Análisis estático (sin ejecución)
- ✅ Detecta patrones comunes de bugs
- ✅ Detección de duplicaciones con threshold configurable

### No Soportado (yet)
- ❌ JavaScript/TypeScript (solo Python)
- ❌ Análisis de runtime
- ❌ Type inference con mypy
- ❌ CFG (Control Flow Graph) avanzado

### Falsos Positivos
- Algunos "bugs" pueden ser intencionales (ej: bare except en REPL)
- La detección de inyección es pattern-based; requiere revisión manual para falsos positivos
- Funciones similares pueden ser patrones legítimos

**Mitigation:** Usa `--ignore` para suprimir falsos positivos en tu contexto.

---

## Ejemplos de Salida

### Ejemplo 1: Reporte Completo
```bash
$ bago bug-detector

═══ Bug Detector ═══════════════════════════════════════════
Analizando: . (1,234 archivos Python)

[SEC] Problemas de Seguridad (3)
  ✗ SEC-W002  auth.py:42     Credencial hardcoded: 'api_key'
  ✗ SEC-W001  database.py:18 Posible SQL injection en query
  
[BUG] Errores Lógicos (2)
  ✗ BUG-E005  models.py:95   Comparación innecesaria con True
  ✗ BUG-E004  handlers.py:12 Bare except (especifica tipo)

[SMELL] Code Smells (5)
  ℹ SMELL-I001 services.py:10  Función 'sync_users' demasiado larga (180 líneas)
  ℹ SMELL-I002 api.py:5        Función 'process' con 9 parámetros
  
═══════════════════════════════════════════════════════════
Hallazgos: 10 (3 warnings, 7 info)
Severidad: 3 críticas (SEC), 2 errores, 5 info

Recomendaciones:
  1. Remover credenciales → usar variables de entorno
  2. Usar prepared statements para SQL
  3. Reducir complejidad de sync_users
```

### Ejemplo 2: Duplicaciones
```bash
$ bago duplication-checker

═══ Duplication Checker ═════════════════════════════════════

[DUP-W001] handlers.py:15
  'handle_user_create' 95% similar a 'handle_user_update' (handlers.py:45)
  → Consolidar en función genérica

[DUP-W001] models.py:102
  'save_to_db' 88% similar a 'update_in_db' (queries.py:34)
  → Refactor a repositorio común

[DUP-I001] config.py:2
  Import duplicado: 'from os import path'

[DUP-I002] constants.py:10
  Constante duplicada: 'TIMEOUT=300' (también en defaults.py:45)

═══════════════════════════════════════════════════════════
Total: 4 duplicaciones (threshold: 90%, 1 critical refactor)
```

---

## Testing

Ambas herramientas incluyen tests internos:

```bash
bago bug-detector --test
bago duplication-checker --test
```

---

## Ver También

- `bago audit` — Auditoría completa del proyecto
- `bago type-check` — Validación de type hints
- `bago naming-check` — Validación de convenciones de nombres
- `bago research` — Investigación de patrones específicos

---

**Versión:** 1.0  
**Actualizado:** 2026-04-28  
**Mantenedor:** BAGO Framework
