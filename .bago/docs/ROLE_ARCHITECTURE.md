# ROLE ARCHITECTURE — Estructura de Roles BAGO

## 🎯 Principio Fundamental

Así como **Agents son especialistas en código**, **Roles son especialistas en governance**.

```
┌─────────────────────────────────────────┐
│        BAGO — Arquitectura Dual         │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────────────────────────┐   │
│  │   AGENTS (Code Quality)          │   │
│  │  Ejecutan análisis + auditoría   │   │
│  │  - security_analyzer             │   │
│  │  - logic_checker                 │   │
│  │  - smell_detector                │   │
│  │  - duplication_finder            │   │
│  └──────────────────────────────────┘   │
│                                         │
│  ┌──────────────────────────────────┐   │
│  │   ROLES (Governance)             │   │
│  │  Deciden + supervisan proceso    │   │
│  │  - MAESTRO_BAGO (interfaz)       │   │
│  │  - REVISOR_SEGURIDAD (validación)│   │
│  │  - ORQUESTADOR (decisiones)      │   │
│  └──────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

---

## 📋 Familia de Roles

### 1. GOVERNMENT (Gobierno Central)

**Propósito:** Tomar decisiones, orquestar, ser interfaz.

```
✓ MAESTRO_BAGO
  - Interfaz principal con usuario
  - Presenta resultados integrados
  - Explica siguiente paso
  - Entrada: Decisiones del orquestador
  - Salida: Respuesta final clara

✓ ORQUESTADOR_CENTRAL
  - Coordina entre especialistas
  - Toma decisiones de flujo
  - Maneja excepciones
  - Entrada: Requisitos del usuario
  - Salida: Plan de ejecución
```

### 2. SPECIALIST (Especialistas)

**Propósito:** Análisis profundo en un dominio.

```
✓ REVISOR_SEGURIDAD
  - Evalúa riesgos de seguridad
  - Audita permisos, secretos, exposición
  - Entrada: Artefactos a revisar
  - Salida: Hallazgos de riesgo

✓ REVISOR_PERFORMANCE
  - Analiza rendimiento y latencia
  - Identifica cuellos de botella
  - Entrada: Código, métricas
  - Salida: Recomendaciones de optimización

✓ REVISOR_UX
  - Valida experiencia de usuario
  - Audita usabilidad
  - Entrada: Interfaz, flujos
  - Salida: Issues de UX

✓ INTEGRADOR_REPO
  - Maneja integración de cambios
  - Asegura coexistencia de código
  - Entrada: PRs, commits
  - Salida: Decisión merge
```

### 3. SUPERVISION (Supervisión)

**Propósito:** Verificación de calidad y cumplimiento.

```
(Roles a definir según necesidades)
  - Quality Verifier
  - Compliance Officer
  - Process Auditor
```

### 4. PRODUCTION (Producción)

**Propósito:** Operaciones y despliegue.

```
(Roles a definir según necesidades)
  - Deployment Manager
  - Incident Commander
  - Infrastructure Lead
```

---

## 🏭 Role Factory

Igual que `agent_factory.py`, existe `role_factory.py`:

```bash
# Crear rol nuevo
python role_factory.py create --family especialistas --name performance_analyzer

# Validar estructura
python role_factory.py validate .bago/roles/especialistas/PERFORMANCE_ANALYZER.md

# Listar roles
python role_factory.py list
python role_factory.py list --family gobierno

# Ver familias disponibles
python role_factory.py families
```

---

## 📄 Plantilla de Rol

**Archivo:** `.bago/roles/ROLE_TEMPLATE.md`

Estructura obligatoria:

```markdown
# {NOMBRE_ROL}

## Identidad
- id: role_{family}_{name}
- family: {government|specialist|supervision|production}
- version: 2.5-stable

## Propósito
Una frase clara: qué hace este rol

## Alcance
- Lista de responsabilidades

## Límites
- Explícitamente qué NO hace

## Entradas
- Qué recibe como input

## Salidas
- Qué produce como output

## Activación
Cuándo se DEBE activar

## No Activación
Cuándo se DEBE EVITAR

## Dependencias
Qué necesita para funcionar

## Criterio de Éxito
Cómo medir si funcionó bien
```

---

## 📊 Manifest de Roles

**Archivo:** `.bago/roles/manifest.json`

Registro centralizado de todos los roles:

```json
{
  "roles": {
    "role_government_maestro_bago": {
      "family": "gobierno",
      "name": "maestro_bago",
      "file": "gobierno/MAESTRO_BAGO.md",
      "created": "2026-04-28T00:00:00Z",
      "status": "active",
      "version": "2.5-stable"
    },
    ...
  },
  "families": {
    "gobierno": "GOVERNMENT — Gobierno central",
    "especialistas": "SPECIALIST — Análisis en dominio",
    ...
  }
}
```

---

## 🔄 Diferencia: Agents vs Roles

### AGENTS (Código)

```
Qué hacen:        Analizan, auditan, verifican artefactos
Cuándo actúan:    Cuando hay código para revisar
Cómo funcionan:   subprocess + JSON
Coordinación:     code_quality_orchestrator.py (paralelo)
Output:           Hallazgos técnicos, recomendaciones
Ejemplo:          security_analyzer.py → detecta vulnerabilidades
```

### ROLES (Governance)

```
Qué hacen:        Deciden, supervisan, gobiernan proceso
Cuándo actúan:    En cualquier momento del ciclo
Cómo funcionan:   Documentos (MD) + lógica de BAGO
Coordinación:     Especificada en cada rol
Output:           Decisiones, veredictos, cambios de estado
Ejemplo:          MAESTRO_BAGO → presenta resultados al usuario
```

---

## 📂 Estructura de Directorio

```
.bago/roles/
│
├── ROLE_TEMPLATE.md           ← Plantilla universal
├── role_factory.py            ← Factory para crear roles
├── manifest.json              ← Registro de roles
│
├── gobierno/
│   ├── MAESTRO_BAGO.md
│   └── ORQUESTADOR_CENTRAL.md
│
├── especialistas/
│   ├── REVISOR_SEGURIDAD.md
│   ├── REVISOR_PERFORMANCE.md
│   ├── REVISOR_UX.md
│   └── INTEGRADOR_REPO.md
│
├── supervision/
│   └── (a crear según necesidades)
│
└── produccion/
    └── (a crear según necesidades)
