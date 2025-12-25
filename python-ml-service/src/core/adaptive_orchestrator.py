"""
Adaptive Training Orchestrator - High-level orchestrator for adaptive distributed training.

This module integrates all adaptive mechanisms (network monitoring, batch adaptation,
node selection) into a cohesive training loop that continuously optimizes for
current conditions.
"""

import time
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import numpy as np

from ..models.config import SystemConfig
from ..utils.logger import get_logger
from .network_monitor import NetworkQualityMonitor
from .adaptive_batch_controller import AdaptiveBatchController, BatchSizeStrategy
from .node_selector import DynamicNodeSelector, SelectionStrategy

logger = get_logger(__name__)


class AdaptationPolicy(str, Enum):
    """Adaptation behavior policies."""
    CONSERVATIVE = "conservative"  # Small gradual changes
    AGGRESSIVE = "aggressive"  # Large changes to find optimum quickly
    REACTIVE = "reactive"  # Respond immediately to changes
    PROACTIVE = "proactive"  # Predict and adapt preemptively


class TrainingPhase(str, Enum):
    """Training phase states."""
    INITIALIZATION = "initialization"
    WARMUP = "warmup"  # Initial phase without adaptation
    ADAPTIVE_TRAINING = "adaptive_training"  # Full adaptive mode
    CONVERGENCE = "convergence"  # Near convergence, minimal adaptation
    COMPLETED = "completed"


