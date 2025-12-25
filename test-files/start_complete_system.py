#!/usr/bin/env python3
"""
Complete System Startup Script
Starts Backend API, Frontend Dashboard, and Blockchain Node
"""

import os
import sys
import time
import signal
import subprocess
from pathlib import Path
from typing import List, Optional

# ANSI Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
RESET = '\033[0m'

def print_success(msg: str):
    print(f"{GREEN}{msg}{RESET}")

def print_error(msg: str):
    print(f"{RED}{msg}{RESET}")

def print_info(msg: str):
    print(f"{CYAN}{msg}{RESET}")

def print_warning(msg: str):
    print(f"{YELLOW}{msg}{RESET}")

class SystemManager:
    def __init__(self, skip_blockchain: bool = False):
        self.processes: List[subprocess.Popen] = []
        self.skip_blockchain = skip_blockchain
        self.root_dir = Path(__file__).parent

    def cleanup(self, signum=None, frame=None):
        """Stop all running processes"""
        print_info("\n🛑 Stopping all components...")
        
        for proc in self.processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
                print_info(f"  ✓ Stopped process {proc.pid}")
            except subprocess.TimeoutExpired:
                proc.kill()
                print_warning(f"  ⚠ Force killed process {proc.pid}")
            except Exception as e:
                print_warning(f"  ⚠ Error stopping process: {e}")
        
        print_success("✓ All components stopped")
        sys.exit(0)

    def check_command(self, cmd: str) -> bool:
        """Check if a command exists"""
        try:
            subprocess.run([cmd, "--version"], 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE,
                          check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def start_blockchain(self) -> bool:
        """Start Hardhat blockchain node"""
        if self.skip_blockchain:
            print_info("[3/5] Skipping Blockchain (--skip-blockchain flag)")
            return True

        print_info("[3/5] Starting Blockchain Node (Hardhat)...")
        blockchain_dir = self.root_dir / "smart-contracts"
        
        if not blockchain_dir.exists():
            print_warning("⚠ Blockchain directory not found, skipping...")
            return True

        node_modules = blockchain_dir / "node_modules"
        if not node_modules.exists():
            print_info("  Installing blockchain dependencies...")
            subprocess.run(["npm", "install"], 
                          cwd=blockchain_dir,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)

        print_info("  Starting Hardhat node on port 8545...")
        try:
            proc = subprocess.Popen(
                ["npx", "hardhat", "node"],
                cwd=blockchain_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
            )
            self.processes.append(proc)
            print_success(f"✓ Blockchain started (PID: {proc.pid})")
            time.sleep(3)
            return True
        except Exception as e:
            print_error(f"✗ Failed to start blockchain: {e}")
            return False

    def start_backend(self) -> bool:
        """Start FastAPI backend server"""
        print_info("[4/5] Starting Backend API Server...")
        backend_dir = self.root_dir / "python-ml-service"
        
        if not backend_dir.exists():
            print_error(f"✗ Backend directory not found: {backend_dir}")
            return False

        print_info("  Starting FastAPI server on port 8000...")
        try:
            proc = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", 
                 "src.api.rest_server:app", 
                 "--host", "0.0.0.0", 
                 "--port", "8000", 
                 "--reload"],
                cwd=backend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
            )
            self.processes.append(proc)
            print_success(f"✓ Backend API started (PID: {proc.pid})")
            time.sleep(2)
            return True
        except Exception as e:
            print_error(f"✗ Failed to start backend: {e}")
            return False

    def start_frontend(self) -> bool:
        """Start Next.js frontend"""
        print_info("[5/5] Starting Frontend Dashboard...")
        frontend_dir = self.root_dir / "frontend"
        
        if not frontend_dir.exists():
            print_error(f"✗ Frontend directory not found: {frontend_dir}")
            return False

        node_modules = frontend_dir / "node_modules"
        if not node_modules.exists():
            print_info("  Installing frontend dependencies...")
            subprocess.run(["npm", "install"], 
                          cwd=frontend_dir,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)

        print_info("  Starting Next.js on port 3000...")
        try:
            proc = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
            )
            self.processes.append(proc)
            print_success(f"✓ Frontend started (PID: {proc.pid})")
            return True
        except Exception as e:
            print_error(f"✗ Failed to start frontend: {e}")
            return False

    def run(self):
        """Main execution"""
        print(f"""
{CYAN}================================================================================
🚀 Starting Complete Distributed Training System
================================================================================{RESET}
""")

        # Check prerequisites
        print_info("[1/5] Checking Python environment...")
        python_version = sys.version.split()[0]
        print_success(f"✓ Python: {python_version}")

        print_info("[2/5] Checking Node.js environment...")
        if not self.check_command("node"):
            print_error("✗ Node.js not found. Please install Node.js 16+")
            return False
        
        node_version = subprocess.check_output(["node", "--version"], 
                                               text=True).strip()
        print_success(f"✓ Node.js: {node_version}")

        if not self.check_command("npm"):
            print_error("✗ npm not found. Please install npm")
            return False

        print_success("✓ All prerequisites met\n")

        # Start components
        if not self.start_blockchain():
            self.cleanup()
            return False

        if not self.start_backend():
            self.cleanup()
            return False

        if not self.start_frontend():
            self.cleanup()
            return False

        # Success message
        print(f"""
{GREEN}================================================================================
✅ System Started Successfully!
================================================================================{RESET}

{GREEN}🌐 Access Points:{RESET}
   Frontend Dashboard: http://localhost:3000
   Backend API Docs:   http://localhost:8000/docs
   API Health Check:   http://localhost:8000/health
   Blockchain RPC:     http://localhost:8545 (if enabled)

{GREEN}📊 Components Running:{RESET}
""")
        
        for i, proc in enumerate(self.processes, 1):
            component = ["Blockchain", "Backend API", "Frontend"][i-1] if i <= 3 else f"Process {i}"
            print(f"   ✓ {component} (PID: {proc.pid})")

        print(f"""
{CYAN}🔧 Quick Actions:{RESET}
   • Open Dashboard: Open http://localhost:3000 in your browser
   • View API Docs:  Open http://localhost:8000/docs
   • Stop System:    Press Ctrl+C

{CYAN}================================================================================{RESET}
""")

        print_info("⏳ Waiting for components to initialize...")
        time.sleep(5)

        print_success("\n✓ All components ready!")
        print_info("Opening dashboard in browser...")
        time.sleep(2)

        # Open browser
        import webbrowser
        webbrowser.open("http://localhost:3000")

        print(f"\n{YELLOW}📝 System is running. Press Ctrl+C to stop all components.{RESET}\n")

        # Monitor processes
        try:
            while True:
                time.sleep(5)
                for proc in self.processes:
                    if proc.poll() is not None:
                        print_error(f"\n✗ Process {proc.pid} has stopped unexpectedly!")
                        print_info(f"Exit code: {proc.returncode}")
                        self.cleanup()
                        return False
        except KeyboardInterrupt:
            self.cleanup()

        return True

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Start Complete Distributed Training System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start_complete_system.py                    # Start all components
  python start_complete_system.py --skip-blockchain  # Start without blockchain

After startup:
  - Frontend: http://localhost:3000
  - API Docs: http://localhost:8000/docs
  - Health:   http://localhost:8000/health
        """
    )
    
    parser.add_argument('--skip-blockchain', action='store_true',
                       help='Skip blockchain startup (for testing)')
    
    args = parser.parse_args()
    
    manager = SystemManager(skip_blockchain=args.skip_blockchain)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, manager.cleanup)
    if sys.platform != "win32":
        signal.signal(signal.SIGTERM, manager.cleanup)
    
    success = manager.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
