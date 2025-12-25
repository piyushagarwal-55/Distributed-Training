# Quick Start Guide - HyperGPU

## 🚀 Get Started in 5 Minutes

### Prerequisites
- Python 3.9+ installed
- 8GB+ RAM recommended
- 5GB free disk space

### Installation (Windows)

1. **Navigate to the project**
   ```powershell
   cd c:\Users\LENOVO\Desktop\lnmhacks1\python-ml-service
   ```

2. **Activate the virtual environment**
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

3. **Verify installation**
   ```powershell
   python -m src.main --validate-only
   ```

### Installation (Linux/WSL)

1. **Navigate to the project**
   ```bash
   cd ~/lnmhacks1/python-ml-service
   ```

2. **Activate the virtual environment**
   ```bash
   source venv/bin/activate
   ```

3. **Verify installation**
   ```bash
   python -m src.main --validate-only
   ```

---

## 📝 Running Your First Training

### Step 1: Check Configuration
```bash
python -m src.main --config configs/default.json --validate-only --log-level INFO
```

### Step 2: Run Tests
```bash
pytest -v
```

### Step 3: Check Test Coverage
```bash
pytest --cov=src tests/
```

---

## 🛠️ Common Commands

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_models.py

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=src --cov-report=html tests/
```

### Development
```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type check
mypy src/
```

### Configuration
```bash
# Validate config
python -m src.main --validate-only

# Custom config
python -m src.main --config configs/custom.json

# Debug mode
python -m src.main --log-level DEBUG
```

---

## 📂 Project Structure Quick Reference

```
python-ml-service/
├── src/
│   ├── models/          # Data models
│   │   ├── config.py    # Configuration
│   │   ├── node.py      # Node metadata
│   │   ├── metrics.py   # Training metrics
│   │   └── blockchain.py # Blockchain
│   │
│   └── utils/           # Utilities
│       ├── logger.py    # Logging
│       ├── serialization.py # Tensors
│       └── validation.py # Validation
│
├── configs/             # Configuration files
├── tests/               # Test suite
└── venv/                # Virtual environment
```

---

## 🔍 Troubleshooting

### Virtual Environment Issues
```powershell
# Windows: Enable script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Recreate venv if needed
rm -r venv
python -m venv venv
```

### Import Errors
```bash
# Ensure you're in python-ml-service directory
cd python-ml-service

# Activate venv
source venv/bin/activate  # Linux
.\venv\Scripts\activate   # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Test Failures
```bash
# Run specific failing test
pytest tests/test_models.py::TestTrainingConfig -v

# Clear pytest cache
pytest --cache-clear
```

---

## 📚 Next Steps

1. ✅ **Phase 1 Complete** - Foundation is ready
2. 🔜 **Phase 2** - Implement Training Coordinator
3. 🔜 **Phase 3** - Build GPU Node Simulator
4. 🔜 **Phase 4** - Add Network Adaptation

See [roadmap.md](../docs/roadmap.md) for detailed plan.

---

## 🆘 Getting Help

- **Documentation**: See `/docs` folder
- **Issues**: Check test output for errors
- **Configuration**: Review `configs/default.json`

---

## ✨ What's Working

- ✅ Data models with validation
- ✅ Configuration system
- ✅ Testing infrastructure
- ✅ Logging and utilities
- ✅ Serialization tools

## 🔨 What's Next (Phase 2)

- Training Coordinator
- Data Sharding
- Model Parameter Management
- Gradient Aggregation

---

*Last Updated: December 23, 2025*
