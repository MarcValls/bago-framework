# AGENTS vs ROLES — Comparativa Arquitectónica

## Contexto

BAGO implementa **dos tipos de especialistas**:

1. **AGENTS** — Para análisis técnico (code quality)
2. **ROLES** — Para gobernanza (decisiones)

Ambos usan **Factory Pattern** pero son complementarios.

---

## 📊 Comparativa Detallada

### AGENTS (Auditoría de Código)

| Aspecto | Detalle |
|---------|---------|
| **Propósito** | Analizar, auditar, verificar artefactos técnicos |
| **Cuándo actúan** | Cuando hay código/artefacto para revisar |
| **Quién los crea** | `agent_factory.py` (factory) |
| **Dónde viven** | `.bago/agents/` |
| **Cómo funcionan** | subprocess + JSON (aislados) |
| **Coordinación** | Paralelo (ThreadPoolExecutor, max 4 workers) |
| **Input** | Código, archivos, paths |
| **Output** | Hallazgos JSON (issues, warnings, info) |
| **Registro** | `.bago/agents/manifest.json` |
| **Timeout** | Configurable por agent |
| **Ejemplos** | security_analyzer, logic_checker, smell_detector |
| **Extensión** | factory → create agent → deploy permanente |

### ROLES (Gobernanza)

| Aspecto | Detalle |
|---------|---------|
| **Propósito** | Decidir, supervisar, gobernar proceso |
| **Cuándo actúan** | En cualquier punto del ciclo de vida |
| **Quién los crea** | `role_factory.py` (factory) |
| **Dónde viven** | `.bago/roles/{family}/` |
| **Cómo funcionan** | Documentos MD + lógica BAGO |
| **Coordinación** | Secuencial/gobernanza (consulta cuando necesario) |
| **Input** | Contexto, decisiones, criterios |
| **Output** | Veredictos, decisiones, recomendaciones |
| **Registro** | `.bago/roles/manifest.json` |
| **Validación** | Estructura MD (obligatorias 10 secciones) |
| **Ejemplos** | MAESTRO_BAGO, REVISOR_SEGURIDAD, ORQUESTADOR |
| **Extensión** | factory → template → edit MD → validate |

---

## 🔄 Ciclo de Vida

### AGENT Lifecycle

```
1. CREATION (on-demand)
   └─ user requests analysis
      └─ agent_factory.py checks manifest
         ├─ exists? → use existing
         └─ missing? → generate from template

2. DEPLOYMENT
   └─ agent file stored in .bago/agents/
   └─ entry added to manifest.json

3. EXECUTION (during analysis)
   └─ code_quality_orchestrator.py
      ├─ verify agents exist (auto-create if needed)
      ├─ launch in parallel (ThreadPoolExecutor)
      ├─ capture JSON output
      └─ aggregate findings

4. PERSISTENCE
   └─ agent code remains in .bago/agents/
   └─ reused in subsequent runs
   └─ can be deleted/replaced via factory CLI
```

### ROLE Lifecycle

```
1. CREATION (on-demand)
   └─ user requests new governance capability
      └─ role_factory.py template generates
         └─ structure with 10 required sections

2. DEFINITION
   └─ human edits .bago/roles/{family}/{ROLE_NAME}.md
   └─ fills propósito, alcance, límites, etc
   └─ validates with role_factory.py validate

3. REGISTRATION
   └─ entry added to manifest.json
   └─ status marked "active"

4. CONSULTATION (during workflow)
   └─ BAGO queries manifest
   └─ loads role definition
   └─ applies role's rules/criteria
   └─ references role in decision-making

5. PERSISTENCE
   └─ role document remains in .bago/roles/
   └─ versioned (2.5-stable, etc)
   └─ can be updated/deprecated via manifest
```

---

## 🛠️ Factory Pattern — Paralelo

### agent_factory.py

```python
# Crear agent bajo demanda
agent = factory.get_or_create_agent(
    name="performance_analyzer",
    category="performance",
    rules=["detect_n_plus_one", "memory_leaks", ...]
)

# Resultado: agent ejecutable como subprocess
result = subprocess.run(["python", agent], ...)
```

### role_factory.py

```python
# Crear rol bajo demanda
role = factory.create(
    family="especialistas",
    name="performance_auditor"
)

# Resultado: .bago/roles/especialistas/PERFORMANCE_AUDITOR.md
# con estructura estándar lista para editar
```

---

## 🔗 Integración en Workflows

### Workflow 1: Code Quality Analysis

```
User Input: "bago code-quality ."
    ↓
code_quality_orchestrator (AGENT COORDINATOR)
    ├─ [AGENT] security_analyzer
    │   └─ output: vulnerabilities JSON
    ├─ [AGENT] logic_checker
    │   └─ output: logic errors JSON
    ├─ [AGENT] smell_detector
    │   └─ output: code smells JSON
    ├─ [AGENT] duplication_finder
    │   └─ output: duplication JSON
    ├─ Synthesize all findings
    ├─ [ROLE] Consult MAESTRO_BAGO
    │   ├─ read: gobierno/MAESTRO_BAGO.md
    │   └─ apply: entradas/salidas rules
    └─ Return: integrated report to user
```

