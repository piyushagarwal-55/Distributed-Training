"""
Core training coordinator components.
"""

# Make torch-dependent imports optional for API-only mode
try:
    from .coordinator import TrainingCoordinator
    from .data_shard import DataShardManager
    from .model_manager import ModelManager
    from .gradient_aggregator import GradientAggregator
    from .gpu_node import GPUNodeService
    from .network_simulator import NetworkSimulator, NetworkProfile
    from .metrics_collector import MetricsCollector
    from .network_monitor import NetworkQualityMonitor, ConnectionQuality
    from .adaptive_batch_controller import AdaptiveBatchController, BatchSizeStrategy
    from .node_selector import DynamicNodeSelector, SelectionStrategy
    from .adaptive_orchestrator import AdaptiveOrchestrator, AdaptationPolicy

    __all__ = [
        "TrainingCoordinator",
        "DataShardManager",
        "ModelManager",
        "GradientAggregator",
        "GPUNodeService",
        "NetworkSimulator",
        "NetworkProfile",
        "MetricsCollector",
        "NetworkQualityMonitor",
        "ConnectionQuality",
        "AdaptiveBatchController",
        "BatchSizeStrategy",
        "DynamicNodeSelector",
        "SelectionStrategy",
        "AdaptiveOrchestrator",
        "AdaptationPolicy",
    ]
except ImportError as e:
    # Torch not available, provide stub classes
    import warnings
    warnings.warn(f"PyTorch not available, ML features disabled: {e}")
    __all__ = []
