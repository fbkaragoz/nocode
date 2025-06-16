#!/usr/bin/env python3
"""
Advanced AI Code Generation System - Main Entry Point
Clean architecture implementation with modular design.
"""

import sys
import os
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Core imports
from config.settings import Settings
from core.auto_coder import AutoCoderEngine
from core.cli.cli_manager import CLIManager


def setup_logging():
    """Setup logging configuration."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "system.log"),
            logging.StreamHandler()
        ]
    )


def check_environment():
    """Check if environment is properly configured."""
    try:
        # Check if we're in conda environment
        conda_env = os.environ.get('CONDA_DEFAULT_ENV')
        if conda_env:
            print(f"Running in conda environment: {conda_env}")
        
        # Check Python version
        if sys.version_info < (3, 8):
            print("Warning: Python 3.8+ recommended")
        
        return True
        
    except Exception as e:
        print(f"Environment check failed: {e}")
        return False


def main():
    """Main entry point."""
    try:
        # Setup
        setup_logging()
        logger = logging.getLogger(__name__)
        
        # Check environment
        if not check_environment():
            return 1
        
        # Load settings
        settings = Settings()
        
        # Initialize engine
        engine = AutoCoderEngine(settings)
        
        # Test connection
        if not engine.test_connection():
            print("Warning: Could not connect to Ollama service")
            print("Make sure Ollama is running and accessible")
        
        # Parse command line arguments
        interface_type = "split"  # Default to split interface
        if len(sys.argv) > 1 and sys.argv[1] == "--standard":
            interface_type = "enhanced"
        
        # Initialize and start CLI
        cli_manager = CLIManager(engine, interface_type)
        return cli_manager.start()
        
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
        return 0
    except Exception as e:
        print(f"Fatal error: {e}")
        logging.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main()) 