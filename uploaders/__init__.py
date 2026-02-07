"""Platform uploaders using Brave browser automation."""

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

__all__ = [
    'upload_to_tiktok',
    'upload_to_instagram', 
    'upload_to_youtube',
    'upload_to_tiktok_browser',
    'upload_to_instagram_browser',
    'upload_to_youtube_browser',
    'BraveBrowserManager'
]
