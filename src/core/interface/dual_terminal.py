"""
Dual Terminal System - Two separate terminal windows.
One for user interaction, one for analytics and monitoring.
"""

import os
import sys
import time
import subprocess
import logging
from typing import Dict, Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from models.session_stats import SessionStats
from utils.system_monitor import SystemMonitor


logger = logging.getLogger(__name__)


class AnalyticsTerminal:
    """Analytics terminal for monitoring and metrics."""
    
    def __init__(self, session_stats: SessionStats, system_monitor: SystemMonitor):
        """Initialize analytics terminal."""
        self.session_stats = session_stats
        self.system_monitor = system_monitor
        self.console = Console()
        self.running = False
        self.update_thread = None
        
    def start(self):
        """Start analytics terminal in separate process."""
        try:
            # Create analytics script
            script_path = self._create_analytics_script()
            
            # Launch in new terminal window
            if sys.platform.startswith('linux'):
                # For Linux - try different terminal emulators
                terminals = [
                    ['gnome-terminal', '--', 'python', script_path],
                    ['konsole', '-e', 'python', script_path],
                    ['xterm', '-e', 'python', script_path],
                    ['terminal', '-e', 'python', script_path]
                ]
                
                for terminal_cmd in terminals:
                    try:
                        subprocess.Popen(terminal_cmd, 
                                       cwd=os.getcwd(),
                                       stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL)
                        logger.info(f"Analytics terminal launched: {terminal_cmd[0]}")
                        return True
                    except FileNotFoundError:
                        continue
                        
            elif sys.platform == 'darwin':  # macOS
                subprocess.Popen(['osascript', '-e', 
                    f'tell app "Terminal" to do script "cd {os.getcwd()} && python {script_path}"'])
                
            elif sys.platform.startswith('win'):  # Windows
                subprocess.Popen(['start', 'cmd', '/k', f'python {script_path}'], shell=True)
            
            logger.error("No suitable terminal emulator found")
            return False
            
        except Exception as e:
            logger.error(f"Failed to start analytics terminal: {e}")
            return False
    
    def _create_analytics_script(self) -> str:
        """Create analytics script for separate terminal."""
        script_content = '''#!/usr/bin/env python3
"""
Analytics Terminal - Real-time monitoring and metrics display.
"""

import os
import sys
import time
import json
import psutil
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.live import Live
from rich.text import Text


class LiveAnalytics:
    """Live analytics display."""
    
    def __init__(self):
        self.console = Console()
        self.start_time = datetime.now()
        
    def run(self):
        """Run live analytics display."""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        with Live(layout, refresh_per_second=2, screen=True):
            while True:
                try:
                    # Header
                    layout["header"].update(
                        Panel(
                            Text.from_markup(
                                "[bold blue]🔍 AI Code Generation - Analytics Terminal[/bold blue]\\n"
                                f"[dim]Started: {self.start_time.strftime('%H:%M:%S')} | "
                                f"Runtime: {self._get_runtime()}[/dim]"
                            ),
                            style="blue"
                        )
                    )
                    
                    # System metrics
                    layout["left"].update(self._create_system_panel())
                    
                    # Project metrics
                    layout["right"].update(self._create_project_panel())
                    
                    # Footer
                    layout["footer"].update(
                        Panel(
                            Text.from_markup(
                                "[dim]Press Ctrl+C to close analytics terminal[/dim]"
                            ),
                            style="dim"
                        )
                    )
                    
                    time.sleep(1)
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"Analytics error: {e}")
                    time.sleep(5)
    
    def _create_system_panel(self) -> Panel:
        """Create system metrics panel."""
        table = Table(title="System Metrics", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_column("Status", style="yellow")
        
        # CPU Usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_status = "🟢 Normal" if cpu_percent < 70 else "🟡 High" if cpu_percent < 90 else "🔴 Critical"
        table.add_row("CPU Usage", f"{cpu_percent:.1f}%", cpu_status)
        
        # Memory Usage
        memory = psutil.virtual_memory()
        mem_percent = memory.percent
        mem_status = "🟢 Normal" if mem_percent < 70 else "🟡 High" if mem_percent < 90 else "🔴 Critical"
        table.add_row("Memory Usage", f"{mem_percent:.1f}% ({memory.used // 1024**2} MB)", mem_status)
        
        # GPU Usage (if available)
        try:
            import subprocess
            result = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total', 
                                   '--format=csv,noheader,nounits'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                gpu_data = result.stdout.strip().split(',')
                gpu_util = float(gpu_data[0])
                gpu_mem_used = int(gpu_data[1])
                gpu_mem_total = int(gpu_data[2])
                gpu_mem_percent = (gpu_mem_used / gpu_mem_total) * 100
                
                gpu_status = "🟢 Normal" if gpu_util < 70 else "🟡 High" if gpu_util < 90 else "🔴 Critical"
                table.add_row("GPU Usage", f"{gpu_util:.1f}%", gpu_status)
                table.add_row("GPU Memory", f"{gpu_mem_percent:.1f}% ({gpu_mem_used} MB)", gpu_status)
        except:
            table.add_row("GPU", "Not available", "🔴 N/A")
        
        # Disk Usage
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        disk_status = "🟢 Normal" if disk_percent < 80 else "🟡 High" if disk_percent < 95 else "🔴 Critical"
        table.add_row("Disk Usage", f"{disk_percent:.1f}%", disk_status)
        
        return Panel(table, title="[bold]System Resources[/bold]", border_style="blue")
    
    def _create_project_panel(self) -> Panel:
        """Create project metrics panel."""
        table = Table(title="Project Status", show_header=True, header_style="bold green")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        table.add_column("Details", style="dim")
        
        # Session stats (from files if available)
        try:
            # Try to read session stats
            if os.path.exists('logs/session_stats.json'):
                with open('logs/session_stats.json', 'r') as f:
                    stats = json.load(f)
                
                table.add_row("Total Requests", str(stats.get('total_requests', 0)), "All time")
                table.add_row("Successful Requests", str(stats.get('successful_requests', 0)), "Completed")
                table.add_row("Failed Requests", str(stats.get('failed_requests', 0)), "Errors")
                table.add_row("Average Response Time", f"{stats.get('avg_response_time', 0):.2f}s", "Performance")
                table.add_row("Total Tokens", str(stats.get('total_tokens', 0)), "Usage")
            else:
                table.add_row("Session Status", "No active session", "Waiting...")
                
        except Exception as e:
            table.add_row("Session Error", str(e), "Check logs")
        
        # Active processes
        python_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'python' in proc.info['name'].lower() and 'run.py' in ' '.join(proc.info['cmdline'] or []):
                    python_processes.append(proc.info['pid'])
            except:
                pass
        
        table.add_row("Active Processes", str(len(python_processes)), f"PIDs: {python_processes[:3]}")
        
        # Log file stats
        log_files = ['auto_coder.log', 'system.log', 'session_*.json']
        log_count = 0
        for pattern in log_files:
            if '*' in pattern:
                import glob
                log_count += len(glob.glob(f'logs/{pattern}'))
            elif os.path.exists(f'logs/{pattern}'):
                log_count += 1
        
        table.add_row("Log Files", str(log_count), "Available")
        
        return Panel(table, title="[bold]Project Analytics[/bold]", border_style="green")
    
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
    print("🚀 Starting Analytics Terminal...")
    analytics = LiveAnalytics()
    try:
        analytics.run()
    except KeyboardInterrupt:
        print("\\n📊 Analytics Terminal closed.")
'''
        
        # Save script to temporary file
        script_path = os.path.join('tmp', 'analytics_terminal.py')
        os.makedirs('tmp', exist_ok=True)
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        return script_path


