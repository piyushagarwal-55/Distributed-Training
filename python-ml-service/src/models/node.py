"""
Node metadata and status models.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class NodeStatus(str, Enum):
    """Node operational status."""
    INITIALIZING = "initializing"
    READY = "ready"
    TRAINING = "training"
    IDLE = "idle"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    ERROR = "error"


class NodeMetadata(BaseModel):
    """GPU node metadata and specifications."""
    
    # Identification
    node_id: str = Field(
        ...,
        description="Unique identifier for the node"
    )
    node_address: str = Field(
        ...,
        description="Network address (IP:port)"
    )
    
    # Status
    status: NodeStatus = Field(
        default=NodeStatus.INITIALIZING,
        description="Current node status"
    )
    
    # GPU Specifications (Simulated)
    gpu_model: str = Field(
        default="Simulated-GPU",
        description="GPU model name"
    )
    gpu_memory_gb: float = Field(
        default=8.0,
        gt=0,
        description="GPU memory in GB"
    )
    compute_capability: float = Field(
        default=1.0,
        gt=0,
        description="Relative compute performance (1.0 = baseline)"
    )
    
    # Network Information
    region: Optional[str] = Field(
        default=None,
        description="Geographic region"
    )
    network_profile: str = Field(
        default="average",
        description="Network quality profile"
    )
    
    # Operational Metrics
    current_batch_size: int = Field(
        default=64,
        gt=0,
        description="Current batch size assigned to this node"
    )
    data_shard_id: Optional[int] = Field(
        default=None,
        description="Assigned data shard index"
    )
    
    # Timestamps
    registered_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When node was registered"
    )
    last_heartbeat: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last heartbeat timestamp"
    )
    last_update: Optional[datetime] = Field(
        default=None,
        description="Last successful update"
    )
    
    # Performance Tracking
    total_gradients_submitted: int = Field(
        default=0,
        ge=0,
        description="Total number of gradient updates submitted"
    )
    successful_updates: int = Field(
        default=0,
        ge=0,
        description="Number of successful updates"
    )
    failed_updates: int = Field(
        default=0,
        ge=0,
        description="Number of failed updates"
    )
    total_compute_time_seconds: float = Field(
        default=0.0,
        ge=0,
        description="Cumulative compute time"
    )
    
    # Health Metrics
    average_latency_ms: Optional[float] = Field(
        default=None,
        description="Average network latency"
    )
    packet_loss_rate: Optional[float] = Field(
        default=None,
        description="Observed packet loss rate"
    )
    reliability_score: float = Field(
        default=1.0,
        ge=0,
        le=1,
        description="Reliability score (0-1)"
    )
    
    # Blockchain
    wallet_address: Optional[str] = Field(
        default=None,
        description="Ethereum/Monad wallet address for rewards"
    )
    
    # Additional Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional custom metadata"
    )
    
    def update_heartbeat(self):
        """Update last heartbeat timestamp."""
        self.last_heartbeat = datetime.utcnow()
    
    def update_status(self, status: NodeStatus):
        """Update node status."""
        self.status = status
        self.last_update = datetime.utcnow()
    
    def record_successful_update(self, compute_time: float):
        """Record a successful gradient update."""
        self.successful_updates += 1
        self.total_gradients_submitted += 1
        self.total_compute_time_seconds += compute_time
        self.last_update = datetime.utcnow()
    
    def record_failed_update(self):
        """Record a failed gradient update."""
        self.failed_updates += 1
        self.total_gradients_submitted += 1
    
    def calculate_success_rate(self) -> float:
        """Calculate success rate of updates."""
        if self.total_gradients_submitted == 0:
            return 1.0
        return self.successful_updates / self.total_gradients_submitted
    
    def is_healthy(self) -> bool:
        """Check if node is in a healthy state."""
        return self.status in [NodeStatus.READY, NodeStatus.TRAINING, NodeStatus.IDLE]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return self.model_dump()


class NodeRegistry(BaseModel):
    """Registry of all GPU nodes."""
    
    nodes: Dict[str, NodeMetadata] = Field(
        default_factory=dict,
        description="Map of node_id to NodeMetadata"
    )
    
    def register_node(self, node: NodeMetadata) -> bool:
        """Register a new node."""
        self.nodes[node.node_id] = node
        return True
    
    def add_node(self, node: NodeMetadata) -> bool:
        """Add a new node (alias for register_node)."""
        return self.register_node(node)
    
    def update_node(self, node: NodeMetadata) -> bool:
        """Update existing node."""
        if node.node_id in self.nodes:
            self.nodes[node.node_id] = node
            return True
        return False
    
    def remove_node(self, node_id: str) -> bool:
        """Remove a node and return success status."""
        if node_id in self.nodes:
            del self.nodes[node_id]
            return True
        return False
    
    def get_node(self, node_id: str) -> Optional[NodeMetadata]:
        """Get node metadata by ID."""
        return self.nodes.get(node_id)
    
    def get_all_nodes(self) -> list[NodeMetadata]:
        """Get list of all nodes."""
        return list(self.nodes.values())
    
    def get_active_nodes(self) -> list[NodeMetadata]:
        """Get list of active (healthy) nodes."""
        return [node for node in self.nodes.values() if node.is_healthy()]
    
    def get_nodes_by_status(self, status: NodeStatus) -> list[NodeMetadata]:
        """Get nodes with specific status."""
        return [node for node in self.nodes.values() if node.status == status]
    
    def update_node_status(self, node_id: str, status: NodeStatus):
        """Update status of a specific node."""
        if node_id in self.nodes:
            self.nodes[node_id].update_status(status)
    
    def count_nodes(self) -> int:
        """Get total number of registered nodes."""
        return len(self.nodes)
    
    def count_active_nodes(self) -> int:
        """Get number of active nodes."""
        return len(self.get_active_nodes())    
    def get_active_count(self) -> int:
        """Alias for count_active_nodes for backward compatibility."""
        return self.count_active_nodes()