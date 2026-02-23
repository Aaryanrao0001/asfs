"""
Metadata resolver - Resolves metadata for individual clips.

Handles uniform and randomized metadata generation.
"""

import random
from typing import Dict, List, Optional
from .config import MetadataConfig


def resolve_description(user_description: Optional[str], ai_description: str) -> str:
    """
    Resolve final description with strict user priority.

    User-provided description always wins over AI-generated one.
    No merging, enhancing, or optimizing.

    Args:
        user_description: Description provided by the user (may be None or empty)
        ai_description: AI-generated description (fallback)

    Returns:
        User description if non-empty, otherwise ai_description
    """
    if user_description and user_description.strip():
        return user_description.strip()
    return ai_description


def resolve_metadata(config: MetadataConfig) -> Dict[str, str]:
    """
    Resolve metadata for a single clip based on configuration.
    
    Args:
        config: MetadataConfig instance with mode and values
        
    Returns:
        Dictionary with resolved title, description, caption, tags string, and overlays
    """
    result = {}
    
    if config.mode == "randomized":
        # Randomized mode - select one title, one description, one caption, shuffle tags
        result["title"] = random.choice(config.titles) if config.titles else ""
        result["description"] = random.choice(config.descriptions) if config.descriptions else ""
        result["caption"] = random.choice(config.captions) if config.captions else ""
        
        # Shuffle tags and format
        tags = config.tags.copy()
        random.shuffle(tags)
        
    else:
        # Uniform mode - use first (only) values
        result["title"] = config.titles[0] if config.titles else ""
        result["description"] = config.descriptions[0] if config.descriptions else ""
        result["caption"] = config.captions[0] if config.captions else ""
        tags = config.tags.copy()
    
    # Format tags with optional hashtag prefix
    if config.hashtag_prefix:
        formatted_tags = [f"#{tag}" if not tag.startswith('#') else tag for tag in tags]
    else:
        formatted_tags = [tag.lstrip('#') for tag in tags]
    
    result["tags"] = " ".join(formatted_tags)
    
    # Add overlay settings
    result["hook_phrase"] = config.hook_phrase
    result["hook_position"] = config.hook_position
    result["logo_path"] = config.logo_path
    
    return result


def resolve_metadata_batch(config: MetadataConfig, count: int) -> List[Dict[str, str]]:
    """
    Resolve metadata for multiple clips.
    
    Args:
        config: MetadataConfig instance
        count: Number of clips to generate metadata for
        
    Returns:
        List of metadata dictionaries
    """
    return [resolve_metadata(config) for _ in range(count)]
