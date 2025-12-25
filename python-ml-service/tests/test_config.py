"""
Test configuration system.
"""

import pytest
import json
import tempfile
from pathlib import Path
from src.models.config import (
    TrainingConfig,
    NetworkConfig,
    BlockchainConfig,
    SystemConfig,
)
from src.utils.validation import validate_config, check_system_requirements


class TestConfigValidation:
    """Test configuration validation."""
    
    def test_valid_config(self, mocker):
        """Test validation of valid configuration."""
        # Mock CUDA check and system requirements
        mocker.patch('torch.cuda.is_available', return_value=False)
        config = SystemConfig()
        # Use CPU device for test since we mock CUDA as unavailable
        config.training.device = "cpu"
        is_valid, errors = validate_config(config)
        assert is_valid
        assert len(errors) == 0
    
    def test_invalid_learning_rate(self):
        """Test detection of invalid learning rate."""
        config = SystemConfig()
        config.training.learning_rate = 1.5
        
        is_valid, errors = validate_config(config)
        assert not is_valid
        assert any("learning rate" in err.lower() for err in errors)
    
    def test_invalid_batch_size(self):
        """Test detection of invalid batch size."""
        config = SystemConfig()
        config.training.batch_size = 0
        
        is_valid, errors = validate_config(config)
        assert not is_valid
        assert any("batch size" in err.lower() for err in errors)
    
    def test_invalid_packet_loss(self):
        """Test detection of invalid packet loss rate."""
        config = SystemConfig()
        config.network.packet_loss_rate = 1.5
        
        is_valid, errors = validate_config(config)
        assert not is_valid
        assert any("packet loss" in err.lower() for err in errors)


class TestConfigSerialization:
    """Test configuration serialization."""
    
    def test_save_and_load_config(self):
        """Test saving and loading configuration from file."""
        # Create config
        original_config = SystemConfig()
        original_config.training.learning_rate = 0.01
        original_config.training.batch_size = 128
        original_config.training.epochs = 20
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
            original_config.to_file(temp_file)
        
        try:
            # Load from file
            loaded_config = SystemConfig.from_file(temp_file)
            
            # Verify
            assert loaded_config.training.learning_rate == 0.01
            assert loaded_config.training.batch_size == 128
            assert loaded_config.training.epochs == 20
        finally:
            # Clean up
            Path(temp_file).unlink()
    
    def test_config_to_dict(self):
        """Test configuration to dictionary conversion."""
        config = TrainingConfig(
            learning_rate=0.01,
            batch_size=32,
            epochs=15,
        )
        
        config_dict = config.model_dump()
        
        assert isinstance(config_dict, dict)
        assert config_dict["learning_rate"] == 0.01
        assert config_dict["batch_size"] == 32
        assert config_dict["epochs"] == 15


class TestSystemRequirements:
    """Test system requirements checking."""
    
    def test_check_requirements(self):
        """Test checking system requirements."""
        is_ready, warnings = check_system_requirements()
        
        # Should always return a boolean and list
        assert isinstance(is_ready, bool)
        assert isinstance(warnings, list)
        
        # Print warnings for informational purposes
        for warning in warnings:
            print(f"Warning: {warning}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
