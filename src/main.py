#!/usr/bin/env python3
"""
Main entry point for the Advanced Automatic Code Generation System.
"""

import logging
import sys
import argparse


from config.settings import Settings
from services.ollama_service import OllamaService
from core.auto_coder import AutoCoderEngine
from core.simple_cli import SimpleAutoCoderCLI
from core.enhanced_cli import EnhancedAutoCoderCLI


def setup_logging(settings: Settings) -> None:
    """Setup logging configuration."""
    log_level = settings.get("logging.level", "INFO")
    log_format = settings.get("logging.format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    log_file = settings.get("logging.file", "auto_coder.log")
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Advanced AI Code Generation System")
    parser.add_argument(
        '--interface', 
        choices=['simple', 'enhanced'], 
        default='enhanced',
        help='Choose interface type (default: enhanced)'
    )
    parser.add_argument(
        '--quiet', 
        action='store_true',
        help='Reduce console output'
    )
    return parser.parse_args()


def main():
    """Main application entry point."""
    try:
        # Parse arguments
        args = parse_arguments()
        
        # Load settings
        settings = Settings()
        
        # Setup logging
        setup_logging(settings)
        logger = logging.getLogger(__name__)
        
        if not args.quiet:
            logger.info("🚀 Starting Advanced Automatic Code Generation System")
            logger.info(f"Using model: {settings.model_name}")
            logger.info(f"Ollama URL: {settings.ollama_url}")
            logger.info(f"Interface: {args.interface}")
        
        # Initialize services
        ollama_service = OllamaService(settings)
        
        # Check Ollama connection
        if not ollama_service.check_connection():
            print("❌ Failed to connect to Ollama!")
            print("Please ensure Ollama is running and the model is available.")
            print(f"Expected model: {settings.model_name}")
            print(f"Available models: {ollama_service.get_available_models()}")
            return 1
        
        if not args.quiet:
            print("✅ Ollama connection successful!")
        
        # Initialize core engine
        engine = AutoCoderEngine(settings, ollama_service)
        
        # Choose CLI interface
        if args.interface == 'enhanced':
            try:
                cli = EnhancedAutoCoderCLI(engine)
                print("🚀 Starting Enhanced Split Terminal Interface...")
            except ImportError as e:
                print(f"⚠️ Enhanced interface not available: {e}")
                print("🔄 Falling back to simple interface...")
                cli = SimpleAutoCoderCLI(engine)
        else:
            cli = SimpleAutoCoderCLI(engine)
        
        # Start interactive mode
        return cli.run_interactive()
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        return 0
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        logging.getLogger(__name__).exception("Fatal error")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 