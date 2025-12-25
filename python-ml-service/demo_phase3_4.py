"""
Demo Script for Phase 3 & 4: Adaptive Distributed Training

This script demonstrates the complete adaptive training system including:
- GPU Node Simulation
- Network Condition Simulation
- Metrics Collection
- Network Quality Monitoring
- Adaptive Batch Size Control
- Dynamic Node Selection
- Adaptive Training Orchestration
"""

import sys
import time
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.models.config import SystemConfig, TrainingConfig
from src.core.gpu_node import GPUNodeService
from src.core.network_simulator import NetworkSimulator, NetworkProfile
from src.core.metrics_collector import MetricsCollector
from src.core.network_monitor import NetworkQualityMonitor
from src.core.adaptive_batch_controller import AdaptiveBatchController, BatchSizeStrategy
from src.core.node_selector import DynamicNodeSelector, SelectionStrategy
from src.core.adaptive_orchestrator import AdaptiveOrchestrator, AdaptationPolicy
from src.core.model_manager import ModelManager
from src.utils.logger import setup_logger, get_logger

# Setup logging
setup_logger(log_level="INFO")
logger = get_logger(__name__)


def create_dummy_dataset(num_samples: int = 500):
    """Create dummy MNIST-like dataset for demo."""
    print("\n[DEMO] Creating dummy dataset...")
    X = torch.randn(num_samples, 1, 28, 28)
    y = torch.randint(0, 10, (num_samples,))
    dataset = TensorDataset(X, y)
    print(f"[DEMO] ✓ Created dataset with {num_samples} samples")
    return dataset


def setup_training_config():
    """Create training configuration."""
    print("\n[DEMO] Setting up training configuration...")
    config = SystemConfig(
        training=TrainingConfig(
            model_architecture="simple_cnn",
            dataset="mnist",
            batch_size=32,
            epochs=3,
            learning_rate=0.01,
            steps_per_epoch=20
        )
    )
    print("[DEMO] ✓ Configuration ready")
    return config


def create_gpu_nodes(config: SystemConfig, num_nodes: int = 5):
    """Create simulated GPU nodes with varying specifications."""
    print(f"\n[DEMO] Creating {num_nodes} simulated GPU nodes...")
    
    nodes = []
    node_specs = [
        {'name': 'High-End GPU', 'memory': 16.0, 'compute': 1.5},
        {'name': 'Mid-Range GPU', 'memory': 8.0, 'compute': 1.0},
        {'name': 'Budget GPU', 'memory': 4.0, 'compute': 0.7},
        {'name': 'Entry-Level GPU', 'memory': 4.0, 'compute': 0.5},
        {'name': 'Integrated GPU', 'memory': 2.0, 'compute': 0.3},
    ]
    
    for i in range(num_nodes):
        spec = node_specs[i % len(node_specs)]
        node_id = f"node_{i}"
        
        gpu_specs = {
            'gpu_model': spec['name'],
            'gpu_memory_gb': spec['memory'],
            'compute_capability': spec['compute']
        }
        
        node = GPUNodeService(
            node_id,
            gpu_specs,
            config,
            simulated_delay_factor=0.01  # Fast simulation
        )
        
        nodes.append((node_id, node))
        
        print(f"[DEMO]   Node {i}: {spec['name']} "
              f"({spec['memory']}GB, {spec['compute']}x compute)")
    
    print("[DEMO] ✓ All nodes created")
    return nodes


def setup_network_profiles(network_simulator: NetworkSimulator, nodes: list):
    """Setup network profiles for nodes to simulate different conditions."""
    print("\n[DEMO] Setting up network profiles...")
    
    profiles = [
        (NetworkProfile.PERFECT, "Perfect (Data Center)"),
        (NetworkProfile.GOOD, "Good (Office Network)"),
        (NetworkProfile.AVERAGE, "Average (Home Network)"),
        (NetworkProfile.POOR, "Poor (Mobile Hotspot)"),
        (NetworkProfile.UNSTABLE, "Unstable (Congested)"),
    ]
    
    for i, (node_id, _) in enumerate(nodes):
        profile, description = profiles[i % len(profiles)]
        network_simulator.set_node_profile(node_id, profile.value)
        print(f"[DEMO]   {node_id}: {description}")
    
    print("[DEMO] ✓ Network profiles configured")


