"""Platform uploaders using Brave browser automation."""

from abc import ABC, abstractmethod
from typing import Optional, Dict
from dataclasses import dataclass

# New browser-based uploaders
from .brave_tiktok import upload_to_tiktok
from .brave_instagram import upload_to_instagram
from .brave_youtube import upload_to_youtube

# Also export browser-specific functions for direct use
from .brave_tiktok import upload_to_tiktok_browser
from .brave_instagram import upload_to_instagram_browser
from .brave_youtube import upload_to_youtube_browser

# Brave browser manager (singleton for pipeline)
from .brave_manager import BraveBrowserManager


@dataclass
class UploadResult:
    """Result of a platform upload operation."""
    success: bool
    platform_post_id: Optional[str] = None
    error_message: Optional[str] = None


class PlatformUploader(ABC):
    """
    Abstract interface for platform uploaders.
    
    All platform uploaders should implement this interface for consistency.
    This enables future refactoring and dependency injection.
    """
    
    @abstractmethod
    def upload(self, video_path: str, metadata: Dict) -> UploadResult:
        """
        Upload a video to the platform.
        
        Args:
            video_path: Path to video file
            metadata: Upload metadata including:
                - caption: Video caption/description
                - hashtags: List of hashtags
                - title: Video title (for YouTube)
                - Any platform-specific fields
                
        Returns:
            UploadResult with success status and post ID or error
        """
        pass


__all__ = [
    'upload_to_tiktok',
    'upload_to_instagram', 
    'upload_to_youtube',
    'upload_to_tiktok_browser',
    'upload_to_instagram_browser',
    'upload_to_youtube_browser',
    'BraveBrowserManager',
    'PlatformUploader',
    'UploadResult'
]
