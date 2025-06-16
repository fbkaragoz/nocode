"""
Code response data model.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from config.constants import CodeLanguage


@dataclass
class CodeBlock:
    """Represents a single code block."""
    
    id: str
    language: CodeLanguage
    code: str
    description: Optional[str] = None
    file_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "language": self.language.value,
            "code": self.code,
            "description": self.description,
            "file_path": self.file_path
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CodeBlock':
        """Create from dictionary representation."""
        return cls(
            id=data["id"],
            language=CodeLanguage(data["language"]),
            code=data["code"],
            description=data.get("description"),
            file_path=data.get("file_path")
        )


@dataclass
class PerformanceMetrics:
    """Performance metrics for code generation."""
    
    response_time: float = 0.0
    token_count: int = 0
    tokens_per_second: float = 0.0
    model_name: str = ""
    eval_count: int = 0
    eval_duration: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "response_time": self.response_time,
            "token_count": self.token_count,
            "tokens_per_second": self.tokens_per_second,
            "model_name": self.model_name,
            "eval_count": self.eval_count,
            "eval_duration": self.eval_duration
        }


@dataclass
class CodeResponse:
    """Represents a code generation response."""
    
    success: bool
    content: str
    code_blocks: List[CodeBlock] = field(default_factory=list)
    error_message: Optional[str] = None
    performance: Optional[PerformanceMetrics] = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def generated_code(self) -> str:
        """Get generated code content."""
        return self.content
    
    @property
    def confidence(self) -> float:
        """Get confidence score (0.0 to 1.0)."""
        # Simple confidence based on success and content length
        if not self.success:
            return 0.0
        if not self.content.strip():
            return 0.1
        # Basic heuristic: longer responses with code blocks = higher confidence
        base_confidence = 0.7 if self.code_blocks else 0.5
        length_bonus = min(len(self.content) / 1000, 0.3)  # Up to 0.3 bonus
        return min(base_confidence + length_bonus, 1.0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "success": self.success,
            "content": self.content,
            "code_blocks": [block.to_dict() for block in self.code_blocks],
            "error_message": self.error_message,
            "performance": self.performance.to_dict() if self.performance else None,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CodeResponse':
        """Create from dictionary representation."""
        code_blocks = []
        if data.get("code_blocks"):
            code_blocks = [CodeBlock.from_dict(block) for block in data["code_blocks"]]
        
        performance = None
        if data.get("performance"):
            perf_data = data["performance"]
            performance = PerformanceMetrics(**perf_data)
        
        created_at = datetime.now()
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])
        
        return cls(
            success=data["success"],
            content=data["content"],
            code_blocks=code_blocks,
            error_message=data.get("error_message"),
            performance=performance,
            created_at=created_at,
            metadata=data.get("metadata", {})
        )
    
    def add_code_block(self, block: CodeBlock) -> None:
        """Add a code block to the response."""
        self.code_blocks.append(block)
    
    def get_code_blocks_by_language(self, language: CodeLanguage) -> List[CodeBlock]:
        """Get code blocks filtered by language."""
        return [block for block in self.code_blocks if block.language == language]
    
    def has_errors(self) -> bool:
        """Check if response has errors."""
        return not self.success or self.error_message is not None
    
    def __str__(self) -> str:
        """String representation."""
        status = "SUCCESS" if self.success else "ERROR"
        block_count = len(self.code_blocks)
        return f"CodeResponse(status={status}, blocks={block_count})" 