def initialize_adaptive_system(config: SystemConfig, nodes: list):
    """Initialize all adaptive components."""
    print("\n[DEMO] Initializing adaptive training system...")
    
    # Create network simulator
    print("[DEMO]   Creating network simulator...")
    network_simulator = NetworkSimulator(default_profile="average")
    setup_network_profiles(network_simulator, nodes)
    
    # Create network monitor
    print("[DEMO]   Creating network quality monitor...")
    network_monitor = NetworkQualityMonitor(update_interval_seconds=5.0)
    
    # Create batch controller
    print("[DEMO]   Creating adaptive batch controller...")
    batch_controller = AdaptiveBatchController(
        network_monitor,
        baseline_batch_size=32,
        min_batch_size=16,
        max_batch_size=128,
        strategy=BatchSizeStrategy.HYBRID
    )
    
    # Create node selector
    print("[DEMO]   Creating dynamic node selector...")
    node_selector = DynamicNodeSelector(
        network_monitor,
        strategy=SelectionStrategy.ADAPTIVE_THRESHOLD,
        enable_quarantine=True
    )
    
    # Create orchestrator
    print("[DEMO]   Creating adaptive orchestrator...")
    orchestrator = AdaptiveOrchestrator(
        config,
        network_monitor,
        batch_controller,
        node_selector,
        adaptation_policy=AdaptationPolicy.REACTIVE,
        adaptation_interval=3,
        warmup_rounds=5
    )
    
    # Register all nodes
    print("[DEMO]   Registering nodes with adaptive components...")
    for node_id, _ in nodes:
        network_monitor.register_node(node_id)
        batch_controller.register_node(node_id)
        node_selector.register_node(node_id)
    
    print("[DEMO] ✓ Adaptive system initialized")
    
    return network_simulator, network_monitor, batch_controller, node_selector, orchestrator


def initialize_nodes_with_data(nodes: list, dataset, config: SystemConfig):
    """Initialize nodes with model parameters and data shards."""
    print("\n[DEMO] Initializing nodes with model and data...")
    
    # Create model
    model_manager = ModelManager(config.training.model_architecture)
    model_manager.initialize_model()
    model_params = model_manager.get_parameters()
    
    print(f"[DEMO]   Model parameters: {len(model_params)} tensors")
    
    # Distribute data to nodes
    samples_per_node = len(dataset) // len(nodes)
    
    for i, (node_id, node) in enumerate(nodes):
        # Create data shard
        start_idx = i * samples_per_node
        end_idx = start_idx + samples_per_node if i < len(nodes) - 1 else len(dataset)
        
        shard_indices = list(range(start_idx, end_idx))
        shard_dataset = torch.utils.data.Subset(dataset, shard_indices)
        shard_loader = DataLoader(shard_dataset, batch_size=32, shuffle=True)
        
        # Initialize node
        success = node.initialize(model_params, shard_loader, data_shard_id=i)
        
        if success:
            print(f"[DEMO]   {node_id}: ✓ Initialized with {len(shard_dataset)} samples")
        else:
            print(f"[DEMO]   {node_id}: ✗ Initialization failed")
    
    print("[DEMO] ✓ All nodes initialized with data")
    
    return model_manager


def inject_network_events(network_simulator: NetworkSimulator, nodes: list, round_num: int):
    """Inject network events at specific rounds to simulate real-world conditions."""
    
    # At round 10, inject latency spike on a node
    if round_num == 10:
        target_node = nodes[1][0]
        print(f"\n[DEMO EVENT] Injecting latency spike on {target_node}")
        network_simulator.inject_latency_spike(target_node, duration_seconds=2.0)
    
    # At round 15, degrade a node's network
    if round_num == 15:
        target_node = nodes[2][0]
        print(f"\n[DEMO EVENT] Degrading network quality for {target_node}")
        network_simulator.set_node_profile(target_node, NetworkProfile.POOR.value)
    
    # At round 20, improve a node's network
    if round_num == 20:
        target_node = nodes[4][0]
        print(f"\n[DEMO EVENT] Improving network quality for {target_node}")
        network_simulator.set_node_profile(target_node, NetworkProfile.GOOD.value)


