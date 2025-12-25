"""
Training Coordinator - Central orchestrator for distributed training.

This is the brain of the system that manages the lifecycle of training jobs,
maintains state about all GPU nodes, handles data distribution, and coordinates
gradient aggregation.
"""

import threading
import signal
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime
import pickle
from pathlib import Path

from ..models.config import SystemConfig, TrainingConfig
from ..models.node import NodeMetadata, NodeStatus, NodeRegistry
from ..models.metrics import TrainingMetrics, AggregatedMetrics, NetworkMetrics
from ..utils.logger import get_logger
from .blockchain_integrator import BlockchainIntegrator

logger = get_logger(__name__)


class TrainingCoordinator:
    """
    Central coordinator service that orchestrates distributed training.
    
    Responsibilities:
    - Manage the lifecycle of training jobs
    - Maintain state about all GPU nodes
    - Handle data distribution coordination
    - Coordinate gradient aggregation
    - Track training progress and metrics
    """
    
    def __init__(self, config: SystemConfig):
        """
        Initialize the training coordinator.
        
        Args:
            config: System configuration including training, network, and blockchain settings
        """
        self.config = config
        self.training_config = config.training
        
        # State management
        self.node_registry = NodeRegistry(nodes={})
        self.global_model_parameters: Optional[Dict[str, Any]] = None
        self.current_epoch = 0
        self.current_step = 0
        self.total_steps = 0
        self.is_training = False
        self.is_initialized = False
        
        # Metrics tracking
        self.metrics_history: List[AggregatedMetrics] = []
        
        # Node health tracking
        self.node_health: Dict[str, Dict[str, Any]] = {}
        self.pending_gradients: Dict[str, Any] = {}
        self.node_performance: Dict[str, List[float]] = {}
        
        # Blockchain integration (Phase 5)
        self.blockchain_integrator: Optional[BlockchainIntegrator] = None
        if config.blockchain.enabled:
            logger.info("[Coordinator] Blockchain integration enabled")
            self.blockchain_integrator = BlockchainIntegrator(
                config.blockchain,
                session_prefix="training"
            )
        else:
            logger.info("[Coordinator] Blockchain integration disabled")
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Graceful shutdown setup
        self.shutdown_requested = False
        signal.signal(signal.SIGINT, self._shutdown_handler)
        signal.signal(signal.SIGTERM, self._shutdown_handler)
        
        logger.info(f"Training Coordinator initialized with config: {config.model_dump_json()}")
    
    def initialize_training(self, model_params: Optional[Dict[str, Any]] = None) -> bool:
        """
        Initialize the training session.
        
        Loads the model, prepares dataset splits, and sets up the training environment.
        
        Args:
            model_params: Optional pre-initialized model parameters
            
        Returns:
            bool: True if initialization successful, False otherwise
        """
        with self.lock:
            try:
                logger.info("Initializing training session...")
                
                # Initialize blockchain if enabled
                if self.blockchain_integrator:
                    logger.info("[Coordinator] Initializing blockchain integration...")
                    if not self.blockchain_integrator.initialize():
                        logger.error("[Coordinator] Blockchain initialization failed")
                        if self.config.blockchain.enabled:
                            # Blockchain is required, fail initialization
                            return False
                        else:
                            # Blockchain is optional, continue
                            self.blockchain_integrator = None
                
                # Set global model parameters
                if model_params is not None:
                    self.global_model_parameters = model_params
                else:
                    # Will be set by ModelManager
                    self.global_model_parameters = {}
                
                # Calculate total training steps
                steps_per_epoch = self.training_config.steps_per_epoch
                if steps_per_epoch is None:
                    steps_per_epoch = 10  # Default fallback
                
                self.total_steps = self.training_config.epochs * steps_per_epoch
                
                # Reset training state
                self.current_epoch = 0
                self.current_step = 0
                self.metrics_history = []
                self.pending_gradients = {}
                
                self.is_initialized = True
                self.is_training = False
                
                # Start blockchain session
                if self.blockchain_integrator:
                    logger.info("[Coordinator] Starting blockchain session...")
                    model_name = self.training_config.model_architecture.value
                    if not self.blockchain_integrator.start_session(model_name):
                        logger.error("[Coordinator] Failed to start blockchain session")
                        if self.config.blockchain.enabled:
                            return False
                
                logger.info(f"Training initialized: {self.total_steps} total steps planned")
                return True
                
            except Exception as e:
                logger.error(f"Failed to initialize training: {e}", exc_info=True)
                return False
    
    def register_node(self, node_metadata: NodeMetadata) -> bool:
        """
        Register a new GPU node to the training pool.
        
        Args:
            node_metadata: Metadata about the node to register
            
        Returns:
            bool: True if registration successful, False otherwise
        """
        with self.lock:
            try:
                # Check if node already exists
                existing_node = self.node_registry.get_node(node_metadata.node_id)
                if existing_node is not None:
                    logger.warning(f"Node {node_metadata.node_id} already registered, updating...")
                    return self.node_registry.update_node(node_metadata)
                
                # Add new node
                success = self.node_registry.add_node(node_metadata)
                
                if success:
                    # Initialize health tracking
                    self.node_health[node_metadata.node_id] = {
                        "last_heartbeat": datetime.now(),
                        "consecutive_failures": 0,
                        "total_heartbeats": 0,
                        "status": NodeStatus.READY
                    }
                    
                    # Initialize performance tracking
                    self.node_performance[node_metadata.node_id] = []
                    
                    # Register node with blockchain
                    if self.blockchain_integrator:
                        logger.info(f"[Coordinator] Registering node on blockchain: {node_metadata.node_id}")
                        self.blockchain_integrator.register_node(
                            node_metadata.node_id,
                            node_metadata.node_address
                        )
                    
                    logger.info(
                        f"Node registered: {node_metadata.node_id} "
                        f"({node_metadata.node_address}) - "
                        f"GPU: {node_metadata.gpu_model} ({node_metadata.gpu_memory_gb}GB)"
                    )
                    logger.info(f"Total active nodes: {self.node_registry.count_active_nodes()}")
                else:
                    logger.error(f"Failed to register node: {node_metadata.node_id}")
                
                return success
                
            except Exception as e:
                logger.error(f"Error registering node {node_metadata.node_id}: {e}", exc_info=True)
                return False
    
    def remove_node(self, node_id: str, reason: str = "unknown") -> bool:
        """
        Remove a node from the training pool.
        
        Handles node disconnection or failure gracefully.
        
        Args:
            node_id: ID of the node to remove
            reason: Reason for removal (for logging)
            
        Returns:
            bool: True if removal successful, False otherwise
        """
        with self.lock:
            try:
                success = self.node_registry.remove_node(node_id)
                
                if success:
                    # Clean up node state
                    if node_id in self.node_health:
                        del self.node_health[node_id]
                    
                    if node_id in self.pending_gradients:
                        del self.pending_gradients[node_id]
                    
                    # Keep performance history for analysis
                    
                    logger.warning(
                        f"Node removed: {node_id} (reason: {reason}) - "
                        f"Remaining nodes: {self.node_registry.count_active_nodes()}"
                    )
                else:
                    logger.error(f"Failed to remove node: {node_id}")
                
                return success
                
            except Exception as e:
                logger.error(f"Error removing node {node_id}: {e}", exc_info=True)
                return False
    
    def update_node_heartbeat(self, node_id: str) -> bool:
        """
        Update the last heartbeat time for a node.
        
        Args:
            node_id: ID of the node
            
        Returns:
            bool: True if update successful
        """
        with self.lock:
            if node_id not in self.node_health:
                logger.warning(f"Heartbeat from unknown node: {node_id}")
                return False
            
            self.node_health[node_id]["last_heartbeat"] = datetime.now()
            self.node_health[node_id]["total_heartbeats"] += 1
            self.node_health[node_id]["consecutive_failures"] = 0
            
            return True
    
    def record_node_failure(self, node_id: str) -> None:
        """
        Record a failure for a node.
        
        Args:
            node_id: ID of the failed node
        """
        with self.lock:
            if node_id in self.node_health:
                self.node_health[node_id]["consecutive_failures"] += 1
                failures = self.node_health[node_id]["consecutive_failures"]
                
                logger.warning(f"Node {node_id} failure recorded (consecutive: {failures})")
                
                # Auto-remove if too many failures
                max_failures = 5
                if failures >= max_failures:
                    logger.error(
                        f"Node {node_id} exceeded max failures ({max_failures}), removing..."
                    )
                    self.remove_node(node_id, reason=f"exceeded {max_failures} consecutive failures")
    
    def record_node_performance(self, node_id: str, performance_score: float) -> None:
        """
        Record performance metrics for a node.
        
        Args:
            node_id: ID of the node
            performance_score: Performance score (e.g., samples/second)
        """
        with self.lock:
            if node_id not in self.node_performance:
                self.node_performance[node_id] = []
            
            self.node_performance[node_id].append(performance_score)
            
            # Keep only recent history (last 100 measurements)
            if len(self.node_performance[node_id]) > 100:
                self.node_performance[node_id] = self.node_performance[node_id][-100:]
    
    def get_training_status(self) -> Dict[str, Any]:
        """
        Get current training status as a dictionary.
        
        Returns:
            Dict containing current training state
        """
        with self.lock:
            return {
                "is_initialized": self.is_initialized,
                "is_training": self.is_training,
                "current_epoch": self.current_epoch,
                "current_step": self.current_step,
                "total_steps": self.total_steps,
                "progress_percentage": (
                    (self.current_step / self.total_steps * 100) 
                    if self.total_steps > 0 else 0
                ),
                "active_nodes": self.node_registry.count_active_nodes(),
                "total_registered_nodes": len(self.node_registry.nodes),
                "pending_gradients": len(self.pending_gradients),
                "metrics_history_length": len(self.metrics_history),
                "has_global_model": self.global_model_parameters is not None,
            }
    
    def get_node_health_summary(self) -> Dict[str, Any]:
        """
        Get summary of node health status.
        
        Returns:
            Dict with node health information
        """
        with self.lock:
            healthy_nodes = 0
            degraded_nodes = 0
            offline_nodes = 0
            
            for node_id, health in self.node_health.items():
                failures = health.get("consecutive_failures", 0)
                if failures == 0:
                    healthy_nodes += 1
                elif failures < 3:
                    degraded_nodes += 1
                else:
                    offline_nodes += 1
            
            return {
                "healthy_nodes": healthy_nodes,
                "degraded_nodes": degraded_nodes,
                "offline_nodes": offline_nodes,
                "total_tracked_nodes": len(self.node_health),
            }
    
    def advance_step(self) -> None:
        """Advance to the next training step."""
        with self.lock:
            self.current_step += 1
            
            # Check if epoch completed
            if self.current_step > 0 and self.current_step % self.training_config.steps_per_epoch == 0:
                self.current_epoch += 1
                logger.info(f"Epoch {self.current_epoch} completed")
    
    def add_metrics(self, metrics: AggregatedMetrics) -> None:
        """
        Add aggregated metrics to history.
        
        Args:
            metrics: Aggregated metrics from a training round
        """
        with self.lock:
            self.metrics_history.append(metrics)
            
            # Keep only recent history (last 1000 entries)
            if len(self.metrics_history) > 1000:
                self.metrics_history = self.metrics_history[-1000:]
    
    def save_state(self, checkpoint_dir: str = "checkpoints") -> bool:
        """
        Save current coordinator state to disk.
        
        Args:
            checkpoint_dir: Directory to save checkpoint
            
        Returns:
            bool: True if save successful
        """
        with self.lock:
            try:
                checkpoint_path = Path(checkpoint_dir)
                checkpoint_path.mkdir(parents=True, exist_ok=True)
                
                state = {
                    "current_epoch": self.current_epoch,
                    "current_step": self.current_step,
                    "total_steps": self.total_steps,
                    "is_training": self.is_training,
                    "is_initialized": self.is_initialized,
                    "node_registry": self.node_registry.model_dump(),
                    "node_health": self.node_health,
                    "node_performance": self.node_performance,
                    "metrics_history": [m.model_dump() for m in self.metrics_history],
                    "timestamp": datetime.now().isoformat(),
                }
                
                checkpoint_file = checkpoint_path / f"coordinator_state_epoch_{self.current_epoch}.pkl"
                with open(checkpoint_file, "wb") as f:
                    pickle.dump(state, f)
                
                logger.info(f"Coordinator state saved to {checkpoint_file}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to save coordinator state: {e}", exc_info=True)
                return False
    
    def load_state(self, checkpoint_file: str) -> bool:
        """
        Load coordinator state from disk.
        
        Args:
            checkpoint_file: Path to checkpoint file
            
        Returns:
            bool: True if load successful
        """
        with self.lock:
            try:
                with open(checkpoint_file, "rb") as f:
                    state = pickle.load(f)
                
                self.current_epoch = state["current_epoch"]
                self.current_step = state["current_step"]
                self.total_steps = state["total_steps"]
                self.is_training = state["is_training"]
                self.is_initialized = state["is_initialized"]
                self.node_registry = NodeRegistry(**state["node_registry"])
                self.node_health = state["node_health"]
                self.node_performance = state["node_performance"]
                self.metrics_history = [
                    AggregatedMetrics(**m) for m in state["metrics_history"]
                ]
                
                logger.info(f"Coordinator state loaded from {checkpoint_file}")
                logger.info(f"Resumed at epoch {self.current_epoch}, step {self.current_step}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to load coordinator state: {e}", exc_info=True)
                return False
    
    def _shutdown_handler(self, signum, frame):
        """Handle graceful shutdown on signals."""
        logger.info(f"Shutdown signal received (signal {signum})")
        self.shutdown_requested = True
        
        # Complete blockchain session if active
        if self.blockchain_integrator and self.blockchain_integrator.session_started:
            logger.info("[Coordinator] Completing blockchain session before shutdown...")
            try:
                self.blockchain_integrator.complete_session_and_distribute_rewards()
            except Exception as e:
                logger.error(f"[Coordinator] Error completing blockchain session: {e}")
        
        # Save state before exit
        logger.info("Saving coordinator state before shutdown...")
        self.save_state()
        
        # Shutdown blockchain integrator
        if self.blockchain_integrator:
            self.blockchain_integrator.shutdown()
        
        logger.info("Coordinator shutdown complete")
        sys.exit(0)
    
    # ==================== Blockchain Integration Methods ====================
    
    def record_training_metrics_blockchain(self, metrics: TrainingMetrics):
        """
        Record training metrics for blockchain contribution tracking.
        
        Args:
            metrics: Training metrics from a node
        """
        if self.blockchain_integrator:
            try:
                self.blockchain_integrator.record_training_metrics(metrics)
                logger.debug(f"[Coordinator] Recorded training metrics to blockchain: {metrics.node_id}")
            except Exception as e:
                logger.error(f"[Coordinator] Error recording training metrics: {e}")
    
    def record_network_metrics_blockchain(self, metrics: NetworkMetrics):
        """
        Record network metrics for blockchain contribution tracking.
        
        Args:
            metrics: Network metrics from a node
        """
        if self.blockchain_integrator:
            try:
                self.blockchain_integrator.record_network_metrics(metrics)
                logger.debug(f"[Coordinator] Recorded network metrics to blockchain: {metrics.node_id}")
            except Exception as e:
                logger.error(f"[Coordinator] Error recording network metrics: {e}")
    
    def record_gradient_submission_blockchain(self, node_id: str, accepted: bool, 
                                            gradient_norm: Optional[float] = None):
        """
        Record gradient submission result for blockchain tracking.
        
        Args:
            node_id: Node identifier
            accepted: Whether gradient was accepted
            gradient_norm: L2 norm of gradient
        """
        if self.blockchain_integrator:
            try:
                self.blockchain_integrator.record_gradient_submission(node_id, accepted, gradient_norm)
                logger.debug(f"[Coordinator] Recorded gradient submission: {node_id} accepted={accepted}")
            except Exception as e:
                logger.error(f"[Coordinator] Error recording gradient submission: {e}")
    
    def complete_epoch_blockchain(self, epoch: int) -> bool:
        """
        Complete epoch and submit contributions to blockchain.
        
        Args:
            epoch: Epoch number
            
        Returns:
            True if successful
        """
        if self.blockchain_integrator:
            try:
                logger.info(f"[Coordinator] Completing epoch {epoch} on blockchain...")
                return self.blockchain_integrator.submit_epoch_contributions(epoch)
            except Exception as e:
                logger.error(f"[Coordinator] Error completing epoch on blockchain: {e}")
                return False
        return True
    
    def complete_training_blockchain(self) -> bool:
        """
        Complete training session and distribute rewards on blockchain.
        
        Returns:
            True if successful
        """
        if self.blockchain_integrator:
            try:
                logger.info("[Coordinator] Completing training session on blockchain...")
                return self.blockchain_integrator.complete_session_and_distribute_rewards()
            except Exception as e:
                logger.error(f"[Coordinator] Error completing training on blockchain: {e}")
                return False
        return True
    
    def get_blockchain_contribution_summary(self):
        """Get blockchain contribution summary."""
        if self.blockchain_integrator:
            return self.blockchain_integrator.get_contribution_summary()
        return None
    
    def __repr__(self) -> str:
        """String representation of coordinator."""
        status = self.get_training_status()
        blockchain_status = "enabled" if self.blockchain_integrator else "disabled"
        return (
            f"TrainingCoordinator("
            f"epoch={status['current_epoch']}, "
            f"step={status['current_step']}, "
            f"nodes={status['active_nodes']}, "
            f"training={status['is_training']}, "
            f"blockchain={blockchain_status})"
        )
