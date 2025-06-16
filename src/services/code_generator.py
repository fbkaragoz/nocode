"""
Code generation service with advanced features.
"""

import logging
from typing import List, Dict, Any

from config.settings import Settings
from config.constants import PromptType, CodeLanguage
from models.code_request import CodeRequest
from models.code_response import CodeResponse
from services.ollama_service import OllamaService


logger = logging.getLogger(__name__)


class CodeGeneratorService:
    """Service for generating code with various strategies."""
    
    def __init__(self, settings: Settings, ollama_service: OllamaService):
        """Initialize code generator service."""
        self.settings = settings
        self.ollama = ollama_service
    
    def generate_with_context(self, prompt: str, context: Dict[str, Any]) -> CodeResponse:
        """Generate code with additional context."""
        enhanced_prompt = self._enhance_prompt_with_context(prompt, context)
        
        request = CodeRequest(
            prompt=enhanced_prompt,
            prompt_type=PromptType.CODE_GENERATION,
            temperature=context.get('temperature', self.settings.temperature),
            max_tokens=context.get('max_tokens', self.settings.max_tokens)
        )
        
        return self.ollama.generate_chat_response(request)
    
    def generate_multi_language(self, prompt: str, languages: List[CodeLanguage]) -> Dict[CodeLanguage, CodeResponse]:
        """Generate code in multiple programming languages."""
        results = {}
        
        for language in languages:
            language_prompt = f"{prompt}\n\nGenerate the solution in {language.value}."
            
            request = CodeRequest(
                prompt=language_prompt,
                target_language=language,
                prompt_type=PromptType.CODE_GENERATION
            )
            
            response = self.ollama.generate_chat_response(request)
            results[language] = response
        
        return results
    
    def generate_with_tests(self, prompt: str) -> CodeResponse:
        """Generate code along with unit tests."""
        enhanced_prompt = f"""
        {prompt}
        
        Requirements:
        1. Implement the main functionality
        2. Include comprehensive unit tests
        3. Add proper error handling
        4. Use type hints and docstrings
        5. Follow best practices for the chosen language
        
        Structure the response with:
        - Main implementation code
        - Unit test code
        - Usage examples
        """
        
        request = CodeRequest(
            prompt=enhanced_prompt,
            prompt_type=PromptType.CODE_GENERATION,
            temperature=0.1  # Lower temperature for more consistent test generation
        )
        
        return self.ollama.generate_chat_response(request)
    
    def _enhance_prompt_with_context(self, prompt: str, context: Dict[str, Any]) -> str:
        """Enhance prompt with additional context information."""
        enhanced_parts = [prompt]
        
        if context.get('project_type'):
            enhanced_parts.append(f"Project type: {context['project_type']}")
        
        if context.get('technologies'):
            tech_list = ', '.join(context['technologies'])
            enhanced_parts.append(f"Required technologies: {tech_list}")
        
        if context.get('constraints'):
            enhanced_parts.append(f"Constraints: {context['constraints']}")
        
        if context.get('style_guide'):
            enhanced_parts.append(f"Style guide: {context['style_guide']}")
        
        return '\n\n'.join(enhanced_parts) 