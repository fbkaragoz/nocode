"""
Display Manager - Professional UI coordination and management.
Handles all user interface interactions with a clean, modular architecture.
"""

import logging
import os
import subprocess
from typing import Optional, Iterator
from enum import Enum
from dataclasses import dataclass

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.markdown import Markdown
from rich.prompt import Prompt

from .formatter import UIFormatter


logger = logging.getLogger(__name__)


class DisplayMode(Enum):
    """Display mode enumeration."""
    STANDARD = "standard"
    ANALYTICS = "analytics"
    MINIMAL = "minimal"


class AIState(Enum):
    """AI processing state enumeration."""
    IDLE = "💭 Ready"
    THINKING = "🤔 Thinking..."
    CODING = "⚡ Coding..."
    COMPLETE = "✅ Complete"


@dataclass
class DisplayConfig:
    """Display configuration."""
    mode: DisplayMode = DisplayMode.ANALYTICS # Default to analytics
    refresh_rate: int = 10 # For live display


class AnalyticsDisplay:
    """Analytics display component for system monitoring."""
    
    def __init__(self, console: Console):
        self.console = console
        self.process = None
    
    def initialize(self) -> bool:
        """Initialize analytics display in a separate terminal."""
        try:
            script_path = os.path.join('src', 'core', 'interface', 'analytics_terminal.py')
            if not os.path.exists(script_path):
                logger.error(f"Analytics terminal module not found: {script_path}")
                return False

            terminals = [
                ['gnome-terminal', '--title=Nocode-Analytics', '--', 'python3', script_path],
                ['konsole', '--title', 'Nocode-Analytics', '-e', 'python3', script_path],
                ['xterm', '-title', 'Nocode-Analytics', '-e', 'python3', script_path]
            ]
            
            for terminal_cmd in terminals:
                try:
                    self.process = subprocess.Popen(
                        terminal_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                    logger.info(f"Analytics display launched with: {terminal_cmd[0]}")
                    return True
                except FileNotFoundError:
                    continue
            
            logger.warning("No suitable terminal emulator found for analytics display.")
            return False
            
        except Exception as e:
            logger.error(f"Failed to initialize analytics display: {e}")
            return False
    
    def cleanup(self) -> None:
        """Cleanup analytics display."""
        if self.process:
            self.process.terminate()


class DisplayManager:
    """
    Handles all UI interactions, including real-time streaming display.
    """
    
    def __init__(self, config: DisplayConfig = None):
        """Initialize display manager."""
        self.config = config or DisplayConfig()
        self.console = Console()
        self.formatter = UIFormatter()
        self.analytics_display = None
        self.ai_state = AIState.IDLE
        
        logger.info(f"Display manager initialized in {self.config.mode.value} mode.")
    
    def initialize(self) -> bool:
        """Initialize the display manager and components."""
        self.console.clear()
        if self.config.mode == DisplayMode.ANALYTICS:
            self.analytics_display = AnalyticsDisplay(self.console)
            if not self.analytics_display.initialize():
                self.console.print("[yellow]⚠️ Analytics display failed to launch.[/yellow]")
        
        self._show_initialization_message()
        return True
            
    def set_ai_state(self, state: AIState):
        """Set and display the current AI processing state."""
        self.ai_state = state
        self.console.print(f"[dim]{state.value}[/dim]")

    def get_user_input(self, prompt: str = "What would you like to code?") -> Optional[str]:
        """Get user input."""
        self.set_ai_state(AIState.IDLE)
        try:
            return Prompt.ask(f"[bold cyan]💭 {prompt}[/bold cyan]", console=self.console)
        except KeyboardInterrupt:
            return None
    
    def stream_content(self, stream: Iterator[str]) -> str:
        """Display content from a stream with live updates."""
        full_response = ""
        panel = Panel("", title="⚡ Coding...", border_style="green", padding=(1, 2))
        
        try:
            with Live(panel, console=self.console, refresh_per_second=self.config.refresh_rate, vertical_overflow="visible") as live:
                self.set_ai_state(AIState.CODING)
                for chunk in stream:
                    full_response += chunk
                    # Use Markdown to render code blocks correctly
                    live.update(Markdown(full_response, style="code"))
            
            # Final update to ensure all content is displayed
            self.console.print(Panel(Markdown(full_response), title="✅ Complete", border_style="green", padding=(1, 2)))

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            self.show_error("Streaming failed", str(e))
            
        return full_response

    def show_success(self, message: str):
        """Show a success message panel."""
        self.console.print(Panel(f"✅ {message}", title="Success", border_style="green", padding=(1, 1)))

    def show_error(self, error_message: str, details: str = None):
        """Show an error message panel."""
        error_content = f"❌ {error_message}"
        if details:
            error_content += f"\n[dim]{details}[/dim]"
        self.console.print(Panel(error_content, title="Error", border_style="red", padding=(1, 2)))

    def show_goodbye(self):
        """Show a goodbye message."""
        self.console.print("\n👋 Goodbye!")

    def cleanup(self):
        """Cleanup display resources."""
        if self.analytics_display:
            self.analytics_display.cleanup()
        logger.info("Display manager cleaned up.")
    
    def _show_initialization_message(self):
        """Show the initial welcome message."""
        init_text = Text("AI Code Generation System", style="bold bright_blue")
        if self.config.mode == DisplayMode.ANALYTICS:
            init_text.append(" + Analytics Dashboard", style="dim green")
        
        self.console.print(init_text)
        self.console.print("─" * 60, style="dim") 