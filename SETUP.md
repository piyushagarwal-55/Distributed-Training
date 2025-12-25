# 🚀 Quick Setup Guide for Teammates

## Prerequisites Check

Before starting, ensure you have:

```bash
# Check Python version (need 3.13+)
python --version

# Check Node version (need 18+)
node --version

# Check npm
npm --version

# Check git
git --version
```

If any command fails, install the missing tool first.

---

## 🎯 5-Minute Setup

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd lnmhacks1
```

### 2. Install Everything

```bash
npm install
```

This single command will:
- ✅ Create Python virtual environment
- ✅ Install all Python packages
- ✅ Install frontend dependencies  
- ✅ Install smart contract dependencies

**Wait 2-3 minutes for installation to complete.**

### 3. Start the Project

```bash
npm start
```

This starts all services:
- 🟢 Backend API: http://localhost:8000
- 🟢 Frontend: http://localhost:3000
- 🟢 Blockchain: http://localhost:8546

### 4. Open Dashboard

Open your browser: **http://localhost:3000**

You should see the HyperGPU dashboard! 🎉

---

## ✅ Verify Setup

### Check Backend

Open: http://localhost:8000/docs

You should see FastAPI interactive documentation.

### Check Frontend

Open: http://localhost:3000

You should see:
- Dashboard with 0 nodes (initially empty)
- Navigation: Dashboard, Nodes, Training, Blockchain, Settings

### Register Test Node

Run this in a new terminal:

```bash
# PowerShell
$body = @{
    node_id = "test-node-1"
    capabilities = @{
        address = "192.168.1.100:8000"
        gpu_specs = @{
            model = "RTX 4090"
            memory_gb = 24
        }
        compute_power = 1500.0
    }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "http://localhost:8000/api/nodes/register" -Method Post -Body $body -ContentType "application/json"
```

```bash
# Linux/macOS
curl -X POST http://localhost:8000/api/nodes/register \
  -H "Content-Type: application/json" \
  -d '{
    "node_id": "test-node-1",
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

Refresh dashboard → You should see 1 node! ✅

---

## 📁 Project Structure Overview

```
lnmhacks1/
│
├── 📦 package.json              # Root package (npm start here)
│
├── 📁 frontend/                 # Next.js Dashboard
│   ├── src/
│   │   ├── pages/              # Dashboard pages
│   │   ├── components/         # React components
│   │   ├── lib/                # API + WebSocket + Stores
│   │   └── utils/              # Helpers
│   └── package.json
│
├── 📁 python-ml-service/       # FastAPI Backend
│   ├── src/
│   │   ├── api/                # REST endpoints
│   │   ├── core/               # Training logic
│   │   └── models/             # Data models
│   ├── configs/                # Config files
│   └── requirements.txt
│
└── 📁 smart-contracts/         # Blockchain
    ├── contracts/              # Solidity
    └── scripts/                # Deploy scripts
```

---

## 🎮 Common Commands

### Start/Stop

```bash
npm start                # Start all services
npm run dev:backend      # Backend only
npm run dev:frontend     # Frontend only
npm run dev:blockchain   # Blockchain only
```

**Stop:** Press `Ctrl+C` in the terminal

### API Testing

```bash
# Health check
curl http://localhost:8000/health

# List nodes
curl http://localhost:8000/api/nodes

# Training status
curl http://localhost:8000/api/status
```

### Development

```bash
# Frontend hot reload
cd frontend
npm run dev

# Backend hot reload
cd python-ml-service
python -m uvicorn src.api.rest_server:app --reload
```

---

## 🐛 Troubleshooting

### "Port already in use"

**Windows:**
```powershell
# Find process on port 8000
netstat -ano | findstr :8000

# Kill process
taskkill /PID <PID> /F
```

**Linux/macOS:**
```bash
lsof -ti:8000 | xargs kill -9
```

### "Python not found"

Install Python 3.13+ from: https://www.python.org/downloads/

Make sure to check "Add Python to PATH" during installation.

### "npm install fails"

```bash
# Clear cache
npm cache clean --force

# Delete node_modules
rm -rf node_modules package-lock.json

# Reinstall
npm install
```

### "Backend won't start"

```bash
cd python-ml-service

# Recreate virtual environment
rm -rf venv
python -m venv venv

# Activate
venv\Scripts\activate     # Windows
source venv/bin/activate  # Linux/macOS

# Reinstall packages
pip install -r requirements.txt
```

### "Frontend shows errors"

1. Clear browser cache: `Ctrl+Shift+R`
2. Restart frontend: `npm run dev:frontend`
3. Check console (F12) for specific errors

### "No nodes showing"

Backend might not be running:
1. Check: http://localhost:8000/health
2. Register a test node (see above)
3. Check browser console for errors

---

## 📝 Development Workflow

### 1. Create Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Edit files in:
- `frontend/src/` for UI changes
- `python-ml-service/src/` for backend changes
- `smart-contracts/contracts/` for blockchain changes

### 3. Test

```bash
npm start
# Test manually in browser
```

### 4. Commit

```bash
git add .
git commit -m "feat: describe your changes"
```

### 5. Push

```bash
git push origin feature/your-feature-name
```

### 6. Create Pull Request

On GitHub, create PR from your branch to main.

---

## 🔑 Important Files

### Configuration

- `python-ml-service/configs/default.json` - Backend config
- `smart-contracts/hardhat.config.js` - Blockchain config  
- `frontend/next.config.js` - Frontend config

### API Integration

- `frontend/src/lib/api.ts` - API client
- `frontend/src/lib/store.ts` - State management
- `frontend/src/lib/websocket.ts` - Real-time updates

### Backend Endpoints

- `python-ml-service/src/api/rest_server.py` - All API routes

---

## 📚 Learning Resources

### Documentation

- Main README: `README.md`
- API Docs: http://localhost:8000/docs (when running)
- Project Status: `HYDRATION_FIXED.md`, `FRONTEND_CONNECTED.md`

### Technologies

- **Backend:** FastAPI (https://fastapi.tiangolo.com/)
- **Frontend:** Next.js (https://nextjs.org/)
- **Blockchain:** Hardhat (https://hardhat.org/)
- **State:** Zustand (https://zustand-demo.pmnd.rs/)

---

## ✅ Success Checklist

After setup, you should be able to:

- [ ] Access backend API: http://localhost:8000/docs
- [ ] Access frontend: http://localhost:3000
- [ ] See "0 / 0" nodes on dashboard
- [ ] Register a test node via API
- [ ] See registered node on dashboard
- [ ] Navigate all pages (Dashboard, Nodes, Training, Blockchain, Settings)
- [ ] See "Connected" blockchain status (green)
- [ ] Open browser console → no errors

If all checked, you're ready! 🎉

---

## 🆘 Need Help?

1. **Check existing issues:** GitHub Issues
2. **Read docs:** `/docs` folder
3. **API questions:** http://localhost:8000/docs
4. **Ask teammates:** Team chat

---

**Last Updated:** December 25, 2025
