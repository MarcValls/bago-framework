#!/usr/bin/env powershell
<#
.SYNOPSIS
    .bago tablet start - Inicia monitorización de agentes en tablet
    
.DESCRIPTION
    Script para gestionar acceso a BAGO Agent Monitor desde tablet Android.
    
    Comandos:
        .bago tablet start          - Inicia todo (monitor + instrucciones)
        .bago tablet stop           - Detiene el monitor
        .bago tablet adb-setup      - Setup USB via ADB
        .bago tablet wifi           - Instrucciones para WiFi
        .bago tablet status         - Ver estado actual
        .bago tablet logs           - Ver logs del monitor
    
.EXAMPLE
    .\bago-tablet.ps1 start
    .\bago-tablet.ps1 adb-setup
    .\bago-tablet.ps1 wifi
    
.NOTES
    Version: 1.0
    Author: BAGO System
    Date: 2026-04-28
#>

param(
    [ValidateSet("start", "stop", "adb-setup", "wifi", "status", "logs", "help")]
    [string]$Command = "help",
    
    [int]$Port = 8080,
    [int]$Interval = 5
)

# ============================================================
# CONFIGURATION
# ============================================================

$Script:BAGOPath = "C:\Marc_max_20gb\.bago"
$Script:MonitorScript = "$Script:BAGOPath\agents-monitor-service.ps1"
$Script:ADBScript = "$Script:BAGOPath\adb-helper.ps1"
$Script:LogFile = "$Script:BAGOPath\monitor\tablet.log"

# ============================================================
# HELPER FUNCTIONS
# ============================================================

function Write-Header {
    param([string]$Message, [string]$Icon = "🎯")
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║ $Icon  $($Message.PadRight(56)) ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Cyan
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Ensure-Paths {
    $dirs = @(
        "$Script:BAGOPath\monitor"
    )
    foreach ($dir in $dirs) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory $dir -Force | Out-Null
        }
    }
}

function Log-Message {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $Message" | Add-Content $Script:LogFile -ErrorAction SilentlyContinue
}

# ============================================================
# COMMANDS
# ============================================================

function Invoke-Start {
    Write-Header "BAGO Tablet Monitor - START" "📱"
    
    Log-Message "START command initiated"
    
    Write-Info "Verificando requisitos..."
    
    # Check if monitor script exists
    if (-not (Test-Path $Script:MonitorScript)) {
        Write-Error-Custom "Monitor script no encontrado en $Script:MonitorScript"
        Log-Message "ERROR: Monitor script not found"
        return
    }
    
    Write-Success "Monitor script encontrado"
    
    # Check if port is available
    try {
        $test = Test-NetConnection -ComputerName 127.0.0.1 -Port $Port -WarningAction SilentlyContinue
        if ($test.TcpTestSucceeded) {
            Write-Warning-Custom "Puerto $Port ya está en uso"
            Log-Message "WARNING: Port $Port already in use"
            Write-Info "Usa: .\bago-tablet.ps1 start -Port 9090"
            return
        }
    } catch {}
    
    Write-Success "Puerto $Port disponible"
    
    # Start monitor service
    Write-Info "Iniciando Monitor Service en puerto $Port..."
    Log-Message "Starting Monitor Service on port $Port"
    
    try {
        & $Script:MonitorScript -Port $Port -Interval $Interval
    } catch {
        Write-Error-Custom "Error iniciando monitor: $_"
        Log-Message "ERROR: Failed to start monitor - $_"
        return
    }
}

function Invoke-Stop {
    Write-Header "BAGO Tablet Monitor - STOP" "⏹️"
    
    Log-Message "STOP command initiated"
    
    Write-Info "Buscando procesos de monitor..."
    
    $processes = Get-Process | Where-Object { $_.CommandLine -like "*agents-monitor-service*" }
    
    if ($processes) {
        foreach ($proc in $processes) {
            Write-Info "Deteniendo proceso $($proc.Id)..."
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            Write-Success "Proceso $($proc.Id) detenido"
            Log-Message "Stopped process $($proc.Id)"
        }
    } else {
        Write-Warning-Custom "No se encontraron procesos de monitor ejecutándose"
        Log-Message "No running monitor processes found"
    }
}

