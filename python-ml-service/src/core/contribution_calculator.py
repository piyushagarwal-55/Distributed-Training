"""
Contribution Calculator - Calculates and tracks node contributions from training metrics.

This module processes collected metrics to quantify each node's contribution fairly,
computing multiple scoring dimensions and formatting data for blockchain submission.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import statistics
from collections import defaultdict

from ..models.metrics import TrainingMetrics, NetworkMetrics
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class NodeContribution:
    """Represents a node's total contribution metrics."""
    
    node_id: str
    node_address: str
    
    # Raw metrics
    compute_time: float = 0.0  # Total compute time in seconds
    gradients_accepted: int = 0
    gradients_rejected: int = 0
    successful_rounds: int = 0
    failed_rounds: int = 0
    samples_processed: int = 0
    
    # Quality metrics
    avg_gradient_norm: float = 0.0
    gradient_consistency: float = 0.0  # 0-1 score
    avg_loss: float = 0.0
    
    # Network metrics
    avg_latency_ms: float = 0.0
    uptime_percentage: float = 0.0
    
    # Calculated scores (0-10000 scale)
    quality_score: int = 0
    reliability_score: int = 0
    final_score: int = 0
    
    # Timestamps
    first_contribution: Optional[datetime] = None
    last_contribution: Optional[datetime] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionContributionSummary:
    """Summary of all contributions for a training session."""
    
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # Node contributions
    node_contributions: Dict[str, NodeContribution] = field(default_factory=dict)
    
    # Session totals
    total_compute_time: float = 0.0
    total_gradients: int = 0
    total_rounds: int = 0
    total_samples: int = 0
    
    # Statistics
    avg_quality_score: float = 0.0
    avg_reliability_score: float = 0.0
    participant_count: int = 0
    
    # Outliers
    outlier_nodes: List[str] = field(default_factory=list)
    
    metadata: Dict[str, Any] = field(default_factory=dict)


