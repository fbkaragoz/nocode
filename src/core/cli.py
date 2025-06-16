"""
Command Line Interface for the Auto Coder System.
"""

import logging
from typing import Optional

from config.constants import PromptType
from models.code_request import CodeRequest
from core.auto_coder import AutoCoderEngine


logger = logging.getLogger(__name__)


class AutoCoderCLI:
    """Command Line Interface for Auto Coder System."""
    
    def __init__(self, engine: AutoCoderEngine):
        """Initialize CLI with engine."""
        self.engine = engine
    
    def run_interactive(self) -> int:
        """Run interactive mode - continuous user interaction."""
        print("🚀 Advanced Automatic Code Generation System")
        print("=" * 60)
        print("Commands:")
        print("  'exit' or 'quit' - Exit the program")
        print("  'clear' - Clear conversation history")  
        print("  'improve: <code>' - Recursively improve code")
        print("  'breakdown: <description>' - Break down complex task")
        print("  'help' - Show this help message")
        print("=" * 60)
        print()
        
        while True:
            try:
                user_input = input("\n🎯 What would you like me to do? > ").strip()
                
                if not user_input:
                    continue
                    
                # Handle special commands
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("👋 Goodbye!")
                    return 0
                elif user_input.lower() in ['clear', 'clear history']:
                    self.engine.clear_conversation_history()
                    print("🧹 Conversation history cleared!")
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
                
                # Normal code generation
                self._handle_code_generation(user_input)
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                return 0
            except Exception as e:
                logger.error(f"CLI error: {e}")
                print(f"❌ Unexpected error: {e}")
    
    def _handle_code_generation(self, prompt: str) -> None:
        """Handle normal code generation request."""
        print("🤖 Generating code...")
        
        request = CodeRequest(prompt=prompt)
        response = self.engine.generate_code(request)
        
        if response.success:
            print("\n" + "="*60)
            print("📝 GENERATED CODE:")
            print("="*60)
            print(response.content)
            print("="*60)
            
            if response.code_blocks:
                save_choice = input("\n💾 Save code to files? (y/n): ").lower()
                if save_choice in ['y', 'yes']:
                    task_name = input("📁 Task name (for file naming): ").strip() or "code_generation"
                    saved_files = self.engine.save_code_blocks(response.code_blocks, task_name)
                    print(f"✅ {len(saved_files)} files saved:")
                    for file in saved_files:
                        print(f"   📄 {file}")
            
            # Show performance metrics
            if response.performance:
                perf = response.performance
                print(f"\n📊 Performance: {perf.token_count} tokens, "
                      f"{perf.response_time:.2f}s, {perf.tokens_per_second:.1f} tokens/s")
        else:
            print(f"❌ Error: {response.error_message}")
    
    def _handle_recursive_improvement(self, code: str) -> None:
        """Handle recursive code improvement."""
        print("🔄 Starting recursive code improvement...")
        
        improvements = self.engine.improve_code_recursively(code)
        
        for i, improvement in enumerate(improvements, 1):
            print(f"\n🔄 Iteration {i}:")
            print("-" * 40)
            print(improvement.content[:300] + "..." if len(improvement.content) > 300 else improvement.content)
            print("-" * 40)
        
        if improvements:
            save_choice = input("\n💾 Save improvement results? (y/n): ").lower()
            if save_choice in ['y', 'yes']:
                # Save the final improved version
                final_improvement = improvements[-1]
                if final_improvement.code_blocks:
                    saved_files = self.engine.save_code_blocks(
                        final_improvement.code_blocks, 
                        "improved_code"
                    )
                    print(f"✅ {len(saved_files)} files saved!")
        else:
            print("⚠️ No improvements generated. Please check your input.")
    
    def _handle_task_breakdown(self, task_description: str) -> None:
        """Handle task breakdown/decomposition."""
        print("📋 Analyzing and breaking down task...")
        
        result = self.engine.break_down_task(task_description)
        
        if result.success:
            print("\n📋 TASK BREAKDOWN:")
            print("="*60)
            print(result.content)
            print("="*60)
            
            if result.code_blocks:
                save_choice = input("\n💾 Save breakdown analysis? (y/n): ").lower()
                if save_choice in ['y', 'yes']:
                    saved_files = self.engine.save_code_blocks(result.code_blocks, "task_breakdown")
                    print(f"✅ {len(saved_files)} files saved!")
        else:
            print(f"❌ Task breakdown failed: {result.error_message}")
    
    def _show_help(self) -> None:
        """Show detailed help information."""
        help_text = """
🔧 ADVANCED AUTO CODER SYSTEM - HELP

📋 BASIC COMMANDS:
  • Type any natural language request to generate code
  • Example: "Create a Python web scraper for product data"
  
🔄 SPECIAL COMMANDS:
  • improve: <code>     - Recursively improve existing code
  • breakdown: <task>   - Break complex projects into subtasks
  • clear              - Clear conversation history
  • help               - Show this help
  • exit/quit          - Exit the program

💡 TIPS FOR BETTER RESULTS:
  • Be specific about requirements and technologies
  • Mention the programming language you prefer
  • Include context about the project's purpose
  • Specify any constraints or special requirements

📖 EXAMPLES:
  → "Build a FastAPI REST API with JWT authentication"
  → "improve: def calculate_average(numbers): return sum(numbers)/len(numbers)"
  → "breakdown: Create a blog platform with React and Node.js"

🎯 BEST PRACTICES:
  • Start with simple requests and iterate
  • Use the improve command to enhance generated code
  • Break down large projects using the breakdown command
  • Save important code snippets for future reference
        """
        print(help_text) 