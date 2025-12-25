"""
Serialization utilities for tensors and model parameters.
"""

import numpy as np
import torch
from typing import List, Tuple, Dict, Any
import msgpack
import json


def serialize_tensors(tensors: List[torch.Tensor], use_msgpack: bool = False) -> Dict[str, Any]:
    """
    Serialize PyTorch tensors for network transmission.
    
    Args:
        tensors: List of PyTorch tensors
        use_msgpack: Whether to use MessagePack for binary serialization
        
    Returns:
        Dictionary with serialized data and metadata
    """
    serialized_data = []
    shapes = []
    dtypes = []
    
    for tensor in tensors:
        # Convert to numpy
        np_array = tensor.detach().cpu().numpy()
        shapes.append(list(np_array.shape))
        dtypes.append(str(np_array.dtype))
        
        # Flatten and convert to list
        flat_data = np_array.flatten().tolist()
        serialized_data.append(flat_data)
    
    result = {
        "data": serialized_data,
        "shapes": shapes,
        "dtypes": dtypes,
        "num_tensors": len(tensors),
    }
    
    if use_msgpack:
        # Convert to MessagePack binary format
        return {"binary": msgpack.packb(result), "format": "msgpack"}
    else:
        # Return as JSON-serializable dict
        result["format"] = "json"
        return result


def deserialize_tensors(
    serialized: Dict[str, Any],
    device: str = "cpu"
) -> List[torch.Tensor]:
    """
    Deserialize tensors from network transmission format.
    
    Args:
        serialized: Serialized tensor data
        device: Device to place tensors on (cpu, cuda)
        
    Returns:
        List of PyTorch tensors
    """
    # Handle MessagePack format
    if serialized.get("format") == "msgpack":
        data_dict = msgpack.unpackb(serialized["binary"])
    else:
        data_dict = serialized
    
    tensors = []
    data_list = data_dict["data"]
    shapes = data_dict["shapes"]
    dtypes = data_dict.get("dtypes", ["float32"] * len(shapes))
    
    for data, shape, dtype_str in zip(data_list, shapes, dtypes):
        # Convert list to numpy array
        np_array = np.array(data, dtype=dtype_str)
        
        # Reshape
        np_array = np_array.reshape(shape)
        
        # Convert to PyTorch tensor
        tensor = torch.from_numpy(np_array).to(device)
        tensors.append(tensor)
    
    return tensors


def serialize_model_state(
    model: torch.nn.Module,
    include_optimizer: bool = False,
    optimizer: Any = None
) -> Dict[str, Any]:
    """
    Serialize model state dict for checkpointing.
    
    Args:
        model: PyTorch model
        include_optimizer: Whether to include optimizer state
        optimizer: Optimizer instance (if include_optimizer=True)
        
    Returns:
        Serialized state dictionary
    """
    state = {
        "model_state_dict": model.state_dict(),
        "model_architecture": str(type(model).__name__),
    }
    
    if include_optimizer and optimizer is not None:
        state["optimizer_state_dict"] = optimizer.state_dict()
        state["optimizer_type"] = str(type(optimizer).__name__)
    
    return state


def deserialize_model_state(
    model: torch.nn.Module,
    state: Dict[str, Any],
    optimizer: Any = None,
    strict: bool = True
):
    """
    Load model state from serialized format.
    
    Args:
        model: PyTorch model to load into
        state: Serialized state dictionary
        optimizer: Optimizer instance (if loading optimizer state)
        strict: Whether to strictly enforce state dict keys match
    """
    model.load_state_dict(state["model_state_dict"], strict=strict)
    
    if optimizer is not None and "optimizer_state_dict" in state:
        optimizer.load_state_dict(state["optimizer_state_dict"])


def tensor_to_json_compatible(tensor: torch.Tensor) -> List[List[float]]:
    """
    Convert tensor to JSON-compatible nested list.
    
    Args:
        tensor: PyTorch tensor
        
    Returns:
        Nested list representation
    """
    np_array = tensor.detach().cpu().numpy()
    return np_array.tolist()


def json_compatible_to_tensor(
    data: List[List[float]],
    device: str = "cpu"
) -> torch.Tensor:
    """
    Convert JSON-compatible nested list to tensor.
    
    Args:
        data: Nested list representation
        device: Device to place tensor on
        
    Returns:
        PyTorch tensor
    """
    np_array = np.array(data)
    return torch.from_numpy(np_array).to(device)


def calculate_tensor_size_mb(tensors: List[torch.Tensor]) -> float:
    """
    Calculate total size of tensors in megabytes.
    
    Args:
        tensors: List of PyTorch tensors
        
    Returns:
        Size in MB
    """
    total_bytes = sum(
        tensor.element_size() * tensor.nelement()
        for tensor in tensors
    )
    return total_bytes / (1024 * 1024)


def compress_gradients(
    gradients: List[torch.Tensor],
    method: str = "topk",
    compression_ratio: float = 0.1
) -> Tuple[List[torch.Tensor], Dict[str, Any]]:
    """
    Compress gradients for efficient transmission.
    
    Args:
        gradients: List of gradient tensors
        method: Compression method (topk, quantize)
        compression_ratio: How much to compress (0-1)
        
    Returns:
        Tuple of (compressed_gradients, metadata)
    """
    if method == "topk":
        # Keep only top-k elements by magnitude
        compressed = []
        metadata = {"method": "topk", "ratio": compression_ratio, "indices": []}
        
        for grad in gradients:
            flat_grad = grad.flatten()
            k = max(1, int(len(flat_grad) * compression_ratio))
            
            # Get top-k indices
            _, indices = torch.topk(torch.abs(flat_grad), k)
            values = flat_grad[indices]
            
            # Create sparse representation
            sparse_grad = torch.zeros_like(flat_grad)
            sparse_grad[indices] = values
            
            compressed.append(sparse_grad.reshape(grad.shape))
            metadata["indices"].append(indices.tolist())
        
        return compressed, metadata
    
    elif method == "quantize":
        # Quantize to fewer bits
        compressed = []
        metadata = {"method": "quantize", "bits": 8}
        
        for grad in gradients:
            # Simple 8-bit quantization
            grad_min, grad_max = grad.min(), grad.max()
            scale = (grad_max - grad_min) / 255.0
            quantized = ((grad - grad_min) / scale).to(torch.uint8)
            compressed.append(quantized)
        
        return compressed, metadata
    
    else:
        return gradients, {"method": "none"}
