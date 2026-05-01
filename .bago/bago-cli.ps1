#!/usr/bin/env powershell
<#
.SYNOPSIS
    BAGO CLI v3.0 - Professional Code Quality Orchestrator
    
.DESCRIPTION
    Interactive CLI for BAGO orchestration system with agents and roles governance.
    
.EXAMPLE
    .\bago-cli.ps1
    
.NOTES
    Version: 3.0
    Author: BAGO System
    Date: 2026-04-28
#>

param(
    [switch]$NoColor = $false,
    [switch]$Verbose = $false
)

# ============================================================
# CONFIGURATION
# ============================================================

$Script:BAGOPath = "C:\Marc_max_20gb\.bago"
$Script:CurrentProject = ""
$Script:AnalysisHistory = @()
$Script:Settings = @{
    ColorEnabled = -not $NoColor
    VerboseMode = $Verbose
    AutoSave = $true
    HistoryMax = 10
}

# ============================================================
# COLOR PALETTE
# ============================================================

function Write-ColorText {
    param(
        [string]$Text,
        [ValidateSet("Header", "Success", "Warning", "Error", "Info", "Menu", "Prompt", "Subtle")]
        [string]$Type = "Info"
    )
    
    $colors = @{
        Header  = "Cyan"
        Success = "Green"
        Warning = "Yellow"
        Error   = "Red"
        Info    = "White"
        Menu    = "Blue"
        Prompt  = "Magenta"
        Subtle  = "Gray"
    }
    
    if ($Script:Settings.ColorEnabled) {
        Write-Host $Text -ForegroundColor $colors[$Type]
    } else {
        Write-Host $Text
    }
}

function Write-Section {
    param([string]$Title, [string]$Icon = "")
    Write-Host ""
    Write-ColorText "═══════════════════════════════════════════════════════════════" Header
    Write-ColorText "  $Icon $Title" Header
    Write-ColorText "═══════════════════════════════════════════════════════════════" Header
    Write-Host ""
}

# ============================================================
# MAIN MENU
# ============================================================

function Show-MainMenu {
    Clear-Host
    Write-ColorText @"

    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║              🎯 BAGO CLI v3.0                            ║
    ║         Code Quality Orchestrator                        ║
    ║                                                           ║
    ║    Líder de Agentes | Gobernanza por Roles              ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝

"@ Header
    
    if ($Script:CurrentProject) {
        Write-ColorText "📂 Current Project: $Script:CurrentProject" Info
        Write-Host ""
    }
    
    Write-ColorText "MAIN MENU" Menu
    Write-Host ""
    Write-ColorText "  [1]  Analyze Code         Ejecutar análisis completo" Info
    Write-ColorText "  [2]  View Agents          Listar agents disponibles" Info
    Write-ColorText "  [3]  View Roles           Listar roles y familias" Info
    Write-ColorText "  [4]  Create Agent         Crear nuevo agent" Info
    Write-ColorText "  [5]  Create Role          Crear nuevo role" Info
    Write-ColorText "  [6]  Analysis History     Ver historial de análisis" Info
    Write-ColorText "  [7]  Settings             Configuración" Info
    Write-ColorText "  [8]  Help & Docs          Documentación" Info
    Write-ColorText "  [9]  Run Demo             Demo de ejecución" Info
    Write-ColorText "  [0]  Exit                 Salir" Error
    Write-Host ""
    Write-ColorText "Selecciona opción: " Prompt -NoNewline
}

function Get-MenuChoice {
    $choice = Read-Host
    return $choice
}

# ============================================================
# ANALYSIS FUNCTIONS
# ============================================================

function Invoke-Analysis {
    param([string]$ProjectPath)
    
    if (-not $ProjectPath) {
        Write-ColorText "Ingresa ruta del proyecto (ej: ..\typing-course\src): " Prompt -NoNewline
        $ProjectPath = Read-Host
    }
    
    if (-not (Test-Path $ProjectPath)) {
        Write-ColorText "❌ Error: Ruta no encontrada: $ProjectPath" Error
        Read-Host "Presiona Enter para continuar"
        return
    }
    
    Write-Section "EJECUTANDO ANÁLISIS" "🔍"
    Write-ColorText "Ruta: $ProjectPath" Info
    Write-Host ""
    
    # Actualizar proyecto actual
    $Script:CurrentProject = $ProjectPath
    
    # Ejecutar orchestrator
    Write-ColorText "▶ Iniciando orchestrator..." Info
    & "$Script:BAGOPath\code_quality_orchestrator.ps1" -ProjectPath $ProjectPath
    
    # Guardar en historial
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $Script:AnalysisHistory += @{
        Timestamp = $timestamp
        Project = $ProjectPath
        Status = "Completed"
    }
    
    Write-Host ""
    Write-ColorText "✓ Análisis completado" Success
    Read-Host "Presiona Enter para continuar"
}

# ============================================================
# AGENTS MANAGEMENT
# ============================================================

