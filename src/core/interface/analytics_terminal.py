#!/usr/bin/env python3
"""
System Analytics Terminal - Separate module for analytics dashboard.
Clean separation of concerns with proper import structure.
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

# Import shared monitoring from utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.utils.system_monitor import SystemMonitor


class AnalyticsTerminal:
    """Clean analytics terminal using shared monitoring utilities."""
    
    def __init__(self):
        self.console = Console()
        self.start_time = datetime.now()
        self.system_monitor = SystemMonitor()
        
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
    
    def _create_header(self) -> Panel:
        """Create header panel."""
        return Panel(
            Text.from_markup(
                "[bold blue]🔍 AI Code Generation - System Analytics[/bold blue]\n"
                f"[dim]Started: {self.start_time.strftime('%H:%M:%S')} | "
                f"Runtime: {self._get_runtime()}[/dim]"
            ),
            style="blue"
        )
    
    def _create_system_panel(self) -> Panel:
        """Create system metrics panel using shared monitor."""
        metrics = self.system_monitor.collect_metrics()
        health = self.system_monitor.get_system_health()
        
        table = Table(title="System Resources", show_header=True, header_style="bold magenta")
        table.add_column("Resource", style="cyan")
        table.add_column("Usage", style="green")
        table.add_column("Status", style="yellow")
        
        # CPU Usage
        cpu_status = "🟢 Normal" if health['cpu'] == 'Normal' else "🟡 High" if health['cpu'] == 'High' else "🔴 Critical"
        table.add_row("CPU", f"{metrics.cpu_percent:.1f}%", cpu_status)
        
        # Memory Usage
        mem_status = "🟢 Normal" if health['memory'] == 'Normal' else "🟡 High" if health['memory'] == 'High' else "🔴 Critical"
        table.add_row("Memory", f"{metrics.memory_percent:.1f}% ({metrics.memory_used_mb:.0f} MB)", mem_status)
        
        # GPU Usage (if available)
        if metrics.gpu_percent is not None:
            gpu_status = "🟢 Normal" if metrics.gpu_percent < 70 else "🟡 High" if metrics.gpu_percent < 90 else "🔴 Critical"
            table.add_row("GPU", f"{metrics.gpu_percent:.1f}%", gpu_status)
            if metrics.gpu_memory_percent:
                table.add_row("GPU Memory", f"{metrics.gpu_memory_percent:.1f}% ({metrics.gpu_memory_used_mb:.0f} MB)", gpu_status)
        else:
            table.add_row("GPU", "Not available", "⚪ N/A")
        
        # Disk Usage
        disk_status = "🟢 Normal" if health['disk'] == 'Normal' else "🟡 High" if health['disk'] == 'High' else "🔴 Critical"
        table.add_row("Disk", f"{metrics.disk_percent:.1f}%", disk_status)
        
        return Panel(table, title="[bold]Hardware Monitoring[/bold]", border_style="blue")
    
    def _create_project_panel(self) -> Panel:
        """Create project metrics panel."""
        table = Table(title="Project Status", show_header=True, header_style="bold green")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        table.add_column("Details", style="dim")
        
        # Session stats
        try:
            if os.path.exists('cache/system_metrics.json'):
                with open('cache/system_metrics.json', 'r') as f:
                    cached_data = json.load(f)
                    if cached_data:
                        latest = cached_data[-1]
                        table.add_row("Conversations", str(latest.get('conversation_turns', 0)), "Total")
                        table.add_row("Model Status", latest.get('model_status', 'Unknown'), "Connection")
                        table.add_row("Uptime", latest.get('uptime', '0s'), "Session")
            else:
                table.add_row("Session Status", "Waiting for input", "Ready")
        except Exception as e:
            table.add_row("Session Error", str(e)[:30], "Check logs")
        
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
    analytics = AnalyticsTerminal()
    try:
        analytics.run()
    except KeyboardInterrupt:
        print("\n📊 Analytics dashboard closed.") 