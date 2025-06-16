"""
Ollama API service for communication with local Ollama instance.
"""

import logging
import requests
import json
from typing import Dict, List, Optional, Any, Iterator

from src.config.settings import Settings


logger = logging.getLogger(__name__)


class OllamaService:
    """Service for interacting with Ollama API using the chat endpoint."""

    def __init__(self, settings: Settings):
        """Initialize Ollama service with settings."""
        self.settings = settings
        self.session = requests.Session()
        self.conversation_history: List[Dict[str, str]] = []
        self.base_url = self.settings.get("ollama.base_url")
        self.model_name = self.settings.get("ollama.model_name")

    def test_connection(self) -> bool:
        """Check if Ollama service is available."""
        try:
            health_check_url = self.base_url.replace("/api", "")
            response = self.session.get(health_check_url, timeout=3)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            logger.error(f"Ollama connection failed at {self.base_url}")
            return False

    def stream_chat_completion(self, prompt: str) -> Iterator[str]:
        """
        Generate a streaming chat response from Ollama.
        This method maintains conversation history.
        """
        url = f"{self.base_url}/generate"

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": self.settings.get("ollama.temperature", 0.7),
                "top_p": self.settings.get("ollama.top_p", 0.9),
                "top_k": self.settings.get("ollama.top_k", 40),
            },
        }

        full_response_content = ""
        try:
            with self.session.post(
                url,
                json=payload,
                stream=True,
                timeout=self.settings.get("ollama.timeout", 300),
            ) as response:
                response.raise_for_status()

                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            content_part = chunk.get("response", "")
                            if content_part:
                                full_response_content += content_part
                                yield content_part

                            if chunk.get("done"):
                                break
                        except json.JSONDecodeError:
                            logger.warning(f"Could not decode JSON line: {line}")

        except requests.exceptions.RequestException as e:
            error_message = f"[ERROR] Ollama request failed: {e}"
            logger.error(error_message)
            yield error_message

    def _trim_history(self):
        """Keep the conversation history to a manageable size."""
        max_history = self.settings.get("ollama.history_size", 10)
        if len(self.conversation_history) > max_history * 2:
            self.conversation_history = self.conversation_history[-(max_history * 2) :]

    def clear_conversation_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history.clear()
        logger.info("Conversation history cleared")

    def get_available_models(self) -> list:
        """Get list of available models from Ollama."""
        try:
            response = self.session.get(f"{self.base_url}/tags", timeout=10)
            response.raise_for_status()
            models = response.json().get("models", [])
            return [model["name"] for model in models]
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get models from Ollama: {e}")
            return []
    
    def get_model_info(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Get information about a specific model."""
        target_model = model_name or self.model_name
        
        try:
            payload = {"name": target_model}
            response = self.session.post(
                f"{self.base_url}/show",
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