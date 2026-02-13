"""
Campaigns Tab - Campaign management and video assignment interface.
"""

import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox,
    QGroupBox, QMessageBox, QDialog, QLineEdit, QTextEdit,
    QSpinBox, QListWidget, QListWidgetItem, QComboBox,
    QScrollArea, QAbstractItemView
)
from PySide6.QtCore import Signal, Qt, QTimer

from database import CampaignManager, VideoRegistry

logger = logging.getLogger(__name__)


class CreateCampaignDialog(QDialog):
    """Dialog for creating a new campaign."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Campaign")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Campaign name
        layout.addWidget(QLabel("Campaign Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., Summer Promo 2024")
        layout.addWidget(self.name_input)
        
        # Campaign description
        layout.addWidget(QLabel("Description (optional):"))
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Brief description of the campaign...")
        self.description_input.setMaximumHeight(80)
        layout.addWidget(self.description_input)
        
        # Platform selection
        platforms_group = QGroupBox("Target Platforms")
        platforms_layout = QVBoxLayout(platforms_group)
        
        self.instagram_check = QCheckBox("Instagram")
        self.instagram_check.setChecked(True)
        platforms_layout.addWidget(self.instagram_check)
        
        self.tiktok_check = QCheckBox("TikTok")
        self.tiktok_check.setChecked(True)
        platforms_layout.addWidget(self.tiktok_check)
        
        self.youtube_check = QCheckBox("YouTube Shorts")
        self.youtube_check.setChecked(True)
        platforms_layout.addWidget(self.youtube_check)
        
        layout.addWidget(platforms_group)
        
        # Schedule settings
        schedule_group = QGroupBox("Schedule Settings")
        schedule_layout = QVBoxLayout(schedule_group)
        
        self.schedule_enabled_check = QCheckBox("Enable Automatic Scheduling")
        self.schedule_enabled_check.setChecked(False)
        schedule_layout.addWidget(self.schedule_enabled_check)
        
        gap_layout = QHBoxLayout()
        gap_layout.addWidget(QLabel("Upload Gap:"))
        
        self.gap_hours = QSpinBox()
        self.gap_hours.setMinimum(0)
        self.gap_hours.setMaximum(168)  # 1 week
        self.gap_hours.setValue(1)
        gap_layout.addWidget(self.gap_hours)
        gap_layout.addWidget(QLabel("hours"))
        
        self.gap_minutes = QSpinBox()
        self.gap_minutes.setMinimum(0)
        self.gap_minutes.setMaximum(59)
        self.gap_minutes.setValue(0)
        gap_layout.addWidget(self.gap_minutes)
        gap_layout.addWidget(QLabel("minutes"))
        
        gap_layout.addStretch()
        schedule_layout.addLayout(gap_layout)
        
        layout.addWidget(schedule_group)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        create_btn = QPushButton("Create Campaign")
        create_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(create_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def get_campaign_data(self):
        """Get campaign data from form."""
        platforms = []
        if self.instagram_check.isChecked():
            platforms.append("Instagram")
        if self.tiktok_check.isChecked():
            platforms.append("TikTok")
        if self.youtube_check.isChecked():
            platforms.append("YouTube")
        
        return {
            "name": self.name_input.text().strip(),
            "description": self.description_input.toPlainText().strip(),
            "platforms": platforms,
            "schedule_enabled": self.schedule_enabled_check.isChecked(),
            "schedule_gap_hours": self.gap_hours.value(),
            "schedule_gap_minutes": self.gap_minutes.value()
        }


class AddVideosToCampaignDialog(QDialog):
    """Dialog for adding videos to a campaign."""
    
    def __init__(self, campaign_id, campaign_name, parent=None):
        super().__init__(parent)
        self.campaign_id = campaign_id
        self.campaign_name = campaign_name
        self.video_registry = VideoRegistry()
        self.campaign_manager = CampaignManager()
        
        self.setWindowTitle(f"Add Videos to Campaign: {campaign_name}")
        self.setModal(True)
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        self.init_ui()
        self.load_available_videos()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Instructions
        instructions = QLabel(
            "Select videos to add to this campaign. You can set individual metadata "
            "for each video later."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Available videos list
        layout.addWidget(QLabel("Available Videos:"))
        self.videos_list = QListWidget()
        self.videos_list.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.videos_list)
        
        # Metadata section
        metadata_group = QGroupBox("Default Metadata for Selected Videos (optional)")
        metadata_layout = QVBoxLayout(metadata_group)
        
        metadata_layout.addWidget(QLabel("Title:"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Leave empty to use video's default title")
        metadata_layout.addWidget(self.title_input)
        
        metadata_layout.addWidget(QLabel("Caption:"))
        self.caption_input = QLineEdit()
        self.caption_input.setPlaceholderText("Campaign-specific caption")
        metadata_layout.addWidget(self.caption_input)
        
        metadata_layout.addWidget(QLabel("Hashtags:"))
        self.hashtags_input = QLineEdit()
        self.hashtags_input.setPlaceholderText("#campaign, #video, #content")
        metadata_layout.addWidget(self.hashtags_input)
        
        layout.addWidget(metadata_group)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        add_btn = QPushButton("Add Selected Videos")
        add_btn.clicked.connect(self.add_videos)
        buttons_layout.addWidget(add_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_available_videos(self):
        """Load available videos from registry."""
        self.videos_list.clear()
        
        # Get all registered videos
        all_videos = self.video_registry.list_videos()
        
        # Get videos already in this campaign
        campaign_videos = self.campaign_manager.get_campaign_videos(self.campaign_id)
        campaign_video_ids = {v['video_id'] for v in campaign_videos}
        
        # Filter out videos already in campaign
        for video in all_videos:
            video_id = video['id']
            if video_id not in campaign_video_ids:
                item = QListWidgetItem(f"{video['title']} ({video_id})")
                item.setData(Qt.UserRole, video_id)
                self.videos_list.addItem(item)
    
    def add_videos(self):
        """Add selected videos to campaign."""
        selected_items = self.videos_list.selectedItems()
        
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select at least one video.")
            return
        
        # Get metadata from form
        title = self.title_input.text().strip() or None
        caption = self.caption_input.text().strip() or None
        hashtags = self.hashtags_input.text().strip() or None
        
        # Add each selected video
        added_count = 0
        for item in selected_items:
            video_id = item.data(Qt.UserRole)
            success = self.campaign_manager.add_video_to_campaign(
                self.campaign_id,
                video_id,
                title=title,
                caption=caption,
                hashtags=hashtags
            )
            if success:
                added_count += 1
        
        if added_count > 0:
            QMessageBox.information(
                self,
                "Success",
                f"Added {added_count} video(s) to campaign."
            )
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "Failed",
                "Failed to add videos to campaign. They may already be in the campaign."
            )


class EditCampaignVideoDialog(QDialog):
    """Dialog for editing video metadata in a campaign."""
    
    def __init__(self, campaign_id, video_id, video_data, parent=None):
        super().__init__(parent)
        self.campaign_id = campaign_id
        self.video_id = video_id
        self.video_data = video_data
        
        self.setWindowTitle(f"Edit Video Metadata")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        layout.addWidget(QLabel(f"Video ID: {self.video_id}"))
        
        # Title
        layout.addWidget(QLabel("Title:"))
        self.title_input = QLineEdit()
        self.title_input.setText(self.video_data.get('title', ''))
        layout.addWidget(self.title_input)
        
        # Caption
        layout.addWidget(QLabel("Caption:"))
        self.caption_input = QTextEdit()
        self.caption_input.setPlainText(self.video_data.get('caption', ''))
        self.caption_input.setMaximumHeight(100)
        layout.addWidget(self.caption_input)
        
        # Hashtags
        layout.addWidget(QLabel("Hashtags:"))
        self.hashtags_input = QLineEdit()
        self.hashtags_input.setText(self.video_data.get('hashtags', ''))
        layout.addWidget(self.hashtags_input)
        
        # Upload order
        layout.addWidget(QLabel("Upload Order:"))
        self.order_input = QSpinBox()
        self.order_input.setMinimum(0)
        self.order_input.setMaximum(9999)
        self.order_input.setValue(self.video_data.get('upload_order', 0))
        layout.addWidget(self.order_input)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def get_metadata(self):
        """Get updated metadata from form."""
        return {
            "title": self.title_input.text().strip(),
            "caption": self.caption_input.toPlainText().strip(),
            "hashtags": self.hashtags_input.text().strip(),
            "upload_order": self.order_input.value()
        }


class CampaignsTab(QWidget):
    """Tab for campaign management."""
    
    # Signals
    campaign_created = Signal(int)  # campaign_id
    campaign_updated = Signal(int)  # campaign_id
    campaign_deleted = Signal(int)  # campaign_id
    start_campaign_scheduler = Signal()  # Request to start campaign scheduler
    stop_campaign_scheduler = Signal()  # Request to stop campaign scheduler
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.campaign_manager = CampaignManager()
        self.video_registry = VideoRegistry()
        self.selected_campaign_id = None
        self.scheduler_running = False
        self.init_ui()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_campaigns)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds
    
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
        title = QLabel("Campaign Management")
        title.setProperty("heading", True)
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel(
            "Create multiple independent campaigns with their own videos, schedules, "
            "and metadata. Each campaign can have different captions, hashtags, and titles."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Campaign controls
        controls_h_layout = QHBoxLayout()
        
        self.create_campaign_btn = QPushButton("➕ Create Campaign")
        self.create_campaign_btn.clicked.connect(self.create_campaign)
        controls_h_layout.addWidget(self.create_campaign_btn)
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setProperty("secondary", True)
        self.refresh_btn.clicked.connect(self.refresh_campaigns)
        controls_h_layout.addWidget(self.refresh_btn)
        
        # Scheduler control button
        self.scheduler_btn = QPushButton("▶️ Start Campaign Scheduler")
        self.scheduler_btn.clicked.connect(self.toggle_campaign_scheduler)
        controls_h_layout.addWidget(self.scheduler_btn)
        
        controls_h_layout.addStretch()
        
        layout.addLayout(controls_h_layout)
        
        # Campaigns list
        campaigns_group = QGroupBox("Campaigns")
        campaigns_layout = QVBoxLayout(campaigns_group)
        
        self.campaigns_table = QTableWidget()
        self.campaigns_table.setColumnCount(7)
        self.campaigns_table.setHorizontalHeaderLabels([
            "ID", "Name", "Platforms", "Videos", "Schedule", "Active", "Actions"
        ])
        self.campaigns_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.campaigns_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.campaigns_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.campaigns_table.itemSelectionChanged.connect(self.on_campaign_selected)
        campaigns_layout.addWidget(self.campaigns_table)
        
        layout.addWidget(campaigns_group)
        
        # Campaign videos section
        videos_group = QGroupBox("Campaign Videos")
        videos_layout = QVBoxLayout(videos_group)
        
        # Video controls
        video_controls = QHBoxLayout()
        
        self.add_videos_btn = QPushButton("➕ Add Videos")
        self.add_videos_btn.clicked.connect(self.add_videos_to_campaign)
        self.add_videos_btn.setEnabled(False)
        video_controls.addWidget(self.add_videos_btn)
        
        self.remove_video_btn = QPushButton("➖ Remove Selected")
        self.remove_video_btn.clicked.connect(self.remove_video_from_campaign)
        self.remove_video_btn.setEnabled(False)
        video_controls.addWidget(self.remove_video_btn)
        
        self.edit_video_btn = QPushButton("✏️ Edit Metadata")
        self.edit_video_btn.clicked.connect(self.edit_video_metadata)
        self.edit_video_btn.setEnabled(False)
        video_controls.addWidget(self.edit_video_btn)
        
        video_controls.addStretch()
        videos_layout.addLayout(video_controls)
        
        # Videos table
        self.videos_table = QTableWidget()
        self.videos_table.setColumnCount(6)
        self.videos_table.setHorizontalHeaderLabels([
            "Video ID", "Title", "Caption", "Hashtags", "Upload Order", "Added"
        ])
        self.videos_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.videos_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.videos_table.setEditTriggers(QTableWidget.NoEditTriggers)
        videos_layout.addWidget(self.videos_table)
        
        layout.addWidget(videos_group)
        
        # Set scroll area content
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        
        # Initial load
        self.refresh_campaigns()
    
    def create_campaign(self):
        """Open dialog to create a new campaign."""
        dialog = CreateCampaignDialog(self)
        
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_campaign_data()
            
            if not data["name"]:
                QMessageBox.warning(self, "Invalid Input", "Campaign name is required.")
                return
            
            if not data["platforms"]:
                QMessageBox.warning(self, "Invalid Input", "Select at least one platform.")
                return
            
            campaign_id = self.campaign_manager.create_campaign(
                name=data["name"],
                description=data["description"],
                platforms=data["platforms"],
                schedule_enabled=data["schedule_enabled"],
                schedule_gap_hours=data["schedule_gap_hours"],
                schedule_gap_minutes=data["schedule_gap_minutes"]
            )
            
            if campaign_id:
                QMessageBox.information(
                    self,
                    "Success",
                    f"Campaign '{data['name']}' created successfully!"
                )
                self.campaign_created.emit(campaign_id)
                self.refresh_campaigns()
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to create campaign. Campaign name may already exist."
                )
    
    def refresh_campaigns(self):
        """Refresh campaigns list."""
        campaigns = self.campaign_manager.list_campaigns()
        
        self.campaigns_table.setRowCount(len(campaigns))
        
        for row, campaign in enumerate(campaigns):
            campaign_id = campaign['id']
            
            # ID
            self.campaigns_table.setItem(row, 0, QTableWidgetItem(str(campaign_id)))
            
            # Name
            self.campaigns_table.setItem(row, 1, QTableWidgetItem(campaign['name']))
            
            # Platforms
            platforms_str = ", ".join(campaign['platforms'])
            self.campaigns_table.setItem(row, 2, QTableWidgetItem(platforms_str))
            
            # Video count
            videos = self.campaign_manager.get_campaign_videos(campaign_id)
            self.campaigns_table.setItem(row, 3, QTableWidgetItem(str(len(videos))))
            
            # Schedule
            if campaign['schedule_enabled']:
                schedule_str = f"{campaign['schedule_gap_hours']}h {campaign['schedule_gap_minutes']}m"
            else:
                schedule_str = "Disabled"
            self.campaigns_table.setItem(row, 4, QTableWidgetItem(schedule_str))
            
            # Active
            active_str = "Yes" if campaign['is_active'] else "No"
            self.campaigns_table.setItem(row, 5, QTableWidgetItem(active_str))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            
            delete_btn = QPushButton("Delete")
            delete_btn.setProperty("danger", True)
            delete_btn.clicked.connect(lambda checked, cid=campaign_id: self.delete_campaign(cid))
            actions_layout.addWidget(delete_btn)
            
            self.campaigns_table.setCellWidget(row, 6, actions_widget)
        
        # If a campaign was previously selected, try to reselect it
        if self.selected_campaign_id:
            self.refresh_campaign_videos()
    
    def on_campaign_selected(self):
        """Handle campaign selection."""
        selected_rows = self.campaigns_table.selectionModel().selectedRows()
        
        if selected_rows:
            row = selected_rows[0].row()
            campaign_id = int(self.campaigns_table.item(row, 0).text())
            self.selected_campaign_id = campaign_id
            
            # Enable video controls
            self.add_videos_btn.setEnabled(True)
            
            # Load campaign videos
            self.refresh_campaign_videos()
        else:
            self.selected_campaign_id = None
            self.add_videos_btn.setEnabled(False)
            self.remove_video_btn.setEnabled(False)
            self.edit_video_btn.setEnabled(False)
            self.videos_table.setRowCount(0)
    
    def refresh_campaign_videos(self):
        """Refresh videos for selected campaign."""
        if not self.selected_campaign_id:
            return
        
        videos = self.campaign_manager.get_campaign_videos(self.selected_campaign_id)
        
        self.videos_table.setRowCount(len(videos))
        
        for row, video in enumerate(videos):
            # Video ID
            self.videos_table.setItem(row, 0, QTableWidgetItem(video['video_id']))
            
            # Title
            self.videos_table.setItem(row, 1, QTableWidgetItem(video['title'] or ""))
            
            # Caption
            caption_text = video['caption'] or ""
            if len(caption_text) > 50:
                caption_text = caption_text[:47] + "..."
            self.videos_table.setItem(row, 2, QTableWidgetItem(caption_text))
            
            # Hashtags
            hashtags_text = video['hashtags'] or ""
            if len(hashtags_text) > 50:
                hashtags_text = hashtags_text[:47] + "..."
            self.videos_table.setItem(row, 3, QTableWidgetItem(hashtags_text))
            
            # Upload Order
            self.videos_table.setItem(row, 4, QTableWidgetItem(str(video['upload_order'])))
            
            # Added
            added_at = video['added_at'].split('T')[0] if 'T' in video['added_at'] else video['added_at']
            self.videos_table.setItem(row, 5, QTableWidgetItem(added_at))
        
        # Enable/disable buttons
        self.remove_video_btn.setEnabled(False)
        self.edit_video_btn.setEnabled(False)
        
        # Connect selection signal
        self.videos_table.itemSelectionChanged.connect(self.on_video_selected)
    
    def on_video_selected(self):
        """Handle video selection in campaign."""
        selected = len(self.videos_table.selectionModel().selectedRows()) > 0
        self.remove_video_btn.setEnabled(selected)
        self.edit_video_btn.setEnabled(selected)
    
    def add_videos_to_campaign(self):
        """Open dialog to add videos to campaign."""
        if not self.selected_campaign_id:
            return
        
        campaign = self.campaign_manager.get_campaign(self.selected_campaign_id)
        if not campaign:
            QMessageBox.warning(self, "Error", "Campaign not found.")
            return
        
        dialog = AddVideosToCampaignDialog(
            self.selected_campaign_id,
            campaign['name'],
            self
        )
        
        if dialog.exec() == QDialog.Accepted:
            self.refresh_campaign_videos()
    
    def remove_video_from_campaign(self):
        """Remove selected video from campaign."""
        if not self.selected_campaign_id:
            return
        
        selected_rows = self.videos_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        video_id = self.videos_table.item(row, 0).text()
        
        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Remove video {video_id} from this campaign?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success = self.campaign_manager.remove_video_from_campaign(
                self.selected_campaign_id,
                video_id
            )
            
            if success:
                QMessageBox.information(self, "Success", "Video removed from campaign.")
                self.refresh_campaign_videos()
            else:
                QMessageBox.critical(self, "Error", "Failed to remove video.")
    
    def edit_video_metadata(self):
        """Edit metadata for selected video in campaign."""
        if not self.selected_campaign_id:
            return
        
        selected_rows = self.videos_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        video_id = self.videos_table.item(row, 0).text()
        
        # Get current video data
        videos = self.campaign_manager.get_campaign_videos(self.selected_campaign_id)
        video_data = next((v for v in videos if v['video_id'] == video_id), None)
        
        if not video_data:
            QMessageBox.warning(self, "Error", "Video not found.")
            return
        
        dialog = EditCampaignVideoDialog(
            self.selected_campaign_id,
            video_id,
            video_data,
            self
        )
        
        if dialog.exec() == QDialog.Accepted:
            metadata = dialog.get_metadata()
            success = self.campaign_manager.update_campaign_video_metadata(
                self.selected_campaign_id,
                video_id,
                title=metadata['title'],
                caption=metadata['caption'],
                hashtags=metadata['hashtags'],
                upload_order=metadata['upload_order']
            )
            
            if success:
                QMessageBox.information(self, "Success", "Video metadata updated.")
                self.refresh_campaign_videos()
            else:
                QMessageBox.critical(self, "Error", "Failed to update metadata.")
    
    def delete_campaign(self, campaign_id: int):
        """Delete a campaign."""
        campaign = self.campaign_manager.get_campaign(campaign_id)
        if not campaign:
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Delete campaign '{campaign['name']}'?\n\nThis will remove all video assignments but won't delete the videos themselves.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success = self.campaign_manager.delete_campaign(campaign_id)
            
            if success:
                QMessageBox.information(self, "Success", "Campaign deleted.")
                self.campaign_deleted.emit(campaign_id)
                
                # Clear selection if deleted campaign was selected
                if self.selected_campaign_id == campaign_id:
                    self.selected_campaign_id = None
                    self.videos_table.setRowCount(0)
                    self.add_videos_btn.setEnabled(False)
                
                self.refresh_campaigns()
            else:
                QMessageBox.critical(self, "Error", "Failed to delete campaign.")
    
    def toggle_campaign_scheduler(self):
        """Toggle campaign scheduler on/off."""
        if self.scheduler_running:
            # Stop scheduler
            self.stop_campaign_scheduler.emit()
            self.scheduler_running = False
            self.scheduler_btn.setText("▶️ Start Campaign Scheduler")
            QMessageBox.information(
                self,
                "Scheduler Stopped",
                "Campaign scheduler has been stopped."
            )
        else:
            # Check if there are any active campaigns with scheduling enabled
            campaigns = self.campaign_manager.list_campaigns(active_only=True)
            scheduled_campaigns = [c for c in campaigns if c.get('schedule_enabled')]
            
            if not scheduled_campaigns:
                QMessageBox.warning(
                    self,
                    "No Scheduled Campaigns",
                    "No active campaigns have scheduling enabled.\n\n"
                    "Please create a campaign and enable automatic scheduling in the campaign settings."
                )
                return
            
            # Start scheduler
            self.start_campaign_scheduler.emit()
            self.scheduler_running = True
            self.scheduler_btn.setText("⏸️ Stop Campaign Scheduler")
            QMessageBox.information(
                self,
                "Scheduler Started",
                f"Campaign scheduler is now running for {len(scheduled_campaigns)} campaign(s)."
            )
    
    def set_scheduler_running(self, running: bool):
        """Update scheduler running state from parent."""
        self.scheduler_running = running
        if running:
            self.scheduler_btn.setText("⏸️ Stop Campaign Scheduler")
        else:
            self.scheduler_btn.setText("▶️ Start Campaign Scheduler")
