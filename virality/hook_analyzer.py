"""
Hook window analyzer for the first 7 seconds of clips.

Enforces hook quality requirements:
- No filler words
- Strong opening (question, contradiction, specificity)
- Emotional trigger
- Curiosity gap
"""

import logging
import re
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


# Death signals (auto-fail patterns)
DEATH_SIGNALS = [
    r'\b(hey guys|hey everyone|whats up|welcome back)\b',
    r'\b(so today|today i want|im going to talk about)\b',
    r'\b(lets get started|first thing|first off)\b',
    r'\b(before we|make sure to)\b'
]

# Strong opening patterns
STRONG_OPENINGS = [
    r'^(nobody|never|everyone|always|stop|wait|listen)\b',
    r'\b(shocked|insane|crazy|unbelievable)\b',
    r'\b(secret|truth|lie|wrong|mistake)\b',
    r'\?$',  # Question
    r'\b(this is why|heres why|the reason)\b'
]

# Filler indicators
FILLER_PATTERNS = [
    r'\b(um|uh|like|you know|basically|literally)\b',
    r'\b(kind of|sort of|i mean|actually)\b',
    r'\b(well|so|and|but)\s*$'  # Trailing connectors
]


class HookAnalyzer:
    """
    Analyzes the first 7 seconds (hook window) of a clip.
    
    Enforces strict hook quality to ensure clips start strong.
    """
    
    def __init__(self):
        """Initialize hook analyzer."""
        self.death_regex = [re.compile(p, re.IGNORECASE) for p in DEATH_SIGNALS]
        self.strong_regex = [re.compile(p, re.IGNORECASE) for p in STRONG_OPENINGS]
        self.filler_regex = [re.compile(p, re.IGNORECASE) for p in FILLER_PATTERNS]
        
        logger.info("Hook analyzer initialized")
    
    def extract_hook_window(
        self, 
        transcript_segments: List[Dict],
        clip_start: float,
        hook_duration: float = 7.0
    ) -> Tuple[str, List[Dict]]:
        """
        Extract text from the first N seconds of a clip.
        
        Args:
            transcript_segments: List of transcript segments with start/end times
            clip_start: Start time of the clip
            hook_duration: Duration of hook window in seconds
            
        Returns:
            Tuple of (hook_text, hook_segments)
        """
        hook_end = clip_start + hook_duration
        hook_segments = []
        hook_text = []
        
        for segment in transcript_segments:
            seg_start = segment.get('start', 0)
            seg_end = segment.get('end', 0)
            
            # Check if segment overlaps with hook window
            if seg_start < hook_end and seg_end > clip_start:
                hook_segments.append(segment)
                hook_text.append(segment.get('text', ''))
        
        return ' '.join(hook_text), hook_segments
    
    def analyze_hook(self, hook_text: str) -> Dict:
        """
        Analyze hook quality.
        
        Args:
            hook_text: Text from the first 7 seconds
            
        Returns:
            Dictionary with hook analysis and score
        """
        if not hook_text or not hook_text.strip():
            return {
                'hook_score': 0.0,
                'has_death_signal': False,
                'has_strong_opening': False,
                'filler_count': 0,
                'passes_threshold': False,
                'issues': ['Empty hook'],
                'strengths': []
            }
        
        issues = []
        strengths = []
        hook_score = 5.0  # Start neutral
        
        # Check for death signals (auto-fail)
        has_death_signal = any(pattern.search(hook_text) for pattern in self.death_regex)
        if has_death_signal:
            hook_score = min(hook_score, 3.0)
            issues.append('Contains death signal (greeting/slow start)')
        
        # Check for strong openings
        has_strong_opening = any(pattern.search(hook_text) for pattern in self.strong_regex)
        if has_strong_opening:
            hook_score += 2.0
            strengths.append('Strong opening pattern detected')
        else:
            hook_score -= 1.0
            issues.append('No strong opening detected')
        
        # Check for filler words
        filler_matches = sum(1 for pattern in self.filler_regex if pattern.search(hook_text))
        if filler_matches > 0:
            hook_score -= (filler_matches * 0.5)
            issues.append(f'Contains {filler_matches} filler patterns')
        else:
            hook_score += 1.0
            strengths.append('No filler words')
        
        # Check for questions (curiosity trigger)
        if '?' in hook_text:
            hook_score += 1.0
            strengths.append('Contains question (curiosity trigger)')
        
        # Check for numbers/specificity
        if re.search(r'\b\d+\b', hook_text):
            hook_score += 0.5
            strengths.append('Contains specific numbers')
        
        # Check length (too short = incomplete)
        word_count = len(hook_text.split())
        if word_count < 5:
            hook_score -= 1.0
            issues.append('Hook too short (< 5 words)')
        elif word_count > 25:
            hook_score -= 0.5
            issues.append('Hook too long (> 25 words)')
        
        # Cap at 0-10
        hook_score = max(0.0, min(hook_score, 10.0))
        
        # Pass threshold: 6.0 or higher
        passes_threshold = hook_score >= 6.0
        
        return {
            'hook_score': hook_score,
            'has_death_signal': has_death_signal,
            'has_strong_opening': has_strong_opening,
            'filler_count': filler_matches,
            'passes_threshold': passes_threshold,
            'issues': issues,
            'strengths': strengths,
            'hook_text': hook_text,
            'word_count': word_count
        }
    
    def score_clip_hook(
        self,
        transcript_segments: List[Dict],
        clip_start: float,
        hook_duration: float = 7.0
    ) -> Dict:
        """
        Complete hook scoring for a clip.
        
        Args:
            transcript_segments: List of transcript segments
            clip_start: Start time of clip
            hook_duration: Hook window duration in seconds
            
        Returns:
            Hook analysis dictionary
        """
        hook_text, hook_segments = self.extract_hook_window(
            transcript_segments, clip_start, hook_duration
        )
        
        analysis = self.analyze_hook(hook_text)
        analysis['hook_segments'] = hook_segments
        
        return analysis
    
    def filter_by_hook_quality(
        self,
        candidates: List[Dict],
        transcript_segments: List[Dict],
        min_hook_score: float = 6.0
    ) -> List[Dict]:
        """
        Filter clip candidates by hook quality.
        
        Args:
            candidates: List of candidate clips with start times
            transcript_segments: Full transcript segments
            min_hook_score: Minimum hook score to pass
            
        Returns:
            Filtered candidates with hook analysis attached
        """
        filtered = []
        
        for candidate in candidates:
            clip_start = candidate.get('start', 0)
            hook_analysis = self.score_clip_hook(transcript_segments, clip_start)
            
            # Attach hook analysis to candidate
            candidate['hook_analysis'] = hook_analysis
            candidate['hook_score'] = hook_analysis['hook_score']
            
            # Filter by threshold
            if hook_analysis['hook_score'] >= min_hook_score:
                filtered.append(candidate)
            else:
                logger.debug(
                    f"Rejected clip at {clip_start:.1f}s: "
                    f"hook_score={hook_analysis['hook_score']:.1f} < {min_hook_score}"
                )
        
        logger.info(
            f"Hook quality filter: {len(filtered)}/{len(candidates)} candidates passed "
            f"(threshold={min_hook_score})"
        )
        
        return filtered
