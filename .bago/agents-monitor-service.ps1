#!/usr/bin/env powershell
<#
.SYNOPSIS
    BAGO Agent Monitor Service - Monitoreo en tiempo real de agentes
    
.DESCRIPTION
    Servicio de monitorización que:
    - Rastrea estado de agentes (running/idle/failed)
    - Registra ejecuciones y hallazgos
    - Expone API REST para tabletas
    - Genera dashboards HTML5
    
.EXAMPLE
    .\agents-monitor-service.ps1 -Port 8080 -Interval 5
    
.NOTES
    Version: 1.0
    Author: BAGO System
    Date: 2026-04-28
#>

param(
    [int]$Port = 8080,
    [int]$Interval = 5,
    [switch]$Verbose = $false
)

# ============================================================
# CONFIGURATION
# ============================================================

$Script:BAGOPath = "C:\Marc_max_20gb\.bago"
$Script:MonitorDB = "$Script:BAGOPath\monitor\monitor.json"
$Script:Port = $Port
$Script:Interval = $Interval
$Script:Running = $true

# Crear directorio de monitoreo si no existe
$MonitorDir = Split-Path $Script:MonitorDB
if (-not (Test-Path $MonitorDir)) {
    New-Item -ItemType Directory $MonitorDir -Force | Out-Null
}

# ============================================================
# DATA STRUCTURES
# ============================================================

class AgentStatus {
    [string]$Name
    [string]$Status          # running, idle, failed, pending
    [datetime]$LastSeen
    [int]$ExecutionsCount
    [int]$SuccessCount
    [int]$FailureCount
    [double]$AvgExecutionTime
    [array]$RecentFindings
    [string]$CurrentTask
    [int]$Progress           # 0-100
}

class MonitorData {
    [datetime]$StartTime
    [array]$Agents
    [array]$ExecutionHistory
    [int]$TotalAnalyses
    [int]$TotalFindings
    [hashtable]$SystemMetrics
}

# ============================================================
# INITIALIZATION
# ============================================================

function Initialize-Monitor {
    $data = @{
        StartTime = Get-Date
        Agents = @()
        ExecutionHistory = @()
        TotalAnalyses = 0
        TotalFindings = 0
        SystemMetrics = @{
            CPUUsage = 0
            MemoryUsage = 0
            DiskUsage = 0
        }
    }
    
    # Inicializar agents
    $agentNames = @("security_analyzer", "logic_checker", "smell_detector", "duplication_finder")
    foreach ($name in $agentNames) {
        $agent = @{
            Name = $name
            Status = "idle"
            LastSeen = Get-Date
            ExecutionsCount = 0
            SuccessCount = 0
            FailureCount = 0
            AvgExecutionTime = 0
            RecentFindings = @()
            CurrentTask = ""
            Progress = 0
        }
        $data.Agents += $agent
    }
    
    Save-MonitorData $data
    return $data
}

# ============================================================
# DATA PERSISTENCE
# ============================================================

function Load-MonitorData {
    if (Test-Path $Script:MonitorDB) {
        $json = Get-Content $Script:MonitorDB | ConvertFrom-Json
        return $json
    } else {
        return Initialize-Monitor
    }
}

function Save-MonitorData {
    param([object]$Data)
    $Data | ConvertTo-Json -Depth 10 | Set-Content $Script:MonitorDB -Force
}

# ============================================================
# SYSTEM METRICS
# ============================================================

function Get-SystemMetrics {
    $cpu = Get-CimInstance Win32_Processor | Select-Object -ExpandProperty LoadPercentage
    $memory = Get-CimInstance Win32_OperatingSystem | Select-Object -ExpandProperty FreePhysicalMemory
    $disk = Get-PSDrive C | Select-Object -ExpandProperty Free
    
    return @{
        CPUUsage = if ($cpu) { $cpu } else { 0 }
        MemoryUsage = [math]::Round($memory / 1GB, 2)
        DiskUsage = [math]::Round($disk / 1GB, 2)
        Timestamp = Get-Date -Format "o"
    }
}

# ============================================================
# AGENT MONITORING
# ============================================================

