"""
Metadata Settings Tab - Title, description, and tags configuration.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QComboBox, QCheckBox, QGroupBox
)
from PySide6.QtCore import Signal


class MetadataTab(QWidget):
    """Tab for metadata configuration (title, description, tags)."""
    
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
        self.title_input.setMaximumHeight(80)
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
        self.description_input.setMaximumHeight(100)
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
        
        # Spacer
        layout.addStretch()
    
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
            self.tags_hint.setText(
                "Comma-separated tags (shuffled per clip)"
            )
        else:
            self.mode_description.setText(
                "Uniform: Same metadata for all clips"
            )
            self.title_hint.setText("Single title for all clips")
            self.desc_hint.setText("Single description for all clips")
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
            "tags": self.tags_input.text(),
            "hashtag_prefix": self.hashtag_prefix.isChecked()
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
        
        if "tags" in settings:
            self.tags_input.setText(settings["tags"])
        
        if "hashtag_prefix" in settings:
            self.hashtag_prefix.setChecked(settings["hashtag_prefix"])
