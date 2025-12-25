"""
Comprehensive tests for Phase 3 & 4: GPU Node Simulator and Network-Aware Adaptation.

This test suite covers all components:
- Phase 3.1: GPU Node Service
- Phase 3.2: Network Simulation Layer
- Phase 3.3: Node Metrics Collection
- Phase 4.1: Network Quality Monitor
- Phase 4.2: Adaptive Batch Size Controller
- Phase 4.3: Dynamic Node Selection
- Phase 4.4: Adaptive Training Orchestrator
"""

import pytest
import time
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader

from src.models.config import SystemConfig, TrainingConfig, ModelArchitecture
from src.models.node import NodeStatus
from src.core.gpu_node import GPUNodeService
from src.core.network_simulator import NetworkSimulator, NetworkProfile, NetworkEvent
from src.core.metrics_collector import MetricsCollector
from src.core.network_monitor import NetworkQualityMonitor, ConnectionQuality
from src.core.adaptive_batch_controller import AdaptiveBatchController, BatchSizeStrategy
from src.core.node_selector import DynamicNodeSelector, SelectionStrategy
from src.core.adaptive_orchestrator import AdaptiveOrchestrator, AdaptationPolicy, TrainingPhase


# ============================================================================
# PHASE 3.1: GPU Node Service Tests
# ============================================================================

