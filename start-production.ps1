# API Sentinel - Production Launch Script
# Builds the production React frontend and serves everything via FastAPI (Port 8000)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "         API SENTINEL - PRODUCTION ENVIRONMENT            " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Prerequisite Checks
Write-Host "`n[1/5] Checking Prerequisites..." -ForegroundColor Yellow

try {
    $pythonVersion = python --version 2>&1
    Write-Host "  Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Python is not installed or not in PATH." -ForegroundColor Red
    exit 1
}

try {
    $nodeVersion = node --version 2>&1
    Write-Host "  Found Node: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Node.js is not installed or not in PATH." -ForegroundColor Red
    exit 1
}

# 2. Compile Production Frontend
Write-Host "`n[2/5] Building Production Frontend Assets..." -ForegroundColor Yellow
Set-Location "$ScriptDir\frontend"
cmd.exe /c "npm run build"
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [ERROR] Production frontend build failed." -ForegroundColor Red
    exit 1
}

# Sync to backend static mount
$backendDist = "$ScriptDir\backend\frontend\dist"
if (-not (Test-Path $backendDist)) {
    New-Item -ItemType Directory -Path $backendDist -Force | Out-Null
}
Copy-Item -Path "$ScriptDir\frontend\dist\*" -Destination $backendDist -Recurse -Force
Write-Host "  Compiled assets synchronized to backend static mount." -ForegroundColor Green
Set-Location $ScriptDir

# 3. Port Conflict Checks (8000, 8001)
Write-Host "`n[3/5] Checking Port Availability (8000, 8001)..." -ForegroundColor Yellow
$ports = @(8000, 8001)
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
Write-Host "  All required production ports (8000, 8001) are available." -ForegroundColor Green

# 4. Launch Production Services
Write-Host "`n[4/5] Launching Production Core Services..." -ForegroundColor Yellow
$pids = @{}

# Demo API (8001)
$demoProc = Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "demo_api.main:app", "--host", "127.0.0.1", "--port", "8001" -WorkingDirectory $ScriptDir -PassThru
$pids["demo_api"] = $demoProc.Id
Write-Host "  Demo API started (PID $($demoProc.Id)) on http://127.0.0.1:8001" -ForegroundColor Green

# FastAPI Production Backend (8000)
$backendProc = Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000" -WorkingDirectory "$ScriptDir\backend" -PassThru
$pids["backend"] = $backendProc.Id
Write-Host "  FastAPI Production Server started (PID $($backendProc.Id)) on http://127.0.0.1:8000" -ForegroundColor Green

# Save PIDs
$pids | ConvertTo-Json | Set-Content "$ScriptDir\.sentinel_pids.json" -Encoding UTF8

# 5. Summary
Write-Host "`n[5/5] Production Environment Ready!" -ForegroundColor Cyan
Write-Host "----------------------------------------------------------" -ForegroundColor Gray
Write-Host "  Production Dashboard URL:     http://127.0.0.1:8000/" -ForegroundColor Cyan
Write-Host "  API Documentation:            http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host "  Healthcare Demo API:          http://127.0.0.1:8001/health" -ForegroundColor Cyan
Write-Host "----------------------------------------------------------" -ForegroundColor Gray
Write-Host "  To stop all services cleanly, run: .\stop-api-sentinel.ps1" -ForegroundColor Yellow
