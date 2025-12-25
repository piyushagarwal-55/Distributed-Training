"""
Data Sharding and Distribution Manager.

Handles intelligent data distribution that splits datasets across GPU nodes efficiently.
Implements balanced, deterministic sharding with dynamic reassignment capabilities.
"""

import hashlib
import pickle
import gzip
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader, Subset
from torchvision import datasets, transforms
from collections import defaultdict

from ..models.config import DatasetType
from ..utils.logger import get_logger

logger = get_logger(__name__)


class DataShardManager:
    """
    Manages data sharding and distribution for distributed training.
    
    Features:
    - Balanced data splitting across N nodes
    - Stratified splitting (maintains class distribution)
    - Dynamic reassignment when nodes join/leave
    - Data serialization and caching
    - Checksum verification
    """
    
    def __init__(
        self,
        dataset_type: DatasetType,
        dataset_path: Optional[str] = None,
        cache_dir: str = "data_cache",
    ):
        """
        Initialize the data shard manager.
        
        Args:
            dataset_type: Type of dataset (MNIST, CIFAR-10, etc.)
            dataset_path: Path to dataset (None for built-in datasets)
            cache_dir: Directory for caching shards
        """
        self.dataset_type = dataset_type
        self.dataset_path = dataset_path
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Dataset storage
        self.train_dataset: Optional[Dataset] = None
        self.test_dataset: Optional[Dataset] = None
        self.num_classes: int = 10  # Default, will be updated
        
        # Shard management
        self.shards: Dict[str, List[int]] = {}  # node_id -> list of indices
        self.shard_metadata: Dict[str, Dict[str, Any]] = {}
        self.orphaned_shards: List[List[int]] = []
        
        # Cache tracking
        self.cache_valid = False
        self.cache_hash: Optional[str] = None
        
        logger.info(f"DataShardManager initialized for {dataset_type.value}")
    
    def load_dataset(self, download: bool = True) -> bool:
        """
        Load the dataset from disk or download if needed.
        
        Args:
            download: Whether to download dataset if not found
            
        Returns:
            bool: True if successful
        """
        try:
            logger.info(f"Loading dataset: {self.dataset_type.value}")
            
            if self.dataset_type == DatasetType.MNIST:
                transform = transforms.Compose([
                    transforms.ToTensor(),
                    transforms.Normalize((0.1307,), (0.3081,))
                ])
                
                data_path = self.dataset_path or './data'
                self.train_dataset = datasets.MNIST(
                    root=data_path,
                    train=True,
                    download=download,
                    transform=transform
                )
                self.test_dataset = datasets.MNIST(
                    root=data_path,
                    train=False,
                    download=download,
                    transform=transform
                )
                self.num_classes = 10
                
            elif self.dataset_type == DatasetType.CIFAR10:
                transform = transforms.Compose([
                    transforms.ToTensor(),
                    transforms.Normalize(
                        (0.4914, 0.4822, 0.4465),
                        (0.2023, 0.1994, 0.2010)
                    )
                ])
                
                data_path = self.dataset_path or './data'
                self.train_dataset = datasets.CIFAR10(
                    root=data_path,
                    train=True,
                    download=download,
                    transform=transform
                )
                self.test_dataset = datasets.CIFAR10(
                    root=data_path,
                    train=False,
                    download=download,
                    transform=transform
                )
                self.num_classes = 10
                
            elif self.dataset_type == DatasetType.CIFAR100:
                transform = transforms.Compose([
                    transforms.ToTensor(),
                    transforms.Normalize(
                        (0.5071, 0.4867, 0.4408),
                        (0.2675, 0.2565, 0.2761)
                    )
                ])
                
                data_path = self.dataset_path or './data'
                self.train_dataset = datasets.CIFAR100(
                    root=data_path,
                    train=True,
                    download=download,
                    transform=transform
                )
                self.test_dataset = datasets.CIFAR100(
                    root=data_path,
                    train=False,
                    download=download,
                    transform=transform
                )
                self.num_classes = 100
                
            else:
                logger.error(f"Unsupported dataset type: {self.dataset_type}")
                return False
            
            logger.info(
                f"Dataset loaded: {len(self.train_dataset)} train samples, "
                f"{len(self.test_dataset)} test samples, "
                f"{self.num_classes} classes"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to load dataset: {e}", exc_info=True)
            return False
    
    def create_shards(
        self,
        num_shards: int,
        stratified: bool = True,
        seed: int = 42
    ) -> bool:
        """
        Split the dataset into N shards.
        
        Args:
            num_shards: Number of shards to create
            stratified: Whether to maintain class distribution
            seed: Random seed for reproducibility
            
        Returns:
            bool: True if successful
        """
        try:
            if self.train_dataset is None:
                logger.error("Dataset not loaded. Call load_dataset() first.")
                return False
            
            logger.info(
                f"Creating {num_shards} shards "
                f"({'stratified' if stratified else 'random'})"
            )
            
            dataset_size = len(self.train_dataset)
            
            if stratified:
                # Group indices by class
                class_indices = defaultdict(list)
                for idx in range(dataset_size):
                    _, label = self.train_dataset[idx]
                    if isinstance(label, torch.Tensor):
                        label = label.item()
                    class_indices[label].append(idx)
                
                # Split each class evenly across shards
                shard_indices = [[] for _ in range(num_shards)]
                
                np.random.seed(seed)
                for class_label, indices in class_indices.items():
                    # Shuffle indices for this class
                    indices = np.array(indices)
                    np.random.shuffle(indices)
                    
                    # Split evenly across shards
                    splits = np.array_split(indices, num_shards)
                    for shard_id, split in enumerate(splits):
                        shard_indices[shard_id].extend(split.tolist())
                
                # Shuffle within each shard
                for indices in shard_indices:
                    np.random.shuffle(indices)
                
            else:
                # Random splitting
                indices = np.arange(dataset_size)
                np.random.seed(seed)
                np.random.shuffle(indices)
                
                shard_indices = np.array_split(indices, num_shards)
                shard_indices = [split.tolist() for split in shard_indices]
            
            # Store shards (initially unassigned)
            self.orphaned_shards = shard_indices
            self.shards = {}
            self.shard_metadata = {}
            
            # Log statistics
            shard_sizes = [len(shard) for shard in shard_indices]
            logger.info(
                f"Shards created: min={min(shard_sizes)}, "
                f"max={max(shard_sizes)}, "
                f"avg={np.mean(shard_sizes):.1f}"
            )
            
            # Verify all samples included
            total_samples = sum(shard_sizes)
            assert total_samples == dataset_size, "Sample count mismatch!"
            
            # Verify no duplicates
            all_indices = set()
            for shard in shard_indices:
                all_indices.update(shard)
            assert len(all_indices) == dataset_size, "Duplicate indices found!"
            
            logger.info("Shard verification passed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create shards: {e}", exc_info=True)
            return False
    
    def assign_shard(self, node_id: str, shard_index: Optional[int] = None) -> bool:
        """
        Assign a shard to a node.
        
        Args:
            node_id: ID of the node
            shard_index: Specific shard index to assign (None for next available)
            
        Returns:
            bool: True if successful
        """
        try:
            if not self.orphaned_shards:
                logger.warning("No available shards to assign")
                return False
            
            # Get shard
            if shard_index is not None:
                if shard_index >= len(self.orphaned_shards):
                    logger.error(f"Invalid shard index: {shard_index}")
                    return False
                shard = self.orphaned_shards.pop(shard_index)
            else:
                shard = self.orphaned_shards.pop(0)
            
            # Assign to node
            self.shards[node_id] = shard
            
            # Create metadata
            self.shard_metadata[node_id] = {
                "num_samples": len(shard),
                "assigned_at": torch.cuda.Event(enable_timing=True) if torch.cuda.is_available() else None,
                "checksum": self._compute_checksum(shard),
            }
            
            logger.info(
                f"Shard assigned to node {node_id}: "
                f"{len(shard)} samples, "
                f"remaining unassigned shards: {len(self.orphaned_shards)}"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to assign shard to {node_id}: {e}", exc_info=True)
            return False
    
    def reassign_shard(self, old_node_id: str, new_node_id: str) -> bool:
        """
        Reassign a shard from one node to another.
        
        Args:
            old_node_id: ID of node losing the shard
            new_node_id: ID of node receiving the shard
            
        Returns:
            bool: True if successful
        """
        try:
            if old_node_id not in self.shards:
                logger.error(f"Node {old_node_id} has no assigned shard")
                return False
            
            # Move shard
            shard = self.shards.pop(old_node_id)
            self.shards[new_node_id] = shard
            
            # Update metadata
            metadata = self.shard_metadata.pop(old_node_id)
            self.shard_metadata[new_node_id] = metadata
            
            logger.info(f"Shard reassigned: {old_node_id} -> {new_node_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reassign shard: {e}", exc_info=True)
            return False
    
    def release_shard(self, node_id: str) -> bool:
        """
        Release a shard back to the orphaned pool.
        
        Args:
            node_id: ID of node releasing the shard
            
        Returns:
            bool: True if successful
        """
        try:
            if node_id not in self.shards:
                logger.warning(f"Node {node_id} has no assigned shard")
                return False
            
            # Return to orphaned pool
            shard = self.shards.pop(node_id)
            self.orphaned_shards.append(shard)
            
            # Clean up metadata
            if node_id in self.shard_metadata:
                del self.shard_metadata[node_id]
            
            logger.info(f"Shard released from node {node_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to release shard from {node_id}: {e}", exc_info=True)
            return False
    
    def get_shard_dataloader(
        self,
        node_id: str,
        batch_size: int = 32,
        shuffle: bool = True,
        num_workers: int = 0
    ) -> Optional[DataLoader]:
        """
        Create a DataLoader for a node's shard.
        
        Args:
            node_id: ID of the node
            batch_size: Batch size for the loader
            shuffle: Whether to shuffle data
            num_workers: Number of worker processes
            
        Returns:
            DataLoader or None if node has no shard
        """
        try:
            if node_id not in self.shards:
                logger.error(f"Node {node_id} has no assigned shard")
                return None
            
            if self.train_dataset is None:
                logger.error("Dataset not loaded")
                return None
            
            indices = self.shards[node_id]
            subset = Subset(self.train_dataset, indices)
            
            loader = DataLoader(
                subset,
                batch_size=batch_size,
                shuffle=shuffle,
                num_workers=num_workers,
                pin_memory=torch.cuda.is_available()
            )
            
            return loader
            
        except Exception as e:
            logger.error(f"Failed to create DataLoader for {node_id}: {e}", exc_info=True)
            return None
    
    def serialize_shard(self, node_id: str, compress: bool = True) -> Optional[bytes]:
        """
        Serialize a shard for network transmission.
        
        Args:
            node_id: ID of the node
            compress: Whether to compress the data
            
        Returns:
            Serialized bytes or None if failed
        """
        try:
            if node_id not in self.shards:
                logger.error(f"Node {node_id} has no assigned shard")
                return None
            
            if self.train_dataset is None:
                logger.error("Dataset not loaded")
                return None
            
            # Get shard data
            indices = self.shards[node_id]
            shard_data = []
            
            for idx in indices:
                data, label = self.train_dataset[idx]
                # Convert to numpy for efficient serialization
                if isinstance(data, torch.Tensor):
                    data = data.numpy()
                if isinstance(label, torch.Tensor):
                    label = label.item()
                shard_data.append((data, label))
            
            # Serialize
            serialized = pickle.dumps(shard_data, protocol=pickle.HIGHEST_PROTOCOL)
            
            # Compress if requested
            if compress:
                serialized = gzip.compress(serialized, compresslevel=6)
            
            logger.info(
                f"Shard serialized for {node_id}: "
                f"{len(serialized)} bytes "
                f"({'compressed' if compress else 'uncompressed'})"
            )
            
            return serialized
            
        except Exception as e:
            logger.error(f"Failed to serialize shard for {node_id}: {e}", exc_info=True)
            return None
    
    def deserialize_shard(
        self,
        serialized_data: bytes,
        compressed: bool = True
    ) -> Optional[List[Tuple[np.ndarray, int]]]:
        """
        Deserialize a shard from bytes.
        
        Args:
            serialized_data: Serialized shard data
            compressed: Whether data is compressed
            
        Returns:
            List of (data, label) tuples or None if failed
        """
        try:
            # Decompress if needed
            if compressed:
                serialized_data = gzip.decompress(serialized_data)
            
            # Deserialize
            shard_data = pickle.loads(serialized_data)
            
            logger.info(f"Shard deserialized: {len(shard_data)} samples")
            return shard_data
            
        except Exception as e:
            logger.error(f"Failed to deserialize shard: {e}", exc_info=True)
            return None
    
    def cache_shards(self, config_hash: Optional[str] = None) -> bool:
        """
        Cache prepared shards to disk.
        
        Args:
            config_hash: Hash of configuration for cache validation
            
        Returns:
            bool: True if successful
        """
        try:
            cache_file = self.cache_dir / f"shards_{self.dataset_type.value}.pkl"
            
            cache_data = {
                "shards": self.shards,
                "orphaned_shards": self.orphaned_shards,
                "shard_metadata": self.shard_metadata,
                "config_hash": config_hash or self._compute_config_hash(),
                "dataset_type": self.dataset_type.value,
                "num_classes": self.num_classes,
            }
            
            with open(cache_file, "wb") as f:
                pickle.dump(cache_data, f)
            
            self.cache_valid = True
            self.cache_hash = cache_data["config_hash"]
            
            logger.info(f"Shards cached to {cache_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache shards: {e}", exc_info=True)
            return False
    
    def load_cache(self, config_hash: Optional[str] = None) -> bool:
        """
        Load shards from cache.
        
        Args:
            config_hash: Hash of configuration for validation
            
        Returns:
            bool: True if successful and cache valid
        """
        try:
            cache_file = self.cache_dir / f"shards_{self.dataset_type.value}.pkl"
            
            if not cache_file.exists():
                logger.info("No cache file found")
                return False
            
            with open(cache_file, "rb") as f:
                cache_data = pickle.load(f)
            
            # Validate cache
            current_hash = config_hash or self._compute_config_hash()
            if cache_data.get("config_hash") != current_hash:
                logger.warning("Cache invalid: configuration mismatch")
                return False
            
            # Load data
            self.shards = cache_data["shards"]
            self.orphaned_shards = cache_data["orphaned_shards"]
            self.shard_metadata = cache_data["shard_metadata"]
            self.num_classes = cache_data["num_classes"]
            
            self.cache_valid = True
            self.cache_hash = cache_data["config_hash"]
            
            logger.info(f"Shards loaded from cache: {len(self.shards)} assigned")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load cache: {e}", exc_info=True)
            return False
    
    def invalidate_cache(self) -> None:
        """Invalidate the cache."""
        self.cache_valid = False
        self.cache_hash = None
        logger.info("Cache invalidated")
    
    def get_shard_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about current shards.
        
        Returns:
            Dict with shard statistics
        """
        assigned_sizes = [len(shard) for shard in self.shards.values()]
        orphaned_sizes = [len(shard) for shard in self.orphaned_shards]
        
        stats = {
            "num_assigned_shards": len(self.shards),
            "num_orphaned_shards": len(self.orphaned_shards),
            "total_shards": len(self.shards) + len(self.orphaned_shards),
        }
        
        if assigned_sizes:
            stats.update({
                "assigned_min_size": min(assigned_sizes),
                "assigned_max_size": max(assigned_sizes),
                "assigned_avg_size": np.mean(assigned_sizes),
            })
        
        if orphaned_sizes:
            stats.update({
                "orphaned_min_size": min(orphaned_sizes),
                "orphaned_max_size": max(orphaned_sizes),
                "orphaned_avg_size": np.mean(orphaned_sizes),
            })
        
        return stats
    
    def _compute_checksum(self, indices: List[int]) -> str:
        """Compute checksum for a shard."""
        data = str(sorted(indices)).encode()
        return hashlib.md5(data).hexdigest()
    
    def _compute_config_hash(self) -> str:
        """Compute hash of current configuration."""
        config_str = f"{self.dataset_type.value}_{len(self.shards) + len(self.orphaned_shards)}"
        return hashlib.md5(config_str.encode()).hexdigest()
