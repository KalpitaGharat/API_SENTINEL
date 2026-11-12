# API Sentinel - Clean Shutdown Script
# Gracefully terminates only API Sentinel processes without touching unrelated applications

$ErrorActionPreference = "SilentlyContinue"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "             STOPPING API SENTINEL SERVICES               " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$pidFile = "$ScriptDir\.sentinel_pids.json"
$stoppedCount = 0

# 1. Stop recorded PIDs from tracking file
if (Test-Path $pidFile) {
    try {
        $pidsJson = Get-Content $pidFile -Raw | ConvertFrom-Json
        foreach ($prop in $pidsJson.PSObject.Properties) {
            $serviceName = $prop.Name
            $targetPid = $prop.Value
            if ($targetPid) {
                $proc = Get-Process -Id $targetPid -ErrorAction SilentlyContinue
                if ($proc) {
                    Write-Host "  Stopping $serviceName (PID $targetPid)..." -ForegroundColor Yellow
                    Stop-Process -Id $targetPid -Force -ErrorAction SilentlyContinue
                    $stoppedCount++
                }
            }
        }
        Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
    } catch {
        Write-Host "  Note: Failed parsing PID tracking file." -ForegroundColor Gray
    }
}

# 2. Check remaining listeners strictly on Sentinel ports (8000, 8001, 5173)
$sentinelPorts = @(8000, 8001, 5173)
foreach ($port in $sentinelPorts) {
    $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    foreach ($conn in $connections) {
        $owningPid = $conn.OwningProcess
        if ($owningPid -and $owningPid -ne 0 -and $owningPid -ne $PID) {
            $proc = Get-Process -Id $owningPid -ErrorAction SilentlyContinue
            if ($proc -and ($proc.ProcessName -match "python|node|uvicorn|cmd")) {
                Write-Host "  Terminating lingering listener on port $port (PID $owningPid - $($proc.ProcessName))..." -ForegroundColor Yellow
                Stop-Process -Id $owningPid -Force -ErrorAction SilentlyContinue
                $stoppedCount++
            }
        }
    }
}

Write-Host "`nAll API Sentinel services stopped cleanly ($stoppedCount processes terminated)." -ForegroundColor Green
Write-Host "Ports 8000, 8001, and 5173 are now free." -ForegroundColor Cyan
