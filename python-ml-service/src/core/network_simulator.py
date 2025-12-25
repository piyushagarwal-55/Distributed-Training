"""
Network Simulation Layer - Simulates realistic network conditions.

This module provides network condition simulation to mimic real-world
distributed environments with latency, packet loss, and bandwidth constraints.
"""

import time
import random
import threading
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from enum import Enum
import numpy as np
from collections import deque

from ..utils.logger import get_logger

logger = get_logger(__name__)


class NetworkProfile(str, Enum):
    """Predefined network quality profiles."""
    PERFECT = "perfect"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"
    UNSTABLE = "unstable"


class NetworkEvent:
    """Represents a network condition change event."""
    
    def __init__(
        self,
        event_type: str,
        target_node: Optional[str],
        new_profile: Optional[str],
        scheduled_time: Optional[float] = None
    ):
        self.event_type = event_type  # 'profile_change', 'latency_spike', 'disconnect'
        self.target_node = target_node
        self.new_profile = new_profile
        self.scheduled_time = scheduled_time or time.time()
        self.executed = False


class NetworkSimulator:
    """
    Simulates network conditions for distributed training.
    
    This class wraps communication functions and applies realistic network
    conditions including latency, packet loss, and bandwidth throttling.
    """
    
    # Network profile configurations
    PROFILE_CONFIGS = {
        NetworkProfile.PERFECT: {
            'latency_ms': (0, 1),  # (min, max)
            'packet_loss_rate': 0.0,
            'bandwidth_mbps': float('inf'),
            'jitter_ms': 0
        },
        NetworkProfile.GOOD: {
            'latency_ms': (10, 50),
            'packet_loss_rate': 0.001,  # 0.1%
            'bandwidth_mbps': 100,
            'jitter_ms': 5
        },
        NetworkProfile.AVERAGE: {
            'latency_ms': (50, 150),
            'packet_loss_rate': 0.01,  # 1%
            'bandwidth_mbps': 50,
            'jitter_ms': 20
        },
        NetworkProfile.POOR: {
            'latency_ms': (150, 300),
            'packet_loss_rate': 0.05,  # 5%
            'bandwidth_mbps': 10,
            'jitter_ms': 50
        },
        NetworkProfile.UNSTABLE: {
            'latency_ms': (50, 500),
            'packet_loss_rate': 0.10,  # 10%
            'bandwidth_mbps': 20,
            'jitter_ms': 100
        }
    }
    
    def __init__(self, default_profile: str = "average"):
        """
        Initialize network simulator.
        
        Args:
            default_profile: Default network profile for all nodes
        """
        self.default_profile = default_profile
        
        # Per-node network profiles
        self.node_profiles: Dict[str, str] = {}
        
        # Network metrics tracking
        self.metrics = {
            'total_messages': 0,
            'dropped_messages': 0,
            'total_latency_ms': 0.0,
            'retries': 0
        }
        
        # Per-node metrics
        self.node_metrics: Dict[str, Dict[str, Any]] = {}
        
        # Latency history for each node (for monitoring)
        self.latency_history: Dict[str, deque] = {}
        
        # Scheduled events
        self.scheduled_events: List[NetworkEvent] = []
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Simulation state
        self.enabled = True
        
        logger.info(f"Network Simulator initialized with default profile: {default_profile}")
        print(f"[NETWORK SIM] Initialized with default profile: {default_profile}")
    
    def set_node_profile(self, node_id: str, profile: str):
        """
        Set network profile for a specific node.
        
        Args:
            node_id: Node identifier
            profile: Network profile name
        """
        with self.lock:
            if profile not in [p.value for p in NetworkProfile]:
                logger.warning(f"Unknown profile '{profile}', using 'average'")
                profile = NetworkProfile.AVERAGE.value
            
            old_profile = self.node_profiles.get(node_id, self.default_profile)
            self.node_profiles[node_id] = profile
            
            # Initialize metrics for this node if needed
            if node_id not in self.node_metrics:
                self.node_metrics[node_id] = {
                    'messages_sent': 0,
                    'messages_dropped': 0,
                    'total_latency_ms': 0.0,
                    'retries': 0,
                    'profile_changes': 0
                }
                self.latency_history[node_id] = deque(maxlen=100)
            
            self.node_metrics[node_id]['profile_changes'] += 1
            
            logger.info(f"[NETWORK SIM] Node {node_id} profile: {old_profile} -> {profile}")
            print(f"[NETWORK SIM] Node {node_id} profile changed: {old_profile} -> {profile}")
    
    def get_node_profile(self, node_id: str) -> str:
        """Get the current network profile for a node."""
        return self.node_profiles.get(node_id, self.default_profile)
    
    def simulate_communication(
        self,
        node_id: str,
        message: Any,
        message_size_bytes: Optional[int] = None
    ) -> tuple[bool, float, Any]:
        """
        Simulate sending a message through the network.
        
        Args:
            node_id: Identifier of the node sending/receiving
            message: The message to send
            message_size_bytes: Size of message in bytes (for bandwidth simulation)
            
        Returns:
            tuple: (success, latency_ms, message)
                - success: Whether message was delivered (not dropped)
                - latency_ms: Simulated latency in milliseconds
                - message: The message (unchanged if successful, None if dropped)
        """
        if not self.enabled:
            return True, 0.0, message
        
        with self.lock:
            # Get profile config
            profile = self.get_node_profile(node_id)
            config = self.PROFILE_CONFIGS[NetworkProfile(profile)]
            
            # Track message
            self.metrics['total_messages'] += 1
            if node_id not in self.node_metrics:
                self.node_metrics[node_id] = {
                    'messages_sent': 0,
                    'messages_dropped': 0,
                    'total_latency_ms': 0.0,
                    'retries': 0,
                    'profile_changes': 0
                }
                self.latency_history[node_id] = deque(maxlen=100)
            
            self.node_metrics[node_id]['messages_sent'] += 1
            
            # Check for packet loss
            if random.random() < config['packet_loss_rate']:
                # Message dropped
                self.metrics['dropped_messages'] += 1
                self.node_metrics[node_id]['messages_dropped'] += 1
                
                logger.debug(f"[NETWORK SIM] Message from {node_id} DROPPED (packet loss)")
                print(f"[NETWORK SIM] ✗ Node {node_id}: Message dropped (packet loss)")
                
                return False, 0.0, None
            
            # Calculate latency
            latency_ms = self._calculate_latency(config)
            
            # Add bandwidth delay if message size provided
            if message_size_bytes is not None:
                bandwidth_delay_ms = self._calculate_bandwidth_delay(
                    message_size_bytes,
                    config['bandwidth_mbps']
                )
                latency_ms += bandwidth_delay_ms
            
            # Track latency
            self.metrics['total_latency_ms'] += latency_ms
            self.node_metrics[node_id]['total_latency_ms'] += latency_ms
            self.latency_history[node_id].append(latency_ms)
            
            # Apply the delay
            time.sleep(latency_ms / 1000.0)  # Convert ms to seconds
            
            logger.debug(f"[NETWORK SIM] Node {node_id}: latency {latency_ms:.1f}ms")
            
            return True, latency_ms, message
    
    def _calculate_latency(self, config: Dict[str, Any]) -> float:
        """
        Calculate latency with jitter.
        
        Args:
            config: Network profile configuration
            
        Returns:
            Latency in milliseconds
        """
        # Base latency from range
        min_lat, max_lat = config['latency_ms']
        base_latency = random.uniform(min_lat, max_lat)
        
        # Add jitter
        jitter = random.gauss(0, config['jitter_ms'] / 3)  # 3-sigma rule
        latency = base_latency + jitter
        
        # Ensure non-negative
        return max(0, latency)
    
    def _calculate_bandwidth_delay(self, size_bytes: int, bandwidth_mbps: float) -> float:
        """
        Calculate delay due to bandwidth limitation.
        
        Args:
            size_bytes: Message size in bytes
            bandwidth_mbps: Bandwidth in Mbps
            
        Returns:
            Delay in milliseconds
        """
        if bandwidth_mbps == float('inf'):
            return 0.0
        
        # Convert to consistent units
        bandwidth_bytes_per_second = (bandwidth_mbps * 1000000) / 8
        
        # Calculate transmission time
        transmission_time_seconds = size_bytes / bandwidth_bytes_per_second
        
        return transmission_time_seconds * 1000  # Convert to ms
    
    def simulate_with_retry(
        self,
        node_id: str,
        message: Any,
        max_retries: int = 3,
        message_size_bytes: Optional[int] = None
    ) -> tuple[bool, float, Any, int]:
        """
        Simulate communication with automatic retry on failure.
        
        Args:
            node_id: Node identifier
            message: Message to send
            max_retries: Maximum number of retry attempts
            message_size_bytes: Message size for bandwidth simulation
            
        Returns:
            tuple: (success, total_latency_ms, message, attempts)
        """
        total_latency = 0.0
        attempts = 0
        
        for attempt in range(max_retries + 1):
            attempts += 1
            success, latency, result = self.simulate_communication(
                node_id, message, message_size_bytes
            )
            total_latency += latency
            
            if success:
                if attempt > 0:
                    logger.info(f"[NETWORK SIM] Node {node_id}: Success after {attempt} retries")
                    print(f"[NETWORK SIM] Node {node_id}: ✓ Delivered after {attempt} retries")
                return True, total_latency, result, attempts
            
            # Track retry
            with self.lock:
                self.metrics['retries'] += 1
                self.node_metrics[node_id]['retries'] += 1
            
            # Exponential backoff before retry
            if attempt < max_retries:
                backoff_time = (2 ** attempt) * 0.1  # 0.1s, 0.2s, 0.4s, ...
                logger.debug(f"[NETWORK SIM] Node {node_id}: Retry {attempt + 1}, "
                           f"backing off {backoff_time:.2f}s")
                time.sleep(backoff_time)
        
        logger.warning(f"[NETWORK SIM] Node {node_id}: Failed after {max_retries} retries")
        print(f"[NETWORK SIM] ✗ Node {node_id}: Failed after {max_retries} retries")
        
        return False, total_latency, None, attempts
    
    def schedule_event(self, event: NetworkEvent):
        """
        Schedule a network event to occur.
        
        Args:
            event: NetworkEvent to schedule
        """
        with self.lock:
            self.scheduled_events.append(event)
            logger.info(f"[NETWORK SIM] Scheduled event: {event.event_type} "
                       f"for node {event.target_node} at {event.scheduled_time}")
    
    def process_scheduled_events(self):
        """Process any scheduled events that are due."""
        with self.lock:
            current_time = time.time()
            
            for event in self.scheduled_events:
                if not event.executed and current_time >= event.scheduled_time:
                    self._execute_event(event)
                    event.executed = True
            
            # Remove executed events
            self.scheduled_events = [e for e in self.scheduled_events if not e.executed]
    
    def _execute_event(self, event: NetworkEvent):
        """Execute a scheduled network event."""
        logger.info(f"[NETWORK SIM] Executing event: {event.event_type} "
                   f"for node {event.target_node}")
        print(f"[NETWORK SIM] Event triggered: {event.event_type} for {event.target_node}")
        
        if event.event_type == 'profile_change' and event.new_profile:
            self.set_node_profile(event.target_node, event.new_profile)
        
        elif event.event_type == 'latency_spike':
            # Temporarily worsen the profile
            # This is a simplified version; could be more sophisticated
            self.set_node_profile(event.target_node, NetworkProfile.POOR.value)
        
        elif event.event_type == 'disconnect':
            # Set to worst profile to simulate disconnect
            self.set_node_profile(event.target_node, NetworkProfile.UNSTABLE.value)
    
    def inject_latency_spike(self, node_id: str, duration_seconds: float = 5.0):
        """
        Inject a temporary latency spike for a node.
        
        Args:
            node_id: Target node
            duration_seconds: How long the spike should last
        """
        # Store current profile
        current_profile = self.get_node_profile(node_id)
        
        # Create spike event
        spike_event = NetworkEvent(
            event_type='latency_spike',
            target_node=node_id,
            new_profile=NetworkProfile.POOR.value,
            scheduled_time=time.time()
        )
        
        # Create recovery event
        recovery_event = NetworkEvent(
            event_type='profile_change',
            target_node=node_id,
            new_profile=current_profile,
            scheduled_time=time.time() + duration_seconds
        )
        
        self.schedule_event(spike_event)
        self.schedule_event(recovery_event)
        
        logger.info(f"[NETWORK SIM] Injected latency spike for {node_id}, "
                   f"duration: {duration_seconds}s")
        print(f"[NETWORK SIM] Injected latency spike for {node_id}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get overall network simulation metrics.
        
        Returns:
            Dictionary with aggregated metrics
        """
        with self.lock:
            return {
                'total_messages': self.metrics['total_messages'],
                'dropped_messages': self.metrics['dropped_messages'],
                'drop_rate': (
                    self.metrics['dropped_messages'] / self.metrics['total_messages']
                    if self.metrics['total_messages'] > 0 else 0.0
                ),
                'average_latency_ms': (
                    self.metrics['total_latency_ms'] / self.metrics['total_messages']
                    if self.metrics['total_messages'] > 0 else 0.0
                ),
                'total_retries': self.metrics['retries'],
                'scheduled_events': len(self.scheduled_events)
            }
    
    def get_node_metrics(self, node_id: str) -> Dict[str, Any]:
        """
        Get network metrics for a specific node.
        
        Args:
            node_id: Node identifier
            
        Returns:
            Dictionary with node-specific metrics
        """
        with self.lock:
            if node_id not in self.node_metrics:
                return {}
            
            metrics = self.node_metrics[node_id].copy()
            
            # Calculate statistics
            if metrics['messages_sent'] > 0:
                metrics['drop_rate'] = metrics['messages_dropped'] / metrics['messages_sent']
                metrics['average_latency_ms'] = (
                    metrics['total_latency_ms'] / metrics['messages_sent']
                )
            else:
                metrics['drop_rate'] = 0.0
                metrics['average_latency_ms'] = 0.0
            
            # Add latency statistics
            if node_id in self.latency_history and len(self.latency_history[node_id]) > 0:
                latencies = list(self.latency_history[node_id])
                metrics['latency_stats'] = {
                    'min': float(np.min(latencies)),
                    'max': float(np.max(latencies)),
                    'mean': float(np.mean(latencies)),
                    'std': float(np.std(latencies)),
                    'median': float(np.median(latencies))
                }
            
            metrics['current_profile'] = self.get_node_profile(node_id)
            
            return metrics
    
    def get_all_node_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all nodes."""
        with self.lock:
            return {
                node_id: self.get_node_metrics(node_id)
                for node_id in self.node_metrics.keys()
            }
    
    def reset_metrics(self):
        """Reset all metrics."""
        with self.lock:
            self.metrics = {
                'total_messages': 0,
                'dropped_messages': 0,
                'total_latency_ms': 0.0,
                'retries': 0
            }
            self.node_metrics.clear()
            self.latency_history.clear()
            
            logger.info("[NETWORK SIM] Metrics reset")
    
    def enable(self):
        """Enable network simulation."""
        self.enabled = True
        logger.info("[NETWORK SIM] Simulation enabled")
        print("[NETWORK SIM] Network simulation enabled")
    
    def disable(self):
        """Disable network simulation (perfect network)."""
        self.enabled = False
        logger.info("[NETWORK SIM] Simulation disabled")
        print("[NETWORK SIM] Network simulation disabled")
    
    def set_geographic_regions(
        self,
        node_regions: Dict[str, str],
        inter_region_latency_ms: Optional[Dict[tuple, float]] = None
    ):
        """
        Set geographic regions for nodes with inter-region latency.
        
        Args:
            node_regions: Dictionary mapping node_id to region name
            inter_region_latency_ms: Dictionary mapping (region1, region2) to base latency
        """
        # This is a placeholder for more sophisticated geographic simulation
        # For now, we'll adjust profiles based on regions
        
        logger.info(f"[NETWORK SIM] Setting geographic regions for {len(node_regions)} nodes")
        
        for node_id, region in node_regions.items():
            # Could set different profiles based on region
            logger.debug(f"[NETWORK SIM] Node {node_id} assigned to region: {region}")
