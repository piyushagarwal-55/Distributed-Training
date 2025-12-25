# Python ML Service

The Python ML Service is the core training coordinator for HyperGPU. It handles distributed training orchestration, gradient aggregation, and adaptive network optimization.

## Features

- 🧠 **Training Coordination**: Manages distributed training across multiple GPU nodes
- 📊 **Data Sharding**: Intelligently distributes datasets across nodes
- 🔄 **Gradient Aggregation**: Implements All-Reduce and weighted averaging
- 🌐 **Network Adaptation**: Monitors and adapts to network conditions
- 📈 **Metrics Tracking**: Comprehensive performance and network metrics

## Setup

### 1. Create Virtual Environment

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**On Linux/WSL:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
- API endpoints
- Blockchain RPC URLs
- Logging levels

### 4. Run Tests

```bash
pytest tests/
```

## Project Structure

```
python-ml-service/
├── src/
│   ├── models/          # Data models and schemas
│   ├── core/            # Core training logic
│   ├── utils/           # Utility functions
│   └── main.py          # Entry point
├── configs/             # Configuration files
├── tests/               # Test suite
└── requirements.txt     # Dependencies
```

## Usage

### Basic Training Run

```python
from src.core.coordinator import TrainingCoordinator
from src.models.config import TrainingConfig

# Load configuration
config = TrainingConfig.from_file("configs/default.json")

# Initialize coordinator
coordinator = TrainingCoordinator(config)

# Start training
coordinator.start_training()
```

### Command Line

```bash
python -m src.main --config configs/default.json
```

## Configuration

See `configs/default.json` for available options:

- **Model Settings**: Architecture, learning rate, batch size
- **Dataset**: Which dataset to use (MNIST, CIFAR-10)
- **Nodes**: Number of nodes, resource allocation
- **Network**: Simulation parameters
- **Blockchain**: Contract addresses, RPC endpoints

## Development

### Code Style

We use `black` for formatting and `flake8` for linting:

```bash
black src/ tests/
flake8 src/ tests/
```

### Type Checking

```bash
mypy src/
```

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src tests/

# Specific test file
pytest tests/test_models.py

# Verbose mode
pytest -v
```

## Components

### Core Modules

- **coordinator.py**: Main training orchestration
- **data_sharding.py**: Dataset distribution logic
- **gradient_aggregator.py**: Gradient combination strategies
- **model_manager.py**: Model parameter management
- **network_monitor.py**: Network quality tracking
- **adaptive_controller.py**: Adaptive batch sizing and node selection

### Data Models

- **TrainingConfig**: Training configuration schema
- **NodeMetadata**: GPU node information
- **NetworkMetrics**: Network performance data
- **GradientUpdate**: Gradient transmission format
- **TrainingMetrics**: Loss, accuracy, and performance metrics

## Troubleshooting

### Import Errors

Ensure you're in the virtual environment:
```bash
which python  # Should point to venv/bin/python
```

### CUDA Not Available

For CPU-only testing:
```python
config.device = "cpu"
```

### gRPC Connection Issues

Check firewall settings and ensure ports are open.

## API Documentation

See [API.md](./docs/API.md) for detailed API documentation.

## License

MIT License
