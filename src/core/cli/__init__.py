"""
Core CLI module for Advanced AI Code Generation System.
Provides modular, clean architecture for user interfaces.
"""

from .cli_manager import CLIManager
from .command_processor import CommandProcessor
from .input_handler import InputHandler

__all__ = ['CLIManager', 'CommandProcessor', 'InputHandler'] 