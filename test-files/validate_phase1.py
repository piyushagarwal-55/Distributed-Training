#!/usr/bin/env python3
"""
Automated validation script for Phase 1 implementation.
"""

import sys
import subprocess
from pathlib import Path
import json


def print_header(text):
    """Print formatted header."""
    print("\n" + "=" * 80)
    print(f" {text}")
    print("=" * 80)


def print_success(text):
    """Print success message."""
    print(f"✓ {text}")


def print_error(text):
    """Print error message."""
    print(f"✗ {text}")


def print_info(text):
    """Print info message."""
    print(f"ℹ {text}")


def check_python_version():
    """Check Python version."""
    print_header("Checking Python Version")
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 9:
        print_success("Python version is 3.9 or higher")
        return True
    else:
        print_error(f"Python 3.9+ required, found {version.major}.{version.minor}")
        return False


def check_directory_structure():
    """Check if all required directories exist."""
    print_header("Checking Directory Structure")
    
    base_dir = Path(__file__).parent.parent
    required_dirs = [
        "python-ml-service",
        "python-ml-service/src",
        "python-ml-service/src/models",
        "python-ml-service/src/core",
        "python-ml-service/src/utils",
        "python-ml-service/configs",
        "python-ml-service/tests",
        "backend",
        "backend/src",
        "smart-contracts",
        "smart-contracts/contracts",
        "frontend",
        "frontend/src",
        "docs",
        "test-files",
        "shared",
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        if full_path.exists():
            print_success(f"{dir_path}")
        else:
            print_error(f"{dir_path} - NOT FOUND")
            all_exist = False
    
    return all_exist


def check_required_files():
    """Check if all required files exist."""
    print_header("Checking Required Files")
    
    base_dir = Path(__file__).parent.parent
    required_files = [
        "python-ml-service/requirements.txt",
        "python-ml-service/README.md",
        "python-ml-service/.env.example",
        "python-ml-service/src/__init__.py",
        "python-ml-service/src/main.py",
        "python-ml-service/src/models/__init__.py",
        "python-ml-service/src/models/config.py",
        "python-ml-service/src/models/node.py",
        "python-ml-service/src/models/metrics.py",
        "python-ml-service/src/models/blockchain.py",
        "python-ml-service/src/utils/__init__.py",
        "python-ml-service/src/utils/logger.py",
        "python-ml-service/src/utils/serialization.py",
        "python-ml-service/src/utils/validation.py",
        "python-ml-service/configs/default.json",
        "python-ml-service/tests/test_models.py",
        "python-ml-service/tests/test_config.py",
        "python-ml-service/pytest.ini",
        "README.md",
        ".gitignore",
        "docs/PROJECT_ANALYSIS.md",
        "docs/roadmap.md",
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = base_dir / file_path
        if full_path.exists():
            print_success(f"{file_path}")
        else:
            print_error(f"{file_path} - NOT FOUND")
            all_exist = False
    
    return all_exist


def check_config_validity():
    """Check if default configuration is valid."""
    print_header("Checking Configuration Validity")
    
    base_dir = Path(__file__).parent.parent
    config_path = base_dir / "python-ml-service" / "configs" / "default.json"
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Check required top-level keys
        required_keys = ["training", "network", "blockchain"]
        for key in required_keys:
            if key in config:
                print_success(f"Configuration has '{key}' section")
            else:
                print_error(f"Configuration missing '{key}' section")
                return False
        
        # Check training config
        training = config["training"]
        if training.get("learning_rate", 0) > 0:
            print_success(f"Learning rate: {training['learning_rate']}")
        else:
            print_error("Invalid learning rate")
            return False
        
        if training.get("batch_size", 0) > 0:
            print_success(f"Batch size: {training['batch_size']}")
        else:
            print_error("Invalid batch size")
            return False
        
        print_success("Configuration is valid JSON and has required fields")
        return True
        
    except Exception as e:
        print_error(f"Error loading configuration: {e}")
        return False


def test_imports():
    """Test that all modules can be imported."""
    print_header("Testing Module Imports")
    
    test_imports = [
        "src.models.config",
        "src.models.node",
        "src.models.metrics",
        "src.models.blockchain",
        "src.utils.logger",
        "src.utils.serialization",
        "src.utils.validation",
    ]
    
    base_dir = Path(__file__).parent.parent / "python-ml-service"
    original_cwd = Path.cwd()
    
    try:
        import os
        os.chdir(base_dir)
        sys.path.insert(0, str(base_dir))
        
        all_imported = True
        for module_name in test_imports:
            try:
                __import__(module_name)
                print_success(f"Imported {module_name}")
            except Exception as e:
                print_error(f"Failed to import {module_name}: {e}")
                all_imported = False
        
        return all_imported
        
    finally:
        os.chdir(original_cwd)
        if str(base_dir) in sys.path:
            sys.path.remove(str(base_dir))


def main():
    """Main validation function."""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "HyperGPU Phase 1 Validation" + " " * 31 + "║")
    print("╚" + "═" * 78 + "╝")
    
    results = []
    
    # Run checks
    results.append(("Python Version", check_python_version()))
    results.append(("Directory Structure", check_directory_structure()))
    results.append(("Required Files", check_required_files()))
    results.append(("Configuration Validity", check_config_validity()))
    results.append(("Module Imports", test_imports()))
    
    # Summary
    print_header("Validation Summary")
    
    total = len(results)
    passed = sum(1 for _, result in results if result)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{name:.<40} {status}")
    
    print(f"\nTotal: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n" + "🎉" * 40)
        print("✓ Phase 1 Validation Complete - All Checks Passed!")
        print("Ready to proceed with Phase 2 implementation.")
        print("🎉" * 40 + "\n")
        return 0
    else:
        print("\n" + "⚠" * 40)
        print(f"✗ Phase 1 Validation Failed - {total - passed} check(s) failed")
        print("Please fix the issues above before proceeding.")
        print("⚠" * 40 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
