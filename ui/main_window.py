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
from .workers.ollama_worker import OllamaWorker
from .workers.pipeline_worker import PipelineWorker

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window with tabbed interface."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_workers()
        self.load_settings()
        
        # Start status updates
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_ollama_status)
        self.status_timer.start(3000)  # Update every 3 seconds
    
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
    
    def init_workers(self):
        """Initialize background workers."""
        self.ollama_worker = OllamaWorker()
        self.ollama_worker.operation_complete.connect(self.on_ollama_operation_complete)
        self.ollama_worker.status_update.connect(self.on_ollama_status_update)
        
        self.pipeline_worker = PipelineWorker()
        self.pipeline_worker.log_message.connect(self.on_pipeline_log)
        self.pipeline_worker.progress_update.connect(self.on_pipeline_progress)
        self.pipeline_worker.finished.connect(self.on_pipeline_finished)
        self.pipeline_worker.error_occurred.connect(self.on_pipeline_error)
    
    def connect_signals(self):
        """Connect all UI signals to handlers."""
        # Input tab
        self.input_tab.video_selected.connect(self.on_video_selected)
        self.input_tab.output_changed.connect(self.on_output_changed)
        
        # AI tab
        self.ai_tab.start_ollama_clicked.connect(self.on_start_ollama)
        self.ai_tab.stop_ollama_clicked.connect(self.on_stop_ollama)
        self.ai_tab.load_model_clicked.connect(self.on_load_model)
        self.ai_tab.settings_changed.connect(self.on_ai_settings_changed)
        
        # Metadata tab
        self.metadata_tab.settings_changed.connect(self.on_metadata_settings_changed)
        
        # Upload tab
        self.upload_tab.settings_changed.connect(self.on_upload_settings_changed)
        
        # Run tab
        self.run_tab.run_clicked.connect(self.on_run_pipeline)
        self.run_tab.stop_clicked.connect(self.on_stop_pipeline)
        self.run_tab.clear_logs_clicked.connect(self.on_clear_logs)
    
    def on_video_selected(self, path: str):
        """Handle video selection."""
        logger.info(f"Video selected: {path}")
        self.save_settings()
    
    def on_output_changed(self, path: str):
        """Handle output directory change."""
        logger.info(f"Output directory changed: {path}")
        self.save_settings()
    
    def on_start_ollama(self):
        """Handle start Ollama request."""
        self.run_tab.append_log("Starting Ollama server...")
        self.ollama_worker.start_server()
    
    def on_stop_ollama(self):
        """Handle stop Ollama request."""
        self.run_tab.append_log("Stopping Ollama server...")
        self.ollama_worker.stop_server()
    
    def on_load_model(self, model_name: str):
        """Handle load model request."""
        self.run_tab.append_log(f"Loading model: {model_name}")
        QMessageBox.information(
            self,
            "Loading Model",
            f"Downloading {model_name}...\n\nThis may take several minutes depending on model size and network speed.\n\nThe UI will remain responsive. Check the logs for progress."
        )
        self.ollama_worker.load_model(model_name)
    
    def on_ollama_operation_complete(self, success: bool, message: str):
        """Handle Ollama operation completion."""
        self.run_tab.append_log(f"Ollama: {message}")
        
        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.warning(self, "Operation Failed", message)
        
        # Update status
        self.update_ollama_status()
    
    def on_ollama_status_update(self, status: dict):
        """Handle Ollama status update."""
        running = status.get("running", False)
        model_loaded = status.get("model_loaded", False)
        self.ai_tab.update_ollama_status(running, model_loaded)
    
    def update_ollama_status(self):
        """Request Ollama status update."""
        if not self.ollama_worker.isRunning():
            self.ollama_worker.check_status()
    
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
    
    def on_run_pipeline(self):
        """Handle run pipeline request."""
        # Validate inputs
        video_path = self.input_tab.get_video_path()
        
        if not video_path or not os.path.exists(video_path):
            QMessageBox.warning(
                self,
                "Invalid Input",
                "Please select a valid video file before running the pipeline."
            )
            self.run_tab.pipeline_finished(False)
            return
        
        output_dir = self.input_tab.get_output_path()
        
        # Gather all configuration
        config = {
            "ai": self.ai_tab.get_settings(),
            "metadata": self.metadata_tab.get_settings(),
            "upload": self.upload_tab.get_settings()
        }
        
        # Configure and start worker
        self.pipeline_worker.configure(video_path, output_dir, config)
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
                
                logger.info("Settings loaded")
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Save settings
        self.save_settings()
        
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
