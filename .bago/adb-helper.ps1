#!/usr/bin/env powershell
<#
.SYNOPSIS
    BAGO ADB Helper - Facilita setup de monitorización en tablet
    
.DESCRIPTION
    Script que:
    - Verifica ADB está instalado
    - Busca dispositivos conectados
    - Configura port forwarding
    - Inicia monitor service automáticamente
    
.EXAMPLE
    .\adb-helper.ps1
    
.NOTES
    Version: 1.0
    Author: BAGO System
    Date: 2026-04-28
#>

param(
    [int]$Port = 8080,
    [switch]$NoAuto = $false
)

# ============================================================
# CONFIGURATION
# ============================================================

$Script:BAGOPath = "C:\Marc_max_20gb\.bago"
$Script:ADBPath = ""
$Script:Device = ""

# ============================================================
# COLOR OUTPUT
# ============================================================

function Write-Success { 
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green 
}

function Write-Error-Custom { 
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red 
}

function Write-Warning-Custom { 
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow 
}

function Write-Info { 
    param([string]$Message)
    Write-Host "ℹ $Message" -ForegroundColor Cyan 
}

function Write-Section {
    param([string]$Title)
    Write-Host ""
    Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  $Title" -ForegroundColor Cyan
    Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
}

# ============================================================
# ADB DETECTION
# ============================================================

function Find-ADB {
    Write-Section "Buscando ADB"
    
    # Intenta comando directo
    try {
        $version = & adb version 2>&1
        if ($version -like "*Android Debug Bridge*") {
            $Script:ADBPath = "adb"
            Write-Success "ADB encontrado en PATH"
            return $true
        }
    } catch { }
    
    # Búsquedas comunes
    $searchPaths = @(
        "C:\Android\platform-tools\adb.exe"
        "C:\Program Files\Android\platform-tools\adb.exe"
        "C:\Program Files (x86)\Android\platform-tools\adb.exe"
        "$env:PROGRAMFILES\Android\platform-tools\adb.exe"
        "$env:USERPROFILE\AppData\Local\Android\Sdk\platform-tools\adb.exe"
    )
    
    foreach ($path in $searchPaths) {
        if (Test-Path $path) {
            $Script:ADBPath = $path
            Write-Success "ADB encontrado: $path"
            return $true
        }
    }
    
    Write-Error-Custom "ADB no encontrado"
    Write-Info "Descargar desde: https://developer.android.com/studio/releases/platform-tools"
    return $false
}

# ============================================================
# DEVICE DETECTION
# ============================================================

function Find-Device {
    Write-Section "Buscando dispositivo Android"
    
    $devices = & $Script:ADBPath devices | Select-Object -Skip 1 | Where-Object { $_ -and $_ -notmatch "^List" }
    
    if (-not $devices) {
        Write-Error-Custom "No hay dispositivos conectados"
        Write-Info "Pasos:"
        Write-Info "1. Conectar tablet vía USB"
        Write-Info "2. Habilitar USB Debugging en Settings → Developer Options"
        Write-Info "3. Permitir acceso cuando se pregunte"
        Write-Info "4. Ejecutar este script de nuevo"
        return $false
    }
    
    $deviceList = $devices | ForEach-Object { 
        $parts = $_ -split '\s+'
        $parts[0]
    }
    
    if ($deviceList.Count -eq 1) {
        $Script:Device = $deviceList[0]
        Write-Success "Dispositivo encontrado: $Script:Device"
        return $true
    } else {
        Write-Warning-Custom "Múltiples dispositivos encontrados"
        $i = 1
        foreach ($dev in $deviceList) {
            Write-Host "  [$i] $dev"
            $i++
        }
        
        $choice = Read-Host "Selecciona dispositivo (número)"
        $index = [int]$choice - 1
        
        if ($index -ge 0 -and $index -lt $deviceList.Count) {
            $Script:Device = $deviceList[$index]
            Write-Success "Dispositivo seleccionado: $Script:Device"
            return $true
        } else {
            Write-Error-Custom "Selección inválida"
            return $false
        }
    }
}

