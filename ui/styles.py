"""
Dark theme stylesheet for ASFS desktop application.
"""

DARK_THEME = """
QWidget {
    background-color: #1e1e1e;
    color: #d4d4d4;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 10pt;
}

QMainWindow {
    background-color: #1e1e1e;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #3e3e3e;
    background-color: #252525;
}

QTabBar::tab {
    background-color: #2d2d2d;
    color: #d4d4d4;
    padding: 8px 16px;
    margin-right: 2px;
    border: 1px solid #3e3e3e;
    border-bottom: none;
}

QTabBar::tab:selected {
    background-color: #0e639c;
    color: #ffffff;
}

QTabBar::tab:hover {
    background-color: #3e3e3e;
}

/* Buttons */
QPushButton {
    background-color: #0e639c;
    color: #ffffff;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
}

QPushButton:hover {
    background-color: #1177bb;
}

QPushButton:pressed {
    background-color: #0d5689;
}

QPushButton:disabled {
    background-color: #3e3e3e;
    color: #7f7f7f;
}

/* Secondary Buttons */
QPushButton[secondary="true"] {
    background-color: #3e3e3e;
    color: #d4d4d4;
}

QPushButton[secondary="true"]:hover {
    background-color: #4e4e4e;
}

/* Danger Buttons */
QPushButton[danger="true"] {
    background-color: #c42b1c;
    color: #ffffff;
}

QPushButton[danger="true"]:hover {
    background-color: #e03e2d;
}

/* Text Inputs */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #2d2d2d;
    color: #d4d4d4;
    border: 1px solid #3e3e3e;
    padding: 6px;
    border-radius: 4px;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #0e639c;
}

/* Combo Box */
QComboBox {
    background-color: #2d2d2d;
    color: #d4d4d4;
    border: 1px solid #3e3e3e;
    padding: 6px;
    border-radius: 4px;
}

QComboBox:hover {
    border: 1px solid #4e4e4e;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox QAbstractItemView {
    background-color: #2d2d2d;
    color: #d4d4d4;
    selection-background-color: #0e639c;
    border: 1px solid #3e3e3e;
}

/* Checkboxes */
QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #3e3e3e;
    border-radius: 3px;
    background-color: #2d2d2d;
}

QCheckBox::indicator:checked {
    background-color: #0e639c;
    border: 1px solid #0e639c;
}

QCheckBox::indicator:hover {
    border: 1px solid #4e4e4e;
}

/* Sliders */
QSlider::groove:horizontal {
    border: 1px solid #3e3e3e;
    height: 6px;
    background: #2d2d2d;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #0e639c;
    border: 1px solid #0e639c;
    width: 16px;
    margin: -6px 0;
    border-radius: 8px;
}

QSlider::handle:horizontal:hover {
    background: #1177bb;
}

/* Labels */
QLabel {
    color: #d4d4d4;
}

QLabel[heading="true"] {
    font-size: 12pt;
    font-weight: bold;
    color: #ffffff;
    padding: 4px 0px;
}

QLabel[subheading="true"] {
    font-size: 10pt;
    font-weight: bold;
    color: #b4b4b4;
}

/* Group Boxes */
QGroupBox {
    border: 1px solid #3e3e3e;
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 12px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 4px 8px;
    color: #ffffff;
    font-weight: bold;
}

/* Scroll Bars */
QScrollBar:vertical {
    background-color: #2d2d2d;
    width: 12px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #4e4e4e;
    min-height: 20px;
    border-radius: 6px;
}

QScrollBar::handle:vertical:hover {
    background-color: #5e5e5e;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #2d2d2d;
    height: 12px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background-color: #4e4e4e;
    min-width: 20px;
    border-radius: 6px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #5e5e5e;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Progress Bar */
QProgressBar {
    border: 1px solid #3e3e3e;
    border-radius: 4px;
    text-align: center;
    background-color: #2d2d2d;
}

QProgressBar::chunk {
    background-color: #0e639c;
    border-radius: 3px;
}

/* Status Indicator */
QLabel[status="running"] {
    color: #4ec9b0;
    font-weight: bold;
}

QLabel[status="stopped"] {
    color: #7f7f7f;
    font-weight: bold;
}

QLabel[status="error"] {
    color: #f48771;
    font-weight: bold;
}

QLabel[status="success"] {
    color: #4ec9b0;
    font-weight: bold;
}
"""
