import numpy as np
import torch
from src.core.model_manager import ModelManager
from src.models.config import ModelArchitecture

# Create model manager
manager = ModelManager(
    ModelArchitecture.SIMPLE_CNN,
    checkpoint_dir="./temp",
    device='cpu'
)
manager.initialize_model(learning_rate=0.01)

# Get initial parameters
initial_params = manager.get_parameters()
print(f"Initial params type: {type(initial_params)}")
first_key = list(initial_params.keys())[0]
print(f"First param type: {type(initial_params[first_key])}")
print(f"First param ID: {id(initial_params[first_key])}")
print(f"First param ({first_key}) first 3 values: {initial_params[first_key].flatten()[:3]}")

# Create mock gradients
gradients = {
    name: np.random.randn(*arr.shape) * 0.01
    for name, arr in initial_params.items()
}

print(f"Gradient for {first_key} first 3: {gradients[first_key].flatten()[:3]}")

# Apply gradients
success = manager.apply_gradients(gradients)
print(f"Apply gradients success: {success}")

# Check parameters changed  
new_params = manager.get_parameters()
print(f"New param ID: {id(new_params[first_key])}")
print(f"New param ({first_key}) first 3 values: {new_params[first_key].flatten()[:3]}")

# Check if same object
print(f"Same object: {id(initial_params[first_key]) == id(new_params[first_key])}")

# Check if changed
print(f"Arrays equal: {np.array_equal(initial_params[first_key], new_params[first_key])}")
print(f"Arrays allclose: {np.allclose(initial_params[first_key], new_params[first_key])}")

# Compute difference
diff = np.abs(initial_params[first_key] - new_params[first_key])
print(f"Max difference: {diff.max()}")
print(f"Mean difference: {diff.mean()}")
