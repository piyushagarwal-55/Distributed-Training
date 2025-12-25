#!/bin/bash
# HyperGPU Phase 1 Setup Script for Linux/WSL
# Run this script to set up the Python environment and validate Phase 1 implementation

set -e  # Exit on error

echo "================================================================================"
echo "                HyperGPU Phase 1 Environment Setup (Linux/WSL)                "
echo "================================================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Check Python installation
echo -e "${YELLOW}[1/6] Checking Python installation...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓ Found: $PYTHON_VERSION${NC}"
    
    # Check version is 3.9+
    VERSION_NUM=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    if (( $(echo "$VERSION_NUM < 3.9" | bc -l) )); then
        echo -e "${RED}✗ Python 3.9 or higher is required${NC}"
        exit 1
    fi
else
    echo -e "${RED}✗ Python3 not found. Please install Python 3.9 or higher${NC}"
    exit 1
fi

# Get project root directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON_SERVICE_DIR="$PROJECT_ROOT/python-ml-service"

# Navigate to python-ml-service directory
echo ""
echo -e "${YELLOW}[2/6] Navigating to python-ml-service directory...${NC}"
if [ -d "$PYTHON_SERVICE_DIR" ]; then
    cd "$PYTHON_SERVICE_DIR"
    echo -e "${GREEN}✓ Changed to: $PYTHON_SERVICE_DIR${NC}"
else
    echo -e "${RED}✗ Directory not found: $PYTHON_SERVICE_DIR${NC}"
    exit 1
fi

# Create virtual environment
echo ""
echo -e "${YELLOW}[3/6] Creating Python virtual environment...${NC}"
if [ -d "venv" ]; then
    echo -e "${CYAN}ℹ Virtual environment already exists, skipping creation${NC}"
else
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created successfully${NC}"
fi

# Activate virtual environment
echo ""
echo -e "${YELLOW}[4/6] Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Upgrade pip
echo ""
echo -e "${YELLOW}[5/6] Upgrading pip...${NC}"
pip install --upgrade pip --quiet
echo -e "${GREEN}✓ pip upgraded successfully${NC}"

# Install dependencies
echo ""
echo -e "${YELLOW}[6/6] Installing dependencies (this may take a few minutes)...${NC}"
pip install -r requirements.txt --quiet
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Dependencies installed successfully${NC}"
else
    echo -e "${RED}✗ Failed to install dependencies${NC}"
    echo -e "${YELLOW}Try running: pip install -r requirements.txt${NC}"
    exit 1
fi

# Create logs directory
echo ""
echo -e "${YELLOW}Creating logs directory...${NC}"
if [ ! -d "logs" ]; then
    mkdir -p logs
    echo -e "${GREEN}✓ Logs directory created${NC}"
else
    echo -e "${CYAN}ℹ Logs directory already exists${NC}"
fi

# Run validation
echo ""
echo "================================================================================"
echo "                         Running Phase 1 Validation                            "
echo "================================================================================"
echo ""

cd "$PROJECT_ROOT"
python3 test-files/validate_phase1.py

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}================================================================================"
    echo "                   ✓ Phase 1 Setup Complete!                                  "
    echo "================================================================================${NC}"
    echo ""
    echo -e "${CYAN}Next steps:${NC}"
    echo "  1. Activate virtual environment: cd python-ml-service && source venv/bin/activate"
    echo "  2. Run tests: pytest"
    echo "  3. Test configuration: python -m src.main --validate-only"
    echo "  4. Proceed to Phase 2 implementation"
    echo ""
else
    echo ""
    echo -e "${RED}================================================================================"
    echo "                   ✗ Phase 1 Validation Failed                                "
    echo "================================================================================${NC}"
    echo ""
    echo -e "${YELLOW}Please review the errors above and fix them before proceeding.${NC}"
    echo ""
    exit 1
fi
