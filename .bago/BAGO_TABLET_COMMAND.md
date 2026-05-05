# 🎯 .bago tablet - Nuevo Comando TABLET START

**Versión:** 1.0  
**Fecha:** 2026-04-28 06:06:41 UTC+2  
**Status:** ✅ OPERATIVO

---

## 🚀 USO RÁPIDO

```powershell
cd C:\Marc_max_20gb\.bago

# Opción A: Iniciar monitor (comando por defecto)
.\bago-tablet.ps1 start

# Opción B: Ver ayuda
.\bago-tablet.ps1 help

# Opción C: Verificar estado
.\bago-tablet.ps1 status

# Opción D: Setup USB (ADB)
.\bago-tablet.ps1 adb-setup

# Opción E: Ver instrucciones WiFi
.\bago-tablet.ps1 wifi

# Opción F: Detener monitor
.\bago-tablet.ps1 stop
```

---

## 📋 COMANDOS DISPONIBLES

### `start` (Opción por defecto)
```powershell
.\bago-tablet.ps1 start
.\bago-tablet.ps1 start -Port 9090  # Puerto alternativo
```
**Qué hace:**
- Verifica que todos los requisitos existan
- Inicia Monitor Service en puerto 8080 (o especificado)
- Mostrará dashboard en http://localhost:8080

---

### `status`
```powershell
.\bago-tablet.ps1 status
```
**Qué hace:**
- Verifica si monitor está corriendo
- Muestra puertos accesibles (USB, WiFi)
- Muestra datos de monitor si existen
- Rápido y sin bloqueos

**Output:**
```
✅ Monitor Service está CORRIENDO en puerto 8080

ℹ️  Dashboard accesible en:
  • USB:  http://localhost:8080
  • WiFi: http://<IP_PC>:8080
```

---

### `adb-setup`
```powershell
.\bago-tablet.ps1 adb-setup
```
**Qué hace:**
- Ejecuta ADB Helper automáticamente
- Setup USB forwarding
- Detecta tablets conectadas
- Configura todo para acceso seguro

**Requisitos:**
- Android tablet conectada por USB
- USB Debugging habilitado en tablet
- Autorización en tablet

---

### `wifi`
```powershell
.\bago-tablet.ps1 wifi
```
**Qué hace:**
- Muestra instrucciones para acceso WiFi
- Explica cómo obtener IP del PC
- Paso-a-paso para tablet

**Acceso WiFi:**
```
1. Obtén IP: ipconfig
2. En tablet Chrome: http://<IP>:8080
```

---

### `stop`
```powershell
.\bago-tablet.ps1 stop
```
**Qué hace:**
- Busca procesos de monitor
- Los detiene gracefully
- Limpia recursos

---

### `logs`
```powershell
.\bago-tablet.ps1 logs
```
**Qué hace:**
- Muestra últimas 20 líneas de log
- Útil para troubleshooting
- Archivo: `.bago\monitor\tablet.log`

---

### `help`
```powershell
.\bago-tablet.ps1 help
.\bago-tablet.ps1              # Si no especificas comando
```
**Qué hace:**
- Muestra todos los comandos disponibles
- Ejemplos de uso
- Flujo típico
- Ubicación de archivos

---

## 💡 FLUJO TÍPICO DE USO

### Escenario 1: WiFi (Lo más simple)

```powershell
# Terminal 1 - Inicia monitor
cd C:\Marc_max_20gb\.bago
.\bago-tablet.ps1 start

# Terminal 2 - Ver estado (opcional)
.\bago-tablet.ps1 status

# En tablet
# Abre Chrome → http://<IP_PC>:8080
```

### Escenario 2: USB (Lo más seguro)

```powershell
# Terminal 1 - Inicia monitor
cd C:\Marc_max_20gb\.bago
.\bago-tablet.ps1 start

# Terminal 2 - Setup ADB
.\bago-tablet.ps1 adb-setup

# En tablet
# Abre Chrome → http://localhost:8080
```

### Escenario 3: Troubleshooting

```powershell
# Ver estado
.\bago-tablet.ps1 status

# Ver logs
.\bago-tablet.ps1 logs

# Ver instrucciones WiFi
.\bago-tablet.ps1 wifi

# Detener monitor
.\bago-tablet.ps1 stop

# Iniciar de nuevo
.\bago-tablet.ps1 start
```

