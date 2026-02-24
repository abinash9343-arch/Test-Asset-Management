"""Health check system for IT Agent"""
import psutil
import time
import socket
from typing import Dict, Any, List, Optional
from datetime import datetime

class HealthCheck:
    """System health monitoring"""
    
    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.checks = []
    
    def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            # Windows compatibility for disk check
            import os
            disk_path = 'C:\\' if os.name == 'nt' else '/'
            disk = psutil.disk_usage(disk_path)
            
            return {
                'status': 'healthy' if cpu_percent < 80 and memory.percent < 80 else 'degraded',
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_mb': memory.available / (1024 * 1024),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / (1024 * 1024 * 1024),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def check_network_connectivity(self, host: str = "8.8.8.8", port: int = 53) -> Dict[str, Any]:
        """Check network connectivity"""
        try:
            socket.setdefaulttimeout(self.timeout)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex((host, port))
            sock.close()
            
            return {
                'status': 'healthy' if result == 0 else 'unreachable',
                'host': host,
                'port': port,
                'reachable': result == 0,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def check_service_health(self, service_name: str) -> Dict[str, Any]:
        """Check if a service is running"""
        try:
            # Check if process is running (simplified)
            running = False
            for proc in psutil.process_iter(['pid', 'name']):
                if service_name.lower() in proc.info['name'].lower():
                    running = True
                    break
            
            return {
                'status': 'healthy' if running else 'stopped',
                'service': service_name,
                'running': running,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def comprehensive_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        results = {
            'overall_status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'checks': {}
        }
        
        # System resources
        results['checks']['system_resources'] = self.check_system_resources()
        
        # Network connectivity
        results['checks']['network'] = self.check_network_connectivity()
        
        # Determine overall status
        for check in results['checks'].values():
            if check.get('status') == 'error':
                results['overall_status'] = 'error'
                break
            elif check.get('status') in ['degraded', 'unreachable', 'stopped']:
                results['overall_status'] = 'degraded'
        
        return results