def run_training_round(
    round_num: int,
    nodes: list,
    network_simulator: NetworkSimulator,
    network_monitor: NetworkQualityMonitor,
    batch_controller: AdaptiveBatchController,
    node_selector: DynamicNodeSelector,
    orchestrator: AdaptiveOrchestrator,
    model_manager: ModelManager
):
    """Execute one training round."""
    
    # Inject network events
    inject_network_events(network_simulator, nodes, round_num)
    
    # Pre-round adaptation
    available_nodes = [node_id for node_id, _ in nodes]
    decisions = orchestrator.pre_round_adaptation(available_nodes, round_num)
    
    selected_nodes = decisions['selected_nodes']
    batch_sizes = decisions['batch_sizes']
    
    # Training on selected nodes
    round_losses = []
    round_compute_times = []
    round_gradients = []
    
    for node_id in selected_nodes:
        # Find node
        node = next(n for nid, n in nodes if nid == node_id)
        
        # Update batch size if changed
        new_batch_size = batch_sizes[node_id]
        if new_batch_size != node.current_batch_size:
            node.update_batch_size(new_batch_size)
        
        # Execute training step
        result = node.train_step()
        
        if result is None:
            continue
        
        # Extract metrics
        loss = result['metrics']['loss']
        compute_time = result['metrics']['step_time']
        gradients = result['gradients']
        
        round_losses.append(loss)
        round_compute_times.append(compute_time)
        round_gradients.append((node_id, gradients))
        
        # Simulate network communication
        gradient_size_bytes = sum(g.nbytes for g in gradients.values())
        
        success, latency, _ = network_simulator.simulate_communication(
            node_id,
            gradients,
            message_size_bytes=gradient_size_bytes
        )
        
        # Record with monitor
        network_monitor.record_communication(node_id, latency, success)
        
        # Record performance
        batch_controller.record_performance(node_id, new_batch_size, compute_time)
        
        # Record contribution
        node_selector.record_contribution(
            node_id,
            compute_time=compute_time,
            waiting_time=latency / 1000.0,
            success=success
        )
    
    # Aggregate gradients
    if round_gradients:
        aggregated_grads = {}
        for param_name in round_gradients[0][1].keys():
            grads = [g[param_name] for _, g in round_gradients]
            aggregated_grads[param_name] = np.mean(grads, axis=0)
        
        # Apply gradients (simplified, just for demo)
        # In real system, this would update the model
    
    # Calculate round metrics
    if round_losses:
        avg_loss = np.mean(round_losses)
        total_samples = len(selected_nodes) * 32  # Approximate
        total_time = sum(round_compute_times)
        throughput = total_samples / total_time if total_time > 0 else 0
        
        round_metrics = {
            'average_loss': avg_loss,
            'throughput': throughput,
            'nodes_participated': len(selected_nodes)
        }
        
        # Post-round evaluation
        orchestrator.post_round_evaluation(round_num, round_metrics)
        
        return round_metrics
    
    return None


def print_system_status(
    round_num: int,
    round_metrics: dict,
    network_monitor: NetworkQualityMonitor,
    batch_controller: AdaptiveBatchController,
    node_selector: DynamicNodeSelector
):
    """Print current system status."""
    
    if round_num % 5 == 0 or round_num == 1:  # Print detailed status every 5 rounds
        print(f"\n{'=' * 80}")
        print(f"ROUND {round_num} STATUS")
        print(f"{'=' * 80}")
        
        if round_metrics:
            print(f"\nTraining Metrics:")
            print(f"  Average Loss: {round_metrics['average_loss']:.4f}")
            print(f"  Throughput: {round_metrics['throughput']:.1f} samples/sec")
            print(f"  Nodes Participated: {round_metrics['nodes_participated']}")
        
        # Network health
        health = network_monitor.get_cluster_health_summary()
        print(f"\nNetwork Health:")
        print(f"  Total Nodes: {health['total_nodes']}")
        print(f"  Healthy: {health['healthy_nodes']}")
        print(f"  Problematic: {health['problematic_nodes']}")
        print(f"  Avg Latency: {health['average_latency_ms']:.1f}ms")
        
        # Batch sizes
        batch_summary = batch_controller.get_adaptation_summary()
        if batch_summary.get('nodes_tracked', 0) > 0:
            print(f"\nBatch Size Adaptation:")
            bs_stats = batch_summary['batch_size_stats']
            print(f"  Range: [{bs_stats['min']}, {bs_stats['max']}]")
            print(f"  Mean: {bs_stats['mean']:.1f}")
            print(f"  Adaptations: {batch_summary['adaptation_count']}")
        
        # Node selection
        selection_summary = node_selector.get_selection_summary()
        if selection_summary.get('total_nodes', 0) > 0:
            print(f"\nNode Selection:")
            print(f"  Active: {selection_summary['active_nodes']}")
            print(f"  Quarantined: {selection_summary['quarantined_nodes']}")
            print(f"  Selection Rate: {selection_summary['average_selection_rate']:.2%}")
        
        print(f"{'=' * 80}\n")


