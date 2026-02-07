"""
AI/Model Settings Tab - Ollama controls and AI configuration.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QSlider, QGroupBox
)
from PySide6.QtCore import Signal, Qt, QTimer


class AITab(QWidget):
    """Tab for AI model and Ollama management."""
    
    # Signals
    start_ollama_clicked = Signal()
    stop_ollama_clicked = Signal()
    load_model_clicked = Signal(str)  # Model name
    settings_changed = Signal(dict)  # All AI settings
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
        # Timer for status updates
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.request_status_update)
        self.status_timer.start(3000)  # Update every 3 seconds
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Title
        title = QLabel("AI & Model Settings")
        title.setProperty("heading", True)
        layout.addWidget(title)
        
        # Ollama controls group
        ollama_group = QGroupBox("Ollama Local LLM")
        ollama_layout = QVBoxLayout(ollama_group)
        
        # Status display
        status_h_layout = QHBoxLayout()
        status_h_layout.addWidget(QLabel("Server Status:"))
        self.ollama_status = QLabel("Unknown")
        self.ollama_status.setProperty("status", "stopped")
        status_h_layout.addWidget(self.ollama_status)
        status_h_layout.addStretch()
        ollama_layout.addLayout(status_h_layout)
        
        # Model status
        model_status_h_layout = QHBoxLayout()
        model_status_h_layout.addWidget(QLabel("Model Status:"))
        self.model_status = QLabel("Unknown")
        self.model_status.setProperty("status", "stopped")
        model_status_h_layout.addWidget(self.model_status)
        model_status_h_layout.addStretch()
        ollama_layout.addLayout(model_status_h_layout)
        
        # Control buttons
        buttons_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Start Ollama")
        self.start_btn.clicked.connect(self.on_start_clicked)
        buttons_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop Ollama")
        self.stop_btn.setProperty("secondary", True)
        self.stop_btn.clicked.connect(self.on_stop_clicked)
        self.stop_btn.setEnabled(False)
        buttons_layout.addWidget(self.stop_btn)
        
        self.load_model_btn = QPushButton("Load Model")
        self.load_model_btn.clicked.connect(self.on_load_model_clicked)
        self.load_model_btn.setEnabled(False)
        buttons_layout.addWidget(self.load_model_btn)
        
        buttons_layout.addStretch()
        ollama_layout.addLayout(buttons_layout)
        
        layout.addWidget(ollama_group)
        
        # Model configuration group
        model_group = QGroupBox("Model Configuration")
        model_layout = QVBoxLayout(model_group)
        
        # Model name
        model_name_layout = QHBoxLayout()
        model_name_layout.addWidget(QLabel("Model Name:"))
        self.model_name = QLineEdit("qwen2.5:3b-instruct")
        self.model_name.textChanged.connect(self.on_settings_changed)
        model_name_layout.addWidget(self.model_name)
        model_layout.addLayout(model_name_layout)
        
        # LLM backend selector
        backend_layout = QHBoxLayout()
        backend_layout.addWidget(QLabel("LLM Backend:"))
        self.backend_selector = QComboBox()
        self.backend_selector.addItems(["auto", "local", "api"])
        self.backend_selector.setCurrentText("auto")
        self.backend_selector.currentTextChanged.connect(self.on_settings_changed)
        backend_layout.addWidget(self.backend_selector)
        backend_layout.addStretch()
        model_layout.addLayout(backend_layout)
        
        layout.addWidget(model_group)
        
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
        
        layout.addWidget(scoring_group)
        
        # Spacer
        layout.addStretch()
    
    def on_start_clicked(self):
        """Handle start Ollama button click."""
        self.start_ollama_clicked.emit()
    
    def on_stop_clicked(self):
        """Handle stop Ollama button click."""
        self.stop_ollama_clicked.emit()
    
    def on_load_model_clicked(self):
        """Handle load model button click."""
        model = self.model_name.text()
        self.load_model_clicked.emit(model)
    
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
    
    def request_status_update(self):
        """Request parent to update status (called by timer)."""
        # This will be connected to a slot in the main window
        pass
    
    def update_ollama_status(self, running: bool, model_loaded: bool):
        """Update Ollama and model status display."""
        if running:
            self.ollama_status.setText("Running")
            self.ollama_status.setProperty("status", "running")
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.load_model_btn.setEnabled(True)
        else:
            self.ollama_status.setText("Not Running")
            self.ollama_status.setProperty("status", "stopped")
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.load_model_btn.setEnabled(False)
        
        if model_loaded:
            self.model_status.setText("Loaded")
            self.model_status.setProperty("status", "success")
        else:
            self.model_status.setText("Not Loaded")
            self.model_status.setProperty("status", "stopped")
        
        # Refresh style
        self.ollama_status.style().unpolish(self.ollama_status)
        self.ollama_status.style().polish(self.ollama_status)
        self.model_status.style().unpolish(self.model_status)
        self.model_status.style().polish(self.model_status)
    
    def get_settings(self) -> dict:
        """Get all AI settings."""
        return {
            "model_name": self.model_name.text(),
            "backend": self.backend_selector.currentText(),
            "threshold": float(self.threshold_value.text()),
            "temperature": float(self.temp_value.text())
        }
    
    def set_settings(self, settings: dict):
        """Set AI settings from dictionary."""
        if "model_name" in settings:
            self.model_name.setText(settings["model_name"])
        if "backend" in settings:
            self.backend_selector.setCurrentText(settings["backend"])
        if "threshold" in settings:
            value = int(settings["threshold"] * 10)
            self.threshold_slider.setValue(value)
        if "temperature" in settings:
            value = int(settings["temperature"] * 10)
            self.temp_slider.setValue(value)
