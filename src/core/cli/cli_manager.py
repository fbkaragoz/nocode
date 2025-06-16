"""
Main CLI Manager - Coordinates all CLI functionality.
Clean architecture implementation with modular design.
"""

import logging
import threading
import time
import os
from typing import Dict, Any, Optional
from datetime import datetime

from config.constants import PromptType
from models.code_request import CodeRequest
from core.auto_coder import AutoCoderEngine
from core.streaming.stream_manager import StreamManager
from core.interface import DisplayManager, DisplayMode, DisplayConfig
from templates.prompt_manager import PromptManager
from .command_processor import CommandProcessor
from .input_handler import InputHandler


logger = logging.getLogger(__name__)


class CLIManager:
    """
    Main CLI Manager - Clean architecture implementation.
    
    Responsibilities:
    - Coordinate all CLI components
    - Manage user interaction flow
    - Handle streaming and real-time updates
    - Maintain session state
    """
    
    def __init__(self, engine: AutoCoderEngine, interface_mode: str = "standard", project_mode: bool = False):
        """Initialize CLI Manager with clean dependencies."""
        self.engine = engine
        self.interface_mode = interface_mode
        self.project_mode = project_mode
        
        # Configure display mode
        display_mode = DisplayMode.STANDARD
        if interface_mode == "analytics":
            display_mode = DisplayMode.ANALYTICS
        elif interface_mode == "minimal":
            display_mode = DisplayMode.MINIMAL
        
        # Core components
        self.stream_manager = StreamManager()
        self.display_manager = DisplayManager(DisplayConfig(mode=display_mode))
        self.prompt_manager = PromptManager()
        self.command_processor = CommandProcessor(engine, self.stream_manager)
        self.input_handler = InputHandler(self.display_manager)
        
        # Project management (if enabled)
        self.project_manager = None
        if project_mode:
            from core.project_manager import ProjectManager
            self.project_manager = ProjectManager(engine)
        
        # Session state
        self.conversation_turns = 0
        self.total_tokens_generated = 0
        self.session_start_time = time.time()
        self.is_running = False
        
        # System monitoring
        self.system_monitor_thread = None
        self.performance_cache = {}
        
        # Storage paths
        self._setup_storage_paths()
    
    def _setup_storage_paths(self):
        """Setup storage paths for temp, cache, and logs."""
        self.storage_paths = {
            'tmp': 'tmp',
            'cache': 'cache', 
            'logs': 'logs',
            'generated_code': 'generated_code'
        }
        
        # Create directories if they don't exist
        for path in self.storage_paths.values():
            os.makedirs(path, exist_ok=True)
    
    def start(self) -> int:
        """Start the CLI manager and interactive session."""
        try:
            logger.info("Starting CLI Manager")
            
            # Initialize display manager
            self.display_manager.initialize()
            
            # Start system monitoring
            self._start_system_monitoring()
            
            # Show welcome
            self._show_welcome_screen()
            
            # Main interaction loop
            return self._run_interaction_loop()
            
        except KeyboardInterrupt:
            return self._handle_graceful_shutdown()
        except Exception as e:
            logger.error(f"CLI Manager error: {e}")
            self.display_manager.show_error(f"Fatal error: {e}")
            return 1
        finally:
            self._cleanup()
    
    def _run_interaction_loop(self) -> int:
        """Main interaction loop with clean error handling."""
        self.is_running = True
        
        while self.is_running:
            try:
                # Get user input
                user_input = self.input_handler.get_user_input()
                
                if not user_input:
                    continue
                
                # Process command
                result = self.command_processor.process_command(user_input)
                
                if result.should_exit:
                    break
                    
                # Update session metrics
                if result.tokens_generated:
                    self.total_tokens_generated += result.tokens_generated
                    self.conversation_turns += 1
                    
                # Cache performance data
                self._cache_performance_data(result)
                
            except KeyboardInterrupt:
                break
            
            except Exception as e:
                    logger.error(f"Interaction loop error: {e}")
                    self.display_manager.show_error(f"Error: {e}")
        
        return 0
    
    def _start_system_monitoring(self):
        """Start background system monitoring with proper resource management."""
        def monitor_system():
            import psutil
            
            while self.is_running:
                try:
                    # Collect system metrics
                    metrics = self._collect_system_metrics()
                    
                    # Update display
                    self.display_manager.update_system_metrics(metrics)
                    
                    # Cache metrics for analysis
                    self._cache_system_metrics(metrics)
                    
                    time.sleep(5)  # Update every 5 seconds to reduce noise
                    
                except Exception as e:
                    logger.error(f"System monitoring error: {e}")
                    time.sleep(5)
        
        self.system_monitor_thread = threading.Thread(target=monitor_system, daemon=True)
        self.system_monitor_thread.start()
    
    def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive system metrics."""
        import psutil
        
        # Basic system info
        process = psutil.Process()
        memory_info = process.memory_info()
        
        # Get CPU percentage (with interval for accurate reading)
        cpu_percent = process.cpu_percent(interval=0.1)
        if cpu_percent == 0.0:
            # Fallback to system CPU if process CPU is 0
            cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Ollama connection status
        ollama_status = self._check_ollama_status()
        
        metrics = {
            # System resources
            'memory_usage_mb': round(memory_info.rss / 1024 / 1024, 1),
            'cpu_usage_percent': round(cpu_percent, 1),
            
            # Service status
            'ollama_connected': ollama_status,
            'model_status': 'Active' if ollama_status else 'Disconnected',
            
            # Session info
            'conversation_turns': self.conversation_turns,
            'total_tokens': self.total_tokens_generated,
            'uptime': self._get_uptime(),
            'last_updated': datetime.now().strftime("%H:%M:%S"),
            
            # Model info
            'model_name': self.engine.settings.model_name,
            'context_length': f"{self.engine.settings.get('model_params.context_length', 8192)} tokens"
        }
        
        # Add cached performance data
        if self.performance_cache:
            metrics.update(self.performance_cache)
        
        return metrics
    

    
    def _check_ollama_status(self) -> bool:
        """Quick Ollama connection check without spam."""
        try:
            import requests
            response = requests.get(f"{self.engine.settings.ollama_url}/api/tags", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def _cache_performance_data(self, result):
        """Cache performance data for monitoring."""
        if hasattr(result, 'performance_metrics'):
            self.performance_cache.update({
                'last_response_time': f"{result.performance_metrics.get('response_time', 0):.2f}s",
                'last_tokens_per_second': f"{result.performance_metrics.get('tokens_per_second', 0):.1f}",
                'last_confidence': f"{result.performance_metrics.get('confidence', 0):.1%}"
            })
    
    def _cache_system_metrics(self, metrics: Dict[str, Any]):
        """Cache system metrics to file for analysis."""
        cache_file = os.path.join(self.storage_paths['cache'], 'system_metrics.json')
        
        try:
            import json
            
            # Load existing cache
            cached_data = []
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
            
            # Add new metrics with timestamp
            metrics['timestamp'] = time.time()
            cached_data.append(metrics)
            
            # Keep only last 100 entries
            cached_data = cached_data[-100:]
            
            # Save back
            with open(cache_file, 'w') as f:
                json.dump(cached_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Metrics caching error: {e}")
    
    def _get_uptime(self) -> str:
        """Get session uptime."""
        uptime_seconds = time.time() - self.session_start_time
        minutes = int(uptime_seconds // 60)
        seconds = int(uptime_seconds % 60)
        hours = int(minutes // 60)
        minutes = minutes % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        return f"{minutes}m {seconds}s"
    
    def _show_welcome_screen(self):
        """Show welcome screen with system info."""
        features = [
            'Real-time code streaming',
            'Performance monitoring',
            'Modular architecture',
            'Intelligent caching',
            'Extended context (131k tokens)',
            'GPU acceleration'
        ]
        
        # Add project management features if enabled
        if self.project_mode:
            features.extend([
                'Multi-step project management',
                'Automatic project breakdown',
                'Dependency tracking'
            ])
        
        # Add analytics info if enabled
        if self.interface_mode == "analytics":
            features.append('Analytics dashboard monitoring')
        
        welcome_data = {
            'title': 'AI Code Generation System',
            'version': '1.0.0',
            'interface_type': self.interface_mode.title(),
            'model': self.engine.settings.model_name,
            'features': features,
            'project_mode': self.project_mode
        }
        
        self.display_manager.show_welcome(welcome_data)
    
    def _handle_graceful_shutdown(self) -> int:
        """Handle graceful shutdown with session summary."""
        try:
            summary = {
                'conversation_turns': self.conversation_turns,
                'total_tokens': self.total_tokens_generated,
                'uptime': self._get_uptime(),
                'model_used': self.engine.settings.model_name
            }
            
            self.display_manager.show_goodbye(summary)
            return 0
            
        except Exception as e:
            logger.error(f"Shutdown error: {e}")
            return 1
    
    def _cleanup(self):
        """Cleanup resources and save session data."""
        self.is_running = False
        
        # Save session summary
        self._save_session_summary()
        
        # Cleanup display manager
        if self.display_manager:
            self.display_manager.cleanup()
        
        # Stop monitoring
        if self.system_monitor_thread and self.system_monitor_thread.is_alive():
            self.system_monitor_thread.join(timeout=2)
    
    def _save_session_summary(self):
        """Save session summary to logs."""
        try:
            summary = {
                'session_start': self.session_start_time,
                'session_end': time.time(),
                'conversation_turns': self.conversation_turns,
                'total_tokens_generated': self.total_tokens_generated,
                'interface_mode': self.interface_mode,
                'model_used': self.engine.settings.model_name
            }
            
            log_file = os.path.join(
                self.storage_paths['logs'], 
                f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            import json
            with open(log_file, 'w') as f:
                json.dump(summary, f, indent=2)
                
            logger.info(f"Session summary saved to: {log_file}")
            
        except Exception as e:
            logger.error(f"Session summary save error: {e}") 