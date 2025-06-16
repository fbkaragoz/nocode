"""
Enhanced CLI with split terminal interface and real-time streaming.
"""

import logging
import threading
import time
import psutil
import requests


from config.constants import PromptType
from models.code_request import CodeRequest
from core.auto_coder import AutoCoderEngine
from ui.split_terminal import SplitTerminalInterface
from templates.prompt_manager import PromptManager


logger = logging.getLogger(__name__)


class EnhancedAutoCoderCLI:
    """Enhanced CLI with split terminal interface and real-time features."""
    
    def __init__(self, engine: AutoCoderEngine):
        """Initialize enhanced CLI with engine."""
        self.engine = engine
        self.terminal = SplitTerminalInterface()
        self.prompt_manager = PromptManager()
        self.conversation_turns = 0
        self.total_tokens_generated = 0
        self.is_running = False
        
        # Start system monitoring
        self.system_monitor_thread = None
        self.start_system_monitoring()
    
    def start_system_monitoring(self):
        """Start background system monitoring."""
        def monitor_system():
            while self.is_running:
                try:
                    # Simple connection status without detailed logging
                    connection_status = self._check_simple_connection()
                    
                    # Get system info
                    system_info = {
                        "ollama_connected": connection_status,
                        "model_status": "Active" if connection_status else "Disconnected",
                        "model_name": self.engine.settings.model_name,
                        "context_length": self.engine.settings.get("model_params.context_length", 8192),
                        "conversation_turns": self.conversation_turns
                    }
                    
                    # Get memory usage
                    process = psutil.Process()
                    memory_info = process.memory_info()
                    memory_mb = memory_info.rss / 1024 / 1024
                    
                    # Update terminal
                    self.terminal.update_system_info(system_info)
                    
                    # Update metrics with memory
                    current_metrics = getattr(self.terminal, 'metrics_data', {})
                    current_metrics['memory_usage'] = memory_mb
                    self.terminal.update_metrics(current_metrics)
                    
                    time.sleep(5)  # Reduced frequency: Update every 5 seconds
                except Exception as e:
                    logger.error(f"System monitoring error: {e}")
                    time.sleep(10)
        
        self.is_running = True
        self.system_monitor_thread = threading.Thread(target=monitor_system, daemon=True)
        self.system_monitor_thread.start()
    
    def _check_simple_connection(self) -> bool:
        """Simple connection check without logging spam."""
        try:
            response = requests.get(f"{self.engine.settings.ollama_url}/api/tags", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def run_interactive(self) -> int:
        """Run enhanced interactive mode with split terminal."""
        try:
            # Start terminal interface
            self.terminal.start_live_display()
            
            # Welcome message
            self._show_welcome()
            
            while True:
                try:
                    # Get user input
                    user_input = self.terminal.get_user_input("\n🎯 What would you like me to do? > ")
                    
                    if not user_input:
                        continue
                    
                    # Handle special commands
                    if user_input.lower() in ['exit', 'quit', 'q']:
                        self._show_goodbye()
                        return 0
                    elif user_input.lower() in ['clear', 'clear history']:
                        self._handle_clear_history()
                        continue
                    elif user_input.lower().startswith('improve:'):
                        code_to_improve = user_input[8:].strip()
                        self._handle_recursive_improvement(code_to_improve)
                        continue
                    elif user_input.lower().startswith('breakdown:'):
                        task_description = user_input[10:].strip()
                        self._handle_task_breakdown(task_description)
                        continue
                    elif user_input.lower() in ['help', 'h']:
                        self.terminal.show_help()
                        continue
                    elif user_input.lower().startswith('config:'):
                        self._handle_config_command(user_input[7:].strip())
                        continue
                    
                    # Normal code generation
                    self._handle_code_generation(user_input)
                    
                except KeyboardInterrupt:
                    self._show_goodbye()
                    return 0
                except Exception as e:
                    logger.error(f"CLI error: {e}")
                    self.terminal.show_error(str(e))
        
        finally:
            self.is_running = False
            self.terminal.stop_live_display()
    
    def _show_welcome(self):
        """Show welcome message in terminal."""
        welcome_text = """🚀 Advanced Automatic Code Generation System

✨ Features:
• Real-time code generation streaming
• Live performance metrics
• Configurable model behaviors
• Syntax highlighting
• System monitoring

Type 'help' for commands or start coding!"""
        
        self.terminal.update_input_area(welcome_text)
    
    def _show_goodbye(self):
        """Show goodbye message."""
        goodbye_stats = f"""👋 Session Summary:
• Conversation turns: {self.conversation_turns}
• Total tokens generated: {self.total_tokens_generated}
• Model used: {self.engine.settings.model_name}

Thanks for using Advanced Auto Coder!"""
        
        self.terminal.update_input_area(goodbye_stats)
        time.sleep(2)
    
    def _handle_code_generation(self, prompt: str):
        """Handle code generation with real-time streaming."""
        try:
            # Start generation visualization
            self.terminal.start_code_generation(prompt)
            
            # Create request with dynamic configuration
            request = CodeRequest(
                prompt=prompt,
                prompt_type=PromptType.CODE_GENERATION,
                temperature=self.prompt_manager.get_temperature_for_type(PromptType.CODE_GENERATION),
                max_tokens=self.prompt_manager.get_max_tokens_for_type(PromptType.CODE_GENERATION)
            )
            
            # Start metrics tracking
            start_time = time.time()
            
            # Generate code with enhanced prompting
            response = self._generate_with_enhanced_prompting(request)
            
            # Calculate final metrics
            end_time = time.time()
            response_time = end_time - start_time
            
            if response.success:
                # Update conversation count
                self.conversation_turns += 1
                
                # Extract and display final code
                final_code = response.content
                detected_language = self._detect_primary_language(response.code_blocks)
                
                # Complete generation visualization
                self.terminal.complete_code_generation(final_code, detected_language)
                
                # Update metrics
                metrics = {
                    "response_time": response_time,
                    "token_count": response.performance.token_count if response.performance else 0,
                    "tokens_per_second": response.performance.tokens_per_second if response.performance else 0,
                    "model_confidence": self._estimate_confidence(response)
                }
                
                self.total_tokens_generated += metrics["token_count"]
                self.terminal.update_metrics(metrics)
                
                # Offer to save
                if response.code_blocks:
                    self._offer_save_option(response.code_blocks)
                
            else:
                self.terminal.show_error(response.error_message or "Code generation failed")
                
        except Exception as e:
            logger.error(f"Code generation error: {e}")
            self.terminal.show_error(str(e))
    
    def _generate_with_enhanced_prompting(self, request: CodeRequest):
        """Generate code with enhanced prompting from template manager."""
        # Get enhanced system prompt
        context = {
            'target_language': request.target_language.value if request.target_language else None,
            'conversation_turn': self.conversation_turns
        }
        
        enhanced_system_prompt = self.prompt_manager.get_system_prompt(
            request.prompt_type, 
            context
        )
        
        # Update request with enhanced prompt (if the service supports it)
        # For now, we'll enhance through the existing system
        
        return self.engine.generate_code(request)
    
    def _handle_recursive_improvement(self, code: str):
        """Handle recursive code improvement with visualization."""
        try:
            self.terminal.start_code_generation(f"Improving code: {code[:100]}...")
            
            improvements = self.engine.improve_code_recursively(code)
            
            if improvements:
                # Show improvement progress
                for i, improvement in enumerate(improvements, 1):
                    self.terminal.stream_code_chunk(f"\n--- Improvement Cycle {i} ---\n")
                    self.terminal.stream_code_chunk(improvement.content[:500] + "...\n")
                
                # Show final result
                final_improvement = improvements[-1]
                if final_improvement.code_blocks:
                    final_code = final_improvement.code_blocks[0].code
                    language = final_improvement.code_blocks[0].language.value
                    self.terminal.complete_code_generation(final_code, language)
                    
                    # Update metrics
                    metrics = {
                        "improvement_cycles": len(improvements),
                        "final_confidence": self._estimate_confidence(final_improvement)
                    }
                    self.terminal.update_metrics(metrics)
                    
                    self._offer_save_option(final_improvement.code_blocks, "improved_code")
                else:
                    self.terminal.complete_code_generation(final_improvement.content)
            else:
                self.terminal.show_error("No improvements generated")
                
        except Exception as e:
            logger.error(f"Improvement error: {e}")
            self.terminal.show_error(str(e))
    
    def _handle_task_breakdown(self, task_description: str):
        """Handle task breakdown with visualization."""
        try:
            self.terminal.start_code_generation(f"Breaking down task: {task_description}")
            
            result = self.engine.break_down_task(task_description)
            
            if result.success:
                self.terminal.complete_code_generation(result.content, "markdown")
                
                if result.code_blocks:
                    self._offer_save_option(result.code_blocks, "task_breakdown")
            else:
                self.terminal.show_error(result.error_message or "Task breakdown failed")
                
        except Exception as e:
            logger.error(f"Task breakdown error: {e}")
            self.terminal.show_error(str(e))
    
    def _handle_clear_history(self):
        """Handle clearing conversation history."""
        self.engine.clear_conversation_history()
        self.conversation_turns = 0
        self.terminal.update_input_area("🧹 Conversation history cleared!")
    
    def _handle_config_command(self, config_cmd: str):
        """Handle configuration commands."""
        if config_cmd == "show":
            # Show current configuration
            behaviors = self.prompt_manager.list_available_behaviors()
            config_text = f"Available behaviors: {', '.join(behaviors)}"
            self.terminal.update_input_area(config_text)
        elif config_cmd.startswith("set"):
            # Allow runtime configuration changes
            self.terminal.update_input_area("Configuration update feature coming soon!")
        else:
            self.terminal.update_input_area("Config commands: show, set <key> <value>")
    
    def _offer_save_option(self, code_blocks, default_name: str = "generated_code"):
        """Offer to save code blocks (simplified for terminal interface)."""
        # In a full implementation, this could show a save dialog
        # For now, auto-save with timestamp
        try:
            saved_files = self.engine.save_code_blocks(code_blocks, default_name)
            save_message = f"💾 Auto-saved {len(saved_files)} files to {default_name}_[timestamp]/"
            
            # Show save confirmation briefly
            current_metrics = getattr(self.terminal, 'metrics_data', {})
            current_metrics['files_saved'] = len(saved_files)
            self.terminal.update_metrics(current_metrics)
            
        except Exception as e:
            logger.error(f"Save error: {e}")
    
    def _detect_primary_language(self, code_blocks) -> str:
        """Detect primary programming language from code blocks."""
        if not code_blocks:
            return "text"
        
        # Return the language of the first code block
        return code_blocks[0].language.value
    
    def _estimate_confidence(self, response) -> float:
        """Estimate model confidence based on response characteristics."""
        # Simple heuristic confidence estimation
        confidence = 0.5  # Base confidence
        
        if response.success:
            confidence += 0.3
        
        if response.code_blocks:
            confidence += 0.1 * len(response.code_blocks)
        
        if response.performance and response.performance.tokens_per_second > 20:
            confidence += 0.1
        
        # Check for common error indicators in content
        error_indicators = ['error', 'exception', 'failed', 'cannot', 'unable']
        content_lower = response.content.lower()
        
        error_count = sum(1 for indicator in error_indicators if indicator in content_lower)
        confidence -= error_count * 0.05
        
        return min(max(confidence, 0.0), 1.0)  # Clamp between 0 and 1 