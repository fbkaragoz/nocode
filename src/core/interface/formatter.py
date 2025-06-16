"""
UI Formatter - Professional text and code formatting utilities.
Provides clean, consistent formatting for terminal display.
"""

import logging
from typing import Dict, Any, Optional

from rich.text import Text
from rich.table import Table
from rich.syntax import Syntax
from rich.panel import Panel
from rich.console import Console
from rich.markdown import Markdown


logger = logging.getLogger(__name__)


class UIFormatter:
    """
    Professional UI Formatter - Clean, consistent formatting.
    
    Responsibilities:
    - Format code with syntax highlighting
    - Create professional UI elements
    - Format data structures consistently
    - Handle text styling with professional themes
    """
    
    def __init__(self):
        """Initialize UI formatter."""
        self.console = Console()
        
        # Language mappings for syntax highlighting
        self.language_map = {
            'py': 'python',
            'js': 'javascript',
            'ts': 'typescript',
            'cpp': 'cpp',
            'c': 'c',
            'java': 'java',
            'go': 'go',
            'rs': 'rust',
            'rb': 'ruby',
            'php': 'php',
            'sh': 'bash',
            'sql': 'sql',
            'html': 'html',
            'css': 'css',
            'json': 'json',
            'yaml': 'yaml',
            'yml': 'yaml',
            'xml': 'xml',
            'md': 'markdown',
            'dockerfile': 'dockerfile',
            'makefile': 'makefile'
        }
        
        # Professional color scheme
        self.theme = {
            'primary': 'bright_blue',
            'secondary': 'cyan',
            'success': 'green',
            'warning': 'yellow',
            'error': 'red',
            'info': 'blue',
            'muted': 'dim white',
            'accent': 'bright_magenta'
        }
    
    def format_code(self, code: str, language: str = "python", theme: str = "monokai") -> Syntax:
        """Format code with professional syntax highlighting."""
        try:
            normalized_lang = self._normalize_language(language)
            
            syntax = Syntax(
                code,
                normalized_lang,
                theme=theme,
                line_numbers=True,
                word_wrap=True,
                background_color="default",
                indent_guides=True
            )
            
            return syntax
            
        except Exception as e:
            logger.error(f"Failed to format code: {e}")
            return Text(code)
    
    def format_welcome(self, welcome_data: Dict[str, Any]) -> Text:
        """Format professional welcome screen."""
        try:
            welcome_text = Text()
            
            # Title
            title = welcome_data.get('title', 'AI Code Generation System')
            welcome_text.append(f"🚀 {title}\n", style="bold bright_blue")
            
            # Version and model info
            version = welcome_data.get('version', '1.0.0')
            model = welcome_data.get('model', 'DeepSeek Coder')
            welcome_text.append(f"Version: {version} | Model: {model}\n\n", style="dim")
            
            # Mode information
            mode = welcome_data.get('interface_type', 'standard')
            welcome_text.append(f"Display Mode: {mode.title()}\n", style="cyan")
            
            # Features
            features = welcome_data.get('features', [])
            if features:
                welcome_text.append("✨ Active Features:\n", style="bright_yellow")
                for feature in features:
                    welcome_text.append(f"  • {feature}\n", style="white")
            
            welcome_text.append("\n[green]System ready for code generation![/green]", style="green")
            
            return welcome_text
            
        except Exception as e:
            logger.error(f"Failed to format welcome: {e}")
            return Text("Welcome to AI Code Generation System!")
    
    def format_session_summary(self, summary: Dict[str, Any]) -> Text:
        """Format professional session summary."""
        try:
            summary_text = Text()
            
            # Header
            summary_text.append("🎯 Session Summary\n\n", style="bold bright_magenta")
            
            # Key metrics
            conversations = summary.get('conversation_turns', 0)
            tokens = summary.get('total_tokens', 0)
            uptime = summary.get('uptime', '0s')
            model = summary.get('model_used', 'Unknown')
            
            # Format metrics professionally
            summary_text.append(f"💬 Conversations: {conversations}\n", style="cyan")
            summary_text.append(f"🔤 Tokens Generated: {tokens:,}\n", style="green")
            summary_text.append(f"⏱️  Session Duration: {uptime}\n", style="yellow")
            summary_text.append(f"🤖 Model: {model}\n\n", style="blue")
            
            summary_text.append("Thank you for using the AI Code Generation System!", style="bright_blue")
            
            return summary_text
            
        except Exception as e:
            logger.error(f"Failed to format session summary: {e}")
            return Text("Session completed successfully!")
    
    def format_system_metrics(self, metrics: Dict[str, Any]) -> Table:
        """Format system metrics in a professional table."""
        try:
            table = Table(title="🖥️ System Status", show_header=True, header_style="bold magenta")
            table.add_column("Resource", style="cyan", no_wrap=True)
            table.add_column("Usage", style="white")
            table.add_column("Status", justify="center")
            
            # Memory usage
            memory_mb = metrics.get('memory_usage_mb', 0)
            memory_status = self._get_status_indicator(memory_mb, [500, 1000])
            table.add_row("Memory", f"{memory_mb} MB", memory_status)
            
            # CPU usage
            cpu_percent = metrics.get('cpu_usage_percent', 0)
            cpu_status = self._get_status_indicator(cpu_percent, [50, 80])
            table.add_row("CPU", f"{cpu_percent}%", cpu_status)
            
            # Model connection
            model_connected = metrics.get('ollama_connected', False)
            model_status = "🟢 Connected" if model_connected else "🔴 Disconnected"
            table.add_row("Model Service", model_status, "")
            
            # Session info
            conversations = metrics.get('conversation_turns', 0)
            table.add_row("Conversations", str(conversations), "")
            
            uptime = metrics.get('uptime', '0s')
            table.add_row("Uptime", uptime, "")
            
            return table
            
        except Exception as e:
            logger.error(f"Failed to format system metrics: {e}")
            return Table()
    
    def format_error_message(self, error: str, context: str = None) -> Panel:
        """Format professional error message."""
        try:
            error_text = Text()
            error_text.append("❌ ", style="red")
            error_text.append(str(error), style="bold red")
            
            if context:
                error_text.append(f"\n\n💡 Context: {context}", style="dim")
            
            return Panel(
                error_text,
                title="Error",
                border_style="red",
                padding=(1, 2)
            )
            
        except Exception as e:
            logger.error(f"Failed to format error message: {e}")
            return Panel(f"Error: {error}", border_style="red")
    
    def format_progress_info(self, progress_info: Dict[str, Any]) -> Panel:
        """Format progress information professionally."""
        try:
            progress_text = Text()
            
            # Current stage
            stage = progress_info.get('stage', 'processing')
            progress_percent = progress_info.get('progress_percent', 0)
            status_message = progress_info.get('status_message', '')
            
            progress_text.append(f"Stage: {stage.title()}\n", style="bold cyan")
            progress_text.append(f"Progress: {progress_percent:.1f}%\n", style="green")
            
            if status_message:
                progress_text.append(f"Status: {status_message}\n", style="yellow")
            
            # Timing info
            elapsed = progress_info.get('elapsed_time', 0)
            remaining = progress_info.get('estimated_remaining', 0)
            
            if elapsed > 0:
                progress_text.append(f"\n⏱️  Elapsed: {elapsed:.1f}s\n", style="dim")
            if remaining > 0:
                progress_text.append(f"⏳ Remaining: {remaining:.1f}s", style="dim")
            
            return Panel(
                progress_text,
                title="📊 Progress",
                border_style="blue"
            )
            
        except Exception as e:
            logger.error(f"Failed to format progress info: {e}")
            return Panel("Progress information unavailable")
    
    def format_command_help(self, commands: Dict[str, str]) -> Table:
        """Format command help professionally."""
        try:
            table = Table(title="📚 Available Commands", show_header=True, header_style="bold blue")
            table.add_column("Command", style="cyan", no_wrap=True)
            table.add_column("Description", style="white")
            
            for command, description in commands.items():
                table.add_row(command, description)
            
            return table
            
        except Exception as e:
            logger.error(f"Failed to format command help: {e}")
            return Table()
    
    def format_code_explanation(self, explanation: str) -> Panel:
        """Format code explanation as professional markdown."""
        try:
            markdown_content = Markdown(explanation)
            
            return Panel(
                markdown_content,
                title="💡 Code Explanation",
                border_style="bright_yellow",
                padding=(1, 2)
            )
            
        except Exception as e:
            logger.error(f"Failed to format code explanation: {e}")
            return Panel(explanation, title="Code Explanation", border_style="yellow")
    
    def create_status_indicator(self, status: str, is_active: bool = True) -> Text:
        """Create professional status indicator."""
        indicator_text = Text()
        
        if is_active:
            indicator_text.append("🟢 ", style="green")
        else:
            indicator_text.append("🔴 ", style="red")
        
        indicator_text.append(status, style="bold" if is_active else "dim")
        
        return indicator_text
    
    def _normalize_language(self, language: str) -> str:
        """Normalize language name for syntax highlighting."""
        if not language:
            return "text"
        
        lang_lower = language.lower()
        
        # Check direct mapping
        if lang_lower in self.language_map:
            return self.language_map[lang_lower]
        
        # Check if it's already a valid language
        valid_languages = [
            'python', 'javascript', 'typescript', 'java', 'cpp', 'c', 'csharp',
            'go', 'rust', 'ruby', 'php', 'swift', 'kotlin', 'scala', 'bash',
            'sql', 'html', 'css', 'json', 'yaml', 'xml', 'markdown', 'text',
            'dockerfile', 'makefile', 'lua', 'r', 'matlab', 'powershell'
        ]
        
        if lang_lower in valid_languages:
            return lang_lower
        
        return "text"  # Fallback to plain text
    
    def _get_status_indicator(self, value: float, thresholds: list) -> str:
        """Get status indicator based on value and thresholds."""
        if len(thresholds) >= 2:
            if value < thresholds[0]:
                return "🟢 Normal"
            elif value < thresholds[1]:
                return "🟡 High"
            else:
                return "🔴 Critical"
        
        return "🟢 Normal" 