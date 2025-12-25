#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Start Complete Distributed Training System
.DESCRIPTION
    Starts all components: Backend API, Frontend Dashboard, and Blockchain
#>

param(
    [switch]$SkipBlockchain,
    [switch]$Help
)

if ($Help) {
    Write-Host @"
Start Complete Distributed Training System

USAGE:
    .\start_complete_system.ps1 [-SkipBlockchain]

OPTIONS:
    -SkipBlockchain    Skip blockchain startup (use for testing without blockchain)
    -Help              Show this help message

COMPONENTS STARTED:
    1. Backend API Server (FastAPI) - Port 8000
    2. Frontend Dashboard (Next.js) - Port 3000
    3. Blockchain Node (Hardhat) - Port 8545 (optional)

AFTER STARTUP:
    - Frontend: http://localhost:3000
    - API Docs: http://localhost:8000/docs
    - API Health: http://localhost:8000/health

STOPPING:
    Press Ctrl+C to stop all components
"@
    exit 0
}

$ErrorActionPreference = "Stop"

# Colors
function Write-Success { param($msg) Write-Host $msg -ForegroundColor Green }
function Write-Error-Custom { param($msg) Write-Host $msg -ForegroundColor Red }
function Write-Info { param($msg) Write-Host $msg -ForegroundColor Cyan }
function Write-Warning-Custom { param($msg) Write-Host $msg -ForegroundColor Yellow }

Write-Host @"
================================================================================
🚀 Starting Complete Distributed Training System
================================================================================
"@ -ForegroundColor Cyan

# Store all background jobs
$global:jobs = @()

# Cleanup function
function Stop-AllComponents {
    Write-Info "`n🛑 Stopping all components..."
    
    foreach ($job in $global:jobs) {
        if ($job.Process -and !$job.Process.HasExited) {
            Write-Info "  Stopping $($job.Name)..."
            try {
                $job.Process.Kill($true)
                $job.Process.WaitForExit(5000)
            } catch {
                Write-Warning-Custom "  Failed to stop $($job.Name): $_"
            }
        }
    }
    
    Write-Success "✓ All components stopped"
    exit 0
}

# Register cleanup handler
Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action {
    Stop-AllComponents
}

