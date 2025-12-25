"""
Blockchain contribution tracking models.
"""

from typing import Optional, Dict, List
from pydantic import BaseModel, Field
from datetime import datetime


class BlockchainContribution(BaseModel):
    """Node contribution data for blockchain recording."""
    
    # Identity
    node_id: str = Field(..., description="Node identifier")
    wallet_address: str = Field(..., description="Node's wallet address")
    session_id: str = Field(..., description="Training session ID")
    
    # Contribution Data
    epoch: int = Field(..., ge=0, description="Epoch number")
    compute_time_seconds: float = Field(..., ge=0, description="Total compute time")
    gradients_accepted: int = Field(..., ge=0, description="Number of accepted gradients")
    gradients_rejected: int = Field(default=0, ge=0, description="Rejected gradients")
    samples_processed: int = Field(..., ge=0, description="Total samples processed")
    
    # Quality Metrics
    average_loss: float = Field(..., description="Average loss achieved")
    average_accuracy: Optional[float] = Field(None, description="Average accuracy")
    gradient_quality_score: float = Field(
        default=1.0,
        ge=0,
        le=1,
        description="Quality score for gradients"
    )
    network_reliability_score: float = Field(
        default=1.0,
        ge=0,
        le=1,
        description="Network reliability"
    )
    
    # Contribution Score
    contribution_score: float = Field(
        default=0.0,
        ge=0,
        description="Calculated contribution score"
    )
    reward_weight: float = Field(
        default=1.0,
        ge=0,
        description="Weight for reward calculation"
    )
    
    # Blockchain Data
    recorded_on_chain: bool = Field(default=False, description="Recorded to blockchain")
    transaction_hash: Optional[str] = Field(None, description="Transaction hash")
    block_number: Optional[int] = Field(None, description="Block number")
    
    # Timestamp
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When contribution was recorded"
    )
    
    def calculate_contribution_score(self) -> float:
        """
        Calculate overall contribution score based on multiple factors.
        
        Formula:
        score = compute_time * gradient_quality * network_reliability * acceptance_rate
        """
        # Calculate acceptance rate
        total_gradients = self.gradients_accepted + self.gradients_rejected
        if total_gradients > 0:
            acceptance_rate = self.gradients_accepted / total_gradients
        else:
            acceptance_rate = 1.0
        
        # Calculate score
        score = (
            self.compute_time_seconds *
            self.gradient_quality_score *
            self.network_reliability_score *
            acceptance_rate
        )
        
        self.contribution_score = score
        return score
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class SessionContributions(BaseModel):
    """All contributions for a training session."""
    
    session_id: str = Field(..., description="Training session ID")
    contributions: Dict[str, List[BlockchainContribution]] = Field(
        default_factory=dict,
        description="Contributions per node (node_id -> list of contributions)"
    )
    
    # Session Info
    start_time: datetime = Field(
        default_factory=datetime.utcnow,
        description="Session start time"
    )
    end_time: Optional[datetime] = Field(None, description="Session end time")
    total_epochs: int = Field(default=0, ge=0, description="Total epochs")
    
    # Aggregates
    total_compute_time: float = Field(default=0.0, ge=0, description="Total compute time")
    total_samples_processed: int = Field(default=0, ge=0, description="Total samples")
    
    def add_contribution(self, contribution: BlockchainContribution):
        """Add a contribution for a node."""
        node_id = contribution.node_id
        if node_id not in self.contributions:
            self.contributions[node_id] = []
        self.contributions[node_id].append(contribution)
        
        # Update aggregates
        self.total_compute_time += contribution.compute_time_seconds
        self.total_samples_processed += contribution.samples_processed
    
    def get_node_contributions(self, node_id: str) -> List[BlockchainContribution]:
        """Get all contributions for a specific node."""
        return self.contributions.get(node_id, [])
    
    def get_total_contribution_score(self, node_id: str) -> float:
        """Get total contribution score for a node."""
        contributions = self.get_node_contributions(node_id)
        return sum(c.contribution_score for c in contributions)
    
    def get_all_nodes(self) -> List[str]:
        """Get list of all contributing nodes."""
        return list(self.contributions.keys())
    
    def calculate_reward_distribution(
        self, total_reward_pool: float
    ) -> Dict[str, float]:
        """
        Calculate reward distribution based on contributions.
        
        Args:
            total_reward_pool: Total rewards to distribute
            
        Returns:
            Dictionary mapping node_id to reward amount
        """
        # Calculate total contribution score
        total_score = sum(
            self.get_total_contribution_score(node_id)
            for node_id in self.get_all_nodes()
        )
        
        if total_score == 0:
            # Equal distribution if no meaningful contributions
            num_nodes = len(self.get_all_nodes())
            return {
                node_id: total_reward_pool / num_nodes
                for node_id in self.get_all_nodes()
            }
        
        # Proportional distribution
        return {
            node_id: (self.get_total_contribution_score(node_id) / total_score) * total_reward_pool
            for node_id in self.get_all_nodes()
        }
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class RewardDistribution(BaseModel):
    """Reward distribution information."""
    
    session_id: str = Field(..., description="Training session ID")
    epoch: Optional[int] = Field(None, description="Epoch (None for full session)")
    
    # Reward Pool
    total_reward_pool: float = Field(..., gt=0, description="Total rewards to distribute")
    currency: str = Field(default="MONAD", description="Reward currency")
    
    # Distribution
    rewards: Dict[str, float] = Field(
        ...,
        description="Node ID to reward amount mapping"
    )
    
    # Blockchain
    calculated_on_chain: bool = Field(
        default=False,
        description="Calculated on-chain"
    )
    distributed: bool = Field(default=False, description="Rewards distributed")
    transaction_hashes: Dict[str, str] = Field(
        default_factory=dict,
        description="Node ID to transaction hash"
    )
    
    # Timestamp
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When distribution was calculated"
    )
    
    def get_node_reward(self, node_id: str) -> float:
        """Get reward for specific node."""
        return self.rewards.get(node_id, 0.0)
    
    def mark_distributed(self, node_id: str, tx_hash: str):
        """Mark reward as distributed for a node."""
        self.transaction_hashes[node_id] = tx_hash
        # Check if all distributed
        if len(self.transaction_hashes) == len(self.rewards):
            self.distributed = True
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
