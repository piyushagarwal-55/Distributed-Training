"""
Network Quality Monitor - Monitors network conditions between coordinator and nodes.

This module provides real-time visibility into network conditions, tracking
latency, packet loss, reliability, and connection quality for each node.
"""

import time
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import deque
from enum import Enum
import numpy as np

from ..utils.logger import get_logger

logger = get_logger(__name__)


class ConnectionQuality(str, Enum):
    """Connection quality categories."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"
    OFFLINE = "offline"


class ConnectionProfile:
    """
    Profile of connection quality for a single node.
    
    Tracks historical data and current status.
    """
    
    def __init__(self, node_id: str, history_size: int = 50):
        """
        Initialize connection profile.
        
        Args:
            node_id: Node identifier
            history_size: Number of measurements to keep in history
        """
        self.node_id = node_id
        self.history_size = history_size
        
        # Historical data
        self.latency_history: deque = deque(maxlen=history_size)
        self.packet_loss_events: deque = deque(maxlen=history_size)
        self.response_times: deque = deque(maxlen=history_size)
        
        # Statistics
        self.total_messages_sent = 0
        self.total_messages_received = 0
        self.total_failures = 0
        self.consecutive_failures = 0
        
        # Current state
        self.current_quality = ConnectionQuality.GOOD
        self.previous_quality = ConnectionQuality.GOOD
        self.quality_changes = 0
        self.last_update = time.time()
        self.last_successful_communication = time.time()
        
        # Thresholds for hysteresis (prevent flapping)
        self.quality_change_threshold = 3  # Need 3 consistent measurements to change
        self.pending_quality_change = None
        self.pending_change_count = 0
    
    def record_communication(
        self,
        latency_ms: float,
        success: bool,
        response_time_ms: Optional[float] = None
    ):
        """
        Record a communication event.
        
        Args:
            latency_ms: One-way latency in milliseconds
            success: Whether communication succeeded
            response_time_ms: Round-trip time in milliseconds
        """
        self.latency_history.append(latency_ms)
        self.packet_loss_events.append(not success)
        
        if response_time_ms is not None:
            self.response_times.append(response_time_ms)
        
        self.total_messages_sent += 1
        
        if success:
            self.total_messages_received += 1
            self.consecutive_failures = 0
            self.last_successful_communication = time.time()
        else:
            self.total_failures += 1
            self.consecutive_failures += 1
        
        self.last_update = time.time()
    
    def get_current_latency_ms(self) -> float:
        """Get current average latency."""
        if not self.latency_history:
            return 0.0
        return float(np.mean(list(self.latency_history)))
    
    def get_packet_loss_rate(self) -> float:
        """Get current packet loss rate."""
        if not self.packet_loss_events:
            return 0.0
        return float(np.mean(list(self.packet_loss_events)))
    
    def get_reliability_score(self) -> float:
        """
        Calculate reliability score (0-1).
        
        Returns:
            Reliability score based on success rate
        """
        if self.total_messages_sent == 0:
            return 1.0
        return self.total_messages_received / self.total_messages_sent
    
    def calculate_quality_score(self) -> float:
        """
        Calculate overall connection quality score (0-100).
        
        Combines latency, packet loss, and reliability.
        
        Returns:
            Quality score (higher is better)
        """
        if len(self.latency_history) < 3:
            return 50.0  # Neutral score until we have data
        
        # Latency score (0-40 points)
        avg_latency = self.get_current_latency_ms()
        if avg_latency < 50:
            latency_score = 40
        elif avg_latency < 150:
            latency_score = 40 - (avg_latency - 50) * 0.3
        elif avg_latency < 300:
            latency_score = 10 - (avg_latency - 150) * 0.067
        else:
            latency_score = 0
        
        # Packet loss score (0-30 points)
        packet_loss = self.get_packet_loss_rate()
        packet_loss_score = max(0, 30 * (1 - packet_loss * 10))
        
        # Reliability score (0-30 points)
        reliability = self.get_reliability_score()
        reliability_score = reliability * 30
        
        total_score = latency_score + packet_loss_score + reliability_score
        return max(0, min(100, total_score))
    
    def update_quality_classification(self) -> bool:
        """
        Update quality classification with hysteresis.
        
        Returns:
            bool: True if quality changed
        """
        score = self.calculate_quality_score()
        
        # Determine new quality based on score
        if score >= 80:
            new_quality = ConnectionQuality.EXCELLENT
        elif score >= 60:
            new_quality = ConnectionQuality.GOOD
        elif score >= 40:
            new_quality = ConnectionQuality.FAIR
        elif score >= 20:
            new_quality = ConnectionQuality.POOR
        else:
            new_quality = ConnectionQuality.CRITICAL
        
        # Check for offline (no successful communication recently)
        time_since_success = time.time() - self.last_successful_communication
        if time_since_success > 60:  # 60 seconds threshold
            new_quality = ConnectionQuality.OFFLINE
        
        # Apply hysteresis
        if new_quality == self.current_quality:
            # Reset pending change
            self.pending_quality_change = None
            self.pending_change_count = 0
            return False
        
        # Check if this is a new pending change or continuation
        if new_quality == self.pending_quality_change:
            self.pending_change_count += 1
        else:
            self.pending_quality_change = new_quality
            self.pending_change_count = 1
        
        # Apply change if threshold met
        if self.pending_change_count >= self.quality_change_threshold:
            self.previous_quality = self.current_quality
            self.current_quality = new_quality
            self.quality_changes += 1
            self.pending_quality_change = None
            self.pending_change_count = 0
            
            logger.info(f"[NET MONITOR] Node {self.node_id}: Quality changed "
                       f"{self.previous_quality.value} -> {self.current_quality.value}")
            print(f"[NET MONITOR] Node {self.node_id}: Quality now {self.current_quality.value}")
            
            return True
        
        return False
    
    def get_trend(self) -> str:
        """
        Determine if network quality is improving or degrading.
        
        Returns:
            'improving', 'degrading', or 'stable'
        """
        if len(self.latency_history) < 20:
            return 'insufficient_data'
        
        # Compare recent vs older latencies
        recent = np.mean(list(self.latency_history)[-10:])
        older = np.mean(list(self.latency_history)[-20:-10])
        
        change_ratio = (recent - older) / (older + 1)
        
        if change_ratio < -0.15:  # 15% improvement
            return 'improving'
        elif change_ratio > 0.15:  # 15% degradation
            return 'degrading'
        else:
            return 'stable'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        return {
            'node_id': self.node_id,
            'quality': self.current_quality.value,
            'quality_score': self.calculate_quality_score(),
            'latency_ms': self.get_current_latency_ms(),
            'packet_loss_rate': self.get_packet_loss_rate(),
            'reliability_score': self.get_reliability_score(),
            'trend': self.get_trend(),
            'total_messages': self.total_messages_sent,
            'successful_messages': self.total_messages_received,
            'failed_messages': self.total_failures,
            'consecutive_failures': self.consecutive_failures,
            'quality_changes': self.quality_changes,
            'last_update': self.last_update,
            'time_since_success': time.time() - self.last_successful_communication
        }


class NetworkQualityMonitor:
    """
    Monitors network quality for all nodes in the cluster.
    
    Provides real-time visibility into connection quality, tracks trends,
    and generates alerts for degraded connections.
    """
    
    def __init__(
        self,
        update_interval_seconds: float = 5.0,
        enable_active_monitoring: bool = True
    ):
        """
        Initialize network quality monitor.
        
        Args:
            update_interval_seconds: How often to update quality classifications
            enable_active_monitoring: Whether to send periodic ping messages
        """
        self.update_interval = update_interval_seconds
        self.enable_active_monitoring = enable_active_monitoring
        
        # Connection profiles for each node
        self.profiles: Dict[str, ConnectionProfile] = {}
        
        # Alerts
        self.alerts: List[Dict[str, Any]] = []
        self.max_alerts = 100
        
        # Monitoring thread
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # Thread safety
        self.lock = threading.RLock()
        
        logger.info(f"[NET MONITOR] NetworkQualityMonitor initialized")
        print(f"[NET MONITOR] Network quality monitoring initialized")
    
    def register_node(self, node_id: str):
        """
        Register a node for monitoring.
        
        Args:
            node_id: Node identifier
        """
        with self.lock:
            if node_id not in self.profiles:
                self.profiles[node_id] = ConnectionProfile(node_id)
                logger.info(f"[NET MONITOR] Registered node {node_id}")
                print(f"[NET MONITOR] Monitoring node {node_id}")
    
    def record_communication(
        self,
        node_id: str,
        latency_ms: float,
        success: bool,
        response_time_ms: Optional[float] = None
    ):
        """
        Record a communication event with a node.
        
        Args:
            node_id: Node identifier
            latency_ms: Latency in milliseconds
            success: Whether communication succeeded
            response_time_ms: Round-trip time in milliseconds
        """
        with self.lock:
            if node_id not in self.profiles:
                self.register_node(node_id)
            
            self.profiles[node_id].record_communication(
                latency_ms, success, response_time_ms
            )
            
            # Update quality classification
            quality_changed = self.profiles[node_id].update_quality_classification()
            
            if quality_changed:
                self._generate_quality_change_alert(node_id)
    
    def get_node_quality(self, node_id: str) -> ConnectionQuality:
        """
        Get current connection quality for a node.
        
        Args:
            node_id: Node identifier
            
        Returns:
            ConnectionQuality enum value
        """
        with self.lock:
            if node_id not in self.profiles:
                return ConnectionQuality.OFFLINE
            return self.profiles[node_id].current_quality
    
    def get_node_profile(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full profile for a node.
        
        Args:
            node_id: Node identifier
            
        Returns:
            Dictionary with profile data or None
        """
        with self.lock:
            if node_id not in self.profiles:
                return None
            return self.profiles[node_id].to_dict()
    
    def get_all_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Get profiles for all nodes."""
        with self.lock:
            return {
                node_id: profile.to_dict()
                for node_id, profile in self.profiles.items()
            }
    
    def get_nodes_by_quality(
        self,
        min_quality: Optional[ConnectionQuality] = None,
        max_quality: Optional[ConnectionQuality] = None
    ) -> List[str]:
        """
        Get list of nodes filtered by quality.
        
        Args:
            min_quality: Minimum quality threshold (inclusive)
            max_quality: Maximum quality threshold (inclusive)
            
        Returns:
            List of node IDs matching criteria
        """
        quality_order = [
            ConnectionQuality.OFFLINE,
            ConnectionQuality.CRITICAL,
            ConnectionQuality.POOR,
            ConnectionQuality.FAIR,
            ConnectionQuality.GOOD,
            ConnectionQuality.EXCELLENT
        ]
        
        with self.lock:
            matching_nodes = []
            
            for node_id, profile in self.profiles.items():
                quality = profile.current_quality
                quality_idx = quality_order.index(quality)
                
                if min_quality is not None:
                    min_idx = quality_order.index(min_quality)
                    if quality_idx < min_idx:
                        continue
                
                if max_quality is not None:
                    max_idx = quality_order.index(max_quality)
                    if quality_idx > max_idx:
                        continue
                
                matching_nodes.append(node_id)
            
            return matching_nodes
    
    def get_problematic_nodes(self) -> List[str]:
        """Get list of nodes with poor or critical connection quality."""
        return self.get_nodes_by_quality(
            max_quality=ConnectionQuality.POOR
        )
    
    def get_reliable_nodes(self) -> List[str]:
        """Get list of nodes with good or excellent connection quality."""
        return self.get_nodes_by_quality(
            min_quality=ConnectionQuality.GOOD
        )
    
    def _generate_quality_change_alert(self, node_id: str):
        """Generate an alert for quality change."""
        profile = self.profiles[node_id]
        
        alert = {
            'type': 'quality_change',
            'node_id': node_id,
            'old_quality': profile.previous_quality.value,
            'new_quality': profile.current_quality.value,
            'timestamp': time.time(),
            'severity': self._determine_alert_severity(profile.current_quality)
        }
        
        self.alerts.append(alert)
        
        # Keep only recent alerts
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts:]
        
        logger.warning(f"[NET MONITOR] Alert: Node {node_id} quality "
                      f"{profile.previous_quality.value} -> {profile.current_quality.value}")
    
    def _determine_alert_severity(self, quality: ConnectionQuality) -> str:
        """Determine alert severity based on quality."""
        if quality in [ConnectionQuality.CRITICAL, ConnectionQuality.OFFLINE]:
            return 'high'
        elif quality == ConnectionQuality.POOR:
            return 'medium'
        else:
            return 'low'
    
    def get_alerts(
        self,
        since_timestamp: Optional[float] = None,
        severity: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get alerts filtered by timestamp and/or severity.
        
        Args:
            since_timestamp: Only return alerts after this timestamp
            severity: Filter by severity ('low', 'medium', 'high')
            
        Returns:
            List of alert dictionaries
        """
        with self.lock:
            filtered_alerts = self.alerts.copy()
            
            if since_timestamp is not None:
                filtered_alerts = [
                    a for a in filtered_alerts if a['timestamp'] >= since_timestamp
                ]
            
            if severity is not None:
                filtered_alerts = [
                    a for a in filtered_alerts if a['severity'] == severity
                ]
            
            return filtered_alerts
    
    def get_cluster_health_summary(self) -> Dict[str, Any]:
        """
        Get overall cluster network health summary.
        
        Returns:
            Dictionary with cluster health metrics
        """
        with self.lock:
            if not self.profiles:
                return {
                    'total_nodes': 0,
                    'healthy_nodes': 0,
                    'problematic_nodes': 0,
                    'average_latency_ms': 0.0,
                    'average_reliability': 0.0,
                    'quality_distribution': {q.value: 0 for q in ConnectionQuality},
                    'recent_alerts': 0,
                    'message': 'No nodes registered'
                }
            
            quality_counts = {q.value: 0 for q in ConnectionQuality}
            total_latency = 0.0
            total_reliability = 0.0
            
            for profile in self.profiles.values():
                quality_counts[profile.current_quality.value] += 1
                total_latency += profile.get_current_latency_ms()
                total_reliability += profile.get_reliability_score()
            
            num_nodes = len(self.profiles)
            
            return {
                'total_nodes': num_nodes,
                'quality_distribution': quality_counts,
                'average_latency_ms': total_latency / num_nodes,
                'average_reliability': total_reliability / num_nodes,
                'healthy_nodes': (
                    quality_counts[ConnectionQuality.EXCELLENT.value] +
                    quality_counts[ConnectionQuality.GOOD.value]
                ),
                'problematic_nodes': (
                    quality_counts[ConnectionQuality.POOR.value] +
                    quality_counts[ConnectionQuality.CRITICAL.value] +
                    quality_counts[ConnectionQuality.OFFLINE.value]
                ),
                'recent_alerts': len([
                    a for a in self.alerts
                    if time.time() - a['timestamp'] < 300  # Last 5 minutes
                ])
            }
    
    def start_monitoring(self):
        """Start background monitoring thread."""
        if self.monitoring_active:
            logger.warning("[NET MONITOR] Monitoring already active")
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("[NET MONITOR] Background monitoring started")
        print("[NET MONITOR] Background monitoring started")
    
    def stop_monitoring(self):
        """Stop background monitoring thread."""
        self.monitoring_active = False
        
        if self.monitor_thread is not None:
            self.monitor_thread.join(timeout=5.0)
        
        logger.info("[NET MONITOR] Background monitoring stopped")
        print("[NET MONITOR] Background monitoring stopped")
    
    def _monitoring_loop(self):
        """Background monitoring loop."""
        while self.monitoring_active:
            try:
                # Update all quality classifications
                with self.lock:
                    for node_id, profile in self.profiles.items():
                        profile.update_quality_classification()
                
                # Log cluster health periodically
                health = self.get_cluster_health_summary()
                logger.debug(f"[NET MONITOR] Cluster health: {health['healthy_nodes']}/{health['total_nodes']} healthy")
                
                time.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"[NET MONITOR] Error in monitoring loop: {e}")
    
    def export_metrics(self) -> Dict[str, Any]:
        """
        Export all monitoring metrics for visualization/storage.
        
        Returns:
            Dictionary with complete monitoring data
        """
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'cluster_health': self.get_cluster_health_summary(),
            'node_profiles': self.get_all_profiles(),
            'recent_alerts': self.get_alerts(
                since_timestamp=time.time() - 3600  # Last hour
            )
        }
