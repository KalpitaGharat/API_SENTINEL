# API Sentinel - Development Launch Script
# Starts Demo API (8001), FastAPI Core (8000), and React Vite Dev Server (5173)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "         API SENTINEL - DEVELOPMENT ENVIRONMENT           " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Prerequisite Checks
Write-Host "`n[1/4] Checking Prerequisites..." -ForegroundColor Yellow

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Python is not installed or not in PATH." -ForegroundColor Red
    exit 1
}

# Check Node
try {
    $nodeVersion = node --version 2>&1
    Write-Host "  Found Node: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Node.js is not installed or not in PATH." -ForegroundColor Red
    exit 1
}

# Check .env
if (-not (Test-Path "$ScriptDir\backend\.env")) {
    Write-Host "  backend\.env not found. Creating from .env.example..." -ForegroundColor Yellow
    Copy-Item "$ScriptDir\backend\.env.example" "$ScriptDir\backend\.env"
}

# 2. Port Conflict Checks
Write-Host "`n[2/4] Checking Port Availability (8000, 8001, 5173)..." -ForegroundColor Yellow
$ports = @(8000, 8001, 5173)
$conflicts = @()

foreach ($p in $ports) {
    $active = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue
    if ($active) {
        $conflicts += $p
    }
}

if ($conflicts.Count -gt 0) {
    Write-Host "  [ERROR] Port conflicts detected on port(s): $($conflicts -join ', ')" -ForegroundColor Red
    Write-Host "  Run .\stop-api-sentinel.ps1 or close conflicting applications before starting." -ForegroundColor Yellow
    exit 1
}
Write-Host "  All required ports (8000, 8001, 5173) are available." -ForegroundColor Green

# 3. Launch Services
Write-Host "`n[3/4] Launching Services..." -ForegroundColor Yellow
$pids = @{}

# Demo API (8001)
$demoProc = Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "demo_api.main:app", "--host", "127.0.0.1", "--port", "8001" -WorkingDirectory $ScriptDir -PassThru
$pids["demo_api"] = $demoProc.Id
Write-Host "  Demo API started (PID $($demoProc.Id)) on http://127.0.0.1:8001" -ForegroundColor Green

# FastAPI Backend (8000)
$backendProc = Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000" -WorkingDirectory "$ScriptDir\backend" -PassThru
$pids["backend"] = $backendProc.Id
Write-Host "  FastAPI Backend started (PID $($backendProc.Id)) on http://127.0.0.1:8000" -ForegroundColor Green

# Vite Frontend (5173)
$frontendProc = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "npm run dev -- --host 127.0.0.1 --port 5173" -WorkingDirectory "$ScriptDir\frontend" -PassThru
$pids["frontend"] = $frontendProc.Id
Write-Host "  Vite Dev Server started (PID $($frontendProc.Id)) on http://127.0.0.1:5173" -ForegroundColor Green

# Save PIDs for clean shutdown
$pids | ConvertTo-Json | Set-Content "$ScriptDir\.sentinel_pids.json" -Encoding UTF8

# 4. Status Summary
Write-Host "`n[4/4] Environment Ready!" -ForegroundColor Cyan
Write-Host "----------------------------------------------------------" -ForegroundColor Gray
Write-Host "  React Dashboard (Vite Dev):   http://127.0.0.1:5173/" -ForegroundColor Cyan
Write-Host "  FastAPI Core & API Docs:     http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host "  Healthcare Demo API:          http://127.0.0.1:8001/health" -ForegroundColor Cyan
Write-Host "----------------------------------------------------------" -ForegroundColor Gray
Write-Host "  To stop all services cleanly, run: .\stop-api-sentinel.ps1" -ForegroundColor Yellow
