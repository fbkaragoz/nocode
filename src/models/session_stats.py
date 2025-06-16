"""
Session Statistics Model - Track session performance and usage metrics.
"""

import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SessionStats:
    """Session statistics tracking."""
    
    # Session identification
    session_id: str = field(default_factory=lambda: f"session_{int(time.time())}")
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    
    # Request tracking
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    
    # Performance metrics
    total_response_time: float = 0.0
    total_tokens_generated: int = 0  
    total_tokens_processed: int = 0
    
    # Code generation stats
    code_blocks_generated: int = 0
    files_saved: int = 0
    languages_used: List[str] = field(default_factory=list)
    
    # Model usage
    model_name: Optional[str] = None
    context_length_used: int = 0
    
    # User interaction
    user_prompts: List[str] = field(default_factory=list)
    
    def add_request(self, success: bool, response_time: float = 0.0, 
                   tokens_generated: int = 0, tokens_processed: int = 0):
        """Add a request to statistics."""
        self.total_requests += 1
        
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
            
        self.total_response_time += response_time
        self.total_tokens_generated += tokens_generated
        self.total_tokens_processed += tokens_processed
    
    def add_code_generation(self, blocks_count: int, language: str, files_saved: int = 0):
        """Add code generation statistics."""
        self.code_blocks_generated += blocks_count
        self.files_saved += files_saved
        
        if language not in self.languages_used:
            self.languages_used.append(language)
    
    def add_user_prompt(self, prompt: str):
        """Add user prompt to history."""
        self.user_prompts.append(prompt)
    
    @property
    def avg_response_time(self) -> float:
        """Calculate average response time."""
        if self.total_requests == 0:
            return 0.0
        return self.total_response_time / self.total_requests
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    @property
    def tokens_per_second(self) -> float:
        """Calculate tokens per second."""
        if self.total_response_time == 0:
            return 0.0
        return self.total_tokens_generated / self.total_response_time
    
    @property
    def session_duration(self) -> float:
        """Get session duration in seconds."""
        end = self.end_time or time.time()
        return end - self.start_time
    
    def finalize_session(self):
        """Finalize session by setting end time."""
        self.end_time = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'session_id': self.session_id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration_seconds': self.session_duration,
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'success_rate': self.success_rate,
            'avg_response_time': self.avg_response_time,
            'total_tokens_generated': self.total_tokens_generated,
            'total_tokens_processed': self.total_tokens_processed,
            'tokens_per_second': self.tokens_per_second,
            'code_blocks_generated': self.code_blocks_generated,
            'files_saved': self.files_saved,
            'languages_used': self.languages_used,
            'model_name': self.model_name,
            'context_length_used': self.context_length_used,
            'user_prompts_count': len(self.user_prompts)
        } 