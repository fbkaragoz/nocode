"""
Code request data model.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from config.constants import PromptType, CodeLanguage


@dataclass
class CodeRequest:
    """Represents a code generation request."""
    
    description: str  # Main description/prompt
    prompt_type: PromptType = PromptType.CODE_GENERATION
    language: str = "auto-detect"  # Simplified language field
    target_language: Optional[CodeLanguage] = None
    context: Optional[str] = None
    requirements: Optional[List[str]] = field(default_factory=list)
    special_instructions: Optional[str] = None
    temperature: float = 0.1
    max_tokens: int = 4096
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def prompt(self) -> str:
        """Backward compatibility property."""
        return self.description
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "description": self.description,
            "prompt_type": self.prompt_type.value if self.prompt_type else None,
            "language": self.language,
            "target_language": self.target_language.value if self.target_language else None,
            "context": self.context,
            "requirements": self.requirements,
            "special_instructions": self.special_instructions,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CodeRequest':
        """Create from dictionary representation."""
        # Handle enum conversions
        prompt_type = None
        if data.get("prompt_type"):
            prompt_type = PromptType(data["prompt_type"])
        
        target_language = None
        if data.get("target_language"):
            target_language = CodeLanguage(data["target_language"])
        
        created_at = datetime.now()
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])
        
        return cls(
            description=data.get("description", data.get("prompt", "")),
            prompt_type=prompt_type,
            language=data.get("language", "auto-detect"),
            target_language=target_language,
            context=data.get("context"),
            requirements=data.get("requirements", []),
            special_instructions=data.get("special_instructions"),
            temperature=data.get("temperature", 0.1),
            max_tokens=data.get("max_tokens", 4096),
            created_at=created_at,
            metadata=data.get("metadata", {})
        )
    
    def __str__(self) -> str:
        """String representation."""
        return f"CodeRequest(description='{self.description[:50]}...', type={self.prompt_type}, lang={self.language})" 