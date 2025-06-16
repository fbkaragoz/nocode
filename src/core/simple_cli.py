"""
Simple CLI interface with stable interaction.
"""

import logging
import time
from typing import Optional
import os

from config.constants import PromptType
from models.code_request import CodeRequest
from core.auto_coder import AutoCoderEngine
from templates.prompt_manager import PromptManager


logger = logging.getLogger(__name__)


class SimpleAutoCoderCLI:
    """Simple, stable CLI interface for code generation."""
    
    def __init__(self, engine: AutoCoderEngine):
        """Initialize simple CLI with engine."""
        self.engine = engine
        self.prompt_manager = PromptManager()
        self.conversation_turns = 0
        self.total_tokens_generated = 0
    
    def run_interactive(self) -> int:
        """Run simple interactive mode."""
        try:
            self._show_welcome()
            
            while True:
                try:
                    # Get user input
                    user_input = input("\n🎯 What would you like me to do? > ").strip()
                    
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
                        self._show_help()
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
                    print(f"❌ Error: {e}")
        
        except Exception as e:
            logger.error(f"Fatal CLI error: {e}")
            print(f"❌ Fatal error: {e}")
            return 1
    
    def _show_welcome(self):
        """Show welcome message."""
        print("""
🚀 Advanced Automatic Code Generation System

✨ Features:
• Real-time code generation with AI
• Recursive improvement capabilities  
• Task breakdown and planning
• Multi-language support
• Performance tracking

Commands:
• Type your coding request naturally
• improve: <code> - Improve existing code
• breakdown: <task> - Break down complex tasks
• config: <setting>=<value> - Change settings
• clear - Clear conversation history
• help - Show help
• exit - Exit the system

Type 'help' for more commands or start coding!
""")
    
    def _show_goodbye(self):
        """Show goodbye message."""
        print(f"""
👋 Session Summary:
• Conversation turns: {self.conversation_turns}
• Total tokens generated: {self.total_tokens_generated}
• Model used: {self.engine.settings.model_name}

Thanks for using Advanced Auto Coder!
""")
        time.sleep(1)
    
    def _show_help(self):
        """Show help information."""
        print("""
📚 Available Commands:

🔧 Basic Usage:
  <request>                 - Generate code from natural language
  improve: <code>          - Recursively improve existing code
  breakdown: <task>        - Break down complex tasks into subtasks
  
⚙️ Configuration:
  config: model=<name>     - Change AI model
  config: temp=<value>     - Change temperature (0.0-1.0)
  config: show             - Show current configuration

🛠️ Utilities:
  clear                    - Clear conversation history
  help                     - Show this help message
  exit/quit/q             - Exit the system

💡 Examples:
  > Create a Python REST API with FastAPI
  > improve: def factorial(n): return n * factorial(n-1) if n > 1 else 1
  > breakdown: Build a todo application with React and Node.js
  > config: temp=0.2
""")
    
    def _handle_code_generation(self, prompt: str):
        """Handle code generation request."""
        try:
            print("\n⚡ Generating code...")
            start_time = time.time()
            
            # Create request
            request = CodeRequest(
                prompt=prompt,
                prompt_type=PromptType.CODE_GENERATION,
                temperature=self.prompt_manager.get_temperature_for_type(PromptType.CODE_GENERATION),
                max_tokens=self.prompt_manager.get_max_tokens_for_type(PromptType.CODE_GENERATION)
            )
            
            # Generate code
            response = self.engine.generate_code(request)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if response.success:
                self.conversation_turns += 1
                
                # Display result
                print("\n✅ Code generated successfully!")
                print("=" * 80)
                print(response.content)
                print("=" * 80)
                
                # Show performance metrics
                if response.performance:
                    print(f"\n📊 Performance:")
                    print(f"   Response time: {response_time:.2f}s")
                    print(f"   Tokens: {response.performance.token_count}")
                    print(f"   Speed: {response.performance.tokens_per_second:.1f} tokens/s")
                    self.total_tokens_generated += response.performance.token_count
                
                # Offer to save
                if response.code_blocks:
                    self._offer_save_option(response.code_blocks)
            else:
                print(f"\n❌ Generation failed: {response.error_message}")
                
        except Exception as e:
            logger.error(f"Code generation error: {e}")
            print(f"❌ Error during code generation: {e}")
    
    def _handle_recursive_improvement(self, code: str):
        """Handle recursive code improvement."""
        try:
            print("\n🔄 Analyzing and improving code...")
            
            request = CodeRequest(
                prompt=f"Analyze and improve this code:\n\n{code}",
                prompt_type=PromptType.RECURSIVE_IMPROVEMENT,
                temperature=0.1,
                max_tokens=4096
            )
            
            response = self.engine.generate_code(request)
            
            if response.success:
                print("\n✅ Code improvement completed!")
                print("=" * 80)
                print(response.content)
                print("=" * 80)
                
                if response.performance:
                    print(f"\n📊 Performance: {response.performance.response_time:.2f}s")
            else:
                print(f"\n❌ Improvement failed: {response.error_message}")
                
        except Exception as e:
            logger.error(f"Code improvement error: {e}")
            print(f"❌ Error during code improvement: {e}")
    
    def _handle_task_breakdown(self, task_description: str):
        """Handle task breakdown request."""
        try:
            print("\n📋 Breaking down task...")
            
            request = CodeRequest(
                prompt=f"Break down this task into manageable subtasks:\n\n{task_description}",
                prompt_type=PromptType.TASK_DECOMPOSITION,
                temperature=0.2,
                max_tokens=3072
            )
            
            response = self.engine.generate_code(request)
            
            if response.success:
                print("\n✅ Task breakdown completed!")
                print("=" * 80)
                print(response.content)
                print("=" * 80)
            else:
                print(f"\n❌ Task breakdown failed: {response.error_message}")
                
        except Exception as e:
            logger.error(f"Task breakdown error: {e}")
            print(f"❌ Error during task breakdown: {e}")
    
    def _handle_clear_history(self):
        """Clear conversation history."""
        self.engine.ollama.clear_conversation_history()
        self.conversation_turns = 0
        print("\n🧹 Conversation history cleared!")
    
    def _handle_config_command(self, config_cmd: str):
        """Handle configuration commands."""
        try:
            if config_cmd == "show":
                print(f"\n⚙️ Current Configuration:")
                print(f"   Model: {self.engine.settings.model_name}")
                print(f"   Ollama URL: {self.engine.settings.ollama_url}")
                print(f"   Temperature: {self.engine.settings.get('model_params.temperature', 0.1)}")
                print(f"   Max tokens: {self.engine.settings.get('model_params.max_tokens', 4096)}")
            elif "=" in config_cmd:
                key, value = config_cmd.split("=", 1)
                print(f"\n⚙️ Configuration update: {key}={value}")
                print("   (Configuration changes require restart)")
            else:
                print("\n❌ Invalid config command. Use 'config: show' or 'config: key=value'")
        except Exception as e:
            print(f"❌ Config error: {e}")
    
    def _offer_save_option(self, code_blocks, default_name: str = "generated_code"):
        """Offer to save generated code."""
        try:
            save_input = input(f"\n💾 Save code to file? (y/N): ").strip().lower()
            if save_input in ['y', 'yes']:
                filename = input(f"📝 Filename (default: {default_name}): ").strip()
                if not filename:  # If empty, use default
                    filename = default_name
                
                # Simple file save
                if len(code_blocks) == 1:
                    code_block = code_blocks[0]
                    extension = self._get_file_extension(code_block.language)
                    full_filename = f"{filename}{extension}"
                    
                    with open(full_filename, 'w', encoding='utf-8') as f:
                        f.write(code_block.content)
                    
                    print(f"✅ Code saved to: {full_filename}")
                    print(f"📍 Full path: {os.path.abspath(full_filename)}")
                else:
                    # Multiple blocks - save separately
                    for i, code_block in enumerate(code_blocks):
                        extension = self._get_file_extension(code_block.language)
                        full_filename = f"{filename}_part{i+1}{extension}"
                        
                        with open(full_filename, 'w', encoding='utf-8') as f:
                            f.write(code_block.content)
                        
                        print(f"✅ Code saved to: {full_filename}")
                        print(f"📍 Full path: {os.path.abspath(full_filename)}")
        except Exception as e:
            print(f"❌ Save error: {e}")
    
    def _get_file_extension(self, language) -> str:
        """Get file extension for language."""
        # Handle both string and enum types
        lang_str = language.value if hasattr(language, 'value') else str(language).lower()
        
        extensions = {
            'python': '.py',
            'javascript': '.js',
            'typescript': '.ts',
            'java': '.java',
            'cpp': '.cpp',
            'c': '.c',
            'go': '.go',
            'rust': '.rs',
            'html': '.html',
            'css': '.css',
            'sql': '.sql',
            'shell': '.sh',
            'bash': '.sh'
        }
        return extensions.get(lang_str.lower(), '.txt') 