#!/usr/bin/env powershell
<#
.SYNOPSIS
    BAGO Tablet Deployment - Script de inicio rápido
    
.DESCRIPTION
    Script que:
    1. Inicia Monitor Service en puerto 8080
    2. Verifica que está respondiendo
    3. Muestra instrucciones para tablet
    4. Mantiene servicio corriendo
    
.EXAMPLE
    .\deploy-to-tablet.ps1
    
.NOTES
    Version: 1.0
    Author: BAGO System
    Date: 2026-04-28
#>

# ============================================================
# CONFIGURATION
# ============================================================

$Script:BAGOPath = "C:\Marc_max_20gb\.bago"
$Script:Port = 8080
$Script:Interval = 5

# ============================================================
# HELPER FUNCTIONS
# ============================================================

function Show-Header {
    Clear-Host
    Write-Host "
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║          📱 BAGO TABLET DEPLOYMENT - LIVE MONITOR         ║
║                                                            ║
║              Monitoreo de Agentes en Tiempo Real           ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
" -ForegroundColor Cyan
}

function Show-Status {
    param([string]$Message, [string]$Status = "INFO")
    
    $colors = @{
        "SUCCESS" = "Green"
        "ERROR"   = "Red"
        "WARN"    = "Yellow"
        "INFO"    = "Cyan"
        "WAIT"    = "DarkCyan"
    }
    
    $icons = @{
        "SUCCESS" = "✅"
        "ERROR"   = "❌"
        "WARN"    = "⚠️ "
        "INFO"    = "ℹ️ "
        "WAIT"    = "⏳"
    }
    
    $color = $colors[$Status]
    $icon = $icons[$Status]
    
    Write-Host "$icon $Message" -ForegroundColor $color
}

function Wait-ForService {
    param([int]$TimeoutSec = 30)
    
    Show-Status "Esperando que Monitor Service responda..." "WAIT"
    
    $elapsed = 0
    while ($elapsed -lt $TimeoutSec) {
        try {
            $test = Test-NetConnection -ComputerName 127.0.0.1 -Port $Script:Port -WarningAction SilentlyContinue
            if ($test.TcpTestSucceeded) {
                Show-Status "Monitor Service respondiendo en puerto $($Script:Port)" "SUCCESS"
                return $true
            }
        } catch {}
        
        Start-Sleep -Seconds 1
        $elapsed++
        Write-Host "." -NoNewline
    }
    
    Write-Host ""
    Show-Status "Timeout esperando servicio" "ERROR"
    return $false
}

function Get-PCIPAddress {
    try {
        $ipconfig = ipconfig | Select-String "IPv4 Address" | Select-Object -First 1
        if ($ipconfig) {
            $ip = $ipconfig -replace '.*: (.+)$', '$1'
            return $ip.Trim()
        }
    } catch {}
    return "192.168.1.x (obtén tu IP con: ipconfig)"
}

function Show-Tablet-Instructions {
    Write-Host "`n"
    Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║               📱 INSTRUCCIONES PARA TABLET                 ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    
    Write-Host "`n📌 OPCIÓN A: Por USB (Seguro, Recomendado)" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════"
    Write-Host @"
1. Conecta tablet por USB al PC
2. En tablet: Habilita USB Debugging
   → Configuración → Opciones de Desarrollador → USB Debugging
3. En tablet: Autoriza acceso desde PC
4. En PC: Ejecuta en nueva terminal:
   cd $Script:BAGOPath
   .\adb-helper.ps1
5. En tablet: Abre Chrome
   → Dirección: http://localhost:8080
   → ¡Dashboard aparece!
"@
    
    Write-Host "`n📌 OPCIÓN B: Por WiFi (Conveniente)" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════"
    
    $pcIP = Get-PCIPAddress
    
    Write-Host @"
1. Verifica que PC y tablet están en misma red WiFi
2. Obtén IP del PC: $pcIP
3. En tablet: Abre Chrome
   → Dirección: http://$pcIP`:$Script:Port
   → ¡Dashboard aparece!
"@
    
    Write-Host "`n🎯 EL DASHBOARD MOSTRARÁ:" -ForegroundColor Green
    Write-Host "═══════════════════════════════════════════"
    Write-Host @"
✓ Estado General
  • Análisis ejecutados
  • Hallazgos totales
  • Agentes activos

✓ Estado de 4 Agentes
  • security_analyzer
  • logic_checker
  • smell_detector
  • duplication_finder
  
  (Cada uno muestra: estado, ejecuciones, hallazgos)

✓ Métricas del Sistema
  • CPU (%)
  • RAM (GB)
  • Disco (GB)

✓ Historial en Tiempo Real
  • Últimos 10 eventos
  • Auto-actualiza cada 5 segundos
  • Botón de refresh manual
"@
    
    Write-Host "`n⏱️  AUTO-ACTUALIZACIÓN:" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════"
    Write-Host "El dashboard se actualiza automáticamente cada 5 segundos"
    Write-Host "Puedes presionar [🔄 Actualizar Ahora] para refresh manual"
    
    Write-Host "`n🎮 GESTOS EN TABLET:" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════"
    Write-Host "• TAP:  [🔄 Actualizar Ahora] para refresh manual"
    Write-Host "• SCROLL: Para ver más historial"
    Write-Host "• ROTATE: Gira tablet para landscape (más espacio)"
}