function Update-AgentStatus {
    param(
        [string]$AgentName,
        [string]$Status,
        [int]$ExecutionTime = 0,
        [array]$Findings = @(),
        [bool]$Success = $true
    )
    
    $data = Load-MonitorData
    $agent = $data.Agents | Where-Object { $_.Name -eq $AgentName }
    
    if ($agent) {
        $agent.Status = $Status
        $agent.LastSeen = Get-Date
        $agent.ExecutionsCount++
        
        if ($Success) {
            $agent.SuccessCount++
            $agent.RecentFindings = $Findings | Select-Object -Last 5
        } else {
            $agent.FailureCount++
        }
        
        # Calcular promedio de tiempo
        $totalTime = ($agent.AvgExecutionTime * ($agent.ExecutionsCount - 1)) + $ExecutionTime
        $agent.AvgExecutionTime = $totalTime / $agent.ExecutionsCount
        
        # Registrar en historial
        $execution = @{
            Agent = $AgentName
            Status = $Status
            Timestamp = Get-Date -Format "o"
            Duration = $ExecutionTime
            FindingsCount = $Findings.Count
            Success = $Success
        }
        $data.ExecutionHistory += $execution
        $data.TotalAnalyses++
        $data.TotalFindings += $Findings.Count
        
        Save-MonitorData $data
    }
}

function Simulate-AgentExecution {
    $agents = @("security_analyzer", "logic_checker", "smell_detector", "duplication_finder")
    
    foreach ($agent in $agents) {
        # Simular ejecución
        Update-AgentStatus -AgentName $agent -Status "running" -ExecutionTime 0
        Start-Sleep -Seconds 1
        
        $findings = @(
            @{ Type = "HIGH"; Message = "Sample finding 1" }
            @{ Type = "MEDIUM"; Message = "Sample finding 2" }
        )
        
        $success = (Get-Random -Minimum 1 -Maximum 10) -gt 1
        Update-AgentStatus -AgentName $agent -Status "idle" -ExecutionTime 2500 -Findings $findings -Success $success
    }
}

# ============================================================
# REST API
# ============================================================

function Start-MonitorAPI {
    $listener = [System.Net.HttpListener]::new()
    $listener.Prefixes.Add("http://localhost:$Script:Port/")
    
    try {
        $listener.Start()
        Write-Host "Monitor API listening on http://localhost:$Script:Port" -ForegroundColor Green
        
        while ($Script:Running) {
            $context = $listener.GetContext()
            $request = $context.Request
            $response = $context.Response
            
            # Parsing de la ruta
            $path = $request.Url.AbsolutePath
            
            switch ($path) {
                "/api/agents" {
                    Handle-AgentsAPI $response
                }
                "/api/status" {
                    Handle-StatusAPI $response
                }
                "/api/metrics" {
                    Handle-MetricsAPI $response
                }
                "/api/history" {
                    Handle-HistoryAPI $response
                }
                "/dashboard" {
                    Handle-Dashboard $response
                }
                "/" {
                    Handle-Dashboard $response
                }
                default {
                    Handle-NotFound $response
                }
            }
            
            $response.Close()
        }
    } catch {
        Write-Host "API Error: $_" -ForegroundColor Red
    } finally {
        $listener.Close()
    }
}

function Handle-AgentsAPI {
    param([System.Net.HttpListenerResponse]$Response)
    
    $data = Load-MonitorData
    $json = $data.Agents | ConvertTo-Json
    
    $Response.ContentType = "application/json"
    $Response.StatusCode = 200
    
    $buffer = [System.Text.Encoding]::UTF8.GetBytes($json)
    $Response.OutputStream.Write($buffer, 0, $buffer.Length)
}

function Handle-StatusAPI {
    param([System.Net.HttpListenerResponse]$Response)
    
    $data = Load-MonitorData
    $uptime = New-TimeSpan -Start $data.StartTime -End (Get-Date)
    
    $status = @{
        IsRunning = $true
        Uptime = $uptime.ToString()
        TotalAnalyses = $data.TotalAnalyses
        TotalFindings = $data.TotalFindings
        ActiveAgents = ($data.Agents | Where-Object { $_.Status -eq "running" }).Count
        IdleAgents = ($data.Agents | Where-Object { $_.Status -eq "idle" }).Count
        Timestamp = Get-Date -Format "o"
    } | ConvertTo-Json
    
    $Response.ContentType = "application/json"
    $Response.StatusCode = 200
    
    $buffer = [System.Text.Encoding]::UTF8.GetBytes($status)
    $Response.OutputStream.Write($buffer, 0, $buffer.Length)
}

