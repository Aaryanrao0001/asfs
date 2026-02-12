"""
Bulk video upload scheduler with configurable delays.

This scheduler allows uploading multiple videos to multiple platforms
with configurable delays between uploads. It supports pause/cancel
operations and provides progress tracking.
"""

import logging
import time
from typing import List, Dict, Callable, Optional
from PySide6.QtCore import QThread, Signal

logger = logging.getLogger(__name__)


class BulkUploadScheduler(QThread):
    """
    Bulk video upload scheduler.
    
    Features:
    - Upload N videos in sequence
    - Configurable delay between uploads
    - Per-platform selection
    - Progress tracking
    - Cancel/pause support
    
    Usage:
        scheduler = BulkUploadScheduler(
            video_ids=['v1', 'v2'],
            platforms=['Instagram', 'TikTok'],
            delay_seconds=60,
            upload_callback=my_upload_function
        )
        scheduler.upload_started.connect(on_upload_started)
        scheduler.all_finished.connect(on_all_finished)
        scheduler.start()
    """
    
    # Signals
    upload_started = Signal(str, str)  # video_id, platform
    upload_finished = Signal(str, str, bool)  # video_id, platform, success
    all_finished = Signal(int, int)  # success_count, fail_count
    progress_update = Signal(int, int)  # current, total
    
    def __init__(
        self,
        video_ids: List[str],
        platforms: List[str],
        delay_seconds: int = 0,
        upload_callback: Optional[Callable] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Initialize bulk upload scheduler.
        
        Args:
            video_ids: List of video IDs to upload
            platforms: List of platform names (e.g., ['Instagram', 'TikTok', 'YouTube'])
            delay_seconds: Delay in seconds between uploads (default: 0)
            upload_callback: Callback function(video_id, platform, metadata) -> bool
            metadata: Optional metadata dict to pass to upload callback
        """
        super().__init__()
        self.video_ids = video_ids
        self.platforms = platforms
        self.delay_seconds = delay_seconds
        self.upload_callback = upload_callback
        self.metadata = metadata or {}
        self.cancelled = False
        self.paused = False
    
    def run(self):
        """Execute bulk uploads."""
        total_uploads = len(self.video_ids) * len(self.platforms)
        current = 0
        success_count = 0
        fail_count = 0
        
        logger.info(f"Starting bulk upload: {len(self.video_ids)} videos x {len(self.platforms)} platforms = {total_uploads} total uploads")
        
        for video_id in self.video_ids:
            if self.cancelled:
                logger.info("Bulk upload cancelled by user")
                break
            
            for platform in self.platforms:
                if self.cancelled:
                    break
                
                # Wait while paused
                while self.paused and not self.cancelled:
                    time.sleep(0.5)
                
                if self.cancelled:
                    break
                
                current += 1
                self.progress_update.emit(current, total_uploads)
                
                logger.info(f"[{current}/{total_uploads}] Uploading {video_id} to {platform}")
                self.upload_started.emit(video_id, platform)
                
                # Execute upload via callback
                success = False
                try:
                    if self.upload_callback:
                        success = self.upload_callback(video_id, platform, self.metadata)
                        if success:
                            success_count += 1
                            logger.info(f"[{current}/{total_uploads}] Upload succeeded: {video_id} to {platform}")
                        else:
                            fail_count += 1
                            logger.warning(f"[{current}/{total_uploads}] Upload failed: {video_id} to {platform}")
                    else:
                        logger.error("No upload callback provided")
                        fail_count += 1
                except Exception as e:
                    logger.error(f"Upload error: {video_id} to {platform} - {e}")
                    fail_count += 1
                    success = False
                
                self.upload_finished.emit(video_id, platform, success)
                
                # Delay before next upload (except last one)
                if current < total_uploads and self.delay_seconds > 0 and not self.cancelled:
                    logger.info(f"Waiting {self.delay_seconds}s before next upload...")
                    
                    # Sleep in small increments to be responsive to cancel/pause
                    elapsed = 0
                    while elapsed < self.delay_seconds and not self.cancelled:
                        if self.paused:
                            # Don't count time while paused
                            time.sleep(0.5)
                            continue
                        
                        sleep_time = min(0.5, self.delay_seconds - elapsed)
                        time.sleep(sleep_time)
                        elapsed += sleep_time
        
        logger.info(f"Bulk upload complete: {success_count} succeeded, {fail_count} failed")
        self.all_finished.emit(success_count, fail_count)
    
    def cancel(self):
        """Cancel bulk upload."""
        logger.info("Cancelling bulk upload...")
        self.cancelled = True
    
    def pause(self):
        """Pause bulk upload."""
        logger.info("Pausing bulk upload...")
        self.paused = True
    
    def resume(self):
        """Resume bulk upload."""
        logger.info("Resuming bulk upload...")
        self.paused = False
