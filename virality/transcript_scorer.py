"""
Sentence-level virality scoring for transcripts.

Scores sentences based on viral patterns:
- Shock words and confession triggers
- Hooks and curiosity gaps
- Contrarian framing
- Numeric specifics
- Open loops
"""

import logging
import re
from typing import Dict, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SentenceScore:
    """Score data for a single sentence."""
    text: str
    position: int  # Position in transcript
    shock_score: float
    confession_score: float
    hook_score: float
    contrarian_score: float
    numeric_score: float
    open_loop_score: float
    overall_score: float


# Viral patterns
SHOCK_PATTERNS = [
    r'\b(shocked|stunned|cant believe|unbelievable|insane|crazy|wild)\b',
    r'\b(never seen|never knew|never thought|nobody told)\b',
    r'\b(ruined|destroyed|changed everything|game changer)\b'
]

CONFESSION_PATTERNS = [
    r'\b(i have to admit|truth is|honestly|confession)\b',
    r'\b(nobody talks about|secret|hidden truth|they dont tell)\b',
    r'\b(i was wrong|i regret|mistake|should have)\b'
]

HOOK_PATTERNS = [
    r'^\s*(?:wait|stop|listen|look|imagine|picture this)',  # Opening hooks
    r'\b(you wont believe|you need to|you have to)\b',
    r'\b(this is why|heres why|the reason)\b',
    r'\?$'  # Ends with question
]

CONTRARIAN_PATTERNS = [
    r'\b(everyone is wrong|theyre lying|dont believe|myth)\b',
    r'\b(opposite|actually|contrary to|despite what)\b',
    r'\b(nobody tells you|they dont want you to know)\b'
]

NUMERIC_PATTERNS = [
    r'\b\d+%\b',  # Percentages
    r'\$[\d,]+',  # Dollar amounts
    r'\b\d+[xX]\b',  # Multipliers (10x, 5x)
    r'\b\d+\s+(hours?|days?|weeks?|months?|years?)\b'  # Time periods
]

OPEN_LOOP_PATTERNS = [
    r'\b(but|however|until|except)\b',
    r'\b(wait until|but then|and then)\b',
    r'\b(spoiler|surprise|twist)\b'
]


class TranscriptScorer:
    """
    Scores individual sentences in transcript for virality potential.
    """
    
    def __init__(self):
        """Initialize transcript scorer."""
        # Compile regex patterns for efficiency
        self.shock_regex = [re.compile(p, re.IGNORECASE) for p in SHOCK_PATTERNS]
        self.confession_regex = [re.compile(p, re.IGNORECASE) for p in CONFESSION_PATTERNS]
        self.hook_regex = [re.compile(p, re.IGNORECASE) for p in HOOK_PATTERNS]
        self.contrarian_regex = [re.compile(p, re.IGNORECASE) for p in CONTRARIAN_PATTERNS]
        self.numeric_regex = [re.compile(p, re.IGNORECASE) for p in NUMERIC_PATTERNS]
        self.open_loop_regex = [re.compile(p, re.IGNORECASE) for p in OPEN_LOOP_PATTERNS]
        
        logger.info("Transcript scorer initialized")
    
    def score_sentence(self, sentence: str, position: int = 0) -> SentenceScore:
        """
        Score a single sentence for virality.
        
        Args:
            sentence: Sentence text
            position: Position in transcript (0-indexed)
            
        Returns:
            SentenceScore with individual and overall scores
        """
        # Score each pattern category
        shock_score = self._score_patterns(sentence, self.shock_regex)
        confession_score = self._score_patterns(sentence, self.confession_regex)
        hook_score = self._score_patterns(sentence, self.hook_regex)
        contrarian_score = self._score_patterns(sentence, self.contrarian_regex)
        numeric_score = self._score_patterns(sentence, self.numeric_regex)
        open_loop_score = self._score_patterns(sentence, self.open_loop_regex)
        
        # Bonus for position (first sentences more valuable)
        position_bonus = 1.0
        if position == 0:  # First sentence
            position_bonus = 1.5
        elif position < 3:  # First few sentences
            position_bonus = 1.2
        
        # Calculate overall score (weighted average)
        overall_score = (
            shock_score * 0.25 +
            confession_score * 0.20 +
            hook_score * 0.25 +
            contrarian_score * 0.15 +
            numeric_score * 0.10 +
            open_loop_score * 0.05
        ) * position_bonus
        
        return SentenceScore(
            text=sentence,
            position=position,
            shock_score=shock_score,
            confession_score=confession_score,
            hook_score=hook_score,
            contrarian_score=contrarian_score,
            numeric_score=numeric_score,
            open_loop_score=open_loop_score,
            overall_score=min(overall_score, 10.0)  # Cap at 10
        )
    
    def _score_patterns(self, text: str, patterns: List[re.Pattern]) -> float:
        """
        Score text against a list of regex patterns.
        
        Args:
            text: Text to score
            patterns: List of compiled regex patterns
            
        Returns:
            Score 0-10 based on pattern matches
        """
        matches = sum(1 for pattern in patterns if pattern.search(text))
        # Convert to 0-10 scale (3+ matches = max score)
        return min(matches * 3.0, 10.0)
    
    def score_transcript_sentences(self, text: str) -> List[SentenceScore]:
        """
        Score all sentences in a transcript.
        
        Args:
            text: Full transcript text
            
        Returns:
            List of SentenceScore objects
        """
        # Split into sentences (simple split on . ! ?)
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Score each sentence
        scores = []
        for i, sentence in enumerate(sentences):
            score = self.score_sentence(sentence, i)
            scores.append(score)
        
        return scores
    
    def get_high_scoring_sentences(
        self, 
        text: str, 
        threshold: float = 5.0,
        top_n: int = None
    ) -> List[SentenceScore]:
        """
        Get sentences above a virality threshold.
        
        Args:
            text: Full transcript text
            threshold: Minimum overall_score to include
            top_n: If set, return only top N sentences
            
        Returns:
            List of high-scoring sentences
        """
        scores = self.score_transcript_sentences(text)
        high_scores = [s for s in scores if s.overall_score >= threshold]
        
        # Sort by score
        high_scores.sort(key=lambda x: x.overall_score, reverse=True)
        
        if top_n:
            return high_scores[:top_n]
        return high_scores
    
    def analyze_transcript(self, text: str) -> Dict:
        """
        Full transcript analysis with statistics.
        
        Args:
            text: Full transcript text
            
        Returns:
            Dictionary with analysis results
        """
        scores = self.score_transcript_sentences(text)
        
        if not scores:
            return {
                'sentence_count': 0,
                'avg_score': 0.0,
                'high_scoring_count': 0,
                'top_sentences': []
            }
        
        avg_score = sum(s.overall_score for s in scores) / len(scores)
        high_scoring = [s for s in scores if s.overall_score >= 5.0]
        top_sentences = sorted(scores, key=lambda x: x.overall_score, reverse=True)[:5]
        
        return {
            'sentence_count': len(scores),
            'avg_score': avg_score,
            'high_scoring_count': len(high_scoring),
            'high_scoring_ratio': len(high_scoring) / len(scores),
            'top_sentences': top_sentences,
            'all_scores': scores
        }
