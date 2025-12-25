"""
Comprehensive tests for Phase 2: Training Coordinator Core.

Tests all components:
- TrainingCoordinator
- DataShardManager
- ModelManager
- GradientAggregator
"""

import pytest
import numpy as np
import torch
from pathlib import Path
import tempfile
import shutil
from datetime import datetime

from src.core.coordinator import TrainingCoordinator
from src.core.data_shard import DataShardManager
from src.core.model_manager import ModelManager
from src.core.gradient_aggregator import GradientAggregator
from src.models.config import (
    SystemConfig,
    TrainingConfig,
    NetworkConfig,
    BlockchainConfig,
    DatasetType,
    ModelArchitecture,
    AggregationStrategy,
)
from src.models.node import NodeMetadata, NodeStatus
from src.models.metrics import AggregatedMetrics


# Fixtures
@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def system_config():
    """Create test system configuration."""
    return SystemConfig(
        training=TrainingConfig(
            model_architecture=ModelArchitecture.SIMPLE_CNN,
            dataset=DatasetType.MNIST,
            learning_rate=0.001,
            batch_size=32,
            epochs=2,
            steps_per_epoch=10,
        ),
        network=NetworkConfig(
            base_latency_ms=10.0,
            latency_std_ms=5.0,
            packet_loss_rate=0.01,
        ),
        blockchain=BlockchainConfig(
            rpc_endpoint="http://localhost:8545",
            contract_address="0x" + "0" * 40,
        ),
    )


@pytest.fixture
def sample_nodes():
    """Create sample node metadata."""
    return [
        NodeMetadata(
            node_id=f"node_{i}",
            node_address=f"192.168.1.{i}:5000",
            status=NodeStatus.READY,
            gpu_model="Test-GPU",
            gpu_memory_gb=8.0,
            compute_capability=7.5,
        )
        for i in range(5)
    ]


# TrainingCoordinator Tests
class TestTrainingCoordinator:
    """Tests for TrainingCoordinator class."""
    
    def test_coordinator_initialization(self, system_config):
        """Test coordinator initialization."""
        coordinator = TrainingCoordinator(system_config)
        
        assert coordinator.config == system_config
        assert coordinator.current_epoch == 0
        assert coordinator.current_step == 0
        assert not coordinator.is_training
        assert not coordinator.is_initialized
        assert coordinator.node_registry.get_active_count() == 0
    
    def test_initialize_training(self, system_config):
        """Test training initialization."""
        coordinator = TrainingCoordinator(system_config)
        success = coordinator.initialize_training()
        
        assert success
        assert coordinator.is_initialized
        assert coordinator.total_steps == 20  # 2 epochs * 10 steps
        assert coordinator.current_epoch == 0
        assert coordinator.current_step == 0
    
    def test_register_nodes(self, system_config, sample_nodes):
        """Test node registration."""
        coordinator = TrainingCoordinator(system_config)
        
        for node in sample_nodes:
            success = coordinator.register_node(node)
            assert success
        
        assert coordinator.node_registry.get_active_count() == len(sample_nodes)
        
        # Verify health tracking initialized
        for node in sample_nodes:
            assert node.node_id in coordinator.node_health
            assert node.node_id in coordinator.node_performance
    
    def test_register_duplicate_node(self, system_config, sample_nodes):
        """Test registering duplicate node."""
        coordinator = TrainingCoordinator(system_config)
        node = sample_nodes[0]
        
        # Register once
        success1 = coordinator.register_node(node)
        assert success1
        
        # Register again (should update)
        success2 = coordinator.register_node(node)
        assert success2
        
        # Should still have only one node
        assert coordinator.node_registry.get_active_count() == 1
    
    def test_remove_node(self, system_config, sample_nodes):
        """Test node removal."""
        coordinator = TrainingCoordinator(system_config)
        
        # Register nodes
        for node in sample_nodes:
            coordinator.register_node(node)
        
        initial_count = coordinator.node_registry.get_active_count()
        
        # Remove one node
        success = coordinator.remove_node(sample_nodes[0].node_id)
        assert success
        assert coordinator.node_registry.get_active_count() == initial_count - 1
        
        # Verify cleanup
        assert sample_nodes[0].node_id not in coordinator.node_health
    
    def test_node_heartbeat(self, system_config, sample_nodes):
        """Test node heartbeat tracking."""
        coordinator = TrainingCoordinator(system_config)
        node = sample_nodes[0]
        coordinator.register_node(node)
        
        # Update heartbeat
        success = coordinator.update_node_heartbeat(node.node_id)
        assert success
        
        health = coordinator.node_health[node.node_id]
        assert health["total_heartbeats"] == 1
        assert health["consecutive_failures"] == 0
    
    def test_node_failure_tracking(self, system_config, sample_nodes):
        """Test node failure tracking and auto-removal."""
        coordinator = TrainingCoordinator(system_config)
        node = sample_nodes[0]
        coordinator.register_node(node)
        
        # Record failures
        for i in range(4):
            coordinator.record_node_failure(node.node_id)
            health = coordinator.node_health[node.node_id]
            assert health["consecutive_failures"] == i + 1
        
        # Fifth failure should trigger removal
        coordinator.record_node_failure(node.node_id)
        assert node.node_id not in coordinator.node_health
    
    def test_training_status(self, system_config):
        """Test getting training status."""
        coordinator = TrainingCoordinator(system_config)
        coordinator.initialize_training()
        
        status = coordinator.get_training_status()
        
        assert isinstance(status, dict)
        assert "is_initialized" in status
        assert "is_training" in status
        assert "current_epoch" in status
        assert "current_step" in status
        assert "progress_percentage" in status
        assert status["is_initialized"] is True
    
    def test_advance_step(self, system_config):
        """Test step advancement and epoch tracking."""
        coordinator = TrainingCoordinator(system_config)
        coordinator.initialize_training()
        
        # Advance through one epoch
        for _ in range(10):
            coordinator.advance_step()
        
        assert coordinator.current_step == 10
        assert coordinator.current_epoch == 1
    
    def test_save_load_state(self, system_config, sample_nodes, temp_dir):
        """Test state persistence."""
        coordinator = TrainingCoordinator(system_config)
        coordinator.initialize_training()
        
        # Register nodes and advance
        for node in sample_nodes[:2]:
            coordinator.register_node(node)
        coordinator.advance_step()
        coordinator.advance_step()
        
        # Save state
        success = coordinator.save_state(temp_dir)
        assert success
        
        # Create new coordinator and load state
        new_coordinator = TrainingCoordinator(system_config)
        checkpoint_file = list(Path(temp_dir).glob("*.pkl"))[0]
        success = new_coordinator.load_state(str(checkpoint_file))
        
        assert success
        assert new_coordinator.current_step == 2
        assert new_coordinator.node_registry.get_active_count() == 2


