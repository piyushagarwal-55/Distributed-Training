"""
Model Manager - Handles model creation, parameter management, and checkpointing.
"""

import torch
import torch.nn as nn
import torch.optim as optim
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import json

from ..models.config import TrainingConfig, ModelArchitecture
from ..utils.logger import get_logger

logger = get_logger(__name__)


class SimpleCNN(nn.Module):
    """Simple CNN for MNIST/CIFAR classification."""
    
    def __init__(self, num_classes: int = 10, input_channels: int = 1):
        super().__init__()
        self.conv1 = nn.Conv2d(input_channels, 32, 3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, 3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)
        self.fc1 = nn.Linear(64 * 7 * 7, 128)
        self.fc2 = nn.Linear(128, num_classes)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.25)
    
    def forward(self, x):
        x = self.pool(self.relu(self.conv1(x)))
        x = self.pool(self.relu(self.conv2(x)))
        x = x.view(-1, 64 * 7 * 7)
        x = self.dropout(self.relu(self.fc1(x)))
        return self.fc2(x)


class SimpleMLP(nn.Module):
    """Simple MLP for tabular data."""
    
    def __init__(self, input_size: int = 784, hidden_size: int = 256, num_classes: int = 10):
        super().__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size // 2)
        self.fc3 = nn.Linear(hidden_size // 2, num_classes)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.2)
    
    def forward(self, x):
        x = x.view(x.size(0), -1)
        x = self.dropout(self.relu(self.fc1(x)))
        x = self.dropout(self.relu(self.fc2(x)))
        return self.fc3(x)


class ModelManager:
    """Manages model lifecycle, parameters, and checkpoints."""
    
    ARCHITECTURES = {
        ModelArchitecture.SIMPLE_CNN: SimpleCNN,
        ModelArchitecture.SIMPLE_MLP: SimpleMLP,
    }
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        self.model: Optional[nn.Module] = None
        self.optimizer: Optional[optim.Optimizer] = None
        self.checkpoint_dir = Path(config.checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"[ModelManager] Initialized with architecture: {config.model_architecture}")
    
    def create_model(self) -> nn.Module:
        """Create and initialize the model."""
        arch = self.config.model_architecture
        
        if arch not in self.ARCHITECTURES:
            raise ValueError(f"Unknown architecture: {arch}")
        
        model_class = self.ARCHITECTURES[arch]
        
        # Configure based on dataset
        if self.config.dataset.value == "mnist":
            self.model = model_class(num_classes=10, input_channels=1)
        elif self.config.dataset.value == "cifar10":
            self.model = model_class(num_classes=10, input_channels=3)
        else:
            self.model = model_class()
        
        # Move to device
        device = torch.device(self.config.device)
        self.model = self.model.to(device)
        
        logger.info(f"[ModelManager] Created {arch.value} model on {device}")
        return self.model
    
    def create_optimizer(self, model: nn.Module) -> optim.Optimizer:
        """Create optimizer for the model."""
        opt_name = self.config.optimizer.lower()
        lr = self.config.learning_rate
        
        if opt_name == "adam":
            self.optimizer = optim.Adam(model.parameters(), lr=lr)
        elif opt_name == "sgd":
            self.optimizer = optim.SGD(model.parameters(), lr=lr, momentum=0.9)
        elif opt_name == "adamw":
            self.optimizer = optim.AdamW(model.parameters(), lr=lr)
        else:
            self.optimizer = optim.Adam(model.parameters(), lr=lr)
        
        logger.info(f"[ModelManager] Created {opt_name} optimizer with lr={lr}")
        return self.optimizer
    
    def get_parameters(self) -> Dict[str, Any]:
        """Extract model parameters as numpy arrays."""
        if self.model is None:
            raise RuntimeError("Model not initialized")
        
        return {
            name: param.detach().cpu().numpy().copy()
            for name, param in self.model.named_parameters()
        }
    
    def set_parameters(self, parameters: Dict[str, Any]) -> None:
        """Set model parameters from numpy arrays."""
        if self.model is None:
            raise RuntimeError("Model not initialized")
        
        with torch.no_grad():
            for name, param in self.model.named_parameters():
                if name in parameters:
                    param.copy_(torch.from_numpy(parameters[name]))
    
    def save_checkpoint(self, epoch: int, metrics: Dict[str, float]) -> str:
        """Save model checkpoint."""
        checkpoint_path = self.checkpoint_dir / f"checkpoint_epoch_{epoch}.pt"
        
        torch.save({
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict() if self.optimizer else None,
            'metrics': metrics,
            'config': self.config.model_dump()
        }, checkpoint_path)
        
        logger.info(f"[ModelManager] Saved checkpoint: {checkpoint_path}")
        return str(checkpoint_path)
    
    def load_checkpoint(self, checkpoint_path: str) -> Dict[str, Any]:
        """Load model from checkpoint."""
        checkpoint = torch.load(checkpoint_path)
        
        if self.model is None:
            self.create_model()
        
        self.model.load_state_dict(checkpoint['model_state_dict'])
        
        if self.optimizer and checkpoint.get('optimizer_state_dict'):
            self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        
        logger.info(f"[ModelManager] Loaded checkpoint from epoch {checkpoint['epoch']}")
        return checkpoint
