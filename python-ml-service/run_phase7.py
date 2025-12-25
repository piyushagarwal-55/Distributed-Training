"""
Master Orchestration Script for HyperGPU System

Starts all components and runs comprehensive tests.
"""

import sys
import asyncio
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.integration.orchestrator import main_orchestrator
from src.utils.logger import setup_logger, get_logger

logger = get_logger(__name__)


async def run_full_system():
    """Run the full HyperGPU system."""
    logger.info("Starting HyperGPU Full System")
    
    config_path = "configs/default.json"
    await main_orchestrator(
        config_path=config_path,
        start_frontend=True,
        num_nodes=5
    )


async def run_tests():
    """Run all Phase 7 tests."""
    logger.info("\n" + "="*80)
    logger.info("RUNNING PHASE 7 COMPREHENSIVE TEST SUITE")
    logger.info("="*80 + "\n")
    
    import pytest
    
    test_files = [
        "tests/test_e2e_training.py",
        "tests/test_resilience.py",
        "tests/test_performance.py"
    ]
    
    for test_file in test_files:
        logger.info(f"\nRunning {test_file}...")
        logger.info("-" * 80)
        
        result = pytest.main([test_file, "-v", "-s", "--tb=short"])
        
        if result != 0:
            logger.error(f"Tests in {test_file} failed!")
            return False
    
    logger.info("\n" + "="*80)
    logger.info("ALL PHASE 7 TESTS PASSED ✓")
    logger.info("="*80)
    return True


async def run_system_with_tests():
    """Run system and then execute tests."""
    logger.info("Running HyperGPU System with Tests")
    
    # First run tests
    logger.info("\nStep 1: Running Test Suite...")
    test_success = await run_tests()
    
    if not test_success:
        logger.error("Tests failed! Fix issues before starting system.")
        return
    
    logger.info("\n" + "="*80)
    logger.info("Tests passed! Starting full system...")
    logger.info("="*80 + "\n")
    
    # Then start system
    await run_full_system()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="HyperGPU Phase 7 Integration & Testing"
    )
    
    parser.add_argument(
        "mode",
        choices=["system", "tests", "all"],
        help="Mode: 'system' (start system), 'tests' (run tests), 'all' (tests then system)"
    )
    
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logger(level=args.log_level)
    
    # Run based on mode
    try:
        if args.mode == "system":
            asyncio.run(run_full_system())
        elif args.mode == "tests":
            asyncio.run(run_tests())
        elif args.mode == "all":
            asyncio.run(run_system_with_tests())
    except KeyboardInterrupt:
        logger.info("\nShutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