# DataShardManager Tests
class TestDataShardManager:
    """Tests for DataShardManager class."""
    
    def test_shard_manager_initialization(self):
        """Test shard manager initialization."""
        manager = DataShardManager(DatasetType.MNIST)
        
        assert manager.dataset_type == DatasetType.MNIST
        assert manager.train_dataset is None
        assert len(manager.shards) == 0
    
    @pytest.mark.skipif(not torch.cuda.is_available(), reason="Requires CUDA")
    def test_load_mnist_dataset(self, temp_dir):
        """Test loading MNIST dataset."""
        manager = DataShardManager(DatasetType.MNIST, dataset_path=temp_dir)
        success = manager.load_dataset(download=True)
        
        assert success
        assert manager.train_dataset is not None
        assert manager.test_dataset is not None
        assert manager.num_classes == 10
        assert len(manager.train_dataset) > 0
    
    def test_create_shards_balanced(self):
        """Test creating balanced shards."""
        manager = DataShardManager(DatasetType.MNIST)
        
        # Create mock dataset
        class MockDataset:
            def __init__(self, size=1000):
                self.size = size
            def __len__(self):
                return self.size
            def __getitem__(self, idx):
                return torch.randn(1, 28, 28), idx % 10
        
        manager.train_dataset = MockDataset(1000)
        
        # Create 5 shards
        success = manager.create_shards(num_shards=5, stratified=False)
        assert success
        assert len(manager.orphaned_shards) == 5
        
        # Check balance
        sizes = [len(shard) for shard in manager.orphaned_shards]
        assert min(sizes) >= 190  # Roughly 200 each
        assert max(sizes) <= 210
    
    def test_assign_shard(self):
        """Test shard assignment to nodes."""
        manager = DataShardManager(DatasetType.MNIST)
        
        class MockDataset:
            def __len__(self):
                return 1000
            def __getitem__(self, idx):
                return torch.randn(1, 28, 28), 0
        
        manager.train_dataset = MockDataset()
        manager.create_shards(num_shards=3)
        
        # Assign shards
        success1 = manager.assign_shard("node_1")
        assert success1
        assert "node_1" in manager.shards
        assert len(manager.orphaned_shards) == 2
        
        success2 = manager.assign_shard("node_2")
        assert success2
        assert len(manager.orphaned_shards) == 1
    
    def test_release_shard(self):
        """Test releasing shard back to pool."""
        manager = DataShardManager(DatasetType.MNIST)
        
        class MockDataset:
            def __len__(self):
                return 1000
            def __getitem__(self, idx):
                return torch.randn(1, 28, 28), 0
        
        manager.train_dataset = MockDataset()
        manager.create_shards(num_shards=3)
        manager.assign_shard("node_1")
        
        # Release shard
        success = manager.release_shard("node_1")
        assert success
        assert "node_1" not in manager.shards
        assert len(manager.orphaned_shards) == 3
    
    def test_reassign_shard(self):
        """Test reassigning shard between nodes."""
        manager = DataShardManager(DatasetType.MNIST)
        
        class MockDataset:
            def __len__(self):
                return 1000
            def __getitem__(self, idx):
                return torch.randn(1, 28, 28), 0
        
        manager.train_dataset = MockDataset()
        manager.create_shards(num_shards=2)
        manager.assign_shard("node_1")
        
        # Reassign
        success = manager.reassign_shard("node_1", "node_2")
        assert success
        assert "node_1" not in manager.shards
        assert "node_2" in manager.shards
    
    def test_shard_statistics(self):
        """Test shard statistics."""
        manager = DataShardManager(DatasetType.MNIST)
        
        class MockDataset:
            def __len__(self):
                return 1000
            def __getitem__(self, idx):
                return torch.randn(1, 28, 28), 0
        
        manager.train_dataset = MockDataset()
        manager.create_shards(num_shards=5)
        manager.assign_shard("node_1")
        manager.assign_shard("node_2")
        
        stats = manager.get_shard_statistics()
        
        assert stats["num_assigned_shards"] == 2
        assert stats["num_orphaned_shards"] == 3
        assert stats["total_shards"] == 5