function Invoke-ADBSetup {
    Write-Header "BAGO Tablet - USB Setup (ADB)" "🔌"
    
    Log-Message "ADB-SETUP command initiated"
    
    if (-not (Test-Path $Script:ADBScript)) {
        Write-Error-Custom "ADB Helper script no encontrado en $Script:ADBScript"
        return
    }
    
    Write-Info "Ejecutando ADB Helper..."
    Log-Message "Executing ADB Helper"
    
    try {
        & $Script:ADBScript
    } catch {
        Write-Error-Custom "Error ejecutando ADB Helper: $_"
        Log-Message "ERROR: Failed to execute ADB Helper - $_"
    }
}

function Invoke-WiFiInstructions {
    Write-Header "BAGO Tablet - WiFi Setup" "📶"
    
    Log-Message "WIFI command initiated"
    
    Write-Host @"
📋 PASOS PARA CONECTAR VIA WiFi:
════════════════════════════════════════════════════════════════

1️⃣  Verifica que el Monitor está corriendo:
    .\bago-tablet.ps1 status

2️⃣  Obtén la IP del PC:
    ipconfig | Select-String "IPv4"

3️⃣  En la tablet, abre Chrome

4️⃣  En la barra de dirección, escribe:
    http://<IP_PC>:8080

    Ejemplo: http://192.168.1.100:8080

5️⃣  Presiona ENTER

6️⃣  ¡Dashboard aparece en 2 segundos!


✨ Requisitos:
   ✓ PC y tablet en misma red WiFi
   ✓ Monitor Service corriendo en PC
   ✓ Puerto 8080 accesible
   ✓ Navegador Chrome/Firefox en tablet


🔒 Notas de Seguridad:
   • Conexión a través de red local (LAN)
   • No pasa por internet
   • Solo funciona si están en misma WiFi


📱 Desde tablet:
   Chrome → Dirección: http://<IP_PC>:8080
   
   Si no sabes la IP:
   En PC Windows: ipconfig | findstr IPv4

"@ -ForegroundColor Cyan
    
    Log-Message "WiFi instructions displayed"
}

function Invoke-Status {
    Write-Header "BAGO Tablet Monitor - STATUS" "📊"
    
    Log-Message "STATUS command initiated"
    
    Write-Info "Verificando Monitor Service..."
    Write-Host ""
    
    $listening = $false
    try {
        $socket = New-Object System.Net.Sockets.TcpClient
        $socket.ConnectAsync("127.0.0.1", $Port).Wait(1000)
        $listening = $socket.Connected
        $socket.Close()
    } catch {}
    
    if ($listening) {
        Write-Success "Monitor Service está CORRIENDO en puerto $Port"
        Log-Message "Monitor service is RUNNING on port $Port"
        Write-Host ""
        Write-Info "Dashboard accesible en:"
        Write-Host "  • USB:  http://localhost:$Port"
        Write-Host "  • WiFi: http://<IP_PC>:$Port"
        Write-Host ""
    } else {
        Write-Warning-Custom "Monitor Service NO está corriendo"
        Log-Message "Monitor service is NOT running"
        Write-Host ""
        Write-Info "Para iniciarlo:"
        Write-Host "  .\bago-tablet.ps1 start"
        Write-Host ""
    }
    
    # Check if monitor.json exists
    $monitorJson = "$Script:BAGOPath\monitor\monitor.json"
    if (Test-Path $monitorJson) {
        $data = Get-Content $monitorJson | ConvertFrom-Json -ErrorAction SilentlyContinue
        if ($data) {
            Write-Info "Datos de Monitor:"
            Write-Host "  • Análisis: $($data.TotalAnalyses)"
            Write-Host "  • Hallazgos: $($data.TotalFindings)"
            Write-Host "  • Timestamp: $($data.LastUpdate)"
        }
    }
}

