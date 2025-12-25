# 🚀 HOW TO USE THE DISTRIBUTED TRAINING SYSTEM

## 📋 Table of Contents
1. [Quick Start](#quick-start)
2. [Understanding the System](#understanding-the-system)
3. [Step-by-Step Training Guide](#step-by-step-training-guide)
4. [Using the Dashboard](#using-the-dashboard)
5. [Real vs Mock Data](#real-vs-mock-data)
6. [Common Tasks](#common-tasks)

---

## 🎯 Quick Start (3 Steps)

### Step 1: Start the System
```bash
npm start
```
This starts:
- **Backend API** (port 8000) - Real Python server
- **Frontend Dashboard** (port 3000) - React interface
- **Blockchain Node** (port 8546) - Local Ethereum node

### Step 2: Open Dashboard
Open browser: **http://localhost:3000**

### Step 3: Start Training
1. Click **"Settings"** in sidebar
2. Configure training parameters
3. Click **"Start Training"** button

---

## 🧠 Understanding the System

### What Is This Project?

This is a **Distributed Federated Learning System** where:
- Multiple computers (nodes) train AI models together
- Each node keeps its data private (federated learning)
- Blockchain records contributions and rewards
- Real-time dashboard monitors everything

### The Three Parts:

```
┌─────────────────────────────────────────────────────────┐
│  1. BACKEND (Python)                                    │
│     - Coordinates training across nodes                 │
│     - Aggregates model gradients                        │
│     - Manages blockchain integration                    │
│     Port: 8000                                          │
└─────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────┐
│  2. FRONTEND (Next.js)                                  │
│     - Beautiful dashboard UI                            │
│     - Real-time metrics visualization                   │
│     - Node management interface                         │
│     Port: 3000                                          │
└─────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────┐
│  3. BLOCKCHAIN (Hardhat)                                │
│     - Records training contributions                    │
│     - Manages reward distribution                       │
│     - Immutable audit trail                            │
│     Port: 8546                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 📚 Step-by-Step Training Guide

### OPTION A: Quick Demo (No Setup)

**1. Start System**
```bash
npm start
```

**2. Test Backend API**
Open: http://localhost:8000/docs

**3. Try API Endpoints**
- Click on `POST /api/training/start`
- Click "Try it out"
- Use this config:
```json
{
  "model_name": "simple_cnn",
  "dataset": "mnist",
  "epochs": 5,
  "batch_size": 32,
  "learning_rate": 0.001
}
```
- Click "Execute"
- Watch training start!

**4. Check Status**
- Try `GET /api/status` to see training progress
- Try `GET /api/training/metrics` to see loss/accuracy

---

### OPTION B: Full System with Real Nodes

**1. Register Training Nodes**

Open http://localhost:8000/docs and use `POST /api/nodes/register`:

```json
{
  "node_id": "my-node-1",
  "address": "192.168.1.100:8000",
  "gpu_specs": {
    "model": "RTX 4090",
    "memory_gb": 24,
    "compute_capability": "8.9"
  },
  "status": "idle"
}
```

Register 3-5 nodes for better results.

**2. Configure Training**

Use `POST /api/training/start` with your settings:

```json
{
  "model_name": "simple_cnn",
  "dataset": "mnist",
  "epochs": 10,
  "batch_size": 64,
  "learning_rate": 0.001
}
```

**3. Monitor Training**

Use these endpoints:
- `GET /api/status` - Overall status
- `GET /api/training/metrics` - Loss, accuracy per epoch
- `GET /api/nodes` - Node health and performance

**4. Stop When Done**

Use `POST /api/training/stop` when finished.

---

## 🎨 Using the Dashboard

### Current Status: MOCK DATA

Your frontend currently shows **fake/demo data**:
- ❌ Nodes are hardcoded (node_1, node_2, node_3)
- ❌ Blockchain data is fake
- ❌ Not connected to real backend

### Dashboard Pages:

#### 1. **Dashboard (Home)**
- Overview of system status
- Quick action buttons
- Recent training sessions
- Node status summary

#### 2. **Training Page**
- Start/stop/pause training
- Real-time metrics (loss, accuracy)
- Progress visualization
- Training configuration

#### 3. **Nodes Page**
- View all registered nodes
- Add/remove nodes
- Monitor node health
- Check network latency

#### 4. **Blockchain Page**
- View contributions recorded on-chain
- Check reward balances
- Claim pending rewards
- Transaction history

#### 5. **Settings Page**
- Configure training parameters
- Set network simulation
- Blockchain settings
- Save/load presets

---

## 🔄 Real vs Mock Data

### What's Currently Mock?

**Frontend Mock Data (in `frontend/src/lib/store.ts`):**

```typescript
// MOCK NODES - Not Real!
nodes: [
  {
    id: 'node_1',
    status: 'online',
    health: 'healthy',
    latency: 45,
    // ... fake data
  }
]

// MOCK BLOCKCHAIN - Not Real!
contributions: [
  {
    nodeId: 'node_1',
    computeTime: 120,
    // ... fake data
  }
]
```

### How to Use REAL Data:

The backend API has real endpoints, but the frontend isn't calling them yet.

**To connect frontend to backend, you need to:**

1. **Replace mock data with API calls**
2. **Use the WebSocket for real-time updates**
3. **Fetch actual training metrics**

I can help you do this - would you like me to update the frontend to use real data?

---

## 🎯 Common Tasks

### Task 1: Start a Training Session

**Via API (http://localhost:8000/docs):**
1. Open API docs
2. Find `POST /api/training/start`
3. Click "Try it out"
4. Enter config (see examples above)
5. Click "Execute"

**Via Dashboard (when connected):**
1. Go to Settings page
2. Configure parameters
3. Click "Start Training"

---

### Task 2: Monitor Progress

**Via API:**
```bash
# Check status
curl http://localhost:8000/api/status

# Get metrics
curl http://localhost:8000/api/training/metrics

# List nodes
curl http://localhost:8000/api/nodes
```

**Via Dashboard:**
- Training page shows real-time charts
- Metrics update automatically via WebSocket

---

### Task 3: Register New Nodes

**Via API:**
```bash
curl -X POST http://localhost:8000/api/nodes/register \
  -H "Content-Type: application/json" \
  -d '{
    "node_id": "my-gpu-node",
    "address": "192.168.1.50:8000",
    "gpu_specs": {
      "model": "RTX 3090",
      "memory_gb": 24
    }
  }'
```

**Via Dashboard:**
1. Go to Nodes page
2. Click "+ Add Node"
3. Fill in node details
4. Click "Add"

---

### Task 4: Check Blockchain Contributions

**Via API:**
```bash
# Get all contributions (when blockchain enabled)
curl http://localhost:8000/api/blockchain/contributions

# Get rewards for a node
curl http://localhost:8000/api/blockchain/rewards/node_1
```

**Via Dashboard:**
1. Go to Blockchain page
2. View "Recorded Contributions" table
3. Check "Rewards Tracker" for earnings

---

## 🚨 Current Limitations

### Why Dashboard Shows Mock Data?

The frontend was built with mock data for demonstration. To make it work with real backend:

**Option 1: Use API Directly**
- Go to http://localhost:8000/docs
- Use the interactive API (fully functional)
- Real training, real nodes, real metrics

**Option 2: Connect Frontend (Requires Code Changes)**
I can update the frontend to:
- ✅ Fetch real nodes from backend
- ✅ Show actual training metrics
- ✅ Use WebSocket for live updates
- ✅ Connect to real blockchain data

Would you like me to do this?

---

## 📊 Understanding the Training Flow

### What Happens When You Start Training:

```
1. USER: Clicks "Start Training"
          ↓
2. BACKEND: Initializes training session
          ↓
3. COORDINATOR: Selects available nodes
          ↓
4. NODES: Start local training on their data
          ↓
5. NODES: Send gradients to coordinator
          ↓
6. AGGREGATOR: Combines gradients (federated averaging)
          ↓
7. COORDINATOR: Updates global model
          ↓
8. REPEAT: For each epoch
          ↓
9. BLOCKCHAIN: Records contributions (if enabled)
          ↓
10. REWARDS: Calculate and distribute tokens
```

### Training Parameters Explained:

- **model_name**: AI model architecture (e.g., "simple_cnn")
- **dataset**: Training data (e.g., "mnist" - handwritten digits)
- **epochs**: How many times to train on full dataset
- **batch_size**: Samples processed at once (32, 64, 128)
- **learning_rate**: How fast model learns (0.001 is good start)
- **num_nodes**: How many computers participate

---

## 🎓 Example Scenarios

### Scenario 1: Quick Test Run

**Goal:** Test if system works

```bash
# 1. Start system
npm start

# 2. Open API docs
# http://localhost:8000/docs

# 3. Start simple training
POST /api/training/start
{
  "model_name": "simple_cnn",
  "dataset": "mnist",
  "epochs": 2,
  "batch_size": 32,
  "learning_rate": 0.001
}

# 4. Check status
GET /api/status

# 5. Stop
POST /api/training/stop
```

---

### Scenario 2: Full Production Run

**Goal:** Real distributed training with blockchain

```bash
# 1. Start system
npm start

# 2. Register multiple nodes
POST /api/nodes/register (repeat 3-5 times)

# 3. Start serious training
POST /api/training/start
{
  "epochs": 50,
  "batch_size": 64,
  "learning_rate": 0.001
}

# 4. Monitor via dashboard
# Open http://localhost:3000

# 5. Check blockchain contributions
GET /api/blockchain/contributions

# 6. Claim rewards
POST /api/blockchain/claim/{node_id}
```

---

## 🔧 Troubleshooting

### Dashboard Shows "Offline"
**Problem:** WebSocket not connected
**Solution:** 
1. Check backend running: http://localhost:8000/health
2. Refresh browser
3. Check console for errors (F12)

### No Nodes Appear
**Problem:** Frontend using mock data
**Solution:** 
- Use API directly: http://localhost:8000/docs
- Or let me update frontend to use real data

### Training Not Starting
**Problem:** No nodes registered or backend error
**Solution:**
1. Register at least 1 node via API
2. Check backend logs in terminal
3. Check API response for error message

---

## 🎯 Next Steps

### To Actually Use This System:

**EASY WAY (Recommended):**
1. Use the backend API directly at http://localhost:8000/docs
2. All features work here (training, nodes, blockchain)
3. Interactive, fully functional

**ADVANCED WAY:**
Let me update the frontend to connect to real backend:
- Replace mock data with API calls
- Enable real-time WebSocket updates
- Show actual training metrics
- Connect to blockchain data

**Which do you prefer?**

---

## 📞 Quick Reference

### Important URLs:
- **Dashboard**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **API Health**: http://localhost:8000/health
- **Backend Status**: http://localhost:8000/api/status
- **Blockchain RPC**: http://localhost:8546

### Quick Commands:
```bash
# Start everything
npm start

# Stop everything
npm run stop

# Check health
npm run health

# Run tests
npm run test:all

# Backend only
npm run dev:backend

# Frontend only
npm run dev:frontend

# Blockchain only
npm run dev:blockchain
```

---

## 💡 Summary

**What You Have:**
✅ Fully functional backend API
✅ Beautiful frontend dashboard
✅ Blockchain integration (local + Monad testnet)
✅ All components running

**Current Limitation:**
❌ Frontend shows mock data (not connected to backend yet)

**How to Use Right Now:**
1. Use API directly: http://localhost:8000/docs
2. Start training via API
3. Monitor via API endpoints
4. Everything works!

**Want Real Dashboard?**
Tell me and I'll connect the frontend to the backend! 🚀
