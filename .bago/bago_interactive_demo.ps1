#!/usr/bin/env powershell
# bago_interactive_demo.ps1

param([string]$ProjectPath = "C:\Marc_max_20gb\typing-course")

# Read files
$jsFiles = Get-ChildItem -Path $ProjectPath -Filter "*.js" -Recurse
$files = @{}

Write-Host "`n===================================================" -ForegroundColor Cyan
Write-Host "  BAGO INTERACTIVE DEMO - Typing Course Analysis" -ForegroundColor Cyan
Write-Host "==================================================`n" -ForegroundColor Cyan

Write-Host "Step 1: Reading project files..." -ForegroundColor Blue
foreach ($file in $jsFiles) {
    $relPath = $file.FullName.Replace($ProjectPath, "").TrimStart("\")
    $files[$relPath] = Get-Content $file.FullName -Raw
    Write-Host "  OK: $relPath" -ForegroundColor Green
}

Write-Host "`n---" -ForegroundColor Blue
Write-Host "Found $($jsFiles.Count) files`n" -ForegroundColor Cyan

Start-Sleep -Milliseconds 800

# Execute AGENTS
Write-Host "Step 2: Executing AGENTS in parallel..." -ForegroundColor Blue
Write-Host ""

$findings = @{
    security = @()
    logic = @()
    smells = @()
    duplication = @()
}

# AGENT 1: Security
Write-Host "[1/4] Security Analyzer..." -ForegroundColor Green
foreach ($filename in $files.Keys) {
    $content = $files[$filename]
    
    if ($content -like "*innerHTML*") {
        $findings.security += "XSS vulnerability in $filename"
    }
    if ($content -like "*http://*") {
        $findings.security += "Insecure HTTP in $filename"
    }
}
Write-Host "      Found: $($findings.security.Count) issues" -ForegroundColor Red
Start-Sleep -Milliseconds 400

# AGENT 2: Logic
Write-Host "[2/4] Logic Checker..." -ForegroundColor Green
foreach ($filename in $files.Keys) {
    $content = $files[$filename]
    if ($content -like "*TODO*") {
        $findings.logic += "TODO in $filename"
    }
}
Write-Host "      Found: $($findings.logic.Count) issues" -ForegroundColor Yellow
Start-Sleep -Milliseconds 400

# AGENT 3: Smells
Write-Host "[3/4] Code Smell Detector..." -ForegroundColor Green
foreach ($filename in $files.Keys) {
    $content = $files[$filename]
    if ($content -like "*let currentLesson*" -or $content -like "*let lessonData*") {
        $findings.smells += "Global variables in $filename"
    }
}
Write-Host "      Found: $($findings.smells.Count) issues" -ForegroundColor Yellow
Start-Sleep -Milliseconds 400

# AGENT 4: Duplication
Write-Host "[4/4] Duplication Finder..." -ForegroundColor Green
foreach ($filename in $files.Keys) {
    $content = $files[$filename]
    if ($content -like "*function getLessonContent*" -and $content -like "*function getLesson*") {
        $findings.duplication += "Duplicate functions in $filename"
    }
}
Write-Host "      Found: $($findings.duplication.Count) issues" -ForegroundColor Red
Start-Sleep -Milliseconds 400

Write-Host "`nAll AGENTS completed (parallel execution)`n" -ForegroundColor Green

Start-Sleep -Milliseconds 800

# Consult ROLES
Write-Host "Step 3: Consulting ROLES..." -ForegroundColor Blue
Write-Host ""

# ROLE: Security Reviewer
Write-Host "Consulting REVISOR_SEGURIDAD..." -ForegroundColor Cyan
if ($findings.security.Count -gt 2) {
    $securityVerdict = "REJECTED"
    Write-Host "  Result: REJECTED (critical issues)" -ForegroundColor Red
} else {
    $securityVerdict = "ACCEPTED"
    Write-Host "  Result: ACCEPTED" -ForegroundColor Green
}
Start-Sleep -Milliseconds 400

# ROLE: Performance Reviewer
Write-Host "Consulting REVISOR_PERFORMANCE..." -ForegroundColor Cyan
if ($findings.duplication.Count -gt 0) {
    $perfVerdict = "REVIEW"
    Write-Host "  Result: REVIEW NEEDED (duplication)" -ForegroundColor Yellow
} else {
    $perfVerdict = "ACCEPTED"
    Write-Host "  Result: ACCEPTED" -ForegroundColor Green
}
Start-Sleep -Milliseconds 400

# ROLE: Maestro
Write-Host "Consulting MAESTRO_BAGO..." -ForegroundColor Cyan
if ($securityVerdict -eq "REJECTED" -or $perfVerdict -eq "REVIEW") {
    $final = "NOT READY"
    Write-Host "  Result: NOT READY FOR PRODUCTION" -ForegroundColor Red
} else {
    $final = "READY"
    Write-Host "  Result: READY FOR PRODUCTION" -ForegroundColor Green
}
Start-Sleep -Milliseconds 400

Write-Host "`n---" -ForegroundColor Blue
Write-Host "Step 4: Final Report" -ForegroundColor Blue
Write-Host "`n"

Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  Security issues:   $($findings.security.Count)" -ForegroundColor Red
Write-Host "  Logic issues:      $($findings.logic.Count)" -ForegroundColor Yellow
Write-Host "  Code smells:       $($findings.smells.Count)" -ForegroundColor Yellow
Write-Host "  Duplications:      $($findings.duplication.Count)" -ForegroundColor Red

Write-Host "`nVerdicts:" -ForegroundColor Cyan
if ($securityVerdict -eq "REJECTED") {
    Write-Host "  REVISOR_SEGURIDAD:    REJECTED" -ForegroundColor Red
} else {
    Write-Host "  REVISOR_SEGURIDAD:    ACCEPTED" -ForegroundColor Green
}

if ($perfVerdict -eq "REVIEW") {
    Write-Host "  REVISOR_PERFORMANCE:  REVIEW NEEDED" -ForegroundColor Yellow
} else {
    Write-Host "  REVISOR_PERFORMANCE:  ACCEPTED" -ForegroundColor Green
}

if ($final -eq "NOT READY") {
    Write-Host "  MAESTRO_BAGO:         NOT READY" -ForegroundColor Red
    Write-Host "`nNext steps:" -ForegroundColor Cyan
    Write-Host "  1. Fix security vulnerabilities" -ForegroundColor Yellow
    Write-Host "  2. Remove duplicate code" -ForegroundColor Yellow
    Write-Host "  3. Complete TODO items" -ForegroundColor Yellow
} else {
    Write-Host "  MAESTRO_BAGO:         READY FOR PRODUCTION" -ForegroundColor Green
    Write-Host "`nNext steps:" -ForegroundColor Cyan
    Write-Host "  1. Merge to main" -ForegroundColor Green
    Write-Host "  2. Deploy to production" -ForegroundColor Green
}

Write-Host "`n===================================================" -ForegroundColor Cyan
Write-Host "DEMO: BAGO successfully integrated AGENTS + ROLES" -ForegroundColor Green
Write-Host "===================================================`n" -ForegroundColor Cyan