# ============================================================
# PORT FORWARDING
# ============================================================

function Setup-PortForward {
    Write-Section "Configurando Port Forwarding"
    
    Write-Info "Redirigiendo puerto $Port..."
    
    & $Script:ADBPath reverse tcp:$Port tcp:$Port 2>&1 | Out-Null
    
    Start-Sleep -Seconds 1
    
    $status = & $Script:ADBPath reverse --list
    
    if ($status -like "*tcp:$Port*") {
        Write-Success "Port forwarding configurado: tcp:$Port ↔ tcp:$Port"
        return $true
    } else {
        Write-Error-Custom "Port forwarding falló"
        return $false
    }
}

# ============================================================
# MONITOR SERVICE
# ============================================================

function Start-MonitorService {
    Write-Section "Iniciando Monitor Service"
    
    $monitorScript = "$Script:BAGOPath\agents-monitor-service.ps1"
    
    if (-not (Test-Path $monitorScript)) {
        Write-Error-Custom "Script de monitor no encontrado: $monitorScript"
        return $false
    }
    
    Write-Info "Iniciando servicio en puerto $Port..."
    Write-Info ""
    Write-Info "Acceder desde tablet en:"
    Write-Success "http://localhost:$Port"
    Write-Info ""
    Write-Info "O en red local desde PC:"
    Write-Success "http://<IP_DEL_PC>:$Port"
    Write-Info ""
    
    # Iniciar en nueva ventana
    Start-Process powershell -ArgumentList "-NoExit -Command `"& '$monitorScript' -Port $Port -Verbose`"" -WindowStyle Normal
    
    return $true
}

# ============================================================
# SUMMARY
# ============================================================

function Show-Summary {
    Write-Section "Resumen de Configuración"
    
    Write-Info "ADB:            $Script:ADBPath"
    Write-Info "Dispositivo:    $Script:Device"
    Write-Info "Puerto:         $Port"
    Write-Info "Monitor:        $Script:BAGOPath\agents-monitor-service.ps1"
    Write-Info "Dashboard:      http://localhost:$Port"
    Write-Info ""
    
    Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "✓ Configuración completa" -ForegroundColor Green
    Write-Host ""
    Write-Host "Próximos pasos:" -ForegroundColor Cyan
    Write-Host "1. Abre Chrome en tu tablet"
    Write-Host "2. Navega a: http://localhost:$Port"
    Write-Host "3. Verás el dashboard en tiempo real"
    Write-Host "4. Tap [Actualizar Ahora] para refresh manual"
    Write-Host ""
    Write-Host "Presiona Ctrl+C en la ventana del monitor para detener"
    Write-Host ""
}

# ============================================================
# MAIN FLOW
# ============================================================

function Main {
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║         BAGO ADB Helper v1.0                              ║" -ForegroundColor Cyan
    Write-Host "║    Monitorización de Agentes en Tablet Android             ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    
    # Paso 1: Buscar ADB
    if (-not (Find-ADB)) {
        Write-Error-Custom "No se puede continuar sin ADB"
        exit 1
    }
    
    # Paso 2: Buscar dispositivo
    if (-not (Find-Device)) {
        Write-Error-Custom "No se puede continuar sin dispositivo"
        exit 1
    }
    
    # Paso 3: Configurar port forwarding
    if (-not (Setup-PortForward)) {
        Write-Error-Custom "No se puede continuar sin port forwarding"
        exit 1
    }
    
    # Paso 4: Mostrar resumen
    Show-Summary
    
    # Paso 5: Iniciar monitor service
    if (-not $NoAuto) {
        Start-MonitorService
    } else {
        Write-Info "Monitor service no iniciado (modo manual)"
        Write-Info "Para iniciar manualmente:"
        Write-Info "  cd $Script:BAGOPath"
        Write-Info "  .\agents-monitor-service.ps1 -Port $Port"
    }
}

# ============================================================
# ENTRY POINT
# ============================================================

Main
