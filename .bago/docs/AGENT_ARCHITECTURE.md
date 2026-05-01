# BAGO: Gestor Dinámico de Agentes Especializados

**El verdadero principio de BAGO: SI NO EXISTE UN ESPECIALISTA → LO CREA**

## Arquitectura

```
Usuario solicita: "bago code-quality ."
                     ↓
        code_quality_orchestrator.py (LÍDER)
                     ↓
    ¿Existen 4 agentes especializados?
    ├─ security_analyzer ✓
    ├─ logic_checker ✓
    ├─ smell_detector ✓
    └─ duplication_finder ✓
    
    SI FALTA ALGUNO:
    ├─ agent_factory.py lo CREA dinámicamente
    ├─ Lo guarda permanentemente en .bago/agents/
    └─ Lo registra en manifest.json
    
    Luego:
    ├─ Ejecuta 4 agentes EN PARALELO
    ├─ Espera resultados (async)
    ├─ Sintetiza hallazgos
    ├─ Prioriza por severidad
    └─ Retorna reporte unificado
```

## Componentes

### 1. Agent Factory (agent_factory.py)
**La fábrica que GENERA agentes bajo demanda**

```python
# Crea un agente dinámicamente
factory.create_agent(
    name="performance_checker",
    category="performance",
    description="Detecta problemas de performance",
    rules=["long_loops", "inefficient_patterns", "memory_leaks"]
)
```

Características:
- Template universal (código boilerplate automático)
- Genera clase Python estándar
- Guarda permanentemente
- Registra en manifest
- Reutilizable en próximas ejecuciones

### 2. Agentes Especializados Base
Cada agente es un especialista en 1 área:

- **security_analyzer.py** — Vulnerabilidades (SQL injection, hardcoded secrets)
- **logic_checker.py** — Errores lógicos (bare except, bad comparisons)
- **smell_detector.py** — Code smells (funciones largas, complejidad)
- **duplication_finder.py** — Código duplicado (imports, constantes)

### 3. Orquestador (code_quality_orchestrator.py)
**El líder que coordina todo**

Responsabilidades:
1. Recibe solicitud (target directory)
2. Asegura que existan todos los agentes (crea si faltan)
3. Ejecuta en paralelo (subprocess)
4. Espera resultados (async)
5. Sintetiza hallazgos
6. Prioriza por severidad
7. Genera recomendaciones
8. Retorna reporte JSON

## Patrón BAGO: "Generar bajo demanda"

### Caso 1: Agentes ya existen
```bash
$ bago code-quality .

🎯 BAGO Code Quality Orchestrator

⚙️  Fase 1: Verificando especialistas...
  ✓ security_analyzer (existe)
  ✓ logic_checker (existe)
  ✓ smell_detector (existe)
  ✓ duplication_finder (existe)

🚀 Fase 2: Lanzando agentes...
  ✓ security_analyzer         (3 hallazgos)
  ✓ logic_checker             (5 hallazgos)
  ✓ smell_detector            (8 hallazgos)
  ✓ duplication_finder        (2 hallazgos)
```

### Caso 2: Faltan agentes → BAGO los CREA
```bash
$ bago code-quality .

⚙️  Fase 1: Verificando especialistas...
  ⚠️  security_analyzer no existe
  📦 Generando bajo demanda: security_analyzer... ✅
  
  ⚠️  logic_checker no existe
  📦 Generando bajo demanda: logic_checker... ✅
  
[continúa normalmente]
```

### Caso 3: Usuario solicita NUEVO especialista
```bash
$ python .bago/agents/agent_factory.py create \
  performance_analyzer \
  performance \
  "Check performance bottlenecks" \
  "long_loops" "inefficient_patterns" "high_memory"

✅ Agente creado: performance_analyzer
📝 Registrado en manifest: performance_analyzer
```

## Flujo de Ejecución

### Phase 1: Verificación
```
¿Existen todos los agentes necesarios?
├─ security_analyzer.py ✓
├─ logic_checker.py ✓
├─ smell_detector.py ✓
└─ duplication_finder.py ✓

Si alguno falta:
└─ Factory lo crea (template + reglas)
```

### Phase 2: Ejecución Paralela
```
Lanzar simultaneamente:
├─ security_analyzer . → subprocess → JSON
├─ logic_checker . → subprocess → JSON
├─ smell_detector . → subprocess → JSON
└─ duplication_finder . → subprocess → JSON

Esperar con ThreadPoolExecutor (4 workers)
```

