"""
Psychological virality scoring model.

Multi-factor scoring:
- Curiosity Gap: 25%
- Emotional Intensity: 20%
- Contrarian Claim: 20%
- Specific Outcome: 15%
- Relatability: 10%
- CTA/Tension: 10%

Clips must score > 65/100 to pass.
"""

import logging
import re
from typing import Dict, List

logger = logging.getLogger(__name__)


# Curiosity gap patterns
CURIOSITY_PATTERNS = [
    r'\b(why|how|what|secret|nobody|never knew|turns out)\b',
    r'\b(you wont believe|you need to know|this is why)\b',
    r'\b(revealed|exposed|discovered|found out)\b',
    r'\?'
]

# Contrarian patterns
CONTRARIAN_PATTERNS = [
    r'\b(wrong|lie|myth|actually|opposite|dont believe)\b',
    r'\b(everyone thinks|they tell you|they want you)\b',
    r'\b(truth is|reality is|fact is)\b'
]

# Specific outcome patterns
SPECIFIC_PATTERNS = [
    r'\b\d+%',  # Percentages
    r'\$\d+',  # Money
    r'\b\d+[xX]',  # Multipliers
    r'\b(exactly|specific|precise|measured|proven)\b',
    r'\b\d+\s+(days?|weeks?|months?|hours?)\b'  # Time
]

# Relatability patterns
RELATABILITY_PATTERNS = [
    r'\b(you|your|youre)\b',
    r'\b(we all|everyone|anyone|somebody)\b',
    r'\b(if youve ever|you know that feeling)\b',
    r'\b(as a|being a|when youre)\b'
]

# CTA/Tension patterns
CTA_PATTERNS = [
    r'\b(watch|listen|look|see|check|try|do this)\b',
    r'\b(must|have to|need to|should|better)\b',
    r'\b(before|after|until|unless|or else)\b',
    r'\b(warning|danger|careful|watch out)\b'
]


