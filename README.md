# HyperGPU: Network-Aware Distributed AI Training

> **🎯 Production-Ready Distributed Federated Learning Platform**
> 
> Intelligently adapts to real-world network conditions with blockchain-based incentive mechanisms.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Node 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Setup for Teammates](#setup-for-teammates)
- [Usage Guide](#usage-guide)
- [Development](#development)
- [Troubleshooting](#troubleshooting)

---

## 🌟 Overview

HyperGPU is a revolutionary distributed AI training platform that intelligently adapts to real-world network conditions across distributed GPU nodes. By combining network-aware optimization with blockchain-based incentive mechanisms, we create a system that matches or exceeds centralized training performance.

## 🚀 Key Features

- 🌐 **Network-Aware Optimization**: Dynamically adapts to latency, packet loss, and bandwidth constraints
- ⛓️ **Blockchain Integration**: Transparent contribution tracking and rewards via Monad testnet
- 🎯 **Adaptive Training**: Smart batch sizing, gradient routing, and node selection
- 📊 **Real-Time Dashboard**: Comprehensive visualization of training, nodes, and blockchain activity
- 🔄 **Auto-Reconnect WebSocket**: Live updates every 10 seconds
- 🎨 **Modern UI**: Next.js 14 + Tailwind CSS responsive design

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
lnmhacks1/
├── 📁 frontend/                      # Next.js Dashboard (Port 3000)
│   ├── src/
│   │   ├── components/              # React components (atoms/molecules/organisms)
│   │   ├── pages/                   # Next.js pages
│   │   ├── lib/                     # API client, WebSocket, Zustand stores
│   │   └── utils/                   # Date formatting, helpers
│   └── package.json
│
├── 📁 python-ml-service/            # FastAPI Backend (Port 8000)
│   ├── src/
│   │   ├── api/                     # REST API endpoints
│   │   ├── core/                    # Training coordinator, node manager
│   │   ├── models/                  # Pydantic models
│   │   └── utils/                   # Utilities
│   ├── configs/                     # Configuration files
│   └── requirements.txt
│
├── 📁 smart-contracts/              # Hardhat (Port 8546)
│   ├── contracts/                   # Solidity contracts
│   ├── scripts/                     # Deploy scripts
│   └── hardhat.config.js
│
├── 📁 docs/                         # Documentation
├── 📄 package.json                  # Root package (npm start)
└── 📄 README.md                     # This file
```

---

## ⚡ Quick Start (5 Minutes)

### Prerequisites

**Required:**
- ✅ **Python 3.13+** ([Download](https://www.python.org/downloads/))
- ✅ **Node.js 18+** ([Download](https://nodejs.org/))
- ✅ **Git** ([Download](https://git-scm.com/))

**Recommended:**
- VS Code with extensions: Python, ESLint, Prettier
- Windows Terminal or PowerShell 7+

### One-Command Setup

```bash
# Clone repository
git clone <your-repo-url>
cd lnmhacks1

# Install everything (takes ~3 minutes)
npm install

# Start all services
npm start
```

**That's it!** 🎉 Open http://localhost:3000

---

## 👥 Setup for Teammates

### Step 1: Clone Repository

```bash
git clone <your-repo-url>
cd lnmhacks1
```

### Step 2: Install Dependencies

**Option A: Automatic (Recommended)**
```bash
npm install
```

**Option B: Manual**
```bash
# Backend dependencies
cd python-ml-service
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
cd ..

# Frontend dependencies
cd frontend
npm install
cd ..

# Smart contracts
cd smart-contracts
npm install
cd ..

# Root dependencies
npm install
```

### Step 3: Configuration (Optional)

**Backend Config:** Edit `python-ml-service/configs/default.json`
```json
{
  "training": {
    "model_architecture": "simple_cnn",
    "dataset": "mnist",
    "epochs": 10,
    "batch_size": 32
  }
}
```

**Frontend:** No config needed (auto-connects to localhost:8000)

**Smart Contracts:** Already configured for Monad testnet

### Step 4: Start Development

```bash
# Start all services (backend + frontend + blockchain)
npm start
```

**Individual services:**
```bash
npm run dev:backend       # Backend only (port 8000)
npm run dev:frontend      # Frontend only (port 3000)
npm run dev:blockchain    # Blockchain only (port 8546)
```

### Step 5: Verify Setup

1. **Backend:** http://localhost:8000/docs
2. **Frontend:** http://localhost:3000
3. **Health Check:**
   ```bash
   curl http://localhost:8000/health
   ```

---

## 🎮 Usage Guide

### Register GPU Nodes

**Via API:**
```bash
curl -X POST http://localhost:8000/api/nodes/register \
  -H "Content-Type: application/json" \
  -d '{
    "node_id": "gpu-node-1",
    "capabilities": {
      "address": "192.168.1.100:8000",
      "gpu_specs": {
        "model": "RTX 4090",
        "memory_gb": 24
      },
      "compute_power": 1500.0
    }
  }'
```

**Via Dashboard:**
1. Go to Nodes page
2. Click "Add Node"
3. Fill in details

### Start Training

**Via API:**
```bash
curl -X POST http://localhost:8000/api/training/start \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "simple_cnn",
    "dataset": "mnist",
    "epochs": 10,
    "batch_size": 32,
    "learning_rate": 0.001
  }'
```

**Via Dashboard:**
1. Go to Settings page
2. Configure training parameters
3. Click "Start Training"

### Monitor Training

- **Dashboard:** Real-time metrics at http://localhost:3000
- **API:** GET http://localhost:8000/api/training/metrics
- **WebSocket:** Auto-connects and updates every 10 seconds

### View Nodes

```bash
# List all nodes
curl http://localhost:8000/api/nodes

# Get specific node
curl http://localhost:8000/api/nodes/gpu-node-1
```

---

## 🛠️ Development

### Project Scripts

```bash
npm start              # Start all services
npm run dev:backend    # Backend development
npm run dev:frontend   # Frontend development  
npm run dev:blockchain # Blockchain node
npm test               # Run all tests
npm run build          # Build for production
```

### Adding Features

1. **Backend API:**
   - Add endpoint: `python-ml-service/src/api/rest_server.py`
   - Add model: `python-ml-service/src/models/`
   - Update docs: FastAPI auto-generates at `/docs`

2. **Frontend:**
   - Add component: `frontend/src/components/`
   - Add page: `frontend/src/pages/`
   - Update store: `frontend/src/lib/store.ts`
   - Update API client: `frontend/src/lib/api.ts`

3. **Smart Contracts:**
   - Add contract: `smart-contracts/contracts/`
   - Deploy: `npx hardhat run scripts/deploy.js --network monad_testnet`

### Code Style

- **Python:** Black, isort, flake8
- **TypeScript:** Prettier, ESLint
- **Commits:** Conventional commits (feat:, fix:, docs:)

---

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux
lsof -ti:8000 | xargs kill -9
```

### Python Virtual Environment Issues

```bash
# Recreate venv
cd python-ml-service
rm -rf venv
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Node Modules Issues

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Backend Not Starting

```bash
# Check Python version (need 3.13+)
python --version

# Check dependencies
cd python-ml-service
pip list

# Run directly
python -m uvicorn src.api.rest_server:app --reload --port 8000
```

### Frontend Hydration Errors

- Fixed! All hydration errors resolved
- Clear browser cache: Ctrl+Shift+R
- Restart Next.js: `npm run dev:frontend`

### WebSocket Connection Failed

- Check backend is running: http://localhost:8000/health
- Check CORS settings in `rest_server.py`
- Browser console should show: `[WebSocketClient] Connected successfully`

### No Nodes Showing

```bash
# Register a test node
curl -X POST http://localhost:8000/api/nodes/register \
  -H "Content-Type: application/json" \
  -d '{"node_id":"test-1","capabilities":{"address":"localhost:8000","gpu_specs":{"model":"Test GPU","memory_gb":8},"compute_power":100}}'

# Verify
curl http://localhost:8000/api/nodes
```

---

## 📚 API Documentation

**Interactive API Docs:** http://localhost:8000/docs

### Key Endpoints

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

---

## 🌐 Deployment

### Production Build

```bash
# Build frontend
cd frontend
npm run build
npm start

# Backend (production)
cd python-ml-service
gunicorn src.api.rest_server:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Smart contracts (mainnet)
cd smart-contracts
npx hardhat run scripts/deploy.js --network monad
```

### Environment Variables

Create `.env` files:

**Frontend (.env.local):**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

**Backend (.env):**
```env
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
```

---

## 📝 License

MIT License - see [LICENSE](./LICENSE)

---

## 🙏 Acknowledgments

- Built for **LNM Hacks 2025**
- Blockchain: **Monad Testnet**
- Framework: **FastAPI** + **Next.js** + **Hardhat**

---

## 📞 Support

- **Issues:** Open GitHub issue
- **Docs:** Check `/docs` folder
- **API Help:** http://localhost:8000/docs

---

## ✅ Status

**✨ Production Ready** - All features working, all errors fixed!

**Last Updated:** December 25, 2025
