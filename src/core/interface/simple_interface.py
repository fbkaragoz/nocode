"""
Simple Interface - Clean and functional terminal interface.
Shows system status and code generation in a clean layout.
"""

import logging
import time
from typing import Dict, Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .rich_formatter import RichFormatter


logger = logging.getLogger(__name__)


class SimpleInterface:
    """
    Simple Interface - Clean terminal interface with status bar.
    
    Layout:
    ┌─────────────────────────────────────────────────────────────┐
    │                    System Status Bar                        │
    ├─────────────────────────────────────────────────────────────┤
    │                                                             │
    │                    Main Content Area                        │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
    """
    
    def __init__(self):
        """Initialize simple interface."""
        self.console = Console()
        self.formatter = RichFormatter()
        
        # Status tracking
        self.current_metrics = {}
        self.last_status_update = 0
        self.is_active = True
        
        logger.info("Simple interface initialized")
    
    def initialize(self):
        """Initialize the interface."""
        try:
            self.console.clear()
            self._show_header()
            logger.info("Simple interface started")
            
        except Exception as e:
            logger.error(f"Failed to initialize interface: {e}")
    
    def show_welcome(self, welcome_data: Dict[str, Any]):
        """Show welcome message."""
        try:
            welcome_panel = self.formatter.format_welcome_screen(welcome_data)
            self.console.print(welcome_panel)
            self.console.print()
            
        except Exception as e:
            logger.error(f"Failed to show welcome: {e}")
    
    def get_input(self, prompt_text: str = "") -> Optional[str]:
        """Get user input with status bar."""
        try:
            # Update status before input
            self._update_status_bar()
            
            # Get input
            prompt = f"\n[cyan]>[/cyan] {prompt_text or 'What would you like me to code?'}: "
            user_input = self.console.input(prompt)
            
            return user_input
            
        except (EOFError, KeyboardInterrupt):
            return None
        except Exception as e:
            logger.error(f"Input error: {e}")
            return None
    
    def show_code_generation(self, code_content: str, language: str = "python", real_time: bool = True):
        """Show generated code."""
        try:
            code_panel = Panel(
                self.formatter.format_code_block(code_content, language),
                title=f"Generated {language.title()} Code",
                border_style="green"
            )
            self.console.print(code_panel)
            
        except Exception as e:
            logger.error(f"Failed to show code: {e}")
    
    def show_progress(self, progress_percent: float, status_message: str = ""):
        """Show progress."""
        try:
            # Simple progress indicator
            progress_text = f"Progress: {progress_percent:.1f}%"
            if status_message:
                progress_text += f" - {status_message}"
            
            self.console.print(f"[yellow]{progress_text}[/yellow]", end="\r")
            
        except Exception as e:
            logger.error(f"Failed to show progress: {e}")
    
    def update_system_metrics(self, metrics: Dict[str, Any]):
        """Update system metrics."""
        try:
            self.current_metrics = metrics
            
            # Only update status bar every 5 seconds to avoid spam
            current_time = time.time()
            if current_time - self.last_status_update > 5:
                self._update_status_bar()
                self.last_status_update = current_time
            
        except Exception as e:
            logger.error(f"Failed to update metrics: {e}")
    
    def show_error(self, error_message: str):
        """Show error message."""
        try:
            error_panel = Panel(
                f"[red]{error_message}[/red]",
                title="Error",
                border_style="red"
            )
            self.console.print(error_panel)
            
        except Exception as e:
            logger.error(f"Failed to show error: {e}")
    
    def show_success(self, success_message: str):
        """Show success message."""
        try:
            success_panel = Panel(
                f"[green]{success_message}[/green]",
                title="Success",
                border_style="green"
            )
            self.console.print(success_panel)
            
        except Exception as e:
            logger.error(f"Failed to show success: {e}")
    
    def show_info(self, info_message: str):
        """Show info message."""
        try:
            self.console.print(f"[blue]Info: {info_message}[/blue]")
            
        except Exception as e:
            logger.error(f"Failed to show info: {e}")
    
    def show_goodbye(self, summary: Dict[str, Any]):
        """Show goodbye message."""
        try:
            goodbye_panel = Panel(
                self.formatter.format_session_summary(summary),
                title="Session Complete",
                border_style="bright_magenta"
            )
            self.console.print(goodbye_panel)
            
        except Exception as e:
            logger.error(f"Failed to show goodbye: {e}")
    
    def clear_screen(self):
        """Clear screen."""
        try:
            self.console.clear()
            self._show_header()
            
        except Exception as e:
            logger.error(f"Failed to clear screen: {e}")
    
    def cleanup(self):
        """Cleanup resources."""
        try:
            self.is_active = False
            logger.info("Simple interface cleaned up")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    def _show_header(self):
        """Show system header."""
        header_text = Text()
        header_text.append("AI Code Generation System", style="bold bright_blue")
        header_text.append(" - Ready", style="dim")
        
        self.console.print(header_text)
        self.console.print("─" * 80, style="dim")
    
    def _update_status_bar(self):
        """Update system status bar."""
        try:
            if not self.current_metrics:
                return
            
            # Create status table
            status_table = Table.grid(padding=1)
            status_table.add_column(style="cyan")
            status_table.add_column(style="green")
            status_table.add_column(style="yellow")
            status_table.add_column(style="blue")
            status_table.add_column(style="magenta")
            
            status_table.add_row(
                f"Memory: {self.current_metrics.get('memory_usage_mb', 0)}MB",
                f"CPU: {self.current_metrics.get('cpu_usage_percent', 0)}%",
                f"Turns: {self.current_metrics.get('conversation_turns', 0)}",
                f"Status: {self.current_metrics.get('model_status', 'Unknown')}",
                f"Uptime: {self.current_metrics.get('uptime', '0m 0s')}"
            )
            
            status_panel = Panel(
                status_table,
                title="System Status",
                border_style="dim",
                height=3
            )
            
            # Print status and move cursor back
            self.console.print(status_panel)
            
        except Exception as e:
            logger.error(f"Failed to update status bar: {e}") 