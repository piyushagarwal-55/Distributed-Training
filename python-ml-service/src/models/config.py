"""
Configuration data models using Pydantic for validation.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator
from enum import Enum
import json


class DatasetType(str, Enum):
    """Supported dataset types."""
    MNIST = "mnist"
    CIFAR10 = "cifar10"
    CIFAR100 = "cifar100"
    CUSTOM = "custom"


class ModelArchitecture(str, Enum):
    """Supported model architectures."""
    SIMPLE_CNN = "simple_cnn"
    RESNET18 = "resnet18"
    RESNET50 = "resnet50"
    VGG16 = "vgg16"
    CUSTOM = "custom"


class AggregationStrategy(str, Enum):
    """Gradient aggregation strategies."""
    SIMPLE_AVERAGE = "simple_average"
    WEIGHTED_AVERAGE = "weighted_average"
    FEDERATED_AVERAGING = "federated_averaging"


class TrainingConfig(BaseModel):
    """Main training configuration."""
    
    # Model Configuration
    model_architecture: ModelArchitecture = Field(
        default=ModelArchitecture.SIMPLE_CNN,
        description="Neural network architecture to use"
    )
    
    # Dataset Configuration
    dataset: DatasetType = Field(
        default=DatasetType.MNIST,
        description="Dataset to train on"
    )
    dataset_path: Optional[str] = Field(
        default=None,
        description="Path to custom dataset"
    )
    
    # Training Hyperparameters
    learning_rate: float = Field(
        default=0.001,
        gt=0,
        description="Learning rate for optimizer"
    )
    batch_size: int = Field(
        default=64,
        gt=0,
        description="Batch size per node"
    )
    epochs: int = Field(
        default=10,
        gt=0,
        description="Number of training epochs"
    )
    steps_per_epoch: Optional[int] = Field(
        default=None,
        description="Number of steps per epoch (calculated if not provided)"
    )
    optimizer: str = Field(
        default="adam",
        description="Optimizer type (adam, sgd, rmsprop)"
    )
    
    # Distributed Training Settings
    num_nodes: int = Field(
        default=5,
        ge=1,
        description="Number of GPU nodes to simulate"
    )
    aggregation_strategy: AggregationStrategy = Field(
        default=AggregationStrategy.SIMPLE_AVERAGE,
        description="Gradient aggregation method"
    )
    synchronous: bool = Field(
        default=True,
        description="Synchronous vs asynchronous aggregation"
    )
    timeout_seconds: float = Field(
        default=30.0,
        gt=0,
        description="Timeout for gradient collection"
    )
    
    # Device Configuration
    device: str = Field(
        default="cuda",
        description="Device to use (cuda, cpu, mps)"
    )
    
    # Checkpointing
    save_checkpoints: bool = Field(
        default=True,
        description="Whether to save model checkpoints"
    )
    checkpoint_interval: int = Field(
        default=1,
        gt=0,
        description="Save checkpoint every N epochs"
    )
    checkpoint_dir: str = Field(
        default="./checkpoints",
        description="Directory to save checkpoints"
    )
    
    @field_validator('learning_rate')
    @classmethod
    def validate_learning_rate(cls, v):
        if v <= 0 or v > 1:
            raise ValueError("Learning rate must be between 0 and 1")
        return v
    
    @classmethod
    def from_file(cls, filepath: str) -> "TrainingConfig":
        """Load configuration from JSON file."""
        with open(filepath, 'r') as f:
            config_dict = json.load(f)
        return cls(**config_dict)
    
    def to_file(self, filepath: str):
        """Save configuration to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.model_dump(), f, indent=2)


