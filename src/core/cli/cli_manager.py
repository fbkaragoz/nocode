"""
Main CLI Manager - Coordinates all CLI functionality.
"""

import logging
import signal

from src.core.interface.display_manager import DisplayManager
from .command_processor import CommandProcessor
from src.config.settings import Settings


logger = logging.getLogger(__name__)


class CLIManager:
    """
    Main CLI Manager - handles the primary interaction loop and coordinates
    the engine and display for a streaming-first experience.
    """
    
    def __init__(self):
        """Initialize the CLI manager."""
        self.settings = Settings()
        self.display_manager = DisplayManager()
        self.processor = CommandProcessor(self.settings, self.display_manager)
        
        self.session_active = False
        signal.signal(signal.SIGINT, self._handle_interrupt)
        
        logger.info("CLI Manager initialized.")
    
    def start(self):
        """Start the CLI manager."""
        if self.display_manager.initialize():
            self._main_loop()
        self.display_manager.cleanup()
        logger.info("CLI session ended.")

    def _main_loop(self) -> int:
        """Main interaction loop."""
        self.session_active = True
        
        while self.session_active:
            try:
                user_input = self.display_manager.get_user_input()
                if user_input is None:  # Handle Ctrl+C
                    self.session_active = False
                    continue
                
                if not user_input.strip():
                    continue

                if not self._handle_special_commands(user_input):
                    # 1. Get the raw stream from the processor
                    stream = self.processor.generate_stream(user_input)
                    
                    # 2. Display the stream and get the full response back
                    full_response = self.display_manager.stream_content(stream)
                    
                    # 3. Pass the full response to the processor for saving
                    result = self.processor.save_response(full_response, user_input)
                    
                    if result.get("saved_file"):
                        self.display_manager.show_success(f"Code saved to: {result['saved_file']}")
                    else:
                        self.display_manager.show_error("Could not save the generated code.")
            
            except KeyboardInterrupt:
                self.session_active = False
            
            except Exception as e:
                logger.error(f"Main loop error: {e}", exc_info=True)
                self.display_manager.show_error("An unexpected error occurred", str(e))
        
        self.display_manager.show_goodbye()
        return 0
    
    def _handle_interrupt(self, signum, frame):
        """Handle Ctrl+C gracefully."""
        self.session_active = False
    
    def _cleanup(self):
        """Cleanup resources."""
        self.display_manager.show_goodbye()
        self.display_manager.cleanup()
        logger.info("CLI Manager cleaned up successfully.")

    def _handle_special_commands(self, user_input: str) -> bool:
        """Handle special commands and return True if the command was handled."""
        # Implement special command handling logic here
        return False

    def _handle_command(self, user_input: str):
        """Handle a command and return the result."""
        # Implement command handling logic here
        pass

    def _handle_command_result(self, command_result: dict):
        """Handle the result of a command."""
        # Implement command result handling logic here
        pass

    def _handle_command_error(self, error: Exception):
        """Handle a command error."""
        # Implement command error handling logic here
        pass

    def _handle_command_success(self, result: dict):
        """Handle a command success."""
        # Implement command success handling logic here
        pass

    def _handle_command_info(self, info: str):
        """Handle a command info."""
        # Implement command info handling logic here
        pass

    def _handle_command_warning(self, warning: str):
        """Handle a command warning."""
        # Implement command warning handling logic here
        pass

    def _handle_command_error(self, error: Exception):
        """Handle a command error."""
        # Implement command error handling logic here
        pass

    def _handle_command_success(self, result: dict):
        """Handle a command success."""
        # Implement command success handling logic here
        pass

    def _handle_command_info(self, info: str):
        """Handle a command info."""
        # Implement command info handling logic here
        pass

    def _handle_command_warning(self, warning: str):
        """Handle a command warning."""
        # Implement command warning handling logic here
        pass

    def _handle_command_error(self, error: Exception):
        """Handle a command error."""
        # Implement command error handling logic here
        pass

    def _handle_command_success(self, result: dict):
        """Handle a command success."""
        # Implement command success handling logic here
        pass

    def _handle_command_info(self, info: str):
        """Handle a command info."""
        # Implement command info handling logic here
        pass

    def _handle_command_warning(self, warning: str):
        """Handle a command warning."""
        # Implement command warning handling logic here
        pass 