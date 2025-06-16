"""
Settings and configuration management for the auto coder system.
"""

import os
import yaml
from typing import Dict, Any, Optional


class Settings:
    """Configuration settings manager."""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize settings with optional config file."""
        self.config_file = config_file or "config.yaml"
        self._config = {}
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from YAML file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f) or {}
            else:
                self._config = self._get_default_config()
                self.save_config()
        except Exception as e:
            print(f"Warning: Could not load config file. Using defaults. Error: {e}")
            self._config = self._get_default_config()
    
    def save_config(self) -> None:
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config file. Error: {e}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "ollama": {
                "base_url": "http://127.0.0.1:11434",
                "model_name": "huihui_ai/deepseek-r1-Fusion:32b-coder-9010",
                "timeout": 300,
                "max_retries": 3
            },
            "model_params": {
                "temperature": 0.1,
                "top_p": 0.9,
                "top_k": 40,
                "max_tokens": 4096,
                "context_length": 8192
            },
            "recursive_improvement": {
                "max_cycles": 3,
                "improvement_threshold": 0.1,
                "analysis_depth": "deep"
            },
            "code_generation": {
                "output_directory": "generated_code",
                "save_format": "organized",
                "auto_save": False,
                "file_extensions": {
                    "python": ".py",
                    "javascript": ".js",
                    "typescript": ".ts",
                    "html": ".html",
                    "css": ".css",
                    "java": ".java",
                    "cpp": ".cpp",
                    "go": ".go",
                    "rust": ".rs",
                    "php": ".php",
                    "sql": ".sql"
                }
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "auto_coder.log",
                "max_size": "10MB",
                "backup_count": 5,
                "quiet_mode": False
            },
            "performance": {
                "track_token_usage": True,
                "track_response_time": True,
                "track_memory_usage": False,
                "benchmark_mode": False
            },
            "ui": {
                "interface_type": "simple",
                "show_performance_metrics": True,
                "enable_syntax_highlighting": False,
                "auto_save_prompt": True
            },
            "security": {
                "code_analysis": True,
                "vulnerability_check": True,
                "safe_execution": False,
                "allowed_operations": ["read", "write", "execute"]
            },
            "advanced": {
                "plugin_system": False,
                "multi_model_support": False,
                "cloud_integration": False,
                "team_collaboration": False
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports dot notation)."""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value by key (supports dot notation)."""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    @property
    def ollama_url(self) -> str:
        """Get Ollama base URL."""
        return self.get("ollama.base_url", "http://127.0.0.1:11434")
    
    @property
    def model_name(self) -> str:
        """Get model name."""
        return self.get("ollama.model_name", "huihui_ai/deepseek-r1-Fusion:32b-coder-9010")
    
    @property
    def timeout(self) -> int:
        """Get request timeout."""
        return self.get("ollama.timeout", 300)
    
    @property
    def temperature(self) -> float:
        """Get model temperature."""
        return self.get("model_params.temperature", 0.1)
    
    @property
    def max_tokens(self) -> int:
        """Get maximum tokens."""
        return self.get("model_params.max_tokens", 4096)
    
    @property
    def output_directory(self) -> str:
        """Get output directory for generated code."""
        return self.get("code_generation.output_directory", "generated_code")
    
    @property
    def max_improvement_cycles(self) -> int:
        """Get maximum improvement cycles."""
        return self.get("recursive_improvement.max_cycles", 3) 