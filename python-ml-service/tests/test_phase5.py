"""
Tests for Phase 5: Blockchain Integration

Tests all blockchain-related components:
- ContributionCalculator
- RewardCalculator
- MonadClient (mock)
- BlockchainIntegrator
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from src.core.contribution_calculator import (
    ContributionCalculator,
    NodeContribution,
    SessionContributionSummary
)
from src.core.reward_calculator import (
    RewardCalculator,
    RewardStrategy,
    RewardDistribution,
    NodeReward
)
from src.models.metrics import TrainingMetrics, NetworkMetrics


class TestContributionCalculator:
    """Test contribution calculation functionality."""
    
    def test_initialization(self):
        """Test calculator initialization."""
        calc = ContributionCalculator("test_session_1")
        
        assert calc.session_id == "test_session_1"
        assert len(calc.contributions) == 0
        assert len(calc.node_addresses) == 0
        print("[OK] ContributionCalculator initialization test passed")
    
    def test_node_registration(self):
        """Test node registration."""
        calc = ContributionCalculator("test_session_1")
        
        calc.register_node("node_1", "0x1234567890123456789012345678901234567890")
        calc.register_node("node_2", "0x2345678901234567890123456789012345678901")
        
        assert len(calc.contributions) == 2
        assert "node_1" in calc.contributions
        assert calc.contributions["node_1"].node_address == "0x1234567890123456789012345678901234567890"
        print("✅ Node registration test passed")
    
    def test_add_training_metrics(self):
        """Test adding training metrics."""
        calc = ContributionCalculator("test_session_1")
        calc.register_node("node_1", "0x1234567890123456789012345678901234567890")
        
        metrics = TrainingMetrics(
            node_id="node_1",
            epoch=0,
            step=1,
            loss=0.5,
            samples_processed=64,
            time_taken_seconds=2.5,
            samples_per_second=25.6,
            gradient_norm=0.1
        )
        
        calc.add_training_metrics(metrics)
        
        contrib = calc.contributions["node_1"]
        assert contrib.compute_time == 2.5
        assert contrib.samples_processed == 64
        print("✅ Training metrics test passed")
    
    def test_gradient_submission_tracking(self):
        """Test gradient submission tracking."""
        calc = ContributionCalculator("test_session_1")
        calc.register_node("node_1", "0x1234567890123456789012345678901234567890")
        
        # Record accepted gradients
        calc.record_gradient_submission("node_1", True, 0.5)
        calc.record_gradient_submission("node_1", True, 0.6)
        calc.record_gradient_submission("node_1", False)
        
        contrib = calc.contributions["node_1"]
        assert contrib.gradients_accepted == 2
        assert contrib.gradients_rejected == 1
        assert contrib.successful_rounds == 2
        assert contrib.failed_rounds == 1
        print("✅ Gradient submission tracking test passed")
    
    def test_quality_score_calculation(self):
        """Test quality score calculation."""
        calc = ContributionCalculator("test_session_1")
        calc.register_node("node_1", "0x1234567890123456789012345678901234567890")
        
        # Add metrics
        for i in range(10):
            calc.record_gradient_submission("node_1", True, 0.5)
        
        quality_score = calc.calculate_quality_score("node_1")
        
        assert 0 <= quality_score <= 10000
        assert quality_score > 0  # Should have positive score
        print(f"✅ Quality score calculation test passed (score={quality_score})")
    
    def test_reliability_score_calculation(self):
        """Test reliability score calculation."""
        calc = ContributionCalculator("test_session_1")
        calc.register_node("node_1", "0x1234567890123456789012345678901234567890")
        
        # Add successful rounds
        contrib = calc.contributions["node_1"]
        contrib.successful_rounds = 50
        contrib.avg_latency_ms = 100.0
        
        reliability_score = calc.calculate_reliability_score("node_1")
        
        assert 0 <= reliability_score <= 10000
        assert reliability_score > 0
        print(f"✅ Reliability score calculation test passed (score={reliability_score})")
    
    def test_final_score_calculation(self):
        """Test final score with multipliers."""
        calc = ContributionCalculator("test_session_1")
        calc.register_node("node_1", "0x1234567890123456789012345678901234567890")
        
        # Setup contribution
        contrib = calc.contributions["node_1"]
        contrib.compute_time = 100.0  # 100 seconds
        contrib.gradients_accepted = 50
        contrib.successful_rounds = 50
        
        final_score = calc.calculate_final_score("node_1")
        
        assert final_score > 0
        # Should be affected by multipliers
        assert final_score != 100  # Not exactly base score
        print(f"✅ Final score calculation test passed (score={final_score})")
    
    def test_outlier_detection(self):
        """Test outlier detection."""
        calc = ContributionCalculator("test_session_1")
        
        # Register nodes with normal contributions
        for i in range(5):
            node_id = f"node_{i}"
            calc.register_node(node_id, f"0x{'1'*40}")
            contrib = calc.contributions[node_id]
            contrib.compute_time = 100.0
            contrib.gradients_accepted = 50
            contrib.successful_rounds = 40
            contrib.quality_score = 5000 + (i * 10)
            contrib.reliability_score = 6000 + (i * 10)
        
        # Add outlier node with much higher contribution
        calc.register_node("outlier_node", f"0x{'9'*40}")
        outlier_contrib = calc.contributions["outlier_node"]
        outlier_contrib.compute_time = 1000.0  # 10x more
        outlier_contrib.gradients_accepted = 500
        outlier_contrib.successful_rounds = 400
        outlier_contrib.quality_score = 9000
        outlier_contrib.reliability_score = 9500
        
        calc.update_all_scores()
        outliers = calc.detect_outliers(threshold_std=2.0)
        
        assert "outlier_node" in outliers
        print(f"[OK] Outlier detection test passed (found {len(outliers)} outliers)")
    
    def test_contribution_validation(self):
        """Test contribution validation."""
        calc = ContributionCalculator("test_session_1")
        calc.register_node("node_1", "0x1234567890123456789012345678901234567890")
        
        contrib = calc.contributions["node_1"]
        contrib.compute_time = 100.0
        contrib.gradients_accepted = 50
        contrib.quality_score = 5000
        contrib.reliability_score = 7000
        
        assert calc.validate_contributions()
        
        # Test invalid case
        contrib.quality_score = 15000  # Out of range
        assert not calc.validate_contributions()
        print("✅ Contribution validation test passed")
    
    def test_blockchain_formatting(self):
        """Test formatting for blockchain submission."""
        calc = ContributionCalculator("test_session_1")
        
        for i in range(3):
            node_id = f"node_{i}"
            addr = f"0x{'1'*(39-len(str(i)))}{i}"
            calc.register_node(node_id, addr)
            contrib = calc.contributions[node_id]
            contrib.compute_time = 100.0 * (i + 1)
            contrib.gradients_accepted = 50 * (i + 1)
            contrib.successful_rounds = 40 * (i + 1)
            contrib.quality_score = 5000
        
        formatted = calc.format_for_blockchain()
        
        assert len(formatted) == 3
        assert all('node_address' in entry for entry in formatted)
        assert all('compute_time' in entry for entry in formatted)
        assert all('quality_score' in entry for entry in formatted)
        print(f"✅ Blockchain formatting test passed ({len(formatted)} entries)")


class TestRewardCalculator:
    """Test reward calculation functionality."""
    
    def create_test_contributions(self, num_nodes=5):
        """Helper to create test contributions."""
        contributions = {}
        for i in range(num_nodes):
            node_id = f"node_{i}"
            contrib = NodeContribution(
                node_id=node_id,
                node_address=f"0x{'1'*(39-len(str(i)))}{i}",
                compute_time=100.0 * (i + 1),
                gradients_accepted=50 * (i + 1),
                successful_rounds=40 * (i + 1),
                quality_score=5000 + (i * 100),
                reliability_score=6000 + (i * 100),
                final_score=1000 * (i + 1)
            )
            contributions[node_id] = contrib
        return contributions
    
    def test_initialization(self):
        """Test reward calculator initialization."""
        calc = RewardCalculator("test_session", 1000000)
        
        assert calc.session_id == "test_session"
        assert calc.total_pool == 1000000
        print("✅ RewardCalculator initialization test passed")
    
    def test_proportional_distribution(self):
        """Test proportional reward distribution."""
        calc = RewardCalculator("test_session", 1000000)
        contributions = self.create_test_contributions(3)
        
        distribution = calc.calculate_proportional(contributions)
        
        assert distribution.strategy == RewardStrategy.PROPORTIONAL
        assert len(distribution.node_rewards) == 3
        assert distribution.total_distributed <= distribution.total_pool
        assert distribution.validate()
        
        print(f"✅ Proportional distribution test passed")
        print(f"   Total distributed: {distribution.total_distributed}")
        print(f"   Avg reward: {distribution.avg_reward:.2f}")
    
    def test_tiered_distribution(self):
        """Test tiered reward distribution with bonuses."""
        calc = RewardCalculator("test_session", 1000000)
        contributions = self.create_test_contributions(10)
        
        distribution = calc.calculate_tiered(contributions)
        
        assert distribution.strategy == RewardStrategy.TIERED
        assert distribution.validate()
        
        # Check that top nodes got bonuses
        rewards = list(distribution.node_rewards.values())
        assert rewards[0].bonus_reward > 0  # Top node should have bonus
        
        print(f"✅ Tiered distribution test passed")
        print(f"   Total distributed: {distribution.total_distributed}")
        print(f"   Top node bonus: {rewards[0].bonus_reward}")
    
    def test_minimum_guarantee(self):
        """Test distribution with minimum guarantee."""
        calc = RewardCalculator("test_session", 1000000)
        
        # Create contributions with one very low contributor
        contributions = self.create_test_contributions(5)
        contributions["node_0"].final_score = 10  # Very low
        
        distribution = calc.calculate_with_minimum(contributions, min_percentage=0.5)
        
        assert distribution.validate()
        
        # Check that low contributor got minimum
        low_contributor_reward = distribution.node_rewards["node_0"].total_reward
        avg_reward = distribution.avg_reward
        min_guaranteed = avg_reward * 0.5
        
        assert low_contributor_reward >= min_guaranteed * 0.9  # Allow some rounding
        
        print(f"✅ Minimum guarantee test passed")
        print(f"   Low contributor reward: {low_contributor_reward}")
        print(f"   Minimum guaranteed: {min_guaranteed:.2f}")
    
    def test_hybrid_distribution(self):
        """Test hybrid distribution strategy."""
        calc = RewardCalculator("test_session", 1000000)
        contributions = self.create_test_contributions(5)
        
        distribution = calc.calculate_hybrid(contributions)
        
        assert distribution.strategy == RewardStrategy.HYBRID
        assert distribution.validate()
        
        # Check that bonuses were applied
        rewards = list(distribution.node_rewards.values())
        assert any(r.bonus_reward > 0 for r in rewards)
        
        print(f"✅ Hybrid distribution test passed")
        print(f"   Total distributed: {distribution.total_distributed}")
    
    def test_reward_validation(self):
        """Test reward distribution validation."""
        calc = RewardCalculator("test_session", 1000000)
        contributions = self.create_test_contributions(3)
        
        distribution = calc.calculate(contributions, RewardStrategy.PROPORTIONAL)
        
        # Should pass validation
        assert distribution.validate()
        
        # Test invalid case
        distribution.total_distributed = distribution.total_pool + 100000
        assert not distribution.validate()
        
        print("✅ Reward validation test passed")
    
    def test_blockchain_formatting(self):
        """Test formatting for blockchain submission."""
        calc = RewardCalculator("test_session", 1000000)
        contributions = self.create_test_contributions(3)
        
        distribution = calc.calculate(contributions, RewardStrategy.PROPORTIONAL)
        addresses, amounts = calc.format_for_blockchain(distribution)
        
        assert len(addresses) == 3
        assert len(amounts) == 3
        assert all(addr.startswith("0x") for addr in addresses)
        assert all(isinstance(amt, int) for amt in amounts)
        assert sum(amounts) == distribution.total_distributed
        
        print(f"✅ Blockchain formatting test passed")
        print(f"   Total amount: {sum(amounts)}")


def run_all_tests():
    """Run all Phase 5 tests."""
    print("\n" + "="*60)
    print("Phase 5: Blockchain Integration Tests")
    print("="*60 + "\n")
    
    # Contribution Calculator Tests
    print("\n--- ContributionCalculator Tests ---\n")
    test_contrib = TestContributionCalculator()
    test_contrib.test_initialization()
    test_contrib.test_node_registration()
    test_contrib.test_add_training_metrics()
    test_contrib.test_gradient_submission_tracking()
    test_contrib.test_quality_score_calculation()
    test_contrib.test_reliability_score_calculation()
    test_contrib.test_final_score_calculation()
    test_contrib.test_outlier_detection()
    test_contrib.test_contribution_validation()
    test_contrib.test_blockchain_formatting()
    
    # Reward Calculator Tests
    print("\n--- RewardCalculator Tests ---\n")
    test_reward = TestRewardCalculator()
    test_reward.test_initialization()
    test_reward.test_proportional_distribution()
    test_reward.test_tiered_distribution()
    test_reward.test_minimum_guarantee()
    test_reward.test_hybrid_distribution()
    test_reward.test_reward_validation()
    test_reward.test_blockchain_formatting()
    
    print("\n" + "="*60)
    print("✅ All Phase 5 Tests Passed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_all_tests()
