"""
Validation utilities for configuration and data.
"""

from typing import Any, Dict, List
import torch
import numpy as np
from ..models.config import SystemConfig, TrainingConfig
from ..models.metrics import GradientUpdate


def validate_config(config: SystemConfig) -> tuple[bool, List[str]]:
    """
    Validate system configuration.
    
    Args:
        config: System configuration to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Validate training config
    if config.training.learning_rate <= 0 or config.training.learning_rate > 1:
        errors.append("Learning rate must be between 0 and 1")
    
    if config.training.batch_size < 1:
        errors.append("Batch size must be at least 1")
    
    if config.training.epochs < 1:
        errors.append("Epochs must be at least 1")
    
    if config.training.num_nodes < 1:
        errors.append("Number of nodes must be at least 1")
    
    # Validate device
    if config.training.device not in ["cpu", "cuda", "mps"]:
        errors.append(f"Invalid device: {config.training.device}")
    
    # Check CUDA availability if specified
    if config.training.device == "cuda" and not torch.cuda.is_available():
        errors.append("CUDA device specified but CUDA is not available")
    
    # Validate network config
    if config.network.enable_simulation:
        if config.network.base_latency_ms < 0:
            errors.append("Base latency cannot be negative")
        
        if config.network.packet_loss_rate < 0 or config.network.packet_loss_rate > 1:
            errors.append("Packet loss rate must be between 0 and 1")
        
        if config.network.bandwidth_mbps is not None and config.network.bandwidth_mbps < 0:
            errors.append("Bandwidth cannot be negative")
    
    # Validate blockchain config
    if config.blockchain.enabled:
        if config.blockchain.chain_id <= 0:
            errors.append("Chain ID must be positive")
        
        if config.blockchain.gas_limit <= 0:
            errors.append("Gas limit must be positive")
        
        if config.blockchain.private_key and len(config.blockchain.private_key) < 10:
            errors.append("Private key appears invalid (too short)")
    
    return len(errors) == 0, errors


def validate_gradient(gradient_update: GradientUpdate) -> tuple[bool, List[str]]:
    """
    Validate gradient update data.
    
    Args:
        gradient_update: Gradient update to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check basic fields
    if not gradient_update.node_id:
        errors.append("Node ID is required")
    
    if not gradient_update.gradient_data:
        errors.append("Gradient data is empty")
    
    if not gradient_update.gradient_shapes:
        errors.append("Gradient shapes are missing")
    
    # Check data consistency
    if len(gradient_update.gradient_data) != len(gradient_update.gradient_shapes):
        errors.append("Number of gradient tensors does not match number of shapes")
    
    # Check for NaN or Inf values
    try:
        for i, tensor_data in enumerate(gradient_update.gradient_data):
            for j, row in enumerate(tensor_data):
                for k, val in enumerate(row):
                    if not np.isfinite(val):
                        errors.append(
                            f"Invalid value (NaN/Inf) in gradient tensor {i} at position [{j},{k}]"
                        )
                        break
                if errors:
                    break
            if errors:
                break
    except Exception as e:
        errors.append(f"Error validating gradient data: {str(e)}")
    
    # Check gradient norm
    if gradient_update.gradient_norm < 0:
        errors.append("Gradient norm cannot be negative")
    
    # Check gradient norm is finite
    if not np.isfinite(gradient_update.gradient_norm):
        errors.append("Gradient norm is NaN or Inf")
    
    # Warn if gradient norm is suspiciously large
    if gradient_update.gradient_norm > 1000:
        errors.append(f"Warning: Gradient norm is very large ({gradient_update.gradient_norm:.2f})")
    
    # Check compute time
    if gradient_update.compute_time_seconds <= 0:
        errors.append("Compute time must be positive")
    
    # Check loss
    if not np.isfinite(gradient_update.local_loss):
        errors.append("Loss is NaN or Inf")
    
    return len(errors) == 0, errors


def validate_model_parameters(parameters: Dict[str, torch.Tensor]) -> tuple[bool, List[str]]:
    """
    Validate model parameters.
    
    Args:
        parameters: Dictionary of parameter tensors
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if not parameters:
        errors.append("Parameters dictionary is empty")
        return False, errors
    
    for name, param in parameters.items():
        # Check for NaN or Inf
        if torch.isnan(param).any():
            errors.append(f"Parameter '{name}' contains NaN values")
        
        if torch.isinf(param).any():
            errors.append(f"Parameter '{name}' contains Inf values")
        
        # Check if parameter is too large
        if param.abs().max() > 1e6:
            errors.append(f"Parameter '{name}' has very large values (max: {param.abs().max():.2e})")
    
    return len(errors) == 0, errors


def sanitize_config_for_logging(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove sensitive information from config before logging.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Sanitized configuration
    """
    sensitive_keys = ["private_key", "password", "secret", "api_key", "token"]
    
    def _sanitize_recursive(obj):
        if isinstance(obj, dict):
            return {
                k: "***REDACTED***" if any(s in k.lower() for s in sensitive_keys) else _sanitize_recursive(v)
                for k, v in obj.items()
            }
        elif isinstance(obj, list):
            return [_sanitize_recursive(item) for item in obj]
        else:
            return obj
    
    return _sanitize_recursive(config)


def check_system_requirements() -> tuple[bool, List[str]]:
    """
    Check if system meets requirements for training.
    
    Returns:
        Tuple of (is_ready, list_of_warnings)
    """
    warnings = []
    
    # Check Python version
    import sys
    if sys.version_info < (3, 9):
        warnings.append(f"Python 3.9+ recommended, found {sys.version_info.major}.{sys.version_info.minor}")
    
    # Check PyTorch
    try:
        import torch
        if not torch.cuda.is_available():
            warnings.append("CUDA not available, will use CPU (slower)")
    except ImportError:
        warnings.append("PyTorch not installed")
        return False, warnings
    
    # Check available memory
    try:
        import psutil
        available_memory_gb = psutil.virtual_memory().available / (1024 ** 3)
        if available_memory_gb < 4:
            warnings.append(f"Low available memory: {available_memory_gb:.1f} GB (recommend 8+ GB)")
    except ImportError:
        warnings.append("Cannot check memory (psutil not installed)")
    
    # Check disk space
    try:
        import shutil
        _, _, free = shutil.disk_usage("/")
        free_gb = free / (1024 ** 3)
        if free_gb < 5:
            warnings.append(f"Low disk space: {free_gb:.1f} GB (recommend 10+ GB)")
    except Exception:
        pass
    
    return True, warnings
