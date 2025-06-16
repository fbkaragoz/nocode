"""
Command Processor - Handles all user command processing.
Clean separation of command logic and execution.
"""

import logging
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass

from models.code_request import CodeRequest
from core.auto_coder import AutoCoderEngine
from core.streaming.stream_manager import StreamManager
from config.constants import PromptType


logger = logging.getLogger(__name__)


@dataclass
class CommandResult:
    """Result of command processing."""
    success: bool
    message: str = ""
    should_exit: bool = False
    tokens_generated: int = 0
    performance_metrics: Dict[str, Any] = None
    generated_code: Optional[str] = None


class CommandProcessor:
    """
    Command Processor - Clean command handling architecture.
    
    Responsibilities:
    - Parse and validate user commands
    - Delegate to appropriate handlers
    - Track performance metrics
    - Handle errors gracefully
    """
    
    def __init__(self, engine: AutoCoderEngine, stream_manager: StreamManager):
        """Initialize command processor with dependencies."""
        self.engine = engine
        self.stream_manager = stream_manager
        
        # Command registry
        self.commands = {
            'generate': self._handle_generate_command,
            'improve': self._handle_improve_command,
            'breakdown': self._handle_breakdown_command,
            'explain': self._handle_explain_command,
            'help': self._handle_help_command,
            'clear': self._handle_clear_command,
            'exit': self._handle_exit_command,
            'quit': self._handle_exit_command
        }
        
        # Performance tracking
        self.last_command_time = 0
        self.command_history = []
    
    def process_command(self, user_input: str) -> CommandResult:
        """Process user command with clean error handling."""
        try:
            # Parse command
            command, args = self._parse_input(user_input)
            
            # Validate command
            if not self._validate_command(command):
                return CommandResult(
                    success=False,
                    message=f"Unknown command: {command}. Type 'help' for available commands."
                )
            
            # Track command
            self._track_command(command, args)
            
            # Execute command
            start_time = time.time()
            result = self.commands[command](args)
            execution_time = time.time() - start_time
            
            # Add performance metrics
            if result.performance_metrics is None:
                result.performance_metrics = {}
            result.performance_metrics['execution_time'] = execution_time
            
            return result
            
        except Exception as e:
            logger.error(f"Command processing error: {e}")
            return CommandResult(
                success=False,
                message=f"Error processing command: {e}"
            )
    
    def _parse_input(self, user_input: str) -> tuple[str, str]:
        """Parse user input into command and arguments."""
        user_input = user_input.strip()
        
        if not user_input:
            return "help", ""
        
        # Check for prefixed commands
        if ':' in user_input:
            parts = user_input.split(':', 1)
            if len(parts) == 2:
                command = parts[0].strip().lower()
                args = parts[1].strip()
                if command in self.commands:
                    return command, args
        
        # Check for direct commands
        parts = user_input.split(' ', 1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        # If not a recognized command, treat as generate
        if command not in self.commands:
            return "generate", user_input
        
        return command, args
    
    def _validate_command(self, command: str) -> bool:
        """Validate if command exists."""
        return command in self.commands
    
    def _track_command(self, command: str, args: str):
        """Track command for analytics."""
        self.command_history.append({
            'command': command,
            'args': args[:100],  # Truncate long args
            'timestamp': time.time()
        })
        
        # Keep only last 50 commands
        self.command_history = self.command_history[-50:]
    
    def _handle_generate_command(self, args: str) -> CommandResult:
        """Handle code generation command."""
        if not args.strip():
            return CommandResult(
                success=False,
                message="Please provide a description of what you want to generate."
            )
        
        try:
            # Create request
            request = CodeRequest(
                description=args,
                prompt_type=PromptType.GENERATE,
                language="auto-detect"
            )
            
            # Start streaming process
            self.stream_manager.start_streaming_session()
            
            # Generate code with streaming
            start_time = time.time()
            response = self.engine.generate_code(request)
            execution_time = time.time() - start_time
            
            # Save code blocks to files
            saved_files = []
            if response.success and response.code_blocks:
                task_name = args[:30].replace(' ', '_').replace('/', '_')  # Clean task name
                saved_files = self.engine.save_code_blocks(response.code_blocks, task_name)
            
            # Calculate performance metrics
            tokens_generated = len(response.generated_code.split()) if response.generated_code else 0
            tokens_per_second = tokens_generated / execution_time if execution_time > 0 else 0
            
            success_message = f"Code generated successfully!"
            if saved_files:
                success_message += f"\nSaved to: {', '.join(saved_files)}"
            
            return CommandResult(
                success=True,
                message=success_message,
                tokens_generated=tokens_generated,
                generated_code=response.generated_code,
                performance_metrics={
                    'response_time': execution_time,
                    'tokens_per_second': tokens_per_second,
                    'confidence': response.confidence,
                    'model_used': self.engine.settings.model_name,
                    'files_saved': len(saved_files)
                }
            )
            
        except Exception as e:
            logger.error(f"Generate command error: {e}")
            return CommandResult(
                success=False,
                message=f"Code generation failed: {e}"
            )
        finally:
            self.stream_manager.end_streaming_session()
    
    def _handle_improve_command(self, args: str) -> CommandResult:
        """Handle code improvement command."""
        if not args.strip():
            return CommandResult(
                success=False,
                message="Please provide code to improve or description of improvements needed."
            )
        
        try:
            request = CodeRequest(
                description=f"Improve this code: {args}",
                prompt_type=PromptType.IMPROVE,
                language="auto-detect"
            )
            
            self.stream_manager.start_streaming_session()
            
            start_time = time.time()
            response = self.engine.generate_code(request)
            execution_time = time.time() - start_time
            
            tokens_generated = len(response.generated_code.split()) if response.generated_code else 0
            
            return CommandResult(
                success=True,
                message="Code improved successfully!",
                tokens_generated=tokens_generated,
                generated_code=response.generated_code,
                performance_metrics={
                    'response_time': execution_time,
                    'tokens_per_second': tokens_generated / execution_time if execution_time > 0 else 0,
                    'confidence': response.confidence
                }
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Code improvement failed: {e}"
            )
        finally:
            self.stream_manager.end_streaming_session()
    
    def _handle_breakdown_command(self, args: str) -> CommandResult:
        """Handle task breakdown command."""
        if not args.strip():
            return CommandResult(
                success=False,
                message="Please provide a task to break down."
            )
        
        try:
            request = CodeRequest(
                description=f"Break down this task into steps: {args}",
                prompt_type=PromptType.BREAKDOWN,
                language="markdown"
            )
            
            self.stream_manager.start_streaming_session()
            
            start_time = time.time()
            response = self.engine.generate_code(request)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                message="Task breakdown generated!",
                generated_code=response.generated_code,
                performance_metrics={
                    'response_time': execution_time,
                    'confidence': response.confidence
                }
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Task breakdown failed: {e}"
            )
        finally:
            self.stream_manager.end_streaming_session()
    
    def _handle_explain_command(self, args: str) -> CommandResult:
        """Handle code explanation command."""
        if not args.strip():
            return CommandResult(
                success=False,
                message="Please provide code to explain."
            )
        
        try:
            request = CodeRequest(
                description=f"Explain this code: {args}",
                prompt_type=PromptType.EXPLAIN,
                language="markdown"
            )
            
            self.stream_manager.start_streaming_session()
            
            start_time = time.time()
            response = self.engine.generate_code(request)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                message="Code explanation generated!",
                generated_code=response.generated_code,
                performance_metrics={
                    'response_time': execution_time,
                    'confidence': response.confidence
                }
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Code explanation failed: {e}"
            )
        finally:
            self.stream_manager.end_streaming_session()
    
    def _handle_help_command(self, args: str) -> CommandResult:
        """Handle help command."""
        help_text = """
Advanced AI Code Generation System - Command Help

Available Commands:
────────────────────────────────────────────────────────────────────────────

Code Generation:
  generate <description>     Generate code from description
  improve <code>              Improve existing code
  breakdown <task>            Break down complex task into steps
  explain <code>              Explain how code works

Quick Commands:
  <description>               Direct code generation (no prefix needed)
  improve: <code>             Quick improve with colon syntax
  breakdown: <task>           Quick breakdown with colon syntax

System Commands:
  help                        Show this help message
  clear                       Clear the terminal
  exit/quit                   Exit the system

Tips:
  • You can describe what you want in natural language
  • The system supports multiple programming languages
  • Use 'improve:' for code enhancement
  • Use 'breakdown:' for project planning
  • All generated code is automatically saved to generated_code/

────────────────────────────────────────────────────────────────────────────
        """
        
        return CommandResult(
            success=True,
            message=help_text.strip()
        )
    
    def _handle_clear_command(self, args: str) -> CommandResult:
        """Handle clear screen command."""
        return CommandResult(
            success=True,
            message="CLEAR_SCREEN"  # Special message for interface
        )
    
    def _handle_exit_command(self, args: str) -> CommandResult:
        """Handle exit command."""
        return CommandResult(
            success=True,
            message="Goodbye! 👋",
            should_exit=True
        ) 