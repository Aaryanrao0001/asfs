"""
AI/Model Settings Tab - GitHub Models API configuration.
"""

import os
import yaml
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QSlider, QGroupBox
)
from PySide6.QtCore import Signal, Qt


# Default values (loaded from config if available)
DEFAULT_MODEL_NAME = "gpt-4o"
DEFAULT_ENDPOINT = "https://models.inference.ai.azure.com"

def load_model_defaults():
    """Load default values from config/model.yaml if available."""
    global DEFAULT_MODEL_NAME, DEFAULT_ENDPOINT
    
    try:
        config_path = Path(__file__).parent.parent.parent / "config" / "model.yaml"
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                model_config = config.get('model', {})
                DEFAULT_MODEL_NAME = model_config.get('model_name', DEFAULT_MODEL_NAME)
                DEFAULT_ENDPOINT = model_config.get('endpoint', DEFAULT_ENDPOINT)
    except Exception:
        pass  # Use hardcoded defaults if config loading fails


# Load defaults on module import
load_model_defaults()


class AITab(QWidget):
    """Tab for AI model configuration."""
    
    # Signals
    settings_changed = Signal(dict)  # All AI settings
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Title
        title = QLabel("AI & Model Settings")
        title.setProperty("heading", True)
        layout.addWidget(title)
        
        # GitHub Models API group
        api_group = QGroupBox("GitHub Models API")
        api_layout = QVBoxLayout(api_group)
        
        # Info label
        info_label = QLabel(
            "Using GitHub Models API for AI scoring.\n"
            "Set GITHUB_TOKEN environment variable with your GitHub token."
        )
        info_label.setWordWrap(True)
        info_label.setProperty("subheading", True)
        api_layout.addWidget(info_label)
        
        # Model name
        model_name_layout = QHBoxLayout()
        model_name_layout.addWidget(QLabel("Model Name:"))
        self.model_name = QLineEdit(DEFAULT_MODEL_NAME)
        self.model_name.setPlaceholderText("e.g., gpt-4o, gpt-4o-mini")
        self.model_name.textChanged.connect(self.on_settings_changed)
        model_name_layout.addWidget(self.model_name)
        api_layout.addLayout(model_name_layout)
        
        # Endpoint (optional)
        endpoint_layout = QHBoxLayout()
        endpoint_layout.addWidget(QLabel("API Endpoint:"))
        self.endpoint = QLineEdit(DEFAULT_ENDPOINT)
        self.endpoint.setPlaceholderText("Default GitHub Models endpoint")
        self.endpoint.textChanged.connect(self.on_settings_changed)
        endpoint_layout.addWidget(self.endpoint)
        api_layout.addLayout(endpoint_layout)
        
        layout.addWidget(api_group)
        
        # Scoring configuration group
        scoring_group = QGroupBox("Scoring Configuration")
        scoring_layout = QVBoxLayout(scoring_group)
        
        # Scoring threshold
        threshold_layout = QVBoxLayout()
        threshold_label_layout = QHBoxLayout()
        threshold_label_layout.addWidget(QLabel("Min Score Threshold:"))
        self.threshold_value = QLabel("6.0")
        threshold_label_layout.addWidget(self.threshold_value)
        threshold_label_layout.addStretch()
        threshold_layout.addLayout(threshold_label_layout)
        
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setMinimum(0)
        self.threshold_slider.setMaximum(100)
        self.threshold_slider.setValue(60)  # 6.0
        self.threshold_slider.valueChanged.connect(self.on_threshold_changed)
        threshold_layout.addWidget(self.threshold_slider)
        
        scoring_layout.addLayout(threshold_layout)
        
        # Temperature
        temp_layout = QVBoxLayout()
        temp_label_layout = QHBoxLayout()
        temp_label_layout.addWidget(QLabel("Temperature:"))
        self.temp_value = QLabel("0.2")
        temp_label_layout.addWidget(self.temp_value)
        temp_label_layout.addStretch()
        temp_layout.addLayout(temp_label_layout)
        
        self.temp_slider = QSlider(Qt.Horizontal)
        self.temp_slider.setMinimum(0)
        self.temp_slider.setMaximum(20)
        self.temp_slider.setValue(2)  # 0.2
        self.temp_slider.valueChanged.connect(self.on_temp_changed)
        temp_layout.addWidget(self.temp_slider)
        
        scoring_layout.addLayout(temp_layout)
        
        # Max segments
        max_segments_layout = QHBoxLayout()
        max_segments_layout.addWidget(QLabel("Max Segments to Score:"))
        self.max_segments = QLineEdit("50")
        self.max_segments.setMaximumWidth(100)
        self.max_segments.textChanged.connect(self.on_settings_changed)
        max_segments_layout.addWidget(self.max_segments)
        max_segments_layout.addStretch()
        scoring_layout.addLayout(max_segments_layout)
        
        # Batch size
        batch_size_layout = QHBoxLayout()
        batch_size_layout.addWidget(QLabel("Batch Size:"))
        self.batch_size = QLineEdit("6")
        self.batch_size.setMaximumWidth(100)
        self.batch_size.textChanged.connect(self.on_settings_changed)
        batch_size_layout.addWidget(self.batch_size)
        batch_size_layout.addStretch()
        scoring_layout.addLayout(batch_size_layout)
        
        layout.addWidget(scoring_group)
        
        # Spacer
        layout.addStretch()
    
    def on_threshold_changed(self, value):
        """Handle threshold slider change."""
        threshold = value / 10.0
        self.threshold_value.setText(f"{threshold:.1f}")
        self.on_settings_changed()
    
    def on_temp_changed(self, value):
        """Handle temperature slider change."""
        temp = value / 10.0
        self.temp_value.setText(f"{temp:.1f}")
        self.on_settings_changed()
    
    def on_settings_changed(self):
        """Emit settings changed signal."""
        settings = self.get_settings()
        self.settings_changed.emit(settings)
    
    def get_settings(self) -> dict:
        """Get current AI settings."""
        try:
            max_segments = int(self.max_segments.text())
        except ValueError:
            max_segments = 50
        
        try:
            batch_size = int(self.batch_size.text())
        except ValueError:
            batch_size = 6
        
        return {
            'model_name': self.model_name.text(),
            'endpoint': self.endpoint.text(),
            'temperature': self.temp_slider.value() / 10.0,
            'min_score_threshold': self.threshold_slider.value() / 10.0,
            'max_segments_to_score': max_segments,
            'batch_size': batch_size
        }
    
    def set_settings(self, settings: dict):
        """Set AI settings from config."""
        if 'model_name' in settings:
            self.model_name.setText(settings['model_name'])
        
        if 'endpoint' in settings:
            self.endpoint.setText(settings['endpoint'])
        
        if 'temperature' in settings:
            temp = int(settings['temperature'] * 10)
            self.temp_slider.setValue(temp)
            self.temp_value.setText(f"{settings['temperature']:.1f}")
        
        if 'min_score_threshold' in settings:
            threshold = int(settings['min_score_threshold'] * 10)
            self.threshold_slider.setValue(threshold)
            self.threshold_value.setText(f"{settings['min_score_threshold']:.1f}")
        
        if 'max_segments_to_score' in settings:
            self.max_segments.setText(str(settings['max_segments_to_score']))
        
        if 'batch_size' in settings:
            self.batch_size.setText(str(settings['batch_size']))
