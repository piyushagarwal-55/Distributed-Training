"""
Dynamic Node Selector - Intelligently selects nodes for each training round.

This module implements node selection strategies that exclude or deprioritize
poorly performing nodes to optimize overall training efficiency.
"""

import time
import threading
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from enum import Enum
import numpy as np

from ..utils.logger import get_logger
from .network_monitor import NetworkQualityMonitor, ConnectionQuality

logger = get_logger(__name__)


class SelectionStrategy(str, Enum):
    """Node selection strategies."""
    ALL_AVAILABLE = "all_available"  # Use all registered nodes
    QUALITY_THRESHOLD = "quality_threshold"  # Only nodes above quality threshold
    TOP_N = "top_n"  # Only top N performing nodes
    ADAPTIVE_THRESHOLD = "adaptive_threshold"  # Dynamic threshold based on cluster performance
    CONTRIBUTION_BASED = "contribution_based"  # Based on contribution score


class NodeState(str, Enum):
    """Node selection state."""
    ACTIVE = "active"  # Participating in training
    EXCLUDED = "excluded"  # Temporarily excluded
    QUARANTINED = "quarantined"  # In quarantine period
    PROBATION = "probation"  # Testing after quarantine


class DynamicNodeSelector:
    """
    Dynamically selects which nodes should participate in each training round.
    
    Evaluates nodes based on their contribution vs cost (waiting time),
    excludes poor performers, and manages fairness mechanisms.
    """
    
    def __init__(
        self,
        network_monitor: NetworkQualityMonitor,
        strategy: str = SelectionStrategy.ADAPTIVE_THRESHOLD,
        min_quality_score: float = 30.0,
        max_selected_nodes: Optional[int] = None,
        enable_quarantine: bool = True,
        quarantine_threshold: int = 5,  # Consecutive failures
        quarantine_duration: float = 300.0,  # 5 minutes
        probation_steps: int = 3
    ):
        """
        Initialize dynamic node selector.
        
        Args:
            network_monitor: NetworkQualityMonitor instance
            strategy: Selection strategy to use
            min_quality_score: Minimum quality score for selection (0-100)
            max_selected_nodes: Maximum number of nodes to select (None = unlimited)
            enable_quarantine: Whether to quarantine problematic nodes
            quarantine_threshold: Number of consecutive failures before quarantine
            quarantine_duration: How long to quarantine nodes (seconds)
            probation_steps: Number of successful steps to exit probation
        """
        self.network_monitor = network_monitor
        self.strategy = strategy
        self.min_quality_score = min_quality_score
        self.max_selected_nodes = max_selected_nodes
        self.enable_quarantine = enable_quarantine
        self.quarantine_threshold = quarantine_threshold
        self.quarantine_duration = quarantine_duration
        self.probation_steps = probation_steps
        
        # Node state tracking
        self.node_states: Dict[str, NodeState] = {}
        self.node_scores: Dict[str, float] = {}
        
        # Contribution tracking
        self.node_contributions: Dict[str, Dict[str, Any]] = {}
        
        # Quarantine tracking
        self.quarantined_nodes: Dict[str, float] = {}  # node_id -> quarantine_end_time
        self.probation_progress: Dict[str, int] = {}  # node_id -> successful_steps
        
        # Selection history
        self.selection_history: List[Dict[str, Any]] = []
        self.max_history = 100
        
        # Fairness tracking
        self.node_selection_counts: Dict[str, int] = {}
        self.node_exclusion_counts: Dict[str, int] = {}
        
        # Statistics
        self.total_selections = 0
        self.total_exclusions = 0
        
        # Thread safety
        self.lock = threading.RLock()
        
        logger.info(f"[NODE SELECT] DynamicNodeSelector initialized with strategy: {strategy}")
        print(f"[NODE SELECT] Node selection initialized (strategy: {strategy})")
    
    def register_node(self, node_id: str):
        """
        Register a node with the selector.
        
        Args:
            node_id: Node identifier
        """
        with self.lock:
            self.node_states[node_id] = NodeState.ACTIVE
            self.node_scores[node_id] = 50.0  # Neutral initial score
            self.node_contributions[node_id] = {
                'compute_time': 0.0,
                'waiting_time': 0.0,
                'successful_contributions': 0,
                'failed_contributions': 0,
                'total_contribution_score': 0.0
            }
            self.node_selection_counts[node_id] = 0
            self.node_exclusion_counts[node_id] = 0
            
            logger.info(f"[NODE SELECT] Registered node {node_id}")
    
    def record_contribution(
        self,
        node_id: str,
        compute_time: float,
        waiting_time: float,
        success: bool
    ):
        """
        Record a node's contribution to training.
        
        Args:
            node_id: Node identifier
            compute_time: Time spent computing
            waiting_time: Time spent waiting (network latency, etc.)
            success: Whether the contribution was successful
        """
        with self.lock:
            if node_id not in self.node_contributions:
                self.register_node(node_id)
            
            contrib = self.node_contributions[node_id]
            contrib['compute_time'] += compute_time
            contrib['waiting_time'] += waiting_time
            
            if success:
                contrib['successful_contributions'] += 1
                
                # Update probation progress
                if node_id in self.probation_progress:
                    self.probation_progress[node_id] += 1
                    
                    if self.probation_progress[node_id] >= self.probation_steps:
                        # Exit probation
                        self.node_states[node_id] = NodeState.ACTIVE
                        del self.probation_progress[node_id]
                        logger.info(f"[NODE SELECT] Node {node_id} exited probation")
                        print(f"[NODE SELECT] Node {node_id}: ✓ Exited probation")
            else:
                contrib['failed_contributions'] += 1
                
                # Check if should be quarantined
                if self.enable_quarantine:
                    total_recent = contrib['successful_contributions'] + contrib['failed_contributions']
                    if total_recent >= self.quarantine_threshold:
                        # Check recent failure rate
                        failure_rate = contrib['failed_contributions'] / total_recent
                        
                        if failure_rate > 0.7:  # >70% failure rate
                            self._quarantine_node(node_id)
            
            # Update contribution score
            self._calculate_contribution_score(node_id)
    
    def _calculate_contribution_score(self, node_id: str) -> float:
        """
        Calculate contribution score for a node.
        
        Score = (effective_compute_time) / (total_time_including_waiting) * reliability_factor
        
        Args:
            node_id: Node identifier
            
        Returns:
            Contribution score (0-100)
        """
        contrib = self.node_contributions[node_id]
        
        compute_time = contrib['compute_time']
        waiting_time = contrib['waiting_time']
        total_time = compute_time + waiting_time
        
        # Efficiency score (0-50 points)
        if total_time > 0:
            efficiency = (compute_time / total_time) * 50
        else:
            efficiency = 0
        
        # Reliability score (0-50 points)
        total_attempts = contrib['successful_contributions'] + contrib['failed_contributions']
        if total_attempts > 0:
            reliability = (contrib['successful_contributions'] / total_attempts) * 50
        else:
            reliability = 25  # Neutral
        
        score = efficiency + reliability
        
        # Store and return
        self.node_scores[node_id] = score
        contrib['total_contribution_score'] = score
        
        return score
    
    def _quarantine_node(self, node_id: str):
        """
        Place a node in quarantine.
        
        Args:
            node_id: Node to quarantine
        """
        quarantine_end = time.time() + self.quarantine_duration
        self.quarantined_nodes[node_id] = quarantine_end
        self.node_states[node_id] = NodeState.QUARANTINED
        
        logger.warning(f"[NODE SELECT] Node {node_id} quarantined until {datetime.fromtimestamp(quarantine_end)}")
        print(f"[NODE SELECT] Node {node_id}: ⚠ Quarantined for {self.quarantine_duration}s")
    
    def _check_quarantine_expiry(self):
        """Check and release nodes from quarantine if time expired."""
        current_time = time.time()
        nodes_to_release = []
        
        for node_id, expiry_time in self.quarantined_nodes.items():
            if current_time >= expiry_time:
                nodes_to_release.append(node_id)
        
        for node_id in nodes_to_release:
            del self.quarantined_nodes[node_id]
            self.node_states[node_id] = NodeState.PROBATION
            self.probation_progress[node_id] = 0
            
            logger.info(f"[NODE SELECT] Node {node_id} released from quarantine to probation")
            print(f"[NODE SELECT] Node {node_id}: Released to probation")
    
    def select_nodes(self, available_nodes: Optional[List[str]] = None) -> List[str]:
        """
        Select nodes for the current training round.
        
        Args:
            available_nodes: List of available node IDs (None = all registered)
            
        Returns:
            List of selected node IDs
        """
        with self.lock:
            # Check quarantine expiry
            self._check_quarantine_expiry()
            
            # Get available nodes
            if available_nodes is None:
                available_nodes = list(self.node_states.keys())
            
            # Filter out quarantined nodes
            available_nodes = [
                n for n in available_nodes
                if self.node_states.get(n) != NodeState.QUARANTINED
            ]
            
            if not available_nodes:
                logger.warning("[NODE SELECT] No available nodes for selection")
                return []
            
            # Apply selection strategy
            if self.strategy == SelectionStrategy.ALL_AVAILABLE:
                selected = self._select_all(available_nodes)
            
            elif self.strategy == SelectionStrategy.QUALITY_THRESHOLD:
                selected = self._select_by_quality_threshold(available_nodes)
            
            elif self.strategy == SelectionStrategy.TOP_N:
                selected = self._select_top_n(available_nodes)
            
            elif self.strategy == SelectionStrategy.ADAPTIVE_THRESHOLD:
                selected = self._select_adaptive_threshold(available_nodes)
            
            elif self.strategy == SelectionStrategy.CONTRIBUTION_BASED:
                selected = self._select_by_contribution(available_nodes)
            
            else:
                logger.warning(f"[NODE SELECT] Unknown strategy '{self.strategy}', selecting all")
                selected = available_nodes
            
            # Update tracking
            for node_id in available_nodes:
                if node_id in selected:
                    self.node_selection_counts[node_id] = self.node_selection_counts.get(node_id, 0) + 1
                else:
                    self.node_exclusion_counts[node_id] = self.node_exclusion_counts.get(node_id, 0) + 1
            
            self.total_selections += 1
            
            # Record selection
            self.selection_history.append({
                'timestamp': time.time(),
                'strategy': self.strategy,
                'available': len(available_nodes),
                'selected': len(selected),
                'excluded': len(available_nodes) - len(selected),
                'selected_nodes': selected.copy()
            })
            
            if len(self.selection_history) > self.max_history:
                self.selection_history = self.selection_history[-self.max_history:]
            
            logger.info(f"[NODE SELECT] Selected {len(selected)}/{len(available_nodes)} nodes")
            print(f"[NODE SELECT] Selected {len(selected)}/{len(available_nodes)} nodes for training")
            
            return selected
    
    def _select_all(self, available_nodes: List[str]) -> List[str]:
        """Select all available nodes."""
        return available_nodes
    
    def _select_by_quality_threshold(self, available_nodes: List[str]) -> List[str]:
        """Select nodes above quality threshold."""
        selected = []
        
        for node_id in available_nodes:
            profile = self.network_monitor.get_node_profile(node_id)
            
            if profile is None:
                # No profile yet, include by default
                selected.append(node_id)
                continue
            
            quality_score = profile['quality_score']
            
            if quality_score >= self.min_quality_score:
                selected.append(node_id)
        
        return selected
    
    def _select_top_n(self, available_nodes: List[str]) -> List[str]:
        """Select top N nodes by combined score."""
        # Calculate combined score (network quality + contribution)
        node_combined_scores = []
        
        for node_id in available_nodes:
            profile = self.network_monitor.get_node_profile(node_id)
            quality_score = profile['quality_score'] if profile else 50.0
            
            contribution_score = self.node_scores.get(node_id, 50.0)
            
            # Combined score (60% quality, 40% contribution)
            combined = 0.6 * quality_score + 0.4 * contribution_score
            
            node_combined_scores.append((node_id, combined))
        
        # Sort by score (descending)
        node_combined_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Select top N
        n = self.max_selected_nodes or len(available_nodes)
        selected = [node_id for node_id, _ in node_combined_scores[:n]]
        
        return selected
    
    def _select_adaptive_threshold(self, available_nodes: List[str]) -> List[str]:
        """Select nodes using adaptive quality threshold."""
        # Calculate cluster-wide quality statistics
        quality_scores = []
        
        for node_id in available_nodes:
            profile = self.network_monitor.get_node_profile(node_id)
            if profile:
                quality_scores.append(profile['quality_score'])
        
        if not quality_scores:
            # No quality data, include all
            return available_nodes
        
        # Set threshold based on cluster statistics
        mean_quality = np.mean(quality_scores)
        std_quality = np.std(quality_scores)
        
        # Adaptive threshold: mean - 0.5 * std (include nodes within 0.5 std below mean)
        adaptive_threshold = max(self.min_quality_score, mean_quality - 0.5 * std_quality)
        
        # Select nodes above adaptive threshold
        selected = []
        
        for node_id in available_nodes:
            profile = self.network_monitor.get_node_profile(node_id)
            
            if profile is None:
                selected.append(node_id)
                continue
            
            if profile['quality_score'] >= adaptive_threshold:
                selected.append(node_id)
        
        logger.debug(f"[NODE SELECT] Adaptive threshold: {adaptive_threshold:.1f}")
        
        return selected
    
    def _select_by_contribution(self, available_nodes: List[str]) -> List[str]:
        """Select nodes based on contribution scores."""
        # Filter by contribution score
        selected = []
        
        for node_id in available_nodes:
            score = self.node_scores.get(node_id, 50.0)
            
            # Include if score is above minimum threshold
            threshold = 30.0  # Contribution score threshold
            if score >= threshold:
                selected.append(node_id)
        
        return selected
    
    def get_node_state(self, node_id: str) -> Optional[str]:
        """Get current state of a node."""
        with self.lock:
            state = self.node_states.get(node_id)
            return state.value if state else None
    
    def get_node_score(self, node_id: str) -> float:
        """Get contribution score for a node."""
        with self.lock:
            return self.node_scores.get(node_id, 0.0)
    
    def get_selection_summary(self) -> Dict[str, Any]:
        """
        Get summary of selection activity.
        
        Returns:
            Dictionary with selection statistics
        """
        with self.lock:
            if not self.node_states:
                return {
                    'nodes_tracked': 0,
                    'message': 'No nodes registered'
                }
            
            active_nodes = sum(1 for s in self.node_states.values() if s == NodeState.ACTIVE)
            quarantined_nodes = sum(1 for s in self.node_states.values() if s == NodeState.QUARANTINED)
            probation_nodes = sum(1 for s in self.node_states.values() if s == NodeState.PROBATION)
            
            # Calculate average selection rate
            total_nodes = len(self.node_states)
            if self.selection_history:
                recent_selections = self.selection_history[-10:]
                avg_selected = np.mean([s['selected'] for s in recent_selections])
                avg_selection_rate = avg_selected / total_nodes if total_nodes > 0 else 0
            else:
                avg_selection_rate = 0
            
            return {
                'total_nodes': total_nodes,
                'active_nodes': active_nodes,
                'quarantined_nodes': quarantined_nodes,
                'probation_nodes': probation_nodes,
                'strategy': self.strategy,
                'total_selections': self.total_selections,
                'average_selection_rate': avg_selection_rate,
                'fairness_metrics': self._calculate_fairness_metrics()
            }
    
    def _calculate_fairness_metrics(self) -> Dict[str, Any]:
        """Calculate fairness metrics across nodes."""
        if not self.node_selection_counts:
            return {}
        
        selection_counts = list(self.node_selection_counts.values())
        exclusion_counts = list(self.node_exclusion_counts.values())
        
        return {
            'selection_variance': float(np.var(selection_counts)),
            'max_selections': max(selection_counts),
            'min_selections': min(selection_counts),
            'max_exclusions': max(exclusion_counts) if exclusion_counts else 0,
            'min_exclusions': min(exclusion_counts) if exclusion_counts else 0
        }
    
    def get_node_details(self, node_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a node.
        
        Args:
            node_id: Node identifier
            
        Returns:
            Dictionary with node details
        """
        with self.lock:
            if node_id not in self.node_states:
                return {'error': 'Node not found'}
            
            return {
                'node_id': node_id,
                'state': self.node_states[node_id].value,
                'contribution_score': self.node_scores[node_id],
                'contributions': self.node_contributions.get(node_id, {}),
                'selection_count': self.node_selection_counts.get(node_id, 0),
                'exclusion_count': self.node_exclusion_counts.get(node_id, 0),
                'is_quarantined': node_id in self.quarantined_nodes,
                'is_probation': node_id in self.probation_progress,
                'probation_progress': self.probation_progress.get(node_id, 0)
            }
    
    def force_include_node(self, node_id: str):
        """Force a node to be included (remove from quarantine, set active)."""
        with self.lock:
            if node_id in self.quarantined_nodes:
                del self.quarantined_nodes[node_id]
            
            if node_id in self.probation_progress:
                del self.probation_progress[node_id]
            
            self.node_states[node_id] = NodeState.ACTIVE
            
            logger.info(f"[NODE SELECT] Node {node_id} forced to active state")
            print(f"[NODE SELECT] Node {node_id}: Forced to active")
    
    def force_exclude_node(self, node_id: str):
        """Force a node to be excluded."""
        with self.lock:
            self.node_states[node_id] = NodeState.EXCLUDED
            
            logger.info(f"[NODE SELECT] Node {node_id} forced to excluded state")
            print(f"[NODE SELECT] Node {node_id}: Forced to excluded")
    
    def export_metrics(self) -> Dict[str, Any]:
        """
        Export all selector metrics.
        
        Returns:
            Dictionary with complete selector state
        """
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'configuration': {
                'strategy': self.strategy,
                'min_quality_score': self.min_quality_score,
                'max_selected_nodes': self.max_selected_nodes,
                'enable_quarantine': self.enable_quarantine,
                'quarantine_threshold': self.quarantine_threshold
            },
            'summary': self.get_selection_summary(),
            'node_details': {
                node_id: self.get_node_details(node_id)
                for node_id in self.node_states.keys()
            },
            'recent_history': self.selection_history[-20:]
        }
