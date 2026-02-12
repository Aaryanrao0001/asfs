"""
Enhanced scoring integration for the viral detection pipeline.

Wraps the existing score_segments with the new enhanced pipeline.
"""

import logging
from typing import Dict, List

from virality import EnhancedViralPipeline
from .scorer import score_segments as original_score_segments

logger = logging.getLogger(__name__)


def score_segments_enhanced(
    candidates: List[Dict],
    model_config: Dict,
    transcript_segments: List[Dict] = None,
    use_enhanced: bool = True,
    max_segments: int = 50
) -> List[Dict]:
    """
    Enhanced scoring wrapper that uses viral detection pipeline.
    
    Args:
        candidates: List of candidate segment dictionaries
        model_config: Model configuration
        transcript_segments: Full transcript segments (required for enhanced mode)
        use_enhanced: Whether to use enhanced pipeline (default: True)
        max_segments: Maximum segments to score
        
    Returns:
        List of scored segments
    """
    # Check if enhanced mode is explicitly disabled
    if not use_enhanced or model_config.get('disable_enhanced', False):
        logger.info("Using original scoring pipeline (enhanced disabled)")
        return original_score_segments(candidates, model_config, max_segments)
    
    # Check if transcript segments provided (required for enhanced)
    if not transcript_segments:
        logger.warning(
            "Enhanced pipeline requires transcript_segments - "
            "falling back to original scoring"
        )
        return original_score_segments(candidates, model_config, max_segments)
    
    logger.info("Using ENHANCED viral detection pipeline")
    
    # Initialize enhanced pipeline
    enhanced_config = {
        'psychological_threshold': model_config.get('psychological_threshold', 65.0),
        'similarity_threshold': model_config.get('similarity_threshold', 0.85),
        'min_hook_score': model_config.get('min_hook_score', 6.0),
        'use_llm_scoring': model_config.get('use_llm_scoring', True)
    }
    
    pipeline = EnhancedViralPipeline(
        transcript_segments=transcript_segments,
        config=enhanced_config
    )
    
    # Create LLM scorer wrapper if enabled
    llm_scorer = None
    if enhanced_config['use_llm_scoring']:
        def llm_scorer_wrapper(clips: List[Dict]) -> List[Dict]:
            """Wrapper to call original LLM scorer."""
            return original_score_segments(clips, model_config, max_segments)
        llm_scorer = llm_scorer_wrapper
    
    # Run enhanced pipeline
    top_n = model_config.get('top_clips', 10)
    enhanced_results = pipeline.run_pipeline(
        candidates,
        llm_scorer_func=llm_scorer,
        top_n=top_n
    )
    
    # If we got fewer results than expected, pad with original scoring
    if len(enhanced_results) < max_segments and len(candidates) > len(enhanced_results):
        logger.info(
            f"Enhanced pipeline returned {len(enhanced_results)} clips, "
            f"padding with original scoring"
        )
        
        # Get candidates that weren't selected
        selected_starts = {c.get('start') for c in enhanced_results}
        remaining = [c for c in candidates if c.get('start') not in selected_starts]
        
        if remaining:
            # Score remaining with original pipeline
            additional = original_score_segments(
                remaining,
                model_config,
                max_segments - len(enhanced_results)
            )
            enhanced_results.extend(additional)
    
    logger.info(f"Enhanced scoring complete: {len(enhanced_results)} segments")
    
    return enhanced_results
