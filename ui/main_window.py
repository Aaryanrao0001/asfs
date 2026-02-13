"""
Main Window - Central window with tabs for ASFS application.
"""

import os
import json
import logging
from pathlib import Path
from PySide6.QtWidgets import QMainWindow, QTabWidget, QMessageBox
from PySide6.QtCore import Qt, QTimer

from .tabs.input_tab import InputTab
from .tabs.ai_tab import AITab
from .tabs.metadata_tab import MetadataTab
from .tabs.upload_tab import UploadTab
from .tabs.run_tab import RunTab
from .tabs.videos_tab import VideosTab
from .workers.pipeline_worker import PipelineWorker

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window with tabbed interface."""
    
    def __init__(self):
        super().__init__()
        self.batch_message_shown = False  # Track if batch message was shown
        self.init_ui()
        self.init_workers()
        self.load_settings()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("ASFS - Automated Short-Form Content System")
        self.setMinimumSize(900, 700)
        
        # Create tab widget
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        
        # Create tabs
        self.input_tab = InputTab()
        self.ai_tab = AITab()
        self.metadata_tab = MetadataTab()
        self.upload_tab = UploadTab()
        self.videos_tab = VideosTab()
        self.run_tab = RunTab()
        
        # Add tabs
        self.tabs.addTab(self.input_tab, "📹 Input Video")
        self.tabs.addTab(self.ai_tab, "🤖 AI / Model")
        self.tabs.addTab(self.metadata_tab, "📝 Metadata")
        self.tabs.addTab(self.upload_tab, "🚀 Upload")
        self.tabs.addTab(self.videos_tab, "🎬 Videos")
        self.tabs.addTab(self.run_tab, "▶️ Run & Monitor")
        
        self.setCentralWidget(self.tabs)
        
        # Connect signals
        self.connect_signals()
        
        # Set metadata callback for videos tab
        self.videos_tab.set_metadata_callback(lambda: self.metadata_tab.get_settings())
    
    def init_workers(self):
        """Initialize background workers."""
        self.pipeline_worker = PipelineWorker()
        self.pipeline_worker.log_message.connect(self.on_pipeline_log)
        self.pipeline_worker.progress_update.connect(self.on_pipeline_progress)
        self.pipeline_worker.finished.connect(self.on_pipeline_finished)
        self.pipeline_worker.error_occurred.connect(self.on_pipeline_error)
        
        # Initialize scheduler
        try:
            from scheduler.auto_scheduler import get_scheduler
            self.scheduler = get_scheduler()
            self.scheduler.set_upload_callback(self.execute_scheduled_upload)
            logger.info("Scheduler initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize scheduler: {e}")
            # Create a dummy scheduler that does nothing
            class DummyScheduler:
                def configure(self, **kwargs): pass
                def is_running(self): return False
                def start(self): logger.warning("Scheduler not available")
                def stop(self): pass
            self.scheduler = DummyScheduler()
    
    def connect_signals(self):
        """Connect all UI signals to handlers."""
        # Input tab
        self.input_tab.video_selected.connect(self.on_video_selected)
        self.input_tab.videos_selected.connect(self.on_videos_selected)
        self.input_tab.output_changed.connect(self.on_output_changed)
        self.input_tab.cache_changed.connect(self.on_cache_changed)
        
        # AI tab
        self.ai_tab.settings_changed.connect(self.on_ai_settings_changed)
        
        # Metadata tab
        self.metadata_tab.settings_changed.connect(self.on_metadata_settings_changed)
        
        # Upload tab
        self.upload_tab.settings_changed.connect(self.on_upload_settings_changed)
        self.upload_tab.start_scheduler_requested.connect(self.on_start_scheduler)
        self.upload_tab.stop_scheduler_requested.connect(self.on_stop_scheduler)
        
        # Run tab
        self.run_tab.run_clicked.connect(self.on_run_pipeline)
        self.run_tab.stop_clicked.connect(self.on_stop_pipeline)
        self.run_tab.clear_logs_clicked.connect(self.on_clear_logs)
    
    def on_video_selected(self, path: str):
        """Handle video selection."""
        logger.info(f"Video selected: {path}")
        self.save_settings()
    
    def on_videos_selected(self, paths: list):
        """Handle multiple videos selection."""
        logger.info(f"{len(paths)} videos selected")
        self.save_settings()
    
    def on_output_changed(self, path: str):
        """Handle output directory change."""
        logger.info(f"Output directory changed: {path}")
        self.save_settings()
    
    def on_cache_changed(self, use_cache: bool):
        """Handle cache setting change."""
        logger.info(f"Cache setting changed: {use_cache}")
        self.save_settings()
    
    def on_ai_settings_changed(self, settings: dict):
        """Handle AI settings change."""
        logger.debug(f"AI settings changed: {settings}")
        self.save_settings()
    
    def on_metadata_settings_changed(self, settings: dict):
        """Handle metadata settings change."""
        logger.debug(f"Metadata settings changed: {settings}")
        self.save_settings()
    
    def on_upload_settings_changed(self, settings: dict):
        """Handle upload settings change."""
        logger.debug(f"Upload settings changed: {settings}")
        self.save_settings()
        
        # Set environment variables for browser configuration
        # This ensures pipeline.py can access UI-configured browser settings
        if settings.get("brave_path"):
            os.environ["BRAVE_PATH"] = settings["brave_path"]
        if settings.get("user_data_dir"):
            os.environ["BRAVE_USER_DATA_DIR"] = settings["user_data_dir"]
        if settings.get("profile_directory"):
            os.environ["BRAVE_PROFILE_DIRECTORY"] = settings["profile_directory"]
        
        # Update scheduler configuration (but don't auto-start)
        upload_gap_hours = settings.get("upload_gap_hours", 1)
        upload_gap_minutes = settings.get("upload_gap_minutes", 0)
        
        # Get selected platforms
        platforms_config = settings.get("platforms", {})
        enabled_platforms = []
        if platforms_config.get("instagram"):
            enabled_platforms.append("Instagram")
        if platforms_config.get("tiktok"):
            enabled_platforms.append("TikTok")
        if platforms_config.get("youtube"):
            enabled_platforms.append("YouTube")
        
        # Configure scheduler (this does not start it)
        self.scheduler.configure(
            upload_gap_hours=upload_gap_hours,
            upload_gap_minutes=upload_gap_minutes,
            platforms=enabled_platforms
        )
    
    def on_start_scheduler(self):
        """Handle manual start scheduler request."""
        if not self.scheduler.is_running():
            # Get current upload settings
            settings = self.upload_tab.get_settings()
            upload_gap_hours = settings.get("upload_gap_hours", 1)
            upload_gap_minutes = settings.get("upload_gap_minutes", 0)
            
            # Get selected platforms
            platforms_config = settings.get("platforms", {})
            enabled_platforms = []
            if platforms_config.get("instagram"):
                enabled_platforms.append("Instagram")
            if platforms_config.get("tiktok"):
                enabled_platforms.append("TikTok")
            if platforms_config.get("youtube"):
                enabled_platforms.append("YouTube")
            
            if not enabled_platforms:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self,
                    "No Platforms Selected",
                    "Please select at least one platform before starting the scheduler."
                )
                return
            
            # Configure and start scheduler
            self.scheduler.configure(
                upload_gap_hours=upload_gap_hours,
                upload_gap_minutes=upload_gap_minutes,
                platforms=enabled_platforms
            )
            self.scheduler.start()
            logger.info("Scheduler started manually by user")
            
            # Update UI
            self.upload_tab.update_scheduler_status(True)
    
    def on_stop_scheduler(self):
        """Handle manual stop scheduler request."""
        if self.scheduler.is_running():
            self.scheduler.stop()
            logger.info("Scheduler stopped manually by user")
            
            # Update UI
            self.upload_tab.update_scheduler_status(False)
    
    def execute_scheduled_upload(self, video_id: str, platform: str, metadata: dict) -> bool:
        """
        Execute a scheduled upload (called by scheduler).
        
        Args:
            video_id: Video ID to upload
            platform: Platform name
            metadata: Video metadata
            
        Returns:
            True if upload succeeded, False otherwise
        """
        try:
            # Get current metadata settings from UI
            metadata_settings = self.metadata_tab.get_settings()
            
            # Get upload settings for browser configuration
            upload_settings = self.upload_tab.get_settings()
            
            # Set environment variables for browser configuration
            # This ensures pipeline.py uses the UI-configured browser settings
            if upload_settings.get("brave_path"):
                os.environ["BRAVE_PATH"] = upload_settings["brave_path"]
            if upload_settings.get("user_data_dir"):
                os.environ["BRAVE_USER_DATA_DIR"] = upload_settings["user_data_dir"]
            if upload_settings.get("profile_directory"):
                os.environ["BRAVE_PROFILE_DIRECTORY"] = upload_settings["profile_directory"]
            
            # Merge with video metadata
            from metadata import MetadataConfig
            from metadata.resolver import resolve_metadata
            
            # Create metadata config from UI settings
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
            
            # Resolve metadata for this upload
            resolved = resolve_metadata(config)
            
            # Execute upload
            from pipeline import run_upload_stage
            success = run_upload_stage(video_id, platform, resolved)
            
            return success
            
        except Exception as e:
            logger.error(f"Error in scheduled upload: {e}")
            return False
    
    def on_run_pipeline(self):
        """Handle run pipeline request."""
        # Validate inputs
        video_path = self.input_tab.get_video_path()
        selected_videos = self.input_tab.get_selected_videos()
        
        # Check if we have any videos selected
        if not selected_videos:
            QMessageBox.warning(
                self,
                "Invalid Input",
                "Please select a video file or folder before running the pipeline."
            )
            self.run_tab.pipeline_finished(False)
            return
        
        # For now, only process first video (TODO: add batch processing)
        if len(selected_videos) > 1 and not self.batch_message_shown:
            QMessageBox.information(
                self,
                "Batch Processing",
                f"Selected {len(selected_videos)} videos.\n\n"
                "Currently processing first video only.\n"
                "Full batch processing will be added in a future update."
            )
            self.batch_message_shown = True  # Don't show again this session
        
        video_path = selected_videos[0]
        
        if not os.path.exists(video_path):
            QMessageBox.warning(
                self,
                "Invalid Input",
                "Selected video file does not exist."
            )
            self.run_tab.pipeline_finished(False)
            return
        
        output_dir = self.input_tab.get_output_path()
        use_cache = self.input_tab.get_use_cache()
        
        # Gather all configuration
        config = {
            "ai": self.ai_tab.get_settings(),
            "metadata": self.metadata_tab.get_settings(),
            "upload": self.upload_tab.get_settings()
        }
        
        # Log cache status
        cache_status = "enabled" if use_cache else "disabled (forcing fresh processing)"
        self.run_tab.append_log(f"Cache: {cache_status}\n")
        
        # Configure and start worker
        self.pipeline_worker.configure(video_path, output_dir, config, use_cache)
        self.run_tab.pipeline_started()
        self.pipeline_worker.start()
        
        # Switch to run tab
        self.tabs.setCurrentWidget(self.run_tab)
    
    def on_stop_pipeline(self):
        """Handle stop pipeline request."""
        self.pipeline_worker.stop()
        self.run_tab.append_log("\nStopping pipeline...")
    
    def on_clear_logs(self):
        """Handle clear logs request."""
        logger.info("Logs cleared")
    
    def on_pipeline_log(self, message: str):
        """Handle pipeline log message."""
        self.run_tab.append_log(message)
    
    def on_pipeline_progress(self, stage: int, total: int, name: str):
        """Handle pipeline progress update."""
        self.run_tab.update_progress(stage, total, name)
    
    def on_pipeline_finished(self, success: bool):
        """Handle pipeline completion."""
        self.run_tab.pipeline_finished(success)
        
        if success:
            QMessageBox.information(
                self,
                "Pipeline Complete",
                "Video processing completed successfully!\n\nCheck the output directory for clips."
            )
        else:
            QMessageBox.warning(
                self,
                "Pipeline Stopped",
                "Pipeline was stopped or encountered errors.\n\nCheck logs for details."
            )
    
    def on_pipeline_error(self, error_msg: str):
        """Handle pipeline error."""
        self.run_tab.pipeline_error(error_msg)
        QMessageBox.critical(
            self,
            "Pipeline Error",
            f"An error occurred:\n\n{error_msg}\n\nCheck logs for details."
        )
    
    def save_settings(self):
        """Save UI settings to file."""
        try:
            settings = {
                "video_path": self.input_tab.get_video_path(),
                "output_path": self.input_tab.get_output_path(),
                "ai": self.ai_tab.get_settings(),
                "metadata": self.metadata_tab.get_settings(),
                "upload": self.upload_tab.get_settings()
            }
            
            settings_file = Path("ui_settings.json")
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            
            logger.debug("Settings saved")
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
    
    def load_settings(self):
        """Load UI settings from file."""
        try:
            settings_file = Path("ui_settings.json")
            if settings_file.exists():
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                
                # Apply settings
                if "video_path" in settings:
                    self.input_tab.set_video_path(settings["video_path"])
                if "output_path" in settings:
                    self.input_tab.set_output_path(settings["output_path"])
                if "ai" in settings:
                    self.ai_tab.set_settings(settings["ai"])
                if "metadata" in settings:
                    self.metadata_tab.set_settings(settings["metadata"])
                if "upload" in settings:
                    self.upload_tab.set_settings(settings["upload"])
                    # Also set environment variables from upload settings
                    upload_settings = settings["upload"]
                    if upload_settings.get("brave_path"):
                        os.environ["BRAVE_PATH"] = upload_settings["brave_path"]
                    if upload_settings.get("user_data_dir"):
                        os.environ["BRAVE_USER_DATA_DIR"] = upload_settings["user_data_dir"]
                    if upload_settings.get("profile_directory"):
                        os.environ["BRAVE_PROFILE_DIRECTORY"] = upload_settings["profile_directory"]
                
                logger.info("Settings loaded")
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Save settings
        self.save_settings()
        
        # Stop scheduler if running
        if self.scheduler.is_running():
            logger.info("Stopping scheduler on app close...")
            self.scheduler.stop()
        
        # Stop workers
        if self.pipeline_worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Pipeline Running",
                "Pipeline is still running. Stop it and exit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.pipeline_worker.stop()
                self.pipeline_worker.wait(5000)  # Wait up to 5 seconds
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
