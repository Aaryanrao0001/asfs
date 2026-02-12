"""
Auto-scheduler service for background video uploads.

Manages scheduled uploads with configurable time gaps between uploads.
Runs as a background service and uploads videos from the registry.
"""

import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Optional, Callable
from pathlib import Path

from database import VideoRegistry

logger = logging.getLogger(__name__)


class UploadScheduler:
    """
    Background scheduler for automatic video uploads.
    
    Features:
    - Configurable time gaps between uploads
    - Supports all three platforms (Instagram, TikTok, YouTube)
    - Runs continuously in background thread
    - Respects duplicate upload settings
    - Applies metadata and preprocessing before upload
    """
    
    def __init__(self):
        """Initialize the upload scheduler."""
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.video_registry = VideoRegistry()
        
        # Scheduler configuration
        self.upload_gap_seconds = 3600  # Default: 1 hour
        self.platforms = ["Instagram", "TikTok", "YouTube"]
        
        # Callback for upload execution
        self.upload_callback: Optional[Callable] = None
        
        # Last upload timestamp
        self.last_upload_time: Optional[datetime] = None
    
    def configure(
        self,
        upload_gap_hours: int = 1,
        upload_gap_minutes: int = 0,
        platforms: list = None
    ):
        """
        Configure scheduler settings.
        
        Args:
            upload_gap_hours: Hours between uploads
            upload_gap_minutes: Minutes between uploads
            platforms: List of platform names to upload to
        """
        self.upload_gap_seconds = (upload_gap_hours * 3600) + (upload_gap_minutes * 60)
        
        if platforms:
            self.platforms = platforms
        
        logger.info(
            f"Scheduler configured: gap={upload_gap_hours}h {upload_gap_minutes}m, "
            f"platforms={self.platforms}"
        )
    
    def set_upload_callback(self, callback: Callable):
        """
        Set callback function for executing uploads.
        
        Args:
            callback: Function with signature: callback(video_id, platform, metadata) -> bool
        """
        self.upload_callback = callback
    
    def start(self):
        """Start the scheduler in a background thread."""
        if self.running:
            logger.warning("Scheduler already running")
            return
        
        if not self.upload_callback:
            logger.error("Cannot start scheduler: no upload callback set")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info("Upload scheduler started")
    
    def stop(self):
        """Stop the scheduler."""
        if not self.running:
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        
        logger.info("Upload scheduler stopped")
    
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self.running
    
    def _run_loop(self):
        """Main scheduler loop (runs in background thread)."""
        logger.info("Scheduler loop started")
        
        while self.running:
            try:
                # Check if enough time has passed since last upload
                if self._should_upload():
                    # Find next video to upload
                    upload_task = self._find_next_upload_task()
                    
                    if upload_task:
                        video_id, platform, metadata = upload_task
                        
                        logger.info(f"Scheduler: uploading {video_id} to {platform}")
                        
                        # Execute upload via callback
                        try:
                            success = self.upload_callback(video_id, platform, metadata)
                            
                            if success:
                                logger.info(f"Scheduled upload successful: {video_id} to {platform}")
                                self.last_upload_time = datetime.now()
                            else:
                                logger.warning(f"Scheduled upload failed: {video_id} to {platform}")
                        except Exception as e:
                            logger.error(f"Error in scheduled upload: {e}")
                    else:
                        logger.debug("No pending uploads found")
                
                # Sleep for a short interval before checking again
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)
        
        logger.info("Scheduler loop ended")
    
    def _should_upload(self) -> bool:
        """
        Check if enough time has passed to perform another upload.
        
        Returns:
            True if upload should be attempted
        """
        if self.last_upload_time is None:
            # First upload
            return True
        
        elapsed = (datetime.now() - self.last_upload_time).total_seconds()
        return elapsed >= self.upload_gap_seconds
    
    def _find_next_upload_task(self) -> Optional[tuple]:
        """
        Find the next video that needs to be uploaded.
        
        Returns:
            Tuple of (video_id, platform, metadata) or None if no uploads pending
        """
        try:
            videos = self.video_registry.get_all_videos()
            
            for video in videos:
                video_id = video['id']
                uploads = video.get('uploads', {})
                
                # Try each platform
                for platform in self.platforms:
                    # Check if not already successfully uploaded
                    if platform not in uploads or uploads[platform].get('status') != 'SUCCESS':
                        # Check if upload is allowed (respects duplicate settings)
                        can_upload, reason = self.video_registry.can_upload(video_id, platform)
                        
                        if can_upload:
                            # Found a pending upload
                            metadata = {
                                'file_path': video.get('file_path'),
                                'title': video.get('title'),
                                'duration': video.get('duration')
                            }
                            return (video_id, platform, metadata)
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding next upload task: {e}")
            return None
    
    def get_status(self) -> dict:
        """
        Get current scheduler status.
        
        Returns:
            Dictionary with status information
        """
        next_upload_time = None
        if self.last_upload_time:
            next_upload_time = self.last_upload_time + timedelta(seconds=self.upload_gap_seconds)
        
        return {
            "running": self.running,
            "upload_gap_seconds": self.upload_gap_seconds,
            "platforms": self.platforms,
            "last_upload_time": self.last_upload_time.isoformat() if self.last_upload_time else None,
            "next_upload_time": next_upload_time.isoformat() if next_upload_time else None
        }


# Global scheduler instance
_scheduler_instance = None


def get_scheduler() -> UploadScheduler:
    """Get or create the global scheduler instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = UploadScheduler()
    return _scheduler_instance
