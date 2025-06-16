"""
System Monitor - Track system resources and performance metrics.
"""

import time
import psutil
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """System metrics data class."""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_percent: float
    network_sent_mb: float
    network_recv_mb: float
    gpu_percent: Optional[float] = None
    gpu_memory_percent: Optional[float] = None
    gpu_memory_used_mb: Optional[float] = None
    process_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp,
            'cpu_percent': self.cpu_percent,
            'memory_percent': self.memory_percent,
            'memory_used_mb': self.memory_used_mb,
            'memory_available_mb': self.memory_available_mb,
            'disk_percent': self.disk_percent,
            'network_sent_mb': self.network_sent_mb,
            'network_recv_mb': self.network_recv_mb,
            'gpu_percent': self.gpu_percent,
            'gpu_memory_percent': self.gpu_memory_percent,
            'gpu_memory_used_mb': self.gpu_memory_used_mb,
            'process_count': self.process_count
        }


class SystemMonitor:
    """
    System Monitor - Track system resources and performance.
    
    Features:
    - CPU usage monitoring
    - Memory usage tracking
    - Disk usage monitoring
    - Network statistics
    - GPU monitoring (if available)
    - Process tracking
    - Historical data collection
    """
    
    def __init__(self, history_size: int = 100):
        """Initialize system monitor."""
        self.history_size = history_size
        self.metrics_history: List[SystemMetrics] = []
        self.start_time = time.time()
        
        # Cache for expensive operations
        self._last_network_stats = None
        self._last_network_time = 0
        
        # GPU detection
        self.has_gpu = self._detect_gpu()
        
        logger.info("System monitor initialized")
    
    def _detect_gpu(self) -> bool:
        """Detect if GPU monitoring is available."""
        try:
            import subprocess
            result = subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        try:
            current_time = time.time()
            
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)
            memory_available_mb = memory.available / (1024 * 1024)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Network metrics
            network_sent_mb, network_recv_mb = self._get_network_stats()
            
            # Process count
            process_count = len(psutil.pids())
            
            # GPU metrics (if available)
            gpu_percent = None
            gpu_memory_percent = None
            gpu_memory_used_mb = None
            
            if self.has_gpu:
                gpu_stats = self._get_gpu_stats()
                if gpu_stats:
                    gpu_percent = gpu_stats.get('utilization')
                    gpu_memory_percent = gpu_stats.get('memory_percent')
                    gpu_memory_used_mb = gpu_stats.get('memory_used_mb')
            
            # Create metrics object
            metrics = SystemMetrics(
                timestamp=current_time,
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                memory_available_mb=memory_available_mb,
                disk_percent=disk_percent,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb,
                gpu_percent=gpu_percent,
                gpu_memory_percent=gpu_memory_percent,
                gpu_memory_used_mb=gpu_memory_used_mb,
                process_count=process_count
            )
            
            # Add to history
            self._add_to_history(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            # Return default metrics on error
            return SystemMetrics(
                timestamp=time.time(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                memory_available_mb=0.0,
                disk_percent=0.0,
                network_sent_mb=0.0,
                network_recv_mb=0.0
            )
    
    def _get_network_stats(self) -> tuple:
        """Get network statistics."""
        try:
            current_time = time.time()
            
            # Use cached values if called too frequently
            if current_time - self._last_network_time < 1.0:
                return (0.0, 0.0)
            
            net_io = psutil.net_io_counters()
            if net_io:
                sent_mb = net_io.bytes_sent / (1024 * 1024)
                recv_mb = net_io.bytes_recv / (1024 * 1024)
                
                self._last_network_time = current_time
                return (sent_mb, recv_mb)
            
            return (0.0, 0.0)
            
        except Exception as e:
            logger.error(f"Error getting network stats: {e}")
            return (0.0, 0.0)
    
    def _get_gpu_stats(self) -> Optional[Dict[str, float]]:
        """Get GPU statistics using nvidia-smi."""
        try:
            import subprocess
            
            # Query GPU utilization and memory
            result = subprocess.run([
                'nvidia-smi', 
                '--query-gpu=utilization.gpu,memory.used,memory.total',
                '--format=csv,noheader,nounits'
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                values = result.stdout.strip().split(',')
                if len(values) >= 3:
                    utilization = float(values[0].strip())
                    memory_used = float(values[1].strip())
                    memory_total = float(values[2].strip())
                    memory_percent = (memory_used / memory_total) * 100
                    
                    return {
                        'utilization': utilization,
                        'memory_used_mb': memory_used,
                        'memory_total_mb': memory_total,
                        'memory_percent': memory_percent
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting GPU stats: {e}")
            return None
    
    def _add_to_history(self, metrics: SystemMetrics):
        """Add metrics to history and maintain size limit."""
        self.metrics_history.append(metrics)
        
        # Maintain history size limit
        if len(self.metrics_history) > self.history_size:
            self.metrics_history.pop(0)
    
    def get_current_metrics(self) -> SystemMetrics:
        """Get the most recent metrics."""
        if self.metrics_history:
            return self.metrics_history[-1]
        else:
            return self.collect_metrics()
    
    def get_average_metrics(self, duration_minutes: int = 5) -> Optional[SystemMetrics]:
        """Get average metrics over specified duration."""
        if not self.metrics_history:
            return None
        
        # Filter metrics within duration
        cutoff_time = time.time() - (duration_minutes * 60)
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return None
        
        # Calculate averages
        count = len(recent_metrics)
        avg_metrics = SystemMetrics(
            timestamp=time.time(),
            cpu_percent=sum(m.cpu_percent for m in recent_metrics) / count,
            memory_percent=sum(m.memory_percent for m in recent_metrics) / count,
            memory_used_mb=sum(m.memory_used_mb for m in recent_metrics) / count,
            memory_available_mb=sum(m.memory_available_mb for m in recent_metrics) / count,
            disk_percent=sum(m.disk_percent for m in recent_metrics) / count,
            network_sent_mb=sum(m.network_sent_mb for m in recent_metrics) / count,
            network_recv_mb=sum(m.network_recv_mb for m in recent_metrics) / count,
            process_count=int(sum(m.process_count for m in recent_metrics) / count)
        )
        
        # GPU averages (if available)
        gpu_metrics = [m for m in recent_metrics if m.gpu_percent is not None]
        if gpu_metrics:
            gpu_count = len(gpu_metrics)
            avg_metrics.gpu_percent = sum(m.gpu_percent for m in gpu_metrics) / gpu_count
            avg_metrics.gpu_memory_percent = sum(m.gpu_memory_percent for m in gpu_metrics) / gpu_count
            avg_metrics.gpu_memory_used_mb = sum(m.gpu_memory_used_mb for m in gpu_metrics) / gpu_count
        
        return avg_metrics
    
    def get_system_health(self) -> Dict[str, str]:
        """Get system health status."""
        current = self.get_current_metrics()
        
        health = {
            'cpu': 'Normal',
            'memory': 'Normal', 
            'disk': 'Normal',
            'overall': 'Healthy'
        }
        
        # CPU health
        if current.cpu_percent > 90:
            health['cpu'] = 'Critical'
            health['overall'] = 'Warning'
        elif current.cpu_percent > 70:
            health['cpu'] = 'High'
        
        # Memory health
        if current.memory_percent > 90:
            health['memory'] = 'Critical'
            health['overall'] = 'Warning'
        elif current.memory_percent > 80:
            health['memory'] = 'High'
        
        # Disk health
        if current.disk_percent > 95:
            health['disk'] = 'Critical'
            health['overall'] = 'Critical'
        elif current.disk_percent > 85:
            health['disk'] = 'High'
        
        # GPU health (if available)
        if current.gpu_percent is not None:
            health['gpu'] = 'Normal'
            if current.gpu_percent > 90:
                health['gpu'] = 'High'
            elif current.gpu_memory_percent and current.gpu_memory_percent > 90:
                health['gpu'] = 'High'
        
        return health
    
    def get_uptime(self) -> str:
        """Get system uptime formatted string."""
        uptime_seconds = time.time() - self.start_time
        
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        seconds = int(uptime_seconds % 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        else:
            return f"{minutes}m {seconds}s"
    
    def export_metrics(self, filepath: str, format: str = 'json'):
        """Export metrics history to file."""
        try:
            if format.lower() == 'json':
                import json
                data = [m.to_dict() for m in self.metrics_history]
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)
            elif format.lower() == 'csv':
                import csv
                if self.metrics_history:
                    with open(filepath, 'w', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=self.metrics_history[0].to_dict().keys())
                        writer.writeheader()
                        for metrics in self.metrics_history:
                            writer.writerow(metrics.to_dict())
            
            logger.info(f"Metrics exported to {filepath}")
            
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}") 