### Workflow 2: Custom Agent Creation

```
User Input: "bago code-quality --new-agent performance_detector"
    ↓
agent_factory.py create
    ├─ generate from AGENT_TEMPLATE
    ├─ save to .bago/agents/performance_detector.py
    ├─ update manifest.json
    └─ mark as "pending_test"
    ↓
[ready for execution in next code-quality run]
```

### Workflow 3: Custom Role Creation

```
User Input: "python role_factory.py create --family especialistas --name ml_validator"
    ↓
role_factory.py create
    ├─ generate .bago/roles/especialistas/ML_VALIDATOR.md
    ├─ update manifest.json
    └─ mark as "active"
    ↓
User edits: ML_VALIDATOR.md (10 sections)
    ↓
role_factory.py validate
    ├─ check all 10 sections present
    └─ mark as "validated"
    ↓
[ready for BAGO consultation in governance workflows]
```

---

## 📈 Escalabilidad

### Adding New Technical Analysis

**Before Factory:** Modify orchestrator code, add monolithic analyzer

**After Factory (Agent):**
```bash
python agent_factory.py create --category "security_ssl"
# Automatically:
# - generates agent scaffold
# - adds to manifest
# - ready to use in next run
```

### Adding New Governance Capability

**Before Factory:** Create new role file manually, no consistency

**After Factory (Role):**
```bash
python role_factory.py create --family supervision --name audit_compliance
nano .bago/roles/supervision/AUDIT_COMPLIANCE.md
# Factory ensures:
# - structure consistency
# - all sections present
# - manifest tracking
# - validation support
```

---

## 🎯 Key Differences in Practice

### When Agents Execute

```bash
$ bago code-quality .
    ↓
[AGENTS IN PARALLEL]
security_analyzer.py ───→ (subprocess) ───→ JSON output
logic_checker.py ───────→ (subprocess) ───→ JSON output
smell_detector.py ──────→ (subprocess) ───→ JSON output
duplication_finder.py ──→ (subprocess) ───→ JSON output
    ↓
[AGGREGATION]
orchestrator synthesizes → human report
```

### When Roles Execute

```bash
$ bago analyze-with-governance .
    ↓
[ROLE CONSULTATION - Sequential/On-Demand]
1. Check ORQUESTADOR_CENTRAL role
   └─ decide which agents to run
2. Run selected agents [PARALLEL]
3. Check REVISOR_SEGURIDAD role
   └─ if security findings exist, apply rules
4. Check MAESTRO_BAGO role
   └─ format and present final output
    ↓
[SYNTHESIS]
maestro integrates → user-facing output
```

---

## 💾 Manifest Structure Comparison

### agents/manifest.json

```json
{
  "agents": {
    "security_analyzer": {
      "category": "security",
      "rules": 5,
      "created": "...",
      "status": "active"
    }
  }
}
```

### roles/manifest.json

```json
{
  "roles": {
    "role_government_maestro_bago": {
      "family": "gobierno",
      "name": "maestro_bago",
      "file": "gobierno/MAESTRO_BAGO.md",
      "status": "active",
      "version": "2.5-stable"
    }
  },
  "families": {...}
}
```

---

## 🔀 Decision Tree

### When to Create an AGENT

- Need to **analyze/audit code**
- Want **subprocess isolation**
- Need **parallel execution**
- Output is **JSON/structured findings**
- Examples: security, performance, linting

### When to Create a ROLE

- Need to **govern/decide**
- Need **governance rules**
- Output is **decision/policy**
- Consulted **in workflow logic**
- Examples: maestro, revisor, supervisor

### When to Create BOTH

- Complex workflow where:
  - **AGENTS** do technical analysis (code)
  - **ROLES** decide next steps (governance)
  
Example:
```
PR submission
  ├─ [AGENTS] analyze code quality
  ├─ [ROLES] REVISOR_SEGURIDAD decides if security OK
  ├─ [AGENTS] if not OK, run security_analyzer deep dive
  └─ [ROLES] MAESTRO_BAGO decides: merge/hold/reject
```

---

## 🎓 Conclusión

| Aspecto | AGENTS | ROLES |
|---------|--------|-------|
| **Naturaleza** | Especialistas técnicos | Especialistas de gobernanza |
| **Cómo funcionan** | Subprocess (JSON) | Documentos (MD) + lógica |
| **Cuándo se crean** | Bajo demanda (análisis) | Bajo demanda (gobierno) |
| **Cuándo se ejecutan** | En paralelo (rápido) | Secuencial (consulta) |
| **Dónde se usan** | code_quality_orchestrator | rol_orchestrator (próx) |
| **Extensibilidad** | Nueva categoría = nuevo agent | Nueva familia = nuevos roles |
| **Versionado** | v1, v2, etc (por agent) | 2.5-stable (global) |

**Ambos implementan Factory Pattern para escalabilidad y reutilización.**

---

**Document Version:** 1.0  
**Date:** 2026-04-28  
**BAGO Version:** 2.5-stable
