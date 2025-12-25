"""
GPU Node Service - Simulated GPU node that runs local training.

This represents an individual GPU node in the distributed system that:
- Receives training instructions from the coordinator
- Runs training locally on its data shard
- Computes and sends back gradients
- Reports metrics and health status
"""

import time
import threading
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from collections import deque

from ..models.config import SystemConfig
from ..models.node import NodeMetadata, NodeStatus
from ..utils.logger import get_logger

logger = get_logger(__name__)


class GPUNodeService:
    """
    Simulated GPU node service that performs local training.
    
    This class represents a single GPU node in the distributed training system.
    It receives model parameters and data from the coordinator, performs local
    training steps, and sends back gradients and metrics.
    """
    
    def __init__(
        self,
        node_id: str,
        gpu_specs: Dict[str, Any],
        config: SystemConfig,
        simulated_delay_factor: float = 1.0
    ):
        """
        Initialize GPU node service.
        
        Args:
            node_id: Unique identifier for this node
            gpu_specs: Dictionary containing GPU specifications
                - gpu_model: str
                - gpu_memory_gb: float
                - compute_capability: float
            config: System configuration
            simulated_delay_factor: Multiplier for compute delays (for simulation)
        """
        self.node_id = node_id
        self.gpu_specs = gpu_specs
        self.config = config
        self.simulated_delay_factor = simulated_delay_factor
        
        # Node state
        self.status = NodeStatus.INITIALIZING
        self.model: Optional[nn.Module] = None
        self.data_loader: Optional[DataLoader] = None
        self.data_shard_id: Optional[int] = None
        self.current_batch_size = config.training.batch_size
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Model parameters
        self.current_parameters: Optional[Dict[str, np.ndarray]] = None
        self.parameter_version = 0
        
        # Training state
        self.current_epoch = 0
        self.steps_completed = 0
        self.is_training = False
        self.data_iterator = None
        
        # Metrics tracking
        self.local_metrics = {
            'loss_history': deque(maxlen=100),
            'gradient_norms': deque(maxlen=100),
            'step_times': deque(maxlen=100),
            'forward_times': deque(maxlen=100),
            'backward_times': deque(maxlen=100)
        }
        
        # Communication tracking
        self.gradients_sent = 0
        self.updates_received = 0
        self.failed_communications = 0
        self.last_communication_time = None
        
        # Compute tracking for contribution measurement
        self.total_compute_time = 0.0
        self.successful_gradient_submissions = 0
        
        # Thread safety
        self.lock = threading.RLock()
        
        logger.info(f"GPU Node {node_id} initialized with specs: {gpu_specs}")
        print(f"[NODE {node_id}] Initialized with GPU: {gpu_specs.get('gpu_model', 'Unknown')}, "
              f"Memory: {gpu_specs.get('gpu_memory_gb', 0)}GB, "
              f"Compute: {gpu_specs.get('compute_capability', 1.0)}x")
    
    def initialize(
        self,
        model_parameters: Dict[str, np.ndarray],
        data_loader: DataLoader,
        data_shard_id: int
    ) -> bool:
        """
        Initialize node with model parameters and data shard.
        
        Args:
            model_parameters: Dictionary of model parameters (numpy arrays)
            data_loader: PyTorch DataLoader for this node's data shard
            data_shard_id: ID of the assigned data shard
            
        Returns:
            bool: True if initialization successful
        """
        with self.lock:
            try:
                logger.info(f"[NODE {self.node_id}] Initializing with data shard {data_shard_id}")
                print(f"[NODE {self.node_id}] Receiving model parameters and data shard {data_shard_id}...")
                
                # Store data loader and shard info
                self.data_loader = data_loader
                self.data_shard_id = data_shard_id
                self.data_iterator = iter(data_loader)
                
                # Store parameters
                self.current_parameters = model_parameters
                self.parameter_version += 1
                
                # Create model architecture (this should match coordinator's model)
                self._create_model_architecture()
                
                # Load parameters into model
                self._load_parameters(model_parameters)
                
                self.status = NodeStatus.READY
                self.updates_received += 1
                
                logger.info(f"[NODE {self.node_id}] Initialization complete, status: READY")
                print(f"[NODE {self.node_id}] ✓ Initialized successfully with {len(data_loader.dataset)} samples")
                
                return True
                
            except Exception as e:
                logger.error(f"[NODE {self.node_id}] Initialization failed: {e}")
                print(f"[NODE {self.node_id}] ✗ Initialization failed: {e}")
                self.status = NodeStatus.ERROR
                return False
    
    def _create_model_architecture(self):
        """Create the model architecture based on configuration."""
        from ..core.model_manager import ModelManager
        
        # Create a temporary model manager to get the architecture
        temp_manager = ModelManager(self.config.training.model_architecture)
        temp_manager.initialize_model()
        self.model = temp_manager.model.to(self.device)
        
        logger.debug(f"[NODE {self.node_id}] Model architecture created: {type(self.model).__name__}")
    
    def _load_parameters(self, parameters: Dict[str, np.ndarray]):
        """
        Load parameters into the model.
        
        Args:
            parameters: Dictionary of parameter name -> numpy array
        """
        if self.model is None:
            raise ValueError("Model not initialized")
        
        state_dict = {}
        for name, param_array in parameters.items():
            # Convert numpy array to torch tensor
            state_dict[name] = torch.from_numpy(param_array).to(self.device)
        
        self.model.load_state_dict(state_dict)
        logger.debug(f"[NODE {self.node_id}] Loaded {len(parameters)} parameter tensors")
    
    def train_step(self) -> Optional[Dict[str, Any]]:
        """
        Execute one training step.
        
        Returns:
            Dictionary containing:
                - gradients: Dict[str, np.ndarray] - computed gradients
                - metrics: Dict[str, float] - local metrics (loss, etc.)
                - step_info: Dict[str, Any] - metadata about the step
            Returns None if training step fails
        """
        with self.lock:
            if self.status != NodeStatus.READY and self.status != NodeStatus.TRAINING:
                logger.warning(f"[NODE {self.node_id}] Cannot train, status: {self.status}")
                return None
            
            try:
                self.status = NodeStatus.TRAINING
                self.is_training = True
                
                step_start = time.time()
                
                # Get next batch of data
                try:
                    batch = next(self.data_iterator)
                except StopIteration:
                    # Restart data iterator
                    self.data_iterator = iter(self.data_loader)
                    batch = next(self.data_iterator)
                    self.current_epoch += 1
                    logger.info(f"[NODE {self.node_id}] Completed epoch {self.current_epoch}")
                    print(f"[NODE {self.node_id}] Epoch {self.current_epoch} complete")
                
                # Unpack batch
                if isinstance(batch, (tuple, list)):
                    inputs, targets = batch
                else:
                    inputs = batch
                    targets = None
                
                # Move to device
                inputs = inputs.to(self.device)
                if targets is not None:
                    targets = targets.to(self.device)
                
                # Forward pass
                forward_start = time.time()
                self.model.train()
                self.model.zero_grad()
                
                outputs = self.model(inputs)
                
                # Simulate GPU compute time
                self._simulate_compute_delay('forward')
                
                forward_time = time.time() - forward_start
                
                # Compute loss
                if targets is not None:
                    criterion = nn.CrossEntropyLoss()
                    loss = criterion(outputs, targets)
                else:
                    # Dummy loss for testing
                    loss = outputs.mean()
                
                # Backward pass
                backward_start = time.time()
                loss.backward()
                
                # Simulate GPU compute time
                self._simulate_compute_delay('backward')
                
                backward_time = time.time() - backward_start
                
                # Extract gradients
                gradients = self._extract_gradients()
                
                # Calculate gradient norm
                grad_norm = self._calculate_gradient_norm(gradients)
                
                # Record metrics
                step_time = time.time() - step_start
                self.local_metrics['loss_history'].append(float(loss.item()))
                self.local_metrics['gradient_norms'].append(grad_norm)
                self.local_metrics['step_times'].append(step_time)
                self.local_metrics['forward_times'].append(forward_time)
                self.local_metrics['backward_times'].append(backward_time)
                
                # Update tracking
                self.steps_completed += 1
                self.total_compute_time += step_time
                
                self.status = NodeStatus.READY
                self.is_training = False
                
                # Prepare result
                result = {
                    'gradients': gradients,
                    'metrics': {
                        'loss': float(loss.item()),
                        'gradient_norm': grad_norm,
                        'step_time': step_time,
                        'forward_time': forward_time,
                        'backward_time': backward_time,
                        'batch_size': len(inputs)
                    },
                    'step_info': {
                        'node_id': self.node_id,
                        'step': self.steps_completed,
                        'epoch': self.current_epoch,
                        'data_shard_id': self.data_shard_id,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                }
                
                logger.debug(f"[NODE {self.node_id}] Step {self.steps_completed} complete, "
                           f"loss: {loss.item():.4f}, grad_norm: {grad_norm:.4f}")
                
                return result
                
            except Exception as e:
                logger.error(f"[NODE {self.node_id}] Training step failed: {e}")
                print(f"[NODE {self.node_id}] ✗ Training step error: {e}")
                self.status = NodeStatus.ERROR
                self.is_training = False
                self.failed_communications += 1
                return None
    
    def _extract_gradients(self) -> Dict[str, np.ndarray]:
        """
        Extract gradients from model.
        
        Returns:
            Dictionary of parameter name -> gradient array (numpy)
        """
        gradients = {}
        for name, param in self.model.named_parameters():
            if param.grad is not None:
                # Copy gradient to CPU and convert to numpy
                gradients[name] = param.grad.detach().cpu().numpy().copy()
            else:
                # No gradient computed for this parameter
                gradients[name] = np.zeros_like(param.detach().cpu().numpy())
        
        return gradients
    
    def _calculate_gradient_norm(self, gradients: Dict[str, np.ndarray]) -> float:
        """
        Calculate L2 norm of gradients.
        
        Args:
            gradients: Dictionary of gradients
            
        Returns:
            L2 norm of all gradients
        """
        total_norm = 0.0
        for grad in gradients.values():
            total_norm += np.sum(grad ** 2)
        return float(np.sqrt(total_norm))
    
    def _simulate_compute_delay(self, phase: str):
        """
        Simulate GPU computation time.
        
        Args:
            phase: 'forward' or 'backward'
        """
        # Base delay varies by GPU capability
        compute_capability = self.gpu_specs.get('compute_capability', 1.0)
        base_delay = 0.01 / compute_capability  # Faster GPUs have higher capability
        
        # Scale by delay factor
        delay = base_delay * self.simulated_delay_factor
        
        # Add some randomness
        delay *= (0.8 + 0.4 * np.random.random())
        
        time.sleep(delay)
    
    def update_parameters(self, new_parameters: Dict[str, np.ndarray]) -> bool:
        """
        Update model parameters with new values from coordinator.
        
        Args:
            new_parameters: Dictionary of updated parameters
            
        Returns:
            bool: True if update successful
        """
        with self.lock:
            try:
                logger.debug(f"[NODE {self.node_id}] Receiving parameter update")
                
                # Verify parameter shapes match
                if self.current_parameters is not None:
                    for name in new_parameters:
                        if name in self.current_parameters:
                            old_shape = self.current_parameters[name].shape
                            new_shape = new_parameters[name].shape
                            if old_shape != new_shape:
                                raise ValueError(
                                    f"Parameter shape mismatch for {name}: "
                                    f"expected {old_shape}, got {new_shape}"
                                )
                
                # Load new parameters
                self._load_parameters(new_parameters)
                self.current_parameters = new_parameters
                self.parameter_version += 1
                self.updates_received += 1
                
                logger.debug(f"[NODE {self.node_id}] Parameters updated to version {self.parameter_version}")
                return True
                
            except Exception as e:
                logger.error(f"[NODE {self.node_id}] Parameter update failed: {e}")
                print(f"[NODE {self.node_id}] ✗ Parameter update failed: {e}")
                return False
    
    def update_batch_size(self, new_batch_size: int) -> bool:
        """
        Update the batch size for this node.
        
        Args:
            new_batch_size: New batch size to use
            
        Returns:
            bool: True if update successful
        """
        with self.lock:
            try:
                if new_batch_size <= 0:
                    raise ValueError(f"Invalid batch size: {new_batch_size}")
                
                old_batch_size = self.current_batch_size
                self.current_batch_size = new_batch_size
                
                # Recreate data loader with new batch size if we have data
                if self.data_loader is not None:
                    dataset = self.data_loader.dataset
                    self.data_loader = DataLoader(
                        dataset,
                        batch_size=new_batch_size,
                        shuffle=True,
                        num_workers=0
                    )
                    self.data_iterator = iter(self.data_loader)
                
                logger.info(f"[NODE {self.node_id}] Batch size updated: {old_batch_size} -> {new_batch_size}")
                print(f"[NODE {self.node_id}] Batch size changed: {old_batch_size} -> {new_batch_size}")
                
                return True
                
            except Exception as e:
                logger.error(f"[NODE {self.node_id}] Batch size update failed: {e}")
                return False
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check and return current status.
        
        Returns:
            Dictionary with health information
        """
        with self.lock:
            return {
                'node_id': self.node_id,
                'status': self.status.value,
                'is_training': self.is_training,
                'steps_completed': self.steps_completed,
                'current_epoch': self.current_epoch,
                'parameter_version': self.parameter_version,
                'updates_received': self.updates_received,
                'gradients_sent': self.gradients_sent,
                'successful_submissions': self.successful_gradient_submissions,
                'failed_communications': self.failed_communications,
                'total_compute_time': self.total_compute_time,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get summary of local metrics.
        
        Returns:
            Dictionary with aggregated metrics
        """
        with self.lock:
            def safe_mean(deque_obj):
                return float(np.mean(list(deque_obj))) if len(deque_obj) > 0 else 0.0
            
            def safe_std(deque_obj):
                return float(np.std(list(deque_obj))) if len(deque_obj) > 0 else 0.0
            
            return {
                'node_id': self.node_id,
                'loss': {
                    'mean': safe_mean(self.local_metrics['loss_history']),
                    'std': safe_std(self.local_metrics['loss_history']),
                    'recent': list(self.local_metrics['loss_history'])[-10:]
                },
                'gradient_norm': {
                    'mean': safe_mean(self.local_metrics['gradient_norms']),
                    'std': safe_std(self.local_metrics['gradient_norms'])
                },
                'timing': {
                    'step_time_mean': safe_mean(self.local_metrics['step_times']),
                    'forward_time_mean': safe_mean(self.local_metrics['forward_times']),
                    'backward_time_mean': safe_mean(self.local_metrics['backward_times'])
                },
                'training_progress': {
                    'steps_completed': self.steps_completed,
                    'epochs_completed': self.current_epoch,
                    'total_compute_time': self.total_compute_time
                },
                'reliability': {
                    'updates_received': self.updates_received,
                    'gradients_sent': self.gradients_sent,
                    'successful_submissions': self.successful_gradient_submissions,
                    'failed_communications': self.failed_communications,
                    'success_rate': (
                        self.successful_gradient_submissions / self.gradients_sent
                        if self.gradients_sent > 0 else 0.0
                    )
                }
            }
    
    def record_gradient_sent(self, success: bool):
        """
        Record that a gradient was sent to coordinator.
        
        Args:
            success: Whether the send was successful
        """
        with self.lock:
            self.gradients_sent += 1
            self.last_communication_time = datetime.utcnow()
            
            if success:
                self.successful_gradient_submissions += 1
            else:
                self.failed_communications += 1
    
    def shutdown(self):
        """Gracefully shutdown the node."""
        with self.lock:
            logger.info(f"[NODE {self.node_id}] Shutting down...")
            print(f"[NODE {self.node_id}] Shutting down gracefully...")
            
            self.status = NodeStatus.OFFLINE
            self.is_training = False
            
            # Clear model from memory
            if self.model is not None:
                del self.model
                self.model = None
            
            # Clear data
            self.data_loader = None
            self.data_iterator = None
            
            logger.info(f"[NODE {self.node_id}] Shutdown complete")
            print(f"[NODE {self.node_id}] ✓ Shutdown complete")