class TestGPUNodeService:
    """Test GPU node service functionality."""
    
    @pytest.fixture
    def sample_config(self):
        """Create sample config for testing."""
        return SystemConfig(
            training=TrainingConfig(
                model_architecture="simple_cnn",
                dataset="mnist",
                batch_size=32,
                epochs=2,
                learning_rate=0.01
            )
        )
    
    @pytest.fixture
    def gpu_specs(self):
        """Create sample GPU specs."""
        return {
            'gpu_model': 'TestGPU',
            'gpu_memory_gb': 8.0,
            'compute_capability': 1.0
        }
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        # Create dummy dataset
        X = torch.randn(100, 1, 28, 28)
        y = torch.randint(0, 10, (100,))
        dataset = TensorDataset(X, y)
        loader = DataLoader(dataset, batch_size=32, shuffle=True)
        return loader
    
    def test_node_initialization(self, sample_config, gpu_specs):
        """Test GPU node initialization."""
        print("\n[TEST] Testing GPU node initialization...")
        
        node = GPUNodeService("test_node_1", gpu_specs, sample_config)
        
        assert node.node_id == "test_node_1"
        assert node.gpu_specs == gpu_specs
        assert node.status == NodeStatus.INITIALIZING
        assert node.model is None
        
        print("✓ Node initialization successful")
    
    def test_node_setup_with_data(self, sample_config, gpu_specs, sample_data):
        """Test node initialization with model and data."""
        print("\n[TEST] Testing node setup with model and data...")
        
        node = GPUNodeService("test_node_2", gpu_specs, sample_config)
        
        # Create sample parameters
        from src.core.model_manager import ModelManager
        manager = ModelManager(sample_config.training.model_architecture)
        manager.initialize_model()
        params = manager.get_parameters()
        
        # Initialize node
        success = node.initialize(params, sample_data, data_shard_id=0)
        
        assert success == True
        assert node.status == NodeStatus.READY
        assert node.model is not None
        assert node.data_loader is not None
        
        print("✓ Node setup with data successful")
    
    def test_training_step(self, sample_config, gpu_specs, sample_data):
        """Test single training step."""
        print("\n[TEST] Testing training step execution...")
        
        node = GPUNodeService("test_node_3", gpu_specs, sample_config, simulated_delay_factor=0.1)
        
        # Setup node
        from src.core.model_manager import ModelManager
        manager = ModelManager(sample_config.training.model_architecture)
        manager.initialize_model()
        params = manager.get_parameters()
        node.initialize(params, sample_data, data_shard_id=0)
        
        # Execute training step
        result = node.train_step()
        
        assert result is not None
        assert 'gradients' in result
        assert 'metrics' in result
        assert 'step_info' in result
        assert result['metrics']['loss'] > 0
        assert result['metrics']['gradient_norm'] > 0
        
        print(f"✓ Training step successful - Loss: {result['metrics']['loss']:.4f}")
    
    def test_multiple_training_steps(self, sample_config, gpu_specs, sample_data):
        """Test multiple training steps."""
        print("\n[TEST] Testing multiple training steps...")
        
        node = GPUNodeService("test_node_4", gpu_specs, sample_config, simulated_delay_factor=0.1)
        
        from src.core.model_manager import ModelManager
        manager = ModelManager(sample_config.training.model_architecture)
        manager.initialize_model()
        params = manager.get_parameters()
        node.initialize(params, sample_data, data_shard_id=0)
        
        # Run 5 steps
        for i in range(5):
            result = node.train_step()
            assert result is not None
            print(f"  Step {i+1}: Loss={result['metrics']['loss']:.4f}, "
                  f"Time={result['metrics']['step_time']:.3f}s")
        
        assert node.steps_completed == 5
        
        print("✓ Multiple training steps successful")
    
    def test_parameter_update(self, sample_config, gpu_specs, sample_data):
        """Test parameter update."""
        print("\n[TEST] Testing parameter updates...")
        
        node = GPUNodeService("test_node_5", gpu_specs, sample_config)
        
        from src.core.model_manager import ModelManager
        manager = ModelManager(sample_config.training.model_architecture)
        manager.initialize_model()
        params = manager.get_parameters()
        node.initialize(params, sample_data, data_shard_id=0)
        
        initial_version = node.parameter_version
        
        # Update parameters
        new_params = {k: v + 0.01 for k, v in params.items()}
        success = node.update_parameters(new_params)
        
        assert success == True
        assert node.parameter_version > initial_version
        
        print("✓ Parameter update successful")
    
    def test_batch_size_update(self, sample_config, gpu_specs, sample_data):
        """Test batch size update."""
        print("\n[TEST] Testing batch size updates...")
        
        node = GPUNodeService("test_node_6", gpu_specs, sample_config)
        
        from src.core.model_manager import ModelManager
        manager = ModelManager(sample_config.training.model_architecture)
        manager.initialize_model()
        params = manager.get_parameters()
        node.initialize(params, sample_data, data_shard_id=0)
        
        initial_batch_size = node.current_batch_size
        new_batch_size = 64
        
        success = node.update_batch_size(new_batch_size)
        
        assert success == True
        assert node.current_batch_size == new_batch_size
        
        print(f"✓ Batch size updated: {initial_batch_size} -> {new_batch_size}")
    
    def test_health_check(self, sample_config, gpu_specs):
        """Test health check."""
        print("\n[TEST] Testing health check...")
        
        node = GPUNodeService("test_node_7", gpu_specs, sample_config)
        
        health = node.health_check()
        
        assert 'node_id' in health
        assert 'status' in health
        assert health['node_id'] == "test_node_7"
        
        print("✓ Health check successful")
    
    def test_metrics_summary(self, sample_config, gpu_specs, sample_data):
        """Test metrics summary."""
        print("\n[TEST] Testing metrics summary...")
        
        node = GPUNodeService("test_node_8", gpu_specs, sample_config, simulated_delay_factor=0.1)
        
        from src.core.model_manager import ModelManager
        manager = ModelManager(sample_config.training.model_architecture)
        manager.initialize_model()
        params = manager.get_parameters()
        node.initialize(params, sample_data, data_shard_id=0)
        
        # Run a few steps
        for _ in range(3):
            node.train_step()
        
        summary = node.get_metrics_summary()
        
        assert 'loss' in summary
        assert 'gradient_norm' in summary
        assert 'timing' in summary
        assert summary['training_progress']['steps_completed'] == 3
        
        print("✓ Metrics summary successful")


# ============================================================================
# PHASE 3.2: Network Simulation Layer Tests
# ============================================================================

