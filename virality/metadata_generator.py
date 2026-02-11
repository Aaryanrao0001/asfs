"""
Advanced metadata generation for viral clips.

Generates:
- Multiple title variants
- Captions with hooks
- Platform-specific hashtags
- Text overlay suggestions
- B-roll suggestions
"""

import logging
import re
import random
from typing import Dict, List

logger = logging.getLogger(__name__)


# Title templates by pattern
TITLE_TEMPLATES = {
    'curiosity': [
        "Why {topic} (you won't believe this)",
        "The {topic} secret nobody talks about",
        "{number} things about {topic} that'll shock you",
        "What {audience} don't know about {topic}"
    ],
    'contrarian': [
        "Everyone is wrong about {topic}",
        "Stop {action} - here's why",
        "The truth about {topic}",
        "{topic} is a lie - here's proof"
    ],
    'emotional': [
        "This {topic} ruined everything",
        "I can't believe {topic}",
        "{topic} changed my life",
        "The {emotion} truth about {topic}"
    ],
    'specific': [
        "How I {outcome} in {timeframe}",
        "{number}% of {audience} don't know this",
        "${amount} lesson from {topic}",
        "{timeframe} to {outcome}"
    ]
}

# Overlay text patterns
OVERLAY_PATTERNS = {
    'shock': ['WAIT WHAT', 'NO WAY', 'THIS IS INSANE', 'WATCH THIS'],
    'question': ['WHY?', 'HOW?', 'REALLY?', 'SERIOUSLY?'],
    'emphasis': ['EXACTLY', 'FINALLY', 'THIS', 'TRUTH'],
    'cta': ['WATCH', 'LISTEN', 'LOOK', 'SEE THIS']
}

# Platform-specific hashtag strategies
PLATFORM_HASHTAGS = {
    'tiktok': {
        'viral': ['#fyp', '#foryou', '#foryoupage', '#viral', '#trending'],
        'niche': []  # Added by content analysis
    },
    'instagram': {
        'viral': ['#reels', '#reelsinstagram', '#viral', '#explore', '#trending'],
        'niche': []
    },
    'youtube': {
        'viral': ['#shorts', '#viral', '#trending'],
        'niche': []
    }
}


