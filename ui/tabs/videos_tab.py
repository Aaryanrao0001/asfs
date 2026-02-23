"""
Videos Tab - Ultra-modern video registry and upload management interface.
Uber-style design with cards, smooth animations, and advanced features.
"""

import os
import logging
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox,
    QGroupBox, QMessageBox, QAbstractItemView, QFileDialog, QScrollArea,
    QLineEdit, QComboBox, QSpinBox, QDialog, QDialogButtonBox, QFrame
)
from PySide6.QtCore import Signal, Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QPixmap, QIcon, QColor
import subprocess

from database import VideoRegistry
from ..workers.upload_worker import UploadWorker, BulkUploadWorker

logger = logging.getLogger(__name__)


class ToastNotification(QWidget):
    """Toast notification widget that appears at the top of the screen."""
    
    def __init__(self, message: str, notification_type: str = "info", parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        # Setup UI
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Icon based on type
        icons = {
            "success": "✅",
            "error": "❌",
            "warning": "⚠️",
            "info": "ℹ️"
        }
        icon_label = QLabel(icons.get(notification_type, "ℹ️"))
        icon_label.setStyleSheet("font-size: 20px;")
        layout.addWidget(icon_label)
        
        # Message
        message_label = QLabel(message)
        message_label.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: 500;")
        message_label.setWordWrap(False)
        layout.addWidget(message_label)
        
        # Styling based on type
        colors = {
            "success": "background-color: rgba(16, 185, 129, 0.95);",
            "error": "background-color: rgba(239, 68, 68, 0.95);",
            "warning": "background-color: rgba(245, 158, 11, 0.95);",
            "info": "background-color: rgba(59, 130, 246, 0.95);"
        }
        
        self.setStyleSheet(f"""
            QWidget {{
                {colors.get(notification_type, colors["info"])}
                border-radius: 12px;
                padding: 5px;
            }}
        """)
        
        # Auto-hide timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.fade_out)
        self.timer.setSingleShot(True)
        
        # Fade out animation
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(500)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_animation.finished.connect(self.close)
    
    def show_notification(self, duration: int = 3000):
        """Show the notification for a specified duration."""
        self.show()
        self.timer.start(duration)
    
    def fade_out(self):
        """Fade out the notification."""
        self.fade_animation.start()



class EditTitleDialog(QDialog):
    """Dialog for editing video title."""
    
    def __init__(self, current_title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Video Title")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Title input
        layout.addWidget(QLabel("New Title:"))
        self.title_input = QLineEdit(current_title)
        self.title_input.selectAll()
        layout.addWidget(self.title_input)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_title(self) -> str:
        """Get the entered title."""
        return self.title_input.text().strip()


class VideoDetailsDialog(QDialog):
    """Dialog showing detailed video information."""
    
    def __init__(self, video: dict, video_registry: VideoRegistry, parent=None):
        super().__init__(parent)
        self.video = video
        self.video_registry = video_registry
        self.setWindowTitle(f"Video Details - {video.get('title', 'Untitled')}")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Title section
        title_label = QLabel(self.video.get('title', 'Untitled'))
        title_label.setProperty("heading", True)
        layout.addWidget(title_label)
        
        # Info grid
        info_group = QGroupBox("📋 Video Information")
        info_layout = QVBoxLayout(info_group)
        
        # Video ID
        id_layout = QHBoxLayout()
        id_layout.addWidget(QLabel("ID:"))
        id_value = QLabel(self.video.get('id', 'N/A'))
        id_value.setProperty("subheading", True)
        id_layout.addWidget(id_value)
        id_layout.addStretch()
        info_layout.addLayout(id_layout)
        
        # File path
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("File Path:"))
        path_value = QLabel(self.video.get('file_path', 'N/A'))
        path_value.setProperty("subheading", True)
        path_value.setWordWrap(True)
        path_layout.addWidget(path_value)
        path_layout.addStretch()
        info_layout.addLayout(path_layout)
        
        # Duration
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("Duration:"))
        duration = self.video.get('duration', 0)
        if duration > 0:
            mins, secs = divmod(int(duration), 60)
            duration_text = f"{mins}:{secs:02d} ({duration:.1f}s)"
        else:
            duration_text = "N/A"
        duration_value = QLabel(duration_text)
        duration_value.setProperty("subheading", True)
        duration_layout.addWidget(duration_value)
        duration_layout.addStretch()
        info_layout.addLayout(duration_layout)
        
        # File size
        file_size_layout = QHBoxLayout()
        file_size_layout.addWidget(QLabel("File Size:"))
        file_size = self.video_registry.get_file_size(self.video.get('id'))
        size_text = self.format_file_size(file_size) if file_size else "N/A"
        size_value = QLabel(size_text)
        size_value.setProperty("subheading", True)
        file_size_layout.addWidget(size_value)
        file_size_layout.addStretch()
        info_layout.addLayout(file_size_layout)
        
        # Created at
        created_layout = QHBoxLayout()
        created_layout.addWidget(QLabel("Added:"))
        created_value = QLabel(self.video.get('created_at', 'N/A'))
        created_value.setProperty("subheading", True)
        created_layout.addWidget(created_value)
        created_layout.addStretch()
        info_layout.addLayout(created_layout)
        
        # Duplicate allowed
        dup_layout = QHBoxLayout()
        dup_layout.addWidget(QLabel("Duplicate Uploads:"))
        dup_allowed = "Enabled" if self.video.get('duplicate_allowed') else "Disabled"
        dup_value = QLabel(dup_allowed)
        dup_value.setProperty("subheading", True)
        dup_layout.addWidget(dup_value)
        dup_layout.addStretch()
        info_layout.addLayout(dup_layout)
        
        layout.addWidget(info_group)
        
        # Upload status section
        uploads_group = QGroupBox("📤 Upload Status")
        uploads_layout = QVBoxLayout(uploads_group)
        
        uploads = self.video.get('uploads', {})
        
        if not uploads:
            no_uploads_label = QLabel("No uploads yet")
            no_uploads_label.setProperty("subheading", True)
            uploads_layout.addWidget(no_uploads_label)
        else:
            for platform in ['Instagram', 'TikTok', 'YouTube']:
                upload_info = uploads.get(platform)
                
                platform_layout = QHBoxLayout()
                platform_label = QLabel(f"{platform}:")
                platform_label.setMinimumWidth(100)
                platform_layout.addWidget(platform_label)
                
                if upload_info:
                    status = upload_info.get('status', 'UNKNOWN')
                    status_label = QLabel(self.get_status_text(status))
                    
                    if status == 'SUCCESS':
                        status_label.setProperty("status", "success")
                    elif status in ['FAILED', 'FAILED_FINAL']:
                        status_label.setProperty("status", "error")
                    elif status == 'IN_PROGRESS':
                        status_label.setProperty("status", "running")
                    
                    platform_layout.addWidget(status_label)
                    
                    # Post ID if available
                    if upload_info.get('post_id'):
                        post_id_label = QLabel(f"Post ID: {upload_info['post_id']}")
                        post_id_label.setProperty("subheading", True)
                        platform_layout.addWidget(post_id_label)
                else:
                    not_uploaded = QLabel("Not uploaded")
                    not_uploaded.setProperty("subheading", True)
                    platform_layout.addWidget(not_uploaded)
                
                platform_layout.addStretch()
                uploads_layout.addLayout(platform_layout)
        
        layout.addWidget(uploads_group)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
    
    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes is None:
            return "N/A"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    def get_status_text(self, status: str) -> str:
        """Get human-readable status text."""
        status_map = {
            'SUCCESS': '✅ Uploaded',
            'FAILED': '❌ Failed',
            'FAILED_FINAL': '❌ Failed (Final)',
            'IN_PROGRESS': '⏳ In Progress',
            'BLOCKED': '🚫 Blocked',
            'RATE_LIMITED': '🔄 Rate Limited',
            'PENDING': '⏸️ Pending'
        }
        return status_map.get(status, f'❓ {status}')


