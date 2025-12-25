"""
Main entry point for HyperGPU Python ML Service.
"""

import sys
import argparse
from pathlib import Path

from .models.config import SystemConfig
from .utils.logger import setup_logger, get_logger
from .utils.validation import validate_config, check_system_requirements

logger = get_logger(__name__)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="HyperGPU: Network-Aware Distributed AI Training"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default="configs/default.json",
        help="Path to configuration file",
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level",
    )
    
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate configuration, don't start training",
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Setup logging
    setup_logger(log_level=args.log_level, log_file="logs/training.log")
    logger.info("=" * 80)
    logger.info("HyperGPU: Network-Aware Distributed AI Training")
    logger.info("=" * 80)
    
    # Check system requirements
    logger.info("Checking system requirements...")
    is_ready, warnings = check_system_requirements()
    
    if warnings:
        for warning in warnings:
            logger.warning(warning)
    
    if not is_ready:
        logger.error("System does not meet requirements. Cannot proceed.")
        return 1
    
    logger.info("✓ System requirements satisfied")
    
    # Load configuration
    logger.info(f"Loading configuration from: {args.config}")
    try:
        config = SystemConfig.from_file(args.config)
        logger.info("✓ Configuration loaded successfully")
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {args.config}")
        return 1
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return 1
    
    # Validate configuration
    logger.info("Validating configuration...")
    is_valid, errors = validate_config(config)
    
    if not is_valid:
        logger.error("Configuration validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
        return 1
    
    logger.info("✓ Configuration valid")
    
    # If validate-only mode, exit here
    if args.validate_only:
        logger.info("Validation complete. Exiting (--validate-only mode)")
        return 0
    
    # Display configuration summary
    logger.info("")
    logger.info("Configuration Summary:")
    logger.info(f"  Model: {config.training.model_architecture.value}")
    logger.info(f"  Dataset: {config.training.dataset.value}")
    logger.info(f"  Learning Rate: {config.training.learning_rate}")
    logger.info(f"  Batch Size: {config.training.batch_size}")
    logger.info(f"  Epochs: {config.training.epochs}")
    logger.info(f"  Number of Nodes: {config.training.num_nodes}")
    logger.info(f"  Device: {config.training.device}")
    logger.info(f"  Network Simulation: {'Enabled' if config.network.enable_simulation else 'Disabled'}")
    logger.info(f"  Blockchain Integration: {'Enabled' if config.blockchain.enabled else 'Disabled'}")
    logger.info("")
    
    logger.info("Training coordinator initialization will be implemented in Phase 2")
    logger.info("Phase 1 (Project Foundation) completed successfully!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