function Handle-MetricsAPI {
    param([System.Net.HttpListenerResponse]$Response)
    
    $metrics = Get-SystemMetrics | ConvertTo-Json
    
    $Response.ContentType = "application/json"
    $Response.StatusCode = 200
    
    $buffer = [System.Text.Encoding]::UTF8.GetBytes($metrics)
    $Response.OutputStream.Write($buffer, 0, $buffer.Length)
}

function Handle-HistoryAPI {
    param([System.Net.HttpListenerResponse]$Response)
    
    $data = Load-MonitorData
    $history = $data.ExecutionHistory | Select-Object -Last 50 | ConvertTo-Json
    
    $Response.ContentType = "application/json"
    $Response.StatusCode = 200
    
    $buffer = [System.Text.Encoding]::UTF8.GetBytes($history)
    $Response.OutputStream.Write($buffer, 0, $buffer.Length)
}

function Handle-Dashboard {
    param([System.Net.HttpListenerResponse]$Response)
    
    $html = Get-DashboardHTML
    
    $Response.ContentType = "text/html; charset=utf-8"
    $Response.StatusCode = 200
    
    $buffer = [System.Text.Encoding]::UTF8.GetBytes($html)
    $Response.OutputStream.Write($buffer, 0, $buffer.Length)
}

function Handle-NotFound {
    param([System.Net.HttpListenerResponse]$Response)
    
    $Response.StatusCode = 404
    $Response.ContentType = "text/plain"
    
    $message = "Not Found"
    $buffer = [System.Text.Encoding]::UTF8.GetBytes($message)
    $Response.OutputStream.Write($buffer, 0, $buffer.Length)
}

# ============================================================
# DASHBOARD HTML
# ============================================================

