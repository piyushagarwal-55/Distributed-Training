"""
Reward Calculator - Calculates and distributes rewards based on contributions.

This module implements multiple reward distribution strategies and handles
the payment logic for compensating nodes fairly based on their contributions.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import statistics

from .contribution_calculator import NodeContribution
from ..utils.logger import get_logger

logger = get_logger(__name__)


class RewardStrategy(Enum):
    """Reward distribution strategies."""
    PROPORTIONAL = 0      # Rewards proportional to contribution
    TIERED = 1           # Bonus for top contributors
    PERFORMANCE_BASED = 2  # Extra rewards for high quality
    HYBRID = 3           # Combination of strategies


@dataclass
class NodeReward:
    """Reward calculation for a single node."""
    
    node_id: str
    node_address: str
    contribution_score: int
    contribution_percentage: float
    base_reward: int
    bonus_reward: int
    total_reward: int
    tier: Optional[int] = None
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class RewardDistribution:
    """Complete reward distribution for a session."""
    
    session_id: str
    strategy: RewardStrategy
    total_pool: int
    total_distributed: int
    node_rewards: Dict[str, NodeReward]
    min_reward: int
    max_reward: int
    avg_reward: float
    
    def validate(self) -> bool:
        """Validate that distribution is correct."""
        calculated_total = sum(r.total_reward for r in self.node_rewards.values())
        
        # Allow 1% tolerance for rounding errors
        tolerance = self.total_pool * 0.01
        
        if abs(calculated_total - self.total_distributed) > tolerance:
            logger.error(f"[RewardCalc] Distribution mismatch: "
                        f"calculated={calculated_total}, distributed={self.total_distributed}")
            return False
        
        if self.total_distributed > self.total_pool:
            logger.error(f"[RewardCalc] Distribution exceeds pool: "
                        f"{self.total_distributed} > {self.total_pool}")
            return False
        
        return True


class RewardCalculator:
    """
    Calculates reward distributions based on node contributions.
    
    Supports multiple strategies:
    - Proportional: Simple proportional distribution
    - Tiered: Bonuses for top performers
    - Performance-based: Extra rewards for quality
    - Hybrid: Combination of multiple factors
    """
    
    def __init__(self, session_id: str, total_pool: int):
        """
        Initialize reward calculator.
        
        Args:
            session_id: Training session identifier
            total_pool: Total reward amount (in wei)
        """
        self.session_id = session_id
        self.total_pool = total_pool
        
        if total_pool <= 0:
            raise ValueError(f"Invalid reward pool: {total_pool}")
        
        logger.info(f"[RewardCalc] Initialized for session {session_id} "
                   f"with pool {total_pool} wei")
    
    def calculate_proportional(self, 
                               contributions: Dict[str, NodeContribution]) -> RewardDistribution:
        """
        Calculate rewards proportionally to contribution scores.
        
        Args:
            contributions: Dictionary of node contributions
            
        Returns:
            RewardDistribution object
        """
        logger.info(f"[RewardCalc] Calculating proportional rewards for {len(contributions)} nodes")
        
        if not contributions:
            raise ValueError("No contributions provided")
        
        # Calculate total contribution
        total_contribution = sum(c.final_score for c in contributions.values())
        
        if total_contribution == 0:
            raise ValueError("Total contribution is zero")
        
        logger.debug(f"[RewardCalc] Total contribution score: {total_contribution}")
        
        # Calculate proportional rewards
        node_rewards = {}
        total_distributed = 0
        
        for node_id, contrib in contributions.items():
            # Calculate percentage
            percentage = contrib.final_score / total_contribution
            
            # Calculate reward
            reward_amount = int((self.total_pool * contrib.final_score) / total_contribution)
            
            node_rewards[node_id] = NodeReward(
                node_id=node_id,
                node_address=contrib.node_address,
                contribution_score=contrib.final_score,
                contribution_percentage=percentage * 100,
                base_reward=reward_amount,
                bonus_reward=0,
                total_reward=reward_amount
            )
            
            total_distributed += reward_amount
            
            logger.debug(f"[RewardCalc] Node {node_id}: {percentage*100:.2f}% -> {reward_amount} wei")
        
        # Calculate statistics
        reward_amounts = [r.total_reward for r in node_rewards.values()]
        min_reward = min(reward_amounts)
        max_reward = max(reward_amounts)
        avg_reward = statistics.mean(reward_amounts)
        
        distribution = RewardDistribution(
            session_id=self.session_id,
            strategy=RewardStrategy.PROPORTIONAL,
            total_pool=self.total_pool,
            total_distributed=total_distributed,
            node_rewards=node_rewards,
            min_reward=min_reward,
            max_reward=max_reward,
            avg_reward=avg_reward
        )
        
        logger.info(f"[RewardCalc] Proportional distribution complete: "
                   f"{total_distributed} wei distributed, "
                   f"avg={avg_reward:.2f}, min={min_reward}, max={max_reward}")
        
        return distribution
    
    def calculate_tiered(self, 
                        contributions: Dict[str, NodeContribution]) -> RewardDistribution:
        """
        Calculate rewards with tiered bonuses for top contributors.
        
        Top 50% get 15% bonus, top 80% get 5% bonus.
        
        Args:
            contributions: Dictionary of node contributions
            
        Returns:
            RewardDistribution object
        """
        logger.info(f"[RewardCalc] Calculating tiered rewards for {len(contributions)} nodes")
        
        if not contributions:
            raise ValueError("No contributions provided")
        
        # Sort nodes by contribution score (descending)
        sorted_nodes = sorted(
            contributions.items(),
            key=lambda x: x[1].final_score,
            reverse=True
        )
        
        total_contribution = sum(c.final_score for c in contributions.values())
        
        if total_contribution == 0:
            raise ValueError("Total contribution is zero")
        
        # Calculate tier cutoffs
        node_count = len(sorted_nodes)
        tier1_cutoff = int(node_count * 0.50)  # Top 50%
        tier2_cutoff = int(node_count * 0.80)  # Top 80%
        
        logger.debug(f"[RewardCalc] Tier cutoffs: T1={tier1_cutoff}, T2={tier2_cutoff}")
        
        # Allocate 85% for base distribution, 15% for bonuses
        base_pool = int(self.total_pool * 0.85)
        bonus_pool = self.total_pool - base_pool
        
        logger.debug(f"[RewardCalc] Pools: base={base_pool}, bonus={bonus_pool}")
        
        # First pass: calculate base rewards
        node_rewards = {}
        total_distributed = 0
        
        for idx, (node_id, contrib) in enumerate(sorted_nodes):
            # Base reward (proportional)
            base_reward = int((base_pool * contrib.final_score) / total_contribution)
            
            # Determine tier
            if idx < tier1_cutoff:
                tier = 1
                # Top tier gets 15% bonus
                bonus_share = 0.15
            elif idx < tier2_cutoff:
                tier = 2
                # Second tier gets 5% bonus
                bonus_share = 0.05
            else:
                tier = 3
                # No bonus
                bonus_share = 0.0
            
            # Calculate bonus
            if bonus_share > 0:
                # Bonus proportional to contribution within bonus pool
                bonus_reward = int((bonus_pool * contrib.final_score * bonus_share) / total_contribution)
            else:
                bonus_reward = 0
            
            total_reward = base_reward + bonus_reward
            
            node_rewards[node_id] = NodeReward(
                node_id=node_id,
                node_address=contrib.node_address,
                contribution_score=contrib.final_score,
                contribution_percentage=(contrib.final_score / total_contribution) * 100,
                base_reward=base_reward,
                bonus_reward=bonus_reward,
                total_reward=total_reward,
                tier=tier
            )
            
            total_distributed += total_reward
            
            logger.debug(f"[RewardCalc] Node {node_id} (Tier {tier}): "
                        f"base={base_reward}, bonus={bonus_reward}, total={total_reward}")
        
        # Calculate statistics
        reward_amounts = [r.total_reward for r in node_rewards.values()]
        min_reward = min(reward_amounts)
        max_reward = max(reward_amounts)
        avg_reward = statistics.mean(reward_amounts)
        
        distribution = RewardDistribution(
            session_id=self.session_id,
            strategy=RewardStrategy.TIERED,
            total_pool=self.total_pool,
            total_distributed=total_distributed,
            node_rewards=node_rewards,
            min_reward=min_reward,
            max_reward=max_reward,
            avg_reward=avg_reward
        )
        
        logger.info(f"[RewardCalc] Tiered distribution complete: "
                   f"{total_distributed} wei distributed, "
                   f"avg={avg_reward:.2f}, min={min_reward}, max={max_reward}")
        
        return distribution
    
    def calculate_with_minimum(self,
                               contributions: Dict[str, NodeContribution],
                               min_percentage: float = 0.5) -> RewardDistribution:
        """
        Calculate rewards with minimum guarantee.
        
        Ensures all participants get at least min_percentage of average reward.
        
        Args:
            contributions: Dictionary of node contributions
            min_percentage: Minimum reward as percentage of average (0-1)
            
        Returns:
            RewardDistribution object
        """
        logger.info(f"[RewardCalc] Calculating rewards with {min_percentage*100}% minimum")
        
        if not contributions:
            raise ValueError("No contributions provided")
        
        node_count = len(contributions)
        total_contribution = sum(c.final_score for c in contributions.values())
        
        if total_contribution == 0:
            raise ValueError("Total contribution is zero")
        
        # Calculate average reward and minimum
        avg_reward = self.total_pool / node_count
        min_reward = int(avg_reward * min_percentage)
        
        logger.debug(f"[RewardCalc] Average reward: {avg_reward:.2f}, "
                    f"Minimum reward: {min_reward}")
        
        # First pass: calculate proportional rewards
        proportional_rewards = {}
        below_min_nodes = []
        below_min_total = 0
        
        for node_id, contrib in contributions.items():
            proportion = contrib.final_score / total_contribution
            reward = int(self.total_pool * proportion)
            proportional_rewards[node_id] = reward
            
            if reward < min_reward:
                below_min_nodes.append(node_id)
                below_min_total += (min_reward - reward)
        
        logger.debug(f"[RewardCalc] {len(below_min_nodes)} nodes below minimum, "
                    f"need {below_min_total} wei to bring up")
        
        # Second pass: adjust rewards
        node_rewards = {}
        total_distributed = 0
        
        if below_min_nodes:
            # Calculate reduction per above-minimum node
            above_min_nodes = [nid for nid in contributions.keys() 
                             if nid not in below_min_nodes]
            
            if above_min_nodes:
                reduction_per_node = below_min_total / len(above_min_nodes)
                logger.debug(f"[RewardCalc] Reduction per above-min node: {reduction_per_node:.2f}")
            else:
                # All nodes below minimum, distribute equally
                reduction_per_node = 0
                min_reward = self.total_pool // node_count
                logger.warning("[RewardCalc] All nodes below minimum, using equal distribution")
            
            for node_id, contrib in contributions.items():
                if node_id in below_min_nodes:
                    final_reward = min_reward
                else:
                    final_reward = int(proportional_rewards[node_id] - reduction_per_node)
                    # Ensure doesn't go below minimum
                    final_reward = max(min_reward, final_reward)
                
                node_rewards[node_id] = NodeReward(
                    node_id=node_id,
                    node_address=contrib.node_address,
                    contribution_score=contrib.final_score,
                    contribution_percentage=(contrib.final_score / total_contribution) * 100,
                    base_reward=proportional_rewards[node_id],
                    bonus_reward=final_reward - proportional_rewards[node_id],
                    total_reward=final_reward
                )
                
                total_distributed += final_reward
        else:
            # All rewards above minimum, use proportional
            for node_id, contrib in contributions.items():
                reward = proportional_rewards[node_id]
                
                node_rewards[node_id] = NodeReward(
                    node_id=node_id,
                    node_address=contrib.node_address,
                    contribution_score=contrib.final_score,
                    contribution_percentage=(contrib.final_score / total_contribution) * 100,
                    base_reward=reward,
                    bonus_reward=0,
                    total_reward=reward
                )
                
                total_distributed += reward
        
        # Calculate statistics
        reward_amounts = [r.total_reward for r in node_rewards.values()]
        actual_min = min(reward_amounts)
        actual_max = max(reward_amounts)
        actual_avg = statistics.mean(reward_amounts)
        
        distribution = RewardDistribution(
            session_id=self.session_id,
            strategy=RewardStrategy.PERFORMANCE_BASED,
            total_pool=self.total_pool,
            total_distributed=total_distributed,
            node_rewards=node_rewards,
            min_reward=actual_min,
            max_reward=actual_max,
            avg_reward=actual_avg
        )
        
        logger.info(f"[RewardCalc] Minimum-guarantee distribution complete: "
                   f"{total_distributed} wei distributed, "
                   f"avg={actual_avg:.2f}, min={actual_min}, max={actual_max}")
        
        return distribution
    
    def calculate_hybrid(self,
                        contributions: Dict[str, NodeContribution]) -> RewardDistribution:
        """
        Calculate rewards using hybrid strategy.
        
        Combines proportional, quality-based, and minimum guarantee.
        
        Args:
            contributions: Dictionary of node contributions
            
        Returns:
            RewardDistribution object
        """
        logger.info(f"[RewardCalc] Calculating hybrid rewards for {len(contributions)} nodes")
        
        if not contributions:
            raise ValueError("No contributions provided")
        
        node_count = len(contributions)
        total_contribution = sum(c.final_score for c in contributions.values())
        
        if total_contribution == 0:
            raise ValueError("Total contribution is zero")
        
        # Allocate pool: 70% proportional, 20% quality bonus, 10% reliability bonus
        proportional_pool = int(self.total_pool * 0.70)
        quality_bonus_pool = int(self.total_pool * 0.20)
        reliability_bonus_pool = self.total_pool - proportional_pool - quality_bonus_pool
        
        logger.debug(f"[RewardCalc] Hybrid pools: prop={proportional_pool}, "
                    f"quality={quality_bonus_pool}, reliability={reliability_bonus_pool}")
        
        # Calculate quality and reliability totals
        total_quality = sum(c.quality_score for c in contributions.values())
        total_reliability = sum(c.reliability_score for c in contributions.values())
        
        node_rewards = {}
        total_distributed = 0
        
        for node_id, contrib in contributions.items():
            # Proportional reward
            prop_reward = int((proportional_pool * contrib.final_score) / total_contribution)
            
            # Quality bonus
            if total_quality > 0:
                quality_bonus = int((quality_bonus_pool * contrib.quality_score) / total_quality)
            else:
                quality_bonus = 0
            
            # Reliability bonus
            if total_reliability > 0:
                reliability_bonus = int((reliability_bonus_pool * contrib.reliability_score) / total_reliability)
            else:
                reliability_bonus = 0
            
            total_bonus = quality_bonus + reliability_bonus
            total_reward = prop_reward + total_bonus
            
            node_rewards[node_id] = NodeReward(
                node_id=node_id,
                node_address=contrib.node_address,
                contribution_score=contrib.final_score,
                contribution_percentage=(contrib.final_score / total_contribution) * 100,
                base_reward=prop_reward,
                bonus_reward=total_bonus,
                total_reward=total_reward,
                metadata={
                    'quality_bonus': quality_bonus,
                    'reliability_bonus': reliability_bonus
                }
            )
            
            total_distributed += total_reward
            
            logger.debug(f"[RewardCalc] Node {node_id}: "
                        f"prop={prop_reward}, quality_bonus={quality_bonus}, "
                        f"reliability_bonus={reliability_bonus}, total={total_reward}")
        
        # Calculate statistics
        reward_amounts = [r.total_reward for r in node_rewards.values()]
        min_reward = min(reward_amounts)
        max_reward = max(reward_amounts)
        avg_reward = statistics.mean(reward_amounts)
        
        distribution = RewardDistribution(
            session_id=self.session_id,
            strategy=RewardStrategy.HYBRID,
            total_pool=self.total_pool,
            total_distributed=total_distributed,
            node_rewards=node_rewards,
            min_reward=min_reward,
            max_reward=max_reward,
            avg_reward=avg_reward
        )
        
        logger.info(f"[RewardCalc] Hybrid distribution complete: "
                   f"{total_distributed} wei distributed, "
                   f"avg={avg_reward:.2f}, min={min_reward}, max={max_reward}")
        
        return distribution
    
    def calculate(self,
                 contributions: Dict[str, NodeContribution],
                 strategy: RewardStrategy = RewardStrategy.PROPORTIONAL) -> RewardDistribution:
        """
        Calculate rewards using specified strategy.
        
        Args:
            contributions: Dictionary of node contributions
            strategy: Distribution strategy to use
            
        Returns:
            RewardDistribution object
        """
        logger.info(f"[RewardCalc] Calculating rewards with strategy: {strategy.name}")
        
        if strategy == RewardStrategy.PROPORTIONAL:
            distribution = self.calculate_proportional(contributions)
        elif strategy == RewardStrategy.TIERED:
            distribution = self.calculate_tiered(contributions)
        elif strategy == RewardStrategy.PERFORMANCE_BASED:
            distribution = self.calculate_with_minimum(contributions, min_percentage=0.5)
        elif strategy == RewardStrategy.HYBRID:
            distribution = self.calculate_hybrid(contributions)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        # Validate distribution
        if not distribution.validate():
            logger.error("[RewardCalc] Distribution validation failed!")
            raise ValueError("Invalid reward distribution")
        
        logger.info(f"[RewardCalc] Distribution validated successfully")
        return distribution
    
    def format_for_blockchain(self, distribution: RewardDistribution) -> Tuple[List[str], List[int]]:
        """
        Format distribution for blockchain submission.
        
        Args:
            distribution: Reward distribution to format
            
        Returns:
            Tuple of (node_addresses, reward_amounts)
        """
        logger.info(f"[RewardCalc] Formatting distribution for blockchain")
        
        addresses = []
        amounts = []
        
        for node_id, reward in distribution.node_rewards.items():
            addresses.append(reward.node_address)
            amounts.append(reward.total_reward)
        
        logger.info(f"[RewardCalc] Formatted {len(addresses)} rewards for submission")
        logger.debug(f"[RewardCalc] Total amount: {sum(amounts)} wei")
        
        return addresses, amounts
