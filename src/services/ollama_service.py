"""
Ollama API service for communication with local Ollama instance.
"""

import logging
import requests
from typing import Dict, List, Optional, Any
import time

from config.settings import Settings
from config.constants import API_ENDPOINTS
from models.code_request import CodeRequest
from models.code_response import CodeResponse, PerformanceMetrics


logger = logging.getLogger(__name__)


class OllamaService:
    """Service for interacting with Ollama API."""
    
    def __init__(self, settings: Settings):
        """Initialize Ollama service with settings."""
        self.settings = settings
        self.session = requests.Session()
        self.conversation_history: List[Dict[str, str]] = []
        
    def check_connection(self) -> bool:
        """Check if Ollama service is available."""
        try:
            response = self.session.get(
                f"{self.settings.ollama_url}{API_ENDPOINTS['TAGS']}",
                timeout=5
            )
            if response.status_code == 200:
                models = response.json().get('models', [])
                available_models = [model['name'] for model in models]
                
                # Only log once during initialization, not during periodic checks
                if not hasattr(self, '_initial_connection_logged'):
                    logger.info(f"Available models: {available_models}")
                    self._initial_connection_logged = True
                
                # Check if configured model is available
                model_available = any(
                    self.settings.model_name in model or model in self.settings.model_name 
                    for model in available_models
                )
                
                if not model_available and not hasattr(self, '_model_warning_logged'):
                    logger.warning(f"Configured model '{self.settings.model_name}' not found in available models")
                    logger.info(f"Consider using one of: {available_models}")
                    self._model_warning_logged = True
                
                return model_available
            
            return False
            
        except Exception as e:
            # Only log connection errors if they're different from the last one
            error_msg = f"Ollama connection error: {e}"
            if not hasattr(self, '_last_connection_error') or self._last_connection_error != str(e):
                logger.error(error_msg)
                self._last_connection_error = str(e)
            return False
    
    def generate_chat_response(self, request: CodeRequest) -> CodeResponse:
        """Generate response using Ollama chat API."""
        start_time = time.time()
        
        try:
            # Prepare messages for chat API
            messages = [
                {"role": "system", "content": self._get_system_message(request)},
                *self.conversation_history,
                {"role": "user", "content": request.prompt}
            ]
            
            payload = {
                "model": self.settings.model_name,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": request.temperature,
                    "num_predict": request.max_tokens,
                    "top_p": self.settings.get("model_params.top_p", 0.9),
                    "top_k": self.settings.get("model_params.top_k", 40)
                }
            }
            
            logger.info(f"Sending request to Ollama: {request.prompt[:100]}...")
            
            response = self.session.post(
                f"{self.settings.ollama_url}{API_ENDPOINTS['CHAT']}",
                json=payload,
                timeout=self.settings.timeout
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('message', {}).get('content', '')
                
                # Update conversation history
                self._update_conversation_history(request.prompt, content)
                
                # Create performance metrics
                performance = PerformanceMetrics(
                    response_time=response_time,
                    token_count=result.get('eval_count', 0),
                    tokens_per_second=self._calculate_tokens_per_second(
                        result.get('eval_count', 0), 
                        result.get('eval_duration', 0)
                    ),
                    model_name=result.get('model', self.settings.model_name),
                    eval_count=result.get('eval_count', 0),
                    eval_duration=result.get('eval_duration', 0)
                )
                
                return CodeResponse(
                    success=True,
                    content=content,
                    performance=performance
                )
            else:
                error_msg = f"API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return CodeResponse(
                    success=False,
                    content="",
                    error_message=error_msg
                )
                
        except Exception as e:
            error_msg = f"Request failed: {str(e)}"
            logger.error(error_msg)
            return CodeResponse(
                success=False,
                content="",
                error_message=error_msg
            )
    
    def _get_system_message(self, request: CodeRequest) -> str:
        """Get system message based on request type."""
        # Try to use template manager for dynamic prompts
        try:
            from templates.prompt_manager import PromptManager
            prompt_manager = PromptManager()
            context = {
                'target_language': request.target_language.value if request.target_language else None
            }
            return prompt_manager.get_system_prompt(request.prompt_type, context)
        except ImportError:
            # Fallback to static prompts
            from config.constants import DEFAULT_SYSTEM_MESSAGES
            return DEFAULT_SYSTEM_MESSAGES.get(
                request.prompt_type.value,
                DEFAULT_SYSTEM_MESSAGES["code_generation"]
            )
    
    def _update_conversation_history(self, user_message: str, assistant_message: str) -> None:
        """Update conversation history with new messages."""
        self.conversation_history.append({"role": "user", "content": user_message})
        self.conversation_history.append({"role": "assistant", "content": assistant_message})
        
        # Keep only last 20 messages (10 exchanges) for memory management
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
    
    def _calculate_tokens_per_second(self, token_count: int, duration_ns: float) -> float:
        """Calculate tokens per second from duration in nanoseconds."""
        if duration_ns == 0:
            return 0.0
        
        duration_seconds = duration_ns / 1e9
        return token_count / duration_seconds if duration_seconds > 0 else 0.0
    
    def clear_conversation_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history.clear()
        logger.info("Conversation history cleared")
    
    def get_available_models(self) -> List[str]:
        """Get list of available models."""
        try:
            response = self.session.get(
                f"{self.settings.ollama_url}{API_ENDPOINTS['TAGS']}",
                timeout=5
            )
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [model['name'] for model in models]
            return []
        except Exception as e:
            logger.error(f"Failed to get available models: {e}")
            return []
    
    def get_model_info(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Get information about a specific model."""
        target_model = model_name or self.settings.model_name
        
        try:
            payload = {"name": target_model}
            response = self.session.post(
                f"{self.settings.ollama_url}{API_ENDPOINTS['SHOW']}",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get model info: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return {} 