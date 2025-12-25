"""
Phase 5 Demo: Blockchain Integration

This script demonstrates the complete Phase 5 implementation including:
- Smart contract deployment (simulated for demo)
- Training session on blockchain
- Contribution tracking
- Reward calculation and distribution

Usage:
    python demo_phase5.py [--config configs/phase5.json]
"""

import sys
import argparse
from pathlib import Path
import json
import time
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.models.config import SystemConfig, BlockchainConfig
from src.core.contribution_calculator import ContributionCalculator, NodeContribution
from src.core.reward_calculator import RewardCalculator, RewardStrategy
from src.models.metrics import TrainingMetrics, NetworkMetrics
from src.utils.logger import get_logger

logger = get_logger(__name__)


def print_banner(text):
    """Print a nice banner."""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")


def simulate_training_session():
    """Simulate a training session with blockchain integration."""
    print_banner("PHASE 5 DEMO: Blockchain Integration")
    
    # Session configuration
    session_id = f"demo_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    num_nodes = 5
    num_epochs = 3
    steps_per_epoch = 10
    
    logger.info(f"[Demo] Starting demo session: {session_id}")
    logger.info(f"[Demo] Configuration: {num_nodes} nodes, {num_epochs} epochs, {steps_per_epoch} steps/epoch")
    
    # Initialize contribution calculator
    print_banner("Step 1: Initialize Contribution Calculator")
    
    calc = ContributionCalculator(session_id)
    logger.info(f"[Demo] Contribution calculator initialized")
    
    # Register nodes with mock addresses
    print("\n📝 Registering nodes...")
    nodes = []
    for i in range(num_nodes):
        node_id = f"node_{i}"
        # Generate mock Ethereum address
        node_address = f"0x{'1'*(38-len(str(i)))}{i:02d}"
        
        calc.register_node(node_id, node_address)
        nodes.append((node_id, node_address))
        logger.info(f"[Demo] Registered: {node_id} -> {node_address}")
    
    print(f"✅ {len(nodes)} nodes registered\n")
    
    # Simulate training
    print_banner("Step 2: Simulate Training and Track Contributions")
    
    for epoch in range(num_epochs):
        logger.info(f"\n[Demo] === Epoch {epoch + 1}/{num_epochs} ===")
        print(f"\n🔄 Epoch {epoch + 1}/{num_epochs}")
        
        for step in range(steps_per_epoch):
            for node_id, _ in nodes:
                # Simulate different performance levels
                node_idx = int(node_id.split("_")[1])
                performance_multiplier = 0.8 + (node_idx * 0.1)  # 0.8 to 1.2
                
                # Create training metrics
                metrics = TrainingMetrics(
                    node_id=node_id,
                    epoch=epoch,
                    step=step,
                    loss=0.5 - (epoch * 0.1) - (step * 0.01),
                    samples_processed=64,
                    time_taken_seconds=2.5 * performance_multiplier,
                    samples_per_second=25.6 / performance_multiplier,
                    gradient_norm=0.1 + (node_idx * 0.02)
                )
                
                calc.add_training_metrics(metrics)
                
                # Record gradient submission (vary acceptance)
                accepted = (node_idx + step) % 10 != 0  # Occasionally reject
                calc.record_gradient_submission(node_id, accepted, metrics.gradient_norm)
            
            if step % 5 == 0:
                print(f"  Step {step}/{steps_per_epoch}...")
        
        logger.info(f"[Demo] Epoch {epoch + 1} complete")
        print(f"✅ Epoch {epoch + 1} complete\n")
    
    # Calculate scores
    print_banner("Step 3: Calculate Contribution Scores")
    
    calc.update_all_scores()
    
    print("\n📊 Contribution Scores:\n")
    for node_id, contrib in calc.contributions.items():
        logger.info(f"[Demo] {node_id}:")
        logger.info(f"  - Compute time: {contrib.compute_time:.2f}s")
        logger.info(f"  - Gradients accepted: {contrib.gradients_accepted}")
        logger.info(f"  - Quality score: {contrib.quality_score}/10000")
        logger.info(f"  - Reliability score: {contrib.reliability_score}/10000")
        logger.info(f"  - Final score: {contrib.final_score}")
        
        print(f"{node_id}:")
        print(f"  ⏱️  Compute time: {contrib.compute_time:.2f}s")
        print(f"  ✓  Gradients: {contrib.gradients_accepted} accepted, {contrib.gradients_rejected} rejected")
        print(f"  ⭐ Quality: {contrib.quality_score}/10000")
        print(f"  🔄 Reliability: {contrib.reliability_score}/10000")
        print(f"  📈 Final Score: {contrib.final_score}\n")
    
    # Get session summary
    summary = calc.get_summary()
    
    print("📋 Session Summary:")
    print(f"  - Participants: {summary.participant_count}")
    print(f"  - Total compute time: {summary.total_compute_time:.2f}s")
    print(f"  - Total gradients: {summary.total_gradients}")
    print(f"  - Avg quality score: {summary.avg_quality_score:.2f}/10000")
    print(f"  - Avg reliability score: {summary.avg_reliability_score:.2f}/10000")
    
    if summary.outlier_nodes:
        print(f"  ⚠️  Outliers detected: {summary.outlier_nodes}")
    
    # Validate contributions
    print("\n🔍 Validating contributions...")
    if calc.validate_contributions():
        print("✅ All contributions validated successfully\n")
        logger.info("[Demo] Contribution validation passed")
    else:
        print("❌ Contribution validation failed!\n")
        logger.error("[Demo] Contribution validation failed")
        return
    
    # Calculate rewards
    print_banner("Step 4: Calculate and Distribute Rewards")
    
    reward_pool_eth = 0.1
    reward_pool_wei = int(reward_pool_eth * 1e18)
    
    print(f"💰 Reward Pool: {reward_pool_eth} ETH ({reward_pool_wei} wei)\n")
    logger.info(f"[Demo] Reward pool: {reward_pool_eth} ETH")
    
    reward_calc = RewardCalculator(session_id, reward_pool_wei)
    contributions = calc.get_all_contributions()
    
    # Test different strategies
    strategies = [
        (RewardStrategy.PROPORTIONAL, "Proportional"),
        (RewardStrategy.TIERED, "Tiered with Bonuses"),
        (RewardStrategy.HYBRID, "Hybrid")
    ]
    
    for strategy, strategy_name in strategies:
        print(f"\n📊 {strategy_name} Distribution:\n")
        logger.info(f"[Demo] Testing {strategy_name} strategy")
        
        distribution = reward_calc.calculate(contributions, strategy)
        
        print(f"  Strategy: {distribution.strategy.name}")
        print(f"  Total distributed: {distribution.total_distributed} wei ({distribution.total_distributed/1e18:.6f} ETH)")
        print(f"  Min reward: {distribution.min_reward} wei ({distribution.min_reward/1e18:.6f} ETH)")
        print(f"  Max reward: {distribution.max_reward} wei ({distribution.max_reward/1e18:.6f} ETH)")
        print(f"  Avg reward: {distribution.avg_reward:.2f} wei ({distribution.avg_reward/1e18:.6f} ETH)")
        
        print(f"\n  Node Rewards:")
        for node_id, reward in sorted(distribution.node_rewards.items()):
            tier_info = f" (Tier {reward.tier})" if reward.tier else ""
            bonus_info = f" + {reward.bonus_reward} bonus" if reward.bonus_reward > 0 else ""
            
            print(f"    {node_id}{tier_info}:")
            print(f"      Base: {reward.base_reward} wei")
            if reward.bonus_reward > 0:
                print(f"      Bonus: {reward.bonus_reward} wei")
            print(f"      Total: {reward.total_reward} wei ({reward.total_reward/1e18:.6f} ETH)")
            print(f"      Contribution: {reward.contribution_percentage:.2f}%")
        
        # Validate
        if distribution.validate():
            print(f"\n  ✅ Distribution validated\n")
            logger.info(f"[Demo] {strategy_name} distribution validated")
        else:
            print(f"\n  ❌ Distribution validation failed!\n")
            logger.error(f"[Demo] {strategy_name} distribution validation failed")
    
    # Format for blockchain
    print_banner("Step 5: Format for Blockchain Submission")
    
    # Use proportional strategy for final submission
    final_distribution = reward_calc.calculate(contributions, RewardStrategy.PROPORTIONAL)
    addresses, amounts = reward_calc.format_for_blockchain(final_distribution)
    
    print("📤 Blockchain Transaction Data:\n")
    print(f"  Function: recordContributionsBatch()")
    print(f"  Parameters:")
    print(f"    - sessionId: {session_id}")
    print(f"    - nodeAddresses: [{', '.join(addresses[:3])}{'...' if len(addresses) > 3 else ''}]")
    print(f"    - amounts: [{', '.join(map(str, amounts[:3]))}{'...' if len(amounts) > 3 else ''}]")
    print(f"  Total gas estimate: ~{len(addresses) * 50000} gas")
    
    logger.info(f"[Demo] Formatted {len(addresses)} contributions for blockchain")
    
    # Print blockchain submission format
    print("\n📋 Contribution Data for Smart Contract:\n")
    formatted_contribs = calc.format_for_blockchain()
    for i, contrib in enumerate(formatted_contribs[:3]):  # Show first 3
        print(f"  [{i}] {{")
        print(f"    node_address: {contrib['node_address']},")
        print(f"    compute_time: {contrib['compute_time']}s,")
        print(f"    gradients_accepted: {contrib['gradients_accepted']},")
        print(f"    successful_rounds: {contrib['successful_rounds']},")
        print(f"    quality_score: {contrib['quality_score']}/10000")
        print(f"  }}")
    
    if len(formatted_contribs) > 3:
        print(f"  ... and {len(formatted_contribs) - 3} more")
    
    # Success summary
    print_banner("Demo Complete!")
    
    print("✅ Successfully demonstrated:")
    print("  1. ✓ Contribution tracking and calculation")
    print("  2. ✓ Multi-dimensional scoring (quality + reliability)")
    print("  3. ✓ Multiple reward distribution strategies")
    print("  4. ✓ Validation and outlier detection")
    print("  5. ✓ Blockchain data formatting")
    
    print(f"\n📊 Final Statistics:")
    print(f"  - Nodes: {len(nodes)}")
    print(f"  - Epochs: {num_epochs}")
    print(f"  - Total steps: {num_epochs * steps_per_epoch}")
    print(f"  - Total compute time: {summary.total_compute_time:.2f}s")
    print(f"  - Reward pool: {reward_pool_eth} ETH")
    print(f"  - Strategy used: {final_distribution.strategy.name}")
    
    logger.info("[Demo] Phase 5 demo completed successfully")
    
    print("\n" + "="*70)
    print("  To deploy to actual blockchain:")
    print("  1. Deploy smart contracts: cd smart-contracts && npm run deploy:local")
    print("  2. Update config with contract addresses")
    print("  3. Set PRIVATE_KEY environment variable")
    print("  4. Run with --blockchain-enabled flag")
    print("="*70 + "\n")


def main():
    """Main demo entry point."""
    parser = argparse.ArgumentParser(description="Phase 5 Blockchain Integration Demo")
    parser.add_argument("--config", default="configs/phase5.json", help="Config file path")
    
    args = parser.parse_args()
    
    try:
        simulate_training_session()
        return 0
    except Exception as e:
        logger.error(f"[Demo] Error: {e}", exc_info=True)
        print(f"\n❌ Demo failed: {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
