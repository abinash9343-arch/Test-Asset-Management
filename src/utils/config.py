"""Configuration management"""
import yaml
from pathlib import Path
from typing import Dict, Any

class Config:
    """Configuration manager for IT Agent"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file, 'r') as f:
                    return yaml.safe_load(f) or {}
            return self._default_config()
            return self._default_config()
        except Exception as e:
            print(f"Warning: Could not load config: {e}. Using defaults.")
            return self._default_config()

    def save(self):
        """Save configuration to YAML file"""
        try:
            config_file = Path(self.config_path)
            # Create directory if it doesn't exist
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration"""
        return {
            'agent': {
                'name': 'Draup Asset Management',
                'version': '1.0.0',
                'max_retries': 3,
                'timeout': 30
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/agent.log',
                'max_size_mb': 10,
                'backup_count': 5
            },
            'monitoring': {
                'enabled': True,
                'check_interval': 60,
                'health_check_timeout': 5
            },
            'diagnostics': {
                'enable_verbose': False,
                'save_error_details': True
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value using dot notation"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