function Show-Monitoring-Info {
    Write-Host "`n"
    Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║             📊 MONITOREO EN TIEMPO REAL ACTIVO              ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    
    Write-Host @"

🔍 El monitor está rastreando:

✓ Ejecuciones de Agentes (cada 5 segundos)
✓ Cantidad de Hallazgos por Agente
✓ Tiempo promedio de ejecución
✓ Estado (IDLE, RUNNING, FAILED)
✓ Métricas del Sistema (CPU, RAM, Disco)
✓ Historial completo de eventos

📊 Datos Persistentes:
   Archivo: $Script:BAGOPath\monitor\monitor.json
   
🌐 Acceso Remoto:
   Dashboard está disponible en:
   • PC:     http://localhost:$Script:Port
   • Tablet: http://<IP_PC>:$Script:Port
   
🔐 Seguridad:
   • USB:   Conexión encriptada por ADB
   • WiFi:  Red local (solo si en misma WiFi)

"@
}

function Show-Endpoints {
    Write-Host "`n"
    Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor DarkCyan
    Write-Host "║           🔗 API ENDPOINTS (Para desarrolladores)          ║" -ForegroundColor DarkCyan
    Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor DarkCyan
    
    Write-Host @"

GET http://localhost:$Script:Port/api/agents
  └─ Lista de agentes con estado y hallazgos

GET http://localhost:$Script:Port/api/status
  └─ Estado general del monitor

GET http://localhost:$Script:Port/api/metrics
  └─ Métricas del sistema (CPU, RAM, Disco)

GET http://localhost:$Script:Port/api/history
  └─ Historial de últimos 10 eventos

GET http://localhost:$Script:Port/
  └─ Dashboard HTML5 (acceso visual)

"@
}

function Show-Troubleshooting {
    Write-Host "`n"
    Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Yellow
    Write-Host "║                  🔧 TROUBLESHOOTING                        ║" -ForegroundColor Yellow
    Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Yellow
    
    Write-Host @"

❌ Puerto 8080 está ocupado:
   Solución: .\agents-monitor-service.ps1 -Port 9090

❌ No veo cambios en tablet:
   1. Presiona [🔄 Actualizar Ahora]
   2. Recarga página (F5)
   3. Verifica conexión

❌ ADB no funciona:
   Usa WiFi en su lugar: http://<IP_PC>:8080

❌ Tablet no ve PC:
   • Verifica que están en misma WiFi
   • Desactiva firewall temporalmente
   • Intenta con IP manual del PC

❌ Monitor no responde:
   • Cierra e inicia de nuevo
   • Verifica puerto 8080: netstat -an | findstr 8080
   • Reinicia PowerShell

"@
}

# ============================================================
# MAIN
# ============================================================

function Main {
    Show-Header
    
    # Validar que archivo existe
    $monitorScript = "$Script:BAGOPath\agents-monitor-service.ps1"
    if (-not (Test-Path $monitorScript)) {
        Show-Status "Monitor service no encontrado en $monitorScript" "ERROR"
        return
    }
    
    Show-Status "Iniciando BAGO Agent Monitor Service..." "WAIT"
    
    # Iniciar servicio
    try {
        # Start monitor in current session (will block)
        & $monitorScript -Port $Script:Port -Interval $Script:Interval
    } catch {
        Show-Status "Error iniciando servicio: $_" "ERROR"
    }
}

# ============================================================
# ENTRY POINT
# ============================================================

# Si se ejecuta con -ShowInstructions, solo muestra instrucciones
if ($PSBoundParameters.ContainsKey('ShowInstructions')) {
    Show-Header
    Show-Tablet-Instructions
    Show-Monitoring-Info
    Show-Endpoints
    Show-Troubleshooting
    exit
}

# Mostrar información de inicio
Show-Header
Show-Status "Puerto: $Script:Port" "INFO"
Show-Status "Intervalo: $Script:Interval segundos" "INFO"

# Esperar a que servicio responda
Write-Host ""
& $PSScriptRoot\agents-monitor-service.ps1 -Port $Script:Port -Interval $Script:Interval

# Si llegamos aquí, mostrar instrucciones
Show-Tablet-Instructions
Show-Monitoring-Info
Show-Endpoints
Show-Troubleshooting

Write-Host "`n"
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║           ✅ PRESIONA CTRL+C PARA DETENER                 ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Green
