"""Campaign Scheduler - Execute campaigns with proper scheduling and rate limiting."""

import time
import logging
import threading
from typing import Dict, Optional, Callable
from datetime import datetime

from database import CampaignManager

logger = logging.getLogger(__name__)


class CampaignScheduler:
    """
    Campaign scheduler for executing multi-video campaigns with proper rate limiting.
    
    Features:
    - Execute campaigns with delay between uploads
    - Apply campaign-specific metadata per upload
    - Support for pause/resume/cancel
    - Independent scheduling (campaigns don't block each other)
    - Integration with existing upload pipeline
    """
    
    def __init__(self):
        """Initialize campaign scheduler."""
        self.campaign_manager = CampaignManager()
        self.active_campaigns = {}  # campaign_id -> execution_state
        self.upload_callback: Optional[Callable] = None
        self._lock = threading.Lock()
    
    def set_upload_callback(self, callback: Callable):
        """
        Set callback function for executing uploads.
        
        The callback should have signature:
            callback(video_path, platform, metadata) -> bool
        
        Args:
            callback: Upload function that returns True on success
        """
        self.upload_callback = callback
        logger.info("Upload callback set for campaign scheduler")
    
    def execute_campaign(
        self,
        campaign_id: str,
        blocking: bool = True
    ) -> bool:
        """
        Execute a campaign by uploading all videos to configured platforms.
        
        Args:
            campaign_id: Campaign identifier
            blocking: If True, wait for completion; if False, run in background thread
            
        Returns:
            True if campaign started successfully
        """
        if not self.upload_callback:
            logger.error("Cannot execute campaign: no upload callback set")
            return False
        
        # Verify campaign exists and get details
        campaign = self.campaign_manager.get_campaign_details(campaign_id)
        if not campaign:
            logger.error(f"Campaign not found: {campaign_id}")
            return False
        
        # Check if campaign is already running
        with self._lock:
            if campaign_id in self.active_campaigns:
                logger.warning(f"Campaign {campaign_id} is already running")
                return False
            
            # Mark campaign as active
            self.active_campaigns[campaign_id] = {
                'status': 'running',
                'paused': False,
                'thread': None,
                'start_time': datetime.now()
            }
        
        # Update campaign status to active
        self.campaign_manager.update_campaign_status(campaign_id, 'active')
        
        if blocking:
            # Execute synchronously
            self._execute_campaign_sync(campaign_id, campaign)
            return True
        else:
            # Execute in background thread
            thread = threading.Thread(
                target=self._execute_campaign_sync,
                args=(campaign_id, campaign),
                daemon=True
            )
            
            with self._lock:
                self.active_campaigns[campaign_id]['thread'] = thread
            
            thread.start()
            logger.info(f"Campaign {campaign_id} started in background thread")
            return True
    
    def _execute_campaign_sync(self, campaign_id: str, campaign: Dict):
        """
        Synchronous campaign execution logic.
        
        Args:
            campaign_id: Campaign identifier
            campaign: Campaign details dictionary
        """
        logger.info(f"Starting campaign execution: {campaign_id} ({campaign['name']})")
        
        try:
            # Get campaign configuration
            schedule = campaign.get('schedule')
            if not schedule:
                logger.error(f"No schedule configuration for campaign {campaign_id}")
                self._complete_campaign(campaign_id, success=False)
                return
            
            platforms = schedule['platforms']
            delay_seconds = schedule.get('delay_seconds', 0)
            
            # Get videos in order
            videos = campaign.get('videos', [])
            if not videos:
                logger.warning(f"No videos in campaign {campaign_id}")
                self._complete_campaign(campaign_id, success=True)
                return
            
            total_uploads = len(videos) * len(platforms)
            completed = 0
            failed = 0
            
            logger.info(f"Campaign {campaign_id}: {len(videos)} videos × {len(platforms)} platforms = {total_uploads} uploads")
            
            # Execute uploads for each video on each platform
            for video in videos:
                video_id = video['video_id']
                video_path = video['file_path']
                video_title = video.get('title', 'Untitled')
                
                for platform in platforms:
                    # Check if paused
                    if self._is_paused(campaign_id):
                        logger.info(f"Campaign {campaign_id} paused, waiting...")
                        self._wait_while_paused(campaign_id)
                    
                    # Check if cancelled
                    if self._is_cancelled(campaign_id):
                        logger.info(f"Campaign {campaign_id} cancelled")
                        self._complete_campaign(campaign_id, success=False)
                        return
                    
                    logger.info(f"Campaign {campaign_id}: Uploading {video_title} to {platform}")
                    
                    # Get campaign-specific metadata for this upload
                    metadata = self.campaign_manager.get_campaign_metadata_for_upload(
                        campaign_id, video_id
                    )
                    
                    # Add video path to metadata
                    metadata['video_path'] = video_path
                    metadata['platform'] = platform
                    
                    # Execute upload via callback
                    try:
                        success = self.upload_callback(video_path, platform, metadata)
                        
                        if success:
                            completed += 1
                            logger.info(f"Campaign {campaign_id}: Upload successful ({completed}/{total_uploads})")
                        else:
                            failed += 1
                            logger.warning(f"Campaign {campaign_id}: Upload failed ({failed} failures)")
                        
                        # Record upload result
                        self.campaign_manager.record_campaign_upload(
                            campaign_id=campaign_id,
                            video_id=video_id,
                            platform=platform,
                            success=success,
                            metadata_used=metadata,
                            error_message=None if success else "Upload failed"
                        )
                        
                    except Exception as e:
                        failed += 1
                        logger.error(f"Campaign {campaign_id}: Upload error: {e}")
                        
                        # Record failed upload
                        self.campaign_manager.record_campaign_upload(
                            campaign_id=campaign_id,
                            video_id=video_id,
                            platform=platform,
                            success=False,
                            metadata_used=metadata,
                            error_message=str(e)
                        )
                    
                    # Apply delay between uploads (except for last upload)
                    if delay_seconds > 0 and (completed + failed) < total_uploads:
                        logger.info(f"Campaign {campaign_id}: Waiting {delay_seconds}s before next upload...")
                        time.sleep(delay_seconds)
            
            # Campaign completed
            logger.info(f"Campaign {campaign_id} completed: {completed} successful, {failed} failed")
            self._complete_campaign(campaign_id, success=(failed == 0))
            
        except Exception as e:
            logger.error(f"Error executing campaign {campaign_id}: {e}")
            self._complete_campaign(campaign_id, success=False)
    
    def pause_campaign(self, campaign_id: str) -> bool:
        """
        Pause an active campaign.
        
        Args:
            campaign_id: Campaign identifier
            
        Returns:
            True if paused successfully
        """
        with self._lock:
            if campaign_id not in self.active_campaigns:
                logger.warning(f"Campaign {campaign_id} is not active")
                return False
            
            self.active_campaigns[campaign_id]['paused'] = True
        
        self.campaign_manager.update_campaign_status(campaign_id, 'paused')
        logger.info(f"Campaign {campaign_id} paused")
        return True
    
    def resume_campaign(self, campaign_id: str) -> bool:
        """
        Resume a paused campaign.
        
        Args:
            campaign_id: Campaign identifier
            
        Returns:
            True if resumed successfully
        """
        with self._lock:
            if campaign_id not in self.active_campaigns:
                logger.warning(f"Campaign {campaign_id} is not active")
                return False
            
            self.active_campaigns[campaign_id]['paused'] = False
        
        self.campaign_manager.update_campaign_status(campaign_id, 'active')
        logger.info(f"Campaign {campaign_id} resumed")
        return True
    
    def cancel_campaign(self, campaign_id: str) -> bool:
        """
        Cancel an active campaign.
        
        Args:
            campaign_id: Campaign identifier
            
        Returns:
            True if cancelled successfully
        """
        with self._lock:
            if campaign_id not in self.active_campaigns:
                logger.warning(f"Campaign {campaign_id} is not active")
                return False
            
            # Mark as cancelled (will be picked up by execution thread)
            self.active_campaigns[campaign_id]['status'] = 'cancelled'
        
        logger.info(f"Campaign {campaign_id} cancellation requested")
        return True
    
    def get_campaign_status(self, campaign_id: str) -> Optional[Dict]:
        """
        Get current execution status of a campaign.
        
        Args:
            campaign_id: Campaign identifier
            
        Returns:
            Status dictionary or None if not active
        """
        with self._lock:
            if campaign_id not in self.active_campaigns:
                return None
            
            state = self.active_campaigns[campaign_id].copy()
            # Don't include thread object in status
            state.pop('thread', None)
            return state
    
    def _is_paused(self, campaign_id: str) -> bool:
        """Check if campaign is paused."""
        with self._lock:
            if campaign_id in self.active_campaigns:
                return self.active_campaigns[campaign_id].get('paused', False)
            return False
    
    def _is_cancelled(self, campaign_id: str) -> bool:
        """Check if campaign is cancelled."""
        with self._lock:
            if campaign_id in self.active_campaigns:
                return self.active_campaigns[campaign_id].get('status') == 'cancelled'
            return False
    
    def _wait_while_paused(self, campaign_id: str, check_interval: int = 5):
        """Wait while campaign is paused."""
        while self._is_paused(campaign_id) and not self._is_cancelled(campaign_id):
            time.sleep(check_interval)
    
    def _complete_campaign(self, campaign_id: str, success: bool):
        """Mark campaign as completed and cleanup."""
        # Update campaign status
        new_status = 'completed' if success else 'paused'
        self.campaign_manager.update_campaign_status(campaign_id, new_status)
        
        # Remove from active campaigns
        with self._lock:
            if campaign_id in self.active_campaigns:
                del self.active_campaigns[campaign_id]
        
        logger.info(f"Campaign {campaign_id} marked as {new_status}")
    
    def list_active_campaigns(self) -> Dict[str, Dict]:
        """
        Get all currently active campaigns.
        
        Returns:
            Dictionary of campaign_id -> status
        """
        with self._lock:
            return {
                cid: {k: v for k, v in state.items() if k != 'thread'}
                for cid, state in self.active_campaigns.items()
            }


# Global scheduler instance
_campaign_scheduler_instance = None


def get_campaign_scheduler() -> CampaignScheduler:
    """Get or create the global campaign scheduler instance."""
    global _campaign_scheduler_instance
    if _campaign_scheduler_instance is None:
        _campaign_scheduler_instance = CampaignScheduler()
    return _campaign_scheduler_instance