class PsychologicalScorer:
    """
    Scores clips based on psychological virality factors.
    
    Uses weighted multi-factor model to predict viral potential.
    """
    
    def __init__(self, threshold: float = 65.0):
        """
        Initialize psychological scorer.
        
        Args:
            threshold: Minimum score (0-100) for clip to pass
        """
        self.threshold = threshold
        
        # Compile patterns
        self.curiosity_regex = [re.compile(p, re.IGNORECASE) for p in CURIOSITY_PATTERNS]
        self.contrarian_regex = [re.compile(p, re.IGNORECASE) for p in CONTRARIAN_PATTERNS]
        self.specific_regex = [re.compile(p, re.IGNORECASE) for p in SPECIFIC_PATTERNS]
        self.relatability_regex = [re.compile(p, re.IGNORECASE) for p in RELATABILITY_PATTERNS]
        self.cta_regex = [re.compile(p, re.IGNORECASE) for p in CTA_PATTERNS]
        
        logger.info(f"Psychological scorer initialized (threshold={threshold})")
    
    def _score_patterns(self, text: str, patterns: List[re.Pattern], max_score: float = 10.0) -> float:
        """Score text against patterns."""
        matches = sum(1 for pattern in patterns if pattern.search(text))
        # 3+ matches = max score
        return min((matches / 3.0) * max_score, max_score)
    
    def score_clip(self, clip: Dict) -> Dict:
        """
        Score a clip using psychological virality factors.
        
        Args:
            clip: Clip dictionary with text and metadata
            
        Returns:
            Dictionary with factor scores and final score
        """
        text = clip.get('text', '')
        duration = clip.get('duration', 0)
        
        # Factor 1: Curiosity Gap (25%)
        curiosity_score = self._score_patterns(text, self.curiosity_regex)
        
        # Factor 2: Emotional Intensity (20%) - use emotion analysis if available
        emotion_score = clip.get('emotion_intensity', 5.0)  # Default middle
        if 'emotion_analysis' in clip:
            emotion_score = clip['emotion_analysis'].get('emotion_intensity', 5.0)
        
        # Factor 3: Contrarian Claim (20%)
        contrarian_score = self._score_patterns(text, self.contrarian_regex)
        
        # Factor 4: Specific Outcome (15%)
        specific_score = self._score_patterns(text, self.specific_regex)
        
        # Factor 5: Relatability (10%)
        relatability_score = self._score_patterns(text, self.relatability_regex)
        
        # Factor 6: CTA/Tension (10%)
        cta_score = self._score_patterns(text, self.cta_regex)
        
        # Calculate weighted final score (0-100)
        psychological_score = (
            curiosity_score * 0.25 +
            emotion_score * 0.20 +
            contrarian_score * 0.20 +
            specific_score * 0.15 +
            relatability_score * 0.10 +
            cta_score * 0.10
        ) * 10.0  # Scale to 0-100
        
        # Apply penalties
        penalties = []
        
        # Duration penalty (over 60s)
        if duration > 60:
            psychological_score -= 10
            penalties.append('Duration > 60s (-10)')
        
        # No curiosity penalty
        if curiosity_score < 3.0:
            psychological_score -= 5
            penalties.append('Low curiosity (-5)')
        
        # Clip at 0-100
        psychological_score = max(0.0, min(psychological_score, 100.0))
        
        # Determine pass/fail
        passes = psychological_score >= self.threshold
        
        # Generate reasoning
        strengths = []
        weaknesses = []
        
        if curiosity_score >= 7.0:
            strengths.append(f'Strong curiosity gap ({curiosity_score:.1f}/10)')
        elif curiosity_score < 4.0:
            weaknesses.append(f'Weak curiosity gap ({curiosity_score:.1f}/10)')
        
        if emotion_score >= 7.0:
            strengths.append(f'High emotional intensity ({emotion_score:.1f}/10)')
        elif emotion_score < 4.0:
            weaknesses.append(f'Low emotional intensity ({emotion_score:.1f}/10)')
        
        if contrarian_score >= 7.0:
            strengths.append(f'Strong contrarian claim ({contrarian_score:.1f}/10)')
        
        if specific_score >= 7.0:
            strengths.append('Specific outcomes/data')
        
        if relatability_score >= 7.0:
            strengths.append('Highly relatable')
        
        if not strengths:
            strengths.append('Needs improvement across factors')
        
        return {
            'psychological_score': psychological_score,
            'curiosity_score': curiosity_score,
            'emotion_score': emotion_score,
            'contrarian_score': contrarian_score,
            'specific_score': specific_score,
            'relatability_score': relatability_score,
            'cta_score': cta_score,
            'passes_threshold': passes,
            'penalties': penalties,
            'strengths': strengths,
            'weaknesses': weaknesses
        }
    
    def score_and_filter_clips(self, clips: List[Dict]) -> List[Dict]:
        """
        Score clips and filter by threshold.
        
        Args:
            clips: List of clip candidates
            
        Returns:
            Filtered clips with psychological scores
        """
        scored_clips = []
        
        for clip in clips:
            psych_analysis = self.score_clip(clip)
            
            # Add to clip
            clip['psychological_analysis'] = psych_analysis
            clip['psychological_score'] = psych_analysis['psychological_score']
            
            # Filter by threshold
            if psych_analysis['passes_threshold']:
                scored_clips.append(clip)
        
        logger.info(
            f"Psychological scoring: {len(scored_clips)}/{len(clips)} clips passed "
            f"threshold ({self.threshold})"
        )
        
        return scored_clips
    
    def get_top_clips(
        self,
        clips: List[Dict],
        top_n: int = 5
    ) -> List[Dict]:
        """
        Get top N clips by psychological score.
        
        Args:
            clips: List of scored clips
            top_n: Number of top clips to return
            
        Returns:
            Top N clips sorted by score
        """
        # Sort by psychological score
        sorted_clips = sorted(
            clips,
            key=lambda x: x.get('psychological_score', 0),
            reverse=True
        )
        
        top_clips = sorted_clips[:top_n]
        
        # Log results
        logger.info(f"Top {top_n} clips by psychological score:")
        for i, clip in enumerate(top_clips, 1):
            score = clip.get('psychological_score', 0)
            start = clip.get('start', 0)
            logger.info(f"  {i}. Score: {score:.1f}, Start: {start:.1f}s")
        
        return top_clips
