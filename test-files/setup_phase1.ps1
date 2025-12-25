# HyperGPU Phase 1 Setup Script
# Run this script to set up the Python environment and validate Phase 1 implementation

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "                HyperGPU Phase 1 Environment Setup                              " -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Store original location
$originalLocation = Get-Location

# Check Python installation
Write-Host "[1/6] Checking Python installation..." -ForegroundColor Yellow
$pythonCheck = & python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Found: $pythonCheck" -ForegroundColor Green
} else {
    Write-Host "✗ Python not found. Please install Python 3.9 or higher" -ForegroundColor Red
    exit 1
}

# Navigate to python-ml-service directory
Write-Host ""
Write-Host "[2/6] Navigating to python-ml-service directory..." -ForegroundColor Yellow
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonServiceDir = Join-Path $projectRoot "python-ml-service"

if (Test-Path $pythonServiceDir) {
    Set-Location $pythonServiceDir
    Write-Host "✓ Changed to: $pythonServiceDir" -ForegroundColor Green
} else {
    Write-Host "✗ Directory not found: $pythonServiceDir" -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host ""
Write-Host "[3/6] Creating Python virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "ℹ Virtual environment already exists, skipping creation" -ForegroundColor Cyan
} else {
    python -m venv venv
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Virtual environment created successfully" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to create virtual environment" -ForegroundColor Red
        Set-Location $originalLocation
        exit 1
    }
}

# Activate virtual environment
Write-Host ""
Write-Host "[4/6] Activating virtual environment..." -ForegroundColor Yellow
$activateScript = "venv\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
    Write-Host "✓ Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "✗ Activation script not found: $activateScript" -ForegroundColor Red
    Set-Location $originalLocation
    exit 1
}

# Upgrade pip
Write-Host ""
Write-Host "[5/6] Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ pip upgraded successfully" -ForegroundColor Green
} else {
    Write-Host "⚠ Warning: pip upgrade failed, continuing anyway" -ForegroundColor Yellow
}

# Install dependencies
Write-Host ""
Write-Host "[6/6] Installing dependencies (this may take a few minutes)..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Dependencies installed successfully" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to install dependencies" -ForegroundColor Red
    Write-Host "Try running: pip install -r requirements.txt" -ForegroundColor Yellow
    Set-Location $originalLocation
    exit 1
}

# Create logs directory
Write-Host ""
Write-Host "Creating logs directory..." -ForegroundColor Yellow
$logsDir = "logs"
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir | Out-Null
    Write-Host "✓ Logs directory created" -ForegroundColor Green
} else {
    Write-Host "ℹ Logs directory already exists" -ForegroundColor Cyan
}

# Run validation
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "                         Running Phase 1 Validation                            " -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $projectRoot
python test-files\validate_phase1.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Green
    Write-Host "                   ✓ Phase 1 Setup Complete!                                  " -ForegroundColor Green
    Write-Host "================================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Activate virtual environment: cd python-ml-service; venv\Scripts\activate" -ForegroundColor White
    Write-Host "  2. Run tests: pytest" -ForegroundColor White
    Write-Host "  3. Test configuration: python -m src.main --validate-only" -ForegroundColor White
    Write-Host "  4. Proceed to Phase 2 implementation" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Red
    Write-Host "                   ✗ Phase 1 Validation Failed                                " -ForegroundColor Red
    Write-Host "================================================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please review the errors above and fix them before proceeding." -ForegroundColor Yellow
    Write-Host ""
}

# Return to original location
Set-Location $originalLocation
