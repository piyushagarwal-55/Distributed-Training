"""
Simple Phase 7 Test Runner

Runs tests without complex PowerShell dependencies.
"""

import subprocess
import sys
from pathlib import Path

def main():
    print("=" * 80)
    print("PHASE 7 TEST RUNNER")
    print("=" * 80)
    print()
    
    # Check we're in the right directory
    script_dir = Path(__file__).parent
    print(f"Running from: {script_dir}")
    print()
    
    # Install dependencies first
    print("[1/2] Installing required dependencies...")
    print("-" * 80)
    
    deps = ["fastapi", "uvicorn", "httpx", "websockets", "loguru", "psutil"]
    for dep in deps:
        print(f"  Installing {dep}...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", dep, "-q"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"    Warning: Failed to install {dep}")
        else:
            print(f"    ✓ {dep} installed")
    
    print()
    print("[2/2] Running Phase 7 Tests...")
    print("-" * 80)
    print()
    
    # Run pytest on all test files
    test_files = [
        "tests/test_integration.py",
        "tests/test_e2e_training.py",
        "tests/test_resilience.py",
        "tests/test_performance.py"
    ]
    
    for test_file in test_files:
        test_path = script_dir / test_file
        if test_path.exists():
            print(f"\nRunning {test_file}...")
            print("-" * 40)
            
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_path), "-v", "-s", "--tb=short"],
                cwd=str(script_dir)
            )
            
            if result.returncode != 0:
                print(f"\n⚠ Some tests in {test_file} failed")
            else:
                print(f"\n✓ All tests in {test_file} passed")
        else:
            print(f"⚠ Test file not found: {test_file}")
    
    print()
    print("=" * 80)
    print("TEST RUN COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