class AdaptiveOrchestrator:
    """
    Orchestrates adaptive distributed training.
    
    Integrates network monitoring, batch size adaptation, and node selection
    to continuously optimize training under varying conditions.
    """
    
    def __init__(
        self,
        config: SystemConfig,
        network_monitor: NetworkQualityMonitor,
        batch_controller: AdaptiveBatchController,
        node_selector: DynamicNodeSelector,
        adaptation_policy: str = AdaptationPolicy.REACTIVE,
        adaptation_interval: int = 5,  # Adapt every N rounds
        warmup_rounds: int = 10,  # No adaptation during warmup
        enable_rollback: bool = True
    ):
        """
        Initialize adaptive orchestrator.
        
        Args:
            config: System configuration
            network_monitor: NetworkQualityMonitor instance
            batch_controller: AdaptiveBatchController instance
            node_selector: DynamicNodeSelector instance
            adaptation_policy: Adaptation policy to use
            adaptation_interval: How often to trigger adaptations (rounds)
            warmup_rounds: Number of rounds before enabling adaptation
            enable_rollback: Whether to rollback bad adaptations
        """
        self.config = config
        self.network_monitor = network_monitor
        self.batch_controller = batch_controller
        self.node_selector = node_selector
        self.adaptation_policy = adaptation_policy
        self.adaptation_interval = adaptation_interval
        self.warmup_rounds = warmup_rounds
        self.enable_rollback = enable_rollback
        
        # Training state
        self.current_round = 0
        self.current_epoch = 0
        self.phase = TrainingPhase.INITIALIZATION
        
        # Performance tracking
        self.round_metrics: List[Dict[str, Any]] = []
        self.baseline_metrics: Optional[Dict[str, Any]] = None
        self.best_metrics: Optional[Dict[str, Any]] = None
        
        # Adaptation tracking
        self.last_adaptation_round = 0
        self.adaptations_applied = 0
        self.adaptations_rolled_back = 0
        
        # Configuration snapshots for rollback
        self.configuration_history: List[Dict[str, Any]] = []
        self.max_history = 10
        
        # Performance comparison
        self.adaptive_performance: List[float] = []
        self.baseline_performance: List[float] = []
        
        # Thread safety
        self.lock = threading.RLock()
        
        logger.info(f"[ORCHESTRATOR] AdaptiveOrchestrator initialized with policy: {adaptation_policy}")
        print(f"[ORCHESTRATOR] Adaptive training orchestrator ready")
        print(f"[ORCHESTRATOR] Policy: {adaptation_policy}, Adaptation interval: {adaptation_interval} rounds")
    
    def start_training(self):
        """Initialize training session."""
        with self.lock:
            logger.info("[ORCHESTRATOR] Starting adaptive training session")
            print("=" * 80)
            print("[ORCHESTRATOR] Starting Adaptive Training Session")
            print("=" * 80)
            
            self.phase = TrainingPhase.WARMUP
            self.current_round = 0
            self.current_epoch = 0
            
            # Start background monitoring
            self.network_monitor.start_monitoring()
            
            logger.info(f"[ORCHESTRATOR] Warmup phase: {self.warmup_rounds} rounds")
            print(f"[ORCHESTRATOR] Warmup phase: {self.warmup_rounds} rounds (no adaptation)")
    
    def pre_round_adaptation(
        self,
        available_nodes: List[str],
        round_number: int
    ) -> Dict[str, Any]:
        """
        Perform adaptations before a training round.
        
        Args:
            available_nodes: List of available node IDs
            round_number: Current round number
            
        Returns:
            Dictionary with adaptation decisions
        """
        with self.lock:
            self.current_round = round_number
            
            logger.info(f"[ORCHESTRATOR] Pre-round {round_number} adaptation")
            print(f"\n[ORCHESTRATOR] === Round {round_number} - Pre-Round Adaptation ===")
            
            decisions = {
                'round': round_number,
                'phase': self.phase.value,
                'timestamp': time.time(),
                'adaptations': {}
            }
            
            # Check if we should adapt this round
            should_adapt = self._should_adapt_this_round(round_number)
            
            if not should_adapt:
                # No adaptation, just select all nodes with baseline settings
                selected_nodes = available_nodes
                decisions['adaptations']['reason'] = 'not_adaptation_round'
                logger.debug(f"[ORCHESTRATOR] No adaptation (interval: {self.adaptation_interval})")
            else:
                logger.info("[ORCHESTRATOR] Triggering adaptation...")
                print("[ORCHESTRATOR] Running adaptation algorithms...")
                
                # Step 1: Node selection (network monitor runs in background thread)
                selected_nodes = self.node_selector.select_nodes(available_nodes)
                decisions['adaptations']['node_selection'] = {
                    'available': len(available_nodes),
                    'selected': len(selected_nodes),
                    'excluded': len(available_nodes) - len(selected_nodes),
                    'selected_nodes': selected_nodes
                }
                
                print(f"[ORCHESTRATOR] Node selection: {len(selected_nodes)}/{len(available_nodes)} nodes")
                
                # Step 3: Batch size adaptation
                batch_changes = self.batch_controller.evaluate_and_adapt()
                decisions['adaptations']['batch_sizes'] = batch_changes
                
                if batch_changes:
                    print(f"[ORCHESTRATOR] Batch sizes adapted for {len(batch_changes)} nodes")
                
                # Step 4: Record configuration snapshot
                self._save_configuration_snapshot()
                
                self.last_adaptation_round = round_number
                self.adaptations_applied += 1
            
            decisions['selected_nodes'] = selected_nodes
            decisions['batch_sizes'] = {
                node_id: self.batch_controller.get_batch_size(node_id)
                for node_id in selected_nodes
            }
            
            logger.info(f"[ORCHESTRATOR] Pre-round complete: {len(selected_nodes)} nodes selected")
            
            return decisions
    
    def post_round_evaluation(
        self,
        round_number: int,
        round_metrics: Dict[str, Any]
    ):
        """
        Evaluate performance after a training round.
        
        Args:
            round_number: Round number
            round_metrics: Metrics from the round
        """
        with self.lock:
            logger.info(f"[ORCHESTRATOR] Post-round {round_number} evaluation")
            print(f"[ORCHESTRATOR] === Round {round_number} - Post-Round Evaluation ===")
            
            # Store metrics
            self.round_metrics.append({
                'round': round_number,
                'timestamp': time.time(),
                'metrics': round_metrics
            })
            
            # Keep only recent history
            if len(self.round_metrics) > 100:
                self.round_metrics = self.round_metrics[-100:]
            
            # Evaluate if current strategy is working
            is_improving = self._evaluate_performance_trend()
            
            print(f"[ORCHESTRATOR] Performance trend: {'Improving' if is_improving else 'Stable/Degrading'}")
            
            # Check if we should rollback recent adaptation
            if self.enable_rollback and not is_improving and self.adaptations_applied > 0:
                recent_adaptation = (round_number - self.last_adaptation_round) <= 5
                
                if recent_adaptation:
                    logger.warning("[ORCHESTRATOR] Performance degraded after adaptation, considering rollback...")
                    print("[ORCHESTRATOR] ⚠ Performance degraded, considering rollback...")
                    
                    # Simple rollback logic: if last 3 rounds worse than before
                    if len(self.round_metrics) >= 6:
                        self._maybe_rollback_adaptation()
            
            # Update phase if needed
            self._update_training_phase()
            
            # Log summary
            self._log_round_summary(round_metrics)
    
    def _should_adapt_this_round(self, round_number: int) -> bool:
        """
        Determine if we should adapt on this round.
        
        Args:
            round_number: Current round number
            
        Returns:
            True if should adapt
        """
        # Don't adapt during warmup
        if self.phase == TrainingPhase.WARMUP:
            return False
        
        # Don't adapt too frequently
        rounds_since_last = round_number - self.last_adaptation_round
        if rounds_since_last < self.adaptation_interval:
            return False
        
        # Policy-specific logic
        if self.adaptation_policy == AdaptationPolicy.CONSERVATIVE:
            # Only adapt if really needed
            if rounds_since_last < self.adaptation_interval * 2:
                return False
        
        elif self.adaptation_policy == AdaptationPolicy.AGGRESSIVE:
            # Adapt more frequently
            return True
        
        elif self.adaptation_policy == AdaptationPolicy.REACTIVE:
            # Adapt on schedule or when detecting issues
            network_issues = len(self.network_monitor.get_problematic_nodes()) > 0
            return network_issues or (rounds_since_last >= self.adaptation_interval)
        
        return True
    
    def _evaluate_performance_trend(self) -> bool:
        """
        Evaluate if performance is improving.
        
        Returns:
            True if improving, False otherwise
        """
        if len(self.round_metrics) < 5:
            return True  # Not enough data, assume improving
        
        # Compare recent metrics to older metrics
        recent_losses = []
        older_losses = []
        
        for i, record in enumerate(self.round_metrics[-10:]):
            loss = record['metrics'].get('average_loss', 0)
            
            if i < 5:
                older_losses.append(loss)
            else:
                recent_losses.append(loss)
        
        if not recent_losses or not older_losses:
            return True
        
        recent_avg = np.mean(recent_losses)
        older_avg = np.mean(older_losses)
        
        # For loss, lower is better
        is_improving = recent_avg < older_avg
        
        improvement_rate = (older_avg - recent_avg) / (older_avg + 1e-8)
        
        logger.debug(f"[ORCHESTRATOR] Performance: recent_loss={recent_avg:.4f}, "
                    f"older_loss={older_avg:.4f}, improvement={improvement_rate:.2%}")
        
        return is_improving or improvement_rate > -0.05  # Allow 5% tolerance
    
    def _maybe_rollback_adaptation(self):
        """Check if we should rollback the last adaptation."""
        if not self.configuration_history:
            logger.debug("[ORCHESTRATOR] No configuration history to rollback to")
            return
        
        # Compare last 3 rounds vs 3 rounds before adaptation
        if len(self.round_metrics) < 6:
            return
        
        pre_adaptation_rounds = self.round_metrics[-6:-3]
        post_adaptation_rounds = self.round_metrics[-3:]
        
        pre_avg_loss = np.mean([r['metrics'].get('average_loss', 0) for r in pre_adaptation_rounds])
        post_avg_loss = np.mean([r['metrics'].get('average_loss', 0) for r in post_adaptation_rounds])
        
        # If post-adaptation is >10% worse, rollback
        if post_avg_loss > pre_avg_loss * 1.1:
            logger.warning(f"[ORCHESTRATOR] Rolling back adaptation (loss: {pre_avg_loss:.4f} -> {post_avg_loss:.4f})")
            print(f"[ORCHESTRATOR] ↺ Rolling back adaptation (performance degraded by {((post_avg_loss/pre_avg_loss - 1) * 100):.1f}%)")
            
            # Restore previous configuration
            self._rollback_to_snapshot()
            
            self.adaptations_rolled_back += 1
    
    def _save_configuration_snapshot(self):
        """Save current configuration for potential rollback."""
        snapshot = {
            'timestamp': time.time(),
            'round': self.current_round,
            'batch_sizes': self.batch_controller.get_all_batch_sizes().copy(),
            'node_states': {
                node_id: self.node_selector.get_node_state(node_id)
                for node_id in self.node_selector.node_states.keys()
            }
        }
        
        self.configuration_history.append(snapshot)
        
        # Keep only recent history
        if len(self.configuration_history) > self.max_history:
            self.configuration_history = self.configuration_history[-self.max_history:]
        
        logger.debug(f"[ORCHESTRATOR] Configuration snapshot saved (round {self.current_round})")
    
    def _rollback_to_snapshot(self):
        """Rollback to previous configuration snapshot."""
        if len(self.configuration_history) < 2:
            logger.warning("[ORCHESTRATOR] Not enough history to rollback")
            return
        
        # Get previous snapshot (not the current one)
        snapshot = self.configuration_history[-2]
        
        # Restore batch sizes
        for node_id, batch_size in snapshot['batch_sizes'].items():
            self.batch_controller.set_batch_size(node_id, batch_size, reason="rollback")
        
        # Restore node states
        for node_id, state in snapshot['node_states'].items():
            if state == 'active':
                self.node_selector.force_include_node(node_id)
        
        logger.info(f"[ORCHESTRATOR] Rolled back to configuration from round {snapshot['round']}")
    
    def _update_training_phase(self):
        """Update training phase based on progress."""
        old_phase = self.phase
        
        if self.phase == TrainingPhase.WARMUP:
            if self.current_round >= self.warmup_rounds:
                self.phase = TrainingPhase.ADAPTIVE_TRAINING
                logger.info("[ORCHESTRATOR] Entering adaptive training phase")
                print("\n" + "=" * 80)
                print("[ORCHESTRATOR] ✓ Warmup complete - Entering Adaptive Training Phase")
                print("=" * 80 + "\n")
        
        elif self.phase == TrainingPhase.ADAPTIVE_TRAINING:
            # Check if approaching convergence (loss stabilized)
            if len(self.round_metrics) >= 20:
                recent_losses = [r['metrics'].get('average_loss', 0) for r in self.round_metrics[-20:]]
                loss_std = np.std(recent_losses)
                loss_mean = np.mean(recent_losses)
                
                # If coefficient of variation is low, we're converging
                if loss_std / (loss_mean + 1e-8) < 0.05:
                    self.phase = TrainingPhase.CONVERGENCE
                    logger.info("[ORCHESTRATOR] Entering convergence phase")
                    print("[ORCHESTRATOR] ℹ Entering convergence phase (loss stabilized)")
    
    def _log_round_summary(self, metrics: Dict[str, Any]):
        """Log summary of round metrics."""
        avg_loss = metrics.get('average_loss', 0)
        throughput = metrics.get('throughput', 0)
        nodes_participated = metrics.get('nodes_participated', 0)
        
        print(f"[ORCHESTRATOR] Round Summary:")
        print(f"  Loss: {avg_loss:.4f}")
        print(f"  Throughput: {throughput:.2f} samples/sec")
        print(f"  Nodes: {nodes_participated}")
        print(f"  Phase: {self.phase.value}")
    
    def get_orchestrator_status(self) -> Dict[str, Any]:
        """
        Get current orchestrator status.
        
        Returns:
            Dictionary with status information
        """
        with self.lock:
            return {
                'current_round': self.current_round,
                'current_epoch': self.current_epoch,
                'phase': self.phase.value,
                'adaptation_policy': self.adaptation_policy,
                'adaptations_applied': self.adaptations_applied,
                'adaptations_rolled_back': self.adaptations_rolled_back,
                'last_adaptation_round': self.last_adaptation_round,
                'rounds_since_adaptation': self.current_round - self.last_adaptation_round,
                'network_health': self.network_monitor.get_cluster_health_summary(),
                'batch_adaptation': self.batch_controller.get_adaptation_summary(),
                'node_selection': self.node_selector.get_selection_summary()
            }
    
    def get_performance_comparison(self) -> Dict[str, Any]:
        """
        Compare adaptive vs baseline performance.
        
        Returns:
            Dictionary with performance comparison
        """
        if len(self.round_metrics) < 10:
            return {
                'available': False,
                'message': 'Not enough data for comparison'
            }
        
        # Compare warmup (baseline) vs adaptive phases
        warmup_metrics = [
            r['metrics'] for r in self.round_metrics
            if r['round'] < self.warmup_rounds
        ]
        
        adaptive_metrics = [
            r['metrics'] for r in self.round_metrics
            if r['round'] >= self.warmup_rounds
        ]
        
        if not warmup_metrics or not adaptive_metrics:
            return {
                'available': False,
                'message': 'Need both warmup and adaptive data'
            }
        
        warmup_avg_loss = np.mean([m.get('average_loss', 0) for m in warmup_metrics])
        adaptive_avg_loss = np.mean([m.get('average_loss', 0) for m in adaptive_metrics])
        
        warmup_throughput = np.mean([m.get('throughput', 0) for m in warmup_metrics])
        adaptive_throughput = np.mean([m.get('throughput', 0) for m in adaptive_metrics])
        
        loss_improvement = (warmup_avg_loss - adaptive_avg_loss) / (warmup_avg_loss + 1e-8)
        throughput_improvement = (adaptive_throughput - warmup_throughput) / (warmup_throughput + 1e-8)
        
        return {
            'available': True,
            'warmup_phase': {
                'average_loss': warmup_avg_loss,
                'average_throughput': warmup_throughput,
                'rounds': len(warmup_metrics)
            },
            'adaptive_phase': {
                'average_loss': adaptive_avg_loss,
                'average_throughput': adaptive_throughput,
                'rounds': len(adaptive_metrics)
            },
            'improvements': {
                'loss_improvement': loss_improvement,
                'throughput_improvement': throughput_improvement
            }
        }
    
    def export_full_report(self) -> Dict[str, Any]:
        """
        Export comprehensive orchestration report.
        
        Returns:
            Dictionary with all orchestration data
        """
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'status': self.get_orchestrator_status(),
            'performance_comparison': self.get_performance_comparison(),
            'recent_rounds': self.round_metrics[-20:],
            'configuration_history': self.configuration_history,
            'component_exports': {
                'network_monitor': self.network_monitor.export_metrics(),
                'batch_controller': self.batch_controller.export_metrics(),
                'node_selector': self.node_selector.export_metrics()
            }
        }
    
    def shutdown(self):
        """Shutdown orchestrator and cleanup."""
        with self.lock:
            logger.info("[ORCHESTRATOR] Shutting down...")
            print("\n[ORCHESTRATOR] Shutting down adaptive orchestrator...")
            
            # Stop monitoring
            self.network_monitor.stop_monitoring()
            
            # Export final report
            final_report = self.export_full_report()
            
            logger.info("[ORCHESTRATOR] Final statistics:")
            logger.info(f"  Total rounds: {self.current_round}")
            logger.info(f"  Adaptations applied: {self.adaptations_applied}")
            logger.info(f"  Adaptations rolled back: {self.adaptations_rolled_back}")
            
            print(f"[ORCHESTRATOR] ✓ Shutdown complete")
            print(f"  Total rounds: {self.current_round}")
            print(f"  Adaptations: {self.adaptations_applied} applied, {self.adaptations_rolled_back} rolled back")
            
            self.phase = TrainingPhase.COMPLETED
