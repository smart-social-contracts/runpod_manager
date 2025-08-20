import os
from pathlib import Path
from typing import Dict, Optional, Any


class PodConfig:
    """Configuration management for RunPod Manager"""
    
    def __init__(
        self,
        project_name: str,
        api_key: Optional[str] = None,
        config_file: Optional[str] = None,
        **kwargs
    ):
        self.project_name = project_name
        self.api_key = api_key or self._get_api_key()
        self.config = self._load_config(config_file, **kwargs)
    
    def _get_api_key(self) -> str:
        """Get RunPod API key from environment"""
        api_key = os.getenv('RUNPOD_API_KEY')
        if api_key:
            return api_key
        
        raise ValueError("RUNPOD_API_KEY not found in environment")
    
    def _load_config(self, config_file: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Load configuration from file and kwargs"""
        config = {}
        
        if config_file:
            config_path = Path(config_file)
            if config_path.exists():
                with open(config_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            config[key.strip()] = value.strip()
        
        config.setdefault('MAX_GPU_PRICE', '0.30')
        config.setdefault('CONTAINER_DISK', '20')
        config.setdefault('INACTIVITY_TIMEOUT_SECONDS', '3600')
        config.setdefault('VOLUME_MOUNT_PATH', '/workspace')
        config.setdefault('GPU_COUNT', '1')
        config.setdefault('SUPPORT_PUBLIC_IP', 'true')
        config.setdefault('START_SSH', 'true')
        
        config.update(kwargs)
        
        return config
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        self.config[key] = value
    
    def get_pod_name_prefix(self, pod_type: str) -> str:
        """Get pod name prefix for the given pod type"""
        return f"{self.project_name}-{pod_type}-"
    
    def get_pod_name(self, pod_type: str, timestamp: int) -> str:
        """Generate pod name for the given pod type and timestamp"""
        return f"{self.project_name}-{pod_type}-{timestamp}"
