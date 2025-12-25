"""
Blockchain Integration Module - Connects Phase 5 components with the training coordinator.

This module provides the BlockchainIntegrator class that manages:
- Session registration on blockchain
- Contribution tracking
- Reward calculation and distribution
- Integration with training coordinator
"""

from typing import Dict, List, Optional
from pathlib import Path
import uuid
from datetime import datetime

from .monad_client import MonadClient
from .contribution_calculator import ContributionCalculator, NodeContribution
from .reward_calculator import RewardCalculator, RewardStrategy, RewardDistribution
from ..models.config import BlockchainConfig
from ..models.metrics import TrainingMetrics, NetworkMetrics
from ..utils.logger import get_logger

logger = get_logger(__name__)


class BlockchainIntegrator:
    """
    Integrates blockchain functionality with distributed training.
    
    Responsibilities:
    - Manage training session on blockchain
    - Track node contributions
    - Calculate and distribute rewards
    - Handle blockchain interactions asynchronously
    """
    
    def __init__(self, config: BlockchainConfig, session_prefix: str = "training"):
        """
        Initialize blockchain integrator.
        
        Args:
            config: Blockchain configuration
            session_prefix: Prefix for session IDs
        """
        self.config = config
        self.session_prefix = session_prefix
        self.session_id: Optional[str] = None
        self.session_hash: Optional[str] = None
        
        # Components
        self.monad_client: Optional[MonadClient] = None
        self.contrib_calculator: Optional[ContributionCalculator] = None
        self.reward_calculator: Optional[RewardCalculator] = None
        
        # State
        self.is_initialized = False
        self.session_started = False
        self.session_completed = False
        
        # Node tracking
        self.registered_nodes: Dict[str, str] = {}  # node_id -> address
        
        logger.info("[BlockchainIntegrator] Initialized")
    
    def initialize(self) -> bool:
        """
        Initialize blockchain client and components.
        
        Returns:
            True if initialization successful
        """
        if not self.config.enabled:
            logger.info("[BlockchainIntegrator] Blockchain disabled, skipping initialization")
            return True
        
        try:
            logger.info("[BlockchainIntegrator] Initializing blockchain client...")
            
            # Validate configuration
            if not self.config.private_key:
                logger.error("[BlockchainIntegrator] No private key provided")
                return False
            
            if not all([
                self.config.training_registry_address,
                self.config.contribution_tracker_address,
                self.config.reward_distributor_address
            ]):
                logger.error("[BlockchainIntegrator] Contract addresses not configured")
                logger.info("[BlockchainIntegrator] Please deploy contracts and update config")
                return False
            
            # Setup contract addresses
            contract_addresses = {
                'TrainingRegistry': self.config.training_registry_address,
                'ContributionTracker': self.config.contribution_tracker_address,
                'RewardDistributor': self.config.reward_distributor_address
            }
            
            # Setup ABI directory
            abi_dir = Path(self.config.abi_directory).resolve()
            logger.debug(f"[BlockchainIntegrator] ABI directory: {abi_dir}")
            
            # Initialize Monad client
            self.monad_client = MonadClient(
                config=self.config,
                contract_addresses=contract_addresses,
                abi_dir=abi_dir
            )
            
            # Check balance
            balance = self.monad_client.get_balance()
            logger.info(f"[BlockchainIntegrator] Account balance: {balance} wei ({balance/1e18:.4f} ETH)")
            
            if balance == 0:
                logger.warning("[BlockchainIntegrator] Account has zero balance!")
            
            self.is_initialized = True
            logger.info("[BlockchainIntegrator] Initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"[BlockchainIntegrator] Initialization failed: {e}")
            return False
    
    def start_session(self, model_name: str = "distributed_model") -> bool:
        """
        Start a new training session on blockchain.
        
        Args:
            model_name: Name/type of model being trained
            
        Returns:
            True if session started successfully
        """
        if not self.config.enabled or not self.is_initialized:
            logger.info("[BlockchainIntegrator] Blockchain disabled or not initialized")
            return True
        
        try:
            # Generate unique session ID
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            self.session_id = f"{self.session_prefix}_{timestamp}_{unique_id}"
            
            logger.info(f"[BlockchainIntegrator] Starting session: {self.session_id}")
            
            # Create model hash
            self.session_hash = f"{model_name}_{timestamp}"
            
            # Initialize contribution calculator
            self.contrib_calculator = ContributionCalculator(self.session_id)
            
            # Create session on blockchain
            logger.info("[BlockchainIntegrator] Creating session on blockchain...")
            tx_hash = self.monad_client.create_session(self.session_id, self.session_hash)
            
            if tx_hash:
                logger.info(f"[BlockchainIntegrator] Session created on-chain: {tx_hash}")
                self.session_started = True
                return True
            else:
                logger.error("[BlockchainIntegrator] Failed to create session on blockchain")
                return False
                
        except Exception as e:
            logger.error(f"[BlockchainIntegrator] Error starting session: {e}")
            return False
    
    def register_node(self, node_id: str, node_address: str) -> bool:
        """
        Register a node for the training session.
        
        Args:
            node_id: Node identifier
            node_address: Ethereum address of the node
            
        Returns:
            True if registration successful
        """
        if not self.config.enabled or not self.session_started:
            return True
        
        try:
            logger.info(f"[BlockchainIntegrator] Registering node: {node_id} -> {node_address}")
            
            # Register with contribution calculator
            self.contrib_calculator.register_node(node_id, node_address)
            
            # Track registered nodes
            self.registered_nodes[node_id] = node_address
            
            # Register on blockchain (async if enabled)
            if self.config.enable_async_transactions:
                self.monad_client.register_node(
                    self.session_id, 
                    node_address, 
                    node_id
                )
            else:
                tx_hash = self.monad_client.register_node(
                    self.session_id,
                    node_address,
                    node_id
                )
                
                if tx_hash:
                    logger.info(f"[BlockchainIntegrator] Node registered on-chain: {tx_hash}")
                else:
                    logger.warning(f"[BlockchainIntegrator] Failed to register node on-chain: {node_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"[BlockchainIntegrator] Error registering node: {e}")
            return False
    
    def register_nodes_batch(self, nodes: List[tuple]) -> bool:
        """
        Register multiple nodes in batch.
        
        Args:
            nodes: List of (node_id, node_address) tuples
            
        Returns:
            True if registration successful
        """
        if not self.config.enabled or not self.session_started:
            return True
        
        try:
            logger.info(f"[BlockchainIntegrator] Batch registering {len(nodes)} nodes")
            
            # Register with contribution calculator
            for node_id, node_address in nodes:
                self.contrib_calculator.register_node(node_id, node_address)
                self.registered_nodes[node_id] = node_address
            
            # Register on blockchain
            tx_hash = self.monad_client.register_nodes_batch(self.session_id, nodes)
            
            if tx_hash:
                logger.info(f"[BlockchainIntegrator] Batch registration on-chain: {tx_hash}")
                return True
            else:
                logger.warning("[BlockchainIntegrator] Batch registration failed")
                return False
                
        except Exception as e:
            logger.error(f"[BlockchainIntegrator] Error in batch registration: {e}")
            return False
    
    def record_training_metrics(self, metrics: TrainingMetrics):
        """
        Record training metrics for contribution calculation.
        
        Args:
            metrics: Training metrics from a node
        """
        if not self.config.enabled or not self.contrib_calculator:
            return
        
        try:
            self.contrib_calculator.add_training_metrics(metrics)
            logger.debug(f"[BlockchainIntegrator] Recorded training metrics: {metrics.node_id}")
        except Exception as e:
            logger.error(f"[BlockchainIntegrator] Error recording training metrics: {e}")
    
    def record_network_metrics(self, metrics: NetworkMetrics):
        """
        Record network metrics for contribution calculation.
        
        Args:
            metrics: Network metrics from a node
        """
        if not self.config.enabled or not self.contrib_calculator:
            return
        
        try:
            self.contrib_calculator.add_network_metrics(metrics)
            logger.debug(f"[BlockchainIntegrator] Recorded network metrics: {metrics.node_id}")
        except Exception as e:
            logger.error(f"[BlockchainIntegrator] Error recording network metrics: {e}")
    
    def record_gradient_submission(self, node_id: str, accepted: bool, 
                                  gradient_norm: Optional[float] = None):
        """
        Record a gradient submission result.
        
        Args:
            node_id: Node identifier
            accepted: Whether gradient was accepted
            gradient_norm: L2 norm of gradient (if available)
        """
        if not self.config.enabled or not self.contrib_calculator:
            return
        
        try:
            self.contrib_calculator.record_gradient_submission(node_id, accepted, gradient_norm)
            logger.debug(f"[BlockchainIntegrator] Recorded gradient: {node_id} accepted={accepted}")
        except Exception as e:
            logger.error(f"[BlockchainIntegrator] Error recording gradient: {e}")
    
    def submit_epoch_contributions(self, epoch: int) -> bool:
        """
        Submit contributions to blockchain after an epoch.
        
        Args:
            epoch: Epoch number
            
        Returns:
            True if submission successful
        """
        if not self.config.enabled or not self.config.record_per_epoch:
            return True
        
        if not self.contrib_calculator:
            logger.warning("[BlockchainIntegrator] Contribution calculator not initialized")
            return False
        
        try:
            logger.info(f"[BlockchainIntegrator] Submitting epoch {epoch} contributions to blockchain...")
            
            # Update scores
            self.contrib_calculator.update_all_scores()
            
            # Format for blockchain
            contributions = self.contrib_calculator.format_for_blockchain()
            
            if not contributions:
                logger.warning("[BlockchainIntegrator] No contributions to submit")
                return True
            
            logger.info(f"[BlockchainIntegrator] Submitting {len(contributions)} contributions")
            
            # Submit in batches
            batch_size = self.config.batch_size
            
            for i in range(0, len(contributions), batch_size):
                batch = contributions[i:i+batch_size]
                
                logger.debug(f"[BlockchainIntegrator] Submitting batch {i//batch_size + 1} "
                           f"({len(batch)} contributions)")
                
                if self.config.enable_async_transactions:
                    self.monad_client.record_contributions_batch_async(self.session_id, batch)
                else:
                    tx_hash = self.monad_client.record_contributions_batch(self.session_id, batch)
                    
                    if tx_hash:
                        logger.info(f"[BlockchainIntegrator] Batch submitted: {tx_hash}")
                    else:
                        logger.error(f"[BlockchainIntegrator] Batch submission failed")
                        return False
            
            logger.info(f"[BlockchainIntegrator] Epoch {epoch} contributions submitted successfully")
            return True
            
        except Exception as e:
            logger.error(f"[BlockchainIntegrator] Error submitting contributions: {e}")
            return False
    
    def complete_session_and_distribute_rewards(self) -> bool:
        """
        Complete training session and calculate/distribute rewards.
        
        Returns:
            True if completion successful
        """
        if not self.config.enabled or not self.session_started:
            return True
        
        try:
            logger.info("[BlockchainIntegrator] Completing session and distributing rewards...")
            
            # Update all scores one final time
            self.contrib_calculator.update_all_scores()
            
            # Get final contributions
            contributions = self.contrib_calculator.get_all_contributions()
            
            if not contributions:
                logger.warning("[BlockchainIntegrator] No contributions to reward")
                return True
            
            # Get summary for logging
            summary = self.contrib_calculator.get_summary()
            logger.info(f"[BlockchainIntegrator] Session summary:")
            logger.info(f"  - Participants: {summary.participant_count}")
            logger.info(f"  - Total compute time: {summary.total_compute_time:.2f}s")
            logger.info(f"  - Total gradients: {summary.total_gradients}")
            logger.info(f"  - Avg quality score: {summary.avg_quality_score:.2f}")
            logger.info(f"  - Avg reliability score: {summary.avg_reliability_score:.2f}")
            
            if summary.outlier_nodes:
                logger.warning(f"  - Outliers detected: {summary.outlier_nodes}")
            
            # Mark session as complete on blockchain
            logger.info("[BlockchainIntegrator] Marking session complete on blockchain...")
            tx_hash = self.monad_client.complete_session(self.session_id)
            
            if not tx_hash:
                logger.error("[BlockchainIntegrator] Failed to complete session on blockchain")
                return False
            
            logger.info(f"[BlockchainIntegrator] Session completed on-chain: {tx_hash}")
            
            # Calculate rewards
            reward_pool_wei = int(self.config.total_reward_pool_eth * 1e18)
            
            logger.info(f"[BlockchainIntegrator] Calculating rewards with pool: "
                       f"{self.config.total_reward_pool_eth} ETH ({reward_pool_wei} wei)")
            
            self.reward_calculator = RewardCalculator(self.session_id, reward_pool_wei)
            
            strategy = RewardStrategy(self.config.reward_strategy)
            logger.info(f"[BlockchainIntegrator] Using reward strategy: {strategy.name}")
            
            distribution = self.reward_calculator.calculate(contributions, strategy)
            
            # Log reward distribution
            logger.info(f"[BlockchainIntegrator] Reward distribution calculated:")
            logger.info(f"  - Strategy: {distribution.strategy.name}")
            logger.info(f"  - Total distributed: {distribution.total_distributed} wei")
            logger.info(f"  - Min reward: {distribution.min_reward} wei")
            logger.info(f"  - Max reward: {distribution.max_reward} wei")
            logger.info(f"  - Avg reward: {distribution.avg_reward:.2f} wei")
            
            for node_id, reward in distribution.node_rewards.items():
                logger.info(f"  - {node_id}: {reward.total_reward} wei "
                          f"({reward.contribution_percentage:.2f}%)")
            
            # Create reward pool on blockchain
            logger.info("[BlockchainIntegrator] Creating reward pool on blockchain...")
            tx_hash = self.monad_client.create_reward_pool(
                self.session_id,
                reward_pool_wei,
                strategy.value
            )
            
            if not tx_hash:
                logger.error("[BlockchainIntegrator] Failed to create reward pool")
                return False
            
            logger.info(f"[BlockchainIntegrator] Reward pool created: {tx_hash}")
            
            # Submit rewards to blockchain
            logger.info("[BlockchainIntegrator] Submitting rewards to blockchain...")
            addresses, amounts = self.reward_calculator.format_for_blockchain(distribution)
            
            tx_hash = self.monad_client.calculate_rewards_proportional(
                self.session_id,
                addresses,
                amounts
            )
            
            if not tx_hash:
                logger.error("[BlockchainIntegrator] Failed to submit rewards")
                return False
            
            logger.info(f"[BlockchainIntegrator] Rewards submitted: {tx_hash}")
            
            self.session_completed = True
            logger.info("[BlockchainIntegrator] Session completion and reward distribution successful!")
            
            # Log claim instructions
            logger.info("[BlockchainIntegrator] Nodes can now claim their rewards using their addresses")
            
            return True
            
        except Exception as e:
            logger.error(f"[BlockchainIntegrator] Error completing session: {e}")
            return False
    
    def get_contribution_summary(self):
        """Get contribution summary for the session."""
        if not self.contrib_calculator:
            return None
        
        return self.contrib_calculator.get_summary()
    
    def shutdown(self):
        """Shutdown blockchain integrator and cleanup."""
        logger.info("[BlockchainIntegrator] Shutting down...")
        
        if self.monad_client:
            self.monad_client.shutdown()
        
        logger.info("[BlockchainIntegrator] Shutdown complete")
