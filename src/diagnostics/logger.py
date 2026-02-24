"""Logging system for IT Agent"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime
try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False
    Fore = Style = None

class ColoredFormatter(logging.Formatter):
    """Colored log formatter for console output"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if COLORAMA_AVAILABLE:
            self.COLORS = {
                'DEBUG': Fore.CYAN,
                'INFO': Fore.GREEN,
                'WARNING': Fore.YELLOW,
                'ERROR': Fore.RED,
                'CRITICAL': Fore.RED + Style.BRIGHT
            }
        else:
            self.COLORS = {}
    
    def format(self, record):
        if COLORAMA_AVAILABLE and record.levelname in self.COLORS:
            log_color = self.COLORS.get(record.levelname, '')
            record.levelname = f"{log_color}{record.levelname}{Style.RESET_ALL}"
        return super().format(record)

class AgentLogger:
    """Centralized logging for IT Agent"""
    
    def __init__(self, name: str = "ITAgent", log_file: str = "logs/agent.log", 
                 level: str = "INFO", max_size_mb: int = 10, backup_count: int = 5):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
        
        # Create logs directory
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # File handler with rotation
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_size_mb * 1024 * 1024,
            backupCount=backup_count
        )
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self.logger.critical(message, **kwargs)
    
    def log_task(self, task_name: str, status: str, details: str = ""):
        """Log task execution"""
        message = f"Task: {task_name} - Status: {status}"
        if details:
            message += f" - {details}"
        
        if status == "SUCCESS":
            self.info(message)
        elif status == "FAILED":
            self.error(message)
        else:
            self.warning(message)

