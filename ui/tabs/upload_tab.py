"""
Upload Platforms Tab - Platform selection and browser configuration.
"""

import sys
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QLineEdit, QPushButton, QGroupBox, QFileDialog, QSpinBox
)
from PySide6.QtCore import Signal


class UploadTab(QWidget):
    """Tab for upload platform configuration."""
    
    # Signals
    settings_changed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Title
        title = QLabel("Upload Platform Settings")
        title.setProperty("heading", True)
        layout.addWidget(title)
        
        # Platform selection
        platforms_group = QGroupBox("Platforms")
        platforms_layout = QVBoxLayout(platforms_group)
        
        self.tiktok_checkbox = QCheckBox("TikTok")
        self.tiktok_checkbox.setChecked(True)
        self.tiktok_checkbox.stateChanged.connect(self.on_settings_changed)
        platforms_layout.addWidget(self.tiktok_checkbox)
        
        self.instagram_checkbox = QCheckBox("Instagram")
        self.instagram_checkbox.setChecked(True)
        self.instagram_checkbox.stateChanged.connect(self.on_settings_changed)
        platforms_layout.addWidget(self.instagram_checkbox)
        
        self.youtube_checkbox = QCheckBox("YouTube Shorts")
        self.youtube_checkbox.setChecked(True)
        self.youtube_checkbox.stateChanged.connect(self.on_settings_changed)
        platforms_layout.addWidget(self.youtube_checkbox)
        
        layout.addWidget(platforms_group)
        
        # Brave browser configuration
        brave_group = QGroupBox("Brave Browser Configuration")
        brave_layout = QVBoxLayout(brave_group)
        
        # Brave executable path
        brave_exe_label = QLabel("Brave Browser Executable:")
        brave_layout.addWidget(brave_exe_label)
        
        brave_exe_h_layout = QHBoxLayout()
        self.brave_path = QLineEdit()
        self.brave_path.setPlaceholderText(self.get_default_brave_path())
        self.brave_path.textChanged.connect(self.on_settings_changed)
        brave_exe_h_layout.addWidget(self.brave_path)
        
        brave_browse_btn = QPushButton("Browse...")
        brave_browse_btn.clicked.connect(self.browse_brave_path)
        brave_exe_h_layout.addWidget(brave_browse_btn)
        
        brave_layout.addLayout(brave_exe_h_layout)
        
        brave_hint = QLabel("Leave empty to auto-detect")
        brave_hint.setProperty("subheading", True)
        brave_layout.addWidget(brave_hint)
        
        # Brave profile path (optional)
        profile_label = QLabel("Brave Profile Directory (optional):")
        brave_layout.addWidget(profile_label)
        
        profile_h_layout = QHBoxLayout()
        self.profile_path = QLineEdit()
        self.profile_path.setPlaceholderText("Leave empty for default profile")
        self.profile_path.textChanged.connect(self.on_settings_changed)
        profile_h_layout.addWidget(self.profile_path)
        
        profile_browse_btn = QPushButton("Browse...")
        profile_browse_btn.clicked.connect(self.browse_profile_path)
        profile_h_layout.addWidget(profile_browse_btn)
        
        brave_layout.addLayout(profile_h_layout)
        
        profile_hint = QLabel("Reuse existing login session by specifying user-data-dir")
        profile_hint.setProperty("subheading", True)
        brave_layout.addWidget(profile_hint)
        
        layout.addWidget(brave_group)
        
        # Upload delay settings
        delay_group = QGroupBox("Upload Delays (Anti-Ban)")
        delay_layout = QVBoxLayout(delay_group)
        
        delay_h_layout = QHBoxLayout()
        
        # Min delay
        delay_h_layout.addWidget(QLabel("Min Delay (seconds):"))
        self.min_delay = QSpinBox()
        self.min_delay.setMinimum(1)
        self.min_delay.setMaximum(300)
        self.min_delay.setValue(5)
        self.min_delay.valueChanged.connect(self.on_settings_changed)
        delay_h_layout.addWidget(self.min_delay)
        
        delay_h_layout.addWidget(QLabel("Max Delay (seconds):"))
        self.max_delay = QSpinBox()
        self.max_delay.setMinimum(1)
        self.max_delay.setMaximum(300)
        self.max_delay.setValue(15)
        self.max_delay.valueChanged.connect(self.on_settings_changed)
        delay_h_layout.addWidget(self.max_delay)
        
        delay_h_layout.addStretch()
        
        delay_layout.addLayout(delay_h_layout)
        
        delay_hint = QLabel("Random delay between uploads to avoid detection")
        delay_hint.setProperty("subheading", True)
        delay_layout.addWidget(delay_hint)
        
        layout.addWidget(delay_group)
        
        # Spacer
        layout.addStretch()
    
    def get_default_brave_path(self) -> str:
        """Get default Brave browser path for current platform."""
        if sys.platform == "win32":
            return "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"
        elif sys.platform == "darwin":
            return "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
        else:
            return "/usr/bin/brave-browser"
    
    def browse_brave_path(self):
        """Browse for Brave executable."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Brave Browser Executable",
            "",
            "Executable Files (*.exe);;All Files (*.*)" if sys.platform == "win32" else "All Files (*)"
        )
        
        if file_path:
            self.brave_path.setText(file_path)
    
    def browse_profile_path(self):
        """Browse for Brave profile directory."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Brave Profile Directory",
            ""
        )
        
        if dir_path:
            self.profile_path.setText(dir_path)
    
    def on_settings_changed(self):
        """Emit settings changed signal."""
        settings = self.get_settings()
        self.settings_changed.emit(settings)
    
    def get_settings(self) -> dict:
        """Get upload settings."""
        return {
            "platforms": {
                "tiktok": self.tiktok_checkbox.isChecked(),
                "instagram": self.instagram_checkbox.isChecked(),
                "youtube": self.youtube_checkbox.isChecked()
            },
            "brave_path": self.brave_path.text(),
            "profile_path": self.profile_path.text(),
            "min_delay": self.min_delay.value(),
            "max_delay": self.max_delay.value()
        }
    
    def set_settings(self, settings: dict):
        """Set upload settings from dictionary."""
        if "platforms" in settings:
            platforms = settings["platforms"]
            self.tiktok_checkbox.setChecked(platforms.get("tiktok", True))
            self.instagram_checkbox.setChecked(platforms.get("instagram", True))
            self.youtube_checkbox.setChecked(platforms.get("youtube", True))
        
        if "brave_path" in settings:
            self.brave_path.setText(settings["brave_path"])
        
        if "profile_path" in settings:
            self.profile_path.setText(settings["profile_path"])
        
        if "min_delay" in settings:
            self.min_delay.setValue(settings["min_delay"])
        
        if "max_delay" in settings:
            self.max_delay.setValue(settings["max_delay"])