function Invoke-Logs {
    Write-Header "BAGO Tablet Monitor - LOGS" "📋"
    
    Log-Message "LOGS command initiated"
    
    if (-not (Test-Path $Script:LogFile)) {
        Write-Warning-Custom "No hay logs disponibles todavía"
        return
    }
    
    $logs = Get-Content $Script:LogFile -Tail 20
    
    Write-Host "Últimas 20 líneas de log:" -ForegroundColor Cyan
    Write-Host ""
    foreach ($log in $logs) {
        Write-Host $log -ForegroundColor DarkGray
    }
}

function Invoke-Help {
    Write-Header "BAGO Tablet Monitor - HELP" "❓"
    
    Write-Host @"
COMANDOS DISPONIBLES:
════════════════════════════════════════════════════════════════

  start           Inicia Monitor Service (opción por defecto)
  stop            Detiene Monitor Service
  adb-setup       Setup USB via ADB (interactive)
  wifi            Muestra instrucciones para WiFi
  status          Verifica si monitor está corriendo
  logs            Muestra últimos logs
  help            Muestra esta ayuda


EJEMPLOS DE USO:
════════════════════════════════════════════════════════════════

  # Iniciar monitor en puerto 8080 (default)
  .\bago-tablet.ps1 start

  # Iniciar en puerto alternativo
  .\bago-tablet.ps1 start -Port 9090

  # Setup USB (adb reverse)
  .\bago-tablet.ps1 adb-setup

  # Ver instrucciones WiFi
  .\bago-tablet.ps1 wifi

  # Verificar status
  .\bago-tablet.ps1 status

  # Ver logs
  .\bago-tablet.ps1 logs

  # Detener monitor
  .\bago-tablet.ps1 stop


FLUJO TÍPICO:
════════════════════════════════════════════════════════════════

  1. Iniciar monitor:
     .\bago-tablet.ps1 start

  2. Opción A - USB:
     .\bago-tablet.ps1 adb-setup
     En tablet: http://localhost:8080

  2. Opción B - WiFi:
     .\bago-tablet.ps1 wifi
     En tablet: http://<IP_PC>:8080

  3. Ver estado:
     .\bago-tablet.ps1 status

  4. Ver logs (si hay problemas):
     .\bago-tablet.ps1 logs


UBICACIÓN DE ARCHIVOS:
════════════════════════════════════════════════════════════════

  Monitor Service:  $Script:MonitorScript
  ADB Helper:       $Script:ADBScript
  Logs:             $Script:LogFile
  Datos:            $Script:BAGOPath\monitor\monitor.json


PUERTO POR DEFECTO:
════════════════════════════════════════════════════════════════

  8080 - Dashboard HTTP


ACCESO DESDE TABLET:
════════════════════════════════════════════════════════════════

  USB (Seguro):
    .\bago-tablet.ps1 adb-setup
    → http://localhost:8080 en tablet

  WiFi (Conveniente):
    .\bago-tablet.ps1 wifi
    → http://<IP_PC>:8080 en tablet


¿PREGUNTAS?
════════════════════════════════════════════════════════════════

  Ver documentación: $Script:BAGOPath\README_TABLET_START_HERE.md

"@ -ForegroundColor Cyan
}

# ============================================================
# MAIN
# ============================================================

function Main {
    # Ensure paths exist
    Ensure-Paths
    
    # Route to command
    switch ($Command.ToLower()) {
        "start" {
            Invoke-Start
        }
        "stop" {
            Invoke-Stop
        }
        "adb-setup" {
            Invoke-ADBSetup
        }
        "wifi" {
            Invoke-WiFiInstructions
        }
        "status" {
            Invoke-Status
        }
        "logs" {
            Invoke-Logs
        }
        default {
            Invoke-Help
        }
    }
}

# Execute
Main