class TestNetworkSimulator:
    """Test network simulation functionality."""
    
    def test_simulator_initialization(self):
        """Test network simulator initialization."""
        print("\n[TEST] Testing network simulator initialization...")
        
        sim = NetworkSimulator(default_profile="average")
        
        assert sim.default_profile == "average"
        assert sim.enabled == True
        
        print("✓ Network simulator initialized")
    
    def test_node_profile_assignment(self):
        """Test setting node network profiles."""
        print("\n[TEST] Testing node profile assignment...")
        
        sim = NetworkSimulator()
        
        sim.set_node_profile("node1", NetworkProfile.GOOD.value)
        sim.set_node_profile("node2", NetworkProfile.POOR.value)
        
        assert sim.get_node_profile("node1") == "good"
        assert sim.get_node_profile("node2") == "poor"
        
        print("✓ Node profiles assigned successfully")
    
    def test_perfect_network(self):
        """Test perfect network profile."""
        print("\n[TEST] Testing perfect network simulation...")
        
        sim = NetworkSimulator()
        sim.set_node_profile("node1", NetworkProfile.PERFECT.value)
        
        start = time.time()
        success, latency, msg = sim.simulate_communication("node1", "test_message")
        elapsed = time.time() - start
        
        assert success == True
        assert latency < 2  # Very low latency
        assert msg == "test_message"
        
        print(f"✓ Perfect network: latency={latency:.2f}ms")
    
    def test_poor_network(self):
        """Test poor network profile."""
        print("\n[TEST] Testing poor network simulation...")
        
        sim = NetworkSimulator()
        sim.set_node_profile("node1", NetworkProfile.POOR.value)
        
        # Test multiple communications to check packet loss
        successes = 0
        total_latency = 0
        trials = 20
        
        for _ in range(trials):
            success, latency, msg = sim.simulate_communication("node1", "test")
            if success:
                successes += 1
                total_latency += latency
        
        success_rate = successes / trials
        avg_latency = total_latency / successes if successes > 0 else 0
        
        print(f"[+] Poor network: success_rate={success_rate:.2%}, avg_latency={avg_latency:.1f}ms")
        
        assert success_rate < 1.0  # Some packet loss expected
        if successes > 0:
            assert avg_latency > 100  # High latency expected when packets succeed
    
    def test_communication_with_retry(self):
        """Test communication with automatic retry."""
        print("\n[TEST] Testing communication with retry...")
        
        sim = NetworkSimulator()
        sim.set_node_profile("node1", NetworkProfile.UNSTABLE.value)
        
        success, total_latency, msg, attempts = sim.simulate_with_retry(
            "node1", "test_message", max_retries=3
        )
        
        print(f"✓ Retry test: success={success}, attempts={attempts}, latency={total_latency:.1f}ms")
        
        assert attempts >= 1
    
    def test_latency_spike_injection(self):
        """Test latency spike injection."""
        print("\n[TEST] Testing latency spike injection...")
        
        sim = NetworkSimulator()
        sim.set_node_profile("node1", NetworkProfile.GOOD.value)
        
        # Inject spike
        sim.inject_latency_spike("node1", duration_seconds=1.0)
        
        # Process event immediately
        sim.process_scheduled_events()
        
        # Check profile changed
        assert sim.get_node_profile("node1") == "poor"
        
        print("✓ Latency spike injected")
    
    def test_metrics_collection(self):
        """Test network metrics collection."""
        print("\n[TEST] Testing network metrics collection...")
        
        sim = NetworkSimulator()
        sim.set_node_profile("node1", NetworkProfile.AVERAGE.value)
        
        # Send multiple messages
        for _ in range(10):
            sim.simulate_communication("node1", "test")
        
        metrics = sim.get_node_metrics("node1")
        
        assert metrics['messages_sent'] == 10
        assert 'drop_rate' in metrics
        assert 'average_latency_ms' in metrics
        
        print(f"✓ Metrics: {metrics['messages_sent']} messages, "
              f"drop_rate={metrics['drop_rate']:.2%}")


# ============================================================================
# PHASE 3.3: Node Metrics Collection Tests
# ============================================================================

