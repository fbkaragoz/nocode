"""
Improvement cycle data model for recursive code enhancement.
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime

from models.code_response import CodeResponse


@dataclass
class ImprovementCycle:
    """Represents a single improvement cycle in recursive enhancement."""
    
    cycle_number: int
    original_code: str
    improved_code: str
    analysis: str
    response: CodeResponse
    improvements_identified: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "cycle_number": self.cycle_number,
            "original_code": self.original_code,
            "improved_code": self.improved_code,
            "analysis": self.analysis,
            "response": self.response.to_dict(),
            "improvements_identified": self.improvements_identified,
            "metrics": self.metrics,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ImprovementCycle':
        """Create from dictionary representation."""
        created_at = datetime.now()
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])
        
        response = CodeResponse.from_dict(data["response"])
        
        return cls(
            cycle_number=data["cycle_number"],
            original_code=data["original_code"],
            improved_code=data["improved_code"],
            analysis=data["analysis"],
            response=response,
            improvements_identified=data.get("improvements_identified", []),
            metrics=data.get("metrics", {}),
            created_at=created_at
        )
    
    def calculate_improvement_score(self) -> float:
        """Calculate improvement score based on metrics."""
        if not self.metrics:
            return 0.0
        
        # Simple scoring based on common improvement metrics
        score = 0.0
        weights = {
            "complexity_reduction": 0.3,
            "performance_gain": 0.3,
            "readability_improvement": 0.2,
            "security_enhancement": 0.2
        }
        
        for metric, weight in weights.items():
            if metric in self.metrics:
                score += self.metrics[metric] * weight
        
        return min(score, 1.0)  # Cap at 1.0
    
    def __str__(self) -> str:
        """String representation."""
        return f"ImprovementCycle(cycle={self.cycle_number}, score={self.calculate_improvement_score():.2f})" 