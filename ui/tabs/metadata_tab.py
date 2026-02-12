"""
Metadata Settings Tab - Title, description, and tags configuration.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QComboBox, QCheckBox, QGroupBox, QPushButton, QFileDialog,
    QScrollArea
)
from PySide6.QtCore import Signal, Qt


class MetadataTab(QWidget):
    """Tab for metadata configuration (title, description, tags)."""
    
    # Signals
    settings_changed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
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
        title = QLabel("Metadata Settings")
        title.setProperty("heading", True)
        layout.addWidget(title)
        
        # Mode selection
        mode_group = QGroupBox("Mode")
        mode_layout = QVBoxLayout(mode_group)
        
        mode_h_layout = QHBoxLayout()
        mode_h_layout.addWidget(QLabel("Metadata Mode:"))
        
        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["Uniform", "Randomized"])
        self.mode_selector.currentTextChanged.connect(self.on_mode_changed)
        mode_h_layout.addWidget(self.mode_selector)
        mode_h_layout.addStretch()
        
        mode_layout.addLayout(mode_h_layout)
        
        # Mode description
        self.mode_description = QLabel(
            "Uniform: Same metadata for all clips"
        )
        self.mode_description.setProperty("subheading", True)
        self.mode_description.setWordWrap(True)
        mode_layout.addWidget(self.mode_description)
        
        layout.addWidget(mode_group)
        
        # Title configuration
        title_group = QGroupBox("Title")
        title_layout = QVBoxLayout(title_group)
        
        self.title_input = QTextEdit()
        self.title_input.setPlaceholderText("Enter title(s)")
        self.title_input.textChanged.connect(self.on_settings_changed)
        title_layout.addWidget(self.title_input)
        
        self.title_hint = QLabel("Single title for all clips")
        self.title_hint.setProperty("subheading", True)
        title_layout.addWidget(self.title_hint)
        
        layout.addWidget(title_group)
        
        # Description configuration
        desc_group = QGroupBox("Description")
        desc_layout = QVBoxLayout(desc_group)
        
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Enter description(s)")
        self.description_input.textChanged.connect(self.on_settings_changed)
        desc_layout.addWidget(self.description_input)
        
        self.desc_hint = QLabel("Single description for all clips")
        self.desc_hint.setProperty("subheading", True)
        desc_layout.addWidget(self.desc_hint)
        
        layout.addWidget(desc_group)
        
        # Tags configuration
        tags_group = QGroupBox("Tags")
        tags_layout = QVBoxLayout(tags_group)
        
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("Enter tags (comma-separated)")
        self.tags_input.textChanged.connect(self.on_settings_changed)
        tags_layout.addWidget(self.tags_input)
        
        self.tags_hint = QLabel("Comma-separated tags (e.g., viral, trending, motivation)")
        self.tags_hint.setProperty("subheading", True)
        tags_layout.addWidget(self.tags_hint)
        
        # Hashtag prefix toggle
        self.hashtag_prefix = QCheckBox("Add # prefix to tags")
        self.hashtag_prefix.setChecked(True)
        self.hashtag_prefix.stateChanged.connect(self.on_settings_changed)
        tags_layout.addWidget(self.hashtag_prefix)
        
        layout.addWidget(tags_group)
        
        # CSV Import (NEW)
        csv_group = QGroupBox("Import from CSV (Optional)")
        csv_layout = QVBoxLayout(csv_group)
        
        csv_h_layout = QHBoxLayout()
        self.csv_path_input = QLineEdit()
        self.csv_path_input.setPlaceholderText("No CSV file selected")
        self.csv_path_input.setReadOnly(True)
        csv_h_layout.addWidget(self.csv_path_input)
        
        self.csv_browse_btn = QPushButton("Browse...")
        self.csv_browse_btn.clicked.connect(self.browse_csv)
        csv_h_layout.addWidget(self.csv_browse_btn)
        
        self.csv_clear_btn = QPushButton("Clear")
        self.csv_clear_btn.clicked.connect(self.clear_csv)
        csv_h_layout.addWidget(self.csv_clear_btn)
        
        csv_layout.addLayout(csv_h_layout)
        
        csv_hint = QLabel(
            "CSV columns: title, caption, description, tags (one row per variant). "
            "CSV values will be merged with fields above for randomized selection."
        )
        csv_hint.setProperty("subheading", True)
        csv_hint.setWordWrap(True)
        csv_layout.addWidget(csv_hint)
        
        layout.addWidget(csv_group)
        
        # Caption configuration (NEW)
        caption_group = QGroupBox("Captions")
        caption_layout = QVBoxLayout(caption_group)
        
        self.caption_input = QTextEdit()
        self.caption_input.setPlaceholderText("Enter caption(s)")
        self.caption_input.textChanged.connect(self.on_settings_changed)
        caption_layout.addWidget(self.caption_input)
        
        self.caption_hint = QLabel("Single caption for all clips")
        self.caption_hint.setProperty("subheading", True)
        caption_layout.addWidget(self.caption_hint)
        
        layout.addWidget(caption_group)
        
        # Hook Phrase for Reels/Shorts (NEW)
        hook_group = QGroupBox("Hook Phrase (Video Overlay)")
        hook_layout = QVBoxLayout(hook_group)
        
        self.hook_phrase_input = QLineEdit()
        self.hook_phrase_input.setPlaceholderText("Enter hook phrase (e.g., 'Wait for it...', 'This is insane!')")
        self.hook_phrase_input.textChanged.connect(self.on_settings_changed)
        hook_layout.addWidget(self.hook_phrase_input)
        
        hook_hint = QLabel("Text overlay on video (positioned at engaging spot, not center)")
        hook_hint.setProperty("subheading", True)
        hook_layout.addWidget(hook_hint)
        
        # Hook position selector
        position_h_layout = QHBoxLayout()
        position_h_layout.addWidget(QLabel("Position:"))
        
        self.hook_position_selector = QComboBox()
        self.hook_position_selector.addItems([
            "Top Left", "Top Right", "Bottom Left", "Bottom Right", "Top Center"
        ])
        self.hook_position_selector.setCurrentText("Top Left")
        self.hook_position_selector.currentTextChanged.connect(self.on_settings_changed)
        position_h_layout.addWidget(self.hook_position_selector)
        position_h_layout.addStretch()
        
        hook_layout.addLayout(position_h_layout)
        
        layout.addWidget(hook_group)
        
        # Logo Overlay (NEW)
        logo_group = QGroupBox("Logo Overlay")
        logo_layout = QVBoxLayout(logo_group)
        
        logo_h_layout = QHBoxLayout()
        self.logo_path_input = QLineEdit()
        self.logo_path_input.setPlaceholderText("No logo selected")
        self.logo_path_input.setReadOnly(True)
        logo_h_layout.addWidget(self.logo_path_input)
        
        self.logo_browse_btn = QPushButton("Browse...")
        self.logo_browse_btn.clicked.connect(self.browse_logo)
        logo_h_layout.addWidget(self.logo_browse_btn)
        
        self.logo_clear_btn = QPushButton("Clear")
        self.logo_clear_btn.clicked.connect(self.clear_logo)
        logo_h_layout.addWidget(self.logo_clear_btn)
        
        logo_layout.addLayout(logo_h_layout)
        
        logo_hint = QLabel("Logo will be placed at the bottom of videos (PNG with transparency recommended)")
        logo_hint.setProperty("subheading", True)
        logo_hint.setWordWrap(True)
        logo_layout.addWidget(logo_hint)
        
        layout.addWidget(logo_group)
        
        # Spacer
        layout.addStretch()
        
        # Set scroll area content
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
    
    def browse_logo(self):
        """Browse for logo image file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Logo Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.svg *.gif)"
        )
        
        if file_path:
            self.logo_path_input.setText(file_path)
            self.on_settings_changed()
    
    def clear_logo(self):
        """Clear logo selection."""
        self.logo_path_input.clear()
        self.on_settings_changed()
    
    def browse_csv(self):
        """Browse for CSV metadata file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV Metadata File",
            "",
            "CSV Files (*.csv)"
        )
        
        if file_path:
            # Validate CSV format
            from metadata import validate_csv_format
            is_valid, message = validate_csv_format(file_path)
            
            if is_valid:
                self.csv_path_input.setText(file_path)
                self.on_settings_changed()
            else:
                # Show error message to user
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self,
                    "Invalid CSV File",
                    f"The selected CSV file is invalid:\n\n{message}\n\n"
                    "Please ensure the CSV has headers like: title, caption, description, tags"
                )
    
    def clear_csv(self):
        """Clear CSV file selection."""
        self.csv_path_input.clear()
        self.on_settings_changed()
    
    def on_mode_changed(self, mode: str):
        """Handle mode change."""
        is_randomized = (mode == "Randomized")
        
        if is_randomized:
            self.mode_description.setText(
                "Randomized: Comma-separated values will be randomly selected per clip"
            )
            self.title_hint.setText(
                "Comma-separated titles (e.g., \"This is insane, You won't believe this, Wild moment\")"
            )
            self.desc_hint.setText(
                "Comma-separated descriptions (randomly selected per clip)"
            )
            self.caption_hint.setText(
                "Comma-separated captions (randomly selected per clip)"
            )
            self.tags_hint.setText(
                "Comma-separated tags (shuffled per clip)"
            )
        else:
            self.mode_description.setText(
                "Uniform: Same metadata for all clips"
            )
            self.title_hint.setText("Single title for all clips")
            self.desc_hint.setText("Single description for all clips")
            self.caption_hint.setText("Single caption for all clips")
            self.tags_hint.setText(
                "Comma-separated tags (e.g., viral, trending, motivation)"
            )
        
        self.on_settings_changed()
    
    def on_settings_changed(self):
        """Emit settings changed signal."""
        settings = self.get_settings()
        self.settings_changed.emit(settings)
    
    def get_settings(self) -> dict:
        """Get metadata settings."""
        mode = "randomized" if self.mode_selector.currentText() == "Randomized" else "uniform"
        
        return {
            "mode": mode,
            "title": self.title_input.toPlainText(),
            "description": self.description_input.toPlainText(),
            "caption": self.caption_input.toPlainText(),
            "tags": self.tags_input.text(),
            "hashtag_prefix": self.hashtag_prefix.isChecked(),
            "hook_phrase": self.hook_phrase_input.text(),
            "hook_position": self.hook_position_selector.currentText(),
            "logo_path": self.logo_path_input.text(),
            "csv_file_path": self.csv_path_input.text()
        }
    
    def set_settings(self, settings: dict):
        """Set metadata settings from dictionary."""
        if "mode" in settings:
            mode_text = "Randomized" if settings["mode"] == "randomized" else "Uniform"
            self.mode_selector.setCurrentText(mode_text)
        
        if "title" in settings:
            self.title_input.setPlainText(settings["title"])
        
        if "description" in settings:
            self.description_input.setPlainText(settings["description"])
        
        if "caption" in settings:
            self.caption_input.setPlainText(settings["caption"])
        
        if "tags" in settings:
            self.tags_input.setText(settings["tags"])
        
        if "hashtag_prefix" in settings:
            self.hashtag_prefix.setChecked(settings["hashtag_prefix"])
        
        if "hook_phrase" in settings:
            self.hook_phrase_input.setText(settings["hook_phrase"])
        
        if "hook_position" in settings:
            self.hook_position_selector.setCurrentText(settings["hook_position"])
        
        if "logo_path" in settings:
            self.logo_path_input.setText(settings["logo_path"])
        
        if "csv_file_path" in settings:
            self.csv_path_input.setText(settings["csv_file_path"])
