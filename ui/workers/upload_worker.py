"""Worker thread for video uploads."""

import logging
from PySide6.QtCore import QThread, Signal

from pipeline import run_upload_stage

logger = logging.getLogger(__name__)


class UploadWorker(QThread):
    """Worker thread for executing video uploads without blocking UI."""
    
    # Signals
    upload_started = Signal(str, str)  # video_id, platform
    upload_finished = Signal(str, str, bool)  # video_id, platform, success
    upload_error = Signal(str, str, str)  # video_id, platform, error_message
    
    def __init__(self, video_id: str, platform: str, metadata: dict = None):
        """
        Initialize upload worker.
        
        Args:
            video_id: Video identifier
            platform: Platform name
            metadata: Optional upload metadata
        """
        super().__init__()
        self.video_id = video_id
        self.platform = platform
        self.metadata = metadata or {}
    
    def run(self):
        """Execute the upload in background thread."""
        try:
            self.upload_started.emit(self.video_id, self.platform)
            logger.info(f"Starting upload: {self.video_id} to {self.platform}")
            
            # Execute upload
            success = run_upload_stage(self.video_id, self.platform, self.metadata)
            
            # Emit completion signal
            self.upload_finished.emit(self.video_id, self.platform, success)
            logger.info(f"Upload {'succeeded' if success else 'failed'}: {self.video_id} to {self.platform}")
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Upload error: {self.video_id} to {self.platform} - {error_msg}")
            self.upload_error.emit(self.video_id, self.platform, error_msg)


class BulkUploadWorker(QThread):
    """Worker thread for bulk video uploads."""
    
    # Signals
    upload_started = Signal(str, str)  # video_id, platform
    upload_finished = Signal(str, str, bool)  # video_id, platform, success
    all_uploads_finished = Signal(int, int)  # successful_count, failed_count
    
    def __init__(self, upload_tasks: list):
        """
        Initialize bulk upload worker.
        
        Args:
            upload_tasks: List of tuples (video_id, platform, metadata)
        """
        super().__init__()
        self.upload_tasks = upload_tasks
    
    def run(self):
        """Execute all uploads sequentially in background thread."""
        successful = 0
        failed = 0
        
        for video_id, platform, metadata in self.upload_tasks:
            try:
                self.upload_started.emit(video_id, platform)
                logger.info(f"Bulk upload: {video_id} to {platform}")
                
                success = run_upload_stage(video_id, platform, metadata)
                
                self.upload_finished.emit(video_id, platform, success)
                
                if success:
                    successful += 1
                else:
                    failed += 1
                    
            except Exception as e:
                logger.error(f"Bulk upload error: {video_id} to {platform} - {e}")
                self.upload_finished.emit(video_id, platform, False)
                failed += 1
        
        # Emit final summary
        self.all_uploads_finished.emit(successful, failed)
        logger.info(f"Bulk upload complete: {successful} successful, {failed} failed")