function Get-DashboardHTML {
    return @"
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BAGO Agent Monitor</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: #333;
            padding: 10px;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        header {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        
        h1 {
            color: #1e3c72;
            margin-bottom: 5px;
        }
        
        .status-line {
            display: flex;
            gap: 20px;
            margin-top: 10px;
            font-size: 14px;
            color: #666;
        }
        
        .status-item {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #4CAF50;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .card-title {
            font-weight: 600;
            color: #1e3c72;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .agent-item {
            padding: 12px;
            margin-bottom: 10px;
            background: #f9f9f9;
            border-left: 4px solid #2a5298;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .agent-name {
            font-weight: 500;
        }
        
        .agent-status {
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .status-idle { background: #e3f2fd; color: #1565c0; }
        .status-running { background: #e8f5e9; color: #2e7d32; }
        .status-failed { background: #ffebee; color: #c62828; }
        
        .metrics {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-top: 10px;
        }
        
        .metric {
            background: #f0f0f0;
            padding: 10px;
            border-radius: 4px;
            text-align: center;
        }
        
        .metric-label {
            font-size: 12px;
            color: #666;
            margin-bottom: 5px;
        }
        
        .metric-value {
            font-size: 20px;
            font-weight: 600;
            color: #1e3c72;
        }
        
        .history {
            max-height: 300px;
            overflow-y: auto;
        }
        
        .history-item {
            padding: 10px;
            border-bottom: 1px solid #f0f0f0;
            font-size: 13px;
            display: flex;
            justify-content: space-between;
        }
        
        .history-time {
            color: #999;
        }
        
        footer {
            text-align: center;
            color: white;
            padding: 20px;
            font-size: 12px;
        }
        
        .refresh-btn {
            background: #2a5298;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            margin-top: 10px;
        }
        
        @media (max-width: 768px) {
            .grid {
                grid-template-columns: 1fr;
            }
            
            .metrics {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎯 BAGO Agent Monitor</h1>
            <div class="status-line">
                <div class="status-item">
                    <div class="indicator"></div>
                    <span>Sistema en línea</span>
                </div>
                <div class="status-item">
                    <span>Actualizado: <span id="timestamp">--:--:--</span></span>
                </div>
            </div>
        </header>
        
        <div class="grid">
            <div class="card">
                <div class="card-title">📊 Estado General</div>
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-label">Análisis</div>
                        <div class="metric-value" id="totalAnalyses">0</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Hallazgos</div>
                        <div class="metric-value" id="totalFindings">0</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Activos</div>
                        <div class="metric-value" id="activeAgents">0</div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-title">🤖 Agentes</div>
                <div id="agentsList"></div>
            </div>
            
            <div class="card">
                <div class="card-title">💻 Sistema</div>
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-label">CPU</div>
                        <div class="metric-value" id="cpuUsage">-</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">RAM (GB)</div>
                        <div class="metric-value" id="memoryUsage">-</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Disco (GB)</div>
                        <div class="metric-value" id="diskUsage">-</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-title">📋 Historial Reciente</div>
            <div class="history" id="historyList"></div>
            <button class="refresh-btn" onclick="refreshAll()">Actualizar Ahora</button>
        </div>
        
        <footer>
            BAGO Agent Monitor v1.0 | Monitorización en tiempo real
        </footer>
    </div>
    
    <script>
        async function fetchData(endpoint) {
            try {
                const response = await fetch('/api/' + endpoint);
                return await response.json();
            } catch (e) {
                console.error('Error fetching', endpoint, e);
                return null;
            }
        }
        
        async function updateDashboard() {
            // Actualizar estado
            const status = await fetchData('status');
            if (status) {
                document.getElementById('totalAnalyses').textContent = status.TotalAnalyses;
                document.getElementById('totalFindings').textContent = status.TotalFindings;
                document.getElementById('activeAgents').textContent = status.ActiveAgents;
                document.getElementById('timestamp').textContent = new Date().toLocaleTimeString();
            }
            
            // Actualizar agentes
            const agents = await fetchData('agents');
            if (agents) {
                const list = document.getElementById('agentsList');
                list.innerHTML = agents.map(agent => \`
                    <div class="agent-item">
                        <div>
                            <div class="agent-name">\${agent.Name}</div>
                            <div style="font-size: 12px; color: #999;">
                                Ejecuciones: \${agent.ExecutionsCount} | Éxitos: \${agent.SuccessCount}
                            </div>
                        </div>
                        <span class="agent-status status-\${agent.Status}">\${agent.Status.toUpperCase()}</span>
                    </div>
                \`).join('');
            }
            
            // Actualizar métricas del sistema
            const metrics = await fetchData('metrics');
            if (metrics) {
                document.getElementById('cpuUsage').textContent = metrics.CPUUsage + '%';
                document.getElementById('memoryUsage').textContent = metrics.MemoryUsage;
                document.getElementById('diskUsage').textContent = metrics.DiskUsage;
            }
            
            // Actualizar historial
            const history = await fetchData('history');
            if (history) {
                const list = document.getElementById('historyList');
                list.innerHTML = history.slice(-10).reverse().map(item => \`
                    <div class="history-item">
                        <span>\${item.Agent}: \${item.Status} (\${item.FindingsCount} hallazgos)</span>
                        <span class="history-time">\${new Date(item.Timestamp).toLocaleTimeString()}</span>
                    </div>
                \`).join('');
            }
        }
        
        function refreshAll() {
            updateDashboard();
        }
        
        // Actualizar cada 5 segundos
        updateDashboard();
        setInterval(updateDashboard, 5000);
    </script>
</body>
</html>
"@
}

# ============================================================
# MAIN LOOP
# ============================================================

function Start-Monitor {
    Write-Host "BAGO Agent Monitor Service" -ForegroundColor Cyan
    Write-Host "=========================" -ForegroundColor Cyan
    Write-Host "Port: $Script:Port" -ForegroundColor Green
    Write-Host "Interval: ${Script:Interval}s" -ForegroundColor Green
    Write-Host ""
    Write-Host "Access dashboard at: http://localhost:$Script:Port" -ForegroundColor Yellow
    Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
    Write-Host ""
    
    # Inicializar datos
    Initialize-Monitor | Out-Null
    
    # Iniciar API en background
    $apiJob = Start-Job -ScriptBlock {
        param($Port, $BAGOPath)
        . "$BAGOPath\agents-monitor-service.ps1" -Port $Port
    } -ArgumentList $Script:Port, $Script:BAGOPath
    
    # Monitoreo principal
    while ($Script:Running) {
        try {
            Simulate-AgentExecution
            Start-Sleep -Seconds $Script:Interval
        } catch {
            Write-Host "Error: $_" -ForegroundColor Red
        }
    }
    
    # Limpiar
    Stop-Job $apiJob -ErrorAction SilentlyContinue
}

# ============================================================
# ENTRY POINT
# ============================================================

Start-Monitor
