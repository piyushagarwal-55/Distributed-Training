"""
REST API Server for Frontend Communication.

Provides HTTP endpoints for the frontend dashboard to interact with the training coordinator.
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import asyncio
import json
from datetime import datetime

from ..utils.logger import get_logger
from ..core.coordinator import TrainingCoordinator
from ..models.config import SystemConfig, TrainingConfig
from ..models.metrics import TrainingMetrics, AggregatedMetrics

logger = get_logger(__name__)


# Request/Response Models
class StartTrainingRequest(BaseModel):
    """Request to start a training session."""
    model_name: str = "simple_cnn"
    dataset: str = "mnist"
    epochs: int = 10
    batch_size: int = 64
    learning_rate: float = 0.001
    num_nodes: int = 5


class StopTrainingRequest(BaseModel):
    """Request to stop training."""
    force: bool = False


class NodeRegistrationRequest(BaseModel):
    """Request to register a new node."""
    node_id: str
    capabilities: Dict[str, Any]


class ConfigUpdateRequest(BaseModel):
    """Request to update configuration."""
    config: Dict[str, Any]


class SystemStatus(BaseModel):
    """System status response."""
    is_training: bool
    current_epoch: int
    current_step: int
    total_steps: int
    num_nodes: int
    active_nodes: int
    blockchain_connected: bool


class APIServer:
    """REST API server for frontend communication."""
    
    def __init__(self, coordinator: TrainingCoordinator, host: str = "0.0.0.0", port: int = 8000):
        """
        Initialize the API server.
        
        Args:
            coordinator: Training coordinator instance
            host: Host to bind to
            port: Port to listen on
        """
        self.coordinator = coordinator
        self.host = host
        self.port = port
        self.app = FastAPI(title="HyperGPU API", version="1.0.0")
        
        # WebSocket connections for real-time updates
        self.active_connections: List[WebSocket] = []
        
        # Configure CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Frontend URLs
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Setup routes
        self._setup_routes()
        
        logger.info(f"API Server initialized on {host}:{port}")
    
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.app.get("/")
        async def root():
            """Root endpoint."""
            return {"message": "HyperGPU API Server", "version": "1.0.0"}
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        
        @self.app.get("/api/status")
        async def get_status():
            """Get current system status."""
            try:
                nodes = self.coordinator.node_registry.nodes
                active_nodes = sum(1 for node in nodes.values() if node.status == "active")
                
                return SystemStatus(
                    is_training=self.coordinator.is_training,
                    current_epoch=self.coordinator.current_epoch,
                    current_step=self.coordinator.current_step,
                    total_steps=self.coordinator.total_steps,
                    num_nodes=len(nodes),
                    active_nodes=active_nodes,
                    blockchain_connected=self.coordinator.blockchain_integrator is not None
                )
            except Exception as e:
                logger.error(f"Error getting status: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/metrics")
        async def get_metrics():
            """Get training metrics."""
            try:
                if not self.coordinator.metrics_history:
                    return {"metrics": [], "message": "No metrics available yet"}
                
                # Return last 100 metrics for performance
                recent_metrics = self.coordinator.metrics_history[-100:]
                return {
                    "metrics": [m.model_dump() for m in recent_metrics],
                    "count": len(recent_metrics)
                }
            except Exception as e:
                logger.error(f"Error getting metrics: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/nodes/register")
        async def register_node(request: NodeRegistrationRequest):
            """Register a new node."""
            try:
                from ..models.node import NodeMetadata, NodeStatus
                
                # Create node metadata
                gpu_specs = request.capabilities.get('gpu_specs', {})
                node = NodeMetadata(
                    node_id=request.node_id,
                    node_address=request.capabilities.get('address', 'unknown'),
                    status=NodeStatus.IDLE,
                    gpu_model=gpu_specs.get('model', 'Unknown'),
                    gpu_memory_gb=gpu_specs.get('memory_gb', 0),
                    compute_capability=request.capabilities.get('compute_power', 1.0),
                )
                
                # Register node
                success = self.coordinator.register_node(node)
                if not success:
                    raise HTTPException(status_code=400, detail=f"Failed to register node {request.node_id}")
                
                logger.info(f"Node registered: {request.node_id}")
                
                # Broadcast update
                await self._broadcast_update({
                    "type": "node_update",
                    "action": "registered",
                    "node_id": request.node_id
                })
                
                return {
                    "status": "success",
                    "message": f"Node {request.node_id} registered successfully",
                    "node": node.model_dump()
                }
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error registering node: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/nodes")
        async def get_nodes():
            """Get all registered nodes."""
            try:
                nodes = self.coordinator.node_registry.nodes
                return {
                    "nodes": [node.model_dump() for node in nodes.values()],
                    "count": len(nodes)
                }
            except Exception as e:
                logger.error(f"Error getting nodes: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/nodes/{node_id}")
        async def get_node(node_id: str):
            """Get specific node details."""
            try:
                node = self.coordinator.node_registry.nodes.get(node_id)
                if not node:
                    raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
                
                # Get node performance metrics
                performance = self.coordinator.node_performance.get(node_id, [])
                
                return {
                    "node": node.model_dump(),
                    "performance_history": performance[-50:],  # Last 50 measurements
                    "health": self.coordinator.node_health.get(node_id, {})
                }
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting node {node_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/training/start")
        async def start_training(request: StartTrainingRequest):
            """Start a training session."""
            try:
                if self.coordinator.is_training:
                    raise HTTPException(status_code=400, detail="Training already in progress")
                
                # Update coordinator training config
                self.coordinator.training_config.epochs = request.epochs
                self.coordinator.training_config.batch_size = request.batch_size
                self.coordinator.training_config.learning_rate = request.learning_rate
                
                # Initialize training
                success = self.coordinator.initialize_training()
                if not success:
                    raise HTTPException(status_code=500, detail="Failed to initialize training")
                
                # Start training in background
                asyncio.create_task(self._run_training_background())
                
                await self._broadcast_update({
                    "type": "training_started",
                    "timestamp": datetime.now().isoformat()
                })
                
                return {"status": "started", "message": "Training session started"}
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error starting training: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/training/stop")
        async def stop_training(request: StopTrainingRequest):
            """Stop the current training session."""
            try:
                if not self.coordinator.is_training:
                    raise HTTPException(status_code=400, detail="No training in progress")
                
                self.coordinator.stop_training(force=request.force)
                
                await self._broadcast_update({
                    "type": "training_stopped",
                    "timestamp": datetime.now().isoformat()
                })
                
                return {"status": "stopped", "message": "Training session stopped"}
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error stopping training: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/training/pause")
        async def pause_training():
            """Pause the current training session."""
            try:
                if not self.coordinator.is_training:
                    raise HTTPException(status_code=400, detail="No training in progress")
                
                # Implement pause logic
                self.coordinator.is_training = False
                
                await self._broadcast_update({
                    "type": "training_paused",
                    "timestamp": datetime.now().isoformat()
                })
                
                return {"status": "paused", "message": "Training paused"}
            except Exception as e:
                logger.error(f"Error pausing training: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/blockchain/session")
        async def get_blockchain_session():
            """Get blockchain session information."""
            try:
                if not self.coordinator.blockchain_integrator:
                    raise HTTPException(status_code=503, detail="Blockchain not enabled")
                
                session_info = self.coordinator.blockchain_integrator.get_session_info()
                return {"session": session_info}
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting blockchain session: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/blockchain/contributions")
        async def get_contributions():
            """Get all node contributions from blockchain."""
            try:
                if not self.coordinator.blockchain_integrator:
                    raise HTTPException(status_code=503, detail="Blockchain not enabled")
                
                contributions = self.coordinator.blockchain_integrator.get_all_contributions()
                return {"contributions": contributions}
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting contributions: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/config")
        async def get_config():
            """Get current system configuration."""
            try:
                return {"config": self.coordinator.config.model_dump()}
            except Exception as e:
                logger.error(f"Error getting config: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates."""
            await self.connect_websocket(websocket)
            try:
                while True:
                    # Keep connection alive and handle incoming messages
                    data = await websocket.receive_text()
                    # Echo back for now, can implement commands later
                    await websocket.send_text(f"Received: {data}")
            except WebSocketDisconnect:
                self.disconnect_websocket(websocket)
                logger.info("WebSocket client disconnected")
    
    async def connect_websocket(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WebSocket connection. Total connections: {len(self.active_connections)}")
        
        # Send current status
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to HyperGPU",
            "timestamp": datetime.now().isoformat()
        })
    
    def disconnect_websocket(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def _broadcast_update(self, message: Dict[str, Any]):
        """Broadcast update to all connected WebSocket clients."""
        if not self.active_connections:
            return
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to WebSocket: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect_websocket(conn)
    
    async def broadcast_metrics_update(self, metrics: AggregatedMetrics):
        """Broadcast metrics update to all WebSocket clients."""
        await self._broadcast_update({
            "type": "metrics_update",
            "metrics": metrics.model_dump(),
            "timestamp": datetime.now().isoformat()
        })
    
    async def broadcast_node_update(self, node_id: str, status: str):
        """Broadcast node status update."""
        await self._broadcast_update({
            "type": "node_update",
            "node_id": node_id,
            "status": status,
            "timestamp": datetime.now().isoformat()
        })
    
    async def broadcast_training_progress(self, epoch: int, step: int, loss: float):
        """Broadcast training progress update."""
        await self._broadcast_update({
            "type": "training_progress",
            "epoch": epoch,
            "step": step,
            "loss": loss,
            "timestamp": datetime.now().isoformat()
        })
    
    async def _run_training_background(self):
        """Run training in background and broadcast updates."""
        try:
            # This would be called by the coordinator's training loop
            # For now, this is a placeholder
            logger.info("Background training task started")
        except Exception as e:
            logger.error(f"Error in background training: {e}")
            await self._broadcast_update({
                "type": "training_error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    async def run(self):
        """Run the API server."""
        import uvicorn
        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()


def create_api_server(coordinator: TrainingCoordinator, host: str = "0.0.0.0", port: int = 8000) -> APIServer:
    """
    Create and configure an API server instance.
    
    Args:
        coordinator: Training coordinator instance
        host: Host to bind to
        port: Port to listen on
        
    Returns:
        Configured APIServer instance
    """
    return APIServer(coordinator, host, port)


# Create default app instance for uvicorn
# This will use a default configuration
import signal

# Disable signal handlers in coordinator when used as API module
original_signal = signal.signal

from ..models.config import SystemConfig

# Create config with blockchain disabled for API-only mode
_default_config = SystemConfig()
_default_config.blockchain.enabled = False

_default_coordinator = TrainingCoordinator(_default_config)

# Remove signal handlers that interfere with uvicorn
signal.signal(signal.SIGINT, signal.SIG_DFL)
if hasattr(signal, 'SIGBREAK'):
    signal.signal(signal.SIGBREAK, signal.SIG_DFL)

_api_server = APIServer(_default_coordinator)
app = _api_server.app
