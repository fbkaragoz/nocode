"""
Dynamic prompt template manager for configurable model behaviors.
"""

import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from config.constants import PromptType


logger = logging.getLogger(__name__)


class PromptManager:
    """Professional prompt template manager with configurable behaviors."""
    
    def __init__(self, prompts_file: str = "config/prompts.yaml"):
        """Initialize prompt manager with configurable prompts."""
        self.prompts_file = Path(prompts_file)
        self.prompts_config = {}
        self.load_prompts_config()
    
    def load_prompts_config(self) -> None:
        """Load prompt configuration from YAML file."""
        try:
            if self.prompts_file.exists():
                with open(self.prompts_file, 'r', encoding='utf-8') as f:
                    self.prompts_config = yaml.safe_load(f) or {}
                logger.info(f"Loaded prompt configuration from {self.prompts_file}")
            else:
                logger.warning(f"Prompts file not found: {self.prompts_file}")
                self.prompts_config = self._get_default_prompts()
        except Exception as e:
            logger.error(f"Failed to load prompts: {e}")
            self.prompts_config = self._get_default_prompts()
    
    def save_behaviors(self) -> None:
        """Save current behaviors to YAML file."""
        try:
            self.behaviors_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.behaviors_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.behaviors, f, default_flow_style=False, indent=2)
            logger.info("Behaviors saved successfully")
        except Exception as e:
            logger.error(f"Failed to save behaviors: {e}")
    
    def get_system_prompt(self, prompt_type: PromptType, context: Optional[Dict[str, Any]] = None) -> str:
        """Get system prompt for specific type with context enhancement."""
        prompt_key = prompt_type.value
        
        # Get base system prompt
        system_prompts = self.prompts_config.get('system_prompts', {})
        base_prompt = system_prompts.get(prompt_key, '')
        
        if not base_prompt:
            logger.warning(f"Prompt not found for {prompt_key}, using default")
            return self._get_default_system_prompt(prompt_type)
        
        # Enhance with context
        if context:
            enhanced_prompt = self._enhance_prompt_with_context(base_prompt, context)
            return enhanced_prompt
        
        return base_prompt
    
    def _enhance_prompt_with_context(self, base_prompt: str, context: Dict[str, Any]) -> str:
        """Enhance prompt with contextual information."""
        enhanced_parts = [base_prompt]
        
        # Get context modifiers from config
        context_modifiers = self.prompts_config.get('context_modifiers', {})
        
        # Add language-specific preferences
        if context.get('target_language'):
            lang = context['target_language']
            lang_specific = context_modifiers.get('language_specific', {})
            if lang in lang_specific:
                lang_context = lang_specific[lang].get('additional_context', '')
                if lang_context:
                    enhanced_parts.append(lang_context)
        
        # Add project type specific context
        if context.get('project_type'):
            project_type = context['project_type']
            project_types = context_modifiers.get('project_types', {})
            if project_type in project_types:
                project_context = project_types[project_type].get('additional_context', '')
                if project_context:
                    enhanced_parts.append(project_context)
        
        # Apply response style modifications
        response_styles = self.prompts_config.get('response_styles', {})
        
        # Add creativity level adjustments
        creativity = context.get('creativity_level', 'balanced')
        if creativity in response_styles:
            style_note = response_styles[creativity].get('style_note', '')
            if style_note:
                enhanced_parts.append(f"\nApproach: {style_note}")
        
        # Add verbosity level
        verbosity = context.get('verbosity', 'balanced')
        if verbosity in response_styles:
            style_note = response_styles[verbosity].get('style_note', '')
            if style_note:
                enhanced_parts.append(f"\nResponse style: {style_note}")
        
        # Add quality standards
        quality_level = context.get('quality_level', 'minimum')
        enhancement_rules = self.prompts_config.get('enhancement_rules', {})
        quality_standards = enhancement_rules.get('quality_standards', {})
        
        if quality_level == 'production':
            production_req = quality_standards.get('production_requirements', '')
            if production_req:
                enhanced_parts.append(production_req)
        else:
            minimum_req = quality_standards.get('minimum_requirements', '')
            if minimum_req:
                enhanced_parts.append(minimum_req)
        
        return '\n'.join(enhanced_parts)
    
    def get_behavior_config(self, prompt_type: PromptType) -> Dict[str, Any]:
        """Get behavior configuration for specific prompt type."""
        behavior_key = prompt_type.value
        return self.behaviors.get(behavior_key, {})
    
    def update_behavior(self, prompt_type: PromptType, config: Dict[str, Any]) -> None:
        """Update behavior configuration for specific prompt type."""
        behavior_key = prompt_type.value
        if behavior_key not in self.behaviors:
            self.behaviors[behavior_key] = {}
        
        self.behaviors[behavior_key].update(config)
        logger.info(f"Updated behavior for {behavior_key}")
    
    def get_temperature_for_type(self, prompt_type: PromptType) -> float:
        """Get recommended temperature for specific prompt type."""
        behavior_config = self.get_behavior_config(prompt_type)
        
        # Map creativity levels to temperature values
        creativity = behavior_config.get('creativity_level', 'balanced')
        temperature_map = {
            'conservative': 0.1,
            'balanced': 0.3,
            'creative': 0.7
        }
        
        return temperature_map.get(creativity, 0.3)
    
    def get_max_tokens_for_type(self, prompt_type: PromptType) -> int:
        """Get recommended max tokens for specific prompt type."""
        behavior_config = self.get_behavior_config(prompt_type)
        
        # Adjust based on verbosity
        verbosity = behavior_config.get('verbosity', 'balanced')
        base_tokens = 4096
        
        if verbosity == 'minimal':
            return int(base_tokens * 0.7)
        elif verbosity == 'detailed':
            return int(base_tokens * 1.5)
        else:
            return base_tokens
    
    def _get_default_prompts(self) -> Dict[str, Any]:
        """Get default prompts if file loading fails."""
        return {
            'system_prompts': {
                'code_generation': '''You are an expert software developer assistant. Generate clean, efficient, well-documented code.

CORE PRINCIPLES:
- Write production-ready code with proper error handling
- Follow language-specific best practices and conventions
- Include comprehensive documentation and comments
- Use appropriate design patterns and architecture
- Implement proper testing strategies when applicable
- Focus on maintainability, scalability, and performance''',
                
                'recursive_improvement': '''You are a senior code review and optimization specialist.
Analyze code systematically and provide actionable improvements.

ANALYSIS FRAMEWORK:
- Performance optimization opportunities
- Code quality and maintainability improvements
- Security vulnerabilities and best practices
- Error handling and edge case coverage''',
                
                'task_decomposition': '''You are a senior software architect and project manager.
Break down complex projects into manageable, actionable tasks.

DECOMPOSITION METHODOLOGY:
- Feature-based decomposition with clear boundaries
- Priority-based ordering using MoSCoW method
- Technology stack recommendations with rationale'''
            }
        }
    
    def _get_default_system_prompt(self, prompt_type: PromptType) -> str: #FIXME: "prompt_type" is not accessedPylance
        """Get default system prompt for unknown types."""
        return "You are a helpful AI assistant that generates high-quality code."
    
    def list_available_behaviors(self) -> list:
        """List all available behavior configurations."""
        return list(self.behaviors.keys())
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance-related configuration."""
        return self.behaviors.get('performance_config', {
            'code_generation_speed': 'balanced',
            'response_streaming': True,
            'token_prediction': True,
            'context_awareness': 'high'
        }) 