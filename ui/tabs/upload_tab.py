"""
Upload Platforms Tab - Platform selection and browser configuration.
"""

import sys
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QLineEdit, QPushButton, QGroupBox, QFileDialog, QSpinBox, QComboBox
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
        
        # User Data Directory (critical for profile reuse)
        user_data_label = QLabel("User Data Directory:")
        brave_layout.addWidget(user_data_label)
        
        user_data_h_layout = QHBoxLayout()
        self.user_data_dir = QLineEdit()
        self.user_data_dir.setPlaceholderText(self.get_default_user_data_dir())
        self.user_data_dir.textChanged.connect(self.on_user_data_dir_changed)
        user_data_h_layout.addWidget(self.user_data_dir)
        
        user_data_browse_btn = QPushButton("Browse...")
        user_data_browse_btn.clicked.connect(self.browse_user_data_dir)
        user_data_h_layout.addWidget(user_data_browse_btn)
        
        brave_layout.addLayout(user_data_h_layout)
        
        user_data_hint = QLabel("Required for login persistence (e.g., C:\\Users\\<USER>\\AppData\\Local\\BraveSoftware\\Brave-Browser\\User Data)")
        user_data_hint.setProperty("subheading", True)
        user_data_hint.setWordWrap(True)
        brave_layout.addWidget(user_data_hint)
        
        # Profile Directory dropdown
        profile_dir_label = QLabel("Profile Directory:")
        brave_layout.addWidget(profile_dir_label)
        
        profile_dir_h_layout = QHBoxLayout()
        self.profile_directory = QComboBox()
        self.profile_directory.addItems(["Default"])
        self.profile_directory.setEditable(True)
        self.profile_directory.currentTextChanged.connect(self.on_settings_changed)
        profile_dir_h_layout.addWidget(self.profile_directory)
        
        refresh_profiles_btn = QPushButton("Refresh")
        refresh_profiles_btn.clicked.connect(self.refresh_profiles)
        profile_dir_h_layout.addWidget(refresh_profiles_btn)
        
        brave_layout.addLayout(profile_dir_h_layout)
        
        profile_dir_hint = QLabel("Select which Brave profile to use (e.g., 'Default', 'Profile 1', 'Profile 2')")
        profile_dir_hint.setProperty("subheading", True)
        profile_dir_hint.setWordWrap(True)
        brave_layout.addWidget(profile_dir_hint)
        
        # Test Profile button
        test_profile_btn = QPushButton("🔍 Test Profile")
        test_profile_btn.clicked.connect(self.test_profile)
        brave_layout.addWidget(test_profile_btn)
        
        test_hint = QLabel("Opens Google to verify your profile is configured correctly and logged in")
        test_hint.setProperty("subheading", True)
        test_hint.setWordWrap(True)
        brave_layout.addWidget(test_hint)
        
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
    
    def get_default_user_data_dir(self) -> str:
        """Get default Brave user data directory for current platform."""
        if sys.platform == "win32":
            return os.path.expanduser(r"~\AppData\Local\BraveSoftware\Brave-Browser\User Data")
        elif sys.platform == "darwin":
            return os.path.expanduser("~/Library/Application Support/BraveSoftware/Brave-Browser")
        else:
            return os.path.expanduser("~/.config/BraveSoftware/Brave-Browser")
    
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
    
    def browse_user_data_dir(self):
        """Browse for Brave user data directory."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Brave User Data Directory",
            self.get_default_user_data_dir()
        )
        
        if dir_path:
            self.user_data_dir.setText(dir_path)
            self.refresh_profiles()
    
    def on_user_data_dir_changed(self):
        """Called when user data directory changes."""
        self.refresh_profiles()
        self.on_settings_changed()
    
    def refresh_profiles(self):
        """Refresh the list of available profiles."""
        user_data_dir = self.user_data_dir.text().strip()
        
        if not user_data_dir:
            user_data_dir = self.get_default_user_data_dir()
        
        if not os.path.exists(user_data_dir):
            self.profile_directory.clear()
            self.profile_directory.addItem("Default")
            return
        
        # Get available profiles using the brave_base helper
        try:
            from uploaders.brave_base import BraveBrowserBase
            profiles = BraveBrowserBase.get_available_profiles(user_data_dir)
            
            if profiles:
                current_selection = self.profile_directory.currentText()
                self.profile_directory.clear()
                self.profile_directory.addItems(profiles)
                
                # Restore previous selection if it exists
                if current_selection in profiles:
                    self.profile_directory.setCurrentText(current_selection)
            else:
                self.profile_directory.clear()
                self.profile_directory.addItem("Default")
        except Exception as e:
            print(f"Error refreshing profiles: {e}")
            self.profile_directory.clear()
            self.profile_directory.addItem("Default")
    
    def test_profile(self):
        """Test the Brave profile by opening Google."""
        from PySide6.QtWidgets import QMessageBox
        
        try:
            # Get settings
            brave_path = self.brave_path.text().strip()
            user_data_dir = self.user_data_dir.text().strip()
            profile_directory = self.profile_directory.currentText().strip()
            
            # Use defaults if not specified
            if not brave_path:
                brave_path = None  # Will auto-detect
            
            if not user_data_dir:
                QMessageBox.warning(
                    self,
                    "User Data Dir Required",
                    "Please specify a User Data Directory to test the profile.\n\n"
                    "Example (Windows): C:\\Users\\<USER>\\AppData\\Local\\BraveSoftware\\Brave-Browser\\User Data"
                )
                return
            
            if not profile_directory:
                profile_directory = "Default"
            
            # Import and launch browser
            from uploaders.brave_base import BraveBrowserBase
            
            QMessageBox.information(
                self,
                "Testing Profile",
                f"Opening Google in Brave to test profile...\n\n"
                f"User Data Dir: {user_data_dir}\n"
                f"Profile: {profile_directory}\n\n"
                f"NOTE: Any running Brave processes will be automatically closed.\n"
                f"Check if you're logged into Google.\n"
                f"The browser will close automatically in 15 seconds."
            )
            
            browser = BraveBrowserBase(brave_path, user_data_dir, profile_directory)
            page = browser.launch(headless=False)
            
            # Navigate to Google
            try:
                page.goto("https://accounts.google.com", wait_until="networkidle", timeout=30000)
            except Exception as nav_error:
                browser.close()
                raise RuntimeError(
                    f"Failed to navigate to Google:\n{str(nav_error)}\n\n"
                    "This could indicate:\n"
                    "- Network connectivity issues\n"
                    "- Profile configuration problems\n"
                    "- Brave browser issues"
                )
            
            # Wait 15 seconds for user to check
            import time
            time.sleep(15)
            
            # Close browser
            browser.close()
            
            QMessageBox.information(
                self,
                "Test Complete",
                "Profile test complete!\n\n"
                "If you were logged into Google, the profile is configured correctly."
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Test Failed",
                f"Failed to test profile:\n\n{str(e)}\n\n"
                "Make sure the User Data Directory and Profile Directory are correct."
            )
    
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
            "user_data_dir": self.user_data_dir.text(),
            "profile_directory": self.profile_directory.currentText(),
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
        
        if "user_data_dir" in settings:
            self.user_data_dir.setText(settings["user_data_dir"])
            self.refresh_profiles()
        
        if "profile_directory" in settings:
            self.profile_directory.setCurrentText(settings["profile_directory"])
        
        if "min_delay" in settings:
            self.min_delay.setValue(settings["min_delay"])
        
        if "max_delay" in settings:
            self.max_delay.setValue(settings["max_delay"])
