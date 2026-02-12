"""
Emotion and sentiment analysis for transcript segments.

Uses VADER sentiment analysis and custom emotion lexicons
based on NRC Emotion Lexicon patterns.
"""

import logging
from typing import Dict, List, Tuple
import re

logger = logging.getLogger(__name__)

# Try importing VADER
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False
    logger.warning("vaderSentiment not available - emotion analysis will use basic lexicon only")


# NRC-inspired emotion lexicon (high-impact words)
EMOTION_LEXICON = {
    'anger': [
        'angry', 'furious', 'rage', 'mad', 'hate', 'disgusted', 'annoyed', 
        'frustrated', 'outraged', 'pissed', 'irritated', 'enraged'
    ],
    'shock': [
        'shocked', 'stunned', 'amazed', 'surprised', 'unbelievable', 'crazy',
        'insane', 'wtf', 'omg', 'jaw-dropping', 'mindblowing', 'wild'
    ],
    'validation': [
        'finally', 'exactly', 'truth', 'real', 'honest', 'agree', 'same',
        'this', 'why', 'nobody talks about', 'never told', 'secret'
    ],
    'fear': [
        'scared', 'afraid', 'terrified', 'nervous', 'worried', 'anxious',
        'panic', 'danger', 'threat', 'risky', 'warning'
    ],
    'excitement': [
        'excited', 'amazing', 'awesome', 'incredible', 'fantastic', 'epic',
        'love', 'best', 'perfect', 'brilliant', 'genius'
    ],
    'sadness': [
        'sad', 'depressed', 'devastated', 'heartbroken', 'miserable', 'cry',
        'tears', 'painful', 'hurt', 'suffering', 'tragic'
    ],
    'trust': [
        'trust', 'believe', 'reliable', 'honest', 'genuine', 'authentic',
        'transparent', 'credible', 'proven', 'verified'
    ],
    'anticipation': [
        'soon', 'coming', 'wait', 'about to', 'going to', 'next', 'future',
        'watch', 'reveal', 'discover', 'unveil', 'announce'
    ]
}

# High-virality emotional triggers
VIRAL_TRIGGERS = [
    'never', 'always', 'nobody', 'everyone', 'shocked', 'crazy', 'insane',
    'ruined', 'destroyed', 'unbelievable', 'secret', 'truth', 'lie', 'lies',
    'wrong', 'right', 'mistake', 'regret', 'warning', 'danger', 'revealed',
    'exposed', 'hidden', 'banned', 'illegal', 'forbidden', 'controversial'
]

# Filler words that reduce hook strength
FILLER_WORDS = [
    'um', 'uh', 'like', 'you know', 'basically', 'literally', 'actually',
    'so', 'well', 'i mean', 'kind of', 'sort of', 'pretty much'
]


class EmotionAnalyzer:
    """
    Analyzes emotional content and sentiment in text.
    
    Uses both VADER sentiment analysis and custom emotion lexicons
    to identify emotional triggers for viral content.
    """
    
    def __init__(self):
        """Initialize emotion analyzer."""
        self.vader = None
        if VADER_AVAILABLE:
            self.vader = SentimentIntensityAnalyzer()
            logger.info("Emotion analyzer initialized with VADER")
        else:
            logger.info("Emotion analyzer initialized (lexicon-only mode)")
    
    def analyze_text(self, text: str) -> Dict:
        """
        Analyze text for emotional content.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with emotion scores and analysis
        """
        text_lower = text.lower()
        
        # Basic sentiment via VADER (if available)
        sentiment = {'pos': 0.0, 'neg': 0.0, 'neu': 1.0, 'compound': 0.0}
        if self.vader:
            sentiment = self.vader.polarity_scores(text)
        
        # Emotion category scoring
        emotion_scores = {}
        for emotion, words in EMOTION_LEXICON.items():
            count = sum(1 for word in words if word in text_lower)
            # Normalize by text length (per 100 words)
            word_count = len(text.split())
            emotion_scores[emotion] = (count / max(word_count, 1)) * 100
        
        # Viral trigger detection
        viral_triggers_found = [
            word for word in VIRAL_TRIGGERS if word in text_lower
        ]
        viral_trigger_score = len(viral_triggers_found) / max(len(text.split()) / 10, 1)
        
        # Primary emotion (strongest)
        primary_emotion = max(emotion_scores.items(), key=lambda x: x[1])
        
        # Overall emotional intensity (0-10 scale)
        emotion_intensity = min(sum(emotion_scores.values()) / 10, 10.0)
        
        # Polarity strength
        polarity = abs(sentiment['compound'])
        
        return {
            'sentiment': sentiment,
            'emotion_scores': emotion_scores,
            'primary_emotion': primary_emotion[0] if primary_emotion[1] > 0 else 'neutral',
            'emotion_intensity': emotion_intensity,
            'polarity': polarity,
            'viral_triggers': viral_triggers_found,
            'viral_trigger_score': min(viral_trigger_score, 10.0)
        }
    
    def get_emotion_density(self, text: str) -> float:
        """
        Calculate emotion word density (for top 15% filtering).
        
        Args:
            text: Text to analyze
            
        Returns:
            Emotion density score (0-10)
        """
        analysis = self.analyze_text(text)
        # Combine emotion intensity and viral triggers
        density = (analysis['emotion_intensity'] + analysis['viral_trigger_score']) / 2
        return density
    
    def detect_filler_words(self, text: str) -> Tuple[int, List[str]]:
        """
        Detect filler words that weaken hooks.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (count, list of filler words found)
        """
        text_lower = text.lower()
        found = [word for word in FILLER_WORDS if word in text_lower]
        return len(found), found
    
    def analyze_emotional_contrast(self, sentences: List[str]) -> float:
        """
        Detect emotional contrast across sentences (calm → explosive).
        
        Args:
            sentences: List of sentences to analyze
            
        Returns:
            Contrast score (0-10), higher = more contrast
        """
        if len(sentences) < 2:
            return 0.0
        
        # Analyze each sentence
        intensities = []
        for sentence in sentences:
            analysis = self.analyze_text(sentence)
            intensities.append(analysis['emotion_intensity'])
        
        # Calculate variance (higher variance = more contrast)
        if not intensities:
            return 0.0
        
        mean_intensity = sum(intensities) / len(intensities)
        variance = sum((x - mean_intensity) ** 2 for x in intensities) / len(intensities)
        
        # Normalize to 0-10 scale
        contrast_score = min(variance, 10.0)
        return contrast_score
