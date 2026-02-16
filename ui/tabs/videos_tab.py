"""
Videos Tab - Video registry and upload management interface.
"""

import os
import logging
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox,
    QGroupBox, QMessageBox, QAbstractItemView, QFileDialog, QScrollArea
)
from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtGui import QPixmap, QIcon
import subprocess

from database import VideoRegistry
from ..workers.upload_worker import UploadWorker, BulkUploadWorker

logger = logging.getLogger(__name__)


class VideosTab(QWidget):
    """Tab for video registry and upload management."""
    
    # Signals
    upload_requested = Signal(str, str)  # video_id, platform
    refresh_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_registry = VideoRegistry()
        self.upload_workers = []  # Track active upload workers
        self.metadata_callback = None  # Callback to get metadata settings from parent
        self.upload_settings_callback = None  # Callback to get upload settings from parent
        self.init_ui()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_videos)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds
    
    def set_metadata_callback(self, callback):
        """
        Set callback to get metadata settings from parent window.
        
        Args:
            callback: Function that returns metadata settings dict
        """
        self.metadata_callback = callback
    
    def set_upload_settings_callback(self, callback):
        """
        Set callback to get upload settings from parent window.
        
        Args:
            callback: Function that returns upload settings dict
        """
        self.upload_settings_callback = callback
    
    def init_ui(self):
        """Initialize the user interface."""
        # Create main layout with scroll area
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QScrollArea.NoFrame)
        
        # Create content widget
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Title
        title = QLabel("Video Registry & Upload Management")
        title.setProperty("heading", True)
        layout.addWidget(title)
        
        # Control buttons
        controls_h_layout = QHBoxLayout()
        
        self.add_videos_btn = QPushButton("➕ Add Videos")
        self.add_videos_btn.clicked.connect(self.add_videos_from_folder)
        controls_h_layout.addWidget(self.add_videos_btn)
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setProperty("secondary", True)
        self.refresh_btn.clicked.connect(self.refresh_videos)
        controls_h_layout.addWidget(self.refresh_btn)
        
        self.upload_all_btn = QPushButton("⬆ Upload All Pending")
        self.upload_all_btn.clicked.connect(self.upload_all_pending)
        controls_h_layout.addWidget(self.upload_all_btn)
        
        controls_h_layout.addStretch()
        
        layout.addLayout(controls_h_layout)
        
        # Bulk Upload Configuration (NEW)
        bulk_config_group = QGroupBox("Bulk Upload Settings")
        bulk_config_layout = QHBoxLayout(bulk_config_group)
        
        bulk_config_layout.addWidget(QLabel("Delay between uploads:"))
        
        from PySide6.QtWidgets import QSpinBox
        self.upload_delay_spinbox = QSpinBox()
        self.upload_delay_spinbox.setMinimum(0)
        self.upload_delay_spinbox.setMaximum(3600)
        self.upload_delay_spinbox.setValue(60)  # Default 60 seconds
        self.upload_delay_spinbox.setSuffix(" seconds")
        self.upload_delay_spinbox.setToolTip(
            "Time to wait between each upload in bulk upload mode (0 for no delay)"
        )
        bulk_config_layout.addWidget(self.upload_delay_spinbox)
        
        bulk_config_layout.addStretch()
        
        delay_hint = QLabel("Use delay to prevent rate limiting and spread uploads over time")
        delay_hint.setProperty("subheading", True)
        bulk_config_layout.addWidget(delay_hint)
        
        layout.addWidget(bulk_config_group)
        
        # Videos table
        videos_group = QGroupBox("Videos")
        videos_layout = QVBoxLayout(videos_group)
        
        # Create table
        self.videos_table = QTableWidget()
        self.videos_table.setColumnCount(8)
        self.videos_table.setHorizontalHeaderLabels([
            "Title", "Duration", "Instagram", "TikTok", "YouTube", 
            "Allow Duplicates", "Actions", "File Path"
        ])
        
        # Configure table
        self.videos_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.videos_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.videos_table.setAlternatingRowColors(True)
        
        # Set column widths
        header = self.videos_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Title
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Duration
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Instagram
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # TikTok
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # YouTube
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Duplicates
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Actions
        header.setSectionResizeMode(7, QHeaderView.Stretch)  # File Path
        
        videos_layout.addWidget(self.videos_table)
        
        layout.addWidget(videos_group)
        
        # Set scroll area content
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        
        # Initial load
        self.refresh_videos()
    
    def add_videos_from_folder(self):
        """Add multiple videos from any folder to the registry."""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Video Files (*.mp4 *.mov *.avi *.mkv *.webm)")
        file_dialog.setWindowTitle("Select Videos to Add")
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            
            if not selected_files:
                return
            
            # Add each video to registry
            added_count = 0
            skipped_count = 0
            
            for video_path in selected_files:
                try:
                    # Get video duration using ffprobe
                    duration = self._get_video_duration(video_path)
                    
                    # Generate video ID from filename
                    video_id = Path(video_path).stem
                    
                    # Register video
                    # Note: Checksum calculation is skipped for performance reasons.
                    # This means duplicate files won't be detected based on content,
                    # only by video_id (filename). For large video libraries where
                    # content-based deduplication is needed, set calculate_checksum=True.
                    success = self.video_registry.register_video(
                        video_id=video_id,
                        file_path=video_path,
                        title=video_id,
                        duration=duration,
                        duplicate_allowed=False,
                        calculate_checksum=False  # Skip checksum for speed
                    )
                    
                    if success:
                        added_count += 1
                        logger.info(f"Added video to registry: {video_id}")
                    else:
                        skipped_count += 1
                        logger.warning(f"Video already exists: {video_id}")
                        
                except Exception as e:
                    logger.error(f"Failed to add video {video_path}: {e}")
                    skipped_count += 1
            
            # Show summary
            message = f"Added {added_count} video(s)"
            if skipped_count > 0:
                message += f"\nSkipped {skipped_count} (already exist or error)"
            
            QMessageBox.information(self, "Videos Added", message)
            
            # Refresh table
            self.refresh_videos()
    
    def _get_video_duration(self, video_path: str) -> float:
        """
        Get video duration using ffprobe.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Duration in seconds, or 0.0 if ffprobe is not available
        """
        try:
            # Check if ffprobe is available
            import shutil
            if not shutil.which('ffprobe'):
                logger.warning("ffprobe not found - cannot determine video duration")
                return 0.0
            
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                video_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30  # Increased timeout for large files
            )
            
            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())
            else:
                logger.warning(f"Could not get duration for {video_path}: {result.stderr}")
                return 0.0
                
        except FileNotFoundError:
            logger.error("ffprobe not found in system PATH - please install FFmpeg")
            return 0.0
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout getting duration for {video_path}")
            return 0.0
        except Exception as e:
            logger.error(f"Error getting video duration: {e}")
            return 0.0
    
    def get_status_icon(self, status: str) -> str:
        """
        Get status icon for upload status.
        
        Args:
            status: Upload status
            
        Returns:
            Unicode emoji representing the status
        """
        if status == "SUCCESS":
            return "✔"  # Checkmark
        elif status in ["FAILED", "FAILED_FINAL"]:
            return "✖"  # X mark
        elif status == "IN_PROGRESS":
            return "⏳"  # Hourglass
        elif status == "BLOCKED":
            return "❌"  # Prohibited
        elif status == "RATE_LIMITED":
            return "🔁"  # Loop (retry)
        else:
            return "⚪"  # Empty (not uploaded)
    
    def get_status_tooltip(self, upload_info: dict) -> str:
        """
        Get tooltip text for upload status.
        
        Args:
            upload_info: Upload information dictionary
            
        Returns:
            Tooltip text
        """
        if not upload_info:
            return "Not uploaded"
        
        status = upload_info.get('status', 'UNKNOWN')
        timestamp = upload_info.get('timestamp', 'N/A')
        error = upload_info.get('error', '')
        post_id = upload_info.get('post_id', '')
        retry_count = upload_info.get('retry_count', 0)
        
        tooltip = f"Status: {status}\nTimestamp: {timestamp}"
        
        if post_id:
            tooltip += f"\nPost ID: {post_id}"
        
        if retry_count > 0:
            tooltip += f"\nRetries: {retry_count}"
        
        if error:
            tooltip += f"\nError: {error}"
        
        return tooltip
    
    def refresh_videos(self):
        """Refresh the videos table from the database."""
        try:
            videos = self.video_registry.get_all_videos()
            
            # Update table
            self.videos_table.setRowCount(len(videos))
            
            for row, video in enumerate(videos):
                # Title
                title_item = QTableWidgetItem(video.get('title', 'Untitled'))
                self.videos_table.setItem(row, 0, title_item)
                
                # Duration
                duration = video.get('duration', 0)
                duration_text = f"{duration:.1f}s" if duration else "N/A"
                duration_item = QTableWidgetItem(duration_text)
                self.videos_table.setItem(row, 1, duration_item)
                
                # Platform statuses
                uploads = video.get('uploads', {})
                
                # Instagram
                instagram_info = uploads.get('Instagram')
                instagram_icon = self.get_status_icon(instagram_info.get('status') if instagram_info else None)
                instagram_item = QTableWidgetItem(instagram_icon)
                instagram_item.setTextAlignment(Qt.AlignCenter)
                instagram_item.setToolTip(self.get_status_tooltip(instagram_info))
                self.videos_table.setItem(row, 2, instagram_item)
                
                # TikTok
                tiktok_info = uploads.get('TikTok')
                tiktok_icon = self.get_status_icon(tiktok_info.get('status') if tiktok_info else None)
                tiktok_item = QTableWidgetItem(tiktok_icon)
                tiktok_item.setTextAlignment(Qt.AlignCenter)
                tiktok_item.setToolTip(self.get_status_tooltip(tiktok_info))
                self.videos_table.setItem(row, 3, tiktok_item)
                
                # YouTube
                youtube_info = uploads.get('YouTube')
                youtube_icon = self.get_status_icon(youtube_info.get('status') if youtube_info else None)
                youtube_item = QTableWidgetItem(youtube_icon)
                youtube_item.setTextAlignment(Qt.AlignCenter)
                youtube_item.setToolTip(self.get_status_tooltip(youtube_info))
                self.videos_table.setItem(row, 4, youtube_item)
                
                # Duplicate toggle
                duplicate_allowed = bool(video.get('duplicate_allowed', 0))
                duplicate_widget = QWidget()
                duplicate_layout = QHBoxLayout(duplicate_widget)
                duplicate_layout.setContentsMargins(0, 0, 0, 0)
                duplicate_layout.setAlignment(Qt.AlignCenter)
                
                duplicate_checkbox = QCheckBox()
                duplicate_checkbox.setChecked(duplicate_allowed)
                duplicate_checkbox.stateChanged.connect(
                    lambda state, vid=video['id']: self.toggle_duplicate_allowed(vid, state == Qt.Checked)
                )
                duplicate_layout.addWidget(duplicate_checkbox)
                
                self.videos_table.setCellWidget(row, 5, duplicate_widget)
                
                # Actions (Upload buttons)
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(4, 4, 4, 4)
                actions_layout.setSpacing(4)
                
                # Instagram upload button
                instagram_btn = QPushButton("📷")
                instagram_btn.setMaximumWidth(40)
                instagram_btn.setToolTip("Upload to Instagram")
                instagram_btn.clicked.connect(
                    lambda checked, vid=video['id']: self.upload_to_platform(vid, "Instagram")
                )
                actions_layout.addWidget(instagram_btn)
                
                # TikTok upload button
                tiktok_btn = QPushButton("🎵")
                tiktok_btn.setMaximumWidth(40)
                tiktok_btn.setToolTip("Upload to TikTok")
                tiktok_btn.clicked.connect(
                    lambda checked, vid=video['id']: self.upload_to_platform(vid, "TikTok")
                )
                actions_layout.addWidget(tiktok_btn)
                
                # YouTube upload button
                youtube_btn = QPushButton("▶")
                youtube_btn.setMaximumWidth(40)
                youtube_btn.setToolTip("Upload to YouTube")
                youtube_btn.clicked.connect(
                    lambda checked, vid=video['id']: self.upload_to_platform(vid, "YouTube")
                )
                actions_layout.addWidget(youtube_btn)
                
                self.videos_table.setCellWidget(row, 6, actions_widget)
                
                # File Path
                file_path = video.get('file_path', '')
                file_path_item = QTableWidgetItem(file_path)
                file_path_item.setToolTip(file_path)
                self.videos_table.setItem(row, 7, file_path_item)
            
            logger.debug(f"Refreshed videos table: {len(videos)} videos")
            
        except Exception as e:
            logger.error(f"Failed to refresh videos: {e}")
            QMessageBox.warning(self, "Refresh Error", f"Failed to refresh videos:\n{e}")
    
    def toggle_duplicate_allowed(self, video_id: str, allowed: bool):
        """
        Toggle duplicate upload permission for a video.
        
        Args:
            video_id: Video identifier
            allowed: Whether to allow duplicates
        """
        success = self.video_registry.set_duplicate_allowed(video_id, allowed)
        
        if success:
            logger.info(f"Duplicate allowed set to {allowed} for {video_id}")
            self.refresh_videos()
        else:
            QMessageBox.warning(
                self, 
                "Update Failed", 
                f"Failed to update duplicate setting for {video_id}"
            )
    
    def upload_to_platform(self, video_id: str, platform: str):
        """
        Upload a video to a specific platform using background worker.
        
        Args:
            video_id: Video identifier
            platform: Platform name
        """
        # Check if upload is allowed
        can_upload, reason = self.video_registry.can_upload(video_id, platform)
        
        if not can_upload:
            # Show blocking dialog
            reply = QMessageBox.question(
                self,
                "Upload Blocked",
                f"{reason}\n\nDo you want to enable duplicate uploads for this video and try again?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Enable duplicate uploads and retry
                self.video_registry.set_duplicate_allowed(video_id, True)
                self.refresh_videos()
                # Don't actually upload yet - user can click button again
                QMessageBox.information(
                    self,
                    "Duplicates Enabled",
                    "Duplicate uploads enabled. Click the upload button again to proceed."
                )
            
            return
        
        # Confirm upload
        reply = QMessageBox.question(
            self,
            "Confirm Upload",
            f"Upload video {video_id} to {platform}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Get metadata settings from parent window if available
            metadata = {}
            if self.metadata_callback:
                try:
                    metadata_settings = self.metadata_callback()
                    
                    # Resolve metadata using the metadata resolver
                    from metadata import MetadataConfig
                    from metadata.resolver import resolve_metadata
                    
                    config = MetadataConfig.from_ui_values(
                        mode=metadata_settings.get("mode", "uniform"),
                        title_input=metadata_settings.get("title", ""),
                        description_input=metadata_settings.get("description", ""),
                        caption_input=metadata_settings.get("caption", ""),
                        tags_input=metadata_settings.get("tags", ""),
                        hashtag_prefix=metadata_settings.get("hashtag_prefix", True),
                        hook_phrase=metadata_settings.get("hook_phrase", ""),
                        hook_position=metadata_settings.get("hook_position", "Top Left"),
                        logo_path=metadata_settings.get("logo_path", "")
                    )
                    
                    metadata = resolve_metadata(config)
                    logger.info(f"Applied metadata settings to upload: {metadata}")
                    
                except Exception as e:
                    logger.error(f"Error getting metadata settings: {e}")
            
            # Execute upload in background worker thread
            worker = UploadWorker(video_id, platform, metadata)
            worker.upload_started.connect(self.on_upload_started)
            worker.upload_finished.connect(self.on_upload_finished)
            worker.upload_error.connect(self.on_upload_error)
            
            # Keep reference to prevent garbage collection
            self.upload_workers.append(worker)
            
            # Start worker
            worker.start()
            logger.info(f"Started upload worker: {video_id} to {platform}")
    
    def on_upload_started(self, video_id: str, platform: str):
        """Handle upload start."""
        logger.info(f"Upload started: {video_id} to {platform}")
        # Could show progress indicator here
    
    def on_upload_finished(self, video_id: str, platform: str, success: bool):
        """Handle upload completion."""
        # Clean up worker thread properly
        sender = self.sender()
        if sender in self.upload_workers:
            self.upload_workers.remove(sender)
            # Ensure thread is properly cleaned up
            if sender.isRunning():
                sender.quit()
                sender.wait()  # Wait for thread to finish
        
        # Show result
        if success:
            QMessageBox.information(
                self,
                "Upload Successful",
                f"Video {video_id} uploaded to {platform} successfully!"
            )
        else:
            QMessageBox.warning(
                self,
                "Upload Failed",
                f"Failed to upload {video_id} to {platform}. Check logs for details."
            )
        
        # Refresh to show updated status
        self.refresh_videos()
    
    def on_upload_error(self, video_id: str, platform: str, error_msg: str):
        """Handle upload error."""
        # Clean up worker
        sender = self.sender()
        if sender in self.upload_workers:
            self.upload_workers.remove(sender)
        
        QMessageBox.critical(
            self,
            "Upload Error",
            f"An error occurred uploading {video_id} to {platform}:\n{error_msg}"
        )
        
        # Refresh to show updated status
        self.refresh_videos()
    
    def upload_all_pending(self):
        """Upload all videos with pending uploads to selected platforms using background worker."""
        # Get selected platforms from upload settings
        selected_platforms = []
        if self.upload_settings_callback:
            try:
                upload_settings = self.upload_settings_callback()
                platforms_config = upload_settings.get("platforms", {})
                
                if platforms_config.get("instagram"):
                    selected_platforms.append("Instagram")
                if platforms_config.get("tiktok"):
                    selected_platforms.append("TikTok")
                if platforms_config.get("youtube"):
                    selected_platforms.append("YouTube")
            except Exception as e:
                logger.error(f"Error getting upload settings: {e}")
                # Fallback to all platforms if error
                selected_platforms = ["Instagram", "TikTok", "YouTube"]
        else:
            # Fallback to all platforms if no callback
            selected_platforms = ["Instagram", "TikTok", "YouTube"]
        
        if not selected_platforms:
            QMessageBox.warning(
                self,
                "No Platforms Selected",
                "Please select at least one platform in the Upload tab before uploading."
            )
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Bulk Upload",
            f"Upload all videos to selected platforms ({', '.join(selected_platforms)}) where they haven't been uploaded yet?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            videos = self.video_registry.get_all_videos()
            
            # Collect upload tasks for selected platforms only
            upload_tasks = []
            
            for video in videos:
                video_id = video['id']
                uploads = video.get('uploads', {})
                
                for platform in selected_platforms:
                    # Check if not already uploaded
                    if platform not in uploads or uploads[platform].get('status') != 'SUCCESS':
                        # Check if upload is allowed
                        can_upload, reason = self.video_registry.can_upload(video_id, platform)
                        
                        if can_upload:
                            upload_tasks.append((video_id, platform, {}))
            
            if not upload_tasks:
                QMessageBox.information(
                    self,
                    "No Uploads Needed",
                    f"All videos are already uploaded to the selected platforms ({', '.join(selected_platforms)})."
                )
                return
            
            # Get delay from UI
            delay_seconds = self.upload_delay_spinbox.value()
            
            # Execute bulk upload in background worker
            worker = BulkUploadWorker(upload_tasks, delay_seconds=delay_seconds)
            worker.upload_started.connect(self.on_bulk_upload_started)
            worker.upload_finished.connect(self.on_bulk_upload_progress)
            worker.all_uploads_finished.connect(self.on_bulk_upload_complete)
            
            # Keep reference
            self.upload_workers.append(worker)
            
            # Start worker
            worker.start()
            logger.info(f"Started bulk upload: {len(upload_tasks)} tasks to {selected_platforms}")
    
    def on_bulk_upload_started(self, video_id: str, platform: str):
        """Handle bulk upload task start."""
        logger.info(f"Bulk upload progress: {video_id} to {platform}")
    
    def on_bulk_upload_progress(self, video_id: str, platform: str, success: bool):
        """Handle individual upload completion in bulk operation."""
        # Refresh to show updated status
        self.refresh_videos()
    
    def on_bulk_upload_complete(self, successful: int, failed: int):
        """Handle bulk upload completion."""
        # Clean up worker thread properly
        sender = self.sender()
        if sender in self.upload_workers:
            self.upload_workers.remove(sender)
            # Ensure thread is properly cleaned up
            if sender.isRunning():
                sender.quit()
                sender.wait()  # Wait for thread to finish
        
        QMessageBox.information(
            self,
            "Bulk Upload Complete",
            f"Uploaded {successful} videos successfully\n{failed} failed"
        )
        
        self.refresh_videos()
    
    def closeEvent(self, event):
        """Clean up worker threads when tab is closed."""
        logger.info("Cleaning up upload workers...")
        for worker in self.upload_workers[:]:  # Copy list to avoid modification during iteration
            if worker.isRunning():
                logger.info(f"Waiting for worker thread to finish...")
                worker.quit()
                worker.wait(5000)  # Wait up to 5 seconds
                if worker.isRunning():
                    logger.warning("Worker thread did not finish in time")
        self.upload_workers.clear()
        event.accept()
