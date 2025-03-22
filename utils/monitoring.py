import psutil
import platform
import subprocess
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from .logger import logger

class SystemMonitor:
    def __init__(self):
        """Initialize the system monitor"""
        self.history: List[Dict[str, Any]] = []
        self.max_history_size = 1000
        self.metrics_file = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'logs', 
            'metrics.json'
        )
        
    def get_cpu_info(self) -> Dict[str, Any]:
        """Get CPU information"""
        cpu_freq = psutil.cpu_freq()
        return {
            "percent": psutil.cpu_percent(interval=1),
            "count": psutil.cpu_count(),
            "freq_current": cpu_freq.current if cpu_freq else 0,
            "freq_min": cpu_freq.min if cpu_freq else 0,
            "freq_max": cpu_freq.max if cpu_freq else 0
        }
        
    def get_memory_info(self) -> Dict[str, Any]:
        """Get memory information"""
        mem = psutil.virtual_memory()
        return {
            "total": mem.total / (1024**3),  # GB
            "available": mem.available / (1024**3),  # GB
            "percent": mem.percent,
            "used": mem.used / (1024**3)  # GB
        }
        
    def get_disk_info(self) -> Dict[str, Any]:
        """Get disk information"""
        disk = psutil.disk_usage('/')
        return {
            "total": disk.total / (1024**3),  # GB
            "used": disk.used / (1024**3),  # GB
            "free": disk.free / (1024**3),  # GB
            "percent": disk.percent
        }
        
    def get_temperature(self) -> float:
        """Get CPU temperature"""
        if platform.system() == "Darwin":
            try:
                cmd = ["sudo", "powermetrics", "--samplers", "smc", "-n1"]
                output = subprocess.check_output(cmd, text=True)
                temp_line = [line for line in output.split('\n') 
                           if "CPU die temperature" in line]
                if temp_line:
                    return float(temp_line[0].split(':')[1].split()[0])
            except Exception as e:
                logger.error(f"Error reading temperature: {e}")
        return 0.0
        
    def get_gpu_info(self) -> Optional[Dict[str, Any]]:
        """Get GPU information if available"""
        if platform.system() == "Darwin":
            try:
                cmd = ["system_profiler", "SPDisplaysDataType"]
                output = subprocess.check_output(cmd, text=True)
                return {
                    "available": "AMD Radeon" in output,
                    "model": "AMD Radeon Pro" if "AMD Radeon" in output else "Intel UHD"
                }
            except Exception as e:
                logger.error(f"Error reading GPU info: {e}")
        return None
        
    def collect_metrics(self) -> Dict[str, Any]:
        """Collect all system metrics"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "cpu": self.get_cpu_info(),
            "memory": self.get_memory_info(),
            "disk": self.get_disk_info(),
            "temperature": self.get_temperature(),
            "gpu": self.get_gpu_info()
        }
        
        # Add to history
        self.history.append(metrics)
        if len(self.history) > self.max_history_size:
            self.history.pop(0)
            
        return metrics
        
    def save_metrics(self):
        """Save metrics to a JSON file"""
        try:
            # Load existing metrics
            existing_metrics = []
            if os.path.exists(self.metrics_file):
                with open(self.metrics_file, 'r') as f:
                    existing_metrics = json.load(f)
                    
            # Add new metrics
            existing_metrics.extend(self.history)
            
            # Limit file size
            if len(existing_metrics) > self.max_history_size:
                existing_metrics = existing_metrics[-self.max_history_size:]
                
            # Save
            with open(self.metrics_file, 'w') as f:
                json.dump(existing_metrics, f)
                
            # Clear local history
            self.history = []
            
            logger.info("Metrics saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
            
    def get_system_health(self) -> Dict[str, str]:
        """Evaluate system health status"""
        metrics = self.collect_metrics()
        
        health = {}
        
        # CPU
        cpu_percent = metrics["cpu"]["percent"]
        if cpu_percent > 90:
            health["cpu"] = "critical"
        elif cpu_percent > 70:
            health["cpu"] = "warning"
        else:
            health["cpu"] = "good"
            
        # Memory
        mem_percent = metrics["memory"]["percent"]
        if mem_percent > 90:
            health["memory"] = "critical"
        elif mem_percent > 70:
            health["memory"] = "warning"
        else:
            health["memory"] = "good"
            
        # Temperature
        temp = metrics["temperature"]
        if temp > 90:
            health["temperature"] = "critical"
        elif temp > 70:
            health["temperature"] = "warning"
        else:
            health["temperature"] = "good"
            
        return health

    def get_system_info(self):
        """
        Get system information
        
        Returns:
            dict: System information including CPU count, memory, disk space,
                  platform and Python version
        """
        return {
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total,
            'disk_total': psutil.disk_usage('/').total,
            'platform': platform.system(),
            'python_version': platform.python_version()
        }

# Global monitor instance
monitor = SystemMonitor()