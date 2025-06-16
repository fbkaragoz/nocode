"""
Command Processor - Post-stream processing and file saving.
"""

import logging
import re
import os
from typing import Dict, Optional, Iterator
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass

from src.core.auto_coder import AutoCoderEngine
from src.config.settings import Settings
from src.core.interface.display_manager import DisplayManager


logger = logging.getLogger(__name__)


@dataclass
class CommandResult:
    """Data class for command processing results."""
    prompt: str
    context: Optional[str] = None
    
    
class CommandProcessor:
    """Processes commands and orchestrates the code generation."""
    
    def __init__(self, settings: Settings, display_manager: DisplayManager):
        """Initialize the command processor."""
        self.settings = settings
        self.display_manager = display_manager
        self.engine = AutoCoderEngine(settings)
        self.engine.display_manager = display_manager

    def generate_stream(self, prompt: str) -> Iterator[str]:
        """
        Gets the raw stream from the engine for a given prompt.
        """
        return self.engine.generate_code_stream(prompt)

    def save_response(self, full_response: str, prompt: str) -> Dict:
        """
        Passes the full response to the engine for processing and saving.
        """
        return self.engine.process_and_save_response(full_response, prompt)

    def handle_command(self, user_input: str) -> CommandResult:
        """Handles special commands like 'improve'."""
        if user_input.strip().lower().startswith("improve"):
            if self.engine.last_generated_file and os.path.exists(self.engine.last_generated_file):
                with open(self.engine.last_generated_file, 'r', encoding='utf-8') as f:
                    context = f.read()
                
                # The prompt for improvement is the part after "improve"
                prompt = user_input.strip()[len("improve:"):].strip()
                if not prompt:
                    prompt = "Improve the previous code."
                    
                return CommandResult(prompt=prompt, context=context)
            else:
                return CommandResult(
                    prompt="There is no file to improve. Please generate a file first.", 
                    context=None
                )
        
        return CommandResult(prompt=user_input)

    def process_and_save(self, full_response: str, prompt: str) -> Dict:
        """Parse the full response, extract components, and save the code."""
        
        filename = self._parse_value(r'\[filename\]:\s*(.*)', full_response, "generated_code.py")
        code = self._parse_code(full_response)
        
        if not code.strip():
            logger.warning("No code found in the response to save.")
            return {"saved_file": None, "filename": None, "code": None}

        saved_file = self._save_code(filename, code, prompt)
        
        if saved_file:
            self.engine.last_generated_file = saved_file
            
        return {
            "saved_file": saved_file,
            "filename": filename,
            "code": code
        }

    def _parse_value(self, pattern: str, text: str, default: str) -> str:
        """Utility to parse a value from text using regex."""
        match = re.search(pattern, text)
        return match.group(1).strip() if match else default

    def _parse_code(self, text: str) -> str:
        """Extracts code from markdown-style code blocks."""
        match = re.search(r'```(?:\w+)?\n(.*?)\n```', text, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # Fallback if no markdown block is found, remove the [filename] part
        return re.sub(r'\[filename\]:\s*(.*)\n---\n', '', text).strip()

    def _save_code(self, filename: str, code: str, prompt: str) -> Optional[str]:
        """Saves the code to a file with a descriptive directory."""
        try:
            output_dir_name = self.settings.get("code_generation.output_directory", "generated_code")
            output_dir = Path(output_dir_name)
            
            # Create a subdirectory based on the sanitized prompt and timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_prompt = re.sub(r'[^\w\s-]', '', prompt)[:30].strip()
            safe_prompt = re.sub(r'[-\s]+', '_', safe_prompt)
            session_dir = output_dir / f"{safe_prompt}_{timestamp}"
            
            session_dir.mkdir(parents=True, exist_ok=True)
            
            # Sanitize filename just in case
            safe_filename = os.path.basename(filename)
            file_path = session_dir / safe_filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code)
            
            logger.info(f"Code saved to: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to save code: {e}", exc_info=True)
            return None 