class TestMetricsCollector:
    """Test metrics collector functionality."""
    
    def test_collector_initialization(self):
        """Test metrics collector initialization."""
        print("\n[TEST] Testing metrics collector initialization...")
        
        collector = MetricsCollector("node1", history_size=50)
        
        assert collector.node_id == "node1"
        assert collector.history_size == 50
        assert collector.total_steps == 0
        
        print("✓ Metrics collector initialized")
    
    def test_training_metrics_recording(self):
        """Test recording training metrics."""
        print("\n[TEST] Testing training metrics recording...")
        
        collector = MetricsCollector("node1")
        
        # Record some steps
        for i in range(5):
            collector.record_training_step(
                step=i,
                loss=1.0 - i * 0.1,
                gradient_norm=0.5 + i * 0.05,
                step_time=0.1,
                forward_time=0.05,
                backward_time=0.05,
                batch_size=32
            )
        
        summary = collector.get_training_summary()
        
        assert summary['available'] == True
        assert summary['total_steps'] == 5
        assert len(summary['loss']['recent_history']) == 5
        
        print(f"✓ Training metrics recorded: {summary['total_steps']} steps")
    
    def test_network_metrics_recording(self):
        """Test recording network metrics."""
        print("\n[TEST] Testing network metrics recording...")
        
        collector = MetricsCollector("node1")
        
        # Record network events
        for i in range(10):
            collector.record_network_event(
                latency_ms=50.0 + i * 10,
                success=i % 5 != 0,  # 20% failure rate
                retries=1 if i % 5 == 0 else 0
            )
        
        summary = collector.get_network_summary()
        
        assert summary['available'] == True
        assert summary['reliability']['success_rate'] == 0.8
        
        print(f"✓ Network metrics: success_rate={summary['reliability']['success_rate']:.2%}")
    
    def test_contribution_metrics(self):
        """Test contribution metrics calculation."""
        print("\n[TEST] Testing contribution metrics...")
        
        collector = MetricsCollector("node1")
        
        # Simulate some work
        collector.total_compute_time = 10.0
        collector.total_communication_time = 2.0
        collector.successful_communications = 8
        collector.failed_communications = 2
        collector.total_steps = 10
        
        contribution = collector.get_contribution_metrics()
        
        assert 'contribution_score' in contribution
        assert contribution['compute_efficiency'] > 0
        assert contribution['reliability_score'] > 0
        
        print(f"✓ Contribution score: {contribution['contribution_score']:.2f}")
    
    def test_anomaly_detection(self):
        """Test anomaly detection."""
        print("\n[TEST] Testing anomaly detection...")
        
        collector = MetricsCollector("node1")
        
        # Record normal metrics
        for i in range(20):
            collector.record_training_step(
                step=i,
                loss=1.0,
                gradient_norm=0.5,
                step_time=0.1,
                forward_time=0.05,
                backward_time=0.05,
                batch_size=32
            )
        
        # Record anomalous spike
        collector.record_training_step(
            step=20,
            loss=10.0,  # Sudden spike
            gradient_norm=0.5,
            step_time=0.1,
            forward_time=0.05,
            backward_time=0.05,
            batch_size=32
        )
        
        anomalies = collector.detect_anomalies()
        
        assert len(anomalies) > 0
        assert any(a['type'] == 'loss_spike' for a in anomalies)
        
        print(f"✓ Detected {len(anomalies)} anomalies")


# ============================================================================
# PHASE 4.1: Network Quality Monitor Tests
# ============================================================================

class TestNetworkQualityMonitor:
    """Test network quality monitoring."""
    
    def test_monitor_initialization(self):
        """Test monitor initialization."""
        print("\n[TEST] Testing network monitor initialization...")
        
        monitor = NetworkQualityMonitor(update_interval_seconds=1.0)
        
        assert monitor.update_interval == 1.0
        assert len(monitor.profiles) == 0
        
        print("✓ Network monitor initialized")
    
    def test_node_registration(self):
        """Test node registration."""
        print("\n[TEST] Testing node registration...")
        
        monitor = NetworkQualityMonitor()
        
        monitor.register_node("node1")
        monitor.register_node("node2")
        
        assert "node1" in monitor.profiles
        assert "node2" in monitor.profiles
        
        print("✓ Nodes registered")
    
    def test_quality_classification(self):
        """Test connection quality classification."""
        print("\n[TEST] Testing quality classification...")
        
        monitor = NetworkQualityMonitor()
        monitor.register_node("node1")
        
        # Record good communications
        for _ in range(10):
            monitor.record_communication("node1", latency_ms=30.0, success=True)
        
        quality = monitor.get_node_quality("node1")
        
        print(f"✓ Node quality: {quality.value}")
        
        assert quality in [ConnectionQuality.EXCELLENT, ConnectionQuality.GOOD]
    
    def test_quality_degradation(self):
        """Test detecting quality degradation."""
        print("\n[TEST] Testing quality degradation detection...")
        
        monitor = NetworkQualityMonitor()
        monitor.register_node("node1")
        
        # Start with good communications
        for _ in range(5):
            monitor.record_communication("node1", latency_ms=30.0, success=True)
        
        initial_quality = monitor.get_node_quality("node1")
        
        # Simulate degradation
        for _ in range(10):
            monitor.record_communication("node1", latency_ms=300.0, success=False)
        
        final_quality = monitor.get_node_quality("node1")
        
        print(f"✓ Quality changed: {initial_quality.value} -> {final_quality.value}")
    
    def test_cluster_health_summary(self):
        """Test cluster health summary."""
        print("\n[TEST] Testing cluster health summary...")
        
        monitor = NetworkQualityMonitor()
        
        # Register multiple nodes with different qualities
        for i in range(5):
            monitor.register_node(f"node{i}")
            for _ in range(10):
                latency = 50.0 if i < 3 else 300.0
                success = i < 3
                monitor.record_communication(f"node{i}", latency_ms=latency, success=success)
        
        health = monitor.get_cluster_health_summary()
        
        assert health['total_nodes'] == 5
        assert 'quality_distribution' in health
        
        print(f"✓ Cluster health: {health['healthy_nodes']}/{health['total_nodes']} healthy")


