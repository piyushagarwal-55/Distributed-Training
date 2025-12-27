# HyperGPU: Network-Aware Distributed AI Training

> **🎯 Production-Ready Distributed Federated Learning Platform**
> 
> Intelligently adapts to real-world network conditions with blockchain-based incentive mechanisms.

[![CI/CD](https://github.com/yourusername/hypergpu/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/hypergpu/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![Solidity 0.8.20](https://img.shields.io/badge/solidity-0.8.20-purple.svg)](https://soliditylang.org/)

---

## 🌟 Overview

HyperGPU is a revolutionary distributed AI training platform that intelligently adapts to real-world network conditions across distributed GPU nodes. By combining network-aware optimization with blockchain-based incentive mechanisms, we create a system that matches or exceeds centralized training performance.

## 🚀 Key Features

- 🌐 **Network-Aware Optimization**: Dynamically adapts to latency, packet loss, and bandwidth
- ⛓️ **Blockchain Integration**: Transparent contribution tracking and rewards via Monad testnet
- 🎯 **Adaptive Training**: Smart batch sizing, gradient routing, and node selection
- 📊 **Real-Time Dashboard**: Comprehensive visualization with WebSocket updates
- 🔒 **Production Security**: Rate limiting, authentication, and input validation
- 🐳 **Docker Ready**: Full containerization with monitoring stack

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                       │
│              http://localhost:3000                           │
│   • Dashboard • Nodes • Training • Blockchain • Settings    │
└────────────────────┬────────────────────────────────────────┘
                     │ REST API + WebSocket
                     ↓
┌─────────────────────────────────────────────────────────────┐
│              Backend (FastAPI/Python)                        │
│              http://localhost:8000                           │
│   • Training Coordinator • Node Registry • Metrics API      │
└──────┬──────────────────────────────────┬───────────────────┘
       │                                  │
       ↓                                  ↓
┌──────────────────┐          ┌─────────────────────────────┐
│  GPU Nodes       │          │  Smart Contracts (Monad)    │
│  (Distributed)   │          │  Port: 8546                 │
└──────────────────┘          └─────────────────────────────┘
```

## 📂 Project Structure

```
hypergpu/
├── 📁 frontend/                 # Next.js Dashboard
│   ├── src/
│   │   ├── components/         # React components (atoms/molecules/organisms)
│   │   ├── pages/              # Next.js pages
│   │   ├── hooks/              # Custom React hooks
│   │   ├── lib/                # API client, stores
│   │   └── __tests__/          # Jest tests
│   └── Dockerfile
│
├── 📁 python-ml-service/        # FastAPI Backend
│   ├── src/
│   │   ├── api/                # REST endpoints + middleware
│   │   ├── core/               # Training loop, coordinator, aggregator
│   │   ├── models/             # Pydantic models
│   │   └── utils/              # Utilities
│   ├── tests/                  # Pytest tests
│   └── Dockerfile
│
├── 📁 smart-contracts/          # Solidity Contracts
│   ├── contracts/              # TrainingRegistry, ContributionTracker, RewardDistributor
│   ├── test/                   # Hardhat tests (98 tests)
│   └── Dockerfile
│
├── 📁 monitoring/               # Prometheus + Grafana
├── 📁 scripts/                  # Database init, utilities
├── 📄 docker-compose.yml        # Full stack orchestration
├── 📄 Makefile                  # Build automation
└── 📄 .github/workflows/        # CI/CD pipeline
```

---

## ⚡ Quick Start

### Prerequisites

- **Docker & Docker Compose** (recommended)
- Or: Python 3.11+, Node.js 18+, npm 9+

### Option 1: Docker (Recommended)

```bash
# Clone and start
git clone <your-repo-url>
cd hypergpu

# Start all services
docker compose up -d

# View logs
docker compose logs -f
```

### Option 2: Manual Setup

```bash
# Install dependencies
make install

# Start development
make dev
```

**Access:**
- 🌐 Dashboard: http://localhost:3000
- 📡 API Docs: http://localhost:8000/docs
- 📊 Grafana: http://localhost:3001 (admin/admin)
- 📈 Prometheus: http://localhost:9090

---

## 🧪 Testing

### Run All Tests

```bash
make test
```

### Smart Contract Tests (98 tests)

```bash
make test-contracts

# With gas report
make gas-report
```

### Backend Tests

```bash
make test-backend
```

### Frontend Tests

```bash
make test-frontend
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/status` | Training status |
| POST | `/api/training/start` | Start training |
| POST | `/api/training/stop` | Stop training |
| GET | `/api/training/metrics` | Get metrics |
| GET | `/api/nodes` | List all nodes |
| POST | `/api/nodes/register` | Register node |
| WS | `/ws` | WebSocket connection |

**Full API documentation:** http://localhost:8000/docs

---

## ⛓️ Smart Contracts

### Deployed Contracts (Monad Testnet)

| Contract | Address | Purpose |
|----------|---------|---------|
| TrainingRegistry | `0x6f804...` | Session management |
| ContributionTracker | `0xddeD2...` | Contribution tracking |
| RewardDistributor | `0xe7FE8...` | Reward distribution |

### Gas Optimization

- Packed structs (uint96, uint32) for storage efficiency
- Batch operations for reduced transaction costs
- Pull payment pattern for secure withdrawals

### Deploy to Testnet

```bash
# Set environment variables
export PRIVATE_KEY=your_private_key
export MONAD_TESTNET_RPC=https://testnet-rpc.monad.xyz

# Deploy
make deploy-testnet
```

---

## 🔧 Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Key settings:
- `DATABASE_URL`: PostgreSQL connection
- `REDIS_URL`: Redis connection
- `PRIVATE_KEY`: Blockchain wallet key
- `JWT_SECRET`: API authentication secret

---

## 📊 Monitoring

The stack includes:
- **Prometheus**: Metrics collection
- **Grafana**: Visualization dashboards
- **Structured Logging**: JSON logs for analysis

Access Grafana at http://localhost:3001 with default credentials (admin/admin).

---

## 🚀 Deployment

### Production Build

```bash
# Build all containers
docker compose -f docker-compose.yml build

# Start in production mode
NODE_ENV=production docker compose up -d
```

### Environment Variables

See `.env.example` for all configuration options.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`make test`)
4. Commit changes (`git commit -m 'feat: add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- Built for **LNM Hacks 2025**
- Blockchain: **Monad Testnet**
- Framework: **FastAPI** + **Next.js** + **Hardhat**

---

## ✅ Project Status

| Component | Status | Tests |
|-----------|--------|-------|
| Smart Contracts | ✅ Production Ready | 98 passing |
| Backend API | ✅ Production Ready | Comprehensive |
| Frontend | ✅ Production Ready | Jest configured |
| Docker | ✅ Complete | Multi-stage builds |
| CI/CD | ✅ Configured | GitHub Actions |
| Monitoring | ✅ Complete | Prometheus + Grafana |

**Last Updated:** December 27, 2025
