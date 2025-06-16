"""
Stream Manager - Real-time code streaming and progress management.
Handles streaming events and real-time updates.
"""

import logging
import threading
import time
import queue
from typing import Dict, Any, Callable, Optional
from dataclasses import dataclass
from enum import Enum

from .progress_tracker import ProgressTracker


logger = logging.getLogger(__name__)


class StreamEventType(Enum):
    """Types of streaming events."""
    STARTED = "started"
    PROGRESS = "progress"
    CHUNK = "chunk"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class StreamEvent:
    """Streaming event data."""
    event_type: StreamEventType
    data: Any = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class StreamManager:
    """
    Stream Manager - Clean streaming architecture.
    
    Responsibilities:
    - Manage real-time streaming sessions
    - Handle streaming events
    - Coordinate with progress tracker
    - Provide streaming callbacks
    """
    
    def __init__(self):
        """Initialize stream manager."""
        self.is_streaming = False
        self.current_session_id = None
        self.progress_tracker = ProgressTracker()
        
        # Event handling
        self.event_queue = queue.Queue()
        self.event_handlers = {}
        self.stream_thread = None
        
        # Session data
        self.session_data = {}
        self.streaming_callbacks = []
        
        # Performance tracking
        self.streaming_stats = {
            'total_sessions': 0,
            'total_chunks': 0,
            'total_bytes': 0,
            'average_speed': 0.0
        }
    
    def start_streaming_session(self, session_id: Optional[str] = None) -> str:
        """Start a new streaming session."""
        try:
            # Generate session ID if not provided
            if session_id is None:
                session_id = f"stream_{int(time.time() * 1000)}"
            
            self.current_session_id = session_id
            self.is_streaming = True
            
            # Initialize session data
            self.session_data[session_id] = {
                'start_time': time.time(),
                'chunks_received': 0,
                'bytes_received': 0,
                'progress': 0.0,
                'status': 'active'
            }
            
            # Start progress tracking
            self.progress_tracker.start_tracking(session_id)
            
            # Emit started event
            self._emit_event(StreamEvent(StreamEventType.STARTED, session_id))
            
            # Update stats
            self.streaming_stats['total_sessions'] += 1
            
            logger.info(f"Streaming session started: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to start streaming session: {e}")
            raise
    
    def add_chunk(self, chunk_data: str, chunk_type: str = "code") -> bool:
        """Add a chunk of data to the current streaming session."""
        if not self.is_streaming or not self.current_session_id:
            return False
        
        try:
            session_id = self.current_session_id
            session = self.session_data[session_id]
            
            # Update session stats
            session['chunks_received'] += 1
            session['bytes_received'] += len(chunk_data.encode('utf-8'))
            
            # Create chunk event
            chunk_event_data = {
                'content': chunk_data,
                'type': chunk_type,
                'chunk_number': session['chunks_received'],
                'session_id': session_id
            }
            
            # Emit chunk event
            self._emit_event(StreamEvent(StreamEventType.CHUNK, chunk_event_data))
            
            # Update progress
            self.progress_tracker.update_progress(
                session_id, 
                session['chunks_received'],
                chunk_data
            )
            
            # Update global stats
            self.streaming_stats['total_chunks'] += 1
            self.streaming_stats['total_bytes'] += len(chunk_data.encode('utf-8'))
            
            # Execute callbacks
            self._execute_streaming_callbacks(chunk_event_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to add chunk: {e}")
            return False
    
    def update_progress(self, progress_percent: float, status_message: str = ""):
        """Update progress of current streaming session."""
        if not self.is_streaming or not self.current_session_id:
            return
        
        try:
            session_id = self.current_session_id
            session = self.session_data[session_id]
            session['progress'] = progress_percent
            
            # Create progress event
            progress_data = {
                'progress': progress_percent,
                'status': status_message,
                'session_id': session_id,
                'elapsed_time': time.time() - session['start_time']
            }
            
            # Emit progress event
            self._emit_event(StreamEvent(StreamEventType.PROGRESS, progress_data))
            
            # Update progress tracker
            self.progress_tracker.update_progress_percent(session_id, progress_percent, status_message)
            
        except Exception as e:
            logger.error(f"Failed to update progress: {e}")
    
    def end_streaming_session(self, success: bool = True, final_data: Any = None):
        """End the current streaming session."""
        if not self.is_streaming or not self.current_session_id:
            return
        
        try:
            session_id = self.current_session_id
            session = self.session_data[session_id]
            
            # Calculate final stats
            end_time = time.time()
            duration = end_time - session['start_time']
            
            session['end_time'] = end_time
            session['duration'] = duration
            session['status'] = 'completed' if success else 'failed'
            
            # Calculate speed
            if duration > 0:
                bytes_per_second = session['bytes_received'] / duration
                self.streaming_stats['average_speed'] = (
                    self.streaming_stats['average_speed'] + bytes_per_second
                ) / 2
            
            # Complete progress tracking
            self.progress_tracker.complete_tracking(session_id, success)
            
            # Create completion event
            completion_data = {
                'session_id': session_id,
                'success': success,
                'final_data': final_data,
                'stats': {
                    'duration': duration,
                    'chunks': session['chunks_received'],
                    'bytes': session['bytes_received'],
                    'speed': session['bytes_received'] / duration if duration > 0 else 0
                }
            }
            
            # Emit completion event
            self._emit_event(StreamEvent(StreamEventType.COMPLETED, completion_data))
            
            # Reset state
            self.is_streaming = False
            self.current_session_id = None
            
            logger.info(f"Streaming session ended: {session_id} (Success: {success})")
            
        except Exception as e:
            logger.error(f"Failed to end streaming session: {e}")
    
    def add_streaming_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add a callback for streaming events."""
        self.streaming_callbacks.append(callback)
    
    def remove_streaming_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Remove a streaming callback."""
        if callback in self.streaming_callbacks:
            self.streaming_callbacks.remove(callback)
    
    def _execute_streaming_callbacks(self, chunk_data: Dict[str, Any]):
        """Execute all streaming callbacks."""
        for callback in self.streaming_callbacks:
            try:
                callback(chunk_data)
            except Exception as e:
                logger.error(f"Streaming callback error: {e}")
    
    def _emit_event(self, event: StreamEvent):
        """Emit a streaming event."""
        try:
            self.event_queue.put_nowait(event)
            
            # Handle event immediately if handlers exist
            event_type = event.event_type
            if event_type in self.event_handlers:
                for handler in self.event_handlers[event_type]:
                    try:
                        handler(event)
                    except Exception as e:
                        logger.error(f"Event handler error: {e}")
                        
        except Exception as e:
            logger.error(f"Failed to emit event: {e}")
    
    def add_event_handler(self, event_type: StreamEventType, handler: Callable[[StreamEvent], None]):
        """Add an event handler for specific event type."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    def get_session_stats(self, session_id: str = None) -> Dict[str, Any]:
        """Get statistics for a specific session."""
        if session_id is None:
            session_id = self.current_session_id
        
        if session_id and session_id in self.session_data:
            session = self.session_data[session_id].copy()
            
            # Add calculated fields
            if 'start_time' in session:
                current_time = session.get('end_time', time.time())
                session['duration'] = current_time - session['start_time']
                
                if session['duration'] > 0:
                    session['chunks_per_second'] = session['chunks_received'] / session['duration']
                    session['bytes_per_second'] = session['bytes_received'] / session['duration']
            
            return session
        
        return {}
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Get global streaming statistics."""
        return self.streaming_stats.copy()
    
    def simulate_streaming(self, content: str, chunk_size: int = 50, delay: float = 0.1):
        """Simulate streaming for testing purposes."""
        if not self.is_streaming:
            return
        
        def stream_content():
            try:
                chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
                total_chunks = len(chunks)
                
                for i, chunk in enumerate(chunks):
                    if not self.is_streaming:
                        break
                    
                    # Add chunk
                    self.add_chunk(chunk, "simulated")
                    
                    # Update progress
                    progress = ((i + 1) / total_chunks) * 100
                    self.update_progress(progress, f"Streaming chunk {i+1}/{total_chunks}")
                    
                    # Delay
                    time.sleep(delay)
                
                # Complete
                if self.is_streaming:
                    self.end_streaming_session(success=True, final_data=content)
                    
            except Exception as e:
                logger.error(f"Streaming simulation error: {e}")
                if self.is_streaming:
                    self.end_streaming_session(success=False)
        
        # Start streaming in background thread
        self.stream_thread = threading.Thread(target=stream_content, daemon=True)
        self.stream_thread.start()
    
    def cleanup(self):
        """Cleanup streaming resources."""
        try:
            # End current session if active
            if self.is_streaming:
                self.end_streaming_session(success=False)
            
            # Clear queues and handlers
            while not self.event_queue.empty():
                try:
                    self.event_queue.get_nowait()
                except queue.Empty:
                    break
            
            self.event_handlers.clear()
            self.streaming_callbacks.clear()
            
            # Wait for streaming thread
            if self.stream_thread and self.stream_thread.is_alive():
                self.stream_thread.join(timeout=2)
            
            logger.info("🧹 Stream manager cleaned up")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}") 