# ============================================================================
# PHASE 4.2: Adaptive Batch Size Controller Tests
# ============================================================================

class TestAdaptiveBatchController:
    """Test adaptive batch size controller."""
    
    @pytest.fixture
    def network_monitor(self):
        """Create network monitor for testing."""
        monitor = NetworkQualityMonitor()
        return monitor
    
    def test_controller_initialization(self, network_monitor):
        """Test controller initialization."""
        print("\n[TEST] Testing batch controller initialization...")
        
        controller = AdaptiveBatchController(
            network_monitor,
            baseline_batch_size=64,
            strategy=BatchSizeStrategy.HYBRID
        )
        
        assert controller.baseline_batch_size == 64
        assert controller.strategy == BatchSizeStrategy.HYBRID
        
        print("✓ Batch controller initialized")
    
    def test_node_registration(self, network_monitor):
        """Test node registration."""
        print("\n[TEST] Testing node registration in controller...")
        
        controller = AdaptiveBatchController(network_monitor, baseline_batch_size=64)
        
        controller.register_node("node1")
        
        assert controller.get_batch_size("node1") == 64
        
        print("✓ Node registered with baseline batch size")
    
    def test_latency_based_adaptation(self, network_monitor):
        """Test latency-based batch size adaptation."""
        print("\n[TEST] Testing latency-based adaptation...")
        
        # Setup monitor with different latencies
        network_monitor.register_node("node1")
        network_monitor.register_node("node2")
        
        # Node1: low latency
        for _ in range(10):
            network_monitor.record_communication("node1", latency_ms=20.0, success=True)
        
        # Node2: high latency
        for _ in range(10):
            network_monitor.record_communication("node2", latency_ms=250.0, success=True)
        
        controller = AdaptiveBatchController(
            network_monitor,
            baseline_batch_size=64,
            strategy=BatchSizeStrategy.LATENCY_BASED
        )
        
        controller.register_node("node1")
        controller.register_node("node2")
        
        # Adapt
        changes = controller.evaluate_and_adapt()
        
        batch1 = controller.get_batch_size("node1")
        batch2 = controller.get_batch_size("node2")
        
        print(f"✓ Adapted: node1={batch1}, node2={batch2}")
        
        # High latency node should have larger batch
        assert batch2 >= batch1
    
    def test_batch_size_constraints(self, network_monitor):
        """Test batch size constraints."""
        print("\n[TEST] Testing batch size constraints...")
        
        controller = AdaptiveBatchController(
            network_monitor,
            min_batch_size=16,
            max_batch_size=128
        )
        
        controller.register_node("node1")
        
        # Try to set too small
        controller.set_batch_size("node1", 8)
        assert controller.get_batch_size("node1") == 16
        
        # Try to set too large
        controller.set_batch_size("node1", 256)
        assert controller.get_batch_size("node1") == 128
        
        print("✓ Batch size constraints enforced")


# ============================================================================
# PHASE 4.3: Dynamic Node Selection Tests
# ============================================================================

