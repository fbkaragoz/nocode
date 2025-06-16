"""
Split Terminal Interface - Vertical split terminal with dual panes.
Provides separate areas for interaction and system monitoring.
"""

import logging
import os
from typing import Dict, Any, Optional
from threading import Lock

from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.table import Table

from .rich_formatter import RichFormatter


logger = logging.getLogger(__name__)


class SplitTerminalInterface:
    """
    Split Terminal Interface - Vertical dual pane terminal.
    
    Layout:
    +-------------------+-------------------+
    |                   |                   |
    |   Main Panel      |   System Panel    |
    |   - User Input    |   - System Metrics|
    |   - Code Output   |   - Logs          |
    |   - Messages      |   - Progress      |
    |                   |                   |
    +-------------------+-------------------+
    """
    
    def __init__(self):
        """Initialize split terminal interface."""
        self.console = Console()
        self.formatter = RichFormatter()
        
        # Create layout
        self.layout = Layout()
        self.layout.split_row(
            Layout(name="main", ratio=2),
            Layout(name="system", ratio=1)
        )
        
        # Main panel content
        self.main_content = []
        self.system_content = []
        
        # Live display
        self.live_display = None
        self.is_active = False
        
        # Thread safety
        self.update_lock = Lock()
        
        # System metrics
        self.current_metrics = {}
        
        logger.info("Split terminal interface initialized")
    
    def initialize(self):
        """Initialize the split interface."""
        try:
            # Setup initial layout
            self._setup_initial_layout()
            
            # Start live display
            self.live_display = Live(
                self.layout,
                refresh_per_second=4,
                screen=True
            )
            self.live_display.start()
            self.is_active = True
            
            logger.info("Split terminal interface started")
            
        except Exception as e:
            logger.error(f"Failed to initialize split interface: {e}")
    
    def show_welcome(self, welcome_data: Dict[str, Any]):
        """Show welcome message in main panel."""
        try:
            welcome_panel = self.formatter.format_welcome_screen(welcome_data)
            self._update_main_panel(welcome_panel)
            
        except Exception as e:
            logger.error(f"Failed to show welcome: {e}")
    
    def get_input(self, prompt_text: str = "") -> Optional[str]:
        """Get user input with prompt."""
        try:
            if not self.is_active:
                return input(prompt_text or "Input: ")
            
            # Temporarily stop live display for input
            if self.live_display:
                self.live_display.stop()
            
            # Get input
            user_input = input(f"\n{prompt_text or 'What would you like me to code?'}: ")
            
            # Restart live display
            if self.live_display:
                self.live_display.start()
            
            # Add input to main panel history
            self._add_to_main_history(f"User: {user_input}")
            
            return user_input
            
        except (EOFError, KeyboardInterrupt):
            return None
        except Exception as e:
            logger.error(f"Input error: {e}")
            return None
    
    def show_code_generation(self, code_content: str, language: str = "python", real_time: bool = True):
        """Show generated code in main panel."""
        try:
            code_panel = Panel(
                self.formatter.format_code_block(code_content, language),
                title=f"Generated {language.title()} Code",
                border_style="green"
            )
            self._update_main_panel(code_panel)
            
        except Exception as e:
            logger.error(f"Failed to show code: {e}")
    
    def show_progress(self, progress_percent: float, status_message: str = ""):
        """Show progress in system panel."""
        try:
            progress_info = f"Progress: {progress_percent:.1f}%"
            if status_message:
                progress_info += f" - {status_message}"
            
            self._update_system_panel("progress", progress_info)
            
        except Exception as e:
            logger.error(f"Failed to show progress: {e}")
    
    def update_system_metrics(self, metrics: Dict[str, Any]):
        """Update system metrics in system panel."""
        try:
            with self.update_lock:
                self.current_metrics = metrics
                self._refresh_system_panel()
            
        except Exception as e:
            logger.error(f"Failed to update metrics: {e}")
    
    def show_error(self, error_message: str):
        """Show error in main panel."""
        try:
            error_panel = Panel(
                f"[red]{error_message}[/red]",
                title="Error",
                border_style="red"
            )
            self._update_main_panel(error_panel)
            
        except Exception as e:
            logger.error(f"Failed to show error: {e}")
    
    def show_success(self, success_message: str):
        """Show success message in main panel."""
        try:
            success_panel = Panel(
                f"[green]{success_message}[/green]",
                title="Success",
                border_style="green"
            )
            self._update_main_panel(success_panel)
            
        except Exception as e:
            logger.error(f"Failed to show success: {e}")
    
    def show_info(self, info_message: str):
        """Show info message in main panel."""
        try:
            self._add_to_main_history(f"Info: {info_message}")
            
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
            self._update_main_panel(goodbye_panel)
            
        except Exception as e:
            logger.error(f"Failed to show goodbye: {e}")
    
    def clear_screen(self):
        """Clear main panel."""
        try:
            self.main_content.clear()
            self._update_main_panel(Panel("Ready for new input", title="Cleared"))
            
        except Exception as e:
            logger.error(f"Failed to clear screen: {e}")
    
    def cleanup(self):
        """Cleanup interface resources."""
        try:
            if self.live_display:
                self.live_display.stop()
                self.live_display = None
            
            self.is_active = False
            logger.info("Split terminal interface cleaned up")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    def _setup_initial_layout(self):
        """Setup the initial layout structure."""
        # Main panel initial content
        main_panel = Panel(
            "Ready to generate code...",
            title="Main Interface",
            border_style="blue"
        )
        
        # System panel initial content
        system_panel = self._create_system_panel()
        
        self.layout["main"].update(main_panel)
        self.layout["system"].update(system_panel)
    
    def _create_system_panel(self) -> Panel:
        """Create system monitoring panel."""
        try:
            # Create system metrics table
            table = Table(title="System Status", show_header=False, box=None)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            # Add metrics
            metrics = self.current_metrics
            table.add_row("Memory", f"{metrics.get('memory_usage_mb', 0)}MB")
            table.add_row("CPU", f"{metrics.get('cpu_usage_percent', 0)}%")
            table.add_row("Turns", str(metrics.get('conversation_turns', 0)))
            table.add_row("Model", metrics.get('model_name', 'N/A')[:20])
            
            return Panel(
                table,
                title="System Monitor",
                border_style="yellow"
            )
            
        except Exception as e:
            logger.error(f"Failed to create system panel: {e}")
            return Panel("System panel error", border_style="red")
    
    def _update_main_panel(self, content):
        """Update main panel with new content."""
        try:
            with self.update_lock:
                self.layout["main"].update(content)
            
        except Exception as e:
            logger.error(f"Failed to update main panel: {e}")
    
    def _update_system_panel(self, key: str, value: str):
        """Update specific system panel information."""
        try:
            # Store the update
            if not hasattr(self, 'system_updates'):
                self.system_updates = {}
            
            self.system_updates[key] = value
            self._refresh_system_panel()
            
        except Exception as e:
            logger.error(f"Failed to update system panel: {e}")
    
    def _refresh_system_panel(self):
        """Refresh the entire system panel."""
        try:
            system_panel = self._create_system_panel()
            with self.update_lock:
                self.layout["system"].update(system_panel)
            
        except Exception as e:
            logger.error(f"Failed to refresh system panel: {e}")
    
    def _add_to_main_history(self, message: str):
        """Add message to main panel history."""
        try:
            self.main_content.append(message)
            
            # Keep only last 50 messages
            self.main_content = self.main_content[-50:]
            
            # Update display with recent history
            history_text = "\n".join(self.main_content[-10:])  # Show last 10
            history_panel = Panel(
                history_text,
                title="Conversation History",
                border_style="blue"
            )
            self._update_main_panel(history_panel)
            
        except Exception as e:
            logger.error(f"Failed to add to history: {e}") 