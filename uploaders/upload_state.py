"""
Upload state management and retry logic for robust uploads.

This module provides a state machine approach to tracking upload progress
and implements retry logic with exponential backoff for resilient uploads.
"""

import logging
import time
from enum import Enum
from typing import Optional, Callable, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class UploadState(Enum):
    """Upload state machine states."""
    VALIDATING = "VALIDATING"
    UPLOADING_FILE = "UPLOADING_FILE"
    PROCESSING = "PROCESSING"
    FILLING_CAPTION = "FILLING_CAPTION"
    POSTING = "POSTING"
    CONFIRMING = "CONFIRMING"
    DONE = "DONE"
    FAILED = "FAILED"


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    delays: list = None  # Delays in seconds between retries
    
    def __post_init__(self):
        if self.delays is None:
            # Exponential backoff: 5s, 15s, 45s
            self.delays = [5, 15, 45]
        # Ensure we have enough delays for max_attempts
        while len(self.delays) < self.max_attempts:
            self.delays.append(self.delays[-1] * 3)


class UploadStateTracker:
    """
    Tracks upload state and logs state transitions.
    
    Usage:
        tracker = UploadStateTracker(video_path="video.mp4")
        tracker.transition(UploadState.UPLOADING_FILE)
        tracker.transition(UploadState.PROCESSING)
        ...
    """
    
    def __init__(self, video_path: str):
        self.video_path = video_path
        self.current_state = None
        self.start_time = time.time()
        self.state_times = {}
        
    def transition(self, new_state: UploadState) -> None:
        """
        Transition to a new state and log it.
        
        Args:
            new_state: The new state to transition to
        """
        elapsed = time.time() - self.start_time
        
        if self.current_state:
            logger.info(f"[STATE] {self.current_state.value} → {new_state.value} (elapsed: {elapsed:.1f}s)")
        else:
            logger.info(f"[STATE] → {new_state.value}")
            
        self.current_state = new_state
        self.state_times[new_state] = elapsed
        
    def get_elapsed(self) -> float:
        """Get total elapsed time since start."""
        return time.time() - self.start_time
        
    def get_state_duration(self, state: UploadState) -> Optional[float]:
        """Get when a state was reached (seconds since start)."""
        return self.state_times.get(state)


def retry_with_backoff(
    func: Callable,
    retry_config: RetryConfig = None,
    error_message: str = "Operation failed"
) -> Any:
    """
    Execute a function with retry and exponential backoff.
    
    Args:
        func: Function to execute (should raise exception on failure)
        retry_config: RetryConfig object (uses default if None)
        error_message: Error message prefix for logging
        
    Returns:
        Result of func() if successful
        
    Raises:
        Last exception if all retries exhausted
    """
    if retry_config is None:
        retry_config = RetryConfig()
        
    last_exception = None
    
    for attempt in range(1, retry_config.max_attempts + 1):
        try:
            logger.info(f"[RETRY] Attempt {attempt}/{retry_config.max_attempts}")
            result = func()
            logger.info(f"[OK] Operation succeeded on attempt {attempt}")
            return result
            
        except Exception as e:
            last_exception = e
            logger.warning(f"[FAIL] Attempt {attempt} failed: {str(e)}")
            
            if attempt < retry_config.max_attempts:
                delay = retry_config.delays[attempt - 1]
                logger.info(f"[RETRY] Retrying in {delay}s...")
                time.sleep(delay)
            else:
                logger.error(f"[FAIL] {error_message} - all {retry_config.max_attempts} attempts exhausted")
                
    # All retries exhausted
    raise last_exception


def safe_execute(
    func: Callable,
    error_message: str = "Operation failed",
    return_on_error: Any = None
) -> Any:
    """
    Execute a function and catch exceptions, returning a default value on error.
    
    This is useful for validation/check operations that should not block the main flow.
    
    Args:
        func: Function to execute
        error_message: Error message prefix for logging
        return_on_error: Value to return if function raises exception
        
    Returns:
        Result of func() if successful, return_on_error otherwise
    """
    try:
        return func()
    except Exception as e:
        logger.warning(f"[NON-FATAL] {error_message}: {str(e)}")
        logger.warning("[INFO] Continuing anyway - this check is advisory only")
        return return_on_error
