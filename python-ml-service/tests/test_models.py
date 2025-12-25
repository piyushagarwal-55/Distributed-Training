"""
Tests for data models and configuration.
"""

import pytest
import json
from datetime import datetime
from pathlib import Path
from src.models.config import (
    TrainingConfig,
    NetworkConfig,
    BlockchainConfig,
    SystemConfig,
    DatasetType,
    ModelArchitecture,
)
from src.models.node import NodeMetadata, NodeStatus, NodeRegistry
from src.models.metrics import TrainingMetrics, NetworkMetrics, GradientUpdate
from src.models.blockchain import BlockchainContribution, SessionContributions


class TestTrainingConfig:
    """Test TrainingConfig model."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = TrainingConfig()
        assert config.model_architecture == ModelArchitecture.SIMPLE_CNN
        assert config.dataset == DatasetType.MNIST
        assert config.learning_rate == 0.001
        assert config.batch_size == 64
        assert config.epochs == 10
        assert config.num_nodes == 5
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = TrainingConfig(
            model_architecture=ModelArchitecture.RESNET18,
            dataset=DatasetType.CIFAR10,
            learning_rate=0.01,
            batch_size=128,
            epochs=20,
            num_nodes=10,
        )
        assert config.model_architecture == ModelArchitecture.RESNET18
        assert config.dataset == DatasetType.CIFAR10
        assert config.learning_rate == 0.01
        assert config.batch_size == 128
        assert config.epochs == 20
        assert config.num_nodes == 10
    
    def test_invalid_learning_rate(self):
        """Test that invalid learning rate raises error."""
        with pytest.raises(ValueError):
            TrainingConfig(learning_rate=1.5)
    
    def test_invalid_batch_size(self):
        """Test that invalid batch size raises error."""
        with pytest.raises(ValueError):
            TrainingConfig(batch_size=-1)
    
    def test_serialization(self):
        """Test config serialization to/from JSON."""
        config = TrainingConfig(
            learning_rate=0.01,
            batch_size=32,
            epochs=5,
        )
        
        # To dict
        config_dict = config.model_dump()
        assert config_dict["learning_rate"] == 0.01
        assert config_dict["batch_size"] == 32
        
        # From dict
        config2 = TrainingConfig(**config_dict)
        assert config2.learning_rate == config.learning_rate
        assert config2.batch_size == config.batch_size


class TestNodeMetadata:
    """Test NodeMetadata model."""
    
    def test_create_node(self):
        """Test creating node metadata."""
        node = NodeMetadata(
            node_id="node-1",
            node_address="localhost:50051",
            gpu_model="NVIDIA A100",
            gpu_memory_gb=40.0,
        )
        assert node.node_id == "node-1"
        assert node.status == NodeStatus.INITIALIZING
        assert node.gpu_memory_gb == 40.0
    
    def test_update_heartbeat(self):
        """Test heartbeat update."""
        node = NodeMetadata(node_id="node-1", node_address="localhost:50051")
        old_heartbeat = node.last_heartbeat
        
        import time
        time.sleep(0.01)
        node.update_heartbeat()
        
        assert node.last_heartbeat > old_heartbeat
    
    def test_record_updates(self):
        """Test recording successful and failed updates."""
        node = NodeMetadata(node_id="node-1", node_address="localhost:50051")
        
        # Record successful updates
        node.record_successful_update(1.5)
        node.record_successful_update(2.0)
        assert node.successful_updates == 2
        assert node.total_gradients_submitted == 2
        assert node.total_compute_time_seconds == 3.5
        
        # Record failed update
        node.record_failed_update()
        assert node.failed_updates == 1
        assert node.total_gradients_submitted == 3
    
    def test_success_rate(self):
        """Test success rate calculation."""
        node = NodeMetadata(node_id="node-1", node_address="localhost:50051")
        
        # No updates yet
        assert node.calculate_success_rate() == 1.0
        
        # Add some updates
        node.record_successful_update(1.0)
        node.record_successful_update(1.0)
        node.record_failed_update()
        
        # 2 successful out of 3 total
        assert node.calculate_success_rate() == pytest.approx(2/3)
    
    def test_is_healthy(self):
        """Test health check."""
        node = NodeMetadata(node_id="node-1", node_address="localhost:50051")
        
        # Initially should be unhealthy (INITIALIZING)
        assert not node.is_healthy()
        
        # Set to READY
        node.update_status(NodeStatus.READY)
        assert node.is_healthy()
        
        # Set to ERROR
        node.update_status(NodeStatus.ERROR)
        assert not node.is_healthy()


class TestNodeRegistry:
    """Test NodeRegistry."""
    
    def test_register_and_get_node(self):
        """Test node registration and retrieval."""
        registry = NodeRegistry()
        node = NodeMetadata(node_id="node-1", node_address="localhost:50051")
        
        registry.register_node(node)
        retrieved = registry.get_node("node-1")
        
        assert retrieved is not None
        assert retrieved.node_id == "node-1"
    
    def test_remove_node(self):
        """Test node removal."""
        registry = NodeRegistry()
        node = NodeMetadata(node_id="node-1", node_address="localhost:50051")
        
        registry.register_node(node)
        assert registry.count_nodes() == 1
        
        removed = registry.remove_node("node-1")
        assert removed is not None
        assert removed.node_id == "node-1"
        assert registry.count_nodes() == 0
    
    def test_get_active_nodes(self):
        """Test getting active nodes."""
        registry = NodeRegistry()
        
        # Add healthy nodes
        for i in range(3):
            node = NodeMetadata(
                node_id=f"node-{i}",
                node_address=f"localhost:5005{i}",
                status=NodeStatus.READY,
            )
            registry.register_node(node)
        
        # Add unhealthy node
        bad_node = NodeMetadata(
            node_id="node-bad",
            node_address="localhost:50060",
            status=NodeStatus.ERROR,
        )
        registry.register_node(bad_node)
        
        active = registry.get_active_nodes()
        assert len(active) == 3
        assert all(node.is_healthy() for node in active)


class TestTrainingMetrics:
    """Test TrainingMetrics model."""
    
    def test_create_metrics(self):
        """Test creating training metrics."""
        metrics = TrainingMetrics(
            node_id="node-1",
            epoch=1,
            step=10,
            loss=0.5,
            accuracy=0.85,
            samples_processed=64,
            time_taken_seconds=2.5,
            samples_per_second=25.6,
            gradient_norm=1.2,
        )
        
        assert metrics.node_id == "node-1"
        assert metrics.loss == 0.5
        assert metrics.accuracy == 0.85
        assert isinstance(metrics.timestamp, datetime)


class TestNetworkMetrics:
    """Test NetworkMetrics model."""
    
    def test_quality_score_calculation(self):
        """Test network quality score calculation."""
        metrics = NetworkMetrics(
            node_id="node-1",
            latency_ms=50.0,
            packet_loss_rate=0.01,
            messages_sent=100,
            messages_failed=5,
        )
        
        score = metrics.calculate_quality_score()
        assert 0 <= score <= 1
        assert metrics.quality_score == score
    
    def test_perfect_network(self):
        """Test quality score for perfect network."""
        metrics = NetworkMetrics(
            node_id="node-1",
            latency_ms=0.0,
            packet_loss_rate=0.0,
            messages_sent=100,
            messages_failed=0,
        )
        
        score = metrics.calculate_quality_score()
        assert score == 1.0
    
    def test_poor_network(self):
        """Test quality score for poor network."""
        metrics = NetworkMetrics(
            node_id="node-1",
            latency_ms=500.0,
            packet_loss_rate=0.1,
            messages_sent=50,
            messages_failed=50,
        )
        
        score = metrics.calculate_quality_score()
        assert score < 0.65  # Calculated score is ~0.62 for poor network


class TestGradientUpdate:
    """Test GradientUpdate model."""
    
    def test_create_gradient_update(self):
        """Test creating gradient update."""
        update = GradientUpdate(
            node_id="node-1",
            update_id="update-1",
            epoch=1,
            step=10,
            batch_size=64,
            gradient_data=[[1.0, 2.0, 3.0, 4.0]],  # Flattened gradient data
            gradient_shapes=[[2, 2]],
            gradient_norm=5.5,
            num_parameters=4,
            local_loss=0.5,
            compute_time_seconds=2.0,
        )
        
        assert update.node_id == "node-1"
        assert update.gradient_norm == 5.5
        assert len(update.gradient_data) == 1


class TestBlockchainContribution:
    """Test BlockchainContribution model."""
    
    def test_contribution_score_calculation(self):
        """Test contribution score calculation."""
        contribution = BlockchainContribution(
            node_id="node-1",
            wallet_address="0x123",
            session_id="session-1",
            epoch=1,
            compute_time_seconds=100.0,
            gradients_accepted=10,
            gradients_rejected=0,
            samples_processed=640,
            average_loss=0.5,
            gradient_quality_score=0.9,
            network_reliability_score=0.95,
        )
        
        score = contribution.calculate_contribution_score()
        assert score > 0
        assert contribution.contribution_score == score
    
    def test_contribution_with_rejections(self):
        """Test contribution score with some rejections."""
        contribution = BlockchainContribution(
            node_id="node-1",
            wallet_address="0x123",
            session_id="session-1",
            epoch=1,
            compute_time_seconds=100.0,
            gradients_accepted=8,
            gradients_rejected=2,  # 20% rejection rate
            samples_processed=640,
            average_loss=0.5,
            gradient_quality_score=0.9,
            network_reliability_score=0.95,
        )
        
        score = contribution.calculate_contribution_score()
        # Should be lower due to rejections
        assert score < 100.0 * 0.9 * 0.95  # Max if no rejections


class TestSessionContributions:
    """Test SessionContributions model."""
    
    def test_add_contributions(self):
        """Test adding contributions."""
        session = SessionContributions(session_id="session-1")
        
        contribution1 = BlockchainContribution(
            node_id="node-1",
            wallet_address="0x123",
            session_id="session-1",
            epoch=1,
            compute_time_seconds=50.0,
            gradients_accepted=5,
            samples_processed=320,
            average_loss=0.5,
        )
        
        contribution2 = BlockchainContribution(
            node_id="node-2",
            wallet_address="0x456",
            session_id="session-1",
            epoch=1,
            compute_time_seconds=60.0,
            gradients_accepted=6,
            samples_processed=384,
            average_loss=0.45,
        )
        
        session.add_contribution(contribution1)
        session.add_contribution(contribution2)
        
        assert len(session.get_all_nodes()) == 2
        assert session.total_compute_time == 110.0
        assert session.total_samples_processed == 704
    
    def test_reward_distribution(self):
        """Test reward distribution calculation."""
        session = SessionContributions(session_id="session-1")
        
        # Add two contributions with different scores
        for i in range(2):
            contribution = BlockchainContribution(
                node_id=f"node-{i}",
                wallet_address=f"0x{i}",
                session_id="session-1",
                epoch=1,
                compute_time_seconds=50.0 * (i + 1),  # Different compute times
                gradients_accepted=5,
                samples_processed=320,
                average_loss=0.5,
            )
            contribution.calculate_contribution_score()
            session.add_contribution(contribution)
        
        # Calculate distribution
        total_reward = 1000.0
        distribution = session.calculate_reward_distribution(total_reward)
        
        # Check that total equals reward pool
        assert sum(distribution.values()) == pytest.approx(total_reward)
        
        # Check that node-1 gets more (higher compute time)
        assert distribution["node-1"] > distribution["node-0"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
