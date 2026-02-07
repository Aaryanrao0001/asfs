"""
Input Video Tab - Video file selection and output configuration.
"""

import os
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFileDialog, QGroupBox
)
from PySide6.QtCore import Signal


class InputTab(QWidget):
    """Tab for input video and output directory selection."""
    
    # Signals
    video_selected = Signal(str)  # Emitted when video file is selected
    output_changed = Signal(str)  # Emitted when output directory changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Title
        title = QLabel("Input Video & Output Settings")
        title.setProperty("heading", True)
        layout.addWidget(title)
        
        # Video file selection group
        video_group = QGroupBox("Video File")
        video_layout = QVBoxLayout(video_group)
        
        # Video file path display
        self.video_path = QLineEdit()
        self.video_path.setPlaceholderText("No video selected")
        self.video_path.setReadOnly(True)
        video_layout.addWidget(self.video_path)
        
        # Browse button
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_video)
        video_layout.addWidget(browse_btn)
        
        # File info label
        self.file_info = QLabel("Select a video file to begin")
        self.file_info.setProperty("subheading", True)
        video_layout.addWidget(self.file_info)
        
        layout.addWidget(video_group)
        
        # Output directory selection group
        output_group = QGroupBox("Output Directory")
        output_layout = QVBoxLayout(output_group)
        
        # Output directory path
        output_h_layout = QHBoxLayout()
        self.output_path = QLineEdit()
        self.output_path.setText("output")  # Default value
        self.output_path.textChanged.connect(self.on_output_changed)
        output_h_layout.addWidget(self.output_path)
        
        # Browse button for output
        output_browse_btn = QPushButton("Browse...")
        output_browse_btn.clicked.connect(self.browse_output)
        output_h_layout.addWidget(output_browse_btn)
        
        output_layout.addLayout(output_h_layout)
        
        # Output info
        output_info = QLabel("Clips and work files will be saved here")
        output_info.setProperty("subheading", True)
        output_layout.addWidget(output_info)
        
        layout.addWidget(output_group)
        
        # Spacer
        layout.addStretch()
    
    def browse_video(self):
        """Open file dialog to select video file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video File",
            "",
            "Video Files (*.mp4 *.mov *.avi *.mkv *.webm);;All Files (*.*)"
        )
        
        if file_path:
            self.video_path.setText(file_path)
            self.update_file_info(file_path)
            self.video_selected.emit(file_path)
    
    def browse_output(self):
        """Open dialog to select output directory."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            self.output_path.text()
        )
        
        if dir_path:
            self.output_path.setText(dir_path)
    
    def on_output_changed(self, text):
        """Handle output path change."""
        self.output_changed.emit(text)
    
    def update_file_info(self, file_path: str):
        """Update file information label."""
        if os.path.exists(file_path):
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            filename = os.path.basename(file_path)
            self.file_info.setText(f"{filename} ({size_mb:.1f} MB)")
        else:
            self.file_info.setText("File not found")
    
    def get_video_path(self) -> str:
        """Get selected video path."""
        return self.video_path.text()
    
    def get_output_path(self) -> str:
        """Get output directory path."""
        return self.output_path.text()
    
    def set_video_path(self, path: str):
        """Set video path programmatically."""
        self.video_path.setText(path)
        self.update_file_info(path)
    
    def set_output_path(self, path: str):
        """Set output path programmatically."""
        self.output_path.setText(path)