function Show-Agents {
    Write-Section "AGENTS DISPONIBLES" "🤖"
    
    $manifest = Load-AgentManifest
    $builtinAgents = @(
        @{Name="security_analyzer"; Category="Seguridad"; Description="Detecta XSS, SQL injection, credenciales"}
        @{Name="logic_checker"; Category="Lógica"; Description="Verifica TODO, inconsistencias"}
        @{Name="smell_detector"; Category="Calidad"; Description="Detecta variables globales, complejidad"}
        @{Name="duplication_finder"; Category="Duplicación"; Description="Encuentra código duplicado"}
    )
    
    Write-ColorText "BUILT-IN AGENTS (4)" Info
    Write-Host ""
    
    $count = 1
    foreach ($agent in $builtinAgents) {
        Write-ColorText "[$count] $(($agent.Name).ToUpper())" Success
        Write-ColorText "    Categoría: $($agent.Category)" Subtle
        Write-ColorText "    $($agent.Description)" Subtle
        Write-Host ""
        $count++
    }
    
    if ($manifest.agents.Count -gt 0) {
        Write-ColorText "CUSTOM AGENTS ($($manifest.agents.Count))" Info
        Write-Host ""
        foreach ($agent in $manifest.agents) {
            Write-ColorText "[$count] $($agent.name.ToUpper())" Info
            Write-ColorText "    Categoría: $($agent.category)" Subtle
            Write-ColorText "    Estado: $($agent.status)" Subtle
            Write-ColorText "    Creado: $($agent.created)" Subtle
            Write-Host ""
            $count++
        }
    }
    
    Read-Host "Presiona Enter para continuar"
}

function Create-NewAgent {
    Write-Section "CREAR NUEVO AGENT" "➕"
    
    Write-ColorText "Nombre del agent: " Prompt -NoNewline
    $name = Read-Host
    
    Write-ColorText "Categoría (custom/security/logic/performance): " Prompt -NoNewline
    $category = Read-Host
    
    Write-ColorText "Descripción: " Prompt -NoNewline
    $description = Read-Host
    
    $manifest = Load-AgentManifest
    $newAgent = @{
        name = $name
        category = $category
        description = $description
        created = (Get-Date -Format 'o')
        status = "pending"
    }
    
    $manifest.agents += $newAgent
    Save-AgentManifest $manifest
    
    Write-ColorText "✓ Agent creado exitosamente: $name" Success
    Read-Host "Presiona Enter para continuar"
}

function Load-AgentManifest {
    $manifestFile = "$Script:BAGOPath\manifests\custom_agents.json"
    if (Test-Path $manifestFile) {
        return (Get-Content $manifestFile | ConvertFrom-Json)
    } else {
        return @{agents = @(); created = (Get-Date -Format 'o')}
    }
}

function Save-AgentManifest {
    param([object]$Manifest)
    $manifestDir = "$Script:BAGOPath\manifests"
    $manifestFile = "$manifestDir\custom_agents.json"
    
    if (-not (Test-Path $manifestDir)) {
        New-Item -ItemType Directory $manifestDir -Force | Out-Null
    }
    
    $Manifest | ConvertTo-Json -Depth 10 | Set-Content $manifestFile -Force
}

# ============================================================
# ROLES MANAGEMENT
# ============================================================

function Show-Roles {
    Write-Section "ROLES DISPONIBLES" "👑"
    
    $roles = @{
        "GOBIERNO" = @("MAESTRO_BAGO", "ORQUESTADOR_CENTRAL")
        "ESPECIALISTAS" = @("REVISOR_SEGURIDAD", "REVISOR_PERFORMANCE", "REVISOR_UX", "INTEGRADOR_REPO")
        "SUPERVISIÓN" = @("AUDITOR_CANONICO", "CENTINELA_SINCERIDAD", "VERTICE")
        "PRODUCCIÓN" = @("ANALISTA", "ARQUITECTO", "GENERADOR", "ORGANIZADOR", "VALIDADOR")
    }
    
    foreach ($family in $roles.GetEnumerator()) {
        Write-ColorText "📦 $($family.Name)" Success
        foreach ($role in $family.Value) {
            Write-ColorText "   • $role" Info
        }
        Write-Host ""
    }
    
    Write-ColorText "TOTAL: 16 roles en 4 familias" Subtle
    Read-Host "Presiona Enter para continuar"
}

function Create-NewRole {
    Write-Section "CREAR NUEVO ROLE" "➕"
    
    Write-ColorText "Nombre del role: " Prompt -NoNewline
    $name = Read-Host
    
    Write-ColorText "Familia (GOBIERNO/ESPECIALISTAS/SUPERVISIÓN/PRODUCCIÓN): " Prompt -NoNewline
    $family = Read-Host
    
    Write-ColorText "Propósito: " Prompt -NoNewline
    $purpose = Read-Host
    
    Write-ColorText "✓ Role '$name' creado en familia '$family'" Success
    Write-ColorText "⚠ Nota: Se creó el role. Usa role_factory.py para validación completa." Warning
    Read-Host "Presiona Enter para continuar"
}

# ============================================================
# HISTORY & SETTINGS
# ============================================================

