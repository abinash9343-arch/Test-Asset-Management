"""Monitoring system for IT Agent"""
import time
import threading
from typing import Dict, Any, Callable, Optional
from datetime import datetime
from .health_check import HealthCheck
from .logger import AgentLogger

class Monitor:
    """Real-time monitoring for IT Agent"""
    
    def __init__(self, logger: AgentLogger, check_interval: int = 60):
        self.logger = logger
        self.check_interval = check_interval
        self.health_checker = HealthCheck()
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.metrics = {
            'start_time': datetime.now().isoformat(),
            'tasks_completed': 0,
            'tasks_failed': 0,
            'errors': []
        }
    
    def start(self):
        """Start monitoring"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("Monitoring started")
    
    def stop(self):
        """Stop monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.logger.info("Monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                health = self.health_checker.comprehensive_health_check()
                
                if health['overall_status'] != 'healthy':
                    self.logger.warning(f"Health check: {health['overall_status']}")
                    self.metrics['errors'].append({
                        'timestamp': datetime.now().isoformat(),
                        'type': 'health_check',
                        'status': health['overall_status']
                    })
                
                time.sleep(self.check_interval)
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                time.sleep(self.check_interval)
    
    def record_task_completion(self, success: bool = True):
        """Record task completion"""
        if success:
            self.metrics['tasks_completed'] += 1
        else:
            self.metrics['tasks_failed'] += 1
    
    def record_error(self, error_type: str, error_message: str):
        """Record an error"""
        self.metrics['errors'].append({
            'timestamp': datetime.now().isoformat(),
            'type': error_type,
            'message': error_message
        })
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        total_tasks = self.metrics['tasks_completed'] + self.metrics['tasks_failed']
        return {
            **self.metrics,
            'uptime_seconds': (datetime.now() - datetime.fromisoformat(self.metrics['start_time'])).total_seconds(),
            'success_rate': (
                self.metrics['tasks_completed'] / total_tasks
                if total_tasks > 0 else 0
            )
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status"""
        return self.health_checker.comprehensive_health_check()