class VideosTab(QWidget):
    """Tab for video registry and upload management with ultra-modern UI."""
    
    # Signals
    upload_requested = Signal(str, str)  # video_id, platform
    refresh_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_registry = VideoRegistry()
        self.upload_workers = []  # Track active upload workers
        self.metadata_callback = None  # Callback to get metadata settings from parent
        self.upload_settings_callback = None  # Callback to get upload settings from parent
        self.current_filter = ""  # Current search filter
        self.current_sort_column = 0  # Current sort column
        self.current_sort_order = Qt.AscendingOrder  # Current sort order
        self.notifications = []  # Track active notifications
        self.init_ui()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_videos)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds
    
    def show_notification(self, message: str, notification_type: str = "info", duration: int = 3000):
        """
        Show a toast notification.
        
        Args:
            message: Notification message
            notification_type: Type of notification (success, error, warning, info)
            duration: How long to show the notification in milliseconds
        """
        # Create notification
        notification = ToastNotification(message, notification_type, self)
        
        # Position at top center of the tab
        notification.adjustSize()
        parent_rect = self.rect()
        x = parent_rect.center().x() - notification.width() // 2
        y = 20  # 20px from top
        notification.move(x, y)
        
        # Show notification
        notification.show_notification(duration)
        
        # Track notification
        self.notifications.append(notification)
        
        # Clean up after it closes
        QTimer.singleShot(duration + 600, lambda: self._cleanup_notification(notification))
    
    def _cleanup_notification(self, notification):
        """Remove notification from tracking list."""
        if notification in self.notifications:
            self.notifications.remove(notification)
    
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
        """Initialize the ultra-modern user interface."""
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
        layout.setSpacing(20)
        layout.setContentsMargins(32, 32, 32, 32)
        
        # Header section with title and stats
        header_layout = QHBoxLayout()
        
        # Title
        title = QLabel("Video Library")
        title.setProperty("heading", True)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Stats
        self.stats_label = QLabel("0 videos")
        self.stats_label.setProperty("subheading", True)
        header_layout.addWidget(self.stats_label)
        
        layout.addLayout(header_layout)
        
        # Search and filter bar
        search_filter_layout = QHBoxLayout()
        search_filter_layout.setSpacing(12)
        
        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Search videos by name...")
        self.search_box.textChanged.connect(self.on_search_changed)
        self.search_box.setMinimumHeight(42)
        search_filter_layout.addWidget(self.search_box, stretch=3)
        
        # Sort dropdown
        sort_label = QLabel("Sort by:")
        search_filter_layout.addWidget(sort_label)
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "Title (A-Z)", "Title (Z-A)",
            "Duration (Short)", "Duration (Long)",
            "Date Added (Newest)", "Date Added (Oldest)"
        ])
        self.sort_combo.currentIndexChanged.connect(self.on_sort_changed)
        self.sort_combo.setMinimumHeight(42)
        search_filter_layout.addWidget(self.sort_combo, stretch=2)
        
        layout.addLayout(search_filter_layout)
        
        # Action buttons row
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(12)
        
        self.add_videos_btn = QPushButton("➕ Add Videos")
        self.add_videos_btn.clicked.connect(self.add_videos_from_folder)
        self.add_videos_btn.setMinimumHeight(46)
        actions_layout.addWidget(self.add_videos_btn)
        
        self.delete_selected_btn = QPushButton("🗑️ Delete Selected")
        self.delete_selected_btn.setProperty("danger", True)
        self.delete_selected_btn.clicked.connect(self.delete_selected_videos)
        self.delete_selected_btn.setEnabled(False)
        self.delete_selected_btn.setMinimumHeight(46)
        actions_layout.addWidget(self.delete_selected_btn)
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setProperty("secondary", True)
        self.refresh_btn.clicked.connect(self.refresh_videos)
        self.refresh_btn.setMinimumHeight(46)
        actions_layout.addWidget(self.refresh_btn)
        
        self.upload_all_btn = QPushButton("⬆️ Upload All Pending")
        self.upload_all_btn.clicked.connect(self.upload_all_pending)
        self.upload_all_btn.setMinimumHeight(46)
        actions_layout.addWidget(self.upload_all_btn)
        
        actions_layout.addStretch()
        
        layout.addLayout(actions_layout)
        
        # Bulk Upload Configuration
        bulk_config_group = QGroupBox("⚙️ Bulk Upload Settings")
        bulk_config_layout = QHBoxLayout(bulk_config_group)
        bulk_config_layout.setSpacing(16)
        
        bulk_config_layout.addWidget(QLabel("Delay between uploads:"))
        
        self.upload_delay_spinbox = QSpinBox()
        self.upload_delay_spinbox.setMinimum(0)
        self.upload_delay_spinbox.setMaximum(3600)
        self.upload_delay_spinbox.setValue(60)  # Default 60 seconds
        self.upload_delay_spinbox.setSuffix(" seconds")
        self.upload_delay_spinbox.setToolTip(
            "Time to wait between each upload in bulk upload mode (0 for no delay)"
        )
        self.upload_delay_spinbox.setMinimumHeight(42)
        bulk_config_layout.addWidget(self.upload_delay_spinbox)
        
        bulk_config_layout.addStretch()
        
        delay_hint = QLabel("⏱️ Use delay to prevent rate limiting")
        delay_hint.setProperty("subheading", True)
        bulk_config_layout.addWidget(delay_hint)
        
        layout.addWidget(bulk_config_group)
        
        # Videos table with modern styling
        videos_group = QGroupBox("📹 Your Videos")
        videos_layout = QVBoxLayout(videos_group)
        
        # Create table
        self.videos_table = QTableWidget()
        self.videos_table.setColumnCount(9)
        self.videos_table.setHorizontalHeaderLabels([
            "Title", "Duration", "Size", "Instagram", "TikTok", "YouTube", 
            "Allow Duplicates", "Actions", "File Path"
        ])
        
        # Configure table
        self.videos_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.videos_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.videos_table.setSelectionMode(QAbstractItemView.MultiSelection)
        self.videos_table.setAlternatingRowColors(True)
        self.videos_table.verticalHeader().setVisible(False)
        self.videos_table.setShowGrid(False)
        self.videos_table.setMinimumHeight(400)
        
        # Set column widths
        header = self.videos_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Title
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Duration
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Size
        header.setSectionResizeMode(3, QHeaderView.Fixed)  # Instagram
        self.videos_table.setColumnWidth(3, 80)
        header.setSectionResizeMode(4, QHeaderView.Fixed)  # TikTok
        self.videos_table.setColumnWidth(4, 80)
        header.setSectionResizeMode(5, QHeaderView.Fixed)  # YouTube
        self.videos_table.setColumnWidth(5, 80)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Duplicates
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Actions
        header.setSectionResizeMode(8, QHeaderView.Stretch)  # File Path
        
        # Connect selection change
        self.videos_table.itemSelectionChanged.connect(self.on_selection_changed)
        
        videos_layout.addWidget(self.videos_table)
        
        layout.addWidget(videos_group)
        
        # Set scroll area content
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        
        # Initial load
        self.refresh_videos()
    
    def on_search_changed(self, text):
        """Handle search text change."""
        self.current_filter = text.lower()
        self.refresh_videos()
    
    def on_sort_changed(self, index):
        """Handle sort option change."""
        self.refresh_videos()
    
    def on_selection_changed(self):
        """Handle selection change in table."""
        selected_rows = self.videos_table.selectionModel().selectedRows()
        self.delete_selected_btn.setEnabled(len(selected_rows) > 0)
    
    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes is None:
            return "N/A"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
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
            
            # Show summary with notification
            if added_count > 0:
                self.show_notification(
                    f"Added {added_count} video(s)",
                    "success" if skipped_count == 0 else "warning"
                )
            
            if skipped_count > 0 and added_count == 0:
                self.show_notification(
                    f"Skipped {skipped_count} video(s) - already exist or error",
                    "warning"
                )
            
            # Refresh table
            self.refresh_videos()
    
    def delete_selected_videos(self):
        """Delete selected videos from registry."""
        # Get selected rows using table's selection model
        selected_rows = self.videos_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        # Get video IDs from selected rows
        video_ids = []
        for row_index in selected_rows:
            row = row_index.row()
            title_item = self.videos_table.item(row, 0)  # Title column
            if title_item:
                video_id = title_item.data(Qt.UserRole)
                if video_id:
                    video_ids.append(video_id)
        
        if not video_ids:
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete {len(video_ids)} video(s) from the registry?\n\n"
            "⚠️ This will remove the video records and upload history.\n"
            "The actual video files will NOT be deleted from disk.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            deleted_count = 0
            failed_count = 0
            
            for video_id in video_ids:
                if self.video_registry.delete_video(video_id):
                    deleted_count += 1
                else:
                    failed_count += 1
            
            # Show result with notification
            if deleted_count > 0:
                self.show_notification(
                    f"Deleted {deleted_count} video(s)",
                    "success" if failed_count == 0 else "warning"
                )
            
            if failed_count > 0 and deleted_count == 0:
                self.show_notification(
                    f"Failed to delete {failed_count} video(s)",
                    "error"
                )
            
            # Clear selection and refresh
            self.videos_table.clearSelection()
            self.refresh_videos()
    
    def edit_video_title(self, video_id: str, current_title: str):
        """Edit video title."""
        dialog = EditTitleDialog(current_title, self)
        
        if dialog.exec() == QDialog.Accepted:
            new_title = dialog.get_title()
            
            if new_title and new_title != current_title:
                if self.video_registry.update_video_title(video_id, new_title):
                    self.show_notification(f"Title updated: {new_title}", "success")
                    self.refresh_videos()
                else:
                    self.show_notification(f"Failed to update title", "error")
    
    def show_video_details(self, video: dict):
        """Show detailed video information dialog."""
        dialog = VideoDetailsDialog(video, self.video_registry, self)
        dialog.exec()
    
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
                timeout=30
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
            return "✅"  # Green checkmark
        elif status in ["FAILED", "FAILED_FINAL"]:
            return "❌"  # Red X
        elif status == "IN_PROGRESS":
            return "⏳"  # Hourglass
        elif status == "BLOCKED":
            return "🚫"  # Prohibited
        elif status == "RATE_LIMITED":
            return "🔄"  # Loop (retry)
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
        """Refresh the videos table from the database with filtering and sorting."""
        try:
            videos = self.video_registry.get_all_videos()
            
            # Apply search filter
            if self.current_filter:
                videos = [
                    v for v in videos 
                    if self.current_filter in v.get('title', '').lower()
                ]
            
            # Apply sorting
            sort_option = self.sort_combo.currentIndex()
            if sort_option == 0:  # Title A-Z
                videos.sort(key=lambda v: v.get('title', '').lower())
            elif sort_option == 1:  # Title Z-A
                videos.sort(key=lambda v: v.get('title', '').lower(), reverse=True)
            elif sort_option == 2:  # Duration Short
                videos.sort(key=lambda v: v.get('duration', 0))
            elif sort_option == 3:  # Duration Long
                videos.sort(key=lambda v: v.get('duration', 0), reverse=True)
            elif sort_option == 4:  # Date Newest
                videos.sort(key=lambda v: v.get('created_at', ''), reverse=True)
            elif sort_option == 5:  # Date Oldest
                videos.sort(key=lambda v: v.get('created_at', ''))
            
            # Update stats
            self.stats_label.setText(f"{len(videos)} video{'s' if len(videos) != 1 else ''}")
            
            # Update table
            self.videos_table.setRowCount(len(videos))
            
            for row, video in enumerate(videos):
                video_id = video.get('id', '')
                
                # Title (with video_id stored as user data)
                title = video.get('title', 'Untitled')
                title_item = QTableWidgetItem(title)
                title_item.setData(Qt.UserRole, video_id)  # Store video_id
                self.videos_table.setItem(row, 0, title_item)
                
                # Duration
                duration = video.get('duration', 0)
                if duration > 0:
                    mins, secs = divmod(int(duration), 60)
                    duration_text = f"{mins}:{secs:02d}"
                else:
                    duration_text = "N/A"
                duration_item = QTableWidgetItem(duration_text)
                duration_item.setTextAlignment(Qt.AlignCenter)
                self.videos_table.setItem(row, 1, duration_item)
                
                # File size
                file_size = self.video_registry.get_file_size(video_id)
                size_text = self.format_file_size(file_size)
                size_item = QTableWidgetItem(size_text)
                size_item.setTextAlignment(Qt.AlignCenter)
                self.videos_table.setItem(row, 2, size_item)
                
                # Platform statuses
                uploads = video.get('uploads', {})
                
                # Instagram
                instagram_info = uploads.get('Instagram')
                instagram_icon = self.get_status_icon(instagram_info.get('status') if instagram_info else None)
                instagram_item = QTableWidgetItem(instagram_icon)
                instagram_item.setTextAlignment(Qt.AlignCenter)
                instagram_item.setToolTip(self.get_status_tooltip(instagram_info))
                self.videos_table.setItem(row, 3, instagram_item)
                
                # TikTok
                tiktok_info = uploads.get('TikTok')
                tiktok_icon = self.get_status_icon(tiktok_info.get('status') if tiktok_info else None)
                tiktok_item = QTableWidgetItem(tiktok_icon)
                tiktok_item.setTextAlignment(Qt.AlignCenter)
                tiktok_item.setToolTip(self.get_status_tooltip(tiktok_info))
                self.videos_table.setItem(row, 4, tiktok_item)
                
                # YouTube
                youtube_info = uploads.get('YouTube')
                youtube_icon = self.get_status_icon(youtube_info.get('status') if youtube_info else None)
                youtube_item = QTableWidgetItem(youtube_icon)
                youtube_item.setTextAlignment(Qt.AlignCenter)
                youtube_item.setToolTip(self.get_status_tooltip(youtube_info))
                self.videos_table.setItem(row, 5, youtube_item)
                
                # Duplicate toggle
                duplicate_allowed = bool(video.get('duplicate_allowed', 0))
                duplicate_widget = QWidget()
                duplicate_layout = QHBoxLayout(duplicate_widget)
                duplicate_layout.setContentsMargins(0, 0, 0, 0)
                duplicate_layout.setAlignment(Qt.AlignCenter)
                
                duplicate_checkbox = QCheckBox()
                duplicate_checkbox.setChecked(duplicate_allowed)
                duplicate_checkbox.stateChanged.connect(
                    lambda state, vid=video_id: self.toggle_duplicate_allowed(vid, state == Qt.Checked)
                )
                duplicate_layout.addWidget(duplicate_checkbox)
                
                self.videos_table.setCellWidget(row, 6, duplicate_widget)
                
                # Actions (Upload + Edit + Delete buttons)
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(4, 4, 4, 4)
                actions_layout.setSpacing(4)
                
                # View details button
                details_btn = QPushButton("ℹ️")
                details_btn.setMaximumWidth(36)
                details_btn.setToolTip("View Details")
                details_btn.clicked.connect(
                    lambda checked, v=video: self.show_video_details(v)
                )
                actions_layout.addWidget(details_btn)
                
                # Edit title button
                edit_btn = QPushButton("✏️")
                edit_btn.setMaximumWidth(36)
                edit_btn.setToolTip("Edit Title")
                edit_btn.clicked.connect(
                    lambda checked, vid=video_id, t=title: self.edit_video_title(vid, t)
                )
                actions_layout.addWidget(edit_btn)
                
                # Instagram upload button
                instagram_btn = QPushButton("📷")
                instagram_btn.setMaximumWidth(36)
                instagram_btn.setToolTip("Upload to Instagram")
                instagram_btn.clicked.connect(
                    lambda checked, vid=video_id: self.upload_to_platform(vid, "Instagram")
                )
                actions_layout.addWidget(instagram_btn)
                
                # TikTok upload button
                tiktok_btn = QPushButton("🎵")
                tiktok_btn.setMaximumWidth(36)
                tiktok_btn.setToolTip("Upload to TikTok")
                tiktok_btn.clicked.connect(
                    lambda checked, vid=video_id: self.upload_to_platform(vid, "TikTok")
                )
                actions_layout.addWidget(tiktok_btn)
                
                # YouTube upload button
                youtube_btn = QPushButton("▶️")
                youtube_btn.setMaximumWidth(36)
                youtube_btn.setToolTip("Upload to YouTube")
                youtube_btn.clicked.connect(
                    lambda checked, vid=video_id: self.upload_to_platform(vid, "YouTube")
                )
                actions_layout.addWidget(youtube_btn)
                
                # Delete button
                delete_btn = QPushButton("🗑️")
                delete_btn.setMaximumWidth(36)
                delete_btn.setProperty("danger", True)
                delete_btn.setToolTip("Delete Video")
                delete_btn.clicked.connect(
                    lambda checked, vid=video_id: self.delete_single_video(vid)
                )
                actions_layout.addWidget(delete_btn)
                
                self.videos_table.setCellWidget(row, 7, actions_widget)
                
                # File Path
                file_path = video.get('file_path', '')
                file_path_item = QTableWidgetItem(file_path)
                file_path_item.setToolTip(file_path)
                self.videos_table.setItem(row, 8, file_path_item)
            
            logger.debug(f"Refreshed videos table: {len(videos)} videos")
            
        except Exception as e:
            logger.error(f"Failed to refresh videos: {e}")
            QMessageBox.warning(self, "Refresh Error", f"Failed to refresh videos:\n{e}")
    
    def delete_single_video(self, video_id: str):
        """Delete a single video."""
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete this video from the registry?\n\n"
            "⚠️ This will remove the video record and upload history.\n"
            "The actual video file will NOT be deleted from disk.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.video_registry.delete_video(video_id):
                self.show_notification("Video deleted successfully", "success")
                self.refresh_videos()
            else:
                self.show_notification("Failed to delete video", "error")

    
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
                        logo_path=metadata_settings.get("logo_path", ""),
                        hashtag_mode=metadata_settings.get("hashtag_mode", "append")
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
                f"✅ Video {video_id} uploaded to {platform} successfully!"
            )
        else:
            QMessageBox.warning(
                self,
                "Upload Failed",
                f"❌ Failed to upload {video_id} to {platform}. Check logs for details."
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
            f"✅ Uploaded {successful} videos successfully\n❌ {failed} failed"
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
