"""
Data Shard Manager - Handles dataset loading and distribution across nodes.
"""

import torch
from torch.utils.data import DataLoader, Subset, random_split
from torchvision import datasets, transforms
from typing import List, Optional, Tuple
from pathlib import Path

from ..models.config import TrainingConfig, Dataset
from ..utils.logger import get_logger

logger = get_logger(__name__)


class DataShardManager:
    """Manages data sharding and distribution for distributed training."""
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        self.data_dir = Path("./data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.train_dataset = None
        self.test_dataset = None
        self.shards: List[Subset] = []
        
        logger.info(f"[DataShardManager] Initialized for dataset: {config.dataset}")
    
    def load_dataset(self) -> Tuple[torch.utils.data.Dataset, torch.utils.data.Dataset]:
        """Load the configured dataset."""
        dataset_name = self.config.dataset
        
        if dataset_name == Dataset.MNIST:
            transform = transforms.Compose([
                transforms.ToTensor(),
                transforms.Normalize((0.1307,), (0.3081,))
            ])
            self.train_dataset = datasets.MNIST(
                self.data_dir, train=True, download=True, transform=transform
            )
            self.test_dataset = datasets.MNIST(
                self.data_dir, train=False, download=True, transform=transform
            )
        
        elif dataset_name == Dataset.CIFAR10:
            transform_train = transforms.Compose([
                transforms.RandomHorizontalFlip(),
                transforms.RandomCrop(32, padding=4),
                transforms.ToTensor(),
                transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2470, 0.2435, 0.2616))
            ])
            transform_test = transforms.Compose([
                transforms.ToTensor(),
                transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2470, 0.2435, 0.2616))
            ])
            self.train_dataset = datasets.CIFAR10(
                self.data_dir, train=True, download=True, transform=transform_train
            )
            self.test_dataset = datasets.CIFAR10(
                self.data_dir, train=False, download=True, transform=transform_test
            )
        
        else:
            raise ValueError(f"Unknown dataset: {dataset_name}")
        
        logger.info(f"[DataShardManager] Loaded {len(self.train_dataset)} training samples")
        return self.train_dataset, self.test_dataset
    
    def create_shards(self, num_nodes: int) -> List[DataLoader]:
        """Create data shards for distributed training."""
        if self.train_dataset is None:
            self.load_dataset()
        
        total_size = len(self.train_dataset)
        shard_size = total_size // num_nodes
        sizes = [shard_size] * num_nodes
        sizes[-1] += total_size - sum(sizes)  # Handle remainder
        
        self.shards = random_split(self.train_dataset, sizes)
        
        loaders = [
            DataLoader(
                shard,
                batch_size=self.config.batch_size,
                shuffle=True,
                num_workers=0,
                pin_memory=True
            )
            for shard in self.shards
        ]
        
        logger.info(f"[DataShardManager] Created {num_nodes} shards of ~{shard_size} samples each")
        return loaders
    
    def get_test_loader(self) -> DataLoader:
        """Get test data loader."""
        if self.test_dataset is None:
            self.load_dataset()
        
        return DataLoader(
            self.test_dataset,
            batch_size=self.config.batch_size,
            shuffle=False,
            num_workers=0
        )
