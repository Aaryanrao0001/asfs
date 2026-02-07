"""
Metadata configuration for title, description, and tags.

Supports two modes:
1. Uniform - Same metadata for all clips
2. Randomized - Random selection from comma-separated values
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class MetadataConfig:
    """Configuration for clip metadata generation."""
    
    # Mode: "uniform" or "randomized"
    mode: str = "uniform"
    
    # Title settings
    titles: List[str] = None  # Multiple titles for randomized mode
    
    # Description settings
    descriptions: List[str] = None  # Multiple descriptions for randomized mode
    
    # Tags settings
    tags: List[str] = None  # List of tags (shuffled in randomized mode)
    
    # Hashtag prefix toggle
    hashtag_prefix: bool = True
    
    def __post_init__(self):
        """Initialize default empty lists."""
        if self.titles is None:
            self.titles = [""]
        if self.descriptions is None:
            self.descriptions = [""]
        if self.tags is None:
            self.tags = []
    
    @classmethod
    def from_ui_values(cls, mode: str, title_input: str, description_input: str, 
                       tags_input: str, hashtag_prefix: bool = True) -> 'MetadataConfig':
        """
        Create MetadataConfig from UI input values.
        
        Args:
            mode: "uniform" or "randomized"
            title_input: Comma-separated titles (for randomized) or single title (for uniform)
            description_input: Comma-separated descriptions or single description
            tags_input: Comma-separated tags
            hashtag_prefix: Whether to add # prefix to tags
            
        Returns:
            MetadataConfig instance
        """
        # Parse comma-separated values
        if mode == "randomized":
            titles = [t.strip() for t in title_input.split(',') if t.strip()]
            descriptions = [d.strip() for d in description_input.split(',') if d.strip()]
        else:
            titles = [title_input.strip()] if title_input.strip() else [""]
            descriptions = [description_input.strip()] if description_input.strip() else [""]
        
        tags = [t.strip() for t in tags_input.split(',') if t.strip()]
        
        return cls(
            mode=mode,
            titles=titles if titles else [""],
            descriptions=descriptions if descriptions else [""],
            tags=tags,
            hashtag_prefix=hashtag_prefix
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "mode": self.mode,
            "titles": self.titles,
            "descriptions": self.descriptions,
            "tags": self.tags,
            "hashtag_prefix": self.hashtag_prefix
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MetadataConfig':
        """Create from dictionary."""
        return cls(
            mode=data.get("mode", "uniform"),
            titles=data.get("titles", [""]),
            descriptions=data.get("descriptions", [""]),
            tags=data.get("tags", []),
            hashtag_prefix=data.get("hashtag_prefix", True)
        )
