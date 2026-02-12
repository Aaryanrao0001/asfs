"""AI-powered highlight scoring using GitHub Models."""

from .scorer import score_segments
from .enhanced_scorer import score_segments_enhanced

__all__ = ['score_segments', 'score_segments_enhanced']
