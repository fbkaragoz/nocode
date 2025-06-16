"""
Input Handler - Clean user input management and validation.
Handles all user input processing and validation.
"""

import logging
from typing import Optional, List
from datetime import datetime

from core.interface import DisplayManager


logger = logging.getLogger(__name__)


class InputHandler:
    """
    Input Handler - Clean input management architecture.
    
    Responsibilities:
    - Handle user input with proper validation
    - Manage input history
    - Provide input suggestions
    - Handle special input cases
    """
    
    def __init__(self, display_manager: DisplayManager):
        """Initialize input handler with display manager."""
        self.display_manager = display_manager
        self.input_history = []
        self.max_history = 100
        
        # Input validation patterns
        self.command_patterns = [
            'generate', 'improve', 'breakdown', 'explain', 
            'help', 'clear', 'exit', 'quit'
        ]
    
    def get_user_input(self) -> Optional[str]:
        """Get user input with validation and preprocessing."""
        try:
            # Get raw input from display manager
            raw_input = self.display_manager.get_user_input()
            
            if raw_input is None:
                return None
            
            # Preprocess input
            processed_input = self._preprocess_input(raw_input)
            
            # Validate input
            if not self._validate_input(processed_input):
                return None
            
            # Add to history
            self._add_to_history(processed_input)
            
            return processed_input
            
        except KeyboardInterrupt:
            raise
        except Exception as e:
            logger.error(f"Input handling error: {e}")
            return None
    
    def _preprocess_input(self, raw_input: str) -> str:
        """Preprocess user input for consistency."""
        if not raw_input:
            return ""
        
        # Strip whitespace
        processed = raw_input.strip()
        
        # Handle multi-line input
        if '\n' in processed:
            processed = ' '.join(line.strip() for line in processed.split('\n') if line.strip())
        
        # Normalize whitespace
        processed = ' '.join(processed.split())
        
        return processed
    
    def _validate_input(self, user_input: str) -> bool:
        """Validate user input."""
        if not user_input:
            return False
        
        # Check for minimum length
        if len(user_input.strip()) < 1:
            return False
        
        # Check for maximum length
        if len(user_input) > 5000:
            self.display_manager.show_error("Input too long. Please keep it under 5000 characters.")
            return False
        
        # Check for potentially harmful content
        if self._contains_harmful_content(user_input):
            self.display_manager.show_error("Input contains potentially harmful content.")
            return False
        
        return True
    
    def _contains_harmful_content(self, user_input: str) -> bool:
        """Check for potentially harmful content."""
        # Basic check for potentially harmful patterns
        harmful_patterns = [
            'rm -rf',
            'del /f',
            'format c:',
            'DROP TABLE',
            'DELETE FROM',
            'shutdown',
            'reboot'
        ]
        
        user_input_lower = user_input.lower()
        return any(pattern.lower() in user_input_lower for pattern in harmful_patterns)
    
    def _add_to_history(self, user_input: str):
        """Add input to history with timestamp."""
        history_entry = {
            'input': user_input,
            'timestamp': datetime.now().isoformat(),
            'length': len(user_input)
        }
        
        self.input_history.append(history_entry)
        
        # Keep only recent history
        if len(self.input_history) > self.max_history:
            self.input_history = self.input_history[-self.max_history:]
    
    def get_input_suggestions(self, partial_input: str) -> List[str]:
        """Get input suggestions based on partial input."""
        if not partial_input:
            return []
        
        suggestions = []
        partial_lower = partial_input.lower()
        
        # Command suggestions
        for command in self.command_patterns:
            if command.startswith(partial_lower):
                suggestions.append(command)
        
        # History suggestions
        for entry in reversed(self.input_history):
            if entry['input'].lower().startswith(partial_lower):
                if entry['input'] not in suggestions:
                    suggestions.append(entry['input'])
                    if len(suggestions) >= 5:
                        break
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def get_input_statistics(self) -> dict:
        """Get input statistics for monitoring."""
        if not self.input_history:
            return {}
        
        total_inputs = len(self.input_history)
        avg_length = sum(entry['length'] for entry in self.input_history) / total_inputs
        
        # Command usage stats
        command_usage = {}
        for entry in self.input_history:
            first_word = entry['input'].split()[0].lower() if entry['input'].split() else 'unknown'
            command_usage[first_word] = command_usage.get(first_word, 0) + 1
        
        return {
            'total_inputs': total_inputs,
            'average_length': round(avg_length, 1),
            'command_usage': command_usage,
            'recent_inputs': [entry['input'][:50] + '...' if len(entry['input']) > 50 else entry['input'] 
                            for entry in self.input_history[-5:]]
        }
    
    def clear_history(self):
        """Clear input history."""
        self.input_history.clear()
        logger.info("Input history cleared")
    
    def save_history(self, filepath: str):
        """Save input history to file."""
        try:
            import json
            with open(filepath, 'w') as f:
                json.dump(self.input_history, f, indent=2)
            logger.info(f"Input history saved to: {filepath}")
        except Exception as e:
            logger.error(f"Failed to save input history: {e}")
    
    def load_history(self, filepath: str):
        """Load input history from file."""
        try:
            import json
            with open(filepath, 'r') as f:
                self.input_history = json.load(f)
            logger.info(f"Input history loaded from: {filepath}")
        except Exception as e:
            logger.error(f"Failed to load input history: {e}") 