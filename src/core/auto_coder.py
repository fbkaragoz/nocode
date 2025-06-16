"""
AutoCoderEngine - Simple, streaming-first AI code generation engine.
"""

import logging
import re
import os
from typing import List, Optional, Dict, Iterator
from datetime import datetime
from pathlib import Path
import glob
import yaml

from src.config.settings import Settings
from src.services.ollama_service import OllamaService


logger = logging.getLogger(__name__)


class AutoCoderEngine:
    """
    Simple, streaming-first AI code generation engine.
    - Uses streaming for real-time output.
    - Loads prompt templates from an external .secret file.
    - Tracks last generated file for editing context.
    """
    
    def __init__(self, settings: Settings):
        """Initialize the engine."""
        self.settings = settings
        self.ollama = OllamaService(settings)
        self.display_manager = None  # Set by CLI manager
        self.prompt_templates = self._load_prompt_templates()
        self.last_generated_file = None  # Track last generated file
        self.conversation_context = []  # Simple conversation history
        
        logger.info("AutoCoderEngine (streaming-first) initialized")

    def _load_prompt_templates(self) -> Dict[str, str]:
        """Load prompt templates from the .secrets/prompts.yaml file."""
        try:
            secret_path = Path('./.secrets/prompts.yaml')
            if not secret_path.exists():
                logger.error(".secrets/prompts.yaml file not found!")
                return {}

            with open(secret_path, 'r', encoding='utf-8') as f:
                templates = yaml.safe_load(f)
            
            logger.info("Prompt templates loaded successfully.")
            return templates

        except Exception as e:
            logger.error(f"Failed to load prompts from .secrets/prompts.yaml: {e}")
            return {}

    def _is_edit_request(self, prompt: str) -> bool:
        """Check if the prompt is asking to edit/fix existing code."""
        edit_keywords = [
            'fix', 'error', 'bug', 'edit', 'modify', 'change', 'update', 
            'correct', 'repair', 'adjust', 'improve', 'hata', 'düzelt'
        ]
        return any(keyword in prompt.lower() for keyword in edit_keywords) or self._find_mentioned_file(prompt)

    def _find_mentioned_file(self, prompt: str) -> Optional[str]:
        """Find file mentioned in the prompt (e.g., @rps_game.py or its path)."""
        # Look for .py files, possibly prefixed with @ or as a path
        match = re.search(r'@?([\w/.-]+\.py)', prompt)
        if not match:
            return None

        found_path = match.group(1)
        
        # If it's a direct path that exists, use it
        if os.path.exists(found_path):
            return found_path

        # Otherwise, search for the basename in the workspace, prioritizing generated_code
        basename = os.path.basename(found_path)
        
        # Search recursively in 'generated_code' first
        matches = glob.glob(f"generated_code/**/{basename}", recursive=True)
        if matches:
            # Sort by modification time to get the newest one if multiple exist
            matches.sort(key=os.path.getmtime, reverse=True)
            return matches[0]
            
        # If not found, search the entire workspace
        matches = glob.glob(f"**/{basename}", recursive=True)
        if matches:
            matches.sort(key=os.path.getmtime, reverse=True)
            return matches[0]

        return None

    def _get_context_prompt(self, prompt: str) -> str:
        """Build context-aware prompt including conversation history."""
        context_parts = []
        
        # Add conversation history (last 3 exchanges)
        if self.conversation_context:
            context_parts.append("CONVERSATION HISTORY:")
            for i, ctx in enumerate(self.conversation_context[-3:], 1):
                context_parts.append(f"{i}. User: {ctx['user']}")
                if ctx.get('result'):
                    context_parts.append(f"   Result: {ctx['result']}")
        
        # Find target file for editing
        target_file = None
        if self._is_edit_request(prompt):
            # First try to find file mentioned in prompt
            target_file = self._find_mentioned_file(prompt)
            # If not found, use last generated file
            if not target_file and self.last_generated_file:
                target_file = self.last_generated_file
        
        # Add target file info if found
        if target_file:
            context_parts.append(f"\nTARGET FILE FOR EDITING: {target_file}")
            try:
                with open(target_file, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                context_parts.append(f"CURRENT FILE CONTENT:\n```python\n{file_content}\n```")
            except Exception as e:
                logger.warning(f"Could not read target file: {e}")
        
        context = "\n".join(context_parts) if context_parts else "No previous context."
        return context

    def test_connection(self) -> bool:
        """Test connection to Ollama."""
        return self.ollama.test_connection()
    
    def generate_code_stream(self, prompt: str, context: Optional[str] = None) -> Iterator[str]:
        """
        Generate code from a prompt, streaming the response.
        Includes the loaded prompt template and conversation context.
        """
        is_edit = self._is_edit_request(prompt)
        template_key = 'code_editing_template' if is_edit else 'code_creation_template'
        
        if not self.prompt_templates or template_key not in self.prompt_templates:
            logger.error("Prompt template could not be loaded. Using fallback.")
            fallback_prompt = f"USER_REQUEST: {prompt}"
            return self.ollama.stream_chat_completion(prompt=fallback_prompt)

        prompt_template = self.prompt_templates[template_key]
        
        # Build context for the prompt
        final_prompt = ""
        if is_edit:
            target_file = self._find_mentioned_file(prompt) or self.last_generated_file
            if target_file and os.path.exists(target_file):
                try:
                    with open(target_file, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                    
                    context_summary = self._get_context_summary()
                    
                    final_prompt = prompt_template.format(
                        user_request=prompt,
                        context=context_summary,
                        file_to_edit=target_file,
                        file_content=file_content
                    )
                    
                    # Ensure we update this file later
                    self.last_generated_file = target_file
                    
                except Exception as e:
                    logger.error(f"Error reading target file for editing: {e}")
                    is_edit = False # Fallback to creation
            else:
                is_edit = False # Fallback to creation if file not found
        
        if not is_edit:
             context_summary = self._get_context_summary()
             final_prompt = self.prompt_templates['code_creation_template'].format(
                 user_request=prompt,
                 context=context_summary
             )

        # Store in conversation context
        self.conversation_context.append({
            'user': prompt,
            'timestamp': datetime.now().isoformat()
        })
        
        return self.ollama.stream_chat_completion(prompt=final_prompt)
        
    def process_and_save_response(self, full_response: str, prompt: str) -> Dict[str, any]:
        """
        Process the full response string, parse it, and save the file.
        This method is now the single source of truth for handling model output.
        """
        filename = "generated_code.py" # Default
        code = None # Code must be explicitly found
        
        try:
            filename_match = re.search(r'\[filename\]:\s*([\w/.-]+\.py)', full_response, re.IGNORECASE)
            if filename_match:
                filename = filename_match.group(1).strip()
            
            # STRICT PARSING: Only accept code inside a proper code block.
            code_match = re.search(r'```(?:\w+)?\n(.*?)\n```', full_response, re.DOTALL)
            if code_match:
                code = code_match.group(1).strip()
            else:
                logger.warning("No valid code block found in the model's response.")
                # Do not save if no code block is found.
                return { "saved_file": None, "error": "No valid code block found." }

        except Exception as e:
            logger.error(f"Error parsing structured response: {e}")
            return { "saved_file": None, "error": f"Parsing error: {e}" }
        
        # Determine if this is an edit or a new file, and save accordingly
        saved_file = None
        if self._is_edit_request(prompt):
            target_file = self.last_generated_file
            if target_file and os.path.exists(target_file):
                saved_file = self._update_existing_file(target_file, code)
            else:
                logger.warning(f"Edit request for non-existent file '{target_file}'. Saving as new file.")
                saved_file = self._save_code(filename, code, prompt)
        else:
            saved_file = self._save_code(filename, code, prompt)
        
        # Update state for the next command
        if saved_file:
            self.last_generated_file = saved_file
            # Update conversation context with the successful action
            if self.conversation_context:
                self.conversation_context[-1]['result'] = f"File saved to: {saved_file}"
        
        return {
            "full_response": full_response,
            "saved_file": saved_file,
            "parsed_filename": filename,
            "parsed_code": code
        }

    def _update_existing_file(self, file_path: str, new_code: str) -> Optional[str]:
        """Update an existing file with new code."""
        try:
            # Create backup
            backup_path = f"{file_path}.backup"
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # Write new code
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_code)
            
            logger.info(f"Updated existing file: {file_path} (backup: {backup_path})")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to update existing file: {e}")
            return None
    
    def _save_code(self, filename: str, code: str, prompt: str) -> Optional[str]:
        """
        Save a single block of code to a stable directory, preventing subdirectories.
        This is a critical function for maintaining project state.
        """
        try:
            output_dir = Path("generated_code")
            output_dir.mkdir(exist_ok=True)
            
            # CRITICAL: Sanitize filename to prevent any directory creation.
            # We only want the final part of the path (the basename).
            safe_basename = os.path.basename(filename)
            safe_basename = re.sub(r'[^\w\.-]', '', safe_basename)

            # If the resulting name is empty or just a dot, fallback to a prompt-based name.
            if not safe_basename or safe_basename == '.':
                 safe_prompt = re.sub(r'[^\w\s-]', '', prompt)[:30].strip()
                 safe_prompt = re.sub(r'[-\s]+', '_', safe_prompt)
                 safe_basename = f"{safe_prompt or 'untitled'}.py"

            file_path = output_dir / safe_basename
            
            # To prevent accidental overwrites on NEW file creation, add a timestamp if it exists.
            # Updates to existing files are handled by _update_existing_file.
            if file_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                base, ext = os.path.splitext(safe_basename)
                file_path = output_dir / f"{base}_{timestamp}{ext}"

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code)
            
            logger.info(f"Code saved to: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to save code: {e}")
            return None

    def _get_context_summary(self) -> str:
        """Build a summary of the conversation history for context."""
        if not self.conversation_context:
            return "No previous conversation history."
        
        summary_parts = []
        for i, ctx in enumerate(self.conversation_context[-3:], 1):
            summary_parts.append(f"{i}. User: {ctx['user']}")
            if ctx.get('result'):
                summary_parts.append(f"   Result: {ctx['result']}")
        
        return "\n".join(summary_parts) 