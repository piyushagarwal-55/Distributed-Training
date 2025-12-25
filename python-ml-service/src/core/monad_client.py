"""
Monad Blockchain Client - Interfaces with smart contracts for distributed ML training.

This module provides the MonadClient class for interacting with deployed smart contracts
on the Monad blockchain, including transaction management, error handling, and caching.
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from web3 import Web3
from web3.contract import Contract
from web3.exceptions import ContractLogicError, TransactionNotFound
from eth_account import Account
from eth_account.signers.local import LocalAccount
import threading
from queue import Queue
from datetime import datetime, timedelta

from ..models.config import BlockchainConfig
from ..utils.logger import get_logger

logger = get_logger(__name__)


class TransactionManager:
    """Manages transaction nonces and retries."""
    
    def __init__(self, web3: Web3, account: LocalAccount):
        self.web3 = web3
        self.account = account
        self.nonce_lock = threading.Lock()
        self._nonce: Optional[int] = None
        self._last_nonce_update = 0
        
    def get_nonce(self, force_refresh: bool = False) -> int:
        """Get the next transaction nonce with caching."""
        with self.nonce_lock:
            current_time = time.time()
            
            # Refresh nonce if forced or cache is stale (>30 seconds)
            if force_refresh or self._nonce is None or (current_time - self._last_nonce_update) > 30:
                self._nonce = self.web3.eth.get_transaction_count(self.account.address)
                self._last_nonce_update = current_time
                logger.debug(f"[TxManager] Refreshed nonce: {self._nonce}")
            
            nonce = self._nonce
            self._nonce += 1
            return nonce
    
    def reset_nonce(self):
        """Force nonce reset on next transaction."""
        with self.nonce_lock:
            self._nonce = None
            logger.debug("[TxManager] Nonce cache cleared")


class TransactionQueue:
    """Async queue for processing blockchain transactions."""
    
    def __init__(self, client: 'MonadClient'):
        self.client = client
        self.queue: Queue = Queue()
        self.worker_thread: Optional[threading.Thread] = None
        self.is_running = False
        
    def start(self):
        """Start the background worker."""
        if not self.is_running:
            self.is_running = True
            self.worker_thread = threading.Thread(target=self._worker, daemon=True)
            self.worker_thread.start()
            logger.info("[TxQueue] Transaction queue worker started")
    
    def stop(self):
        """Stop the background worker."""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
            logger.info("[TxQueue] Transaction queue worker stopped")
    
    def enqueue(self, func, *args, **kwargs):
        """Add a transaction to the queue."""
        self.queue.put((func, args, kwargs))
        logger.debug(f"[TxQueue] Enqueued transaction: {func.__name__}")
    
    def _worker(self):
        """Background worker that processes queued transactions."""
        logger.info("[TxQueue] Worker thread running")
        
        while self.is_running:
            try:
                if not self.queue.empty():
                    func, args, kwargs = self.queue.get(timeout=1)
                    
                    try:
                        logger.debug(f"[TxQueue] Processing: {func.__name__}")
                        result = func(*args, **kwargs)
                        logger.debug(f"[TxQueue] Completed: {func.__name__} -> {result}")
                    except Exception as e:
                        logger.error(f"[TxQueue] Error in {func.__name__}: {e}")
                    finally:
                        self.queue.task_done()
                else:
                    time.sleep(0.5)
            except Exception as e:
                logger.error(f"[TxQueue] Worker error: {e}")
                time.sleep(1)


class MonadClient:
    """
    Client for interacting with Monad blockchain smart contracts.
    
    Provides methods for:
    - Session and node registration
    - Contribution tracking
    - Reward calculation and distribution
    - Transaction management with retry logic
    - Caching and optimization
    """
    
    def __init__(self, config: BlockchainConfig, contract_addresses: Dict[str, str],
                 abi_dir: Path):
        """
        Initialize the Monad blockchain client.
        
        Args:
            config: Blockchain configuration
            contract_addresses: Dict mapping contract names to addresses
            abi_dir: Directory containing contract ABI JSON files
        """
        self.config = config
        self.contract_addresses = contract_addresses
        self.abi_dir = abi_dir
        
        # Initialize Web3
        logger.info(f"[MonadClient] Connecting to RPC: {config.rpc_endpoint}")
        self.web3 = Web3(Web3.HTTPProvider(config.rpc_endpoint))
        
        if not self.web3.is_connected():
            raise ConnectionError(f"Failed to connect to Monad RPC: {config.rpc_endpoint}")
        
        logger.info(f"[MonadClient] Connected to chain ID: {self.web3.eth.chain_id}")
        
        # Setup account
        self.account: LocalAccount = Account.from_key(config.private_key)
        logger.info(f"[MonadClient] Using account: {self.account.address}")
        
        # Load contracts
        self.contracts: Dict[str, Contract] = {}
        self._load_contracts()
        
        # Transaction management
        self.tx_manager = TransactionManager(self.web3, self.account)
        self.tx_queue = TransactionQueue(self)
        
        # Caching
        self.cache: Dict[str, Any] = {}
        self.cache_timestamps: Dict[str, float] = {}
        self.cache_ttl = 60  # seconds
        
        # Start async transaction processor
        if config.enable_async_transactions:
            self.tx_queue.start()
        
        logger.info("[MonadClient] Initialization complete")
    
    def _load_contracts(self):
        """Load contract ABIs and create contract instances."""
        contract_names = ['TrainingRegistry', 'ContributionTracker', 'RewardDistributor']
        
        for name in contract_names:
            if name not in self.contract_addresses:
                logger.warning(f"[MonadClient] No address for {name}, skipping")
                continue
            
            abi_path = self.abi_dir / f"{name}.json"
            
            if not abi_path.exists():
                logger.error(f"[MonadClient] ABI file not found: {abi_path}")
                continue
            
            with open(abi_path, 'r') as f:
                contract_data = json.load(f)
                abi = contract_data.get('abi', contract_data)
            
            address = Web3.to_checksum_address(self.contract_addresses[name])
            self.contracts[name] = self.web3.eth.contract(address=address, abi=abi)
            
            logger.info(f"[MonadClient] Loaded {name} at {address}")
    
    def _estimate_gas(self, transaction: Dict) -> int:
        """Estimate gas with safety buffer."""
        try:
            estimated = self.web3.eth.estimate_gas(transaction)
            # Add 20% buffer
            buffered = int(estimated * 1.2)
            logger.debug(f"[MonadClient] Gas estimate: {estimated} -> {buffered} (with buffer)")
            return buffered
        except Exception as e:
            logger.warning(f"[MonadClient] Gas estimation failed: {e}, using default")
            return self.config.gas_limit
    
    def _send_transaction(self, contract: Contract, function_name: str, 
                         *args, value: int = 0, **kwargs) -> Optional[str]:
        """
        Send a transaction with retry logic.
        
        Returns:
            Transaction hash if successful, None otherwise
        """
        max_retries = self.config.max_retries
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                # Get contract function
                func = getattr(contract.functions, function_name)
                
                # Build transaction
                nonce = self.tx_manager.get_nonce()
                
                tx_params = {
                    'from': self.account.address,
                    'nonce': nonce,
                    'gas': self.config.gas_limit,
                    'gasPrice': self.web3.eth.gas_price,
                    'chainId': self.web3.eth.chain_id,
                }
                
                if value > 0:
                    tx_params['value'] = value
                
                # Build and estimate gas
                tx = func(*args, **kwargs).build_transaction(tx_params)
                tx['gas'] = self._estimate_gas(tx)
                
                # Sign transaction
                signed_tx = self.account.sign_transaction(tx)
                
                # Send transaction
                logger.info(f"[MonadClient] Sending tx: {function_name} (attempt {attempt + 1}/{max_retries})")
                logger.debug(f"[MonadClient] Tx params: gas={tx['gas']}, nonce={nonce}")
                
                tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
                tx_hash_hex = tx_hash.hex()
                
                logger.info(f"[MonadClient] Tx sent: {tx_hash_hex}")
                
                # Wait for confirmation if configured
                if self.config.wait_for_confirmation:
                    receipt = self.web3.eth.wait_for_transaction_receipt(
                        tx_hash, 
                        timeout=self.config.confirmation_timeout
                    )
                    
                    if receipt['status'] == 1:
                        logger.info(f"[MonadClient] Tx confirmed: {tx_hash_hex} (block {receipt['blockNumber']})")
                        return tx_hash_hex
                    else:
                        logger.error(f"[MonadClient] Tx failed: {tx_hash_hex}")
                        self.tx_manager.reset_nonce()
                        return None
                else:
                    return tx_hash_hex
                    
            except ValueError as e:
                error_msg = str(e)
                logger.error(f"[MonadClient] Transaction error: {error_msg}")
                
                if "nonce" in error_msg.lower():
                    logger.warning("[MonadClient] Nonce error, resetting...")
                    self.tx_manager.reset_nonce()
                elif "gas" in error_msg.lower():
                    logger.warning("[MonadClient] Gas error, may need adjustment")
                
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))
                else:
                    return None
                    
            except Exception as e:
                logger.error(f"[MonadClient] Unexpected error: {e}")
                
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))
                else:
                    return None
        
        return None
    
    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached value if not expired."""
        if key in self.cache:
            timestamp = self.cache_timestamps.get(key, 0)
            if time.time() - timestamp < self.cache_ttl:
                logger.debug(f"[MonadClient] Cache hit: {key}")
                return self.cache[key]
        return None
    
    def _set_cache(self, key: str, value: Any):
        """Set cached value with timestamp."""
        self.cache[key] = value
        self.cache_timestamps[key] = time.time()
        logger.debug(f"[MonadClient] Cached: {key}")
    
    def _invalidate_cache(self, pattern: Optional[str] = None):
        """Invalidate cache entries matching pattern."""
        if pattern is None:
            self.cache.clear()
            self.cache_timestamps.clear()
            logger.debug("[MonadClient] Cache cleared")
        else:
            keys_to_remove = [k for k in self.cache.keys() if pattern in k]
            for key in keys_to_remove:
                del self.cache[key]
                del self.cache_timestamps[key]
            logger.debug(f"[MonadClient] Cache invalidated: {pattern} ({len(keys_to_remove)} entries)")
    
    # ==================== TrainingRegistry Methods ====================
    
    def create_session(self, session_id: str, model_hash: str) -> Optional[str]:
        """
        Create a new training session on-chain.
        
        Args:
            session_id: Unique session identifier
            model_hash: Hash of the model being trained
            
        Returns:
            Transaction hash if successful
        """
        logger.info(f"[MonadClient] Creating session: {session_id}")
        
        contract = self.contracts.get('TrainingRegistry')
        if not contract:
            logger.error("[MonadClient] TrainingRegistry contract not loaded")
            return None
        
        # Convert to bytes32
        session_id_bytes = Web3.keccak(text=session_id)
        model_hash_bytes = Web3.keccak(text=model_hash) if not model_hash.startswith('0x') else bytes.fromhex(model_hash[2:])
        
        tx_hash = self._send_transaction(
            contract, 
            'createSession',
            session_id_bytes,
            model_hash_bytes
        )
        
        if tx_hash:
            self._invalidate_cache('session_')
            logger.info(f"[MonadClient] Session created: {session_id}")
        
        return tx_hash
    
    def register_node(self, session_id: str, node_address: str, node_id: str) -> Optional[str]:
        """
        Register a node for a training session.
        
        Args:
            session_id: Session identifier
            node_address: Ethereum address of the node
            node_id: String identifier for the node
            
        Returns:
            Transaction hash if successful
        """
        logger.info(f"[MonadClient] Registering node: {node_id} ({node_address})")
        
        contract = self.contracts.get('TrainingRegistry')
        if not contract:
            logger.error("[MonadClient] TrainingRegistry contract not loaded")
            return None
        
        session_id_bytes = Web3.keccak(text=session_id)
        node_address_checksum = Web3.to_checksum_address(node_address)
        
        tx_hash = self._send_transaction(
            contract,
            'registerNode',
            session_id_bytes,
            node_address_checksum,
            node_id
        )
        
        if tx_hash:
            self._invalidate_cache(f'session_{session_id}')
            logger.info(f"[MonadClient] Node registered: {node_id}")
        
        return tx_hash
    
    def register_nodes_batch(self, session_id: str, nodes: List[Tuple[str, str]]) -> Optional[str]:
        """
        Register multiple nodes in a single transaction.
        
        Args:
            session_id: Session identifier
            nodes: List of (node_address, node_id) tuples
            
        Returns:
            Transaction hash if successful
        """
        logger.info(f"[MonadClient] Batch registering {len(nodes)} nodes")
        
        contract = self.contracts.get('TrainingRegistry')
        if not contract:
            logger.error("[MonadClient] TrainingRegistry contract not loaded")
            return None
        
        session_id_bytes = Web3.keccak(text=session_id)
        addresses = [Web3.to_checksum_address(addr) for addr, _ in nodes]
        node_ids = [node_id for _, node_id in nodes]
        
        tx_hash = self._send_transaction(
            contract,
            'registerNodesBatch',
            session_id_bytes,
            addresses,
            node_ids
        )
        
        if tx_hash:
            self._invalidate_cache(f'session_{session_id}')
            logger.info(f"[MonadClient] Batch registration complete: {len(nodes)} nodes")
        
        return tx_hash
    
    def complete_session(self, session_id: str) -> Optional[str]:
        """Mark a training session as completed."""
        logger.info(f"[MonadClient] Completing session: {session_id}")
        
        contract = self.contracts.get('TrainingRegistry')
        if not contract:
            return None
        
        session_id_bytes = Web3.keccak(text=session_id)
        
        tx_hash = self._send_transaction(
            contract,
            'completeSession',
            session_id_bytes
        )
        
        if tx_hash:
            self._invalidate_cache(f'session_{session_id}')
            logger.info(f"[MonadClient] Session completed: {session_id}")
        
        return tx_hash
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information from blockchain."""
        cache_key = f'session_{session_id}_info'
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        contract = self.contracts.get('TrainingRegistry')
        if not contract:
            return None
        
        try:
            session_id_bytes = Web3.keccak(text=session_id)
            session = contract.functions.getSession(session_id_bytes).call()
            
            info = {
                'session_id': session[0].hex(),
                'start_time': session[1],
                'end_time': session[2],
                'model_hash': session[3].hex(),
                'status': session[4],
                'node_count': session[5],
                'coordinator': session[6]
            }
            
            self._set_cache(cache_key, info)
            logger.debug(f"[MonadClient] Retrieved session info: {session_id}")
            return info
            
        except Exception as e:
            logger.error(f"[MonadClient] Error getting session info: {e}")
            return None
    
    # ==================== ContributionTracker Methods ====================
    
    def record_contribution(self, session_id: str, node_address: str,
                          compute_time: int, gradients_accepted: int,
                          successful_rounds: int, quality_score: int) -> Optional[str]:
        """
        Record contribution for a single node.
        
        Args:
            session_id: Session identifier
            node_address: Node's Ethereum address
            compute_time: Compute time in seconds
            gradients_accepted: Number of accepted gradients
            successful_rounds: Number of successful rounds
            quality_score: Quality score (0-10000)
            
        Returns:
            Transaction hash if successful
        """
        logger.info(f"[MonadClient] Recording contribution for node: {node_address}")
        
        contract = self.contracts.get('ContributionTracker')
        if not contract:
            logger.error("[MonadClient] ContributionTracker contract not loaded")
            return None
        
        session_id_bytes = Web3.keccak(text=session_id)
        node_address_checksum = Web3.to_checksum_address(node_address)
        
        tx_hash = self._send_transaction(
            contract,
            'recordContribution',
            session_id_bytes,
            node_address_checksum,
            compute_time,
            gradients_accepted,
            successful_rounds,
            quality_score
        )
        
        if tx_hash:
            self._invalidate_cache(f'contribution_{session_id}')
            logger.info(f"[MonadClient] Contribution recorded for: {node_address}")
        
        return tx_hash
    
    def record_contributions_batch(self, session_id: str,
                                   contributions: List[Dict[str, Any]]) -> Optional[str]:
        """
        Record contributions for multiple nodes in batch.
        
        Args:
            session_id: Session identifier
            contributions: List of contribution dictionaries with keys:
                - node_address
                - compute_time
                - gradients_accepted
                - successful_rounds
                - quality_score
                
        Returns:
            Transaction hash if successful
        """
        logger.info(f"[MonadClient] Batch recording {len(contributions)} contributions")
        
        contract = self.contracts.get('ContributionTracker')
        if not contract:
            logger.error("[MonadClient] ContributionTracker contract not loaded")
            return None
        
        session_id_bytes = Web3.keccak(text=session_id)
        
        addresses = [Web3.to_checksum_address(c['node_address']) for c in contributions]
        compute_times = [c['compute_time'] for c in contributions]
        gradients = [c['gradients_accepted'] for c in contributions]
        rounds = [c['successful_rounds'] for c in contributions]
        scores = [c['quality_score'] for c in contributions]
        
        tx_hash = self._send_transaction(
            contract,
            'recordContributionsBatch',
            session_id_bytes,
            addresses,
            compute_times,
            gradients,
            rounds,
            scores
        )
        
        if tx_hash:
            self._invalidate_cache(f'contribution_{session_id}')
            logger.info(f"[MonadClient] Batch contribution recording complete: {len(contributions)} nodes")
        
        return tx_hash
    
    def get_contribution(self, session_id: str, node_address: str) -> Optional[Dict[str, Any]]:
        """Get contribution data for a specific node."""
        cache_key = f'contribution_{session_id}_{node_address}'
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        contract = self.contracts.get('ContributionTracker')
        if not contract:
            return None
        
        try:
            session_id_bytes = Web3.keccak(text=session_id)
            node_address_checksum = Web3.to_checksum_address(node_address)
            
            contrib = contract.functions.getContribution(
                session_id_bytes, 
                node_address_checksum
            ).call()
            
            data = {
                'compute_time': contrib[0],
                'gradients_accepted': contrib[1],
                'successful_rounds': contrib[2],
                'quality_score': contrib[3],
                'last_updated': contrib[4]
            }
            
            self._set_cache(cache_key, data)
            logger.debug(f"[MonadClient] Retrieved contribution for: {node_address}")
            return data
            
        except Exception as e:
            logger.error(f"[MonadClient] Error getting contribution: {e}")
            return None
    
    def get_session_total(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get total contributions for a session."""
        cache_key = f'contribution_{session_id}_total'
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        contract = self.contracts.get('ContributionTracker')
        if not contract:
            return None
        
        try:
            session_id_bytes = Web3.keccak(text=session_id)
            total = contract.functions.getSessionTotal(session_id_bytes).call()
            
            data = {
                'total_compute_time': total[0],
                'total_gradients': total[1],
                'total_rounds': total[2],
                'participant_count': total[3]
            }
            
            self._set_cache(cache_key, data)
            logger.debug(f"[MonadClient] Retrieved session total for: {session_id}")
            return data
            
        except Exception as e:
            logger.error(f"[MonadClient] Error getting session total: {e}")
            return None
    
    # ==================== RewardDistributor Methods ====================
    
    def create_reward_pool(self, session_id: str, total_pool: int, 
                          strategy: int = 0) -> Optional[str]:
        """
        Create a reward pool for a session.
        
        Args:
            session_id: Session identifier
            total_pool: Total reward amount (in wei)
            strategy: Reward strategy (0=Proportional, 1=Tiered, 2=PerformanceBased, 3=Hybrid)
            
        Returns:
            Transaction hash if successful
        """
        logger.info(f"[MonadClient] Creating reward pool: {total_pool} wei (strategy={strategy})")
        
        contract = self.contracts.get('RewardDistributor')
        if not contract:
            logger.error("[MonadClient] RewardDistributor contract not loaded")
            return None
        
        session_id_bytes = Web3.keccak(text=session_id)
        
        tx_hash = self._send_transaction(
            contract,
            'createRewardPool',
            session_id_bytes,
            total_pool,
            strategy,
            value=total_pool  # Send ETH with transaction
        )
        
        if tx_hash:
            self._invalidate_cache(f'reward_{session_id}')
            logger.info(f"[MonadClient] Reward pool created: {session_id}")
        
        return tx_hash
    
    def calculate_rewards_proportional(self, session_id: str,
                                      node_addresses: List[str],
                                      contributions: List[int]) -> Optional[str]:
        """Calculate rewards using proportional strategy."""
        logger.info(f"[MonadClient] Calculating proportional rewards for {len(node_addresses)} nodes")
        
        contract = self.contracts.get('RewardDistributor')
        if not contract:
            return None
        
        session_id_bytes = Web3.keccak(text=session_id)
        addresses = [Web3.to_checksum_address(addr) for addr in node_addresses]
        
        tx_hash = self._send_transaction(
            contract,
            'calculateRewardsProportional',
            session_id_bytes,
            addresses,
            contributions
        )
        
        if tx_hash:
            self._invalidate_cache(f'reward_{session_id}')
            logger.info(f"[MonadClient] Rewards calculated: {session_id}")
        
        return tx_hash
    
    def get_pending_reward(self, session_id: str, node_address: str) -> Optional[int]:
        """Get pending reward amount for a node."""
        contract = self.contracts.get('RewardDistributor')
        if not contract:
            return None
        
        try:
            session_id_bytes = Web3.keccak(text=session_id)
            node_address_checksum = Web3.to_checksum_address(node_address)
            
            reward = contract.functions.getPendingReward(
                session_id_bytes,
                node_address_checksum
            ).call()
            
            logger.debug(f"[MonadClient] Pending reward for {node_address}: {reward}")
            return reward
            
        except Exception as e:
            logger.error(f"[MonadClient] Error getting pending reward: {e}")
            return None
    
    def get_reward_pool_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get reward pool information."""
        cache_key = f'reward_{session_id}_pool'
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        contract = self.contracts.get('RewardDistributor')
        if not contract:
            return None
        
        try:
            session_id_bytes = Web3.keccak(text=session_id)
            pool = contract.functions.getRewardPool(session_id_bytes).call()
            
            info = {
                'session_id': pool[0].hex(),
                'total_pool': pool[1],
                'distributed': pool[2],
                'claimed': pool[3],
                'strategy': pool[4],
                'calculated_at': pool[5],
                'finalized': pool[6]
            }
            
            self._set_cache(cache_key, info)
            logger.debug(f"[MonadClient] Retrieved reward pool info: {session_id}")
            return info
            
        except Exception as e:
            logger.error(f"[MonadClient] Error getting reward pool: {e}")
            return None
    
    # ==================== Async Operations ====================
    
    def create_session_async(self, session_id: str, model_hash: str):
        """Create session asynchronously."""
        self.tx_queue.enqueue(self.create_session, session_id, model_hash)
    
    def record_contributions_batch_async(self, session_id: str, contributions: List[Dict[str, Any]]):
        """Record contributions asynchronously."""
        self.tx_queue.enqueue(self.record_contributions_batch, session_id, contributions)
    
    # ==================== Utility Methods ====================
    
    def get_balance(self, address: Optional[str] = None) -> int:
        """Get ETH balance for an address."""
        addr = address if address else self.account.address
        balance = self.web3.eth.get_balance(Web3.to_checksum_address(addr))
        logger.debug(f"[MonadClient] Balance for {addr}: {balance} wei")
        return balance
    
    def shutdown(self):
        """Shutdown the client and stop background workers."""
        logger.info("[MonadClient] Shutting down...")
        self.tx_queue.stop()
        logger.info("[MonadClient] Shutdown complete")