class ViralMetadataGenerator:
    """
    Generates viral-optimized metadata for clips.
    """
    
    def __init__(self):
        """Initialize metadata generator."""
        logger.info("Viral metadata generator initialized")
    
    def _extract_key_terms(self, text: str, max_terms: int = 5) -> List[str]:
        """
        Extract key terms from text.
        
        Args:
            text: Text to analyze
            max_terms: Maximum terms to extract
            
        Returns:
            List of key terms
        """
        # Remove common words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these',
            'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'my', 'your'
        }
        
        # Extract words
        words = re.findall(r'\b[a-z]+\b', text.lower())
        
        # Filter and count
        word_freq = {}
        for word in words:
            if word not in stop_words and len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        return [word for word, _ in sorted_words[:max_terms]]
    
    def generate_titles(self, clip: Dict, count: int = 3) -> List[str]:
        """
        Generate title variants for a clip.
        
        Args:
            clip: Clip dictionary with text and analysis
            count: Number of titles to generate
            
        Returns:
            List of title strings
        """
        text = clip.get('text', '')
        
        # Extract key terms
        key_terms = self._extract_key_terms(text)
        topic = key_terms[0] if key_terms else 'this'
        
        # Detect clip pattern
        psych_analysis = clip.get('psychological_analysis', {})
        curiosity_score = psych_analysis.get('curiosity_score', 0)
        contrarian_score = psych_analysis.get('contrarian_score', 0)
        emotion_score = psych_analysis.get('emotion_score', 0)
        
        # Choose template category
        if curiosity_score >= 7.0:
            category = 'curiosity'
        elif contrarian_score >= 7.0:
            category = 'contrarian'
        elif emotion_score >= 7.0:
            category = 'emotional'
        else:
            category = 'specific'
        
        templates = TITLE_TEMPLATES.get(category, TITLE_TEMPLATES['curiosity'])
        
        # Generate titles
        titles = []
        for template in templates[:count]:
            title = template.format(
                topic=topic.title(),
                number=3,
                audience='people',
                action='doing this',
                emotion='shocking',
                outcome='success',
                timeframe='30 days',
                amount='1000'
            )
            titles.append(title)
        
        return titles
    
    def generate_caption(self, clip: Dict) -> str:
        """
        Generate engaging caption for a clip.
        
        Args:
            clip: Clip dictionary
            
        Returns:
            Caption string
        """
        text = clip.get('text', '')
        
        # Extract first sentence as hook
        sentences = re.split(r'[.!?]+', text)
        hook = sentences[0].strip() if sentences else text[:100]
        
        # Add emoji based on emotion
        emotion = clip.get('primary_emotion', 'neutral')
        emoji_map = {
            'anger': '😠',
            'shock': '😱',
            'validation': '💯',
            'excitement': '🔥',
            'sadness': '😢',
            'neutral': '👀'
        }
        emoji = emoji_map.get(emotion, '👀')
        
        # Build caption
        caption = f"{emoji} {hook}\n\n"
        
        # Add CTA
        ctas = [
            "Watch till the end!",
            "You need to see this!",
            "This changes everything!",
            "Tag someone who needs this!"
        ]
        
        caption += random.choice(ctas)
        
        return caption
    
    def generate_hashtags(
        self,
        clip: Dict,
        platform: str = 'tiktok',
        max_tags: int = 15
    ) -> List[str]:
        """
        Generate platform-specific hashtags.
        
        Args:
            clip: Clip dictionary
            platform: Platform name (tiktok/instagram/youtube)
            max_tags: Maximum hashtags to generate
            
        Returns:
            List of hashtag strings (with #)
        """
        text = clip.get('text', '').lower()
        
        # Get platform base tags
        platform_tags = PLATFORM_HASHTAGS.get(
            platform.lower(),
            PLATFORM_HASHTAGS['tiktok']
        )
        
        tags = list(platform_tags['viral'])
        
        # Add emotion-based tags
        emotion = clip.get('primary_emotion', 'neutral')
        emotion_tags = {
            'shock': ['#shocking', '#unbelievable', '#mindblown'],
            'anger': ['#truth', '#reality', '#exposed'],
            'validation': ['#relatable', '#facts', '#true'],
            'excitement': ['#amazing', '#incredible', '#awesome']
        }
        
        if emotion in emotion_tags:
            tags.extend(emotion_tags[emotion])
        
        # Add content-based tags (extract from key terms)
        key_terms = self._extract_key_terms(text, max_terms=5)
        for term in key_terms:
            if len(tags) < max_tags:
                tags.append(f'#{term}')
        
        return tags[:max_tags]
    
    def generate_overlays(self, clip: Dict, count: int = 3) -> List[str]:
        """
        Generate text overlay suggestions.
        
        Args:
            clip: Clip dictionary
            count: Number of overlays to suggest
            
        Returns:
            List of overlay text strings
        """
        # Determine overlay style based on clip
        psych_analysis = clip.get('psychological_analysis', {})
        curiosity_score = psych_analysis.get('curiosity_score', 0)
        emotion_score = psych_analysis.get('emotion_score', 0)
        
        overlays = []
        
        if curiosity_score >= 7.0:
            overlays.extend(OVERLAY_PATTERNS['question'][:2])
        
        if emotion_score >= 7.0:
            overlays.extend(OVERLAY_PATTERNS['shock'][:2])
        
        if not overlays:
            overlays.extend(OVERLAY_PATTERNS['emphasis'][:2])
        
        # Add CTA
        overlays.append(OVERLAY_PATTERNS['cta'][0])
        
        return overlays[:count]
    
    def generate_broll_suggestions(self, clip: Dict) -> List[str]:
        """
        Suggest B-roll footage types.
        
        Args:
            clip: Clip dictionary
            
        Returns:
            List of B-roll suggestions
        """
        text = clip.get('text', '').lower()
        
        suggestions = []
        
        # Pattern-based suggestions
        if re.search(r'\b(money|dollar|cash|paid)\b', text):
            suggestions.append('Money/cash visuals')
        
        if re.search(r'\b(time|clock|hour|day|week)\b', text):
            suggestions.append('Clock/time-lapse footage')
        
        if re.search(r'\b(before|after)\b', text):
            suggestions.append('Before/after comparison')
        
        if re.search(r'\b(graph|chart|data|number)\b', text):
            suggestions.append('Data visualization/graphs')
        
        # Default suggestions
        if not suggestions:
            suggestions.append('Reaction shots')
            suggestions.append('Text animations')
        
        return suggestions[:3]
    
    def generate_all_metadata(self, clip: Dict, platform: str = 'tiktok') -> Dict:
        """
        Generate complete metadata package for a clip.
        
        Args:
            clip: Clip dictionary
            platform: Target platform
            
        Returns:
            Dictionary with all metadata
        """
        return {
            'titles': self.generate_titles(clip, count=3),
            'caption': self.generate_caption(clip),
            'hashtags': self.generate_hashtags(clip, platform=platform),
            'overlays': self.generate_overlays(clip, count=3),
            'broll_suggestions': self.generate_broll_suggestions(clip)
        }