# ModelManager Tests
class TestModelManager:
    """Tests for ModelManager class."""
    
    def test_model_manager_initialization(self, temp_dir):
        """Test model manager initialization."""
        manager = ModelManager(
            ModelArchitecture.SIMPLE_CNN,
            num_classes=10,
            checkpoint_dir=temp_dir
        )
        
        assert manager.architecture == ModelArchitecture.SIMPLE_CNN
        assert manager.num_classes == 10
        assert manager.model is None
    
    def test_initialize_model(self, temp_dir):
        """Test model initialization."""
        manager = ModelManager(
            ModelArchitecture.SIMPLE_CNN,
            num_classes=10,
            checkpoint_dir=temp_dir,
            device='cpu'
        )
        
        success = manager.initialize_model(learning_rate=0.001)
        
        assert success
        assert manager.model is not None
        assert manager.optimizer is not None
        assert manager.parameter_version == 0
        assert len(manager.parameter_shapes) > 0
    
    def test_get_set_parameters(self, temp_dir):
        """Test getting and setting parameters."""
        manager = ModelManager(
            ModelArchitecture.SIMPLE_CNN,
            checkpoint_dir=temp_dir,
            device='cpu'
        )
        manager.initialize_model()
        
        # Get parameters
        params = manager.get_parameters()
        assert isinstance(params, dict)
        assert len(params) > 0
        
        # Modify and set back
        modified_params = {
            name: arr * 1.1
            for name, arr in params.items()
        }
        
        success = manager.set_parameters(modified_params)
        assert success
        assert manager.parameter_version == 1
    
    def test_apply_gradients(self, temp_dir):
        """Test applying gradients."""
        manager = ModelManager(
            ModelArchitecture.SIMPLE_CNN,
            checkpoint_dir=temp_dir,
            device='cpu'
        )
        manager.initialize_model(learning_rate=0.01)
        
        # Get initial parameters
        initial_params = manager.get_parameters()
        
        # Create mock gradients
        gradients = {
            name: np.random.randn(*arr.shape) * 0.01
            for name, arr in initial_params.items()
        }
        
        # Apply gradients
        success = manager.apply_gradients(gradients)
        assert success
        
        # Check parameters changed
        new_params = manager.get_parameters()
        assert not np.allclose(
            initial_params[list(initial_params.keys())[0]],
            new_params[list(new_params.keys())[0]]
        )
    
    def test_serialize_deserialize_parameters(self, temp_dir):
        """Test parameter serialization."""
        manager = ModelManager(
            ModelArchitecture.SIMPLE_CNN,
            checkpoint_dir=temp_dir,
            device='cpu'
        )
        manager.initialize_model()
        
        # Serialize
        serialized = manager.serialize_parameters(compress=True)
        assert serialized is not None
        assert isinstance(serialized, bytes)
        
        # Deserialize into new manager
        new_manager = ModelManager(
            ModelArchitecture.SIMPLE_CNN,
            checkpoint_dir=temp_dir,
            device='cpu'
        )
        new_manager.initialize_model()
        
        success = new_manager.deserialize_parameters(serialized, compressed=True)
        assert success
        
        # Verify parameters match
        original_params = manager.get_parameters()
        loaded_params = new_manager.get_parameters()
        
        for name in original_params:
            assert np.allclose(original_params[name], loaded_params[name])
    
    def test_save_load_checkpoint(self, temp_dir):
        """Test checkpoint save and load."""
        manager = ModelManager(
            ModelArchitecture.SIMPLE_CNN,
            checkpoint_dir=temp_dir,
            device='cpu'
        )
        manager.initialize_model()
        
        # Save checkpoint
        checkpoint_file = manager.save_checkpoint(epoch=1, metrics={"loss": 0.5})
        assert checkpoint_file is not None
        assert Path(checkpoint_file).exists()
        
        # Load into new manager
        new_manager = ModelManager(
            ModelArchitecture.SIMPLE_CNN,
            checkpoint_dir=temp_dir,
            device='cpu'
        )
        success = new_manager.load_checkpoint(checkpoint_file)
        assert success
        
        # Verify parameters match
        original_params = manager.get_parameters()
        loaded_params = new_manager.get_parameters()
        
        for name in original_params:
            assert np.allclose(original_params[name], loaded_params[name])
    
    def test_validate_parameters(self, temp_dir):
        """Test parameter validation."""
        manager = ModelManager(
            ModelArchitecture.SIMPLE_CNN,
            checkpoint_dir=temp_dir,
            device='cpu'
        )
        manager.initialize_model()
        
        params = manager.get_parameters()
        
        # Valid parameters
        assert manager.validate_parameters(params)
        
        # Invalid: NaN values
        invalid_params = params.copy()
        first_key = list(invalid_params.keys())[0]
        invalid_params[first_key][0] = np.nan
        assert not manager.validate_parameters(invalid_params)
        
        # Invalid: Inf values
        invalid_params = params.copy()
        invalid_params[first_key][0] = np.inf
        assert not manager.validate_parameters(invalid_params)


