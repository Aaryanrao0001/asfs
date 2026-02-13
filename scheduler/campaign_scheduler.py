"""Campaign Scheduler - Background scheduler for campaign-based uploads."""

import logging
import time
import threading
from datetime import datetime
from typing import Optional, Callable, Dict, List
from pathlib import Path

from database import CampaignManager, VideoRegistry

logger = logging.getLogger(__name__)


class CampaignScheduler:
    """
    Background scheduler for campaign-based automatic video uploads.
    
    Features:
    - Manages multiple independent campaigns
    - Each campaign has its own schedule
    - Respects campaign-specific metadata
    - Runs continuously in background thread
    """
    
    # Class constants
    CHECK_INTERVAL_SECONDS = 60  # How often to check for pending uploads
    
    def __init__(self):
        """Initialize the campaign scheduler."""
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.campaign_manager = CampaignManager()
        self.video_registry = VideoRegistry()
        
        # Track last upload time per campaign
        self.campaign_last_upload: Dict[int, datetime] = {}
        
        # Callback for upload execution
        # Signature: callback(video_id, platform, metadata) -> bool
        self.upload_callback: Optional[Callable] = None
    
    def set_upload_callback(self, callback: Callable):
        """
        Set callback function for executing uploads.
        
        Args:
            callback: Function with signature: callback(video_id, platform, metadata) -> bool
        """
        self.upload_callback = callback
    
    def start(self):
        """Start the campaign scheduler in a background thread."""
        if self.running:
            logger.warning("Campaign scheduler already running")
            return
        
        if not self.upload_callback:
            logger.error("Cannot start campaign scheduler: no upload callback set")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info("Campaign scheduler started")
    
    def stop(self):
        """Stop the campaign scheduler gracefully."""
        if not self.running:
            return
        
        logger.info("Stopping campaign scheduler gracefully...")
        self.running = False
        
        if self.thread:
            # Give thread time to finish current operation
            self.thread.join(timeout=10)
            
            if self.thread.is_alive():
                logger.warning("Campaign scheduler thread did not stop within timeout")
        
        logger.info("Campaign scheduler stopped")
    
    def is_running(self) -> bool:
        """Check if campaign scheduler is running."""
        return self.running
    
    def _run_loop(self):
        """Main scheduler loop (runs in background thread)."""
        logger.info("Campaign scheduler loop started")
        
        while self.running:
            try:
                # Get all active campaigns with scheduling enabled
                campaigns = self.campaign_manager.list_campaigns(active_only=True)
                active_campaigns = [c for c in campaigns if c.get('schedule_enabled')]
                
                if not active_campaigns:
                    logger.debug("No active campaigns with scheduling enabled")
                    time.sleep(self.CHECK_INTERVAL_SECONDS)
                    continue
                
                # Process each campaign independently
                for campaign in active_campaigns:
                    campaign_id = campaign['id']
                    
                    # Check if this campaign should upload
                    if self._should_campaign_upload(campaign):
                        # Find next video to upload for this campaign
                        upload_task = self._find_next_campaign_upload(campaign)
                        
                        if upload_task:
                            video_id, platform, metadata = upload_task
                            
                            logger.info(
                                f"Campaign '{campaign['name']}': "
                                f"uploading {video_id} to {platform}"
                            )
                            
                            # Execute upload via callback
                            try:
                                success = self.upload_callback(video_id, platform, metadata)
                                
                                if success:
                                    logger.info(
                                        f"Campaign '{campaign['name']}': "
                                        f"upload successful - {video_id} to {platform}"
                                    )
                                    # Update last upload time for this campaign
                                    self.campaign_last_upload[campaign_id] = datetime.now()
                                else:
                                    logger.warning(
                                        f"Campaign '{campaign['name']}': "
                                        f"upload failed - {video_id} to {platform}"
                                    )
                            except Exception as e:
                                logger.error(
                                    f"Campaign '{campaign['name']}': "
                                    f"error in scheduled upload - {e}"
                                )
                
                # Sleep for a short interval before checking again
                time.sleep(self.CHECK_INTERVAL_SECONDS)
                
            except Exception as e:
                logger.error(f"Error in campaign scheduler loop: {e}")
                time.sleep(self.CHECK_INTERVAL_SECONDS)
        
        logger.info("Campaign scheduler loop ended")
    
    def _should_campaign_upload(self, campaign: Dict) -> bool:
        """
        Check if enough time has passed for a campaign to perform another upload.
        
        Args:
            campaign: Campaign dictionary
            
        Returns:
            True if upload should be attempted
        """
        campaign_id = campaign['id']
        
        # Get campaign schedule settings
        gap_hours = campaign.get('schedule_gap_hours', 1)
        gap_minutes = campaign.get('schedule_gap_minutes', 0)
        gap_seconds = (gap_hours * 3600) + (gap_minutes * 60)
        
        # Check last upload time for this campaign
        last_upload = self.campaign_last_upload.get(campaign_id)
        
        if last_upload is None:
            # First upload for this campaign
            return True
        
        elapsed = (datetime.now() - last_upload).total_seconds()
        return elapsed >= gap_seconds
    
    def _find_next_campaign_upload(self, campaign: Dict) -> Optional[tuple]:
        """
        Find the next video to upload for a campaign.
        
        Args:
            campaign: Campaign dictionary
            
        Returns:
            Tuple of (video_id, platform, metadata) or None if no uploads pending
        """
        try:
            campaign_id = campaign['id']
            campaign_platforms = campaign.get('platforms', [])
            
            # Get all videos assigned to this campaign
            campaign_videos = self.campaign_manager.get_campaign_videos(campaign_id)
            
            if not campaign_videos:
                logger.debug(f"Campaign '{campaign['name']}': no videos assigned")
                return None
            
            # Sort by upload order
            campaign_videos.sort(key=lambda v: v.get('upload_order', 0))
            
            # Try each video in order
            for campaign_video in campaign_videos:
                video_id = campaign_video['video_id']
                
                # Get video info from registry
                video = self.video_registry.get_video(video_id)
                if not video:
                    logger.warning(f"Video {video_id} not found in registry")
                    continue
                
                # Try each platform for this campaign
                for platform in campaign_platforms:
                    # Check if video can be uploaded to this platform
                    can_upload, reason = self.video_registry.can_upload(video_id, platform)
                    
                    if can_upload:
                        # Found a pending upload
                        # Use campaign-specific metadata with fallbacks
                        title = campaign_video.get('title') or video.get('title') or f"Video {video_id}"
                        metadata = {
                            'file_path': video.get('file_path'),
                            'title': title,
                            'caption': campaign_video.get('caption', ''),
                            'hashtags': campaign_video.get('hashtags', ''),
                            'duration': video.get('duration'),
                            'campaign_id': campaign_id,
                            'campaign_name': campaign['name']
                        }
                        return (video_id, platform, metadata)
            
            logger.debug(f"Campaign '{campaign['name']}': all videos uploaded")
            return None
            
        except Exception as e:
            logger.error(f"Error finding next campaign upload: {e}")
            return None


# Singleton instance
_campaign_scheduler = None


def get_campaign_scheduler() -> CampaignScheduler:
    """Get the global campaign scheduler instance."""
    global _campaign_scheduler
    if _campaign_scheduler is None:
        _campaign_scheduler = CampaignScheduler()
    return _campaign_scheduler
