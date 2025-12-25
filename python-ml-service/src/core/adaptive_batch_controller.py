"""
Adaptive Batch Size Controller - Dynamically adjusts batch sizes based on network conditions.

This module implements intelligent batch size adaptation to optimize training
efficiency under varying network conditions.
"""

import time
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime
import numpy as np

from ..utils.logger import get_logger
from .network_monitor import NetworkQualityMonitor, ConnectionQuality

logger = get_logger(__name__)


class BatchSizeStrategy(str):
    """Batch size adaptation strategies."""
    FIXED = "fixed"  # No adaptation
    LATENCY_BASED = "latency_based"  # Adapt based on latency
    THROUGHPUT_BASED = "throughput_based"  # Adapt based on throughput
    HYBRID = "hybrid"  # Combined strategy


class AdaptiveBatchController:
    """
    Controls batch sizes for nodes based on their network conditions.
    
    Adapts batch sizes to balance communication overhead with convergence speed.
    High latency nodes get larger batches to reduce communication frequency.
    Low latency nodes get smaller batches for more frequent updates.
    """
    
    def __init__(
        self,
        network_monitor: NetworkQualityMonitor,
        baseline_batch_size: int = 64,
        min_batch_size: int = 16,
        max_batch_size: int = 256,
        strategy: str = BatchSizeStrategy.HYBRID,
        adaptation_interval: float = 30.0,
        use_power_of_two: bool = True
    ):
        """
        Initialize adaptive batch controller.
        
        Args:
            network_monitor: NetworkQualityMonitor instance
            baseline_batch_size: Starting batch size for all nodes
            min_batch_size: Minimum allowed batch size
            max_batch_size: Maximum allowed batch size
            strategy: Adaptation strategy to use
            adaptation_interval: How often to evaluate and adapt (seconds)
            use_power_of_two: Constrain batch sizes to powers of 2
        """
        self.network_monitor = network_monitor
        self.baseline_batch_size = baseline_batch_size
        self.min_batch_size = min_batch_size
        self.max_batch_size = max_batch_size
        self.strategy = strategy
        self.adaptation_interval = adaptation_interval
        self.use_power_of_two = use_power_of_two
        
        # Current batch sizes for each node
        self.node_batch_sizes: Dict[str, int] = {}
        
        # Batch size history for tracking changes
        self.batch_size_history: Dict[str, List[Dict[str, Any]]] = {}
        
        # Performance tracking
        self.node_performance: Dict[str, Dict[str, Any]] = {}
        
        # Adaptation state
        self.last_adaptation_time = time.time()
        self.adaptation_count = 0
        
        # Thread safety
        self.lock = threading.RLock()
        
        logger.info(f"[BATCH CTRL] AdaptiveBatchController initialized: "
                   f"baseline={baseline_batch_size}, range=[{min_batch_size}, {max_batch_size}], "
                   f"strategy={strategy}")
        print(f"[BATCH CTRL] Adaptive batch control initialized (strategy: {strategy})")
    
    def register_node(self, node_id: str, initial_batch_size: Optional[int] = None):
        """
        Register a node with the controller.
        
        Args:
            node_id: Node identifier
            initial_batch_size: Optional initial batch size (uses baseline if not specified)
        """
        with self.lock:
            batch_size = initial_batch_size or self.baseline_batch_size
            batch_size = self._constrain_batch_size(batch_size)
            
            self.node_batch_sizes[node_id] = batch_size
            self.batch_size_history[node_id] = [{
                'batch_size': batch_size,
                'timestamp': time.time(),
                'reason': 'initial'
            }]
            self.node_performance[node_id] = {
                'total_samples_processed': 0,
                'total_time_spent': 0.0,
                'throughput_history': []
            }
            
            logger.info(f"[BATCH CTRL] Registered node {node_id} with batch size {batch_size}")
            print(f"[BATCH CTRL] Node {node_id}: Initial batch size = {batch_size}")
    
    def get_batch_size(self, node_id: str) -> int:
        """
        Get current batch size for a node.
        
        Args:
            node_id: Node identifier
            
        Returns:
            Current batch size
        """
        with self.lock:
            return self.node_batch_sizes.get(node_id, self.baseline_batch_size)
    
    def set_batch_size(self, node_id: str, new_batch_size: int, reason: str = "manual"):
        """
        Manually set batch size for a node.
        
        Args:
            node_id: Node identifier
            new_batch_size: New batch size to set
            reason: Reason for change
        """
        with self.lock:
            new_batch_size = self._constrain_batch_size(new_batch_size)
            old_batch_size = self.node_batch_sizes.get(node_id, self.baseline_batch_size)
            
            if old_batch_size != new_batch_size:
                self.node_batch_sizes[node_id] = new_batch_size
                
                if node_id not in self.batch_size_history:
                    self.batch_size_history[node_id] = []
                
                self.batch_size_history[node_id].append({
                    'batch_size': new_batch_size,
                    'timestamp': time.time(),
                    'reason': reason,
                    'old_batch_size': old_batch_size
                })
                
                logger.info(f"[BATCH CTRL] Node {node_id}: Batch size {old_batch_size} -> {new_batch_size} ({reason})")
                print(f"[BATCH CTRL] Node {node_id}: Batch size updated to {new_batch_size}")
    
    def record_performance(
        self,
        node_id: str,
        samples_processed: int,
        time_spent: float
    ):
        """
        Record performance metrics for a node.
        
        Args:
            node_id: Node identifier
            samples_processed: Number of samples processed in this period
            time_spent: Time spent in seconds
        """
        with self.lock:
            if node_id not in self.node_performance:
                self.node_performance[node_id] = {
                    'total_samples_processed': 0,
                    'total_time_spent': 0.0,
                    'throughput_history': []
                }
            
            perf = self.node_performance[node_id]
            perf['total_samples_processed'] += samples_processed
            perf['total_time_spent'] += time_spent
            
            # Calculate throughput (samples/second)
            if time_spent > 0:
                throughput = samples_processed / time_spent
                perf['throughput_history'].append({
                    'throughput': throughput,
                    'batch_size': self.node_batch_sizes.get(node_id, self.baseline_batch_size),
                    'timestamp': time.time()
                })
                
                # Keep only recent history
                if len(perf['throughput_history']) > 50:
                    perf['throughput_history'] = perf['throughput_history'][-50:]
    
    def evaluate_and_adapt(self) -> Dict[str, int]:
        """
        Evaluate all nodes and adapt batch sizes as needed.
        
        Returns:
            Dictionary of node_id -> new_batch_size for nodes that changed
        """
        with self.lock:
            if time.time() - self.last_adaptation_time < self.adaptation_interval:
                return {}  # Not time to adapt yet
            
            logger.info("[BATCH CTRL] Evaluating batch sizes for adaptation...")
            print("[BATCH CTRL] Running batch size adaptation...")
            
            changes = {}
            
            for node_id in self.node_batch_sizes.keys():
                new_batch_size = self._calculate_optimal_batch_size(node_id)
                current_batch_size = self.node_batch_sizes[node_id]
                
                if new_batch_size != current_batch_size:
                    self.set_batch_size(node_id, new_batch_size, reason=f"adaptation_{self.strategy}")
                    changes[node_id] = new_batch_size
            
            self.last_adaptation_time = time.time()
            self.adaptation_count += 1
            
            if changes:
                logger.info(f"[BATCH CTRL] Adapted batch sizes for {len(changes)} nodes")
                print(f"[BATCH CTRL] ✓ Adapted {len(changes)} nodes")
            else:
                logger.debug("[BATCH CTRL] No batch size changes needed")
            
            return changes
    
    def _calculate_optimal_batch_size(self, node_id: str) -> int:
        """
        Calculate optimal batch size for a node based on strategy.
        
        Args:
            node_id: Node identifier
            
        Returns:
            Optimal batch size
        """
        if self.strategy == BatchSizeStrategy.FIXED:
            return self.baseline_batch_size
        
        elif self.strategy == BatchSizeStrategy.LATENCY_BASED:
            return self._latency_based_batch_size(node_id)
        
        elif self.strategy == BatchSizeStrategy.THROUGHPUT_BASED:
            return self._throughput_based_batch_size(node_id)
        
        elif self.strategy == BatchSizeStrategy.HYBRID:
            return self._hybrid_batch_size(node_id)
        
        else:
            logger.warning(f"[BATCH CTRL] Unknown strategy '{self.strategy}', using baseline")
            return self.baseline_batch_size
    
    def _latency_based_batch_size(self, node_id: str) -> int:
        """
        Calculate batch size based on network latency.
        
        High latency -> larger batch size (reduce communication frequency)
        Low latency -> smaller batch size (more frequent updates)
        """
        profile = self.network_monitor.get_node_profile(node_id)
        
        if profile is None:
            return self.baseline_batch_size
        
        latency_ms = profile['latency_ms']
        quality = profile['quality']
        
        # Quality-based multipliers
        quality_multipliers = {
            'excellent': 0.75,  # Can afford smaller batches
            'good': 1.0,        # Baseline
            'fair': 1.5,        # Increase batch size
            'poor': 2.0,        # Significantly increase
            'critical': 2.5,    # Maximum increase
            'offline': 1.0      # Fallback to baseline
        }
        
        multiplier = quality_multipliers.get(quality, 1.0)
        
        # Also consider absolute latency
        if latency_ms < 50:
            multiplier *= 0.8
        elif latency_ms > 200:
            multiplier *= 1.5
        
        new_batch_size = int(self.baseline_batch_size * multiplier)
        return self._constrain_batch_size(new_batch_size)
    
    def _throughput_based_batch_size(self, node_id: str) -> int:
        """
        Calculate batch size based on observed throughput.
        
        If increasing batch size improved throughput, continue increasing.
        If it degraded throughput, decrease.
        """
        perf = self.node_performance.get(node_id)
        
        if perf is None or len(perf['throughput_history']) < 3:
            return self.baseline_batch_size
        
        # Analyze recent throughput trend
        recent_throughputs = [
            t['throughput'] for t in perf['throughput_history'][-10:]
        ]
        recent_batch_sizes = [
            t['batch_size'] for t in perf['throughput_history'][-10:]
        ]
        
        # Calculate correlation between batch size and throughput
        if len(recent_throughputs) >= 5:
            current_throughput = np.mean(recent_throughputs[-3:])
            older_throughput = np.mean(recent_throughputs[-6:-3]) if len(recent_throughputs) >= 6 else current_throughput
            
            current_batch_size = self.node_batch_sizes[node_id]
            
            # If throughput improved, try to continue in that direction
            if current_throughput > older_throughput * 1.05:  # 5% improvement
                # Throughput improved, try slightly larger batch
                new_batch_size = int(current_batch_size * 1.25)
            elif current_throughput < older_throughput * 0.95:  # 5% degradation
                # Throughput degraded, try smaller batch
                new_batch_size = int(current_batch_size * 0.8)
            else:
                # Stable, keep current
                new_batch_size = current_batch_size
            
            return self._constrain_batch_size(new_batch_size)
        
        return self.baseline_batch_size
    
    def _hybrid_batch_size(self, node_id: str) -> int:
        """
        Calculate batch size using hybrid approach (latency + throughput).
        
        Combines network-aware and performance-aware adaptation.
        """
        # Get both recommendations
        latency_batch = self._latency_based_batch_size(node_id)
        throughput_batch = self._throughput_based_batch_size(node_id)
        
        # Weight them (60% latency, 40% throughput)
        hybrid_batch = int(0.6 * latency_batch + 0.4 * throughput_batch)
        
        return self._constrain_batch_size(hybrid_batch)
    
    def _constrain_batch_size(self, batch_size: int) -> int:
        """
        Constrain batch size to valid range and optionally to power of 2.
        
        Args:
            batch_size: Proposed batch size
            
        Returns:
            Constrained batch size
        """
        # Apply min/max constraints
        batch_size = max(self.min_batch_size, min(self.max_batch_size, batch_size))
        
        # Optionally round to nearest power of 2
        if self.use_power_of_two:
            power = int(np.log2(batch_size))
            lower = 2 ** power
            upper = 2 ** (power + 1)
            
            # Choose closer power of 2
            if batch_size - lower < upper - batch_size:
                batch_size = lower
            else:
                batch_size = upper
            
            # Re-apply constraints after rounding
            batch_size = max(self.min_batch_size, min(self.max_batch_size, batch_size))
        
        return batch_size
    
    def get_adaptation_summary(self) -> Dict[str, Any]:
        """
        Get summary of adaptation activity.
        
        Returns:
            Dictionary with adaptation statistics
        """
        with self.lock:
            if not self.node_batch_sizes:
                return {
                    'nodes_tracked': 0,
                    'message': 'No nodes registered'
                }
            
            batch_sizes = list(self.node_batch_sizes.values())
            
            return {
                'nodes_tracked': len(self.node_batch_sizes),
                'adaptation_count': self.adaptation_count,
                'strategy': self.strategy,
                'batch_size_stats': {
                    'min': min(batch_sizes),
                    'max': max(batch_sizes),
                    'mean': float(np.mean(batch_sizes)),
                    'median': float(np.median(batch_sizes))
                },
                'nodes_at_baseline': sum(
                    1 for bs in batch_sizes if bs == self.baseline_batch_size
                ),
                'nodes_above_baseline': sum(
                    1 for bs in batch_sizes if bs > self.baseline_batch_size
                ),
                'nodes_below_baseline': sum(
                    1 for bs in batch_sizes if bs < self.baseline_batch_size
                ),
                'last_adaptation': datetime.fromtimestamp(self.last_adaptation_time).isoformat(),
                'time_since_adaptation': time.time() - self.last_adaptation_time
            }
    
    def get_node_batch_history(self, node_id: str) -> List[Dict[str, Any]]:
        """
        Get batch size history for a node.
        
        Args:
            node_id: Node identifier
            
        Returns:
            List of batch size change events
        """
        with self.lock:
            return self.batch_size_history.get(node_id, []).copy()
    
    def get_all_batch_sizes(self) -> Dict[str, int]:
        """Get current batch sizes for all nodes."""
        with self.lock:
            return self.node_batch_sizes.copy()
    
    def reset_adaptation_history(self):
        """Reset adaptation history and counters."""
        with self.lock:
            self.adaptation_count = 0
            self.last_adaptation_time = time.time()
            
            # Reset all nodes to baseline
            for node_id in self.node_batch_sizes.keys():
                self.set_batch_size(node_id, self.baseline_batch_size, reason="reset")
            
            logger.info("[BATCH CTRL] Adaptation history reset")
            print("[BATCH CTRL] Adaptation history reset")
    
    def compare_strategies(self, node_id: str) -> Dict[str, int]:
        """
        Compare recommendations from different strategies for a node.
        
        Args:
            node_id: Node identifier
            
        Returns:
            Dictionary mapping strategy name to recommended batch size
        """
        return {
            'fixed': self.baseline_batch_size,
            'latency_based': self._latency_based_batch_size(node_id),
            'throughput_based': self._throughput_based_batch_size(node_id),
            'hybrid': self._hybrid_batch_size(node_id),
            'current': self.get_batch_size(node_id)
        }
    
    def export_metrics(self) -> Dict[str, Any]:
        """
        Export all controller metrics.
        
        Returns:
            Dictionary with complete controller state
        """
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'configuration': {
                'baseline_batch_size': self.baseline_batch_size,
                'min_batch_size': self.min_batch_size,
                'max_batch_size': self.max_batch_size,
                'strategy': self.strategy,
                'adaptation_interval': self.adaptation_interval
            },
            'current_state': {
                'batch_sizes': self.get_all_batch_sizes(),
                'adaptation_summary': self.get_adaptation_summary()
            },
            'performance': self.node_performance
        }
