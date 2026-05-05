#!/usr/bin/env powershell
# BAGO CLI - Menu Interactivo

$BAGOPath = "C:\Marc_max_20gb\.bago"
$ProjectPath = ""

function Show-Menu {
    Clear-Host
    Write-Host ""
    Write-Host "======================================================" -ForegroundColor Cyan
    Write-Host "               BAGO CLI v2.5" -ForegroundColor Cyan
    Write-Host "         Code Quality Orchestrator" -ForegroundColor Cyan
    Write-Host "======================================================" -ForegroundColor Cyan
    Write-Host ""
    
    if ($ProjectPath) {
        Write-Host "Current project: $ProjectPath" -ForegroundColor Yellow
        Write-Host ""
    }
    
    Write-Host "Options:" -ForegroundColor Green
    Write-Host ""
    Write-Host "  [1] Analyze code with BAGO" -ForegroundColor Cyan
    Write-Host "  [2] List available AGENTS" -ForegroundColor Cyan
    Write-Host "  [3] List available ROLES" -ForegroundColor Cyan
    Write-Host "  [4] Run demo again" -ForegroundColor Cyan
    Write-Host "  [5] Read quick guide" -ForegroundColor Cyan
    Write-Host "  [6] Change project" -ForegroundColor Cyan
    Write-Host "  [0] Exit" -ForegroundColor Cyan
    Write-Host ""
}

function Analyze-Project {
    param([string]$Path)
    
    if (-not $Path) {
        Write-Host "Enter project path: " -NoNewline -ForegroundColor Cyan
        $Path = Read-Host
    }
    
    if (-not (Test-Path $Path)) {
        Write-Host "Error: Path not found: $Path" -ForegroundColor Red
        Write-Host ""
        Read-Host "Press Enter"
        return $false
    }
    
    Write-Host ""
    Write-Host "Running BAGO analysis..." -ForegroundColor Green
    Write-Host ""
    
    $demo = "$BAGOPath\bago_interactive_demo.ps1"
    
    if (-not (Test-Path $demo)) {
        Write-Host "Error: Demo not found" -ForegroundColor Red
        Read-Host "Press Enter"
        return $false
    }
    
    & powershell -ExecutionPolicy Bypass -File $demo -ProjectPath $Path
    
    Write-Host ""
    Read-Host "Press Enter"
    return $true
}

function Show-Agents {
    Clear-Host
    Write-Host ""
    Write-Host "Available AGENTS" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "[SECURITY ANALYZER]" -ForegroundColor Yellow
    Write-Host "  Detects: XSS, CSRF, secrets, sensitive data"
    Write-Host ""
    
    Write-Host "[LOGIC CHECKER]" -ForegroundColor Yellow
    Write-Host "  Detects: TODOs, inconsistencies, missing validation"
    Write-Host ""
    
    Write-Host "[CODE SMELL DETECTOR]" -ForegroundColor Yellow
    Write-Host "  Detects: Global variables, long functions, high complexity"
    Write-Host ""
    
    Write-Host "[DUPLICATION FINDER]" -ForegroundColor Yellow
    Write-Host "  Detects: Duplicated code, repeated logic"
    Write-Host ""
    
    Write-Host "============================================================" -ForegroundColor Cyan
    Read-Host "Press Enter"
}

function Show-Roles {
    Clear-Host
    Write-Host ""
    Write-Host "Available ROLES" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "[MAESTRO_BAGO]" -ForegroundColor Yellow
    Write-Host "  Government role. User interface, final synthesis"
    Write-Host ""
    
    Write-Host "[SECURITY REVIEWER]" -ForegroundColor Yellow
    Write-Host "  Specialist role. Validates security, risks"
    Write-Host ""
    
    Write-Host "[PERFORMANCE REVIEWER]" -ForegroundColor Yellow
    Write-Host "  Specialist role. Evaluates performance, efficiency"
    Write-Host ""
    
    Write-Host "[UX REVIEWER]" -ForegroundColor Yellow
    Write-Host "  Specialist role. Validates user experience"
    Write-Host ""
    
    Write-Host "[REPO INTEGRATOR]" -ForegroundColor Yellow
    Write-Host "  Specialist role. Manages integrations, merges"
    Write-Host ""
    
    Write-Host "============================================================" -ForegroundColor Cyan
    Read-Host "Press Enter"
}

function Show-Demo {
    & powershell -ExecutionPolicy Bypass -File "$BAGOPath\bago_interactive_demo.ps1"
    Write-Host ""
    Read-Host "Press Enter"
}

function Show-Guide {
    Clear-Host
    $guide = "$BAGOPath\QUICKSTART.md"
    if (Test-Path $guide) {
        Get-Content $guide | Out-Host -Paging
    } else {
        Write-Host "Error: Guide not found" -ForegroundColor Red
    }
}

function Change-Project {
    Write-Host ""
    Write-Host "Enter project path: " -NoNewline -ForegroundColor Cyan
    $newPath = Read-Host
    
    if (Test-Path $newPath) {
        return $newPath
    } else {
        Write-Host "Error: Path not found" -ForegroundColor Red
        return ""
    }
}

# Main Loop
$project = ""

while ($true) {
    Show-Menu
    Write-Host "Select option: " -NoNewline -ForegroundColor Green
    $choice = Read-Host
    
    switch ($choice) {
        "1" {
            Analyze-Project $project
        }
        "2" {
            Show-Agents
        }
        "3" {
            Show-Roles
        }
        "4" {
            Show-Demo
        }
        "5" {
            Show-Guide
        }
        "6" {
            $newProj = Change-Project
            if ($newProj) {
                $project = $newProj
                Write-Host "Project changed to: $project" -ForegroundColor Green
                Write-Host ""
                Read-Host "Press Enter"
            }
        }
        "0" {
            Write-Host ""
            Write-Host "Goodbye!" -ForegroundColor Green
            Write-Host ""
            exit 0
        }
        default {
            Write-Host "Invalid option" -ForegroundColor Red
            Write-Host ""
            Read-Host "Press Enter"
        }
    }
}
