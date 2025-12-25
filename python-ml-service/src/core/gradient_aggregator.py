"""
Gradient Aggregation Engine.

Implements the core gradient aggregation logic that combines updates from multiple nodes.
Supports various aggregation strategies including simple averaging, weighted averaging,
gradient clipping, and handling of stale gradients.
"""

import time
import threading
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np

from ..models.config import AggregationStrategy
from ..models.metrics import GradientUpdate
from ..utils.logger import get_logger

logger = get_logger(__name__)


class GradientAggregator:
    """
    Aggregates gradients from multiple nodes for distributed training.
    
    Features:
    - Multiple aggregation strategies (simple average, weighted average)
    - Gradient validation and clipping
    - Synchronous and asynchronous aggregation modes
    - Timeout handling for straggler nodes
    - Performance metrics tracking
    """
    
    def __init__(
        self,
        strategy: AggregationStrategy = AggregationStrategy.SIMPLE_AVERAGE,
        timeout_seconds: float = 30.0,
        min_nodes_percentage: float = 0.8,
        gradient_clip_value: Optional[float] = None,
        max_stale_rounds: int = 2
    ):
        """
        Initialize the gradient aggregator.
        
        Args:
            strategy: Aggregation strategy to use
            timeout_seconds: Timeout for waiting for gradients
            min_nodes_percentage: Minimum % of nodes required before timeout
            gradient_clip_value: Maximum gradient norm (None to disable)
            max_stale_rounds: Maximum age of stale gradients to accept
        """
        self.strategy = strategy
        self.timeout_seconds = timeout_seconds
        self.min_nodes_percentage = min_nodes_percentage
        self.gradient_clip_value = gradient_clip_value
        self.max_stale_rounds = max_stale_rounds
        
        # Current round state
        self.current_round = 0
        self.expected_nodes: List[str] = []
        self.received_gradients: Dict[str, GradientUpdate] = {}
        self.gradient_metadata: Dict[str, Dict[str, Any]] = {}  # Store metadata per node
        self.round_start_time: Optional[datetime] = None
        
        # Historical data
        self.gradient_history: List[Dict[str, Any]] = []
        self.node_weights: Dict[str, float] = {}
        
        # Performance metrics
        self.aggregation_times: List[float] = []
        self.wait_times: List[float] = []
        self.rejected_gradients: int = 0
        
        # Thread safety
        self.lock = threading.RLock()
        
        logger.info(
            f"GradientAggregator initialized: strategy={strategy.value}, "
            f"timeout={timeout_seconds}s, clip={gradient_clip_value}"
        )
    
    def start_round(self, round_number: int, expected_node_ids: List[str]) -> None:
        """
        Start a new aggregation round.
        
        Args:
            round_number: Round number
            expected_node_ids: List of node IDs expected to submit gradients
        """
        with self.lock:
            self.current_round = round_number
            self.expected_nodes = expected_node_ids.copy()
            self.received_gradients = {}
            self.gradient_metadata = {}
            self.round_start_time = datetime.now()
            
            logger.info(
                f"Round {round_number} started: expecting {len(expected_node_ids)} nodes"
            )
    
    def receive_gradient(
        self,
        node_id: str,
        gradients: Dict[str, np.ndarray],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Receive gradient from a node.
        
        Args:
            node_id: ID of the node submitting gradient
            gradients: Dict mapping parameter names to gradient arrays
            metadata: Optional metadata (compute time, data size, etc.)
            
        Returns:
            bool: True if gradient accepted, False if rejected
        """
        with self.lock:
            try:
                # Check if node is expected
                if node_id not in self.expected_nodes:
                    logger.warning(
                        f"Unexpected gradient from node {node_id} in round {self.current_round}"
                    )
                    self.rejected_gradients += 1
                    return False
                
                # Check if already received
                if node_id in self.received_gradients:
                    logger.warning(
                        f"Duplicate gradient from node {node_id} in round {self.current_round}"
                    )
                    self.rejected_gradients += 1
                    return False
                
                # Validate gradients
                if not self._validate_gradients(gradients, node_id):
                    logger.error(f"Invalid gradients from node {node_id}")
                    self.rejected_gradients += 1
                    return False
                
                # Clip individual gradients if configured (for privacy/security)
                if self.gradient_clip_value is not None:
                    gradients = self._clip_gradients(gradients)
                
                # Store gradients and metadata
                self.received_gradients[node_id] = gradients
                if metadata:
                    self.gradient_metadata[node_id] = metadata
                
                grad_norm = self._compute_gradient_norm(gradients)
                logger.info(
                    f"Gradient received from {node_id}: "
                    f"norm={grad_norm:.4f}, "
                    f"received={len(self.received_gradients)}/{len(self.expected_nodes)}"
                )
                
                return True
                
            except Exception as e:
                logger.error(
                    f"Error receiving gradient from node_id {node_id}: {str(e)}",
                    exc_info=True
                )
                self.rejected_gradients += 1
                return False
    
    def should_aggregate(self) -> Tuple[bool, str]:
        """
        Check if aggregation should proceed.
        
        Returns:
            Tuple of (should_aggregate, reason)
        """
        with self.lock:
            if self.round_start_time is None:
                return False, "Round not started"
            
            num_received = len(self.received_gradients)
            num_expected = len(self.expected_nodes)
            
            # Check if all nodes responded
            if num_received == num_expected:
                return True, "All nodes responded"
            
            # Check minimum threshold
            min_nodes = int(num_expected * self.min_nodes_percentage)
            if num_received < min_nodes:
                # Check timeout
                elapsed = (datetime.now() - self.round_start_time).total_seconds()
                if elapsed >= self.timeout_seconds:
                    return False, f"Timeout with insufficient nodes ({num_received}/{min_nodes})"
                return False, f"Waiting for more nodes ({num_received}/{min_nodes})"
            
            # Minimum threshold met, check timeout
            elapsed = (datetime.now() - self.round_start_time).total_seconds()
            if elapsed >= self.timeout_seconds:
                return True, f"Timeout reached with {num_received}/{num_expected} nodes"
            
            return False, f"Waiting ({num_received}/{num_expected}, {elapsed:.1f}s elapsed)"
    
    def aggregate_round(
        self,
        parameter_shapes: Dict[str, Tuple[int, ...]]
    ) -> Optional[Dict[str, np.ndarray]]:
        """
        Aggregate all received gradients for current round.
        
        Args:
            parameter_shapes: Expected shapes for validation
            
        Returns:
            Dict of aggregated gradients or None if aggregation failed
        """
        with self.lock:
            try:
                start_time = time.time()
                
                # Check if we have gradients
                if not self.received_gradients:
                    logger.error("No gradients to aggregate")
                    return None
                
                # Record wait time
                if self.round_start_time:
                    wait_time = (datetime.now() - self.round_start_time).total_seconds()
                    self.wait_times.append(wait_time)
                
                logger.info(
                    f"Aggregating {len(self.received_gradients)} gradients "
                    f"(strategy: {self.strategy.value})"
                )
                
                # Aggregate based on strategy
                if self.strategy == AggregationStrategy.SIMPLE_AVERAGE:
                    aggregated = self._aggregate_simple_average(parameter_shapes)
                
                elif self.strategy == AggregationStrategy.WEIGHTED_AVERAGE:
                    aggregated = self._aggregate_weighted_average(parameter_shapes)
                
                elif self.strategy == AggregationStrategy.FEDERATED_AVERAGING:
                    aggregated = self._aggregate_federated_averaging(parameter_shapes)
                
                else:
                    logger.error(f"Unknown aggregation strategy: {self.strategy}")
                    return None
                
                # Apply gradient clipping if configured
                if aggregated and self.gradient_clip_value is not None:
                    aggregated = self._clip_gradients(aggregated)
                
                # Validate aggregated gradients
                if not self._validate_aggregated_gradients(aggregated, parameter_shapes):
                    logger.error("Aggregated gradients validation failed")
                    return None
                
                # Record metrics
                aggregation_time = time.time() - start_time
                self.aggregation_times.append(aggregation_time)
                
                # Store history
                self._record_round_history(aggregated)
                
                logger.info(
                    f"Aggregation complete: {len(aggregated)} parameters, "
                    f"time={aggregation_time:.3f}s"
                )
                
                return aggregated
                
            except Exception as e:
                logger.error(f"Aggregation failed: {e}", exc_info=True)
                return None
    
    def _aggregate_simple_average(
        self,
        parameter_shapes: Dict[str, Tuple[int, ...]]
    ) -> Dict[str, np.ndarray]:
        """
        Simple averaging: sum all gradients and divide by number of nodes.
        
        Args:
            parameter_shapes: Expected parameter shapes
            
        Returns:
            Dict of averaged gradients
        """
        aggregated = {}
        num_nodes = len(self.received_gradients)
        
        for param_name in parameter_shapes.keys():
            # Initialize accumulator
            accumulated = None
            
            for node_gradients in self.received_gradients.values():
                if param_name in node_gradients:
                    grad = node_gradients[param_name]
                    
                    if accumulated is None:
                        accumulated = grad.copy()
                    else:
                        accumulated += grad
            
            if accumulated is not None:
                aggregated[param_name] = accumulated / num_nodes
            else:
                # If no gradients for this parameter, use zeros
                aggregated[param_name] = np.zeros(parameter_shapes[param_name])
                logger.warning(f"No gradients received for parameter: {param_name}")
        
        return aggregated
    
    def _aggregate_weighted_average(
        self,
        parameter_shapes: Dict[str, Tuple[int, ...]]
    ) -> Dict[str, np.ndarray]:
        """
        Weighted averaging: weight by node contribution (data samples or compute time).
        
        Args:
            parameter_shapes: Expected parameter shapes
            
        Returns:
            Dict of weighted averaged gradients
        """
        aggregated = {}
        
        # Check if we have metadata with weights
        if not self.gradient_metadata:
            logger.info("No metadata provided, falling back to simple average")
            return self._aggregate_simple_average(parameter_shapes)
        
        # Extract weights from metadata (data_samples)
        node_weights = {}
        for node_id, metadata in self.gradient_metadata.items():
            if "data_samples" in metadata:
                node_weights[node_id] = float(metadata["data_samples"])
            else:
                node_weights[node_id] = 1.0  # Default weight
        
        total_weight = sum(node_weights.values())
        
        if total_weight == 0:
            logger.warning("Total weight is zero, using simple average")
            return self._aggregate_simple_average(parameter_shapes)
        
        # Weighted average for each parameter
        for param_name in parameter_shapes.keys():
            accumulated = None
            
            for node_id, node_gradients in self.received_gradients.items():
                if param_name in node_gradients:
                    grad = node_gradients[param_name]
                    weight = node_weights.get(node_id, 1.0)
                    
                    if accumulated is None:
                        accumulated = grad * weight
                    else:
                        accumulated += grad * weight
            
            if accumulated is not None:
                aggregated[param_name] = accumulated / total_weight
            else:
                # If no gradients for this parameter, use zeros
                aggregated[param_name] = np.zeros(parameter_shapes[param_name])
                logger.warning(f"No gradients received for parameter: {param_name}")
        
        return aggregated
    
    def _aggregate_federated_averaging(
        self,
        parameter_shapes: Dict[str, Tuple[int, ...]]
    ) -> Dict[str, np.ndarray]:
        """
        Federated averaging with node quality weighting.
        
        Args:
            parameter_shapes: Expected parameter shapes
            
        Returns:
            Dict of federated averaged gradients
        """
        aggregated = {}
        
        # Calculate weights combining data samples and node weights
        total_weight = 0.0
        node_combined_weights = {}
        
        for node_id, gradient_update in self.received_gradients.items():
            # Base weight from data samples
            sample_weight = gradient_update.data_samples
            
            # Apply node quality weight if available
            node_quality = self.node_weights.get(node_id, 1.0)
            
            combined_weight = sample_weight * node_quality
            node_combined_weights[node_id] = combined_weight
            total_weight += combined_weight
        
        if total_weight == 0:
            logger.warning("Zero total weight, falling back to simple average")
            return self._aggregate_simple_average(parameter_shapes)
        
        # Normalize weights
        for node_id in node_combined_weights:
            node_combined_weights[node_id] /= total_weight
        
        # Aggregate with normalized weights
        for param_name in parameter_shapes.keys():
            accumulated = None
            
            for node_id, gradient_update in self.received_gradients.items():
                if param_name in gradient_update.gradients:
                    grad = gradient_update.gradients[param_name]
                    weight = node_combined_weights[node_id]
                    
                    if accumulated is None:
                        accumulated = grad * weight
                    else:
                        accumulated += grad * weight
            
            if accumulated is not None:
                aggregated[param_name] = accumulated
            else:
                aggregated[param_name] = np.zeros(parameter_shapes[param_name])
        
        return aggregated
    
    def update_node_weight(self, node_id: str, weight: float) -> None:
        """
        Update quality weight for a node.
        
        Args:
            node_id: Node ID
            weight: Quality weight (typically 0.5 to 1.5)
        """
        with self.lock:
            self.node_weights[node_id] = weight
            logger.debug(f"Node {node_id} weight updated to {weight:.3f}")
    
    def _validate_gradients(
        self,
        gradients: Dict[str, np.ndarray],
        node_id: str
    ) -> bool:
        """
        Validate gradients from a node.
        
        Args:
            gradients: Gradient dict to validate
            node_id: Node ID for logging
            
        Returns:
            bool: True if valid
        """
        try:
            for param_name, grad_array in gradients.items():
                # Check for NaN
                if np.isnan(grad_array).any():
                    logger.error(
                        f"NaN detected in gradient from {node_id}: {param_name}"
                    )
                    return False
                
                # Check for Inf
                if np.isinf(grad_array).any():
                    logger.error(
                        f"Inf detected in gradient from {node_id}: {param_name}"
                    )
                    return False
                
                # Check for suspiciously large norms
                grad_norm = np.linalg.norm(grad_array)
                if grad_norm > 1e6:
                    logger.warning(
                        f"Very large gradient norm from {node_id}: "
                        f"{param_name}={grad_norm:.2e}"
                    )
            
            return True
            
        except Exception as e:
            logger.error(f"Gradient validation error: {e}", exc_info=True)
            return False
    
    def _clip_gradients(
        self,
        gradients: Dict[str, np.ndarray]
    ) -> Dict[str, np.ndarray]:
        """
        Clip gradients by global norm.
        
        Args:
            gradients: Gradients to clip
            
        Returns:
            Clipped gradients
        """
        if self.gradient_clip_value is None:
            return gradients
        
        # Compute global norm
        total_norm = 0.0
        for grad_array in gradients.values():
            total_norm += np.sum(grad_array ** 2)
        total_norm = np.sqrt(total_norm)
        
        # Clip if necessary
        if total_norm > self.gradient_clip_value:
            clip_coef = self.gradient_clip_value / (total_norm + 1e-6)
            clipped_gradients = {
                name: grad * clip_coef
                for name, grad in gradients.items()
            }
            logger.debug(f"Gradients clipped: norm={total_norm:.4f} -> {self.gradient_clip_value}")
            return clipped_gradients
        
        return gradients
    
    def _compute_gradient_norm(self, gradients: Dict[str, np.ndarray]) -> float:
        """Compute global gradient norm."""
        total_norm = 0.0
        for grad_array in gradients.values():
            total_norm += np.sum(grad_array ** 2)
        return float(np.sqrt(total_norm))
    
    def _flatten_gradients(self, gradients: Dict[str, np.ndarray]) -> Tuple[List[List[float]], List[List[int]]]:
        """
        Flatten gradients for transmission.
        
        Args:
            gradients: Dictionary of gradient arrays
            
        Returns:
            Tuple of (flattened data, shapes)
        """
        flattened_data = []
        shapes = []
        
        for param_name, grad_array in sorted(gradients.items()):
            # Store shape
            shapes.append(list(grad_array.shape))
            # Flatten and convert to list
            flattened_data.append(grad_array.flatten().tolist())
        
        return flattened_data, shapes
    
    def _validate_aggregated_gradients(
        self,
        gradients: Dict[str, np.ndarray],
        parameter_shapes: Dict[str, Tuple[int, ...]]
    ) -> bool:
        """
        Validate aggregated gradients.
        
        Args:
            gradients: Aggregated gradients
            parameter_shapes: Expected shapes
            
        Returns:
            bool: True if valid
        """
        try:
            for param_name, expected_shape in parameter_shapes.items():
                if param_name not in gradients:
                    logger.error(f"Missing aggregated gradient: {param_name}")
                    return False
                
                grad_array = gradients[param_name]
                
                # Check shape
                if grad_array.shape != expected_shape:
                    logger.error(
                        f"Shape mismatch for {param_name}: "
                        f"expected {expected_shape}, got {grad_array.shape}"
                    )
                    return False
                
                # Check for NaN/Inf
                if np.isnan(grad_array).any():
                    logger.error(f"NaN in aggregated gradient: {param_name}")
                    return False
                
                if np.isinf(grad_array).any():
                    logger.error(f"Inf in aggregated gradient: {param_name}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Aggregated gradient validation error: {e}", exc_info=True)
            return False
    
    def _record_round_history(self, aggregated_gradients: Dict[str, np.ndarray]) -> None:
        """Record history of this aggregation round."""
        # Compute gradient norms for each node
        node_gradients = {}
        for node_id, gradients_dict in self.received_gradients.items():
            # Compute norm from the dict of gradients
            total_norm = 0.0
            for grad_array in gradients_dict.values():
                total_norm += np.sum(grad_array ** 2)
            node_gradients[node_id] = float(np.sqrt(total_norm))
        
        history_entry = {
            "round": self.current_round,
            "timestamp": datetime.now().isoformat(),
            "num_nodes": len(self.received_gradients),
            "expected_nodes": len(self.expected_nodes),
            "gradient_norm": self._compute_gradient_norm(aggregated_gradients),
            "node_gradients": node_gradients,
        }
        
        self.gradient_history.append(history_entry)
        
        # Keep only recent history
        if len(self.gradient_history) > 100:
            self.gradient_history = self.gradient_history[-100:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get aggregation statistics.
        
        Returns:
            Dict with statistics
        """
        with self.lock:
            stats = {
                "current_round": self.current_round,
                "total_rounds": len(self.gradient_history),
                "rejected_gradients": self.rejected_gradients,
            }
            
            if self.aggregation_times:
                stats.update({
                    "avg_aggregation_time": np.mean(self.aggregation_times),
                    "max_aggregation_time": np.max(self.aggregation_times),
                })
            
            if self.wait_times:
                stats.update({
                    "avg_wait_time": np.mean(self.wait_times),
                    "max_wait_time": np.max(self.wait_times),
                })
            
            return stats
    
    def get_missing_nodes(self) -> List[str]:
        """Get list of nodes that haven't submitted gradients."""
        with self.lock:
            return [
                node_id for node_id in self.expected_nodes
                if node_id not in self.received_gradients
            ]
