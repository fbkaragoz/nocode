"""
Core Auto Coder Engine with recursive improvement and task decomposition.
"""

import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from config.settings import Settings
from config.constants import PromptType, CodeLanguage, FILE_EXTENSIONS
from models.code_request import CodeRequest
from models.code_response import CodeResponse, CodeBlock
from services.ollama_service import OllamaService


logger = logging.getLogger(__name__)


class AutoCoderEngine:
    """Main engine for automatic code generation with advanced features."""
    
    def __init__(self, settings: Settings, ollama_service: OllamaService):
        """Initialize the auto coder engine."""
        self.settings = settings
        self.ollama = ollama_service
    
    def generate_code(self, request: CodeRequest) -> CodeResponse:
        """Generate code based on request."""
        logger.info(f"Generating code for: {request.prompt[:100]}...")
        
        # Get response from Ollama
        response = self.ollama.generate_chat_response(request)
        
        if response.success:
            # Extract code blocks from response
            code_blocks = self._extract_code_blocks(response.content)
            response.code_blocks = code_blocks
            
            logger.info(f"Generated {len(code_blocks)} code blocks")
        
        return response
    
    def improve_code_recursively(self, code: str, max_cycles: Optional[int] = None) -> List[CodeResponse]:
        """Recursively improve code through multiple iterations."""
        if max_cycles is None:
            max_cycles = self.settings.max_improvement_cycles
        
        improvements = []
        current_code = code
        
        for cycle in range(max_cycles):
            logger.info(f"Improvement cycle {cycle + 1}/{max_cycles}")
            
            # Create improvement request
            improvement_prompt = f"""
            Analyze the following code and provide improvements:
            
            ```
            {current_code}
            ```
            
            Focus on:
            1. Performance optimizations
            2. Code quality improvements
            3. Security vulnerabilities
            4. Best practices compliance
            5. Refactoring opportunities
            
            Provide the improved version of the code.
            """
            
            request = CodeRequest(
                prompt=improvement_prompt,
                prompt_type=PromptType.RECURSIVE_IMPROVEMENT,
                temperature=0.1
            )
            
            response = self.generate_code(request)
            
            if response.success and response.code_blocks:
                # Use the first code block as the improved version
                current_code = response.code_blocks[0].code
                improvements.append(response)
            else:
                logger.warning(f"Improvement cycle {cycle + 1} failed")
                break
        
        return improvements
    
    def break_down_task(self, task_description: str) -> CodeResponse:
        """Break down complex task into manageable subtasks."""
        breakdown_prompt = f"""
        Analyze the following complex software development task and break it down:
        
        TASK: {task_description}
        
        Provide:
        1. Main task analysis
        2. Subtask list (ordered by priority)
        3. Required technologies for each subtask
        4. Estimated effort
        5. Dependency analysis
        6. Risk assessment
        
        Then create code examples for the highest priority subtask.
        """
        
        request = CodeRequest(
            prompt=breakdown_prompt,
            prompt_type=PromptType.TASK_DECOMPOSITION,
            temperature=0.2
        )
        
        return self.generate_code(request)
    
    def save_code_blocks(self, code_blocks: List[CodeBlock], task_name: str) -> List[str]:
        """Save code blocks to files."""
        saved_files = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(self.settings.output_directory) / f"{task_name}_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for i, block in enumerate(code_blocks):
            # Determine file extension
            extension = FILE_EXTENSIONS.get(block.language.value, ".txt")
            filename = f"block_{i+1}_{block.language.value}{extension}"
            filepath = output_dir / filename
            
            # Write code to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(block.code)
            
            saved_files.append(str(filepath))
            logger.info(f"Code saved to: {filepath}")
        
        return saved_files
    
    def clear_conversation_history(self) -> None:
        """Clear conversation history."""
        self.ollama.clear_conversation_history()
    
    def _extract_code_blocks(self, content: str) -> List[CodeBlock]:
        """Extract code blocks from markdown-formatted content."""
        code_blocks = []
        pattern = r'```(\w+)?\n(.*?)\n```'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for i, (language, code) in enumerate(matches):
            # Map language string to CodeLanguage enum
            lang = self._map_language(language or "text")
            
            code_blocks.append(CodeBlock(
                id=f"block_{i+1}",
                language=lang,
                code=code.strip()
            ))
        
        return code_blocks
    
    def _map_language(self, language_str: str) -> CodeLanguage:
        """Map language string to CodeLanguage enum."""
        language_mapping = {
            "py": CodeLanguage.PYTHON,
            "python": CodeLanguage.PYTHON,
            "js": CodeLanguage.JAVASCRIPT,
            "javascript": CodeLanguage.JAVASCRIPT,
            "ts": CodeLanguage.TYPESCRIPT,
            "typescript": CodeLanguage.TYPESCRIPT,
            "java": CodeLanguage.JAVA,
            "cpp": CodeLanguage.CPP,
            "c++": CodeLanguage.CPP,
            "c": CodeLanguage.C,
            "go": CodeLanguage.GO,
            "golang": CodeLanguage.GO,
            "rust": CodeLanguage.RUST,
            "rs": CodeLanguage.RUST,
            "php": CodeLanguage.PHP,
            "ruby": CodeLanguage.RUBY,
            "rb": CodeLanguage.RUBY,
            "cs": CodeLanguage.CSHARP,
            "csharp": CodeLanguage.CSHARP,
            "html": CodeLanguage.HTML,
            "css": CodeLanguage.CSS,
            "sql": CodeLanguage.SQL,
            "bash": CodeLanguage.BASH,
            "sh": CodeLanguage.SHELL,
            "shell": CodeLanguage.SHELL,
        }
        
        return language_mapping.get(language_str.lower(), CodeLanguage.PYTHON) 