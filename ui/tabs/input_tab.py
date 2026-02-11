"""
Input Video Tab - Video file selection and output configuration.
"""

import os
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFileDialog, QGroupBox, QCheckBox, QButtonGroup, QRadioButton
)
from PySide6.QtCore import Signal


class InputTab(QWidget):
    """Tab for input video and output directory selection."""
    
    # Signals
    video_selected = Signal(str)  # Emitted when video file is selected
    videos_selected = Signal(list)  # Emitted when multiple videos/folder selected
    output_changed = Signal(str)  # Emitted when output directory changes
    cache_changed = Signal(bool)  # Emitted when cache setting changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_videos = []  # List of selected video paths
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
        video_group = QGroupBox("Video Selection")
        video_layout = QVBoxLayout(video_group)
        
        # Selection mode
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Selection Mode:"))
        
        self.mode_single = QRadioButton("Single File")
        self.mode_multiple = QRadioButton("Multiple Files")
        self.mode_folder = QRadioButton("Folder")
        
        self.mode_group = QButtonGroup()
        self.mode_group.addButton(self.mode_single, 1)
        self.mode_group.addButton(self.mode_multiple, 2)
        self.mode_group.addButton(self.mode_folder, 3)
        
        self.mode_single.setChecked(True)  # Default to single file
        
        mode_layout.addWidget(self.mode_single)
        mode_layout.addWidget(self.mode_multiple)
        mode_layout.addWidget(self.mode_folder)
        mode_layout.addStretch()
        video_layout.addLayout(mode_layout)
        
        # Video file path display
        self.video_path = QLineEdit()
        self.video_path.setPlaceholderText("No video(s) selected")
        self.video_path.setReadOnly(True)
        video_layout.addWidget(self.video_path)
        
        # Browse button
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_video)
        video_layout.addWidget(browse_btn)
        
        # File info label
        self.file_info = QLabel("Select video file(s) or folder to begin")
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
        
        # Pipeline options group
        options_group = QGroupBox("Pipeline Options")
        options_layout = QVBoxLayout(options_group)
        
        # Cache control checkbox
        self.use_cache_checkbox = QCheckBox("Use cached results (resume from last stage)")
        self.use_cache_checkbox.setChecked(True)  # Default: use cache
        self.use_cache_checkbox.stateChanged.connect(self.on_cache_changed)
        options_layout.addWidget(self.use_cache_checkbox)
        
        cache_info = QLabel(
            "When unchecked, forces fresh processing of all pipeline stages.\n"
            "Use this to reprocess a video from scratch."
        )
        cache_info.setProperty("subheading", True)
        cache_info.setWordWrap(True)
        options_layout.addWidget(cache_info)
        
        layout.addWidget(options_group)
        
        # Spacer
        layout.addStretch()
    
    def browse_video(self):
        """Open file dialog to select video file(s) or folder."""
        mode_id = self.mode_group.checkedId()
        
        if mode_id == 1:  # Single file
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Video File",
                "",
                "Video Files (*.mp4 *.mov *.avi *.mkv *.webm);;All Files (*.*)"
            )
            
            if file_path:
                self.selected_videos = [file_path]
                self.video_path.setText(file_path)
                self.update_file_info(file_path)
                self.video_selected.emit(file_path)
                
        elif mode_id == 2:  # Multiple files
            file_paths, _ = QFileDialog.getOpenFileNames(
                self,
                "Select Video Files",
                "",
                "Video Files (*.mp4 *.mov *.avi *.mkv *.webm);;All Files (*.*)"
            )
            
            if file_paths:
                self.selected_videos = file_paths
                count = len(file_paths)
                self.video_path.setText(f"{count} videos selected")
                self.update_multiple_files_info(file_paths)
                self.videos_selected.emit(file_paths)
                
        else:  # Folder
            folder_path = QFileDialog.getExistingDirectory(
                self,
                "Select Folder Containing Videos"
            )
            
            if folder_path:
                # Find all video files in folder
                video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
                video_files = []
                
                for file in os.listdir(folder_path):
                    if any(file.lower().endswith(ext) for ext in video_extensions):
                        video_files.append(os.path.join(folder_path, file))
                
                if video_files:
                    self.selected_videos = sorted(video_files)
                    count = len(video_files)
                    self.video_path.setText(f"{folder_path} ({count} videos)")
                    self.update_multiple_files_info(video_files)
                    self.videos_selected.emit(video_files)
                else:
                    self.file_info.setText("No video files found in folder")
    
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
    
    def on_cache_changed(self, state):
        """Handle cache checkbox change."""
        use_cache = state == 2  # Qt.Checked
        self.cache_changed.emit(use_cache)
    
    def update_file_info(self, file_path: str):
        """Update file information label for single file."""
        if os.path.exists(file_path):
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            filename = os.path.basename(file_path)
            self.file_info.setText(f"{filename} ({size_mb:.1f} MB)")
        else:
            self.file_info.setText("File not found")
    
    def update_multiple_files_info(self, file_paths: list):
        """Update file information label for multiple files."""
        count = len(file_paths)
        total_size = sum(os.path.getsize(f) for f in file_paths if os.path.exists(f))
        total_mb = total_size / (1024 * 1024)
        self.file_info.setText(f"{count} videos selected ({total_mb:.1f} MB total)")
    
    def get_video_path(self) -> str:
        """Get selected video path (single file mode)."""
        return self.video_path.text() if len(self.selected_videos) == 1 else ""
    
    def get_selected_videos(self) -> list:
        """Get list of all selected video paths."""
        return self.selected_videos
    
    def get_output_path(self) -> str:
        """Get output directory path."""
        return self.output_path.text()
    
    def get_use_cache(self) -> bool:
        """Get cache setting."""
        return self.use_cache_checkbox.isChecked()
    
    def set_video_path(self, path: str):
        """Set video path programmatically."""
        self.selected_videos = [path]
        self.video_path.setText(path)
        self.update_file_info(path)
    
    def set_output_path(self, path: str):
        """Set output path programmatically."""
        self.output_path.setText(path)
    
    def set_use_cache(self, use_cache: bool):
        """Set cache checkbox."""
        self.use_cache_checkbox.setChecked(use_cache)