class NetworkConfig(BaseModel):
    """Network simulation configuration."""
    
    enable_simulation: bool = Field(
        default=True,
        description="Enable network simulation"
    )
    
    # Latency Settings
    base_latency_ms: float = Field(
        default=50.0,
        ge=0,
        description="Base network latency in milliseconds"
    )
    latency_variance_ms: float = Field(
        default=20.0,
        ge=0,
        description="Variance in latency"
    )
    
    # Packet Loss
    packet_loss_rate: float = Field(
        default=0.01,
        ge=0,
        le=1,
        description="Probability of packet loss (0-1)"
    )
    
    # Bandwidth
    bandwidth_mbps: Optional[float] = Field(
        default=None,
        ge=0,
        description="Simulated bandwidth in Mbps"
    )
    
    # Network Profiles
    profiles: Dict[str, Dict[str, float]] = Field(
        default_factory=lambda: {
            "perfect": {"latency": 0, "packet_loss": 0},
            "good": {"latency": 20, "packet_loss": 0.001},
            "average": {"latency": 100, "packet_loss": 0.01},
            "poor": {"latency": 300, "packet_loss": 0.05},
        },
        description="Named network profiles"
    )
    
    # Per-Node Configuration
    node_profiles: Dict[str, str] = Field(
        default_factory=dict,
        description="Network profile per node ID"
    )


class BlockchainConfig(BaseModel):
    """Blockchain integration configuration."""
    
    enabled: bool = Field(
        default=True,
        description="Enable blockchain integration"
    )
    
    # Monad Configuration
    rpc_endpoint: str = Field(
        default="http://127.0.0.1:8545",
        description="Monad RPC endpoint (use local for testing)"
    )
    chain_id: int = Field(
        default=1337,
        description="Chain ID (1337 for local, 41454 for Monad testnet)"
    )
    
    # Contract Addresses
    training_registry_address: Optional[str] = Field(
        default=None,
        description="TrainingRegistry contract address"
    )
    contribution_tracker_address: Optional[str] = Field(
        default=None,
        description="ContributionTracker contract address"
    )
    reward_distributor_address: Optional[str] = Field(
        default=None,
        description="RewardDistributor contract address"
    )
    
    # ABI Directory
    abi_directory: str = Field(
        default="../smart-contracts/artifacts/contracts",
        description="Directory containing contract ABIs"
    )
    
    # Transaction Settings
    gas_limit: int = Field(
        default=500000,
        gt=0,
        description="Gas limit for transactions"
    )
    gas_price_gwei: Optional[float] = Field(
        default=None,
        description="Gas price in Gwei (None for automatic)"
    )
    max_retries: int = Field(
        default=3,
        ge=1,
        description="Maximum transaction retry attempts"
    )
    wait_for_confirmation: bool = Field(
        default=True,
        description="Wait for transaction confirmation"
    )
    confirmation_timeout: int = Field(
        default=120,
        gt=0,
        description="Timeout for transaction confirmation (seconds)"
    )
    
    # Recording Settings
    record_per_epoch: bool = Field(
        default=True,
        description="Record contributions every epoch"
    )
    batch_size: int = Field(
        default=10,
        gt=0,
        description="Number of contributions per batch transaction"
    )
    enable_async_transactions: bool = Field(
        default=False,
        description="Enable async transaction processing"
    )
    
    # Reward Settings
    reward_strategy: int = Field(
        default=0,
        ge=0,
        le=3,
        description="Reward distribution strategy (0=Proportional, 1=Tiered, 2=Performance, 3=Hybrid)"
    )
    total_reward_pool_eth: float = Field(
        default=1.0,
        gt=0,
        description="Total reward pool in ETH"
    )
    
    # Private Key (Should be loaded from environment)
    private_key: Optional[str] = Field(
        default=None,
        description="Private key for signing transactions"
    )
    
    @field_validator('private_key')
    @classmethod
    def validate_private_key(cls, v):
        if v and not v.startswith('0x'):
            return f'0x{v}'
        return v


class SystemConfig(BaseModel):
    """Complete system configuration."""
    
    training: TrainingConfig = Field(
        default_factory=TrainingConfig,
        description="Training configuration"
    )
    network: NetworkConfig = Field(
        default_factory=NetworkConfig,
        description="Network simulation configuration"
    )
    blockchain: BlockchainConfig = Field(
        default_factory=BlockchainConfig,
        description="Blockchain configuration"
    )
    
    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    log_file: Optional[str] = Field(
        default="logs/training.log",
        description="Log file path"
    )
    
    @classmethod
    def from_file(cls, filepath: str) -> "SystemConfig":
        """Load complete configuration from JSON file."""
        with open(filepath, 'r') as f:
            config_dict = json.load(f)
        return cls(**config_dict)
    
    def to_file(self, filepath: str):
        """Save configuration to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.model_dump(), f, indent=2)
