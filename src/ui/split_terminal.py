"""
Advanced split terminal interface using Rich library.
Provides real-time code generation visualization and system metrics.
"""

import threading
from typing import Dict, Any
from datetime import datetime
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.syntax import Syntax
from rich.align import Align


class SplitTerminalInterface:
    """Advanced split terminal interface for real-time code generation."""
    
    def __init__(self):
        """Initialize the split terminal interface."""
        self.console = Console()
        self.layout = Layout()
        self.metrics_data = {}
        self.code_buffer = ""
        self.current_status = "Ready"
        self.is_generating = False
        self.live_display = None
        self.update_lock = threading.Lock()
        
        # Setup layout structure
        self._setup_layout()
        
    def _setup_layout(self):
        """Setup the terminal layout structure."""
        # Create main layout splits
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        
        # Split main area
        self.layout["main"].split_row(
            Layout(name="code_area", ratio=2),
            Layout(name="metrics_area", ratio=1)
        )
        
        # Split code area
        self.layout["code_area"].split_column(
            Layout(name="input_area", size=5),
            Layout(name="output_area", ratio=1)
        )
        
        # Split metrics area
        self.layout["metrics_area"].split_column(
            Layout(name="realtime_metrics", ratio=1),
            Layout(name="system_info", ratio=1)
        )
    
    def start_live_display(self):
        """Start the live display update."""
        if self.live_display is None:
            self.live_display = Live(self.layout, refresh_per_second=4, screen=True)
            self.live_display.start()
            self._update_static_components()
    
    def stop_live_display(self):
        """Stop the live display."""
        if self.live_display:
            self.live_display.stop()
            self.live_display = None
    
    def _update_static_components(self):
        """Update static components of the interface."""
        # Header
        header_text = Text("🚀 Advanced Auto Coder System", style="bold blue")
        header_text.append(" | ")
        header_text.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), style="dim")
        self.layout["header"].update(
            Panel(Align.center(header_text), style="blue")
        )
        
        # Footer
        footer_text = Text("Commands: ", style="bold")
        footer_text.append("improve: <code>", style="green")
        footer_text.append(" | ")
        footer_text.append("breakdown: <task>", style="yellow")
        footer_text.append(" | ")
        footer_text.append("clear", style="red")
        footer_text.append(" | ")
        footer_text.append("exit", style="red")
        
        self.layout["footer"].update(
            Panel(Align.center(footer_text), style="dim")
        )
    
    def update_input_area(self, prompt: str):
        """Update the input area with user prompt."""
        with self.update_lock:
            input_panel = Panel(
                Text(f"📝 Input: {prompt}", style="bold white"),
                title="User Request",
                border_style="green"
            )
            self.layout["input_area"].update(input_panel)
    
    def start_code_generation(self, prompt: str):
        """Start code generation visualization."""
        with self.update_lock:
            self.is_generating = True
            self.current_status = "Generating..."
            self.code_buffer = ""
            
            # Update input area
            self.update_input_area(prompt)
            
            # Show generation progress
            progress_text = Text("🤖 Generating code...", style="bold yellow")
            progress_panel = Panel(
                progress_text,
                title="Code Generation",
                border_style="yellow"
            )
            self.layout["output_area"].update(progress_panel)
    
    def stream_code_chunk(self, chunk: str):
        """Stream code generation in real-time."""
        with self.update_lock:
            self.code_buffer += chunk
            
            # Create syntax highlighted code display
            if self.code_buffer.strip():
                # Try to detect language from code
                language = self._detect_language(self.code_buffer)
                
                try:
                    syntax = Syntax(
                        self.code_buffer,
                        language,
                        theme="monokai",
                        line_numbers=True,
                        word_wrap=True
                    )
                    
                    code_panel = Panel(
                        syntax,
                        title=f"Generated Code ({language})",
                        border_style="green"
                    )
                    self.layout["output_area"].update(code_panel)
                except:
                    # Fallback to plain text
                    code_panel = Panel(
                        Text(self.code_buffer),
                        title="Generated Code",
                        border_style="green"
                    )
                    self.layout["output_area"].update(code_panel)
    
    def complete_code_generation(self, final_code: str, language: str = "python"):
        """Complete code generation and show final result."""
        with self.update_lock:
            self.is_generating = False
            self.current_status = "Complete"
            self.code_buffer = final_code
            
            # Show final code with syntax highlighting
            try:
                syntax = Syntax(
                    final_code,
                    language,
                    theme="monokai",
                    line_numbers=True,
                    word_wrap=True
                )
                
                code_panel = Panel(
                    syntax,
                    title=f"✅ Generated Code ({language})",
                    border_style="bright_green"
                )
                self.layout["output_area"].update(code_panel)
            except:
                code_panel = Panel(
                    Text(final_code),
                    title="✅ Generated Code",
                    border_style="bright_green"
                )
                self.layout["output_area"].update(code_panel)
    
    def update_metrics(self, metrics: Dict[str, Any]):
        """Update real-time metrics display."""
        with self.update_lock:
            self.metrics_data.update(metrics)
            
            # Create metrics table
            metrics_table = Table(title="Real-time Metrics", show_header=True)
            metrics_table.add_column("Metric", style="cyan")
            metrics_table.add_column("Value", style="bright_white")
            metrics_table.add_column("Unit", style="dim")
            
            # Add metrics rows
            if "response_time" in self.metrics_data:
                metrics_table.add_row(
                    "Response Time",
                    f"{self.metrics_data['response_time']:.2f}",
                    "seconds"
                )
            
            if "tokens_per_second" in self.metrics_data:
                metrics_table.add_row(
                    "Generation Speed",
                    f"{self.metrics_data['tokens_per_second']:.1f}",
                    "tokens/sec"
                )
            
            if "token_count" in self.metrics_data:
                metrics_table.add_row(
                    "Tokens Generated",
                    str(self.metrics_data['token_count']),
                    "tokens"
                )
            
            if "memory_usage" in self.metrics_data:
                metrics_table.add_row(
                    "Memory Usage",
                    f"{self.metrics_data['memory_usage']:.1f}",
                    "MB"
                )
            
            if "model_confidence" in self.metrics_data:
                confidence = self.metrics_data['model_confidence']
                confidence_style = "green" if confidence > 0.8 else "yellow" if confidence > 0.6 else "red"
                metrics_table.add_row(
                    "Model Confidence",
                    f"{confidence:.1%}",
                    "",
                    style=confidence_style
                )
            
            metrics_panel = Panel(
                metrics_table,
                title="📊 Performance Metrics",
                border_style="blue"
            )
            self.layout["realtime_metrics"].update(metrics_panel)
    
    def update_system_info(self, system_info: Dict[str, Any]):
        """Update system information display."""
        with self.update_lock:
            # Create system info table
            system_table = Table(title="System Status", show_header=True)
            system_table.add_column("Component", style="cyan")
            system_table.add_column("Status", style="bright_white")
            
            # Add system info rows
            system_table.add_row("Ollama Connection", "🟢 Connected" if system_info.get("ollama_connected") else "🔴 Disconnected")
            system_table.add_row("Model Status", system_info.get("model_status", "Unknown"))
            system_table.add_row("Generation Status", self.current_status)
            
            if "model_name" in system_info:
                system_table.add_row("Active Model", system_info["model_name"])
            
            if "context_length" in system_info:
                system_table.add_row("Context Length", f"{system_info['context_length']} tokens")
            
            if "conversation_turns" in system_info:
                system_table.add_row("Conversation Turns", str(system_info["conversation_turns"]))
            
            system_panel = Panel(
                system_table,
                title="🖥️ System Information",
                border_style="magenta"
            )
            self.layout["system_info"].update(system_panel)
    
    def show_error(self, error_message: str):
        """Show error message in the output area."""
        with self.update_lock:
            self.is_generating = False
            self.current_status = "Error"
            
            error_text = Text(f"❌ Error: {error_message}", style="bold red")
            error_panel = Panel(
                error_text,
                title="Error",
                border_style="red"
            )
            self.layout["output_area"].update(error_panel)
    
    def _detect_language(self, code: str) -> str:
        """Detect programming language from code content."""
        code_lower = code.lower() 
        
        # Simple heuristics for language detection
        if "def " in code or "import " in code or "from " in code:
            return "python"
        elif "function" in code or "const " in code or "let " in code:
            return "javascript"
        elif "class " in code and "public " in code:
            return "java"
        elif "#include" in code or "int main" in code:
            return "cpp"
        elif "func " in code or "package " in code:
            return "go"
        elif "fn " in code or "struct " in code:
            return "rust"
        elif "<html>" in code or "<!DOCTYPE" in code:
            return "html"
        elif "SELECT" in code.upper() or "CREATE TABLE" in code.upper():
            return "sql"
        else:
            return "text"
    
    def get_user_input(self, prompt: str = "🎯 What would you like me to do? > ") -> str:
        """Get user input with the live display running."""
        if self.live_display:
            self.live_display.stop()
        
        try:
            user_input = input(prompt).strip()
        finally:
            if self.live_display:
                self.live_display.start()
        
        return user_input
    
    def show_help(self):
        """Show help information."""
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

💡 INTERFACE FEATURES:
  • Real-time code generation streaming
  • Live performance metrics
  • Syntax highlighting
  • System status monitoring

📊 METRICS EXPLAINED:
  • Response Time: How long the model takes to respond
  • Generation Speed: Tokens generated per second
  • Model Confidence: AI confidence in the generated code
  • Memory Usage: System resource consumption
        """
        
        help_panel = Panel(
            Text(help_text, style="white"),
            title="Help & Usage Guide",
            border_style="blue"
        )
        
        with self.update_lock:
            self.layout["output_area"].update(help_panel) 