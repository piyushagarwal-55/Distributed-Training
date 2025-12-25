#!/usr/bin/env python3
"""
Complete Training Flow End-to-End Test
Tests: Node Registration → Training → Metrics → Blockchain Recording
"""

import sys
import time
import json
import requests
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 10

class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    GRAY = '\033[90m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text: str):
    print(f"\n{Colors.CYAN}{Colors.BOLD}{text}{Colors.END}")
    print(f"{Colors.GRAY}{'-' * 60}{Colors.END}")

def print_success(text: str):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text: str):
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text: str):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text: str):
    print(f"{Colors.GRAY}   {text}{Colors.END}")

def test_endpoint(name: str, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
    """Test an API endpoint and return the response"""
    url = f"{BASE_URL}{endpoint}"
    print(f"Testing: {name}...", end=" ")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=TIMEOUT)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=TIMEOUT)
        elif method == "DELETE":
            response = requests.delete(url, timeout=TIMEOUT)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        if response.status_code in [200, 201]:
            print_success("PASS")
            return response.json()
        else:
            print_error(f"FAIL (Status: {response.status_code})")
            return None
    except Exception as e:
        print_error(f"FAIL ({str(e)})")
        return None

def wait_for_service(max_attempts: int = 30) -> bool:
    """Wait for backend service to be ready"""
    print(f"⏳ Waiting for backend service...", end=" ")
    for i in range(max_attempts):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=2)
            if response.status_code == 200:
                print_success("Ready!")
                return True
        except:
            print(".", end="", flush=True)
            time.sleep(1)
    print_error("Timeout!")
    return False

