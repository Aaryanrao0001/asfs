"""Database module for video registry, upload tracking, and campaign management."""

from .video_registry import VideoRegistry
from .campaign_schema import create_campaign_tables, verify_campaign_schema, drop_campaign_tables
from .campaign_manager import CampaignManager

__all__ = [
    'VideoRegistry',
    'CampaignManager',
    'create_campaign_tables',
    'verify_campaign_schema',
    'drop_campaign_tables'
]