class ContributionCalculator:
    """
    Calculates node contributions from training metrics.
    
    Features:
    - Aggregates metrics per epoch and per session
    - Computes multi-dimensional contribution scores
    - Detects and handles outliers
    - Formats data for blockchain submission
    """
    
    def __init__(self, session_id: str):
        """
        Initialize contribution calculator for a session.
        
        Args:
            session_id: Training session identifier
        """
        self.session_id = session_id
        self.start_time = datetime.utcnow()
        
        # Storage for per-epoch data
        self.epoch_metrics: Dict[int, List[TrainingMetrics]] = defaultdict(list)
        self.epoch_network_metrics: Dict[int, List[NetworkMetrics]] = defaultdict(list)
        
        # Accumulated contributions
        self.contributions: Dict[str, NodeContribution] = {}
        
        # Node address mapping (node_id -> address)
        self.node_addresses: Dict[str, str] = {}
        
        logger.info(f"[ContribCalc] Initialized for session: {session_id}")
    
    def register_node(self, node_id: str, node_address: str):
        """
        Register a node and its blockchain address.
        
        Args:
            node_id: Node identifier
            node_address: Ethereum address
        """
        self.node_addresses[node_id] = node_address
        
        if node_id not in self.contributions:
            self.contributions[node_id] = NodeContribution(
                node_id=node_id,
                node_address=node_address
            )
            logger.info(f"[ContribCalc] Registered node: {node_id} -> {node_address}")
    
    def add_training_metrics(self, metrics: TrainingMetrics):
        """
        Add training metrics from a node.
        
        Args:
            metrics: Training metrics to add
        """
        epoch = metrics.epoch
        node_id = metrics.node_id
        
        self.epoch_metrics[epoch].append(metrics)
        
        # Ensure node is registered
        if node_id not in self.contributions:
            logger.warning(f"[ContribCalc] Node {node_id} not registered, auto-registering")
            self.contributions[node_id] = NodeContribution(
                node_id=node_id,
                node_address=f"0x{'0'*40}"  # Placeholder address
            )
        
        contrib = self.contributions[node_id]
        
        # Update compute time
        contrib.compute_time += metrics.time_taken_seconds
        contrib.samples_processed += metrics.samples_processed
        
        # Track timestamps
        if contrib.first_contribution is None:
            contrib.first_contribution = metrics.timestamp
        contrib.last_contribution = metrics.timestamp
        
        logger.debug(f"[ContribCalc] Added training metrics: {node_id} epoch={epoch} "
                    f"time={metrics.time_taken_seconds:.2f}s")
    
    def add_network_metrics(self, metrics: NetworkMetrics):
        """
        Add network metrics for a node.
        
        Args:
            metrics: Network metrics to add
        """
        epoch = getattr(metrics, 'epoch', 0)
        self.epoch_network_metrics[epoch].append(metrics)
        
        logger.debug(f"[ContribCalc] Added network metrics: {metrics.node_id} "
                    f"latency={metrics.latency_ms:.2f}ms")
    
    def record_gradient_submission(self, node_id: str, accepted: bool, 
                                   gradient_norm: Optional[float] = None):
        """
        Record a gradient submission result.
        
        Args:
            node_id: Node identifier
            accepted: Whether gradient was accepted
            gradient_norm: L2 norm of gradient (if available)
        """
        if node_id not in self.contributions:
            logger.warning(f"[ContribCalc] Unknown node for gradient: {node_id}")
            return
        
        contrib = self.contributions[node_id]
        
        if accepted:
            contrib.gradients_accepted += 1
            contrib.successful_rounds += 1
            
            if gradient_norm is not None:
                # Update moving average
                total = contrib.gradients_accepted
                contrib.avg_gradient_norm = (
                    (contrib.avg_gradient_norm * (total - 1) + gradient_norm) / total
                )
        else:
            contrib.gradients_rejected += 1
            contrib.failed_rounds += 1
        
        logger.debug(f"[ContribCalc] Gradient submission: {node_id} "
                    f"accepted={accepted} norm={gradient_norm}")
    
    def calculate_quality_score(self, node_id: str) -> int:
        """
        Calculate quality score for a node (0-10000 scale).
        
        Factors:
        - Gradient acceptance rate
        - Gradient consistency
        - Loss performance
        
        Args:
            node_id: Node identifier
            
        Returns:
            Quality score (0-10000)
        """
        if node_id not in self.contributions:
            return 0
        
        contrib = self.contributions[node_id]
        
        # Base score from acceptance rate
        total_gradients = contrib.gradients_accepted + contrib.gradients_rejected
        if total_gradients == 0:
            acceptance_score = 0
        else:
            acceptance_rate = contrib.gradients_accepted / total_gradients
            acceptance_score = int(acceptance_rate * 5000)  # 0-5000
        
        # Consistency score (gradient norm stability)
        # For now, use a simple heuristic based on gradient norm
        if contrib.avg_gradient_norm > 0:
            # Normalize gradient norm (assume typical range 0.01-10)
            norm_score = min(1.0, contrib.avg_gradient_norm / 10.0)
            consistency_score = int(norm_score * 3000)  # 0-3000
        else:
            consistency_score = 0
        
        # Success rate score
        total_rounds = contrib.successful_rounds + contrib.failed_rounds
        if total_rounds > 0:
            success_rate = contrib.successful_rounds / total_rounds
            success_score = int(success_rate * 2000)  # 0-2000
        else:
            success_score = 0
        
        quality_score = acceptance_score + consistency_score + success_score
        
        # Cap at 10000
        quality_score = min(10000, quality_score)
        
        logger.debug(f"[ContribCalc] Quality score for {node_id}: {quality_score} "
                    f"(acceptance={acceptance_score}, consistency={consistency_score}, "
                    f"success={success_score})")
        
        return quality_score
    
    def calculate_reliability_score(self, node_id: str) -> int:
        """
        Calculate reliability score for a node (0-10000 scale).
        
        Factors:
        - Uptime/participation rate
        - Network quality
        - Consistent participation across epochs
        
        Args:
            node_id: Node identifier
            
        Returns:
            Reliability score (0-10000)
        """
        if node_id not in self.contributions:
            return 0
        
        contrib = self.contributions[node_id]
        
        # Participation score (based on successful rounds)
        # Assume average is 50 rounds per session
        participation_score = min(5000, contrib.successful_rounds * 100)
        
        # Network quality score (inverse of latency)
        if contrib.avg_latency_ms > 0:
            # Lower latency = higher score
            # Assume 500ms is poor, 50ms is excellent
            latency_normalized = max(0, min(1, (500 - contrib.avg_latency_ms) / 450))
            network_score = int(latency_normalized * 3000)
        else:
            network_score = 2000  # Default moderate score
        
        # Consistency score (uptime)
        if contrib.uptime_percentage > 0:
            uptime_score = int(contrib.uptime_percentage * 2000)
        else:
            uptime_score = 2000  # Default if not tracked
        
        reliability_score = participation_score + network_score + uptime_score
        
        # Cap at 10000
        reliability_score = min(10000, reliability_score)
        
        logger.debug(f"[ContribCalc] Reliability score for {node_id}: {reliability_score} "
                    f"(participation={participation_score}, network={network_score}, "
                    f"uptime={uptime_score})")
        
        return reliability_score
    
    def calculate_final_score(self, node_id: str) -> int:
        """
        Calculate final contribution score with multipliers.
        
        Formula: base_score * quality_multiplier * reliability_multiplier
        
        Args:
            node_id: Node identifier
            
        Returns:
            Final score (scaled)
        """
        if node_id not in self.contributions:
            return 0
        
        contrib = self.contributions[node_id]
        
        # Base score: compute time (in seconds)
        base_score = int(contrib.compute_time)
        
        # Quality multiplier: 0.5x to 1.5x
        quality_score = self.calculate_quality_score(node_id)
        quality_multiplier = 0.5 + (quality_score / 10000.0)  # 0.5 to 1.5
        
        # Reliability multiplier: 0.8x to 1.2x
        reliability_score = self.calculate_reliability_score(node_id)
        reliability_multiplier = 0.8 + (reliability_score / 10000.0 * 0.4)  # 0.8 to 1.2
        
        # Final score
        final_score = int(base_score * quality_multiplier * reliability_multiplier)
        
        logger.info(f"[ContribCalc] Final score for {node_id}: {final_score} "
                   f"(base={base_score}, quality_mult={quality_multiplier:.2f}, "
                   f"reliability_mult={reliability_multiplier:.2f})")
        
        return final_score
    
    def update_all_scores(self):
        """Calculate and update scores for all nodes."""
        logger.info(f"[ContribCalc] Updating scores for {len(self.contributions)} nodes")
        
        for node_id in self.contributions:
            contrib = self.contributions[node_id]
            contrib.quality_score = self.calculate_quality_score(node_id)
            contrib.reliability_score = self.calculate_reliability_score(node_id)
            contrib.final_score = self.calculate_final_score(node_id)
        
        logger.info("[ContribCalc] Score update complete")
    
    def detect_outliers(self, threshold_std: float = 3.0) -> List[str]:
        """
        Detect nodes with suspiciously high or low contributions.
        
        Uses z-score method to identify outliers.
        
        Args:
            threshold_std: Number of standard deviations for outlier detection
            
        Returns:
            List of node IDs identified as outliers
        """
        if len(self.contributions) < 3:
            logger.info("[ContribCalc] Too few nodes for outlier detection")
            return []
        
        # Collect final scores
        scores = [c.final_score for c in self.contributions.values()]
        
        if not scores:
            return []
        
        mean_score = statistics.mean(scores)
        
        if len(scores) > 1:
            std_score = statistics.stdev(scores)
        else:
            std_score = 0
        
        outliers = []
        
        if std_score > 0:
            for node_id, contrib in self.contributions.items():
                z_score = abs((contrib.final_score - mean_score) / std_score)
                
                if z_score > threshold_std:
                    outliers.append(node_id)
                    logger.warning(f"[ContribCalc] Outlier detected: {node_id} "
                                 f"(score={contrib.final_score}, z={z_score:.2f})")
        
        logger.info(f"[ContribCalc] Outlier detection complete: {len(outliers)} outliers")
        return outliers
    
    def validate_contributions(self) -> bool:
        """
        Validate all contributions for consistency.
        
        Returns:
            True if all validations pass
        """
        logger.info("[ContribCalc] Validating contributions...")
        
        issues = []
        
        for node_id, contrib in self.contributions.items():
            # Check for negative values
            if contrib.compute_time < 0:
                issues.append(f"{node_id}: negative compute time")
            
            if contrib.gradients_accepted < 0:
                issues.append(f"{node_id}: negative gradients accepted")
            
            # Check for impossibly large values
            if contrib.compute_time > 86400:  # > 24 hours
                issues.append(f"{node_id}: compute time exceeds 24 hours")
            
            # Check score ranges
            if not (0 <= contrib.quality_score <= 10000):
                issues.append(f"{node_id}: quality score out of range")
            
            if not (0 <= contrib.reliability_score <= 10000):
                issues.append(f"{node_id}: reliability score out of range")
        
        if issues:
            logger.error(f"[ContribCalc] Validation failed with {len(issues)} issues:")
            for issue in issues:
                logger.error(f"  - {issue}")
            return False
        
        logger.info("[ContribCalc] Validation passed")
        return True
    
    def format_for_blockchain(self) -> List[Dict[str, Any]]:
        """
        Format contributions for blockchain submission.
        
        Returns:
            List of contribution dictionaries ready for smart contract
        """
        logger.info("[ContribCalc] Formatting contributions for blockchain...")
        
        formatted = []
        
        for node_id, contrib in self.contributions.items():
            formatted.append({
                'node_address': contrib.node_address,
                'compute_time': int(contrib.compute_time),  # Seconds
                'gradients_accepted': contrib.gradients_accepted,
                'successful_rounds': contrib.successful_rounds,
                'quality_score': contrib.quality_score
            })
        
        logger.info(f"[ContribCalc] Formatted {len(formatted)} contributions")
        return formatted
    
    def get_summary(self) -> SessionContributionSummary:
        """
        Get a summary of all contributions for the session.
        
        Returns:
            SessionContributionSummary object
        """
        # Update all scores first
        self.update_all_scores()
        
        # Calculate totals
        total_compute = sum(c.compute_time for c in self.contributions.values())
        total_grads = sum(c.gradients_accepted for c in self.contributions.values())
        total_rounds = sum(c.successful_rounds for c in self.contributions.values())
        total_samples = sum(c.samples_processed for c in self.contributions.values())
        
        # Calculate averages
        if self.contributions:
            avg_quality = statistics.mean(c.quality_score for c in self.contributions.values())
            avg_reliability = statistics.mean(c.reliability_score for c in self.contributions.values())
        else:
            avg_quality = 0
            avg_reliability = 0
        
        # Detect outliers
        outliers = self.detect_outliers()
        
        summary = SessionContributionSummary(
            session_id=self.session_id,
            start_time=self.start_time,
            end_time=datetime.utcnow(),
            node_contributions=self.contributions.copy(),
            total_compute_time=total_compute,
            total_gradients=total_grads,
            total_rounds=total_rounds,
            total_samples=total_samples,
            avg_quality_score=avg_quality,
            avg_reliability_score=avg_reliability,
            participant_count=len(self.contributions),
            outlier_nodes=outliers
        )
        
        logger.info(f"[ContribCalc] Generated summary: {len(self.contributions)} nodes, "
                   f"{total_compute:.2f}s compute, {total_grads} gradients")
        
        return summary
    
    def get_node_contribution(self, node_id: str) -> Optional[NodeContribution]:
        """Get contribution data for a specific node."""
        return self.contributions.get(node_id)
    
    def get_all_contributions(self) -> Dict[str, NodeContribution]:
        """Get all node contributions."""
        return self.contributions.copy()
