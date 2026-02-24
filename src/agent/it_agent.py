"""Main IT Agent class"""
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

from ..utils.config import Config
from ..diagnostics.logger import AgentLogger
from ..diagnostics.monitor import Monitor
from ..diagnostics.health_check import HealthCheck
from .tasks import Task, SystemInfoTask, NetworkDiagnosticTask, ProcessCheckTask, DiskSpaceCheckTask

class AssetManager:
    """Main Asset Management system with diagnostic capabilities"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = Config(config_path)
        self.logger = AgentLogger(
            name=self.config.get('agent.name', 'ITAgent'),
            log_file=self.config.get('logging.file', 'logs/agent.log'),
            level=self.config.get('logging.level', 'INFO'),
            max_size_mb=self.config.get('logging.max_size_mb', 10),
            backup_count=self.config.get('logging.backup_count', 5)
        )
        
        self.monitor = Monitor(
            logger=self.logger,
            check_interval=self.config.get('monitoring.check_interval', 60)
        )
        
        self.health_checker = HealthCheck(
            timeout=self.config.get('monitoring.health_check_timeout', 5)
        )
        
        self.tasks: List[Task] = []
        self.task_history: List[Dict[str, Any]] = []
        self.running = False
        
        # Register default tasks
        self._register_default_tasks()
        
        self.logger.info(f"IT Agent initialized: {self.config.get('agent.name')}")
    
    def _register_default_tasks(self):
        """Register default diagnostic tasks"""
        self.register_task(SystemInfoTask())
        self.register_task(NetworkDiagnosticTask())
        self.register_task(ProcessCheckTask())
        self.register_task(DiskSpaceCheckTask())
    
    def register_task(self, task: Task):
        """Register a new task"""
        self.tasks.append(task)
        self.logger.debug(f"Registered task: {task.name}")
    
    def start(self):
        """Start the agent and monitoring"""
        if self.running:
            self.logger.warning("Agent is already running")
            return
        
        self.running = True
        if self.config.get('monitoring.enabled', True):
            self.monitor.start()
        
        self.logger.info("IT Agent started")
        self._log_startup_info()
    
    def stop(self):
        """Stop the agent and monitoring"""
        if not self.running:
            return
        
        self.running = False
        self.monitor.stop()
        self.logger.info("IT Agent stopped")
    
    def _log_startup_info(self):
        """Log startup information"""
        health = self.health_checker.comprehensive_health_check()
        self.logger.info(f"Initial health check: {health['overall_status']}")
    
    def execute_task(self, task_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a specific task"""
        if not self.running:
            self.logger.warning("Agent is not running. Starting agent...")
            self.start()
        
        task = self._find_task(task_name)
        if not task:
            error_msg = f"Task not found: {task_name}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        self.logger.info(f"Executing task: {task_name}")
        start_time = time.time()
        
        try:
            if not task.validate(**kwargs):
                raise ValueError(f"Task validation failed: {task_name}")
            
            result = task.execute(**kwargs)
            execution_time = time.time() - start_time
            
            self.logger.log_task(task_name, "SUCCESS", f"Completed in {execution_time:.2f}s")
            self.monitor.record_task_completion(success=True)
            
            task_record = {
                'task_name': task_name,
                'status': 'success',
                'execution_time': execution_time,
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
            self.task_history.append(task_record)
            
            return {
                'success': True,
                'task': task_name,
                'result': result,
                'execution_time': execution_time
            }
        
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            self.logger.log_task(task_name, "FAILED", error_msg)
            self.monitor.record_task_completion(success=False)
            self.monitor.record_error('task_execution', error_msg)
            
            task_record = {
                'task_name': task_name,
                'status': 'failed',
                'execution_time': execution_time,
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            }
            self.task_history.append(task_record)
            
            return {
                'success': False,
                'task': task_name,
                'error': error_msg,
                'execution_time': execution_time
            }
    
    def _find_task(self, task_name: str) -> Optional[Task]:
        """Find a task by name"""
        for task in self.tasks:
            if task.name == task_name:
                return task
        return None
    
    def diagnose(self, task_names: List[str] = None) -> Dict[str, Any]:
        """Run diagnostic tasks"""
        if task_names is None:
            # Run all diagnostic tasks
            task_names = [task.name for task in self.tasks]
        
        self.logger.info(f"Starting diagnostic: {len(task_names)} tasks")
        results = {
            'timestamp': datetime.now().isoformat(),
            'tasks': [],
            'overall_status': 'success'
        }
        
        for task_name in task_names:
            result = self.execute_task(task_name)
            results['tasks'].append(result)
            
            if not result['success']:
                results['overall_status'] = 'partial_failure'
        
        if all(not task['success'] for task in results['tasks']):
            results['overall_status'] = 'failure'
        
        self.logger.info(f"Diagnostic completed: {results['overall_status']}")
        return results
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status"""
        return self.monitor.get_health_status()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get agent metrics"""
        return self.monitor.get_metrics()
    
    def get_task_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent task history"""
        return self.task_history[-limit:]
    
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()

