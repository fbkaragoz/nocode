"""
Settings and configuration management for the auto coder system.
"""

import os
import yaml
from typing import Dict, Any, Optional, List


class Settings:
    """
    Configuration settings manager.
    - Simplified to use a hardcoded default configuration.
    - No longer loads from external YAML files to ensure stability.
    """
    
    def __init__(self):
        """Initialize settings with a default configuration."""
        self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "ollama": {
                "base_url": "http://127.0.0.1:11434/api",
                "model_name": "huihui_ai/deepseek-r1-Fusion:32b-coder-9010",
                "timeout": 300,
                "history_size": 10,
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 40,
            },
            "code_generation": {
                "output_directory": "generated_code",
                "auto_save": True,
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "auto_coder.log",
            },
            "ui": {
                "refresh_rate": 10,
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
        return self.get("ollama.base_url", "http://127.0.0.1:11434/api")
    
    @property
    def model_name(self) -> str:
        """Get model name."""
        return self.get("ollama.model_name", "qwen:0.5b")
    
    @property
    def timeout(self) -> int:
        """Get request timeout."""
        return self.get("ollama.timeout", 300)
    
    @property
    def history_size(self) -> int:
        """Get history size."""
        return self.get("ollama.history_size", 10)
    
    @property
    def temperature(self) -> float:
        """Get temperature."""
        return self.get("ollama.temperature", 0.7)
    
    @property
    def top_p(self) -> float:
        """Get top_p."""
        return self.get("ollama.top_p", 0.9)
    
    @property
    def top_k(self) -> int:
        """Get top_k."""
        return self.get("ollama.top_k", 40)
    
    @property
    def output_directory(self) -> str:
        """Get output directory for generated code."""
        return self.get("code_generation.output_directory", "generated_code")
    
    @property
    def auto_save(self) -> bool:
        """Get auto_save."""
        return self.get("code_generation.auto_save", True)
    
    @property
    def refresh_rate(self) -> int:
        """Get refresh rate."""
        return self.get("ui.refresh_rate", 10)
    
    @property
    def logging_level(self) -> str:
        """Get logging level."""
        return self.get("logging.level", "INFO")
    
    @property
    def logging_format(self) -> str:
        """Get logging format."""
        return self.get("logging.format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    @property
    def logging_file(self) -> str:
        """Get logging file."""
        return self.get("logging.file", "auto_coder.log")
    
    @property
    def performance_track_token_usage(self) -> bool:
        """Get performance track_token_usage."""
        return self.get("performance.track_token_usage", True)
    
    @property
    def performance_track_response_time(self) -> bool:
        """Get performance track_response_time."""
        return self.get("performance.track_response_time", True)
    
    @property
    def performance_track_memory_usage(self) -> bool:
        """Get performance track_memory_usage."""
        return self.get("performance.track_memory_usage", False)
    
    @property
    def performance_benchmark_mode(self) -> bool:
        """Get performance benchmark_mode."""
        return self.get("performance.benchmark_mode", False)
    
    @property
    def ui_interface_type(self) -> str:
        """Get ui interface_type."""
        return self.get("ui.interface_type", "simple")
    
    @property
    def ui_show_performance_metrics(self) -> bool:
        """Get ui show_performance_metrics."""
        return self.get("ui.show_performance_metrics", True)
    
    @property
    def ui_enable_syntax_highlighting(self) -> bool:
        """Get ui enable_syntax_highlighting."""
        return self.get("ui.enable_syntax_highlighting", False)
    
    @property
    def ui_auto_save_prompt(self) -> bool:
        """Get ui auto_save_prompt."""
        return self.get("ui.auto_save_prompt", True)
    
    @property
    def security_code_analysis(self) -> bool:
        """Get security code_analysis."""
        return self.get("security.code_analysis", True)
    
    @property
    def security_vulnerability_check(self) -> bool:
        """Get security vulnerability_check."""
        return self.get("security.vulnerability_check", True)
    
    @property
    def security_safe_execution(self) -> bool:
        """Get security safe_execution."""
        return self.get("security.safe_execution", False)
    
    @property
    def security_allowed_operations(self) -> List[str]:
        """Get security allowed_operations."""
        return self.get("security.allowed_operations", ["read", "write", "execute"])
    
    @property
    def advanced_plugin_system(self) -> bool:
        """Get advanced plugin_system."""
        return self.get("advanced.plugin_system", False)
    
    @property
    def advanced_multi_model_support(self) -> bool:
        """Get advanced multi_model_support."""
        return self.get("advanced.multi_model_support", False)
    
    @property
    def advanced_cloud_integration(self) -> bool:
        """Get advanced cloud_integration."""
        return self.get("advanced.cloud_integration", False)
    
    @property
    def advanced_team_collaboration(self) -> bool:
        """Get advanced team_collaboration."""
        return self.get("advanced.team_collaboration", False)
    
    @property
    def recursive_improvement_max_cycles(self) -> int:
        """Get recursive_improvement max_cycles."""
        return self.get("recursive_improvement.max_cycles", 3)
    
    @property
    def recursive_improvement_improvement_threshold(self) -> float:
        """Get recursive_improvement improvement_threshold."""
        return self.get("recursive_improvement.improvement_threshold", 0.1)
    
    @property
    def recursive_improvement_analysis_depth(self) -> str:
        """Get recursive_improvement analysis_depth."""
        return self.get("recursive_improvement.analysis_depth", "deep") 