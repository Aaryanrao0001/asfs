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
    
    # Caption settings (NEW)
    captions: List[str] = None  # Multiple captions for randomized mode
    
    # Tags settings
    tags: List[str] = None  # List of tags (shuffled in randomized mode)
    
    # Hashtag prefix toggle
    hashtag_prefix: bool = True
    
    # Hashtag mode: "strict" | "append" | "ai_only"
    hashtag_mode: str = "append"
    
    # Hook phrase for video overlay (NEW)
    hook_phrase: str = ""
    hook_position: str = "Top Left"
    
    # Logo overlay (NEW)
    logo_path: str = ""
    
    # CSV file path for loading metadata (NEW)
    csv_file_path: str = ""
    
    def __post_init__(self):
        """Initialize default empty lists."""
        if self.titles is None:
            self.titles = [""]
        if self.descriptions is None:
            self.descriptions = [""]
        if self.captions is None:
            self.captions = [""]
        if self.tags is None:
            self.tags = []
    
    @classmethod
    def from_ui_values(cls, mode: str, title_input: str, description_input: str, 
                       caption_input: str, tags_input: str, hashtag_prefix: bool = True,
                       hook_phrase: str = "", hook_position: str = "Top Left",
                       logo_path: str = "", csv_file_path: str = "",
                       hashtag_mode: str = "append") -> 'MetadataConfig':
        """
        Create MetadataConfig from UI input values.
        
        Args:
            mode: "uniform" or "randomized"
            title_input: Comma-separated titles (for randomized) or single title (for uniform)
            description_input: Comma-separated descriptions or single description
            caption_input: Comma-separated captions or single caption
            tags_input: Comma-separated tags
            hashtag_prefix: Whether to add # prefix to tags
            hook_phrase: Text to overlay on video
            hook_position: Position for hook phrase overlay
            logo_path: Path to logo image file
            csv_file_path: Optional path to CSV file with metadata
            
        Returns:
            MetadataConfig instance
        """
        # Parse comma-separated values from UI
        if mode == "randomized":
            titles = [t.strip() for t in title_input.split(',') if t.strip()]
            descriptions = [d.strip() for d in description_input.split(',') if d.strip()]
            captions = [c.strip() for c in caption_input.split(',') if c.strip()]
        else:
            titles = [title_input.strip()] if title_input.strip() else [""]
            descriptions = [description_input.strip()] if description_input.strip() else [""]
            captions = [caption_input.strip()] if caption_input.strip() else [""]
        
        tags = [t.strip() for t in tags_input.split(',') if t.strip()]
        
        # Load and merge CSV data if provided
        if csv_file_path:
            try:
                from .csv_loader import load_csv_metadata, merge_csv_with_ui_metadata
                csv_data = load_csv_metadata(csv_file_path)
                merged = merge_csv_with_ui_metadata(
                    csv_data, titles, captions, descriptions, tags
                )
                titles = merged["titles"]
                descriptions = merged["descriptions"]
                captions = merged["captions"]
                tags = merged["tags"]
            except Exception as e:
                # Log error but continue with UI values
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to load CSV metadata: {e}. Using UI values only.")
        
        return cls(
            mode=mode,
            titles=titles if titles else [""],
            descriptions=descriptions if descriptions else [""],
            captions=captions if captions else [""],
            tags=tags,
            hashtag_prefix=hashtag_prefix,
            hashtag_mode=hashtag_mode,
            hook_phrase=hook_phrase,
            hook_position=hook_position,
            logo_path=logo_path,
            csv_file_path=csv_file_path
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "mode": self.mode,
            "titles": self.titles,
            "descriptions": self.descriptions,
            "captions": self.captions,
            "tags": self.tags,
            "hashtag_prefix": self.hashtag_prefix,
            "hashtag_mode": self.hashtag_mode,
            "hook_phrase": self.hook_phrase,
            "hook_position": self.hook_position,
            "logo_path": self.logo_path,
            "csv_file_path": self.csv_file_path
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MetadataConfig':
        """Create from dictionary."""
        return cls(
            mode=data.get("mode", "uniform"),
            titles=data.get("titles", [""]),
            descriptions=data.get("descriptions", [""]),
            captions=data.get("captions", [""]),
            tags=data.get("tags", []),
            hashtag_prefix=data.get("hashtag_prefix", True),
            hashtag_mode=data.get("hashtag_mode", "append"),
            hook_phrase=data.get("hook_phrase", ""),
            hook_position=data.get("hook_position", "Top Left"),
            logo_path=data.get("logo_path", ""),
            csv_file_path=data.get("csv_file_path", "")
        )
