"""
Interface module for advanced terminal and UI management.
Provides clean architecture for user interface components.
"""

from .terminal_interface import TerminalInterface
from .split_terminal import SplitTerminalInterface
from .rich_formatter import RichFormatter

__all__ = ['TerminalInterface', 'SplitTerminalInterface', 'RichFormatter'] 