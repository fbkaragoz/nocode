"""
Display Manager - Professional UI coordination and management.
Handles all user interface interactions with a clean, modular architecture.
"""

import logging
import os
import sys
import time
import subprocess
from typing import Dict, Any, Optional, Protocol
from enum import Enum
from dataclasses import dataclass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.prompt import Prompt

from .formatter import UIFormatter


logger = logging.getLogger(__name__)


class DisplayMode(Enum):
    """Display mode enumeration."""
    STANDARD = "standard"
    ANALYTICS = "analytics"
    MINIMAL = "minimal"


@dataclass
class DisplayConfig:
    """Display configuration."""
    mode: DisplayMode = DisplayMode.STANDARD
    show_timestamps: bool = True
    show_progress: bool = True
    syntax_highlighting: bool = True
    auto_scroll: bool = True
    max_display_lines: int = 50
    refresh_rate: int = 4


class DisplayProtocol(Protocol):
    """Protocol for display components."""
    
    def initialize(self) -> bool:
        """Initialize the display component."""
        ...
    
    def show_content(self, content: str, content_type: str = "text") -> None:
        """Show content in the display."""
        ...
    
    def cleanup(self) -> None:
        """Cleanup display resources."""
        ...


class AnalyticsDisplay:
    """Analytics display component for system monitoring."""
    
    def __init__(self, console: Console):
        self.console = console
        self.process = None
        self.is_active = False
    
    def initialize(self) -> bool:
        """Initialize analytics display in separate terminal."""
        try:
            script_path = self._create_analytics_script()
            
            # Try different terminal emulators (Linux focus for open source)
            terminals = [
                ['gnome-terminal', '--', 'python', script_path],
                ['konsole', '-e', 'python', script_path],
                ['xterm', '-e', 'python', script_path],
                ['alacritty', '-e', 'python', script_path],
                ['terminator', '-e', 'python', script_path]
            ]
            
            for terminal_cmd in terminals:
                try:
                    self.process = subprocess.Popen(
                        terminal_cmd, 
                        cwd=os.getcwd(),
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    logger.info(f"Analytics display launched: {terminal_cmd[0]}")
                    self.is_active = True
                    return True
                except FileNotFoundError:
                    continue
            
            logger.warning("No suitable terminal emulator found for analytics display")
            return False
            
        except Exception as e:
            logger.error(f"Failed to initialize analytics display: {e}")
            return False
    
    def cleanup(self) -> None:
        """Cleanup analytics display."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                self.process.kill()
        self.is_active = False
    
    def _create_analytics_script(self) -> str:
        """Create analytics monitoring script."""
        script_content = '''#!/usr/bin/env python3
"""
System Analytics - Real-time monitoring dashboard.
Generic GPU support for any compatible hardware.
"""

import os
import sys
import time
import json
import psutil
import subprocess
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.live import Live
from rich.text import Text


class SystemAnalytics:
    """Real-time system analytics dashboard."""
    
    def __init__(self):
        self.console = Console()
        self.start_time = datetime.now()
        self.gpu_info = self._detect_gpu()
        
    def run(self):
        """Run analytics dashboard."""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        layout["main"].split_row(
            Layout(name="system"),
            Layout(name="project")
        )
        
        with Live(layout, refresh_per_second=2, screen=True):
            while True:
                try:
                    # Update header
                    layout["header"].update(self._create_header())
                    
                    # Update system metrics
                    layout["system"].update(self._create_system_panel())
                    
                    # Update project metrics
                    layout["project"].update(self._create_project_panel())
                    
                    # Update footer
                    layout["footer"].update(self._create_footer())
                    
                    time.sleep(1)
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"Analytics error: {e}")
                    time.sleep(5)
    
    def _detect_gpu(self) -> Dict[str, Any]:
        """Detect GPU availability (generic support)."""
        gpu_info = {'available': False, 'type': 'None', 'name': 'N/A'}
        
        try:
            # Try NVIDIA
            result = subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                gpu_info = {
                    'available': True,
                    'type': 'NVIDIA',
                    'name': result.stdout.strip(),
                    'query_cmd': ['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total', 
                                 '--format=csv,noheader,nounits']
                }
                return gpu_info
            
            # Try AMD
            result = subprocess.run(['rocm-smi', '--showproductname'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                gpu_info = {
                    'available': True,
                    'type': 'AMD',
                    'name': 'AMD GPU',
                    'query_cmd': ['rocm-smi', '--showuse', '--csv']
                }
                return gpu_info
            
            # Try Intel
            result = subprocess.run(['intel_gpu_top', '-l'], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                gpu_info = {
                    'available': True,
                    'type': 'Intel',
                    'name': 'Intel GPU',
                    'query_cmd': ['intel_gpu_top', '-l']
                }
                return gpu_info
                
        except Exception as e:
            pass
        
        return gpu_info
    
    def _create_header(self) -> Panel:
        """Create header panel."""
        return Panel(
            Text.from_markup(
                "[bold blue]🔍 AI Code Generation - System Analytics[/bold blue]\\n"
                f"[dim]Started: {self.start_time.strftime('%H:%M:%S')} | "
                f"Runtime: {self._get_runtime()}[/dim]"
            ),
            style="blue"
        )
    
    def _create_system_panel(self) -> Panel:
        """Create system metrics panel."""
        table = Table(title="System Resources", show_header=True, header_style="bold magenta")
        table.add_column("Resource", style="cyan")
        table.add_column("Usage", style="green")
        table.add_column("Status", style="yellow")
        
        # CPU Usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_status = "🟢 Normal" if cpu_percent < 70 else "🟡 High" if cpu_percent < 90 else "🔴 Critical"
        table.add_row("CPU", f"{cpu_percent:.1f}%", cpu_status)
        
        # Memory Usage
        memory = psutil.virtual_memory()
        mem_percent = memory.percent
        mem_status = "🟢 Normal" if mem_percent < 70 else "🟡 High" if mem_percent < 90 else "🔴 Critical"
        table.add_row("Memory", f"{mem_percent:.1f}% ({memory.used // 1024**2} MB)", mem_status)
        
        # GPU Usage (Generic)
        if self.gpu_info['available']:
            gpu_metrics = self._get_gpu_metrics()
            if gpu_metrics:
                gpu_status = "🟢 Normal" if gpu_metrics['utilization'] < 70 else "🟡 High" if gpu_metrics['utilization'] < 90 else "🔴 Critical"
                table.add_row(f"GPU ({self.gpu_info['type']})", f"{gpu_metrics['utilization']:.1f}%", gpu_status)
                if 'memory_percent' in gpu_metrics:
                    table.add_row("GPU Memory", f"{gpu_metrics['memory_percent']:.1f}% ({gpu_metrics.get('memory_used', 0)} MB)", gpu_status)
        else:
            table.add_row("GPU", "Not available", "🔴 N/A")
        
        # Disk Usage
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        disk_status = "🟢 Normal" if disk_percent < 80 else "🟡 High" if disk_percent < 95 else "🔴 Critical"
        table.add_row("Disk", f"{disk_percent:.1f}%", disk_status)
        
        return Panel(table, title="[bold]Hardware Monitoring[/bold]", border_style="blue")
    
    def _get_gpu_metrics(self) -> Optional[Dict]:
        """Get GPU metrics (generic support)."""
        if not self.gpu_info['available']:
            return None
        
        try:
            if self.gpu_info['type'] == 'NVIDIA':
                result = subprocess.run(self.gpu_info['query_cmd'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    values = result.stdout.strip().split(',')
                    if len(values) >= 3:
                        return {
                            'utilization': float(values[0]),
                            'memory_used': int(values[1]),
                            'memory_total': int(values[2]),
                            'memory_percent': (int(values[1]) / int(values[2])) * 100
                        }
            
            elif self.gpu_info['type'] == 'AMD':
                # AMD GPU metrics implementation
                result = subprocess.run(self.gpu_info['query_cmd'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    # Parse AMD GPU metrics
                    return {'utilization': 0.0}  # Placeholder
            
            elif self.gpu_info['type'] == 'Intel':
                # Intel GPU metrics implementation
                result = subprocess.run(self.gpu_info['query_cmd'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    # Parse Intel GPU metrics
                    return {'utilization': 0.0}  # Placeholder
            
            return None
            
        except Exception as e:
            return None
    
    def _create_project_panel(self) -> Panel:
        """Create project metrics panel."""
        table = Table(title="Project Status", show_header=True, header_style="bold green")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        table.add_column("Details", style="dim")
        
        # Session stats
        try:
            if os.path.exists('logs/session_stats.json'):
                with open('logs/session_stats.json', 'r') as f:
                    stats = json.load(f)
                
                table.add_row("Total Requests", str(stats.get('total_requests', 0)), "Completed")
                table.add_row("Success Rate", f"{stats.get('success_rate', 0):.1f}%", "Performance")
                table.add_row("Avg Response Time", f"{stats.get('avg_response_time', 0):.2f}s", "Latency")
                table.add_row("Total Tokens", str(stats.get('total_tokens', 0)), "Generated")
            else:
                table.add_row("Session Status", "Waiting for input", "Ready")
        except Exception as e:
            table.add_row("Session Error", str(e), "Check logs")
        
        # Active processes
        processes = [p for p in psutil.process_iter(['pid', 'name', 'cmdline']) 
                    if 'python' in p.info['name'].lower() and 'run.py' in ' '.join(p.info['cmdline'] or [])]
        table.add_row("Active Processes", str(len(processes)), f"PIDs: {[p.info['pid'] for p in processes[:3]]}")
        
        return Panel(table, title="[bold]Project Analytics[/bold]", border_style="green")
    
    def _create_footer(self) -> Panel:
        """Create footer panel."""
        return Panel(
            Text.from_markup("[dim]Press Ctrl+C to close analytics terminal[/dim]"),
            style="dim"
        )
    
    def _get_runtime(self) -> str:
        """Get formatted runtime."""
        runtime = datetime.now() - self.start_time
        total_seconds = int(runtime.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"


if __name__ == "__main__":
    print("🚀 Starting System Analytics...")
    analytics = SystemAnalytics()
    try:
        analytics.run()
    except KeyboardInterrupt:
        print("\\n📊 Analytics dashboard closed.")
'''
        
        # Save script
        script_path = os.path.join('tmp', 'system_analytics.py')
        os.makedirs('tmp', exist_ok=True)
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        return script_path


class DisplayManager:
    """
    Professional Display Manager - Clean UI coordination.
    
    Responsibilities:
    - Coordinate all UI components
    - Handle user input and display
    - Manage different display modes
    - Provide consistent UI experience
    """
    
    def __init__(self, config: DisplayConfig = None):
        """Initialize display manager."""
        self.config = config or DisplayConfig()
        self.console = Console()
        self.formatter = UIFormatter()
        
        # Display components
        self.analytics_display = None
        self.live_display = None
        self.progress_display = None
        
        # State management
        self.is_active = False
        self.current_metrics = {}
        self.last_status_update = 0
        
        logger.info(f"Display manager initialized with mode: {self.config.mode.value}")
    
    def initialize(self) -> bool:
        """Initialize the display manager."""
        try:
            self.console.clear()
            
            # Initialize analytics display if needed
            if self.config.mode == DisplayMode.ANALYTICS:
                self.analytics_display = AnalyticsDisplay(self.console)
                success = self.analytics_display.initialize()
                if success:
                    self.console.print("🖥️  [bold green]Analytics display launched[/bold green]")
                    time.sleep(2)  # Allow analytics to start
                else:
                    self.console.print("⚠️  [yellow]Analytics display failed to launch[/yellow]")
            
            self.is_active = True
            self._show_initialization_message()
            
            logger.info("Display manager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize display manager: {e}")
            return False
    
    def show_welcome(self, welcome_data: Dict[str, Any]):
        """Show welcome screen."""
        try:
            welcome_content = self.formatter.format_welcome(welcome_data)
            
            welcome_panel = Panel(
                welcome_content,
                title="🚀 AI Code Generation System",
                border_style="bright_blue",
                padding=(1, 2)
            )
            
            self.console.print(welcome_panel)
            self.console.print()
            
        except Exception as e:
            logger.error(f"Failed to show welcome: {e}")
    
    def get_user_input(self, prompt: str = "What would you like me to code?") -> Optional[str]:
        """Get user input."""
        try:
            formatted_prompt = f"[bold cyan]💭 {prompt}[/bold cyan]"
            user_input = Prompt.ask(formatted_prompt, console=self.console)
            return user_input.strip() if user_input else None
        except KeyboardInterrupt:
            raise
        except Exception as e:
            logger.error(f"Failed to get user input: {e}")
            return None
    
    def show_content(self, content: str, content_type: str = "code", language: str = "python"):
        """Show content with appropriate formatting."""
        try:
            if content_type == "code":
                formatted_content = self.formatter.format_code(content, language)
                panel = Panel(
                    formatted_content,
                    title=f"📝 Generated {language.title()} Code",
                    border_style="green",
                    padding=(1, 2)
                )
            else:
                panel = Panel(
                    content,
                    title="Output",
                    border_style="blue"
                )
            
            self.console.print(panel)
            
        except Exception as e:
            logger.error(f"Failed to show content: {e}")
    
    def show_progress(self, progress: float, message: str = "Processing..."):
        """Show progress indicator."""
        try:
            if not self.progress_display:
                self.progress_display = Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    console=self.console
                )
                self.progress_task = self.progress_display.add_task(message, total=100)
            
            self.progress_display.update(
                self.progress_task,
                completed=progress,
                description=message
            )
            
            if not self.live_display:
                self.progress_display.refresh()
                
        except Exception as e:
            logger.error(f"Failed to show progress: {e}")
    
    def update_system_metrics(self, metrics: Dict[str, Any]):
        """Update system metrics display."""
        try:
            self.current_metrics = metrics
            
            # Show periodic status in standard mode
            if self.config.mode == DisplayMode.STANDARD:
                current_time = time.time()
                if current_time - self.last_status_update > 10:
                    self._show_status_update(metrics)
                    self.last_status_update = current_time
            
        except Exception as e:
            logger.error(f"Failed to update system metrics: {e}")
    
    def show_error(self, error_message: str, details: str = None):
        """Show error message."""
        try:
            error_panel = self.formatter.format_error_message(error_message, details)
            self.console.print(error_panel)
        except Exception as e:
            logger.error(f"Failed to show error: {e}")
    
    def show_success(self, message: str):
        """Show success message."""
        try:
            success_panel = Panel(
                f"[green]✅ {message}[/green]",
                title="Success",
                border_style="green"
            )
            self.console.print(success_panel)
        except Exception as e:
            logger.error(f"Failed to show success: {e}")
    
    def show_info(self, message: str):
        """Show info message."""
        try:
            self.console.print(f"[blue]ℹ️ {message}[/blue]")
        except Exception as e:
            logger.error(f"Failed to show info: {e}")
    
    def show_goodbye(self, summary: Dict[str, Any]):
        """Show goodbye message with session summary."""
        try:
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
        """Clear the screen."""
        try:
            self.console.clear()
            self._show_initialization_message()
        except Exception as e:
            logger.error(f"Failed to clear screen: {e}")
    
    def cleanup(self):
        """Cleanup display manager resources."""
        try:
            if self.live_display:
                self.live_display.stop()
                self.live_display = None
            
            if self.progress_display:
                self.progress_display.stop()
                self.progress_display = None
            
            if self.analytics_display:
                self.analytics_display.cleanup()
                self.analytics_display = None
            
            self.is_active = False
            logger.info("Display manager cleaned up")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    def _show_initialization_message(self):
        """Show initialization message."""
        init_text = Text()
        init_text.append("AI Code Generation System", style="bold bright_blue")
        init_text.append(f" - {self.config.mode.value.title()} Mode", style="dim")
        
        self.console.print(init_text)
        self.console.print("─" * 80, style="dim")
    
    def _show_status_update(self, metrics: Dict[str, Any]):
        """Show periodic status update."""
        try:
            status_text = (
                f"[dim]Status: Memory {metrics.get('memory_usage_mb', 0)}MB | "
                f"CPU {metrics.get('cpu_usage_percent', 0)}% | "
                f"Conversations {metrics.get('conversation_turns', 0)} | "
                f"Model {metrics.get('model_status', 'Ready')}[/dim]"
            )
            self.console.print(status_text)
        except Exception as e:
            logger.error(f"Failed to show status: {e}") 