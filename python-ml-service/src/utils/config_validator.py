"""
Configuration validation utilities to ensure safe settings for demos.
"""

from src.models.config import TrainingConfig, ModelArchitecture, DatasetType


def validate_demo_config(config: TrainingConfig, strict: bool = True) -> bool:
    """
    Validate configuration is safe for laptop/demo usage.
    
    Args:
        config: Training configuration to validate
        strict: If True, raise errors. If False, return bool and print warnings.
        
    Returns:
        bool: True if valid, False otherwise (only when strict=False)
        
    Raises:
        ValueError: If config is unsafe and strict=True
    """
    issues = []
    
    # Check model architecture
    if config.model_architecture != ModelArchitecture.SIMPLE_CNN:
        issues.append(
            f"⚠️ Model '{config.model_architecture.value}' may be too heavy for demo. "
            f"Recommended: SimpleCNN (~20K params)"
        )
    
    # Check dataset
    if config.dataset not in [DatasetType.MNIST, DatasetType.CIFAR10]:
        issues.append(
            f"⚠️ Dataset '{config.dataset.value}' may be too large. "
            f"Recommended: MNIST or CIFAR-10"
        )
    
    # Check epochs (warn if too many)
    if config.epochs > 50:
        issues.append(
            f"⚠️ {config.epochs} epochs may take long time. "
            f"Recommended: 10-20 epochs for demo"
        )
    
    # Check batch size (warn if too large or too small)
    if hasattr(config, 'batch_size'):
        if config.batch_size > 256:
            issues.append(
                f"⚠️ Batch size {config.batch_size} may use too much memory. "
                f"Recommended: 32-128"
            )
        elif config.batch_size < 16:
            issues.append(
                f"⚠️ Batch size {config.batch_size} may be too small. "
                f"Recommended: 32-128"
            )
    
    # Handle results
    if issues:
        message = "\n".join(issues)
        if strict:
            raise ValueError(f"\n❌ Configuration validation failed:\n{message}")
        else:
            print(f"\n⚠️ Configuration warnings:\n{message}\n")
            return False
    else:
        print("✅ Configuration validated for demo usage")
        return True


def get_safe_demo_config() -> TrainingConfig:
    """
    Get a guaranteed-safe configuration for demos.
    
    Returns:
        TrainingConfig: Safe configuration using SimpleCNN and MNIST
    """
    return TrainingConfig(
        model_architecture=ModelArchitecture.SIMPLE_CNN,
        dataset=DatasetType.MNIST,
        epochs=10,
        batch_size=64,
        learning_rate=0.01,
        steps_per_epoch=10
    )


def estimate_resources(config: TrainingConfig, num_nodes: int = 1) -> dict:
    """
    Estimate resource requirements for a configuration.
    
    Args:
        config: Training configuration
        num_nodes: Number of simulated nodes
        
    Returns:
        dict: Resource estimates (ram_mb, time_seconds, etc.)
    """
    # Parameter counts for each model
    model_params = {
        ModelArchitecture.SIMPLE_CNN: 20_000,
        ModelArchitecture.RESNET18: 11_000_000,
        ModelArchitecture.RESNET50: 25_000_000,
        ModelArchitecture.VGG16: 138_000_000,
    }
    
    # Base memory per model (MB)
    base_ram = {
        ModelArchitecture.SIMPLE_CNN: 5,
        ModelArchitecture.RESNET18: 200,
        ModelArchitecture.RESNET50: 500,
        ModelArchitecture.VGG16: 1500,
    }
    
    params = model_params.get(config.model_architecture, 20_000)
    ram = base_ram.get(config.model_architecture, 5)
    
    # Estimate total RAM
    coordinator_base = 100  # MB
    model_ram = ram
    nodes_ram = num_nodes * 5  # MB per node
    total_ram = coordinator_base + model_ram + nodes_ram
    
    # Estimate training time (very rough)
    # SimpleCNN: ~0.3s per epoch, others scale with params
    time_per_epoch = (params / 20_000) * 0.3
    total_time = time_per_epoch * config.epochs
    
    return {
        "model_parameters": params,
        "estimated_ram_mb": total_ram,
        "estimated_time_seconds": total_time,
        "time_per_epoch_seconds": time_per_epoch,
        "recommended": params < 1_000_000,
        "warning": "Heavy model, not recommended for demo" if params > 1_000_000 else "Safe for demo"
    }


def print_config_summary(config: TrainingConfig, num_nodes: int = 1):
    """
    Print a summary of configuration with resource estimates.
    
    Args:
        config: Training configuration
        num_nodes: Number of nodes
    """
    estimates = estimate_resources(config, num_nodes)
    
    print("\n" + "="*60)
    print("📋 Configuration Summary")
    print("="*60)
    print(f"Model: {config.model_architecture.value}")
    print(f"Dataset: {config.dataset.value}")
    print(f"Epochs: {config.epochs}")
    if hasattr(config, 'batch_size'):
        print(f"Batch Size: {config.batch_size}")
    print(f"Nodes: {num_nodes}")
    print("\n" + "-"*60)
    print("📊 Resource Estimates")
    print("-"*60)
    print(f"Parameters: {estimates['model_parameters']:,}")
    print(f"RAM Usage: ~{estimates['estimated_ram_mb']} MB")
    print(f"Training Time: ~{estimates['estimated_time_seconds']:.1f} seconds")
    print(f"Time/Epoch: ~{estimates['time_per_epoch_seconds']:.2f} seconds")
    print("-"*60)
    
    if estimates['recommended']:
        print("✅ " + estimates['warning'])
    else:
        print("⚠️ " + estimates['warning'])
    
    print("="*60 + "\n")


if __name__ == "__main__":
    # Test validation
    print("Testing configuration validation...\n")
    
    # Safe config
    print("1. Testing safe configuration:")
    safe_config = get_safe_demo_config()
    validate_demo_config(safe_config)
    print_config_summary(safe_config, num_nodes=10)
    
    # Heavy config (warning)
    print("\n2. Testing heavy configuration (non-strict):")
    heavy_config = TrainingConfig(
        model_architecture=ModelArchitecture.RESNET18,
        dataset=DatasetType.MNIST,
        epochs=10
    )
    is_valid = validate_demo_config(heavy_config, strict=False)
    print(f"Valid: {is_valid}")
    print_config_summary(heavy_config, num_nodes=10)