### Phase 3: Síntesis
```
Recolectar todos los hallazgos:
├─ Clasificar por severidad (critical, warning, info)
├─ Agrupar por tipo (SEC, BUG, SMELL, DUP)
├─ Top 5 por categoría
└─ Generar recomendaciones
```

## Uso

### Ejecución Básica
```bash
cd C:\Marc_max_20gb
bago code-quality .
```

Output:
```
🎯 BAGO Code Quality Orchestrator
⚙️  Fase 1: Verificando especialistas...
🚀 Fase 2: Lanzando agentes...
📊 Fase 3: Síntesis de Hallazgos

🔴 CRÍTICO (3)
   [SEC-W002] auth.py:42 → Credencial hardcoded
   
🟡 WARNINGS (5)
   [LOGIC-E005] models.py:18 → Comparación innecesaria
   
ℹ️  INFO (8)
   [SMELL-I001] services.py:10 → Función demasiado larga

💡 Recomendaciones Prioritarias
1. 🔒 SEGURIDAD → Remover credenciales
2. 📦 REFACTOR → Reducir complejidad

✓ Análisis completado • Total: 16 hallazgos
```

### Generar Agente Nueva
```bash
python .bago/agents/agent_factory.py create \
  perf_analyzer \
  performance \
  "Detecta problemas de performance" \
  "long_loops" "inefficient_patterns"
```

### Listar Agentes Disponibles
```bash
python .bago/agents/agent_factory.py list
```

Output:
```
Agent                    Category       Rules  Status
───────────────────────────────────────────────────────
security_analyzer        security          5   active
logic_checker            logic             5   active
smell_detector           smell             5   active
duplication_finder       duplication       3   active
```

### Verificar Existencia
```bash
python .bago/agents/agent_factory.py exists performance_analyzer
✅ Existe: performance_analyzer
```

## Manifest de Agentes

Ubicación: `.bago/agents/manifest.json`

```json
{
  "agents": {
    "security_analyzer": {
      "category": "security",
      "description": "Detecta vulnerabilidades",
      "rules": 5,
      "created": "2026-04-28T04:50:00+00:00",
      "status": "active"
    },
    "logic_checker": {
      "category": "logic",
      "description": "Detecta errores lógicos",
      "rules": 5,
      "created": "2026-04-28T04:50:00+00:00",
      "status": "active"
    }
  },
  "created": "2026-04-28T04:50:00+00:00"
}
```

## Extensibilidad

### Agregar Nuevo Dominio
```bash
# 1. Factory crea agente
python .bago/agents/agent_factory.py create \
  accessibility_checker \
  accessibility \
  "Detecta problemas de accesibilidad" \
  "missing_alt_text" "low_contrast" "poor_semantics"

# 2. Actualizar orquestador (OPCIONAL - auto-descubre)
# El orquestador escanea .bago/agents/ y lista en manifest

# 3. Usar automáticamente
bago code-quality .
```

### Cambiar Reglas
```bash
# Editar .bago/agents/security_analyzer.py
# → Agregar nuevas reglas al checker
# → Próxima ejecución usa versión actualizada
```

## Ventajas

✅ **Escalabilidad:** Factory genera bajo demanda  
✅ **Reutilización:** Agentes persistentes  
✅ **Mantenibilidad:** Cada agente = 1 dominio  
✅ **Adaptabilidad:** BAGO aprende nuevos dominios  
✅ **Paralelismo:** Análisis 4x más rápido  
✅ **Extensibilidad:** Template = fácil crear nuevos  
✅ **Sin Acoplamiento:** Agentes independientes  

## PRINCIPIOS BAGO

1. **NO ejecutar:** BAGO ORQUESTA
2. **NO monolítico:** BAGO delega a especialistas
3. **NO estático:** BAGO genera bajo demanda
4. **Especialización:** Cada agente = 1 tarea
5. **Autonomía:** Agentes independientes
6. **Persistencia:** Agentes reutilizables
7. **Paralelismo:** Máximo aprovechamiento

---

**Versión:** 1.0  
**Patrón:** Agent Factory + Orchestrator  
**Estado:** Production Ready  
**Actualizado:** 2026-04-28
