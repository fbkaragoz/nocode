#!/usr/bin/env python3
"""
AI Code Generation System - Clean Entry Point
Single mode: Analytics terminal + Clean main interface
"""

import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Core imports
from src.core.cli.cli_manager import CLIManager


def setup_logging():
    """Setup quiet logging - only errors to avoid terminal spam."""
    logging.basicConfig(
        level=logging.ERROR,  # Only errors
        format='%(levelname)s: %(message)s',
        handlers=[logging.StreamHandler(sys.stderr)]  # Errors to stderr, not stdout
    )


def main():
    """Main entry point for the application."""
    setup_logging()
    cli_manager = CLIManager()
    cli_manager.start()


if __name__ == "__main__":
    main() 