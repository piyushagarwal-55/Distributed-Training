"""
Model Parameter Management.

Handles initialization, updates, and distribution of neural network model parameters.
Manages the global model state and provides serialization for network transmission.
"""

import hashlib
import pickle
import gzip
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from ..models.config import ModelArchitecture
from ..utils.logger import get_logger

logger = get_logger(__name__)


# Define model architectures
class SimpleCNN(nn.Module):
    """Simple CNN for MNIST."""
    
    def __init__(self, num_classes: int = 10):
        super(SimpleCNN, self).__init__()
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)
        self.fc1 = nn.Linear(64 * 7 * 7, 128)
        self.fc2 = nn.Linear(128, num_classes)
        self.dropout = nn.Dropout(0.5)
    
    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = x.view(-1, 64 * 7 * 7)
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        return x


class SimpleCNNCIFAR(nn.Module):
    """Simple CNN for CIFAR-10/100."""
    
    def __init__(self, num_classes: int = 10):
        super(SimpleCNNCIFAR, self).__init__()
        self.conv1 = nn.Conv2d(3, 64, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(128, 256, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)
        self.fc1 = nn.Linear(256 * 4 * 4, 512)
        self.fc2 = nn.Linear(512, num_classes)
        self.dropout = nn.Dropout(0.5)
    
    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = self.pool(F.relu(self.conv3(x)))
        x = x.view(-1, 256 * 4 * 4)
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        return x


class ModelManager:
    """
    Manages neural network model parameters for distributed training.
    
    Features:
    - Initialize models from various architectures
    - Extract/apply parameter updates
    - Serialize parameters for transmission
    - Checkpoint management
    - Parameter validation
    """
    
    def __init__(
        self,
        architecture: ModelArchitecture,
        num_classes: int = 10,
        checkpoint_dir: str = "checkpoints",
        device: Optional[str] = None
    ):
        """
        Initialize the model manager.
        
        Args:
            architecture: Model architecture to use
            num_classes: Number of output classes
            checkpoint_dir: Directory for saving checkpoints
            device: Device to use ('cpu', 'cuda', or None for auto)
        """
        self.architecture = architecture
        self.num_classes = num_classes
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # Device setup
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)
        
        # Model and optimizer
        self.model: Optional[nn.Module] = None
        self.optimizer: Optional[torch.optim.Optimizer] = None
        self.parameter_version = 0
        self.parameter_hash: Optional[str] = None
        
        # Parameter tracking
        self.parameter_shapes: Dict[str, torch.Size] = {}
        self.parameter_history: List[Dict[str, Any]] = []
        
        logger.info(
            f"ModelManager initialized: {architecture.value}, "
            f"{num_classes} classes, device={self.device}"
        )
    
    def initialize_model(
        self,
        learning_rate: float = 0.001,
        optimizer_type: str = "adam"
    ) -> bool:
        """
        Initialize the neural network model.
        
        Args:
            learning_rate: Learning rate for optimizer
            optimizer_type: Type of optimizer ('adam', 'sgd', 'adamw')
            
        Returns:
            bool: True if successful
        """
        try:
            logger.info(f"Initializing model: {self.architecture.value}")
            
            # Create model based on architecture
            if self.architecture == ModelArchitecture.SIMPLE_CNN:
                if self.num_classes == 10 and self.device == torch.device('cpu'):
                    # MNIST-style
                    self.model = SimpleCNN(self.num_classes)
                else:
                    # CIFAR-style
                    self.model = SimpleCNNCIFAR(self.num_classes)
            
            elif self.architecture == ModelArchitecture.RESNET18:
                from torchvision.models import resnet18
                self.model = resnet18(num_classes=self.num_classes)
            
            elif self.architecture == ModelArchitecture.RESNET50:
                from torchvision.models import resnet50
                self.model = resnet50(num_classes=self.num_classes)
            
            elif self.architecture == ModelArchitecture.VGG16:
                from torchvision.models import vgg16
                self.model = vgg16(num_classes=self.num_classes)
            
            else:
                logger.error(f"Unsupported architecture: {self.architecture}")
                return False
            
            # Move model to device
            self.model = self.model.to(self.device)
            
            # Store parameter shapes
            self.parameter_shapes = {
                name: param.shape
                for name, param in self.model.named_parameters()
            }
            
            # Initialize optimizer
            if optimizer_type.lower() == "adam":
                self.optimizer = torch.optim.Adam(
                    self.model.parameters(),
                    lr=learning_rate
                )
            elif optimizer_type.lower() == "sgd":
                self.optimizer = torch.optim.SGD(
                    self.model.parameters(),
                    lr=learning_rate,
                    momentum=0.9
                )
            elif optimizer_type.lower() == "adamw":
                self.optimizer = torch.optim.AdamW(
                    self.model.parameters(),
                    lr=learning_rate
                )
            else:
                logger.error(f"Unsupported optimizer: {optimizer_type}")
                return False
            
            # Update version and hash
            self.parameter_version = 0
            self.parameter_hash = self._compute_parameter_hash()
            
            # Log model info
            num_params = sum(p.numel() for p in self.model.parameters())
            trainable_params = sum(
                p.numel() for p in self.model.parameters() if p.requires_grad
            )
            
            logger.info(
                f"Model initialized: {num_params:,} parameters "
                f"({trainable_params:,} trainable)"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize model: {e}", exc_info=True)
            return False
    
    def get_parameters(self) -> Dict[str, np.ndarray]:
        """
        Extract all model parameters as numpy arrays.
        
        Returns:
            Dict mapping parameter names to numpy arrays
        """
        if self.model is None:
            logger.error("Model not initialized")
            return {}
        
        parameters = {}
        for name, param in self.model.named_parameters():
            # Create explicit copy to avoid memory sharing issues
            parameters[name] = param.detach().cpu().numpy().copy()
        
        return parameters
    
    def set_parameters(self, parameters: Dict[str, np.ndarray]) -> bool:
        """
        Set model parameters from numpy arrays.
        
        Args:
            parameters: Dict mapping parameter names to numpy arrays
            
        Returns:
            bool: True if successful
        """
        try:
            if self.model is None:
                logger.error("Model not initialized")
                return False
            
            # Validate parameters
            if not self.validate_parameters(parameters):
                logger.error("Parameter validation failed")
                return False
            
            # Set parameters
            with torch.no_grad():
                for name, param in self.model.named_parameters():
                    if name in parameters:
                        param.copy_(
                            torch.from_numpy(parameters[name]).to(self.device)
                        )
            
            # Update version and hash
            self.parameter_version += 1
            self.parameter_hash = self._compute_parameter_hash()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to set parameters: {e}", exc_info=True)
            return False
    
    def apply_gradients(
        self,
        gradients: Dict[str, np.ndarray],
        learning_rate: Optional[float] = None
    ) -> bool:
        """
        Apply gradient updates to model parameters.
        
        Args:
            gradients: Dict mapping parameter names to gradient arrays
            learning_rate: Optional override for learning rate
            
        Returns:
            bool: True if successful
        """
        try:
            if self.model is None or self.optimizer is None:
                logger.error("Model or optimizer not initialized")
                return False
            
            # Validate gradients
            if not self.validate_parameters(gradients, check_values=False):
                logger.error("Gradient validation failed")
                return False
            
            # Override learning rate if provided
            if learning_rate is not None:
                for param_group in self.optimizer.param_groups:
                    param_group['lr'] = learning_rate
            
            # Apply gradients
            self.optimizer.zero_grad()
            
            with torch.no_grad():
                for name, param in self.model.named_parameters():
                    if name in gradients:
                        # Set gradients
                        if param.grad is None:
                            param.grad = torch.zeros_like(param)
                        param.grad.copy_(
                            torch.from_numpy(gradients[name]).to(self.device)
                        )
            
            # Optimizer step
            self.optimizer.step()
            
            # Update version and hash
            self.parameter_version += 1
            self.parameter_hash = self._compute_parameter_hash()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply gradients: {e}", exc_info=True)
            return False
    
    def serialize_parameters(
        self,
        compress: bool = True,
        include_optimizer: bool = False
    ) -> Optional[bytes]:
        """
        Serialize model parameters for transmission.
        
        Args:
            compress: Whether to compress the data
            include_optimizer: Whether to include optimizer state
            
        Returns:
            Serialized bytes or None if failed
        """
        try:
            if self.model is None:
                logger.error("Model not initialized")
                return None
            
            # Prepare data
            data = {
                "parameters": self.get_parameters(),
                "version": self.parameter_version,
                "hash": self.parameter_hash,
                "architecture": self.architecture.value,
                "num_classes": self.num_classes,
            }
            
            if include_optimizer and self.optimizer is not None:
                data["optimizer_state"] = {
                    k: v.cpu().numpy() if isinstance(v, torch.Tensor) else v
                    for k, v in self.optimizer.state_dict().items()
                }
            
            # Serialize
            serialized = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
            
            # Compress
            if compress:
                serialized = gzip.compress(serialized, compresslevel=6)
            
            logger.info(
                f"Parameters serialized: {len(serialized)} bytes "
                f"(version {self.parameter_version})"
            )
            
            return serialized
            
        except Exception as e:
            logger.error(f"Failed to serialize parameters: {e}", exc_info=True)
            return None
    
    def deserialize_parameters(
        self,
        serialized_data: bytes,
        compressed: bool = True,
        load_optimizer: bool = False
    ) -> bool:
        """
        Deserialize and load model parameters.
        
        Args:
            serialized_data: Serialized parameter data
            compressed: Whether data is compressed
            load_optimizer: Whether to load optimizer state
            
        Returns:
            bool: True if successful
        """
        try:
            # Decompress
            if compressed:
                serialized_data = gzip.decompress(serialized_data)
            
            # Deserialize
            data = pickle.loads(serialized_data)
            
            # Load parameters
            success = self.set_parameters(data["parameters"])
            if not success:
                return False
            
            # Load optimizer state
            if load_optimizer and "optimizer_state" in data and self.optimizer is not None:
                self.optimizer.load_state_dict(data["optimizer_state"])
            
            # Update metadata
            self.parameter_version = data["version"]
            self.parameter_hash = data["hash"]
            
            logger.info(
                f"Parameters deserialized: version {self.parameter_version}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to deserialize parameters: {e}", exc_info=True)
            return False
    
    def save_checkpoint(
        self,
        epoch: int,
        metrics: Optional[Dict[str, float]] = None
    ) -> Optional[str]:
        """
        Save model checkpoint to disk.
        
        Args:
            epoch: Current epoch number
            metrics: Optional training metrics
            
        Returns:
            Path to checkpoint file or None if failed
        """
        try:
            if self.model is None:
                logger.error("Model not initialized")
                return None
            
            checkpoint_file = (
                self.checkpoint_dir /
                f"checkpoint_epoch_{epoch}_v{self.parameter_version}.pt"
            )
            
            checkpoint = {
                "epoch": epoch,
                "model_state_dict": self.model.state_dict(),
                "parameter_version": self.parameter_version,
                "parameter_hash": self.parameter_hash,
                "architecture": self.architecture.value,
                "num_classes": self.num_classes,
            }
            
            if self.optimizer is not None:
                checkpoint["optimizer_state_dict"] = self.optimizer.state_dict()
            
            if metrics is not None:
                checkpoint["metrics"] = metrics
            
            torch.save(checkpoint, checkpoint_file)
            
            logger.info(f"Checkpoint saved: {checkpoint_file}")
            return str(checkpoint_file)
            
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}", exc_info=True)
            return None
    
    def load_checkpoint(self, checkpoint_file: str) -> bool:
        """
        Load model from checkpoint.
        
        Args:
            checkpoint_file: Path to checkpoint file
            
        Returns:
            bool: True if successful
        """
        try:
            if not Path(checkpoint_file).exists():
                logger.error(f"Checkpoint file not found: {checkpoint_file}")
                return False
            
            checkpoint = torch.load(checkpoint_file, map_location=self.device)
            
            # Verify architecture matches
            if checkpoint["architecture"] != self.architecture.value:
                logger.error("Architecture mismatch in checkpoint")
                return False
            
            # Load model state
            if self.model is None:
                # Initialize model first
                self.initialize_model()
            
            self.model.load_state_dict(checkpoint["model_state_dict"])
            
            # Load optimizer state if available
            if "optimizer_state_dict" in checkpoint and self.optimizer is not None:
                self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
            
            # Restore metadata
            self.parameter_version = checkpoint["parameter_version"]
            self.parameter_hash = checkpoint["parameter_hash"]
            
            logger.info(
                f"Checkpoint loaded: epoch {checkpoint['epoch']}, "
                f"version {self.parameter_version}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}", exc_info=True)
            return False
    
    def validate_parameters(
        self,
        parameters: Dict[str, np.ndarray],
        check_values: bool = True
    ) -> bool:
        """
        Validate parameter shapes and values.
        
        Args:
            parameters: Parameters to validate
            check_values: Whether to check for NaN/Inf values
            
        Returns:
            bool: True if valid
        """
        try:
            # Check all expected parameters present
            for name, expected_shape in self.parameter_shapes.items():
                if name not in parameters:
                    logger.error(f"Missing parameter: {name}")
                    return False
                
                # Check shape
                actual_shape = parameters[name].shape
                if actual_shape != tuple(expected_shape):
                    logger.error(
                        f"Shape mismatch for {name}: "
                        f"expected {expected_shape}, got {actual_shape}"
                    )
                    return False
                
                # Check values if requested
                if check_values:
                    param_array = parameters[name]
                    
                    # Check for NaN
                    if np.isnan(param_array).any():
                        logger.error(f"NaN detected in parameter: {name}")
                        return False
                    
                    # Check for Inf
                    if np.isinf(param_array).any():
                        logger.error(f"Inf detected in parameter: {name}")
                        return False
                    
                    # Check magnitude (reasonable bounds)
                    max_val = np.abs(param_array).max()
                    if max_val > 1e6:
                        logger.warning(
                            f"Very large parameter value in {name}: {max_val}"
                        )
            
            return True
            
        except Exception as e:
            logger.error(f"Parameter validation error: {e}", exc_info=True)
            return False
    
    def get_parameter_stats(self) -> Dict[str, Any]:
        """
        Get statistics about current parameters.
        
        Returns:
            Dict with parameter statistics
        """
        if self.model is None:
            return {}
        
        parameters = self.get_parameters()
        
        stats = {
            "version": self.parameter_version,
            "hash": self.parameter_hash,
            "num_parameters": sum(p.size for p in parameters.values()),
            "parameter_layers": len(parameters),
        }
        
        # Compute statistics per layer
        for name, param_array in parameters.items():
            layer_stats = {
                "shape": param_array.shape,
                "mean": float(np.mean(param_array)),
                "std": float(np.std(param_array)),
                "min": float(np.min(param_array)),
                "max": float(np.max(param_array)),
            }
            stats[f"layer_{name}"] = layer_stats
        
        return stats
    
    def _compute_parameter_hash(self) -> str:
        """Compute hash of current parameters."""
        if self.model is None:
            return ""
        
        parameters = self.get_parameters()
        
        # Concatenate all parameters
        param_bytes = b""
        for name in sorted(parameters.keys()):
            param_bytes += parameters[name].tobytes()
        
        return hashlib.md5(param_bytes).hexdigest()
