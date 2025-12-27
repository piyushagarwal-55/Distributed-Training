"""
Adaptive Batch Controller - Dynamically adjusts batch sizes based on network conditions.
"""

from typing import Dict, Optional
from dataclasses import dataclass
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class NodeBatchConfig:
    """Batch configuration for a node."""
    batch_size: int
    gradient_accumulation: int = 1
    effective_batch_size: int = 0
    
    def __post_init__(self):
        self.effective_batch_size = self.batch_size * self.gradient_accumulation


class AdaptiveBatchController:
    """Controls batch sizes adaptively based on network conditions."""
    
    MIN_BATCH_SIZE = 16
    MAX_BATCH_SIZE = 256
    
    def __init__(self, base_batch_size: int = 64):
        self.base_batch_size = base_batch_size
        self.node_configs: Dict[str, NodeBatchConfig] = {}
        self.node_latencies: Dict[str, float] = {}
        
        logger.info(f"[AdaptiveBatchController] Initialized with base batch size: {base_batch_size}")
    
    def register_node(self, node_id: str) -> NodeBatchConfig:
        """Register a node with default batch configuration."""
        config = NodeBatchConfig(batch_size=self.base_batch_size)
        self.node_configs[node_id] = config
        return config
    
    def update_network_metrics(self, node_id: str, latency_ms: float, packet_loss: float = 0.0):
        """Update network metrics for a node and adjust batch size."""
        self.node_latencies[node_id] = latency_ms
        
        if node_id not in self.node_configs:
            self.register_node(node_id)
        
        config = self.node_configs[node_id]
        
        # Adjust batch size based on latency
        if latency_ms > 200:  # High latency
            new_batch = min(config.batch_size * 2, self.MAX_BATCH_SIZE)
        elif latency_ms > 100:  # Medium latency
            new_batch = min(config.batch_size + 16, self.MAX_BATCH_SIZE)
        elif latency_ms < 30:  # Low latency
            new_batch = max(config.batch_size - 16, self.MIN_BATCH_SIZE)
        else:
            new_batch = config.batch_size
        
        # Adjust for packet loss
        if packet_loss > 0.05:
            new_batch = min(new_batch * 2, self.MAX_BATCH_SIZE)
        
        if new_batch != config.batch_size:
            logger.info(f"[AdaptiveBatchController] Node {node_id}: batch {config.batch_size} -> {new_batch}")
            config.batch_size = new_batch
            config.effective_batch_size = new_batch * config.gradient_accumulation
    
    def get_batch_size(self, node_id: str) -> int:
        """Get current batch size for a node."""
        if node_id not in self.node_configs:
            self.register_node(node_id)
        return self.node_configs[node_id].batch_size
    
    def get_all_configs(self) -> Dict[str, NodeBatchConfig]:
        """Get all node configurations."""
        return self.node_configs.copy()
