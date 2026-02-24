"""IT Agent task definitions"""
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

class Task(ABC):
    """Base class for IT Agent tasks"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.status = "pending"
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the task"""
        pass
    
    def validate(self, **kwargs) -> bool:
        """Validate task parameters"""
        return True

class SystemInfoTask(Task):
    """Task to gather system information"""
    
    def __init__(self):
        super().__init__("system_info", "Gather system information")
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute system info gathering"""
        import platform
        import psutil
        
        try:
            self.status = "running"
            info = {
                'platform': platform.system(),
                'platform_version': platform.version(),
                'architecture': platform.machine(),
                'processor': platform.processor(),
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': psutil.virtual_memory().total / (1024**3),
                'hostname': platform.node()
            }
            self.status = "completed"
            self.result = info
            return info
        except Exception as e:
            self.status = "failed"
            self.error = str(e)
            raise

class NetworkDiagnosticTask(Task):
    """Task to diagnose network connectivity"""
    
    def __init__(self):
        super().__init__("network_diagnostic", "Diagnose network connectivity")
    
    def execute(self, hosts: List[str] = None, **kwargs) -> Dict[str, Any]:
        """Execute network diagnostic"""
        import socket
        
        if hosts is None:
            hosts = ["8.8.8.8", "1.1.1.1", "google.com"]
        
        self.status = "running"
        results = {
            'hosts_tested': [],
            'reachable': [],
            'unreachable': []
        }
        
        for host in hosts:
            try:
                socket.setdefaulttimeout(5)
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex((host, 80))
                sock.close()
                
                host_result = {
                    'host': host,
                    'reachable': result == 0
                }
                results['hosts_tested'].append(host_result)
                
                if result == 0:
                    results['reachable'].append(host)
                else:
                    results['unreachable'].append(host)
            except Exception as e:
                results['unreachable'].append(host)
                host_result = {
                    'host': host,
                    'reachable': False,
                    'error': str(e)
                }
                results['hosts_tested'].append(host_result)
        
        self.status = "completed"
        self.result = results
        return results

class ProcessCheckTask(Task):
    """Task to check if a process is running"""
    
    def __init__(self):
        super().__init__("process_check", "Check if a process is running")
    
    def execute(self, process_name: str = None, **kwargs) -> Dict[str, Any]:
        """Execute process check"""
        import psutil
        
        if not process_name:
            # Default to checking for 'python' if no process_name provided
            process_name = 'python'
        
        self.status = "running"
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_percent']):
            try:
                if process_name.lower() in proc.info['name'].lower():
                    processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        result = {
            'process_name': process_name,
            'found': len(processes) > 0,
            'count': len(processes),
            'processes': processes
        }
        
        self.status = "completed"
        self.result = result
        return result

class DiskSpaceCheckTask(Task):
    """Task to check disk space"""
    
    def __init__(self):
        super().__init__("disk_space_check", "Check disk space usage")
    
    def execute(self, path: str = "/", threshold: int = 80, **kwargs) -> Dict[str, Any]:
        """Execute disk space check"""
        import psutil
        import os
        
        # Windows compatibility
        if path == "/" and os.name == 'nt':
            path = "C:\\"
        
        self.status = "running"
        usage = psutil.disk_usage(path)
        
        percent_used = (usage.used / usage.total) * 100
        status = "warning" if percent_used >= threshold else "ok"
        
        result = {
            'path': path,
            'total_gb': usage.total / (1024**3),
            'used_gb': usage.used / (1024**3),
            'free_gb': usage.free / (1024**3),
            'percent_used': percent_used,
            'threshold': threshold,
            'status': status
        }
        
        self.status = "completed"
        self.result = result
        return result

