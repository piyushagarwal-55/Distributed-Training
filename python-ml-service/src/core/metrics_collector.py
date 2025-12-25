"""
Node Metrics Collector - Comprehensive metrics collection and reporting from GPU nodes.

This module provides detailed metrics collection for training performance,
compute time, network quality, and contribution tracking.
"""

import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import deque
import numpy as np
from dataclasses import dataclass, asdict
import json

from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class StepMetrics:
    """Metrics for a single training step."""
    step: int
    loss: float
    gradient_norm: float
    step_time: float
    forward_time: float
    backward_time: float
    batch_size: int
    timestamp: float


@dataclass
class NetworkMetrics:
    """Network performance metrics."""
    latency_ms: float
    success: bool
    retries: int
    timestamp: float


@dataclass
class ResourceMetrics:
    """Resource utilization metrics."""
    gpu_utilization: float  # Simulated
    memory_used_mb: float  # Simulated
    timestamp: float


class MetricsCollector:
    """
    Comprehensive metrics collection for a GPU node.
    
    Tracks training metrics, performance metrics, network metrics,
    resource utilization, and contribution metrics.
    """
    
    def __init__(self, node_id: str, history_size: int = 100):
        """
        Initialize metrics collector.
        
        Args:
            node_id: Unique node identifier
            history_size: Number of recent entries to keep in rolling buffers
        """
        self.node_id = node_id
        self.history_size = history_size
        
        # Training metrics
        self.step_metrics: deque[StepMetrics] = deque(maxlen=history_size)
        
        # Network metrics
        self.network_metrics: deque[NetworkMetrics] = deque(maxlen=history_size)
        
        # Resource metrics
        self.resource_metrics: deque[ResourceMetrics] = deque(maxlen=history_size)
        
        # Cumulative counters
        self.total_steps = 0
        self.total_compute_time = 0.0
        self.total_communication_time = 0.0
        self.successful_communications = 0
        self.failed_communications = 0
        self.total_gradients_submitted = 0
        
        # Session info
        self.session_start_time = time.time()
        self.last_report_time = time.time()
        
        logger.info(f"[METRICS {node_id}] MetricsCollector initialized with history size {history_size}")
        print(f"[METRICS {node_id}] Metrics collector initialized")
    
    def record_training_step(
        self,
        step: int,
        loss: float,
        gradient_norm: float,
        step_time: float,
        forward_time: float,
        backward_time: float,
        batch_size: int
    ):
        """
        Record metrics from a training step.
        
        Args:
            step: Step number
            loss: Training loss
            gradient_norm: L2 norm of gradients
            step_time: Total step time in seconds
            forward_time: Forward pass time in seconds
            backward_time: Backward pass time in seconds
            batch_size: Batch size used
        """
        metrics = StepMetrics(
            step=step,
            loss=loss,
            gradient_norm=gradient_norm,
            step_time=step_time,
            forward_time=forward_time,
            backward_time=backward_time,
            batch_size=batch_size,
            timestamp=time.time()
        )
        
        self.step_metrics.append(metrics)
        self.total_steps += 1
        self.total_compute_time += step_time
        
        logger.debug(f"[METRICS {self.node_id}] Step {step}: loss={loss:.4f}, "
                    f"grad_norm={gradient_norm:.4f}, time={step_time:.3f}s")
    
    def record_network_event(
        self,
        latency_ms: float,
        success: bool,
        retries: int = 0
    ):
        """
        Record a network communication event.
        
        Args:
            latency_ms: Latency in milliseconds
            success: Whether communication succeeded
            retries: Number of retry attempts
        """
        metrics = NetworkMetrics(
            latency_ms=latency_ms,
            success=success,
            retries=retries,
            timestamp=time.time()
        )
        
        self.network_metrics.append(metrics)
        self.total_communication_time += (latency_ms / 1000.0)
        
        if success:
            self.successful_communications += 1
            self.total_gradients_submitted += 1
        else:
            self.failed_communications += 1
        
        logger.debug(f"[METRICS {self.node_id}] Network: latency={latency_ms:.1f}ms, "
                    f"success={success}, retries={retries}")
    
    def record_resource_usage(
        self,
        gpu_utilization: float,
        memory_used_mb: float
    ):
        """
        Record resource utilization metrics.
        
        Args:
            gpu_utilization: GPU utilization percentage (0-100)
            memory_used_mb: Memory used in MB
        """
        metrics = ResourceMetrics(
            gpu_utilization=gpu_utilization,
            memory_used_mb=memory_used_mb,
            timestamp=time.time()
        )
        
        self.resource_metrics.append(metrics)
        
        logger.debug(f"[METRICS {self.node_id}] Resources: GPU={gpu_utilization:.1f}%, "
                    f"Memory={memory_used_mb:.1f}MB")
    
    def get_training_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics of training metrics.
        
        Returns:
            Dictionary with training metric summaries
        """
        if not self.step_metrics:
            return {
                'available': False,
                'message': 'No training metrics collected yet'
            }
        
        losses = [m.loss for m in self.step_metrics]
        gradient_norms = [m.gradient_norm for m in self.step_metrics]
        step_times = [m.step_time for m in self.step_metrics]
        forward_times = [m.forward_time for m in self.step_metrics]
        backward_times = [m.backward_time for m in self.step_metrics]
        
        return {
            'available': True,
            'loss': {
                'current': losses[-1],
                'mean': float(np.mean(losses)),
                'std': float(np.std(losses)),
                'min': float(np.min(losses)),
                'max': float(np.max(losses)),
                'trend': self._calculate_trend(losses),
                'recent_history': losses[-10:]
            },
            'gradient_norm': {
                'current': gradient_norms[-1],
                'mean': float(np.mean(gradient_norms)),
                'std': float(np.std(gradient_norms)),
                'min': float(np.min(gradient_norms)),
                'max': float(np.max(gradient_norms))
            },
            'timing': {
                'step_time': {
                    'mean': float(np.mean(step_times)),
                    'std': float(np.std(step_times)),
                    'min': float(np.min(step_times)),
                    'max': float(np.max(step_times))
                },
                'forward_time': {
                    'mean': float(np.mean(forward_times)),
                    'std': float(np.std(forward_times))
                },
                'backward_time': {
                    'mean': float(np.mean(backward_times)),
                    'std': float(np.std(backward_times))
                },
                'throughput_samples_per_sec': self._calculate_throughput()
            },
            'steps_recorded': len(self.step_metrics),
            'total_steps': self.total_steps
        }
    
    def get_network_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics of network metrics.
        
        Returns:
            Dictionary with network metric summaries
        """
        if not self.network_metrics:
            return {
                'available': False,
                'message': 'No network metrics collected yet'
            }
        
        latencies = [m.latency_ms for m in self.network_metrics]
        successes = [m.success for m in self.network_metrics]
        retries = [m.retries for m in self.network_metrics]
        
        return {
            'available': True,
            'latency_ms': {
                'current': latencies[-1],
                'mean': float(np.mean(latencies)),
                'std': float(np.std(latencies)),
                'min': float(np.min(latencies)),
                'max': float(np.max(latencies)),
                'median': float(np.median(latencies)),
                'p95': float(np.percentile(latencies, 95)),
                'p99': float(np.percentile(latencies, 99))
            },
            'reliability': {
                'success_rate': float(np.mean(successes)),
                'successful_communications': self.successful_communications,
                'failed_communications': self.failed_communications,
                'total_communications': (
                    self.successful_communications + self.failed_communications
                ),
                'average_retries': float(np.mean(retries)) if retries else 0.0
            },
            'events_recorded': len(self.network_metrics)
        }
    
    def get_resource_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics of resource utilization.
        
        Returns:
            Dictionary with resource metric summaries
        """
        if not self.resource_metrics:
            return {
                'available': False,
                'message': 'No resource metrics collected yet'
            }
        
        gpu_utils = [m.gpu_utilization for m in self.resource_metrics]
        memory_used = [m.memory_used_mb for m in self.resource_metrics]
        
        return {
            'available': True,
            'gpu_utilization': {
                'current': gpu_utils[-1],
                'mean': float(np.mean(gpu_utils)),
                'std': float(np.std(gpu_utils)),
                'min': float(np.min(gpu_utils)),
                'max': float(np.max(gpu_utils))
            },
            'memory_usage_mb': {
                'current': memory_used[-1],
                'mean': float(np.mean(memory_used)),
                'std': float(np.std(memory_used)),
                'min': float(np.min(memory_used)),
                'max': float(np.max(memory_used))
            },
            'samples_recorded': len(self.resource_metrics)
        }
    
    def get_contribution_metrics(self) -> Dict[str, Any]:
        """
        Get contribution-related metrics for reward calculation.
        
        Returns:
            Dictionary with contribution metrics
        """
        session_duration = time.time() - self.session_start_time
        
        # Calculate effective contribution (compute time vs total time)
        total_time = self.total_compute_time + self.total_communication_time
        compute_efficiency = (
            self.total_compute_time / total_time if total_time > 0 else 0.0
        )
        
        # Calculate reliability score
        total_comms = self.successful_communications + self.failed_communications
        reliability_score = (
            self.successful_communications / total_comms if total_comms > 0 else 0.0
        )
        
        # Calculate contribution score (weighted combination)
        contribution_score = (
            0.6 * compute_efficiency +  # 60% weight on compute efficiency
            0.3 * reliability_score +     # 30% weight on reliability
            0.1 * min(1.0, self.total_steps / 1000.0)  # 10% weight on participation
        )
        
        return {
            'total_compute_time': self.total_compute_time,
            'total_communication_time': self.total_communication_time,
            'compute_efficiency': compute_efficiency,
            'reliability_score': reliability_score,
            'contribution_score': contribution_score,
            'total_gradients_submitted': self.total_gradients_submitted,
            'successful_submissions': self.successful_communications,
            'session_duration': session_duration,
            'average_step_time': (
                self.total_compute_time / self.total_steps
                if self.total_steps > 0 else 0.0
            )
        }
    
    def get_full_report(self) -> Dict[str, Any]:
        """
        Get comprehensive metrics report.
        
        Returns:
            Dictionary with all metrics
        """
        return {
            'node_id': self.node_id,
            'timestamp': datetime.utcnow().isoformat(),
            'session_info': {
                'session_start': datetime.fromtimestamp(self.session_start_time).isoformat(),
                'session_duration_seconds': time.time() - self.session_start_time,
                'total_steps': self.total_steps
            },
            'training': self.get_training_summary(),
            'network': self.get_network_summary(),
            'resources': self.get_resource_summary(),
            'contribution': self.get_contribution_metrics()
        }
    
    def get_compact_report(self) -> Dict[str, Any]:
        """
        Get compact metrics report for periodic transmission.
        
        Returns:
            Dictionary with summarized metrics (smaller size)
        """
        training = self.get_training_summary()
        network = self.get_network_summary()
        contribution = self.get_contribution_metrics()
        
        return {
            'node_id': self.node_id,
            'timestamp': time.time(),
            'loss_current': training.get('loss', {}).get('current', 0.0) if training.get('available') else 0.0,
            'loss_mean': training.get('loss', {}).get('mean', 0.0) if training.get('available') else 0.0,
            'latency_mean_ms': network.get('latency_ms', {}).get('mean', 0.0) if network.get('available') else 0.0,
            'success_rate': network.get('reliability', {}).get('success_rate', 0.0) if network.get('available') else 0.0,
            'compute_time': contribution['total_compute_time'],
            'steps': self.total_steps,
            'gradients_submitted': self.total_gradients_submitted
        }
    
    def serialize_to_json(self) -> str:
        """
        Serialize full report to JSON string.
        
        Returns:
            JSON string of metrics report
        """
        report = self.get_full_report()
        return json.dumps(report, indent=2)
    
    def _calculate_trend(self, values: List[float]) -> str:
        """
        Calculate trend direction for a metric.
        
        Args:
            values: List of metric values (time-ordered)
            
        Returns:
            'improving', 'degrading', or 'stable'
        """
        if len(values) < 10:
            return 'insufficient_data'
        
        # Compare recent vs older values
        recent = np.mean(values[-10:])
        older = np.mean(values[-20:-10]) if len(values) >= 20 else np.mean(values[:-10])
        
        # For loss, lower is better
        change_ratio = (recent - older) / (older + 1e-8)
        
        if change_ratio < -0.05:  # 5% improvement
            return 'improving'
        elif change_ratio > 0.05:  # 5% degradation
            return 'degrading'
        else:
            return 'stable'
    
    def _calculate_throughput(self) -> float:
        """
        Calculate training throughput in samples per second.
        
        Returns:
            Samples per second
        """
        if not self.step_metrics or len(self.step_metrics) < 2:
            return 0.0
        
        # Use recent metrics for throughput calculation
        recent_metrics = list(self.step_metrics)[-20:]
        
        total_samples = sum(m.batch_size for m in recent_metrics)
        total_time = sum(m.step_time for m in recent_metrics)
        
        if total_time > 0:
            return total_samples / total_time
        return 0.0
    
    def detect_anomalies(self) -> List[Dict[str, Any]]:
        """
        Detect anomalous conditions in metrics.
        
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        # Check training metrics
        training = self.get_training_summary()
        if training.get('available'):
            loss_data = training['loss']
            
            # Sudden loss increase
            if len(self.step_metrics) >= 10:
                recent_loss = loss_data['current']
                mean_loss = loss_data['mean']
                std_loss = loss_data['std']
                
                if recent_loss > mean_loss + 3 * std_loss:
                    anomalies.append({
                        'type': 'loss_spike',
                        'severity': 'high',
                        'message': f'Loss spiked to {recent_loss:.4f} (mean: {mean_loss:.4f})',
                        'timestamp': time.time()
                    })
            
            # Loss not decreasing
            if loss_data.get('trend') == 'degrading' and self.total_steps > 50:
                anomalies.append({
                    'type': 'loss_not_improving',
                    'severity': 'medium',
                    'message': 'Loss trend is degrading',
                    'timestamp': time.time()
                })
        
        # Check network metrics
        network = self.get_network_summary()
        if network.get('available'):
            reliability = network['reliability']
            
            # Low success rate
            if reliability['success_rate'] < 0.8:
                anomalies.append({
                    'type': 'low_network_reliability',
                    'severity': 'high',
                    'message': f'Network success rate: {reliability["success_rate"]:.2%}',
                    'timestamp': time.time()
                })
            
            # High latency
            latency = network['latency_ms']
            if latency['mean'] > 500:  # >500ms is concerning
                anomalies.append({
                    'type': 'high_latency',
                    'severity': 'medium',
                    'message': f'Average latency: {latency["mean"]:.1f}ms',
                    'timestamp': time.time()
                })
        
        if anomalies:
            logger.warning(f"[METRICS {self.node_id}] Detected {len(anomalies)} anomalies")
            for anomaly in anomalies:
                print(f"[METRICS {self.node_id}] ⚠ Anomaly: {anomaly['message']}")
        
        return anomalies
    
    def reset(self):
        """Reset all metrics."""
        self.step_metrics.clear()
        self.network_metrics.clear()
        self.resource_metrics.clear()
        
        self.total_steps = 0
        self.total_compute_time = 0.0
        self.total_communication_time = 0.0
        self.successful_communications = 0
        self.failed_communications = 0
        self.total_gradients_submitted = 0
        
        self.session_start_time = time.time()
        self.last_report_time = time.time()
        
        logger.info(f"[METRICS {self.node_id}] Metrics reset")