class TestDynamicNodeSelector:
    """Test dynamic node selector."""
    
    @pytest.fixture
    def network_monitor(self):
        """Create network monitor."""
        monitor = NetworkQualityMonitor()
        return monitor
    
    def test_selector_initialization(self, network_monitor):
        """Test selector initialization."""
        print("\n[TEST] Testing node selector initialization...")
        
        selector = DynamicNodeSelector(
            network_monitor,
            strategy=SelectionStrategy.ADAPTIVE_THRESHOLD
        )
        
        assert selector.strategy == SelectionStrategy.ADAPTIVE_THRESHOLD
        
        print("✓ Node selector initialized")
    
    def test_node_registration(self, network_monitor):
        """Test node registration."""
        print("\n[TEST] Testing node registration in selector...")
        
        selector = DynamicNodeSelector(network_monitor)
        
        selector.register_node("node1")
        
        assert "node1" in selector.node_states
        
        print("✓ Node registered")
    
    def test_all_available_strategy(self, network_monitor):
        """Test all-available selection strategy."""
        print("\n[TEST] Testing all-available strategy...")
        
        selector = DynamicNodeSelector(
            network_monitor,
            strategy=SelectionStrategy.ALL_AVAILABLE
        )
        
        for i in range(5):
            selector.register_node(f"node{i}")
        
        selected = selector.select_nodes()
        
        assert len(selected) == 5
        
        print(f"✓ Selected {len(selected)}/5 nodes (all available)")
    
    def test_quality_threshold_strategy(self, network_monitor):
        """Test quality threshold selection."""
        print("\n[TEST] Testing quality threshold strategy...")
        
        # Setup nodes with different qualities
        for i in range(5):
            network_monitor.register_node(f"node{i}")
            latency = 50.0 if i < 3 else 300.0
            success = i < 3
            for _ in range(10):
                network_monitor.record_communication(
                    f"node{i}",
                    latency_ms=latency,
                    success=success
                )
        
        selector = DynamicNodeSelector(
            network_monitor,
            strategy=SelectionStrategy.QUALITY_THRESHOLD,
            min_quality_score=40.0
        )
        
        for i in range(5):
            selector.register_node(f"node{i}")
        
        selected = selector.select_nodes()
        
        print(f"✓ Selected {len(selected)}/5 nodes (quality threshold)")
        
        # Should exclude poor quality nodes
        assert len(selected) < 5
    
    def test_contribution_tracking(self, network_monitor):
        """Test contribution tracking."""
        print("\n[TEST] Testing contribution tracking...")
        
        selector = DynamicNodeSelector(network_monitor)
        selector.register_node("node1")
        
        # Record contributions
        selector.record_contribution(
            "node1",
            compute_time=5.0,
            waiting_time=1.0,
            success=True
        )
        
        score = selector.get_node_score("node1")
        
        assert score > 0
        
        print(f"✓ Contribution score: {score:.2f}")
    
    def test_node_quarantine(self, network_monitor):
        """Test node quarantine mechanism."""
        print("\n[TEST] Testing node quarantine...")
        
        selector = DynamicNodeSelector(
            network_monitor,
            enable_quarantine=True,
            quarantine_threshold=3
        )
        
        selector.register_node("node1")
        
        # Record failures
        for _ in range(5):
            selector.record_contribution(
                "node1",
                compute_time=1.0,
                waiting_time=5.0,
                success=False
            )
        
        state = selector.get_node_state("node1")
        
        print(f"✓ Node state after failures: {state}")


# ============================================================================
# PHASE 4.4: Adaptive Orchestrator Tests
# ============================================================================