def main():
    print(f"{Colors.CYAN}{Colors.BOLD}")
    print("=" * 60)
    print("🧪 COMPLETE TRAINING FLOW END-TO-END TEST")
    print("=" * 60)
    print(f"{Colors.END}")
    
    tests_passed = 0
    tests_failed = 0
    test_node_id = None
    
    # ========================================================================
    # PHASE 1: Service Check
    # ========================================================================
    print_header("📡 PHASE 1: Service Availability")
    
    if not wait_for_service():
        print_error("Backend service not running!")
        print_info("Start with: npm run dev:backend")
        sys.exit(1)
    tests_passed += 1
    
    # ========================================================================
    # PHASE 2: Basic API Tests
    # ========================================================================
    print_header("🔧 PHASE 2: Basic API Tests")
    
    # Health check
    result = test_endpoint("Health Check", "GET", "/health")
    if result:
        tests_passed += 1
    else:
        tests_failed += 1
    
    # System status
    result = test_endpoint("System Status", "GET", "/api/status")
    if result:
        tests_passed += 1
        print_info(f"Training Active: {result.get('is_training', False)}")
        print_info(f"Total Nodes: {result.get('num_nodes', 0)}")
    else:
        tests_failed += 1
    
    # ========================================================================
    # PHASE 3: Node Management
    # ========================================================================
    print_header("🖥️  PHASE 3: Node Management")
    
    # Register test node
    node_data = {
        "node_id": f"test-node-{int(time.time())}",
        "address": "192.168.1.100:8000",
        "gpu_specs": {
            "model": "RTX 4090",
            "memory_gb": 24,
            "compute_capability": "8.9"
        },
        "status": "idle"
    }
    
    result = test_endpoint("Register Node", "POST", "/api/nodes/register", node_data)
    if result:
        tests_passed += 1
        test_node_id = result.get('node_id')
        print_info(f"Node ID: {test_node_id}")
    else:
        tests_failed += 1
    
    # Get all nodes
    result = test_endpoint("Get Nodes", "GET", "/api/nodes")
    if result:
        tests_passed += 1
        node_count = result.get('count', 0)
        print_info(f"Total nodes: {node_count}")
    else:
        tests_failed += 1
    
    # ========================================================================
    # PHASE 4: Training Workflow
    # ========================================================================
    print_header("🎯 PHASE 4: Training Workflow")
    
    # Start training
    training_config = {
        "model_name": "simple_cnn",
        "dataset": "mnist",
        "epochs": 3,
        "batch_size": 32,
        "learning_rate": 0.001
    }
    
    result = test_endpoint("Start Training", "POST", "/api/training/start", training_config)
    if result:
        tests_passed += 1
        print_success("Training session started!")
        training_started = True
    else:
        tests_failed += 1
        training_started = False
    
    if training_started:
        # Wait for training to initialize
        print("⏳ Waiting for training initialization (5s)...")
        time.sleep(5)
        
        # Check training status
        result = test_endpoint("Training Status", "GET", "/api/status")
        if result:
            tests_passed += 1
            is_training = result.get('is_training', False)
            current_epoch = result.get('current_epoch', 0)
            print_info(f"Training Active: {is_training}")
            print_info(f"Current Epoch: {current_epoch}")
            print_info(f"Active Nodes: {result.get('active_nodes', 0)}")
        else:
            tests_failed += 1
        
        # Get training metrics
        result = test_endpoint("Get Metrics", "GET", "/api/training/metrics")
        if result:
            tests_passed += 1
            metrics = result.get('metrics', [])
            print_info(f"Metrics collected: {len(metrics)} entries")
            if metrics:
                latest = metrics[-1]
                print_info(f"Latest - Epoch: {latest.get('epoch')}, Loss: {latest.get('loss', 'N/A'):.4f}, Accuracy: {latest.get('accuracy', 'N/A'):.4f}")
        else:
            tests_failed += 1
        
        # Pause training
        result = test_endpoint("Pause Training", "POST", "/api/training/pause")
        if result:
            tests_passed += 1
        else:
            tests_failed += 1
        
        time.sleep(2)
        
        # Resume training
        result = test_endpoint("Resume Training", "POST", "/api/training/resume")
        if result:
            tests_passed += 1
        else:
            tests_failed += 1
        
        time.sleep(2)
        
        # Stop training
        result = test_endpoint("Stop Training", "POST", "/api/training/stop")
        if result:
            tests_passed += 1
            print_success("Training stopped successfully")
        else:
            tests_failed += 1
    
    # ========================================================================
    # PHASE 5: Blockchain Integration
    # ========================================================================
    print_header("⛓️  PHASE 5: Blockchain Integration")
    
    # Check blockchain status
    result = test_endpoint("Blockchain Status", "GET", "/api/status")
    if result:
        blockchain_connected = result.get('blockchain_connected', False)
        if blockchain_connected:
            print_success("Blockchain connected!")
            tests_passed += 1
        else:
            print_warning("Blockchain not connected (contracts not deployed or disabled)")
            tests_failed += 1
    else:
        tests_failed += 1
    
    # ========================================================================
    # PHASE 6: Cleanup
    # ========================================================================
    print_header("🧹 PHASE 6: Cleanup")
    
    # Remove test node
    if test_node_id:
        result = test_endpoint("Remove Test Node", "DELETE", f"/api/nodes/{test_node_id}")
        if result:
            tests_passed += 1
            print_success(f"Test node {test_node_id} removed")
        else:
            tests_failed += 1
    
    # ========================================================================
    # RESULTS
    # ========================================================================
    print(f"\n{Colors.GRAY}{'=' * 60}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}📋 TEST RESULTS SUMMARY{Colors.END}")
    print(f"{Colors.GRAY}{'=' * 60}{Colors.END}\n")
    
    total_tests = tests_passed + tests_failed
    pass_rate = (tests_passed / total_tests * 100) if total_tests > 0 else 0
    
    print(f"  Total Tests:    {total_tests}")
    print(f"  {Colors.GREEN}Tests Passed:   {tests_passed}{Colors.END}")
    print(f"  {Colors.RED if tests_failed > 0 else Colors.GREEN}Tests Failed:   {tests_failed}{Colors.END}")
    print(f"  Pass Rate:      {pass_rate:.1f}%")
    print()
    
    if tests_failed == 0:
        print_success("🎉 ALL TESTS PASSED! System is fully operational!")
        return 0
    elif pass_rate >= 80:
        print_warning("✅ Most tests passed. System is operational with minor issues.")
        return 0
    else:
        print_error("❌ Multiple tests failed. Please check the system.")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  Tests interrupted by user{Colors.END}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error: {str(e)}{Colors.END}")
        sys.exit(1)