class DualTerminalInterface:
    """
    Dual Terminal Interface - Main interaction + Analytics monitoring.
    
    Features:
    - Main terminal for user interaction
    - Separate analytics terminal for monitoring
    - Real-time metrics and system status
    - Project progress tracking
    """
    
    def __init__(self, session_stats: SessionStats, system_monitor: SystemMonitor):
        """Initialize dual terminal interface."""
        self.session_stats = session_stats
        self.system_monitor = system_monitor
        self.console = Console()
        self.analytics_terminal = AnalyticsTerminal(session_stats, system_monitor)
        
        logger.info("Dual terminal interface initialized")
    
    def initialize(self):
        """Initialize dual terminal system."""
        try:
            # Start analytics terminal
            success = self.analytics_terminal.start()
            if success:
                self.console.print("🖥️  [bold green]Analytics terminal launched[/bold green]")
                time.sleep(2)  # Give analytics terminal time to start
            else:
                self.console.print("⚠️  [yellow]Analytics terminal failed to launch[/yellow]")
            
            # Initialize main terminal
            self.show_welcome()
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize dual terminal: {e}")
            return False
    
    def show_welcome(self, welcome_data: Dict[str, Any] = None):
        """Show welcome message in main terminal."""
        # Use provided data or defaults
        if not welcome_data:
            welcome_data = {
                'title': 'Dual Terminal System',
                'features': ['Multi-step projects', 'Real-time monitoring', 'GPU acceleration']
            }
        
        features_text = "\n".join([f"• {feature}" for feature in welcome_data.get('features', [])])
        
        welcome_panel = Panel(
            Text.from_markup(
                f"""[bold blue]🚀 {welcome_data.get('title', 'AI Code Generation System')}[/bold blue]

[bold]Main Terminal:[/bold] User interaction and code generation
[bold]Analytics Terminal:[/bold] Real-time monitoring and metrics

[dim]Features:[/dim]
{features_text}

[green]Ready for advanced code generation![/green]"""
            ),
            title="[bold]Dual Terminal System[/bold]",
            border_style="blue",
            padding=(1, 2)
        )
        
        self.console.print(welcome_panel)
    
    def get_user_input(self, prompt: str = "💭 What would you like me to code?") -> str:
        """Get user input from main terminal."""
        try:
            return self.console.input(f"\n{prompt}: ")
        except KeyboardInterrupt:
            return ""
        except EOFError:
            return ""
    
    def display_response(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Display response in main terminal."""
        # Main response
        response_panel = Panel(
            content,
            title="[bold green]Generated Code[/bold green]",
            border_style="green"
        )
        self.console.print(response_panel)
        
        # Metadata if provided
        if metadata:
            meta_table = Table(title="Response Metadata", show_header=True)
            meta_table.add_column("Property", style="cyan")
            meta_table.add_column("Value", style="white")
            
            for key, value in metadata.items():
                meta_table.add_row(str(key), str(value))
            
            self.console.print(meta_table)
    
    def display_error(self, error_message: str, details: Optional[str] = None):
        """Display error in main terminal."""
        error_panel = Panel(
            f"[red]{error_message}[/red]" + (f"\n\n[dim]{details}[/dim]" if details else ""),
            title="[bold red]Error[/bold red]",
            border_style="red"
        )
        self.console.print(error_panel)
    
    def display_project_status(self, project_status: Dict[str, Any]):
        """Display project status in main terminal."""
        status_table = Table(title=f"Project: {project_status.get('name', 'Unknown')}", 
                           show_header=True, header_style="bold blue")
        status_table.add_column("Property", style="cyan")
        status_table.add_column("Value", style="white")
        status_table.add_column("Progress", style="green")
        
        total_steps = project_status.get('total_steps', 0)
        completed_steps = project_status.get('completed_steps', 0)
        progress_percent = project_status.get('progress_percent', 0)
        
        status_table.add_row("Total Steps", str(total_steps), "")
        status_table.add_row("Completed Steps", str(completed_steps), f"{progress_percent:.1f}%")
        status_table.add_row("Current Step", project_status.get('current_step', 'None'), "")
        
        # Progress bar
        progress_bar = "█" * int(progress_percent / 10) + "░" * (10 - int(progress_percent / 10))
        status_table.add_row("Progress", progress_bar, f"{progress_percent:.1f}%")
        
        self.console.print(Panel(status_table, border_style="blue"))
    
    def show_error(self, error_message: str, details: Optional[str] = None):
        """Display error in main terminal."""
        error_panel = Panel(
            f"[red]{error_message}[/red]" + (f"\n\n[dim]{details}[/dim]" if details else ""),
            title="[bold red]Error[/bold red]",
            border_style="red"
        )
        self.console.print(error_panel)
    
    def show_goodbye(self, summary: Dict[str, Any]):
        """Display goodbye message with session summary."""
        goodbye_panel = Panel(
            Text.from_markup(
                f"""[bold blue]Session Complete[/bold blue]

[dim]Session Summary:[/dim]
• Conversation turns: {summary.get('conversation_turns', 0)}
• Total tokens: {summary.get('total_tokens', 0)}
• Uptime: {summary.get('uptime', '0s')}
• Model: {summary.get('model_used', 'Unknown')}

[green]Thank you for using the AI Code Generation System![/green]"""
            ),
            title="[bold]Goodbye[/bold]",
            border_style="blue"
        )
        self.console.print(goodbye_panel)
    
    def cleanup(self):
        """Cleanup dual terminal system."""
        try:
            self.console.print("\n🔚 [dim]Closing dual terminal system...[/dim]")
            
            # The analytics terminal will close when the main process ends
            # or when user presses Ctrl+C in the analytics window
            
            logger.info("Dual terminal interface cleaned up")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}") 