try {
    # Check Python
    Write-Info "[1/5] Checking Python environment..."
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCmd) {
        Write-Error-Custom "✗ Python not found. Please install Python 3.8+"
        exit 1
    }
    $pythonVersion = & python --version 2>&1
    Write-Success "✓ Python: $pythonVersion"

    # Check Node.js
    Write-Info "[2/5] Checking Node.js environment..."
    $nodeCmd = Get-Command node -ErrorAction SilentlyContinue
    if (-not $nodeCmd) {
        Write-Error-Custom "✗ Node.js not found. Please install Node.js 16+"
        exit 1
    }
    $nodeVersion = & node --version 2>&1
    Write-Success "✓ Node.js: $nodeVersion"

    # Check npm
    $npmCmd = Get-Command npm -ErrorAction SilentlyContinue
    if (-not $npmCmd) {
        Write-Error-Custom "✗ npm not found. Please install npm"
        exit 1
    }

    Write-Success "✓ All prerequisites met"
    Write-Host ""

    # Start Blockchain (if not skipped)
    if (-not $SkipBlockchain) {
        Write-Info "[3/5] Starting Blockchain Node (Hardhat)..."
        $blockchainPath = Join-Path $PSScriptRoot "smart-contracts"
        
        if (Test-Path $blockchainPath) {
            Push-Location $blockchainPath
            
            # Check if node_modules exists
            if (-not (Test-Path "node_modules")) {
                Write-Info "  Installing blockchain dependencies..."
                & npm install --silent
            }
            
            Write-Info "  Starting Hardhat node on port 8545..."
            $blockchainProcess = Start-Process -FilePath "npx" `
                -ArgumentList "hardhat", "node" `
                -WorkingDirectory $blockchainPath `
                -PassThru `
                -WindowStyle Hidden
            
            $global:jobs += @{
                Name = "Blockchain"
                Process = $blockchainProcess
            }
            
            Write-Success "✓ Blockchain started (PID: $($blockchainProcess.Id))"
            Start-Sleep -Seconds 3
            Pop-Location
        } else {
            Write-Warning-Custom "⚠ Blockchain directory not found, skipping..."
        }
    } else {
        Write-Info "[3/5] Skipping Blockchain (--SkipBlockchain flag)"
    }

    # Start Backend API
    Write-Info "[4/5] Starting Backend API Server..."
    $backendPath = Join-Path $PSScriptRoot "python-ml-service"
    
    if (Test-Path $backendPath) {
        Push-Location $backendPath
        
        Write-Info "  Starting FastAPI server on port 8000..."
        $backendProcess = Start-Process -FilePath "python" `
            -ArgumentList "-m", "uvicorn", "src.api.rest_server:app", "--host", "0.0.0.0", "--port", "8000", "--reload" `
            -WorkingDirectory $backendPath `
            -PassThru `
            -WindowStyle Hidden
        
        $global:jobs += @{
            Name = "Backend API"
            Process = $backendProcess
        }
        
        Write-Success "✓ Backend API started (PID: $($backendProcess.Id))"
        Start-Sleep -Seconds 2
        Pop-Location
    } else {
        Write-Error-Custom "✗ Backend directory not found: $backendPath"
        Stop-AllComponents
        exit 1
    }

    # Start Frontend
    Write-Info "[5/5] Starting Frontend Dashboard..."
    $frontendPath = Join-Path $PSScriptRoot "frontend"
    
    if (Test-Path $frontendPath) {
        Push-Location $frontendPath
        
        # Check if node_modules exists
        if (-not (Test-Path "node_modules")) {
            Write-Info "  Installing frontend dependencies..."
            & npm install --silent
        }
        
        Write-Info "  Starting Next.js on port 3000..."
        $frontendProcess = Start-Process -FilePath "npm" `
            -ArgumentList "run", "dev" `
            -WorkingDirectory $frontendPath `
            -PassThru `
            -WindowStyle Hidden
        
        $global:jobs += @{
            Name = "Frontend"
            Process = $frontendProcess
        }
        
        Write-Success "✓ Frontend started (PID: $($frontendProcess.Id))"
        Pop-Location
    } else {
        Write-Error-Custom "✗ Frontend directory not found: $frontendPath"
        Stop-AllComponents
        exit 1
    }

    Write-Host ""
    Write-Host @"
================================================================================
✅ System Started Successfully!
================================================================================

🌐 Access Points:
   Frontend Dashboard: http://localhost:3000
   Backend API Docs:   http://localhost:8000/docs
   API Health Check:   http://localhost:8000/health
   Blockchain RPC:     http://localhost:8545 (if enabled)

📊 Components Running:
"@ -ForegroundColor Green

    foreach ($job in $global:jobs) {
        Write-Host "   ✓ $($job.Name) (PID: $($job.Process.Id))" -ForegroundColor Green
    }

    Write-Host @"

🔧 Quick Actions:
   • Open Dashboard: start http://localhost:3000
   • View API Docs:  start http://localhost:8000/docs
   • Stop System:    Press Ctrl+C

================================================================================
"@ -ForegroundColor Cyan

    Write-Info "⏳ Waiting for components to initialize..."
    Start-Sleep -Seconds 5

    Write-Success "`n✓ All components ready!"
    Write-Info "Opening dashboard in browser..."
    Start-Sleep -Seconds 2
    Start-Process "http://localhost:3000"

    Write-Host "`n📝 System is running. Press Ctrl+C to stop all components.`n" -ForegroundColor Yellow

    # Keep script running and monitor processes
    while ($true) {
        Start-Sleep -Seconds 5
        
        # Check if any process has died
        foreach ($job in $global:jobs) {
            if ($job.Process.HasExited) {
                Write-Error-Custom "`n✗ $($job.Name) has stopped unexpectedly!"
                Write-Info "Exit code: $($job.Process.ExitCode)"
                Stop-AllComponents
                exit 1
            }
        }
    }

} catch {
    Write-Error-Custom "`n✗ Error occurred: $_"
    Write-Error-Custom $_.ScriptStackTrace
    Stop-AllComponents
    exit 1
} finally {
    # Ensure cleanup on exit
    if ($global:jobs.Count -gt 0) {
        Stop-AllComponents
    }
}
