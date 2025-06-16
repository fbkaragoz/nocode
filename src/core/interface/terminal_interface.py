"""
Terminal Interface - Main UI coordination and management.
Handles all terminal interface interactions with real-time streaming.
"""

import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from .split_terminal import SplitTerminalInterface
from .rich_formatter import RichFormatter


logger = logging.getLogger(__name__)


class TerminalInterface:
    """
    Terminal Interface - Clean UI architecture.
    
    Responsibilities:
    - Coordinate terminal UI components
    - Handle user input and display
    - Manage real-time streaming display
    - Provide consistent UI experience
    """
    
    def __init__(self, interface_type: str = "enhanced"):
        """Initialize terminal interface with specified type."""
        self.interface_type = interface_type
        self.console = Console()
        self.formatter = RichFormatter()
        
        # Interface components based on type
        if interface_type == "split":
            self.split_interface = SplitTerminalInterface()
            self.use_split_interface = True
        else:
            self.split_interface = None
            self.use_split_interface = False
        
        # Display state
        self.live_display = None
        self.current_progress = None
        self.is_streaming = False
        
        # UI Configuration
        self.ui_config = {
            'show_timestamps': True,
            'show_progress': True,
            'syntax_highlighting': True,
            'auto_scroll': True,
            'max_display_lines': 50
        }
    
    def initialize(self):
        """Initialize the terminal interface."""
        try:
            # Clear screen
            self.console.clear()
            
            # Initialize split interface if needed
            if self.use_split_interface and self.split_interface:
                self.split_interface.initialize()
                return
            
            # Show initialization message
            self._show_init_message()
            
            logger.info("Terminal interface initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize terminal interface: {e}")
            raise
    
    def show_welcome(self, welcome_data: Dict[str, Any]):
        """Show welcome screen with system information."""
        try:
            if self.use_split_interface:
                self.split_interface.show_welcome(welcome_data)
                return
            
            # Create welcome panel
            welcome_content = self.formatter.format_welcome(welcome_data)
            
            welcome_panel = Panel(
                welcome_content,
                title="🚀 Welcome to Advanced AI Code Generation System",
                border_style="bright_blue",
                padding=(1, 2)
            )
            
            self.console.print(welcome_panel)
            self.console.print()  # Add spacing
            
        except Exception as e:
            logger.error(f"Failed to show welcome: {e}")
    
    def get_input(self, prompt_text: str = "") -> Optional[str]:
        """Get user input with proper prompt handling."""
        try:
            if self.use_split_interface:
                return self.split_interface.get_input(prompt_text)
            
            # Default prompt if none provided
            if not prompt_text:
                prompt_text = "[bold cyan]💭 What would you like me to code?[/bold cyan]"
            
            # Get input with rich prompt
            user_input = Prompt.ask(prompt_text, console=self.console)
            return user_input.strip() if user_input else None
            
        except KeyboardInterrupt:
            raise
        except Exception as e:
            logger.error(f"Failed to get user input: {e}")
            return None
    
    def show_code_generation(self, code_content: str, language: str = "python", real_time: bool = True):
        """Show code generation with real-time streaming if enabled."""
        try:
            if self.use_split_interface:
                self.split_interface.show_code_generation(code_content, language, real_time)
                return
            
            if real_time and not self.is_streaming:
                self._start_real_time_display()
            
            # Format and display code
            formatted_code = self.formatter.format_code(code_content, language)
            
            code_panel = Panel(
                formatted_code,
                title=f"📝 Generated {language.title()} Code",
                border_style="green",
                padding=(1, 2)
            )
            
            if self.live_display:
                self.live_display.update(code_panel)
            else:
                self.console.print(code_panel)
            
        except Exception as e:
            logger.error(f"Failed to show code generation: {e}")
    
    def stream_code_chunk(self, chunk: str, chunk_type: str = "code"):
        """Stream a chunk of code in real-time."""
        try:
            if self.use_split_interface:
                self.split_interface.stream_code_chunk(chunk, chunk_type)
                return
            
            # Handle streaming display
            if not self.is_streaming:
                self._start_real_time_display()
            
            # Process chunk based on type
            if chunk_type == "progress":
                self._update_progress_display(chunk)
            elif chunk_type == "status":
                self._update_status_display(chunk)
            else:
                self._update_code_display(chunk)
                
        except Exception as e:
            logger.error(f"Failed to stream code chunk: {e}")
    
    def update_system_metrics(self, metrics: Dict[str, Any]):
        """Update system metrics display."""
        try:
            if self.use_split_interface:
                self.split_interface.update_system_metrics(metrics)
                return
            
            # Store metrics silently - no continuous output
            self.current_metrics = metrics
                
        except Exception as e:
            logger.error(f"Failed to update system metrics: {e}")
    
    def show_progress(self, progress_percent: float, status_message: str = ""):
        """Show progress with progress bar."""
        try:
            if self.use_split_interface:
                self.split_interface.show_progress(progress_percent, status_message)
                return
            
            # Create or update progress display
            if not self.current_progress:
                self.current_progress = Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    console=self.console
                )
                self.progress_task = self.current_progress.add_task(
                    status_message or "Processing...", 
                    total=100
                )
            
            # Update progress
            self.current_progress.update(
                self.progress_task,
                completed=progress_percent,
                description=status_message or "Processing..."
            )
            
            # Show progress if not in live mode
            if not self.live_display:
                self.current_progress.refresh()
                
        except Exception as e:
            logger.error(f"Failed to show progress: {e}")
    
    def show_error(self, error_message: str):
        """Show error message with proper formatting."""
        try:
            if self.use_split_interface:
                self.split_interface.show_error(error_message)
                return
            
            error_panel = Panel(
                f"[red]❌ {error_message}[/red]",
                title="Error",
                border_style="red",
                padding=(0, 1)
            )
            
            self.console.print(error_panel)
            
        except Exception as e:
            logger.error(f"Failed to show error: {e}")
    
    def show_success(self, success_message: str):
        """Show success message with proper formatting."""
        try:
            if self.use_split_interface:
                self.split_interface.show_success(success_message)
                return
            
            success_panel = Panel(
                f"[green]✅ {success_message}[/green]",
                title="Success",
                border_style="green",
                padding=(0, 1)
            )
            
            self.console.print(success_panel)
            
        except Exception as e:
            logger.error(f"Failed to show success: {e}")
    
    def show_info(self, info_message: str):
        """Show informational message."""
        try:
            if self.use_split_interface:
                self.split_interface.show_info(info_message)
                return
            
            self.console.print(f"[blue]ℹ️ {info_message}[/blue]")
            
        except Exception as e:
            logger.error(f"Failed to show info: {e}")
    
    def show_goodbye(self, summary: Dict[str, Any]):
        """Show goodbye message with session summary."""
        try:
            if self.use_split_interface:
                self.split_interface.show_goodbye(summary)
                return
            
            # Format summary
            summary_content = self.formatter.format_session_summary(summary)
            
            goodbye_panel = Panel(
                summary_content,
                title="👋 Session Complete",
                border_style="bright_magenta",
                padding=(1, 2)
            )
            
            self.console.print(goodbye_panel)
            
        except Exception as e:
            logger.error(f"Failed to show goodbye: {e}")
    
    def clear_screen(self):
        """Clear the terminal screen."""
        try:
            if self.use_split_interface:
                self.split_interface.clear_screen()
                return
            
            self.console.clear()
            
        except Exception as e:
            logger.error(f"Failed to clear screen: {e}")
    
    def cleanup(self):
        """Cleanup interface resources."""
        try:
            # Stop live display if active
            if self.live_display:
                self.live_display.stop()
                self.live_display = None
            
            # Stop progress if active
            if self.current_progress:
                self.current_progress.stop()
                self.current_progress = None
            
            # Cleanup split interface
            if self.use_split_interface and self.split_interface:
                self.split_interface.cleanup()
            
            self.is_streaming = False
            
            logger.info("Terminal interface cleaned up")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    def _start_real_time_display(self):
        """Start real-time display mode."""
        try:
            if self.is_streaming:
                return
            
            self.is_streaming = True
            
            # Create live display for real-time updates
            initial_content = Panel(
                "[yellow]🔄 Initializing code generation...[/yellow]",
                title="Real-time Code Generation",
                border_style="yellow"
            )
            
            self.live_display = Live(
                initial_content,
                console=self.console,
                refresh_per_second=4,
                auto_refresh=True
            )
            
            self.live_display.start()
            
        except Exception as e:
            logger.error(f"Failed to start real-time display: {e}")
    
    def _update_code_display(self, chunk: str):
        """Update code display with new chunk."""
        # This would accumulate chunks and update the display
        # Implementation depends on how chunks are structured
        pass
    
    def _update_progress_display(self, progress_info: str):
        """Update progress display."""
        # Parse progress info and update display
        pass
    
    def _update_status_display(self, status: str):
        """Update status display."""
        if self.live_display:
            status_panel = Panel(
                f"[cyan]{status}[/cyan]",
                title="Status",
                border_style="cyan"
            )
            self.live_display.update(status_panel)
    
    def _show_init_message(self):
        """Show initialization message."""
        init_text = Text()
        init_text.append("Advanced AI Code Generation System", style="bold bright_blue")
        init_text.append(" - Initializing...", style="dim")
        
        self.console.print(init_text)
        self.console.print() 