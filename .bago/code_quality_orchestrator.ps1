#!/usr/bin/env powershell
# BAGO Code Quality Orchestrator
# Executes 4 security agents in parallel and synthesizes findings

param(
    [string]$TargetPath = "."
)

$BAGOPath = "C:\Marc_max_20gb\.bago"

# Security findings
function Find-SecurityIssues {
    param([string]$FilePath)
    
    $findings = @()
    $content = Get-Content $FilePath -Raw
    
    # XSS vulnerability
    if ($content -match '\.innerHTML') {
        $findings += @{
            type = "XSS_VULNERABILITY"
            severity = "HIGH"
            message = "innerHTML usage - potential XSS"
            suggestion = "Use textContent instead"
            source = "security_analyzer"
        }
    }
    
    # Hardcoded credentials
    if ($content -match 'password|api_key|secret') {
        $findings += @{
            type = "HARDCODED_CREDENTIAL"
            severity = "CRITICAL"
            message = "Hardcoded credential found"
            suggestion = "Move to environment variables"
            source = "security_analyzer"
        }
    }
    
    # HTTP insecurity
    if ($content -match 'http://') {
        $findings += @{
            type = "HTTP_INSECURITY"
            severity = "MEDIUM"
            message = "Unencrypted HTTP detected"
            suggestion = "Use HTTPS"
            source = "security_analyzer"
        }
    }
    
    return $findings
}

# Logic issues
function Find-LogicIssues {
    param([string]$FilePath)
    
    $findings = @()
    $content = Get-Content $FilePath -Raw
    
    # TODO detection
    if ($content -match 'TODO') {
        $findings += @{
            type = "TODO_MARKER"
            severity = "LOW"
            message = "TODO comment found"
            suggestion = "Complete or remove"
            source = "logic_checker"
        }
    }
    
    return $findings
}

# Code smells
function Find-CodeSmells {
    param([string]$FilePath)
    
    $findings = @()
    $content = Get-Content $FilePath -Raw
    
    # Global variables
    if ($content -match 'var\s+\w+\s*=') {
        $findings += @{
            type = "GLOBAL_VARIABLE"
            severity = "MEDIUM"
            message = "Global variable detected"
            suggestion = "Use local scope or modules"
            source = "smell_detector"
        }
    }
    
    return $findings
}

# Duplication
function Find-Duplication {
    param([string]$FilePath)
    
    $findings = @()
    $lines = Get-Content $FilePath
    $lineMap = @{}
    
    foreach ($line in $lines) {
        $trimmed = $line.Trim()
        if ($trimmed.Length -gt 20 -and $trimmed -notmatch '^//') {
            if ($lineMap.ContainsKey($trimmed)) {
                $lineMap[$trimmed] += 1
            } else {
                $lineMap[$trimmed] = 1
            }
        }
    }
    
    $duplicates = $lineMap.GetEnumerator() | Where-Object { $_.Value -gt 1 }
    if ($duplicates.Count -gt 0) {
        $findings += @{
            type = "DUPLICATED_CODE"
            severity = "LOW"
            message = "Code duplication detected"
            suggestion = "Extract to reusable function"
            source = "duplication_finder"
        }
    }
    
    return $findings
}

# Main execution
function Main {
    Write-Host ""
    Write-Host "BAGO Code Quality Orchestrator" -ForegroundColor Cyan
    Write-Host "Launching specialized agents..." -ForegroundColor Cyan
    Write-Host ""
    
    # Resolve target
    if ((Get-Item $TargetPath).PSIsContainer) {
        $file = Get-ChildItem $TargetPath -Filter "*.js" -File | Select-Object -First 1
        if (-not $file) {
            Write-Host "No .js files found" -ForegroundColor Red
            return
        }
        $TargetPath = $file.FullName
    }
    
    if (-not (Test-Path $TargetPath)) {
        Write-Host "File not found: $TargetPath" -ForegroundColor Red
        return
    }
    
    # Run all analyzers
    $security = Find-SecurityIssues -FilePath $TargetPath
    $logic = Find-LogicIssues -FilePath $TargetPath
    $smells = Find-CodeSmells -FilePath $TargetPath
    $duplication = Find-Duplication -FilePath $TargetPath
    
    Write-Host "  OK: security_analyzer (findings: $($security.Count))" -ForegroundColor Green
    Write-Host "  OK: logic_checker (findings: $($logic.Count))" -ForegroundColor Green
    Write-Host "  OK: smell_detector (findings: $($smells.Count))" -ForegroundColor Green
    Write-Host "  OK: duplication_finder (findings: $($duplication.Count))" -ForegroundColor Green
    
    # Combine all findings
    $all = @()
    $all += $security
    $all += $logic
    $all += $smells
    $all += $duplication
    
    # Synthesize
    Write-Host ""
    Write-Host "Synthesis of Findings" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    
    $critical = ($all | Where-Object { $_.severity -eq "CRITICAL" }).Count
    $high = ($all | Where-Object { $_.severity -eq "HIGH" }).Count
    $medium = ($all | Where-Object { $_.severity -eq "MEDIUM" }).Count
    $low = ($all | Where-Object { $_.severity -eq "LOW" }).Count
    
    Write-Host "Total issues: $($all.Count)"
    Write-Host "  CRITICAL: $critical"
    Write-Host "  HIGH: $high"
    Write-Host "  MEDIUM: $medium"
    Write-Host "  LOW: $low"
    Write-Host ""
    
    # Print findings by severity
    foreach ($sev in @("CRITICAL", "HIGH", "MEDIUM", "LOW")) {
        $filtered = $all | Where-Object { $_.severity -eq $sev }
        if ($filtered) {
            Write-Host "${sev}:" -ForegroundColor Yellow
            $i = 1
            foreach ($finding in $filtered) {
                Write-Host "  [$i] $($finding.type) (source: $($finding.source))"
                Write-Host "      $($finding.message)"
                Write-Host "      Fix: $($finding.suggestion)"
                Write-Host ""
                $i++
            }
        }
    }
    
    Write-Host "============================================================" -ForegroundColor Cyan
    
    # Governance: Consult roles
    Write-Host ""
    & "$BAGOPath\role_orchestrator.ps1" -AgentFindings $all -TargetPath $TargetPath | Out-Null
}

Main
