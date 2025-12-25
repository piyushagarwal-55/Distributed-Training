"""
Metrics data models for training, network, and gradient updates.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import numpy as np


class TrainingMetrics(BaseModel):
    """Training performance metrics."""
    
    # Identity
    node_id: str = Field(..., description="Node that generated these metrics")
    epoch: int = Field(..., ge=0, description="Current epoch")
    step: int = Field(..., ge=0, description="Current step/iteration")
    
    # Loss and Accuracy
    loss: float = Field(..., description="Training loss value")
    accuracy: Optional[float] = Field(None, ge=0, le=1, description="Training accuracy")
    
    # Performance
    samples_processed: int = Field(..., ge=0, description="Number of samples processed")
    time_taken_seconds: float = Field(..., gt=0, description="Time for this step")
    samples_per_second: float = Field(..., gt=0, description="Training throughput")
    
    # Gradient Statistics
    gradient_norm: Optional[float] = Field(None, description="L2 norm of gradients")
    gradient_mean: Optional[float] = Field(None, description="Mean gradient value")
    gradient_std: Optional[float] = Field(None, description="Gradient standard deviation")
    
    # Timestamp
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When metrics were recorded"
    )
    
    # Additional Info
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional custom metrics"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class NetworkMetrics(BaseModel):
    """Network performance and quality metrics."""
    
    # Identity
    node_id: str = Field(..., description="Node being measured")
    coordinator_id: str = Field(default="coordinator", description="Coordinator ID")
    
    # Latency Measurements
    latency_ms: float = Field(..., ge=0, description="Round-trip latency in milliseconds")
    min_latency_ms: Optional[float] = Field(None, description="Minimum observed latency")
    max_latency_ms: Optional[float] = Field(None, description="Maximum observed latency")
    avg_latency_ms: Optional[float] = Field(None, description="Average latency")
    
    # Packet Loss
    packet_loss_rate: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="Packet loss rate (0-1)"
    )
    
    # Bandwidth
    bandwidth_mbps: Optional[float] = Field(
        None,
        ge=0,
        description="Measured bandwidth in Mbps"
    )
    
    # Connection Quality
    jitter_ms: Optional[float] = Field(
        None,
        ge=0,
        description="Latency variation (jitter)"
    )
    connection_stable: bool = Field(
        default=True,
        description="Whether connection is stable"
    )
    
    # Communication Stats
    messages_sent: int = Field(default=0, ge=0, description="Total messages sent")
    messages_received: int = Field(default=0, ge=0, description="Messages received")
    messages_failed: int = Field(default=0, ge=0, description="Failed transmissions")
    bytes_sent: int = Field(default=0, ge=0, description="Total bytes transmitted")
    bytes_received: int = Field(default=0, ge=0, description="Total bytes received")
    
    # Quality Score
    quality_score: float = Field(
        default=1.0,
        ge=0,
        le=1,
        description="Overall quality score (0-1)"
    )
    
    # Timestamp
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When metrics were measured"
    )
    
    # Measurement Window
    window_seconds: float = Field(
        default=10.0,
        gt=0,
        description="Time window for these measurements"
    )
    
    def calculate_quality_score(self) -> float:
        """Calculate overall network quality score."""
        # Latency score (lower is better, normalized to 0-1)
        latency_score = max(0, 1 - (self.latency_ms / 1000))  # 1000ms = score 0
        
        # Packet loss score
        loss_score = 1 - self.packet_loss_rate
        
        # Success rate score
        total_messages = self.messages_sent + self.messages_failed
        if total_messages > 0:
            success_score = self.messages_sent / total_messages
        else:
            success_score = 1.0
        
        # Weighted average
        quality = (0.4 * latency_score + 0.3 * loss_score + 0.3 * success_score)
        
        self.quality_score = quality
        return quality
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class GradientUpdate(BaseModel):
    """Gradient update transmission format."""
    
    # Identity
    node_id: str = Field(..., description="Node submitting gradients")
    update_id: str = Field(..., description="Unique update identifier")
    
    # Training Context
    epoch: int = Field(..., ge=0, description="Epoch number")
    step: int = Field(..., ge=0, description="Step number")
    batch_size: int = Field(..., gt=0, description="Batch size used")
    
    # Gradient Data (serialized as list for JSON compatibility)
    gradient_data: List[List[float]] = Field(
        ...,
        description="Flattened gradient tensors"
    )
    gradient_shapes: List[List[int]] = Field(
        ...,
        description="Original shapes of gradient tensors"
    )
    
    # Gradient Statistics
    gradient_norm: float = Field(..., description="L2 norm of gradients")
    num_parameters: int = Field(..., gt=0, description="Total number of parameters")
    
    # Compression Info
    is_compressed: bool = Field(default=False, description="Whether data is compressed")
    compression_ratio: Optional[float] = Field(
        None,
        description="Compression ratio if compressed"
    )
    
    # Local Training Metrics
    local_loss: float = Field(..., description="Loss on local data")
    local_accuracy: Optional[float] = Field(None, description="Accuracy on local data")
    compute_time_seconds: float = Field(..., gt=0, description="Time to compute gradients")
    
    # Network Metrics
    transmission_time_seconds: Optional[float] = Field(
        None,
        description="Time to transmit"
    )
    
    # Status
    success: bool = Field(default=True, description="Whether update was successful")
    error_message: Optional[str] = Field(None, description="Error if failed")
    
    # Timestamp
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When update was created"
    )
    
    # Validation
    checksum: Optional[str] = Field(None, description="Data integrity checksum")
    
    def validate_gradient_data(self) -> bool:
        """Validate that gradient data is valid."""
        if not self.gradient_data or not self.gradient_shapes:
            return False
        
        # Check that number of tensors matches
        if len(self.gradient_data) != len(self.gradient_shapes):
            return False
        
        # Check for NaN or Inf
        for tensor in self.gradient_data:
            if any(not np.isfinite(val) for row in tensor for val in row):
                return False
        
        return True
    
    def get_data_size_mb(self) -> float:
        """Calculate size of gradient data in MB."""
        total_elements = sum(len(row) for tensor in self.gradient_data for row in tensor)
        # Assuming float32 (4 bytes per element)
        size_bytes = total_elements * 4
        return size_bytes / (1024 * 1024)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class AggregatedMetrics(BaseModel):
    """Aggregated metrics across all nodes for an epoch."""
    
    # Identity
    epoch: int = Field(..., ge=0, description="Epoch number")
    session_id: str = Field(..., description="Training session ID")
    
    # Training Performance
    average_loss: float = Field(..., description="Average loss across nodes")
    average_accuracy: Optional[float] = Field(None, description="Average accuracy")
    best_loss: float = Field(..., description="Best loss achieved")
    best_accuracy: Optional[float] = Field(None, description="Best accuracy achieved")
    
    # Throughput
    total_samples_processed: int = Field(..., ge=0, description="Total samples this epoch")
    average_throughput: float = Field(..., gt=0, description="Avg samples/sec")
    total_time_seconds: float = Field(..., gt=0, description="Total time for epoch")
    
    # Node Participation
    num_nodes_participated: int = Field(..., gt=0, description="Nodes that contributed")
    num_nodes_excluded: int = Field(default=0, ge=0, description="Nodes excluded")
    
    # Network Health
    average_latency_ms: Optional[float] = Field(None, description="Average latency")
    average_packet_loss: Optional[float] = Field(None, description="Average packet loss")
    average_network_quality: Optional[float] = Field(None, description="Avg quality score")
    
    # Adaptation Info
    adaptations_made: int = Field(default=0, ge=0, description="Number of adaptations")
    nodes_adjusted: List[str] = Field(
        default_factory=list,
        description="Node IDs that were adjusted"
    )
    
    # Blockchain
    recorded_on_chain: bool = Field(default=False, description="Recorded to blockchain")
    transaction_hash: Optional[str] = Field(None, description="Blockchain tx hash")
    
    # Timestamp
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When metrics were aggregated"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class MetricsHistory(BaseModel):
    """Historical metrics storage."""
    
    training_metrics: List[TrainingMetrics] = Field(
        default_factory=list,
        description="Training metrics history"
    )
    network_metrics: List[NetworkMetrics] = Field(
        default_factory=list,
        description="Network metrics history"
    )
    aggregated_metrics: List[AggregatedMetrics] = Field(
        default_factory=list,
        description="Aggregated epoch metrics"
    )
    
    def add_training_metric(self, metric: TrainingMetrics):
        """Add training metric to history."""
        self.training_metrics.append(metric)
    
    def add_network_metric(self, metric: NetworkMetrics):
        """Add network metric to history."""
        self.network_metrics.append(metric)
    
    def add_aggregated_metric(self, metric: AggregatedMetrics):
        """Add aggregated metric to history."""
        self.aggregated_metrics.append(metric)
    
    def get_latest_training_metrics(self, n: int = 10) -> List[TrainingMetrics]:
        """Get most recent training metrics."""
        return self.training_metrics[-n:]
    
    def get_metrics_for_node(self, node_id: str) -> List[TrainingMetrics]:
        """Get all metrics for specific node."""
        return [m for m in self.training_metrics if m.node_id == node_id]
    
    def get_metrics_for_epoch(self, epoch: int) -> List[TrainingMetrics]:
        """Get all metrics for specific epoch."""
        return [m for m in self.training_metrics if m.epoch == epoch]
