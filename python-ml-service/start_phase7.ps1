#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Phase 7 Integration & Testing - PowerShell Orchestration Script

.DESCRIPTION
    Starts all HyperGPU components and runs comprehensive integration tests.
    
.PARAMETER Mode
    Operation mode: system, tests, or all
    
.PARAMETER Frontend
    Whether to start the frontend dashboard (default: true)
    
.PARAMETER Nodes
    Number of simulated nodes to start (default: 5)

.EXAMPLE
    .\start_phase7.ps1 -Mode all
    .\start_phase7.ps1 -Mode system -Nodes 10
    .\start_phase7.ps1 -Mode tests
#>

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('system', 'tests', 'all')]
    [string]$Mode = 'all',
    
    [Parameter(Mandatory=$false)]
    [bool]$Frontend = $true,
    
    [Parameter(Mandatory=$false)]
    [int]$Nodes = 5
)

$ErrorActionPreference = "Stop"

# Colors for output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Header {
    param([string]$Message)
    Write-Host ""
    Write-Host ("=" * 80) -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Cyan
    Write-Host ("=" * 80) -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Yellow
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

# Check if in virtual environment
function Test-VirtualEnv {
    if ($env:VIRTUAL_ENV) {
        Write-Success "Virtual environment active: $env:VIRTUAL_ENV"
        return $true
    } else {
        Write-Error "No virtual environment detected"
        Write-Host "Please activate the virtual environment first:"
        Write-Host "  .venv\Scripts\Activate.ps1"
        return $false
    }
}

# Install dependencies
function Install-Dependencies {
    Write-Step "Installing Python dependencies..."
    
    pip install --upgrade pip
    pip install -r requirements.txt
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Dependencies installed"
        return $true
    } else {
        Write-Error "Failed to install dependencies"
        return $false
    }
}

# Run tests
function Invoke-Tests {
    Write-Header "RUNNING PHASE 7 TEST SUITE"
    
    Write-Step "Running end-to-end training tests..."
    python -m pytest tests/test_e2e_training.py -v -s --tb=short
    $test1 = $LASTEXITCODE
    
    Write-Step "Running network resilience tests..."
    python -m pytest tests/test_resilience.py -v -s --tb=short
    $test2 = $LASTEXITCODE
    
    Write-Step "Running performance benchmarks..."
    python -m pytest tests/test_performance.py -v -s --tb=short
    $test3 = $LASTEXITCODE
    
    if ($test1 -eq 0 -and $test2 -eq 0 -and $test3 -eq 0) {
        Write-Header "ALL TESTS PASSED ✓"
        return $true
    } else {
        Write-Header "SOME TESTS FAILED ✗"
        Write-Error "Test results: E2E=$test1, Resilience=$test2, Performance=$test3"
        return $false
    }
}

# Start the system
function Start-System {
    Write-Header "STARTING HYPERGPU SYSTEM"
    
    Write-Step "Starting coordinator, API server, and nodes..."
    
    $frontendFlag = if ($Frontend) { "--frontend" } else { "" }
    
    python run_phase7.py system --nodes $Nodes $frontendFlag
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "System started successfully"
        return $true
    } else {
        Write-Error "System failed to start"
        return $false
    }
}

# Main execution
Write-Header "HYPERGPU PHASE 7: INTEGRATION & END-TO-END TESTING"

# Check virtual environment
if (-not (Test-VirtualEnv)) {
    exit 1
}

# Check dependencies
Write-Step "Checking dependencies..."
$depsOk = Install-Dependencies
if (-not $depsOk) {
    Write-Error "Dependency installation failed"
    exit 1
}

# Execute based on mode
switch ($Mode) {
    'tests' {
        $success = Invoke-Tests
        if (-not $success) { exit 1 }
    }
    'system' {
        $success = Start-System
        if (-not $success) { exit 1 }
    }
    'all' {
        Write-Header "PHASE 1: RUNNING TESTS"
        $testSuccess = Invoke-Tests
        
        if ($testSuccess) {
            Write-Header "PHASE 2: STARTING SYSTEM"
            $systemSuccess = Start-System
            
            if (-not $systemSuccess) {
                Write-Error "System failed to start"
                exit 1
            }
        } else {
            Write-Error "Tests failed! Fix issues before starting system."
            exit 1
        }
    }
}

Write-Header "PHASE 7 COMPLETE ✓"
Write-Host ""
Write-Host "System Components:" -ForegroundColor Cyan
Write-Host "  - API Server: http://localhost:8000" -ForegroundColor White
Write-Host "  - API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  - WebSocket: ws://localhost:8000/ws" -ForegroundColor White
if ($Frontend) {
    Write-Host "  - Frontend: http://localhost:3000" -ForegroundColor White
}
Write-Host ""
Write-Host "Press Ctrl+C to stop the system" -ForegroundColor Yellow

