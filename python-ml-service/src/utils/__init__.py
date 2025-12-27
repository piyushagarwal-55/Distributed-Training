"""
Utility functions and helpers for HyperGPU.
"""

from .logger import setup_logger, get_logger

# Make torch-dependent imports optional
try:
    from .serialization import serialize_tensors, deserialize_tensors
    from .validation import validate_config, validate_gradient
    __all__ = [
        "setup_logger",
        "get_logger",
        "serialize_tensors",
        "deserialize_tensors",
        "validate_config",
        "validate_gradient",
    ]
except ImportError:
    # Torch not available, only export logger
    __all__ = [
        "setup_logger",
        "get_logger",
    ]
