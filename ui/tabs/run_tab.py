"""
Run & Monitor Tab - Pipeline execution and live logging.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QProgressBar, QGroupBox
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QTextCursor


class RunTab(QWidget):
    """Tab for pipeline execution and monitoring."""
    
    # Signals
    run_clicked = Signal()
    stop_clicked = Signal()
    clear_logs_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Title
        title = QLabel("Run Pipeline & Monitor")
        title.setProperty("heading", True)
        layout.addWidget(title)
        
        # Control buttons
        controls_h_layout = QHBoxLayout()
        
        self.run_btn = QPushButton("▶ Run Pipeline")
        self.run_btn.clicked.connect(self.on_run_clicked)
        self.run_btn.setMinimumHeight(40)
        controls_h_layout.addWidget(self.run_btn)
        
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setProperty("danger", True)
        self.stop_btn.clicked.connect(self.on_stop_clicked)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumHeight(40)
        controls_h_layout.addWidget(self.stop_btn)
        
        clear_btn = QPushButton("Clear Logs")
        clear_btn.setProperty("secondary", True)
        clear_btn.clicked.connect(self.on_clear_logs)
        clear_btn.setMinimumHeight(40)
        controls_h_layout.addWidget(clear_btn)
        
        controls_h_layout.addStretch()
        
        layout.addLayout(controls_h_layout)
        
        # Progress group
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        # Status label
        self.status_label = QLabel("Ready to run")
        self.status_label.setProperty("heading", True)
        progress_layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        # Stage info
        self.stage_label = QLabel("")
        self.stage_label.setProperty("subheading", True)
        progress_layout.addWidget(self.stage_label)
        
        layout.addWidget(progress_group)
        
        # Logs group
        logs_group = QGroupBox("Live Logs")
        logs_layout = QVBoxLayout(logs_group)
        
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setLineWrapMode(QTextEdit.NoWrap)
        self.log_display.setPlaceholderText("Logs will appear here when pipeline runs...")
        logs_layout.addWidget(self.log_display)
        
        layout.addWidget(logs_group)
    
    def on_run_clicked(self):
        """Handle run button click."""
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("Running...")
        self.status_label.setProperty("status", "running")
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        self.run_clicked.emit()
    
    def on_stop_clicked(self):
        """Handle stop button click."""
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Stopping...")
        self.stop_clicked.emit()
    
    def on_clear_logs(self):
        """Clear the log display."""
        self.log_display.clear()
        self.clear_logs_clicked.emit()
    
    def append_log(self, message: str):
        """
        Append a log message to the display.
        
        Args:
            message: Log message to append
        """
        self.log_display.append(message)
        # Auto-scroll to bottom
        cursor = self.log_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_display.setTextCursor(cursor)
    
    def update_progress(self, stage: int, total_stages: int, stage_name: str = ""):
        """
        Update progress indicators.
        
        Args:
            stage: Current stage number (1-based)
            total_stages: Total number of stages
            stage_name: Name of current stage
        """
        progress = int((stage / total_stages) * 100)
        self.progress_bar.setValue(progress)
        
        if stage_name:
            self.stage_label.setText(f"Stage {stage}/{total_stages}: {stage_name}")
        else:
            self.stage_label.setText(f"Stage {stage}/{total_stages}")
    
    def set_status(self, status: str, status_type: str = ""):
        """
        Set the status label.
        
        Args:
            status: Status message
            status_type: Status type (running, success, error, stopped)
        """
        self.status_label.setText(status)
        if status_type:
            self.status_label.setProperty("status", status_type)
            self.status_label.style().unpolish(self.status_label)
            self.status_label.style().polish(self.status_label)
    
    def pipeline_started(self):
        """Called when pipeline starts."""
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.set_status("Running...", "running")
    
    def pipeline_finished(self, success: bool = True):
        """Called when pipeline finishes."""
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setValue(100 if success else 0)
        
        if success:
            self.set_status("Completed successfully", "success")
        else:
            self.set_status("Failed or stopped", "error")
    
    def pipeline_error(self, error_msg: str):
        """Called when pipeline encounters an error."""
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.set_status(f"Error: {error_msg}", "error")
        self.append_log(f"\n❌ ERROR: {error_msg}\n")
