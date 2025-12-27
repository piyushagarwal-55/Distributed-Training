#!/bin/bash

# HyperGPU - Complete Setup and Start Script
# This script installs all dependencies and starts the development environment

set -e

echo "=============================================="
echo "  HyperGPU - Distributed AI Training Platform"
echo "=============================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check prerequisites
echo "Checking prerequisites..."

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node -v)
    print_status "Node.js found: $NODE_VERSION"
else
    print_error "Node.js not found. Please install Node.js 18+"
    exit 1
fi

# Check npm
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm -v)
    print_status "npm found: $NPM_VERSION"
else
    print_error "npm not found"
    exit 1
fi

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    print_status "Python found: $PYTHON_VERSION"
else
    print_warning "Python3 not found - backend may not work"
fi

echo ""
echo "=============================================="
echo "  Installing Dependencies"
echo "=============================================="
echo ""

# Install root dependencies
echo "Installing root dependencies..."
npm install
print_status "Root dependencies installed"

# Install frontend dependencies
echo ""
echo "Installing frontend dependencies..."
cd frontend
npm install
cd ..
print_status "Frontend dependencies installed"

# Install smart contract dependencies
echo ""
echo "Installing smart contract dependencies..."
cd smart-contracts
npm install
cd ..
print_status "Smart contract dependencies installed"

# Install Python dependencies (if Python available)
if command -v python3 &> /dev/null; then
    echo ""
    echo "Installing Python dependencies..."
    cd python-ml-service
    if [ -f "requirements.txt" ]; then
        python3 -m pip install -r requirements.txt --quiet 2>/dev/null || print_warning "Some Python packages may have failed"
    fi
    cd ..
    print_status "Python dependencies installed"
fi

# Compile smart contracts
echo ""
echo "Compiling smart contracts..."
cd smart-contracts
# Use yes to auto-accept Hardhat telemetry prompt
yes n | npx hardhat compile 2>/dev/null || npx hardhat compile
cd ..
print_status "Smart contracts compiled"

echo ""
echo "=============================================="
echo "  Starting Development Environment"
echo "=============================================="
echo ""

echo "Starting all services..."
echo ""
echo "  📡 Backend API:    http://localhost:8000"
echo "  🌐 Frontend:       http://localhost:3000"
echo "  ⛓️  Blockchain:     http://localhost:8546"
echo "  📚 API Docs:       http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Start all services using npm
npm start
