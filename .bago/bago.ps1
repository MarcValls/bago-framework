#!/usr/bin/env powershell
# BAGO CLI - Main entry point
# Orchestrates code quality agents and roles

param(
    [string]$Command = "help",
    [string]$Target = ".",
    [string]$NewAgent = "",
    [string]$Category = "custom",
    [string]$RemoveAgent = "",
    [string]$ListFormat = "table"
)

$BAGOPath = "C:\Marc_max_20gb\.bago"
$ManifestFile = "$BAGOPath\manifests\custom_agents.json"

# Ensure manifest directory exists
$ManifestDir = Split-Path $ManifestFile
if (-not (Test-Path $ManifestDir)) { 
    New-Item -ItemType Directory $ManifestDir -Force | Out-Null 
}

# ============================================================
# MANIFEST MANAGEMENT
# ============================================================

function Load-AgentManifest {
    if (Test-Path $ManifestFile) {
        return (Get-Content $ManifestFile | ConvertFrom-Json)
    } else {
        return @{agents = @(); created = (Get-Date -Format 'o')}
    }
}

function Save-AgentManifest {
    param([object]$Manifest)
    $Manifest | ConvertTo-Json -Depth 10 | Set-Content $ManifestFile -Force
}

# ============================================================
# COMMANDS
# ============================================================

function Cmd-Help {
    Write-Host ""
    Write-Host "BAGO Code Quality Orchestrator" -ForegroundColor Cyan
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Green
    Write-Host "  bago analyze <path>                    Analyze code quality"
    Write-Host "  bago list-agents                       Show all agents"
    Write-Host "  bago new-agent <name> [--category X]   Create custom agent"
    Write-Host "  bago remove-agent <name>               Delete agent"
    Write-Host "  bago list-roles                        Show all roles"
    Write-Host "  bago cli                               Start interactive menu"
    Write-Host ""
}

function Cmd-Analyze {
    param([string]$Path = ".")
    
    $orchestrator = "$BAGOPath\code_quality_orchestrator.ps1"
    if (-not (Test-Path $orchestrator)) {
        Write-Host "Error: Orchestrator not found" -ForegroundColor Red
        return
    }
    
    & powershell -ExecutionPolicy Bypass -File $orchestrator -TargetPath $Path
}

function Cmd-ListAgents {
    $manifest = Load-AgentManifest
    
    Write-Host ""
    Write-Host "Registered Custom Agents" -ForegroundColor Cyan
    Write-Host "========================" -ForegroundColor Cyan
    
    if ($manifest.agents.Count -eq 0) {
        Write-Host "No custom agents registered"
    } else {
        $manifest.agents | ForEach-Object {
            Write-Host ""
            Write-Host "  Name: $($_.name)" -ForegroundColor Yellow
            Write-Host "  Category: $($_.category)"
            Write-Host "  Created: $($_.created)"
            Write-Host "  Status: $($_.status)"
        }
    }
    
    Write-Host ""
    Write-Host "Built-in Agents:" -ForegroundColor Cyan
    Write-Host "  - security_analyzer"
    Write-Host "  - logic_checker"
    Write-Host "  - smell_detector"
    Write-Host "  - duplication_finder"
    Write-Host ""
}

function Cmd-NewAgent {
    param(
        [string]$AgentName,
        [string]$Category = "custom"
    )
    
    Write-Host ""
    Write-Host "Creating agent: $AgentName" -ForegroundColor Green
    
    $manifest = Load-AgentManifest
    
    # Check if already exists
    $existing = $manifest.agents | Where-Object { $_.name -eq $AgentName }
    if ($existing) {
        Write-Host "Agent already exists: $AgentName" -ForegroundColor Yellow
        return
    }
    
    # Add to manifest
    $newAgent = @{
        name = $AgentName
        category = $Category
        created = (Get-Date -Format 'o')
        status = "pending"
        rules = @()
    }
    
    $manifest.agents += @($newAgent)
    Save-AgentManifest $manifest
    
    Write-Host "Agent created successfully" -ForegroundColor Green
    Write-Host "Next: Implement agent logic in .bago/agents/$AgentName.ps1" -ForegroundColor Cyan
    Write-Host ""
}

function Cmd-RemoveAgent {
    param([string]$AgentName)
    
    $manifest = Load-AgentManifest
    
    $manifest.agents = $manifest.agents | Where-Object { $_.name -ne $AgentName }
    Save-AgentManifest $manifest
    
    Write-Host "Agent removed: $AgentName" -ForegroundColor Green
}

function Cmd-ListRoles {
    Write-Host ""
    Write-Host "Available ROLES" -ForegroundColor Cyan
    Write-Host "===============" -ForegroundColor Cyan
    Write-Host ""
    
    $rolesDir = "$BAGOPath\roles"
    if (Test-Path $rolesDir) {
        Get-ChildItem $rolesDir -Filter "*.md" | ForEach-Object {
            Write-Host "  - $($_.BaseName)"
        }
    }
    
    Write-Host ""
}

function Cmd-InteractiveCLI {
    $cli = "$BAGOPath\cli.ps1"
    if (Test-Path $cli) {
        & powershell -ExecutionPolicy Bypass -File $cli
    } else {
        Write-Host "Error: CLI not found" -ForegroundColor Red
    }
}

# ============================================================
# MAIN DISPATCH
# ============================================================

switch ($Command) {
    "help" {
        Cmd-Help
    }
    "analyze" {
        Cmd-Analyze -Path $Target
    }
    "list-agents" {
        Cmd-ListAgents
    }
    "new-agent" {
        Cmd-NewAgent -AgentName $NewAgent -Category $Category
    }
    "remove-agent" {
        Cmd-RemoveAgent -AgentName $RemoveAgent
    }
    "list-roles" {
        Cmd-ListRoles
    }
    "cli" {
        Cmd-InteractiveCLI
    }
    default {
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Cmd-Help
    }
}
