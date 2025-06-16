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
    """Manages dynamic prompt templates and model behaviors."""
    
    def __init__(self, behaviors_file: str = "src/templates/model_behaviors.yaml"):
        """Initialize prompt manager with behaviors file."""
        self.behaviors_file = Path(behaviors_file)
        self.behaviors = {}
        self.load_behaviors()
    
    def load_behaviors(self) -> None:
        """Load model behaviors from YAML file."""
        try:
            if self.behaviors_file.exists():
                with open(self.behaviors_file, 'r', encoding='utf-8') as f:
                    self.behaviors = yaml.safe_load(f) or {}
                logger.info(f"Loaded model behaviors from {self.behaviors_file}")
            else:
                logger.warning(f"Behaviors file not found: {self.behaviors_file}")
                self.behaviors = self._get_default_behaviors()
        except Exception as e:
            logger.error(f"Failed to load behaviors: {e}")
            self.behaviors = self._get_default_behaviors()
    
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
        behavior_key = prompt_type.value
        
        if behavior_key not in self.behaviors:
            logger.warning(f"Behavior not found for {behavior_key}, using default")
            return self._get_default_system_prompt(prompt_type)
        
        behavior_config = self.behaviors[behavior_key]
        base_prompt = behavior_config.get('system_prompt', '')
        
        # Enhance with context
        if context:
            enhanced_prompt = self._enhance_prompt_with_context(base_prompt, behavior_config, context)
            return enhanced_prompt
        
        return base_prompt
    
    def _enhance_prompt_with_context(self, base_prompt: str, config: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Enhance prompt with contextual information."""
        enhanced_parts = [base_prompt]
        
        # Add language-specific preferences
        if context.get('target_language'):
            lang = context['target_language']
            if lang in self.behaviors.get('language_preferences', {}):
                lang_prefs = self.behaviors['language_preferences'][lang]
                enhanced_parts.append(f"\nLanguage-specific guidelines for {lang}:")
                enhanced_parts.append(f"- Style guide: {lang_prefs.get('style_guide', 'standard')}")
                if 'frameworks' in lang_prefs:
                    enhanced_parts.append(f"- Preferred frameworks: {', '.join(lang_prefs['frameworks'])}")
                if 'testing' in lang_prefs:
                    enhanced_parts.append(f"- Testing framework: {lang_prefs['testing']}")
        
        # Add creativity level adjustments
        creativity = config.get('creativity_level', 'balanced')
        if creativity == 'creative':
            enhanced_parts.append("\nApproach: Be creative and explore innovative solutions.")
        elif creativity == 'conservative':
            enhanced_parts.append("\nApproach: Use well-established, proven patterns and practices.")
        
        # Add code style preferences
        code_style = config.get('code_style', 'production')
        if code_style == 'production':
            enhanced_parts.append("\nCode quality: Production-ready with comprehensive error handling.")
        elif code_style == 'prototype':
            enhanced_parts.append("\nCode quality: Focus on rapid prototyping and core functionality.")
        
        # Add verbosity level
        verbosity = config.get('verbosity', 'balanced')
        if verbosity == 'detailed':
            enhanced_parts.append("\nExplanation level: Provide detailed explanations and comments.")
        elif verbosity == 'minimal':
            enhanced_parts.append("\nExplanation level: Keep explanations concise and focused.")
        
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
    
    def _get_default_behaviors(self) -> Dict[str, Any]:
        """Get default behaviors if file loading fails."""
        return {
            'code_generation': {
                'personality': 'expert_developer',
                'creativity_level': 'balanced',
                'code_style': 'production',
                'verbosity': 'detailed',
                'system_prompt': '''You are an expert software developer.
Generate clean, efficient, and well-documented code.
Include proper error handling and follow best practices.'''
            },
            'recursive_improvement': {
                'focus_areas': ['performance_optimization', 'code_quality'],
                'analysis_depth': 'comprehensive',
                'system_prompt': '''You are a code review specialist.
Analyze code and provide concrete improvement suggestions.
Focus on performance, security, and maintainability.'''
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