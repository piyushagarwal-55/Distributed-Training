.PHONY: help install dev test build deploy clean

# Default target
help:
	@echo "HyperGPU - Distributed AI Training Platform"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  install     Install all dependencies"
	@echo "  dev         Start development environment"
	@echo "  test        Run all tests"
	@echo "  test-contracts  Run smart contract tests"
	@echo "  test-backend    Run backend tests"
	@echo "  test-frontend   Run frontend tests"
	@echo "  build       Build all components"
	@echo "  docker-up   Start Docker containers"
	@echo "  docker-down Stop Docker containers"
	@echo "  clean       Clean build artifacts"

# Install all dependencies
install:
	npm install
	cd frontend && npm install
	cd smart-contracts && npm install
	cd python-ml-service && pip install -r requirements.txt

# Start development environment
dev:
	npm start

# Run all tests
test: test-contracts test-backend

# Smart contract tests
test-contracts:
	cd smart-contracts && npx hardhat test

# Backend tests
test-backend:
	cd python-ml-service && pytest tests/ -v

# Frontend tests
test-frontend:
	cd frontend && npm test

# Build all components
build:
	cd smart-contracts && npx hardhat compile
	cd frontend && npm run build

# Docker commands
docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

# Clean build artifacts
clean:
	rm -rf frontend/.next
	rm -rf frontend/node_modules
	rm -rf smart-contracts/artifacts
	rm -rf smart-contracts/cache
	rm -rf smart-contracts/node_modules
	rm -rf python-ml-service/__pycache__
	rm -rf python-ml-service/.pytest_cache

# Deploy contracts to testnet
deploy-testnet:
	cd smart-contracts && npx hardhat run scripts/deploy.js --network monad_testnet

# Gas report
gas-report:
	cd smart-contracts && REPORT_GAS=true npx hardhat test