---

## 🔧 CONFIGURACIÓN

### Puerto Alternativo

```powershell
.\bago-tablet.ps1 start -Port 9090

# Acceso: http://localhost:9090
```

### Intervalo de Actualización

```powershell
.\bago-tablet.ps1 start -Interval 3

# Refresh cada 3 segundos (en lugar de 5)
```

---

## 📁 ARCHIVOS GENERADOS

```
.bago/
├── bago-tablet.ps1                    ← Este script
├── monitor/
│   ├── tablet.log                     ← Logs del tablet
│   └── monitor.json                   ← Datos persistentes
├── agents-monitor-service.ps1         ← Monitor core
└── adb-helper.ps1                     ← ADB setup
```

---

## ✅ CHECKLIST DE USO

```
Antes de empezar:
  ☐ Monitor script existe
  ☐ Puerto 8080 disponible (o usar otro con -Port)

Iniciando:
  ☐ Terminal PowerShell abierta
  ☐ CD a C:\Marc_max_20gb\.bago
  ☐ Ejecuta: .\bago-tablet.ps1 start

Conectando tablet:
  ☐ Tablet conectada (USB o WiFi)
  ☐ Chrome abierto en tablet
  ☐ URL ingresada: http://localhost:8080 (USB)
    o http://<IP>:8080 (WiFi)

Verificando:
  ☐ Dashboard aparece
  ☐ Agentes visibles
  ☐ Auto-refresh funciona
  ☐ Historial se actualiza
```

---

## 🎯 EJEMPLO REAL

```powershell
PS C:\Marc_max_20gb\.bago> .\bago-tablet.ps1 start

╔════════════════════════════════════════════════════════════╗
║ 📱  BAGO Tablet Monitor - START                           ║
╚════════════════════════════════════════════════════════════╝

ℹ️  Verificando requisitos...
✅ Monitor script encontrado
✅ Puerto 8080 disponible
ℹ️  Iniciando Monitor Service en puerto 8080...

BAGO Agent Monitor Service
=========================
Port: 8080
Interval: 5s
Access dashboard at: http://localhost:8080
Press Ctrl+C to stop

Monitor API listening on http://localhost:8080
[06:03:42] Started monitoring...
```

Luego en tablet:
```
Chrome → Dirección: http://localhost:8080 → ENTER

✅ Dashboard aparece en 2 segundos
✅ 4 agentes visibles
✅ Métricas en tiempo real
✅ Se actualiza cada 5 segundos
```

---

## 🆘 TROUBLESHOOTING

| Problema | Solución |
|----------|----------|
| "Puerto 8080 en uso" | `.\bago-tablet.ps1 start -Port 9090` |
| "Monitor no inicia" | `.\bago-tablet.ps1 logs` |
| "Tablet no ve PC" | `.\bago-tablet.ps1 wifi` |
| "ADB no funciona" | Usa WiFi con `.\bago-tablet.ps1 wifi` |
| "Dashboard no carga" | Verifica: `.\bago-tablet.ps1 status` |

---

## 📖 DOCUMENTACIÓN COMPLETA

Para más detalles:
- `README_TABLET_START_HERE.md` - Punto de entrada
- `DEPLOYMENT_SUMMARY.md` - Resumen ejecutivo
- `TABLET_MONITORING_GUIDE.md` - Setup completo
- `TABLET_DEPLOYMENT_INDEX.md` - Índice de todo

---

## ✨ CARACTERÍSTICAS

- ✅ Comandos simples y directos
- ✅ Output colorizado y visual
- ✅ Logging automático
- ✅ Status checking rápido
- ✅ USB y WiFi soportados
- ✅ Troubleshooting integrado
- ✅ Ayuda incorporada

---

## 🎉 CONCLUSIÓN

**Nuevo workflow simplificado:**

```powershell
# Antes (complicado):
cd C:\Marc_max_20gb\.bago
.\agents-monitor-service.ps1 -Port 8080 -Interval 5

# Ahora (simple):
.\bago-tablet.ps1 start

# ¡Y listo!
```

---

**BAGO Tablet Command v1.0**  
*Monitorización simplificada para tablets*  
*2026-04-28*