```

---

## 🚀 Workflow: Crear Rol Nuevo

### Paso 1: Usar factory

```bash
cd .bago/roles
python role_factory.py create --family especialistas --name code_style_enforcer
```

Output:
```
✅ Rol creado: especialistas/CODE_STYLE_ENFORCER.md
📝 Registrado en manifest
```

### Paso 2: Editar archivo

```bash
nano .bago/roles/especialistas/CODE_STYLE_ENFORCER.md
```

Rellenar secciones usando la plantilla.

### Paso 3: Validar

```bash
python role_factory.py validate .bago/roles/especialistas/CODE_STYLE_ENFORCER.md
```

Output:
```
✅ Rol válido: .bago/roles/especialistas/CODE_STYLE_ENFORCER.md
```

### Paso 4: Usar en BAGO

El rol está registrado automáticamente. BAGO puede:
- Consultar manifest.json
- Activarlo según contexto
- Usar sus reglas de decisión

---

## 🎬 Casos de Uso

### Caso 1: Crear especialista en Performance

```bash
# Factory crea archivo
python role_factory.py create \
  --family especialistas \
  --name performance_validator

# Editar para especificar:
# - Qué métricas revisa (latency, throughput, memory)
# - Cuándo se activa (en PRs que toquen código crítico)
# - Qué criterios usa (benchmarks, umbrales)
# - Cómo reporta (JSON + Markdown)

# Manifest registra automáticamente
# BAGO usa rol en siguiente análisis
```

### Caso 2: Crear supervisor de compliance

```bash
# Factory crea archivo
python role_factory.py create \
  --family supervision \
  --name compliance_verifier

# Especificar:
# - Leyes/estándares a verificar (GDPR, HIPAA, etc)
# - Documentación requerida
# - Auditoría automática
```

### Caso 3: Listar todos los roles

```bash
python role_factory.py list
```

Output:
```
ID                                       Family         Status
─────────────────────────────────────────────────────────────────
role_government_maestro_bago             gobierno       active
role_government_orquestador_central      gobierno       active
role_specialist_security_reviewer        especialistas  active
role_specialist_performance_reviewer     especialistas  active
...
```

---

## 🔗 Integración con BAGO

El sistema BAGO puede consultar roles de 3 maneras:

### 1. Por Familia
```python
# En bago script o tools
import json
manifest = json.load(open(".bago/roles/manifest.json"))
gobierno_roles = [r for r in manifest["roles"].values() 
                   if r["family"] == "gobierno"]
```

### 2. Por Nombre
```python
# Buscar rol específico
role = manifest["roles"].get("role_government_maestro_bago")
```

### 3. Por Status
```python
# Listar activos
active_roles = [r for r in manifest["roles"].values() 
                 if r["status"] == "active"]
```

---

## 🏁 Checklist para Rol Válido

- [ ] ID único: `role_{familia}_{nombre}`
- [ ] Familia correcta (gobierno|especialistas|supervision|produccion)
- [ ] Propósito claro en una frase
- [ ] Alcance específico (4-6 items)
- [ ] Límites explícitos
- [ ] Entradas definidas
- [ ] Salidas esperadas
- [ ] Activación clara
- [ ] No-activación clara
- [ ] Dependencias realistas
- [ ] Criterios de éxito medibles
- [ ] Version compatible (2.5-stable)

---

## 🎓 Ejemplo Completo: Rol de Performance

**Archivo:** `.bago/roles/especialistas/PERFORMANCE_VALIDATOR.md`

```markdown
# PERFORMANCE VALIDATOR

## Identidad
- id: role_specialist_performance_validator
- family: especialistas
- version: 2.5-stable

## Propósito
Validar que cambios de código no degradan rendimiento más allá de umbrales aceptables.

## Alcance
- Análisis de latencia endpoint
- Medición de uso de memoria
- Detección de N+1 queries
- Comparativa antes/después

## Límites
- No mide experiencia de usuario (lo hace REVISOR_UX)
- No audita infraestructura (lo hace equipo ops)
- Solo en cambios que tocan lógica crítica

## Entradas
- Código propuesto (PR)
- Baseline de performance actual
- Criterios de aceptación

## Salidas
- Reporte de benchmark comparativo
- Recomendaciones de optimización
- Veredicto: Aceptado / Revisar / Rechazado

## Activación
Cuando PR toca: queries, índices, loops, algoritmos complejos

## No Activación
No en PRs de documentación o typos

## Dependencias
- Acceso a ambiente de testing
- Datos históricos de performance
- Criterios de benchmark del proyecto

## Criterio de Éxito
Previene regressions de performance
```

---

## 📚 Más Información

- **ROLE_TEMPLATE.md** — Plantilla completa con ejemplos
- **role_factory.py** — Código de factory
- **manifest.json** — Registro de roles actuales

---

**Version:** 1.0  
**Status:** Active  
**Última actualización:** 2026-04-28