class TestAdaptiveOrchestrator:
    """Test adaptive orchestrator."""
    
    @pytest.fixture
    def setup_components(self):
        """Setup all components for orchestrator."""
        config = SystemConfig(
            training=TrainingConfig(
                epochs=2,
                batch_size=64
            )
        )
        
        network_monitor = NetworkQualityMonitor()
        batch_controller = AdaptiveBatchController(network_monitor, baseline_batch_size=64)
        node_selector = DynamicNodeSelector(network_monitor)
        
        return config, network_monitor, batch_controller, node_selector
    
    def test_orchestrator_initialization(self, setup_components):
        """Test orchestrator initialization."""
        print("\n[TEST] Testing orchestrator initialization...")
        
        config, monitor, batch_ctrl, node_sel = setup_components
        
        orchestrator = AdaptiveOrchestrator(
            config,
            monitor,
            batch_ctrl,
            node_sel,
            adaptation_policy=AdaptationPolicy.REACTIVE
        )
        
        assert orchestrator.adaptation_policy == AdaptationPolicy.REACTIVE
        assert orchestrator.current_round == 0
        
        print("✓ Orchestrator initialized")
    
    def test_training_start(self, setup_components):
        """Test training session start."""
        print("\n[TEST] Testing training start...")
        
        config, monitor, batch_ctrl, node_sel = setup_components
        
        orchestrator = AdaptiveOrchestrator(
            config, monitor, batch_ctrl, node_sel
        )
        
        orchestrator.start_training()
        
        from src.core.adaptive_orchestrator import TrainingPhase
        assert orchestrator.phase == TrainingPhase.WARMUP
        
        print("✓ Training started in warmup phase")
    
    def test_pre_round_adaptation(self, setup_components):
        """Test pre-round adaptation."""
        print("\n[TEST] Testing pre-round adaptation...")
        
        config, monitor, batch_ctrl, node_sel = setup_components
        
        orchestrator = AdaptiveOrchestrator(
            config, monitor, batch_ctrl, node_sel,
            warmup_rounds=0  # Skip warmup for testing
        )
        
        orchestrator.start_training()
        orchestrator.phase = TrainingPhase.ADAPTIVE_TRAINING  # Force adaptive phase
        
        # Register some nodes
        for i in range(3):
            node_id = f"node{i}"
            monitor.register_node(node_id)
            batch_ctrl.register_node(node_id)
            node_sel.register_node(node_id)
        
        decisions = orchestrator.pre_round_adaptation(
            available_nodes=["node0", "node1", "node2"],
            round_number=5
        )
        
        assert 'selected_nodes' in decisions
        assert 'batch_sizes' in decisions
        
        print(f"✓ Pre-round adaptation: {len(decisions['selected_nodes'])} nodes selected")
    
    def test_post_round_evaluation(self, setup_components):
        """Test post-round evaluation."""
        print("\n[TEST] Testing post-round evaluation...")
        
        config, monitor, batch_ctrl, node_sel = setup_components
        
        orchestrator = AdaptiveOrchestrator(
            config, monitor, batch_ctrl, node_sel
        )
        
        orchestrator.start_training()
        
        # Simulate round metrics
        metrics = {
            'average_loss': 0.5,
            'throughput': 100.0,
            'nodes_participated': 3
        }
        
        orchestrator.post_round_evaluation(1, metrics)
        
        assert len(orchestrator.round_metrics) == 1
        
        print("✓ Post-round evaluation complete")
    
    def test_orchestrator_status(self, setup_components):
        """Test getting orchestrator status."""
        print("\n[TEST] Testing orchestrator status...")
        
        config, monitor, batch_ctrl, node_sel = setup_components
        
        orchestrator = AdaptiveOrchestrator(
            config, monitor, batch_ctrl, node_sel
        )
        
        status = orchestrator.get_orchestrator_status()
        
        assert 'current_round' in status
        assert 'phase' in status
        assert 'adaptations_applied' in status
        
        print("✓ Orchestrator status retrieved")


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for complete system."""
    
    def test_full_adaptive_training_simulation(self):
        """Test complete adaptive training simulation."""
        print("\n[TEST] Running full adaptive training simulation...")
        
        # Create configuration
        config = SystemConfig(
            training=TrainingConfig(
                model_architecture="simple_cnn",
                dataset="mnist",
                batch_size=32,
                epochs=1,
                learning_rate=0.01,
                steps_per_epoch=10
            )
        )
        
        # Initialize components
        network_simulator = NetworkSimulator(default_profile="average")
        network_monitor = NetworkQualityMonitor()
        batch_controller = AdaptiveBatchController(network_monitor, baseline_batch_size=32)
        node_selector = DynamicNodeSelector(network_monitor)
        
        orchestrator = AdaptiveOrchestrator(
            config,
            network_monitor,
            batch_controller,
            node_selector,
            warmup_rounds=2
        )
        
        # Create mock nodes
        nodes = []
        for i in range(3):
            node_id = f"node{i}"
            gpu_specs = {
                'gpu_model': f'GPU{i}',
                'gpu_memory_gb': 8.0,
                'compute_capability': 1.0 + i * 0.2
            }
            
            node = GPUNodeService(node_id, gpu_specs, config, simulated_delay_factor=0.01)
            nodes.append((node_id, node))
            
            # Register with components
            network_monitor.register_node(node_id)
            batch_controller.register_node(node_id)
            node_selector.register_node(node_id)
            
            # Set network profiles
            if i == 0:
                network_simulator.set_node_profile(node_id, NetworkProfile.GOOD.value)
            elif i == 1:
                network_simulator.set_node_profile(node_id, NetworkProfile.AVERAGE.value)
            else:
                network_simulator.set_node_profile(node_id, NetworkProfile.POOR.value)
        
        # Start training
        orchestrator.start_training()
        
        # Create sample data for nodes
        X = torch.randn(100, 1, 28, 28)
        y = torch.randint(0, 10, (100,))
        dataset = TensorDataset(X, y)
        
        from src.core.model_manager import ModelManager
        manager = ModelManager(config.training.model_architecture)
        manager.initialize_model()
        params = manager.get_parameters()
        
        # Initialize nodes with data
        for node_id, node in nodes:
            shard_loader = DataLoader(dataset, batch_size=32, shuffle=True)
            node.initialize(params, shard_loader, data_shard_id=0)
        
        # Simulate training rounds
        num_rounds = 15
        for round_num in range(num_rounds):
            print(f"\n  === Round {round_num + 1}/{num_rounds} ===")
            
            # Pre-round adaptation
            available_nodes = [node_id for node_id, _ in nodes]
            decisions = orchestrator.pre_round_adaptation(available_nodes, round_num)
            
            selected_nodes = decisions['selected_nodes']
            print(f"  Selected nodes: {len(selected_nodes)}/{len(available_nodes)}")
            
            # Simulate training on selected nodes
            round_losses = []
            round_compute_times = []
            
            for node_id in selected_nodes:
                node = next(n for nid, n in nodes if nid == node_id)
                
                # Get batch size for this node
                batch_size = batch_controller.get_batch_size(node_id)
                node.update_batch_size(batch_size)
                
                # Execute training step
                result = node.train_step()
                
                if result:
                    round_losses.append(result['metrics']['loss'])
                    compute_time = result['metrics']['step_time']
                    round_compute_times.append(compute_time)
                    
                    # Simulate network communication
                    success, latency, _ = network_simulator.simulate_communication(
                        node_id,
                        result['gradients'],
                        message_size_bytes=10000
                    )
                    
                    # Record metrics
                    network_monitor.record_communication(node_id, latency, success)
                    batch_controller.record_performance(node_id, batch_size, compute_time)
                    node_selector.record_contribution(
                        node_id,
                        compute_time=compute_time,
                        waiting_time=latency / 1000.0,
                        success=success
                    )
            
            # Post-round evaluation
            if round_losses:
                avg_loss = np.mean(round_losses)
                throughput = sum(32 for _ in round_losses) / sum(round_compute_times) if round_compute_times else 0
                
                metrics = {
                    'average_loss': avg_loss,
                    'throughput': throughput,
                    'nodes_participated': len(selected_nodes)
                }
                
                orchestrator.post_round_evaluation(round_num, metrics)
                
                print(f"  Avg Loss: {avg_loss:.4f}, Throughput: {throughput:.1f} samples/s")
        
        # Get final status
        status = orchestrator.get_orchestrator_status()
        perf_comparison = orchestrator.get_performance_comparison()
        
        print(f"\n✓ Adaptive training simulation complete!")
        print(f"  Total rounds: {status['current_round'] + 1}")
        print(f"  Adaptations applied: {status['adaptations_applied']}")
        print(f"  Phase: {status['phase']}")
        
        if perf_comparison.get('available'):
            print(f"\n  Performance Comparison:")
            print(f"    Warmup loss: {perf_comparison['warmup_phase']['average_loss']:.4f}")
            print(f"    Adaptive loss: {perf_comparison['adaptive_phase']['average_loss']:.4f}")
            print(f"    Improvement: {perf_comparison['improvements']['loss_improvement']:.2%}")
        
        # Cleanup
        orchestrator.shutdown()
        
        assert status['current_round'] >= num_rounds - 1
        assert status['adaptations_applied'] > 0


if __name__ == "__main__":
    print("=" * 80)
    print("Phase 3 & 4 Comprehensive Test Suite")
    print("=" * 80)
    pytest.main([__file__, "-v", "-s"])