# GradientAggregator Tests
class TestGradientAggregator:
    """Tests for GradientAggregator class."""
    
    def test_aggregator_initialization(self):
        """Test aggregator initialization."""
        aggregator = GradientAggregator(
            strategy=AggregationStrategy.SIMPLE_AVERAGE,
            timeout_seconds=10.0,
            gradient_clip_value=1.0
        )
        
        assert aggregator.strategy == AggregationStrategy.SIMPLE_AVERAGE
        assert aggregator.timeout_seconds == 10.0
        assert aggregator.gradient_clip_value == 1.0
        assert aggregator.current_round == 0
    
    def test_start_round(self):
        """Test starting an aggregation round."""
        aggregator = GradientAggregator()
        
        node_ids = ["node_1", "node_2", "node_3"]
        aggregator.start_round(round_number=1, expected_node_ids=node_ids)
        
        assert aggregator.current_round == 1
        assert aggregator.expected_nodes == node_ids
        assert len(aggregator.received_gradients) == 0
        assert aggregator.round_start_time is not None
    
    def test_receive_gradient(self):
        """Test receiving gradients from nodes."""
        aggregator = GradientAggregator()
        node_ids = ["node_1", "node_2"]
        aggregator.start_round(1, node_ids)
        
        # Create mock gradients
        gradients = {
            "layer1": np.random.randn(10, 10),
            "layer2": np.random.randn(5),
        }
        
        # Receive gradient
        success = aggregator.receive_gradient("node_1", gradients)
        assert success
        assert "node_1" in aggregator.received_gradients
        
        # Try duplicate
        success = aggregator.receive_gradient("node_1", gradients)
        assert not success  # Should reject duplicate
    
    def test_gradient_validation(self):
        """Test gradient validation."""
        aggregator = GradientAggregator()
        aggregator.start_round(1, ["node_1"])
        
        # Valid gradients
        valid_grads = {
            "layer1": np.random.randn(10, 10),
        }
        success = aggregator.receive_gradient("node_1", valid_grads)
        assert success
        
        # Invalid: NaN
        aggregator.start_round(2, ["node_2"])
        invalid_grads = {
            "layer1": np.array([[np.nan, 1.0], [2.0, 3.0]]),
        }
        success = aggregator.receive_gradient("node_2", invalid_grads)
        assert not success
    
    def test_simple_average_aggregation(self):
        """Test simple average aggregation."""
        aggregator = GradientAggregator(
            strategy=AggregationStrategy.SIMPLE_AVERAGE
        )
        
        node_ids = ["node_1", "node_2", "node_3"]
        aggregator.start_round(1, node_ids)
        
        # Create gradients
        grad_shape = (5, 5)
        grad1 = np.ones(grad_shape) * 1.0
        grad2 = np.ones(grad_shape) * 2.0
        grad3 = np.ones(grad_shape) * 3.0
        
        # Submit gradients
        aggregator.receive_gradient("node_1", {"layer1": grad1})
        aggregator.receive_gradient("node_2", {"layer1": grad2})
        aggregator.receive_gradient("node_3", {"layer1": grad3})
        
        # Aggregate
        parameter_shapes = {"layer1": grad_shape}
        result = aggregator.aggregate_round(parameter_shapes)
        
        assert result is not None
        assert "layer1" in result
        
        # Should be average: (1 + 2 + 3) / 3 = 2
        expected = np.ones(grad_shape) * 2.0
        assert np.allclose(result["layer1"], expected)
    
    def test_weighted_average_aggregation(self):
        """Test weighted average aggregation."""
        aggregator = GradientAggregator(
            strategy=AggregationStrategy.WEIGHTED_AVERAGE
        )
        
        node_ids = ["node_1", "node_2"]
        aggregator.start_round(1, node_ids)
        
        grad_shape = (3, 3)
        grad1 = np.ones(grad_shape) * 1.0
        grad2 = np.ones(grad_shape) * 3.0
        
        # Submit with metadata (data_samples)
        aggregator.receive_gradient(
            "node_1",
            {"layer1": grad1},
            metadata={"data_samples": 100}
        )
        aggregator.receive_gradient(
            "node_2",
            {"layer1": grad2},
            metadata={"data_samples": 200}
        )
        
        # Aggregate
        parameter_shapes = {"layer1": grad_shape}
        result = aggregator.aggregate_round(parameter_shapes)
        
        assert result is not None
        # Weighted avg: (1*100 + 3*200) / 300 = 700/300 ≈ 2.333
        expected = np.ones(grad_shape) * (700.0 / 300.0)
        assert np.allclose(result["layer1"], expected, atol=0.01)
    
    def test_gradient_clipping(self):
        """Test gradient clipping."""
        aggregator = GradientAggregator(
            gradient_clip_value=1.0
        )
        
        aggregator.start_round(1, ["node_1"])
        
        # Create large gradients
        large_grads = {
            "layer1": np.ones((5, 5)) * 10.0,  # Large values
        }
        
        success = aggregator.receive_gradient("node_1", large_grads)
        assert success
        
        # Check gradient was clipped
        received = aggregator.received_gradients["node_1"]
        # Compute norm from dict of gradients
        total_norm = 0.0
        for grad_array in received.values():
            total_norm += np.sum(grad_array ** 2)
        grad_norm = np.sqrt(total_norm)
        assert grad_norm <= aggregator.gradient_clip_value * 1.1  # Small tolerance
    
    def test_should_aggregate_all_nodes(self):
        """Test aggregation decision with all nodes."""
        aggregator = GradientAggregator()
        
        node_ids = ["node_1", "node_2"]
        aggregator.start_round(1, node_ids)
        
        # Not ready initially
        should, reason = aggregator.should_aggregate()
        assert not should
        
        # Receive all gradients
        for node_id in node_ids:
            aggregator.receive_gradient(node_id, {"layer1": np.ones((2, 2))})
        
        # Should aggregate now
        should, reason = aggregator.should_aggregate()
        assert should
        assert "All nodes" in reason
    
    def test_aggregation_statistics(self):
        """Test aggregation statistics."""
        aggregator = GradientAggregator()
        
        node_ids = ["node_1", "node_2"]
        aggregator.start_round(1, node_ids)
        
        # Receive gradients
        for node_id in node_ids:
            aggregator.receive_gradient(node_id, {"layer1": np.ones((2, 2))})
        
        # Aggregate
        parameter_shapes = {"layer1": (2, 2)}
        aggregator.aggregate_round(parameter_shapes)
        
        # Get statistics
        stats = aggregator.get_statistics()
        
        assert "current_round" in stats
        assert "total_rounds" in stats
        assert stats["total_rounds"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