def print_final_report(
    orchestrator: AdaptiveOrchestrator,
    network_monitor: NetworkQualityMonitor,
    network_simulator: NetworkSimulator
):
    """Print final training report."""
    
    print("\n" + "=" * 80)
    print("FINAL TRAINING REPORT")
    print("=" * 80)
    
    # Orchestrator status
    status = orchestrator.get_orchestrator_status()
    print(f"\nOrchestrator Summary:")
    print(f"  Total Rounds: {status['current_round'] + 1}")
    print(f"  Training Phase: {status['phase']}")
    print(f"  Adaptations Applied: {status['adaptations_applied']}")
    print(f"  Adaptations Rolled Back: {status['adaptations_rolled_back']}")
    
    # Performance comparison
    perf_comp = orchestrator.get_performance_comparison()
    if perf_comp.get('available'):
        print(f"\nPerformance Comparison:")
        print(f"  Warmup Phase:")
        print(f"    Avg Loss: {perf_comp['warmup_phase']['average_loss']:.4f}")
        print(f"    Avg Throughput: {perf_comp['warmup_phase']['average_throughput']:.1f} samples/s")
        
        print(f"  Adaptive Phase:")
        print(f"    Avg Loss: {perf_comp['adaptive_phase']['average_loss']:.4f}")
        print(f"    Avg Throughput: {perf_comp['adaptive_phase']['average_throughput']:.1f} samples/s")
        
        print(f"  Improvements:")
        loss_imp = perf_comp['improvements']['loss_improvement']
        throughput_imp = perf_comp['improvements']['throughput_improvement']
        print(f"    Loss: {loss_imp:+.2%}")
        print(f"    Throughput: {throughput_imp:+.2%}")
    
    # Network statistics
    net_metrics = network_simulator.get_metrics()
    print(f"\nNetwork Simulation Statistics:")
    print(f"  Total Messages: {net_metrics['total_messages']}")
    print(f"  Dropped Messages: {net_metrics['dropped_messages']}")
    print(f"  Drop Rate: {net_metrics['drop_rate']:.2%}")
    print(f"  Avg Latency: {net_metrics['average_latency_ms']:.1f}ms")
    print(f"  Total Retries: {net_metrics['total_retries']}")
    
    print("\n" + "=" * 80)
    print("Demo completed successfully!")
    print("=" * 80 + "\n")


def main():
    """Main demo function."""
    
    print("\n" + "=" * 80)
    print("Phase 3 & 4: Adaptive Distributed Training Demo")
    print("=" * 80)
    
    # Setup
    config = setup_training_config()
    dataset = create_dummy_dataset(num_samples=500)
    nodes = create_gpu_nodes(config, num_nodes=5)
    
    # Initialize adaptive system
    network_simulator, network_monitor, batch_controller, node_selector, orchestrator = \
        initialize_adaptive_system(config, nodes)
    
    # Initialize nodes with data
    model_manager = initialize_nodes_with_data(nodes, dataset, config)
    
    # Start training
    print("\n" + "=" * 80)
    print("STARTING ADAPTIVE TRAINING")
    print("=" * 80)
    
    orchestrator.start_training()
    
    # Run training rounds
    num_rounds = 25
    
    for round_num in range(num_rounds):
        round_metrics = run_training_round(
            round_num,
            nodes,
            network_simulator,
            network_monitor,
            batch_controller,
            node_selector,
            orchestrator,
            model_manager
        )
        
        # Print status
        if round_metrics:
            print_system_status(
                round_num,
                round_metrics,
                network_monitor,
                batch_controller,
                node_selector
            )
        
        # Small delay for readability
        time.sleep(0.1)
    
    # Print final report
    print_final_report(orchestrator, network_monitor, network_simulator)
    
    # Cleanup
    orchestrator.shutdown()
    
    print("[DEMO] ✓ Demo completed successfully!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[DEMO] Interrupted by user")
    except Exception as e:
        print(f"\n\n[DEMO] Error: {e}")
        import traceback
        traceback.print_exc()
