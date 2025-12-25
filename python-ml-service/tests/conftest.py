"""
Shared pytest fixtures for Phase 7 tests.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from src.models.config import SystemConfig, TrainingConfig, NetworkConfig, BlockchainConfig
from src.models.node import NodeStatus


@pytest.fixture
def test_config() -> SystemConfig:
    """Create test configuration."""
    return SystemConfig(
        training=TrainingConfig(
            model_architecture="simple_cnn",
            dataset="mnist",
            dataset_path=None,
            learning_rate=0.001,
            batch_size=32,
            epochs=5,
            optimizer="adam",
            num_nodes=5,
            aggregation_strategy="simple_average",
            synchronous=True,
            timeout_seconds=30.0,
            device="cpu",  # Use CPU for testing
            save_checkpoints=True,
            checkpoint_interval=1,
            checkpoint_dir="./checkpoints"
        ),
        network=NetworkConfig(
            enable_simulation=True,
            base_latency_ms=50.0,
            latency_variance_ms=20.0,
            packet_loss_rate=0.1
        ),
        blockchain=BlockchainConfig(
            enabled=False,  # Disable blockchain for tests
            rpc_endpoint="http://127.0.0.1:8545",
            chain_id=1337
        ),
        log_level="INFO",
        log_file="logs/test_training.log"
    )


@pytest.fixture
def performance_config() -> SystemConfig:
    """Create performance test configuration."""
    return SystemConfig(
        training=TrainingConfig(
            model_architecture="simple_cnn",
            dataset="mnist",
            dataset_path=None,
            learning_rate=0.001,
            batch_size=64,
            epochs=5,
            optimizer="adam",
            num_nodes=5,
            aggregation_strategy="simple_average",
            synchronous=True,
            timeout_seconds=30.0,
            device="cpu",  # Use CPU for testing
            save_checkpoints=True,
            checkpoint_interval=1,
            checkpoint_dir="./checkpoints"
        ),
        network=NetworkConfig(
            enable_simulation=True,
            base_latency_ms=50.0,
            latency_variance_ms=20.0,
            packet_loss_rate=0.01
        ),
        blockchain=BlockchainConfig(
            enabled=False,  # Disable blockchain for tests
            rpc_endpoint="http://127.0.0.1:8545",
            chain_id=1337
        ),
        log_level="INFO",
        log_file="logs/test_training.log"
    )
