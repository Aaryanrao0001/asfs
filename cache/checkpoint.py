"""Pipeline checkpoint management for resuming interrupted runs."""

import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def get_video_hash(video_path: str) -> str:
    """
    Generate a unique hash for a video file based on its path and size.
    
    This is used to identify the same video across runs without hashing
    the entire file content (which would be slow for large videos).
    
    Args:
        video_path: Path to video file
        
    Returns:
        MD5 hash string
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    # Get absolute path and file size
    abs_path = os.path.abspath(video_path)
    file_size = os.path.getsize(abs_path)
    
    # Create hash from path + size (fast, good enough for caching)
    hash_input = f"{abs_path}:{file_size}".encode('utf-8')
    return hashlib.md5(hash_input).hexdigest()


class PipelineCache:
    """
    Manages pipeline state caching to resume interrupted runs.
    
    Saves intermediate results after each pipeline stage:
    - Audio extraction
    - Transcription
    - Segmentation
    - AI scoring
    - Validation
    - Extraction
    - Metadata
    
    This allows resuming from the last completed stage if the pipeline
    is interrupted or if the same video is processed again.
    """
    
    def __init__(self, cache_dir: str = "output/cache"):
        """
        Initialize pipeline cache.
        
        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
    def _get_cache_path(self, video_hash: str) -> str:
        """Get cache file path for a video."""
        return os.path.join(self.cache_dir, f"{video_hash}.json")
    
    def load_state(self, video_path: str) -> Optional[Dict[str, Any]]:
        """
        Load cached pipeline state for a video.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Cached state dictionary or None if no cache exists
        """
        try:
            video_hash = get_video_hash(video_path)
            cache_path = self._get_cache_path(video_hash)
            
            if not os.path.exists(cache_path):
                logger.info("No cache found for this video")
                return None
            
            with open(cache_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            logger.info(f"[OK] Found cached state from {state.get('last_updated', 'unknown time')}")
            logger.info(f"[OK] Last completed stage: {state.get('last_stage', 'none')}")
            
            return state
            
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
            return None
    
    def save_state(self, video_path: str, state: Dict[str, Any], stage: str, config: dict = None):
        """
        Save pipeline state after completing a stage.
        
        Args:
            video_path: Path to video file
            state: Current pipeline state dictionary
            stage: Name of completed stage
            config: Configuration used for this stage (for cache invalidation)
        """
        try:
            video_hash = get_video_hash(video_path)
            cache_path = self._get_cache_path(video_hash)
            
            # Update metadata
            state['last_stage'] = stage
            state['last_updated'] = datetime.now().isoformat()
            state['video_path'] = os.path.abspath(video_path)
            
            # Store config for ai_scoring stage
            if stage == "ai_scoring" and config:
                state["ai_config"] = {
                    "endpoint": config.get("endpoint"),
                    "model_name": config.get("model_name"),
                    "min_score_threshold": config.get("min_score_threshold"),
                    "timestamp": datetime.now().isoformat()
                }
            
            # Store output file metadata if available
            if stage in state and 'transcript_path' in state[stage]:
                output_path = state[stage]['transcript_path']
                if os.path.exists(output_path):
                    if 'outputs' not in state:
                        state['outputs'] = {}
                    
                    state['outputs'][stage] = {
                        'path': str(output_path),
                        'size': os.path.getsize(output_path),
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # For transcript, use segment count from state if available
                    if stage == 'transcription' and 'segment_count' in state[stage]:
                        state['outputs'][stage]['segments'] = state[stage]['segment_count']
            
            # Store audio output metadata
            elif stage in state and 'audio_path' in state[stage]:
                output_path = state[stage]['audio_path']
                if os.path.exists(output_path):
                    if 'outputs' not in state:
                        state['outputs'] = {}
                    
                    state['outputs'][stage] = {
                        'path': str(output_path),
                        'size': os.path.getsize(output_path),
                        'timestamp': datetime.now().isoformat()
                    }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"[OK] Cached state after stage: {stage}")
            
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
    
    def clear_cache(self, video_path: str):
        """
        Clear cached state for a video.
        
        Args:
            video_path: Path to video file
        """
        try:
            video_hash = get_video_hash(video_path)
            cache_path = self._get_cache_path(video_hash)
            
            if os.path.exists(cache_path):
                os.remove(cache_path)
                logger.info("[OK] Cache cleared")
            
        except Exception as e:
            logger.warning(f"Failed to clear cache: {e}")
    
    def get_stage_result(self, state: Optional[Dict], stage: str, key: str = None) -> Any:
        """
        Get cached result for a specific stage.
        
        Args:
            state: Pipeline state dictionary
            stage: Stage name
            key: Optional specific key to retrieve
            
        Returns:
            Cached result or None if not found
        """
        if not state or stage not in state:
            return None
        
        stage_data = state[stage]
        
        if key:
            return stage_data.get(key)
        
        return stage_data
    
    def has_completed_stage(self, state: Optional[Dict], stage: str) -> bool:
        """
        Check if a stage has been completed in cached state.
        
        Args:
            state: Pipeline state dictionary
            stage: Stage name to check
            
        Returns:
            True if stage is completed in cache
        """
        if not state:
            return False
        
        return stage in state and state[stage].get('completed', False)
    
    def should_invalidate_ai_scoring(self, video_path: str, model_config: dict, state: Optional[Dict] = None) -> bool:
        """
        Check if AI scoring cache should be invalidated.
        
        Returns True if any of these changed:
        - Model config (endpoint, model name)
        - Score threshold
        
        Args:
            video_path: Path to input video
            model_config: Current model configuration
            state: Optional pre-loaded pipeline state (to avoid re-loading)
            
        Returns:
            True if cache should be invalidated
        """
        # Load state if not provided
        if state is None:
            state = self.load_state(video_path)
        
        if not state or "ai_scoring" not in state:
            return False  # No cache, no need to invalidate
        
        cached_config = state.get("ai_config", {})
        
        # Check if model endpoint changed
        if cached_config.get("endpoint") != model_config.get("endpoint"):
            logger.info("AI scoring cache invalidated: endpoint changed")
            return True
        
        # Check if model name changed
        if cached_config.get("model_name") != model_config.get("model_name"):
            logger.info("AI scoring cache invalidated: model changed")
            return True
        
        # Check if threshold changed
        if cached_config.get("min_score_threshold") != model_config.get("min_score_threshold"):
            logger.info("AI scoring cache invalidated: threshold changed")
            return True
        
        # Check if all cached scores are zero (indicates failed scoring)
        scored_segments = state.get("ai_scoring", {}).get("scored_segments", [])
        if scored_segments:
            all_zero = all(
                seg.get("overall_score", 0) == 0 and seg.get("final_score", 0) == 0
                for seg in scored_segments
            )
            if all_zero:
                logger.info("AI scoring cache invalidated: all cached scores are 0 (likely failed scoring)")
                return True
        
        return False
