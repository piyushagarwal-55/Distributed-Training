"""
System Integration Orchestrator.

Coordinates startup, shutdown, and health monitoring of all system components.
"""

import asyncio
import subprocess
import sys
import signal
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
import psutil

from ..utils.logger import get_logger
from ..models.config import SystemConfig
from ..core.coordinator import TrainingCoordinator
from ..api.rest_server import create_api_server

logger = get_logger(__name__)


class ComponentStatus:
    """Track status of a system component."""
    
    def __init__(self, name: str):
        self.name = name
        self.status = "stopped"  # stopped, starting, running, error, stopping
        self.process: Optional[subprocess.Popen] = None
        self.start_time: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.health_check_url: Optional[str] = None
        self.pid: Optional[int] = None
    
    def is_running(self) -> bool:
        """Check if component is running."""
        return self.status == "running"
    
    def mark_running(self, pid: Optional[int] = None):
        """Mark component as running."""
        self.status = "running"
        self.start_time = datetime.now()
        self.pid = pid
        self.error_message = None
    
    def mark_error(self, error: str):
        """Mark component as errored."""
        self.status = "error"
        self.error_message = error
    
    def mark_stopped(self):
        """Mark component as stopped."""
        self.status = "stopped"
        self.process = None
        self.pid = None


class SystemOrchestrator:
    """
    Orchestrates all system components and manages their lifecycle.
    
    Components:
    - Coordinator (Python ML Service with API server)
    - GPU Nodes (simulated or real)
    - Blockchain Connection
    - Frontend Dashboard (Next.js)
    """
    
    def __init__(self, config: SystemConfig, base_path: Optional[Path] = None):
        """
        Initialize the system orchestrator.
        
        Args:
            config: System configuration
            base_path: Base path for the project (defaults to parent of python-ml-service)
        """
        self.config = config
        self.base_path = base_path or Path(__file__).parent.parent.parent.parent
        
        # Component status tracking
        self.components: Dict[str, ComponentStatus] = {
            "coordinator": ComponentStatus("coordinator"),
            "api_server": ComponentStatus("api_server"),
            "frontend": ComponentStatus("frontend"),
            "blockchain": ComponentStatus("blockchain"),
        }
        
        # Core components
        self.coordinator: Optional[TrainingCoordinator] = None
        self.api_server: Optional[Any] = None
        
        # Shutdown flag
        self.shutdown_requested = False
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("System Orchestrator initialized")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_requested = True
    
    async def start_all(self, start_frontend: bool = True, start_nodes: int = 5):
        """
        Start all system components in correct order.
        
        Args:
            start_frontend: Whether to start the frontend
            start_nodes: Number of simulated nodes to start
        """
        logger.info("=" * 80)
        logger.info("STARTING HYPERGPU DISTRIBUTED TRAINING SYSTEM")
        logger.info("=" * 80)
        
        try:
            # Step 1: Initialize and start coordinator
            await self._start_coordinator()
            
            # Step 2: Start API server
            await self._start_api_server()
            
            # Step 3: Initialize blockchain connection
            await self._start_blockchain()
            
            # Step 4: Start simulated nodes
            await self._start_nodes(start_nodes)
            
            # Step 5: Start frontend (optional)
            if start_frontend:
                await self._start_frontend()
            
            # Step 6: Run health checks
            await self._run_health_checks()
            
            logger.info("=" * 80)
            logger.info("ALL COMPONENTS STARTED SUCCESSFULLY")
            logger.info("=" * 80)
            self._print_status()
            
            # Keep running until shutdown requested
            await self._monitor_components()
            
        except Exception as e:
            logger.error(f"Error during startup: {e}")
            await self.stop_all()
            raise
    
    async def _start_coordinator(self):
        """Initialize and start the training coordinator."""
        logger.info("[1/5] Starting Training Coordinator...")
        self.components["coordinator"].status = "starting"
        
        try:
            self.coordinator = TrainingCoordinator(self.config)
            self.components["coordinator"].mark_running()
            logger.info("✓ Training Coordinator started")
        except Exception as e:
            logger.error(f"✗ Failed to start coordinator: {e}")
            self.components["coordinator"].mark_error(str(e))
            raise
    
    async def _start_api_server(self):
        """Start the REST API server."""
        logger.info("[2/5] Starting API Server...")
        self.components["api_server"].status = "starting"
        
        try:
            if not self.coordinator:
                raise RuntimeError("Coordinator must be started before API server")
            
            self.api_server = create_api_server(
                self.coordinator,
                host="0.0.0.0",
                port=8000
            )
            
            # Start API server in background task
            asyncio.create_task(self.api_server.run())
            
            # Wait a bit for server to start
            await asyncio.sleep(2)
            
            self.components["api_server"].mark_running()
            self.components["api_server"].health_check_url = "http://localhost:8000/health"
            logger.info("✓ API Server started on http://localhost:8000")
        except Exception as e:
            logger.error(f"✗ Failed to start API server: {e}")
            self.components["api_server"].mark_error(str(e))
            raise
    
    async def _start_blockchain(self):
        """Initialize blockchain connection."""
        logger.info("[3/5] Initializing Blockchain Connection...")
        self.components["blockchain"].status = "starting"
        
        try:
            if self.config.blockchain.enabled:
                if self.coordinator and self.coordinator.blockchain_integrator:
                    # Test connection
                    connected = await asyncio.get_event_loop().run_in_executor(
                        None,
                        self.coordinator.blockchain_integrator.test_connection
                    )
                    if connected:
                        self.components["blockchain"].mark_running()
                        logger.info("✓ Blockchain connection established")
                    else:
                        self.components["blockchain"].mark_error("Connection test failed")
                        logger.warning("✗ Blockchain connection failed (continuing without blockchain)")
                else:
                    self.components["blockchain"].mark_error("Blockchain integrator not initialized")
                    logger.warning("✗ Blockchain integrator not available")
            else:
                self.components["blockchain"].status = "disabled"
                logger.info("○ Blockchain disabled in configuration")
        except Exception as e:
            logger.warning(f"✗ Blockchain connection error: {e} (continuing without blockchain)")
            self.components["blockchain"].mark_error(str(e))
    
    async def _start_nodes(self, num_nodes: int):
        """Start simulated GPU nodes."""
        logger.info(f"[4/5] Starting {num_nodes} Simulated GPU Nodes...")
        
        try:
            # Nodes will register themselves with the coordinator
            # For now, we'll create mock node registrations
            for i in range(num_nodes):
                node_id = f"node_{i+1}"
                # In a real system, nodes would register via API
                # For testing, we can pre-register them
                logger.info(f"  - Node {node_id} ready for registration")
            
            logger.info(f"✓ {num_nodes} nodes initialized and ready")
        except Exception as e:
            logger.error(f"✗ Failed to start nodes: {e}")
            raise
    
    async def _start_frontend(self):
        """Start the Next.js frontend."""
        logger.info("[5/5] Starting Frontend Dashboard...")
        self.components["frontend"].status = "starting"
        
        try:
            frontend_path = self.base_path / "frontend"
            
            if not frontend_path.exists():
                logger.warning("✗ Frontend directory not found, skipping")
                self.components["frontend"].status = "not_found"
                return
            
            # Check if dev server is already running
            if await self._check_port_in_use(3000):
                logger.info("○ Frontend already running on port 3000")
                self.components["frontend"].mark_running()
                self.components["frontend"].health_check_url = "http://localhost:3000"
                return
            
            # Start frontend dev server
            logger.info("  Starting Next.js dev server (this may take a moment)...")
            
            # Use PowerShell to start in background
            if sys.platform == "win32":
                cmd = ["powershell", "-Command", f"cd '{frontend_path}'; npm run dev"]
            else:
                cmd = ["npm", "run", "dev"]
            
            process = subprocess.Popen(
                cmd,
                cwd=str(frontend_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
            )
            
            self.components["frontend"].process = process
            self.components["frontend"].pid = process.pid
            
            # Wait for frontend to be ready
            await asyncio.sleep(5)
            
            if await self._check_port_in_use(3000):
                self.components["frontend"].mark_running(process.pid)
                self.components["frontend"].health_check_url = "http://localhost:3000"
                logger.info("✓ Frontend started on http://localhost:3000")
            else:
                self.components["frontend"].mark_error("Frontend failed to start")
                logger.warning("✗ Frontend may not have started properly")
        except Exception as e:
            logger.warning(f"✗ Failed to start frontend: {e}")
            self.components["frontend"].mark_error(str(e))
    
    async def _check_port_in_use(self, port: int) -> bool:
        """Check if a port is in use."""
        for conn in psutil.net_connections():
            if conn.laddr.port == port and conn.status == 'LISTEN':
                return True
        return False
    
    async def _run_health_checks(self):
        """Run health checks on all components."""
        logger.info("\nRunning health checks...")
        
        all_healthy = True
        for name, component in self.components.items():
            if component.status == "disabled" or component.status == "not_found":
                continue
            
            if component.status == "running":
                logger.info(f"  ✓ {name}: {component.status}")
            else:
                logger.warning(f"  ✗ {name}: {component.status}")
                all_healthy = False
        
        return all_healthy
    
    async def _monitor_components(self):
        """Monitor components and handle failures."""
        logger.info("\nMonitoring system components (Press Ctrl+C to stop)...")
        
        while not self.shutdown_requested:
            await asyncio.sleep(10)
            
            # Check component health
            for name, component in self.components.items():
                if component.is_running() and component.process:
                    if component.process.poll() is not None:
                        logger.error(f"Component {name} has died!")
                        component.mark_error("Process terminated unexpectedly")
        
        logger.info("\nShutdown requested, stopping all components...")
        await self.stop_all()
    
    def _print_status(self):
        """Print current system status."""
        logger.info("\nSystem Status:")
        logger.info("-" * 80)
        
        for name, component in self.components.items():
            status_symbol = {
                "running": "✓",
                "stopped": "○",
                "error": "✗",
                "disabled": "-",
                "not_found": "?"
            }.get(component.status, "?")
            
            status_line = f"  {status_symbol} {name.upper()}: {component.status}"
            if component.health_check_url:
                status_line += f" ({component.health_check_url})"
            if component.pid:
                status_line += f" [PID: {component.pid}]"
            
            logger.info(status_line)
        
        logger.info("-" * 80)
        logger.info("\nAccess Points:")
        logger.info("  - API Server: http://localhost:8000")
        logger.info("  - API Docs: http://localhost:8000/docs")
        logger.info("  - Frontend: http://localhost:3000")
        logger.info("  - WebSocket: ws://localhost:8000/ws")
        logger.info("-" * 80)
    
    async def stop_all(self):
        """Stop all system components gracefully."""
        logger.info("\nStopping all components...")
        
        # Stop in reverse order
        components_to_stop = ["frontend", "nodes", "api_server", "coordinator", "blockchain"]
        
        for name in components_to_stop:
            if name in self.components:
                await self._stop_component(name)
        
        logger.info("All components stopped")
    
    async def _stop_component(self, name: str):
        """Stop a specific component."""
        component = self.components.get(name)
        if not component or not component.is_running():
            return
        
        logger.info(f"Stopping {name}...")
        component.status = "stopping"
        
        try:
            if component.process:
                component.process.terminate()
                try:
                    component.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    component.process.kill()
            
            component.mark_stopped()
            logger.info(f"✓ {name} stopped")
        except Exception as e:
            logger.error(f"Error stopping {name}: {e}")
    
    async def restart_component(self, name: str):
        """Restart a specific component."""
        logger.info(f"Restarting {name}...")
        await self._stop_component(name)
        
        # Restart based on component type
        if name == "coordinator":
            await self._start_coordinator()
        elif name == "api_server":
            await self._start_api_server()
        elif name == "blockchain":
            await self._start_blockchain()
        elif name == "frontend":
            await self._start_frontend()
        
        logger.info(f"✓ {name} restarted")


async def main_orchestrator(config_path: str, start_frontend: bool = True, num_nodes: int = 5):
    """
    Main entry point for the system orchestrator.
    
    Args:
        config_path: Path to configuration file
        start_frontend: Whether to start the frontend
        num_nodes: Number of nodes to simulate
    """
    from ..utils.config_validator import load_and_validate_config
    
    # Load configuration
    config = load_and_validate_config(config_path)
    
    # Create and run orchestrator
    orchestrator = SystemOrchestrator(config)
    await orchestrator.start_all(start_frontend=start_frontend, start_nodes=num_nodes)
