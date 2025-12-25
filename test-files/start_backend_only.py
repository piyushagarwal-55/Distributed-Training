#!/usr/bin/env python3
"""
Start Backend API Only
Quick way to get the API running for testing
"""

import os
import sys
import subprocess
from pathlib import Path

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
CYAN = '\033[96m'
RESET = '\033[0m'

def main():
    print(f"""
{CYAN}================================================================================
🚀 Starting Backend API Server
================================================================================{RESET}
""")

    # Get paths
    root_dir = Path(__file__).parent
    backend_dir = root_dir / "python-ml-service"
    
    if not backend_dir.exists():
        print(f"{RED}✗ Backend directory not found: {backend_dir}{RESET}")
        sys.exit(1)
    
    print(f"{CYAN}[1/2] Checking Python environment...{RESET}")
    python_version = sys.version.split()[0]
    print(f"{GREEN}✓ Python: {python_version}{RESET}")
    
    print(f"{CYAN}[2/2] Starting FastAPI server...{RESET}")
    print(f"{CYAN}  Port: 8000{RESET}")
    print(f"{CYAN}  Working directory: {backend_dir}{RESET}\n")
    
    try:
        # Start the server
        subprocess.run(
            [sys.executable, "-m", "uvicorn", 
             "src.api.rest_server:app", 
             "--host", "0.0.0.0", 
             "--port", "8000", 
             "--reload"],
            cwd=backend_dir,
            check=True
        )
    except KeyboardInterrupt:
        print(f"\n{CYAN}Stopping server...{RESET}")
        print(f"{GREEN}✓ Server stopped{RESET}")
    except subprocess.CalledProcessError as e:
        print(f"{RED}✗ Failed to start server: {e}{RESET}")
        sys.exit(1)

if __name__ == "__main__":
    print(f"""
{GREEN}================================================================================
✅ Backend API will start on: http://localhost:8000
================================================================================{RESET}

{GREEN}🌐 Access Points:{RESET}
   API Documentation:  http://localhost:8000/docs
   Health Check:       http://localhost:8000/health
   OpenAPI Spec:       http://localhost:8000/openapi.json

{GREEN}🔧 API Endpoints:{RESET}
   GET  /health                    - Health check
   GET  /api/v1/status             - System status
   GET  /api/v1/nodes              - List all nodes
   GET  /api/v1/metrics            - Training metrics
   POST /api/v1/training/start     - Start training
   POST /api/v1/training/stop      - Stop training
   
   ... and 10+ more endpoints (see /docs)

{CYAN}Press Ctrl+C to stop the server
================================================================================{RESET}
""")
    main()
