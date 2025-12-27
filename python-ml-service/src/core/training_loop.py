"""
Complete Training Loop - Integrates all components for end-to-end distributed training.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import numpy as np

from ..models.config import SystemConfig, TrainingConfig
from ..models.metrics import AggregatedMetrics, TrainingMetrics
from ..utils.logger import get_logger
from .model_manager import ModelManager
from .data_shard import DataShardManager
from .gradient_aggregator import GradientAggregator
from .network_simulator import NetworkSimulator
from .adaptive_batch_controller import AdaptiveBatchController

logger = get_logger(__name__)


class DistributedTrainingLoop:
    """
    Complete distributed training loop that orchestrates all components.
    """
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.training_config = config.training
        
        # Core components
        self.model_manager = ModelManager(config.training)
        self.data_manager = DataShardManager(config.training)
        self.gradient_aggregator = GradientAggregator(
            strategy=config.training.aggregation_strategy,
            timeout_seconds=config.training.timeout_seconds
        )
        
        # Adaptive components
        self.network_simulator = NetworkSimulator(
            default_profile=config.network.profiles.get("default", "average")
        ) if config.network.enable_simulation else None
        
        self.batch_controller = AdaptiveBatchController(
            base_batch_size=config.training.batch_size
        )
        
        # Training state
        self.is_training = False
        self.current_epoch = 0
        self.current_step = 0
        self.global_step = 0
        self.best_accuracy = 0.0
        self.best_loss = float('inf')
        
        # Metrics
        self.metrics_history: List[AggregatedMetrics] = []
        self.epoch_metrics: Dict[str, List[float]] = {
            'loss': [], 'accuracy': [], 'learning_rate': []
        }
        
        # Callbacks
        self.on_epoch_end_callbacks = []
        self.on_step_end_callbacks = []
        
        logger.info("[TrainingLoop] Initialized")
    
    async def run_training(
        self,
        node_ids: List[str],
        epochs: Optional[int] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Run the complete distributed training loop.
        """
        epochs = epochs or self.training_config.epochs
        self.is_training = True
        start_time = time.time()
        
        logger.info(f"[TrainingLoop] Starting training for {epochs} epochs with {len(node_ids)} nodes")
        
        try:
            # Initialize model
            model = self.model_manager.create_model()
            optimizer = self.model_manager.create_optimizer(model)
            criterion = nn.CrossEntropyLoss()
            
            # Prepare data shards
            train_loaders = self.data_manager.create_shards(len(node_ids))
            
            # Get parameter shapes for aggregation
            param_shapes = {
                name: tuple(param.shape) 
                for name, param in model.named_parameters()
            }
            
            for epoch in range(epochs):
                if not self.is_training:
                    logger.info("[TrainingLoop] Training stopped by user")
                    break
                
                self.current_epoch = epoch
                epoch_loss = 0.0
                epoch_correct = 0
                epoch_total = 0
                epoch_start = time.time()
                
                # Simulate distributed training round
                for step, batches in enumerate(zip(*train_loaders)):
                    if not self.is_training:
                        break
                    
                    self.current_step = step
                    self.global_step += 1
                    
                    # Collect gradients from all nodes
                    all_gradients = []
                    step_loss = 0.0
                    step_correct = 0
                    step_total = 0
                    
                    for node_idx, (data, target) in enumerate(batches):
                        node_id = node_ids[node_idx]
                        
                        # Simulate network conditions
                        if self.network_simulator:
                            success, latency, _ = self.network_simulator.simulate_communication(
                                node_id, None, message_size_bytes=1024
                            )
                            if not success:
                                continue
                        
                        # Forward pass
                        model.zero_grad()
                        output = model(data)
                        loss = criterion(output, target)
                        
                        # Backward pass
                        loss.backward()
                        
                        # Collect gradients
                        gradients = {
                            name: param.grad.numpy().copy()
                            for name, param in model.named_parameters()
                            if param.grad is not None
                        }
                        all_gradients.append(gradients)
                        
                        # Track metrics
                        step_loss += loss.item()
                        pred = output.argmax(dim=1)
                        step_correct += pred.eq(target).sum().item()
                        step_total += target.size(0)
                    
                    if not all_gradients:
                        continue
                    
                    # Aggregate gradients
                    self.gradient_aggregator.start_round(self.global_step, node_ids[:len(all_gradients)])
                    for i, grads in enumerate(all_gradients):
                        self.gradient_aggregator.receive_gradient(node_ids[i], grads)
                    
                    aggregated = self.gradient_aggregator.aggregate_round(param_shapes)
                    
                    if aggregated:
                        # Apply aggregated gradients
                        with torch.no_grad():
                            for name, param in model.named_parameters():
                                if name in aggregated:
                                    param.grad = torch.from_numpy(aggregated[name])
                        
                        optimizer.step()
                    
                    # Update epoch metrics
                    epoch_loss += step_loss / len(all_gradients)
                    epoch_correct += step_correct
                    epoch_total += step_total
                    
                    # Progress callback
                    if progress_callback and step % 10 == 0:
                        await progress_callback({
                            'epoch': epoch,
                            'step': step,
                            'loss': step_loss / len(all_gradients),
                            'accuracy': step_correct / step_total if step_total > 0 else 0
                        })
                
                # Epoch complete
                epoch_time = time.time() - epoch_start
                avg_loss = epoch_loss / max(self.current_step + 1, 1)
                accuracy = epoch_correct / max(epoch_total, 1)
                
                # Track best metrics
                if accuracy > self.best_accuracy:
                    self.best_accuracy = accuracy
                if avg_loss < self.best_loss:
                    self.best_loss = avg_loss
                
                # Store metrics
                metrics = AggregatedMetrics(
                    epoch=epoch,
                    step=self.global_step,
                    loss=avg_loss,
                    accuracy=accuracy,
                    learning_rate=optimizer.param_groups[0]['lr'],
                    num_nodes=len(node_ids),
                    timestamp=datetime.now()
                )
                self.metrics_history.append(metrics)
                
                logger.info(
                    f"[TrainingLoop] Epoch {epoch+1}/{epochs} - "
                    f"Loss: {avg_loss:.4f}, Accuracy: {accuracy:.4f}, "
                    f"Time: {epoch_time:.2f}s"
                )
                
                # Run epoch callbacks
                for callback in self.on_epoch_end_callbacks:
                    await callback(epoch, metrics)
            
            # Training complete
            total_time = time.time() - start_time
            
            return {
                'status': 'completed',
                'epochs_completed': self.current_epoch + 1,
                'final_loss': self.best_loss,
                'final_accuracy': self.best_accuracy,
                'total_time': total_time,
                'metrics_history': [m.model_dump() for m in self.metrics_history]
            }
            
        except Exception as e:
            logger.error(f"[TrainingLoop] Training failed: {e}", exc_info=True)
            return {
                'status': 'failed',
                'error': str(e),
                'epochs_completed': self.current_epoch
            }
        finally:
            self.is_training = False
    
    def stop_training(self):
        """Stop the training loop."""
        self.is_training = False
        logger.info("[TrainingLoop] Stop requested")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current training status."""
        return {
            'is_training': self.is_training,
            'current_epoch': self.current_epoch,
            'current_step': self.current_step,
            'global_step': self.global_step,
            'best_accuracy': self.best_accuracy,
            'best_loss': self.best_loss,
            'metrics_count': len(self.metrics_history)
        }
