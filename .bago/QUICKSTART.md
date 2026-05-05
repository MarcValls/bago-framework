# 🚀 BAGO QUICKSTART — Empieza Ahora en 30 segundos

## Opción 1: CLI Interactivo (RECOMENDADO)

```bash
cd C:\Marc_max_20gb
powershell -ExecutionPolicy Bypass -File .bago\cli.ps1
```

Verás un menú con opciones:
- ✅ Analizar código
- ✅ Crear AGENTS
- ✅ Crear ROLES
- ✅ Ver documentación

---

## Opción 2: Ejecutar en Tu Proyecto Directamente

```bash
powershell -ExecutionPolicy Bypass -File C:\Marc_max_20gb\.bago\bago_interactive_demo.ps1 `
  -ProjectPath "C:\Tu\Proyecto"
```

Resultado:
- 📊 Issues detectados
- 🎯 Veredictos de ROLES
- 💡 Recomendaciones

---

## Opción 3: Ver Demo Nuevamente

```bash
cd C:\Marc_max_20gb
powershell -ExecutionPolicy Bypass -File .bago\bago_interactive_demo.ps1
```

Analiza `typing-course/` automáticamente.

---

## Opción 4: Leer Documentación

```bash
# Ver índice completo
type .bago\INDEX.md

# Ver resultados de demo
type .bago\DEMO_RESULTS.md

# Ver guía de uso
type .bago\GUIDE_HOW_TO_USE.md
```

---

## 🎯 Lo que BAGO hace

Para **cada proyecto** que analices:

### 1️⃣ AGENTS (Análisis en Paralelo)

| Agent | Detecta |
|-------|---------|
| 🔒 Security | Vulnerabilidades XSS, HTTP inseguro, secrets |
| ⚙️ Logic | TODOs, inconsistencias, null checks |
| 👃 Smells | Global variables, funciones largas |
| 🔍 Duplication | Código duplicado, lógica repetida |

### 2️⃣ ROLES (Gobierno)

| Role | Decide |
|------|--------|
| 🛡️ REVISOR_SEGURIDAD | ¿Es seguro? |
| ⚡ REVISOR_PERFORMANCE | ¿Es eficiente? |
| 👑 MAESTRO_BAGO | ¿Listo para producción? |

### 3️⃣ Reporte

- ✅ Hallazgos categorizados
- 🎯 Veredictos de cada rol
- 💡 Recomendaciones prioritarias
- 🚀 Próximos pasos

---

## 📊 Ejemplo Real: Typing Course

```
Input:  src/lesson.js (1 archivo, 1.8 KB)

AGENTS:
  🔒 Security: 2 issues
  ⚙️ Logic: 1 issue
  👃 Smells: 1 issue
  🔍 Duplication: 1 issue

ROLES:
  🛡️ REVISOR_SEGURIDAD: ACCEPTED ✅
  ⚡ REVISOR_PERFORMANCE: REVIEW NEEDED 🟡
  👑 MAESTRO_BAGO: NOT READY 🔴

Output: Recommendations + Próximos pasos
```

---

## 💡 Tips

1. **Ejecuta frecuentemente**
   - Después de cada feature
   - Antes de cada PR
   - Después de refactoring

2. **Lee recomendaciones**
   - Está detectando problemas reales
   - Impactarán tu código

3. **Itera**
   - Implementa cambios
   - Re-ejecuta BAGO
   - Repite hasta READY

4. **Personaliza**
   - Crea nuevos AGENTS
   - Crea nuevos ROLES
   - Adapta a tu equipo

---

## ❓ Qué Necesitas

- ✅ Windows (PowerShell)
- ✅ Proyecto con código (.js, .ts, .py, etc)
- ✅ Nada más (Python opcional)

---

## 🎓 Próximos Pasos

1. Ejecuta CLI: `powershell -File .bago\cli.ps1`
2. Selecciona opción 1 (Analizar)
3. Ingresa ruta a tu proyecto
4. Lee recomendaciones
5. ¡Mejora tu código!

---

**Let's go! 🚀**

```bash
powershell -ExecutionPolicy Bypass -File C:\Marc_max_20gb\.bago\cli.ps1
```

---

Version: 1.0  
BAGO: 2.5-stable