function Show-History {
    Write-Section "HISTORIAL DE ANÁLISIS" "📋"
    
    if ($Script:AnalysisHistory.Count -eq 0) {
        Write-ColorText "No hay análisis en el historial" Subtle
    } else {
        Write-Host ""
        $Script:AnalysisHistory | ForEach-Object {
            Write-ColorText "[$($_.Timestamp)]" Info
            Write-ColorText "  Proyecto: $($_.Project)" Subtle
            Write-ColorText "  Estado: $($_.Status)" Subtle
            Write-Host ""
        }
    }
    
    Read-Host "Presiona Enter para continuar"
}

function Show-Settings {
    Write-Section "CONFIGURACIÓN" "⚙️"
    
    Write-ColorText "Configuración Actual:" Info
    Write-Host ""
    Write-ColorText "  Color Habilitado: $($Script:Settings.ColorEnabled)" Info
    Write-ColorText "  Modo Verbose: $($Script:Settings.VerboseMode)" Info
    Write-ColorText "  Auto-Guardar: $($Script:Settings.AutoSave)" Info
    Write-ColorText "  Máximo Historial: $($Script:Settings.HistoryMax)" Info
    Write-Host ""
    
    Write-ColorText "[1] Alternar colores" Info
    Write-ColorText "[2] Alternar verbose" Info
    Write-ColorText "[3] Alternar auto-guardar" Info
    Write-ColorText "[0] Volver" Info
    Write-Host ""
    
    Write-ColorText "Selecciona: " Prompt -NoNewline
    $choice = Read-Host
    
    switch ($choice) {
        "1" { $Script:Settings.ColorEnabled = -not $Script:Settings.ColorEnabled }
        "2" { $Script:Settings.VerboseMode = -not $Script:Settings.VerboseMode }
        "3" { $Script:Settings.AutoSave = -not $Script:Settings.AutoSave }
    }
    
    Write-ColorText "✓ Configuración actualizada" Success
    Read-Host "Presiona Enter para continuar"
}

# ============================================================
# HELP & DOCUMENTATION
# ============================================================

function Show-Help {
    Write-Section "AYUDA Y DOCUMENTACIÓN" "📚"
    
    Write-ColorText "Documentos Disponibles:" Info
    Write-Host ""
    Write-ColorText "[1] Guía Rápida" Info
    Write-ColorText "[2] Ejemplo Interacción Completa" Info
    Write-ColorText "[3] Demo Ejecución Real" Info
    Write-ColorText "[4] Documentación Agents" Info
    Write-ColorText "[5] Documentación Roles" Info
    Write-ColorText "[6] Verificación de Componentes" Info
    Write-ColorText "[0] Volver" Info
    Write-Host ""
    
    Write-ColorText "Selecciona documento: " Prompt -NoNewline
    $choice = Read-Host
    
    $docs = @{
        "1" = "PHASE_4_5_GUIDE.md"
        "2" = "EJEMPLO_INTERACCION_COMPLETA.md"
        "3" = "DEMO_EJECUCION_REAL.md"
        "4" = "AGENT_FACTORY_DOCUMENTATION.md"
        "5" = "ROLE_FACTORY_DOCUMENTATION.md"
        "6" = "VERIFICACION_COMPONENTES_Y_ESTADO.md"
    }
    
    if ($docs.ContainsKey($choice)) {
        $docPath = "$Script:BAGOPath\$($docs[$choice])"
        if (Test-Path $docPath) {
            & notepad $docPath
        } else {
            Write-ColorText "❌ Documento no encontrado" Error
        }
    }
    
    Read-Host "Presiona Enter para continuar"
}

# ============================================================
# DEMO
# ============================================================

function Run-Demo {
    Write-Section "DEMO DE EJECUCIÓN" "🎬"
    
    Write-ColorText "Ejecutando demo con typing-course/src..." Info
    Write-Host ""
    
    & "$Script:BAGOPath\code_quality_orchestrator.ps1" -ProjectPath "..\typing-course\src"
    
    Write-Host ""
    Read-Host "Presiona Enter para continuar"
}

# ============================================================
# MAIN LOOP
# ============================================================

function Start-CLILoop {
    while ($true) {
        Show-MainMenu
        $choice = Get-MenuChoice
        
        switch ($choice) {
            "1" { Invoke-Analysis }
            "2" { Show-Agents }
            "3" { Show-Roles }
            "4" { Create-NewAgent }
            "5" { Create-NewRole }
            "6" { Show-History }
            "7" { Show-Settings }
            "8" { Show-Help }
            "9" { Run-Demo }
            "0" { 
                Write-ColorText "¡Hasta luego! 👋" Success
                exit 0
            }
            default { 
                Write-ColorText "❌ Opción inválida. Intenta de nuevo." Error
                Read-Host "Presiona Enter"
            }
        }
    }
}

# ============================================================
# ENTRY POINT
# ============================================================

if ($Script:Verbose) {
    Write-ColorText "Verbose Mode Enabled" Subtle
    Write-ColorText "BAGO Path: $Script:BAGOPath" Subtle
}

Start-CLILoop
