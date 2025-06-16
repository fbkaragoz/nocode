"""
Progress Tracker - Intelligent progress monitoring and estimation.
Provides smart progress tracking for streaming operations.
"""

import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


logger = logging.getLogger(__name__)


class ProgressStage(Enum):
    """Stages of progress tracking."""
    INITIALIZING = "initializing"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    OPTIMIZING = "optimizing"
    FINALIZING = "finalizing"
    COMPLETED = "completed"


@dataclass
class ProgressSnapshot:
    """Snapshot of progress at a specific time."""
    stage: ProgressStage
    progress_percent: float
    chunks_processed: int
    bytes_processed: int
    elapsed_time: float
    estimated_remaining: float
    status_message: str
    timestamp: float
    
    def __post_init__(self):
        if self.timestamp == 0:
            self.timestamp = time.time()


class ProgressTracker:
    """
    Progress Tracker - Intelligent progress monitoring.
    
    Responsibilities:
    - Track progress across different stages
    - Estimate completion times
    - Provide smart progress indicators
    - Handle progress smoothing
    """
    
    def __init__(self):
        """Initialize progress tracker."""
        self.active_sessions = {}
        self.progress_history = {}
        
        # Stage weights for overall progress calculation
        self.stage_weights = {
            ProgressStage.INITIALIZING: 5,
            ProgressStage.ANALYZING: 15,
            ProgressStage.GENERATING: 60,
            ProgressStage.OPTIMIZING: 15,
            ProgressStage.FINALIZING: 5
        }
        
        # Performance baselines for estimation
        self.performance_baselines = {
            'chunks_per_second': 10.0,
            'bytes_per_second': 1000.0,
            'average_response_time': 5.0
        }
    
    def start_tracking(self, session_id: str):
        """Start tracking progress for a session."""
        try:
            self.active_sessions[session_id] = {
                'start_time': time.time(),
                'current_stage': ProgressStage.INITIALIZING,
                'stage_start_time': time.time(),
                'progress_percent': 0.0,
                'chunks_processed': 0,
                'bytes_processed': 0,
                'stage_progress': {},
                'snapshots': [],
                'estimated_total_time': 0.0,
                'status_message': 'Starting...'
            }
            
            self.progress_history[session_id] = []
            
            # Initial snapshot
            self._take_snapshot(session_id)
            
            logger.info(f"Progress tracking started for: {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to start progress tracking: {e}")
    
    def update_progress(self, session_id: str, chunks_processed: int, chunk_data: str = ""):
        """Update progress based on processed chunks."""
        if session_id not in self.active_sessions:
            return
        
        try:
            session = self.active_sessions[session_id]
            
            # Update basic metrics
            session['chunks_processed'] = chunks_processed
            session['bytes_processed'] += len(chunk_data.encode('utf-8'))
            
            # Estimate progress based on chunk analysis
            progress = self._estimate_progress_from_chunks(session, chunk_data)
            session['progress_percent'] = min(progress, 95.0)  # Cap at 95% until completion
            
            # Update stage if needed
            self._update_stage_if_needed(session)
            
            # Take snapshot
            self._take_snapshot(session_id)
            
        except Exception as e:
            logger.error(f"Failed to update progress: {e}")
    
    def update_progress_percent(self, session_id: str, progress_percent: float, status_message: str = ""):
        """Update progress with explicit percentage."""
        if session_id not in self.active_sessions:
            return
        
        try:
            session = self.active_sessions[session_id]
            
            # Smooth progress updates to avoid jumping
            current_progress = session['progress_percent']
            if progress_percent > current_progress:
                # Allow progress increase
                session['progress_percent'] = min(progress_percent, 95.0)
            else:
                # Smooth backward progress (might be normal in some cases)
                session['progress_percent'] = max(progress_percent, current_progress - 5.0)
            
            if status_message:
                session['status_message'] = status_message
            
            # Update stage based on progress
            self._update_stage_from_progress(session, progress_percent)
            
            # Take snapshot
            self._take_snapshot(session_id)
            
        except Exception as e:
            logger.error(f"Failed to update progress percent: {e}")
    
    def advance_stage(self, session_id: str, new_stage: ProgressStage, message: str = ""):
        """Advance to a new progress stage."""
        if session_id not in self.active_sessions:
            return
        
        try:
            session = self.active_sessions[session_id]
            old_stage = session['current_stage']
            
            # Update stage
            session['current_stage'] = new_stage
            session['stage_start_time'] = time.time()
            
            if message:
                session['status_message'] = message
            
            # Calculate overall progress based on stage
            overall_progress = self._calculate_overall_progress(session)
            session['progress_percent'] = overall_progress
            
            # Take snapshot
            self._take_snapshot(session_id)
            
            logger.info(f"Stage advanced: {old_stage.value} → {new_stage.value} ({session_id})")
            
        except Exception as e:
            logger.error(f"Failed to advance stage: {e}")
    
    def complete_tracking(self, session_id: str, success: bool = True):
        """Complete progress tracking for a session."""
        if session_id not in self.active_sessions:
            return
        
        try:
            session = self.active_sessions[session_id]
            
            # Final update
            session['current_stage'] = ProgressStage.COMPLETED
            session['progress_percent'] = 100.0 if success else session['progress_percent']
            session['status_message'] = 'Completed successfully!' if success else 'Completed with errors'
            session['end_time'] = time.time()
            session['total_duration'] = session['end_time'] - session['start_time']
            
            # Final snapshot
            self._take_snapshot(session_id)
            
            # Move to history
            if session_id in self.progress_history:
                self.progress_history[session_id] = session
            
            # Remove from active sessions
            del self.active_sessions[session_id]
            
            logger.info(f"Progress tracking completed for: {session_id} (Success: {success})")
            
        except Exception as e:
            logger.error(f"Failed to complete progress tracking: {e}")
    
    def get_progress_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current progress information for a session."""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            
            # Calculate additional info
            elapsed_time = time.time() - session['start_time']
            estimated_remaining = self._estimate_remaining_time(session)
            
            return {
                'session_id': session_id,
                'stage': session['current_stage'].value,
                'progress_percent': session['progress_percent'],
                'status_message': session['status_message'],
                'chunks_processed': session['chunks_processed'],
                'bytes_processed': session['bytes_processed'],
                'elapsed_time': elapsed_time,
                'estimated_remaining': estimated_remaining,
                'estimated_total': elapsed_time + estimated_remaining
            }
        
        # Check history
        if session_id in self.progress_history:
            historical_session = self.progress_history[session_id]
            return {
                'session_id': session_id,
                'stage': 'completed',
                'progress_percent': 100.0,
                'status_message': 'Completed',
                'total_duration': historical_session.get('total_duration', 0),
                'chunks_processed': historical_session.get('chunks_processed', 0),
                'bytes_processed': historical_session.get('bytes_processed', 0)
            }
        
        return None
    
    def _estimate_progress_from_chunks(self, session: Dict[str, Any], chunk_data: str) -> float:
        """Estimate progress based on chunk analysis."""
        chunks_processed = session['chunks_processed']
        
        # Basic estimation based on chunk count
        if chunks_processed == 0:
            return 0.0
        
        # Analyze chunk content for better estimation
        if chunk_data:
            # Look for completion indicators
            completion_indicators = ['```', 'def ', 'class ', 'import ', 'return', '}', '</']
            indicator_count = sum(1 for indicator in completion_indicators if indicator in chunk_data)
            
            # Estimate based on content richness
            content_richness = len(chunk_data.strip()) / max(len(chunk_data), 1)
            
            # Dynamic estimation
            base_progress = min(chunks_processed * 2, 80)  # 2% per chunk, capped at 80%
            content_bonus = indicator_count * 3  # 3% per completion indicator
            richness_bonus = content_richness * 10  # Up to 10% for content richness
            
            return min(base_progress + content_bonus + richness_bonus, 95)
        
        # Fallback to simple chunk-based estimation
        return min(chunks_processed * 2, 95)
    
    def _update_stage_if_needed(self, session: Dict[str, Any]):
        """Update stage based on progress and content analysis."""
        current_progress = session['progress_percent']
        current_stage = session['current_stage']
        
        # Stage transitions based on progress
        if current_progress < 10 and current_stage == ProgressStage.INITIALIZING:
            pass  # Stay in initializing
        elif 10 <= current_progress < 25 and current_stage == ProgressStage.INITIALIZING:
            session['current_stage'] = ProgressStage.ANALYZING
            session['status_message'] = 'Analyzing requirements...'
        elif 25 <= current_progress < 80 and current_stage in [ProgressStage.INITIALIZING, ProgressStage.ANALYZING]:
            session['current_stage'] = ProgressStage.GENERATING
            session['status_message'] = 'Generating code...'
        elif 80 <= current_progress < 95 and current_stage != ProgressStage.FINALIZING:
            session['current_stage'] = ProgressStage.FINALIZING
            session['status_message'] = 'Finalizing output...'
    
    def _update_stage_from_progress(self, session: Dict[str, Any], progress_percent: float):
        """Update stage based on explicit progress percentage."""
        if progress_percent < 5:
            stage = ProgressStage.INITIALIZING
            message = 'Initializing...'
        elif progress_percent < 20:
            stage = ProgressStage.ANALYZING
            message = 'Analyzing request...'
        elif progress_percent < 85:
            stage = ProgressStage.GENERATING
            message = 'Generating code...'
        elif progress_percent < 98:
            stage = ProgressStage.FINALIZING
            message = 'Finalizing...'
        else:
            stage = ProgressStage.COMPLETED
            message = 'Completed!'
        
        if session['current_stage'] != stage:
            session['current_stage'] = stage
            session['status_message'] = message
            session['stage_start_time'] = time.time()
    
    def _calculate_overall_progress(self, session: Dict[str, Any]) -> float:
        """Calculate overall progress based on stage completion."""
        current_stage = session['current_stage']
        
        # Base progress for completed stages
        completed_progress = 0.0
        for stage, weight in self.stage_weights.items():
            if stage.value < current_stage.value:
                completed_progress += weight
        
        # Add partial progress for current stage (estimate 50% completion)
        if current_stage in self.stage_weights:
            completed_progress += self.stage_weights[current_stage] * 0.5
        
        return min(completed_progress, 95.0)
    
    def _estimate_remaining_time(self, session: Dict[str, Any]) -> float:
        """Estimate remaining time based on current progress."""
        elapsed_time = time.time() - session['start_time']
        progress_percent = session['progress_percent']
        
        if progress_percent <= 0:
            return self.performance_baselines['average_response_time']
        
        # Linear estimation based on current progress
        if progress_percent < 100:
            remaining_percent = 100 - progress_percent
            time_per_percent = elapsed_time / progress_percent
            estimated_remaining = time_per_percent * remaining_percent
            
            # Apply stage-based adjustments
            current_stage = session['current_stage']
            if current_stage == ProgressStage.GENERATING:
                # Generation typically takes longer
                estimated_remaining *= 1.2
            elif current_stage == ProgressStage.FINALIZING:
                # Finalizing is usually quick
                estimated_remaining *= 0.5
            
            return max(estimated_remaining, 1.0)  # At least 1 second
        
        return 0.0
    
    def _take_snapshot(self, session_id: str):
        """Take a snapshot of current progress."""
        if session_id not in self.active_sessions:
            return
        
        try:
            session = self.active_sessions[session_id]
            
            snapshot = ProgressSnapshot(
                stage=session['current_stage'],
                progress_percent=session['progress_percent'],
                chunks_processed=session['chunks_processed'],
                bytes_processed=session['bytes_processed'],
                elapsed_time=time.time() - session['start_time'],
                estimated_remaining=self._estimate_remaining_time(session),
                status_message=session['status_message'],
                timestamp=time.time()
            )
            
            session['snapshots'].append(snapshot)
            
            # Keep only recent snapshots (last 50)
            session['snapshots'] = session['snapshots'][-50:]
            
        except Exception as e:
            logger.error(f"Failed to take progress snapshot: {e}")
    
    def get_session_history(self, session_id: str) -> List[ProgressSnapshot]:
        """Get progress history for a session."""
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]['snapshots'].copy()
        elif session_id in self.progress_history:
            return self.progress_history[session_id].get('snapshots', [])
        return []