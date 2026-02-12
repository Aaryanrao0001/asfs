"""
Luxury dark theme stylesheet for ASFS desktop application.
Modern, sophisticated design with premium aesthetics.
"""

DARK_THEME = """
/* ============================================
   GLOBAL STYLES
   ============================================ */
QWidget {
    background-color: #0f0f0f;
    color: #e5e5e5;
    font-family: 'Inter', 'SF Pro Display', 'Segoe UI Variable', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 14pt;
    font-weight: 400;
    selection-background-color: #3b82f6;
    selection-color: #ffffff;
}

QMainWindow {
    background-color: #0a0a0a;
}

/* ============================================
   TAB WIDGET - Modern with Gradient Indicators
   ============================================ */
QTabWidget::pane {
    border: 1px solid #2a2a2a;
    background-color: #1a1a1a;
    border-radius: 8px;
    padding: 4px;
}

QTabBar {
    background-color: transparent;
}

QTabBar::tab {
    background-color: transparent;
    color: #a0a0a0;
    padding: 14px 24px;
    margin-right: 4px;
    border: none;
    border-bottom: 3px solid transparent;
    font-size: 14pt;
    font-weight: 500;
    min-width: 100px;
}

QTabBar::tab:selected {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                               stop:0 rgba(59, 130, 246, 0.1),
                               stop:1 rgba(139, 92, 246, 0.05));
    color: #ffffff;
    border-bottom: 3px solid qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #3b82f6,
                                            stop:1 #8b5cf6);
    font-weight: 600;
}

QTabBar::tab:hover:!selected {
    background-color: rgba(255, 255, 255, 0.05);
    color: #e5e5e5;
    border-bottom: 3px solid rgba(59, 130, 246, 0.3);
}

/* ============================================
   BUTTONS - Large, Comfortable with Gradients
   ============================================ */
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                               stop:0 #3b82f6,
                               stop:1 #2563eb);
    color: #ffffff;
    border: none;
    padding: 14px 20px;
    border-radius: 8px;
    font-size: 14pt;
    font-weight: 600;
    min-height: 44px;
    min-width: 100px;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                               stop:0 #60a5fa,
                               stop:1 #3b82f6);
}

QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                               stop:0 #2563eb,
                               stop:1 #1d4ed8);
    padding: 15px 19px 13px 21px;
}

QPushButton:disabled {
    background-color: #2a2a2a;
    color: #6b6b6b;
}

/* Secondary Buttons - Subtle with Depth */
QPushButton[secondary="true"] {
    background-color: #242424;
    color: #e5e5e5;
    border: 1px solid #333333;
    font-weight: 500;
}

QPushButton[secondary="true"]:hover {
    background-color: #2d2d2d;
    border: 1px solid #404040;
}

QPushButton[secondary="true"]:pressed {
    background-color: #1f1f1f;
    border: 1px solid #2a2a2a;
}

/* Danger Buttons - Bold Warning Colors */
QPushButton[danger="true"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                               stop:0 #ef4444,
                               stop:1 #dc2626);
    color: #ffffff;
    font-weight: 600;
}

QPushButton[danger="true"]:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                               stop:0 #f87171,
                               stop:1 #ef4444);
}

QPushButton[danger="true"]:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                               stop:0 #dc2626,
                               stop:1 #b91c1c);
}

/* ============================================
   TEXT INPUTS - Large, Clear with Glow Focus
   ============================================ */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #1a1a1a;
    color: #e5e5e5;
    border: 2px solid #2a2a2a;
    padding: 12px 16px;
    border-radius: 8px;
    font-size: 14pt;
    min-height: 40px;
    selection-background-color: #3b82f6;
}

QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover {
    border: 2px solid #333333;
    background-color: #1f1f1f;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 2px solid #3b82f6;
    background-color: #1a1a1a;
}

QLineEdit[readOnly="true"] {
    background-color: #161616;
    color: #a0a0a0;
    border: 2px solid #242424;
}

/* Placeholder Text */
QLineEdit::placeholder, QTextEdit::placeholder, QPlainTextEdit::placeholder {
    color: #6b6b6b;
}

/* ============================================
   COMBO BOX - Polished Dropdown
   ============================================ */
QComboBox {
    background-color: #1a1a1a;
    color: #e5e5e5;
    border: 2px solid #2a2a2a;
    padding: 12px 16px;
    border-radius: 8px;
    font-size: 14pt;
    min-height: 40px;
}

QComboBox:hover {
    border: 2px solid #333333;
    background-color: #1f1f1f;
}

QComboBox:focus {
    border: 2px solid #3b82f6;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
    padding-right: 10px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #e5e5e5;
    margin-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #1f1f1f;
    color: #e5e5e5;
    selection-background-color: #3b82f6;
    selection-color: #ffffff;
    border: 1px solid #333333;
    border-radius: 8px;
    padding: 4px;
    outline: none;
}

QComboBox QAbstractItemView::item {
    padding: 10px 16px;
    border-radius: 6px;
    min-height: 32px;
}

QComboBox QAbstractItemView::item:hover {
    background-color: rgba(59, 130, 246, 0.2);
}

/* ============================================
   CHECKBOXES & RADIO BUTTONS - Modern Style
   ============================================ */
QCheckBox, QRadioButton {
    spacing: 10px;
    color: #e5e5e5;
    font-size: 14pt;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 20px;
    height: 20px;
    border: 2px solid #404040;
    border-radius: 5px;
    background-color: #1a1a1a;
}

QRadioButton::indicator {
    border-radius: 10px;
}

QCheckBox::indicator:hover, QRadioButton::indicator:hover {
    border: 2px solid #4a4a4a;
    background-color: #1f1f1f;
}

QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                               stop:0 #3b82f6,
                               stop:1 #2563eb);
    border: 2px solid #3b82f6;
}

QCheckBox::indicator:checked:hover, QRadioButton::indicator:checked:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                               stop:0 #60a5fa,
                               stop:1 #3b82f6);
}

/* ============================================
   SLIDERS - Smooth & Premium
   ============================================ */
QSlider::groove:horizontal {
    border: none;
    height: 8px;
    background: #242424;
    border-radius: 4px;
}

QSlider::handle:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                               stop:0 #3b82f6,
                               stop:1 #2563eb);
    border: 2px solid #1e40af;
    width: 20px;
    height: 20px;
    margin: -7px 0;
    border-radius: 10px;
}

QSlider::handle:horizontal:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                               stop:0 #60a5fa,
                               stop:1 #3b82f6);
}

QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                               stop:0 #3b82f6,
                               stop:1 #2563eb);
    border-radius: 4px;
}

/* ============================================
   LABELS - Clear Hierarchy
   ============================================ */
QLabel {
    color: #e5e5e5;
    background-color: transparent;
}

QLabel[heading="true"] {
    font-size: 20pt;
    font-weight: 700;
    color: #ffffff;
    padding: 8px 0px;
    letter-spacing: -0.5px;
}

QLabel[subheading="true"] {
    font-size: 13pt;
    font-weight: 500;
    color: #a0a0a0;
    padding: 4px 0px;
}

/* ============================================
   GROUP BOXES - Glassmorphic Containers
   ============================================ */
QGroupBox {
    border: 1px solid #2a2a2a;
    border-radius: 12px;
    margin-top: 20px;
    padding-top: 24px;
    padding: 24px;
    background-color: rgba(26, 26, 26, 0.8);
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 8px 16px;
    color: #ffffff;
    font-weight: 700;
    font-size: 15pt;
    background-color: transparent;
    border-radius: 6px;
}

/* ============================================
   SCROLL BARS - Minimal & Smooth
   ============================================ */
QScrollBar:vertical {
    background-color: transparent;
    width: 14px;
    margin: 2px;
}

QScrollBar::handle:vertical {
    background-color: rgba(80, 80, 80, 0.6);
    min-height: 30px;
    border-radius: 7px;
}

QScrollBar::handle:vertical:hover {
    background-color: rgba(100, 100, 100, 0.8);
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

QScrollBar:horizontal {
    background-color: transparent;
    height: 14px;
    margin: 2px;
}

QScrollBar::handle:horizontal {
    background-color: rgba(80, 80, 80, 0.6);
    min-width: 30px;
    border-radius: 7px;
}

QScrollBar::handle:horizontal:hover {
    background-color: rgba(100, 100, 100, 0.8);
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
}

/* ============================================
   PROGRESS BAR - Gradient with Glow
   ============================================ */
QProgressBar {
    border: 1px solid #2a2a2a;
    border-radius: 8px;
    text-align: center;
    background-color: #1a1a1a;
    color: #ffffff;
    font-weight: 600;
    font-size: 13pt;
    min-height: 32px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                               stop:0 #3b82f6,
                               stop:1 #8b5cf6);
    border-radius: 7px;
}

/* ============================================
   STATUS INDICATORS - Vibrant Colors
   ============================================ */
QLabel[status="running"] {
    color: #10b981;
    font-weight: 700;
    font-size: 14pt;
}

QLabel[status="stopped"] {
    color: #6b6b6b;
    font-weight: 700;
    font-size: 14pt;
}

QLabel[status="error"] {
    color: #ef4444;
    font-weight: 700;
    font-size: 14pt;
}

QLabel[status="success"] {
    color: #10b981;
    font-weight: 700;
    font-size: 14pt;
}

/* ============================================
   TOOLTIPS - Elegant Popups
   ============================================ */
QToolTip {
    background-color: #1f1f1f;
    color: #e5e5e5;
    border: 1px solid #333333;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13pt;
}

/* ============================================
   MESSAGE BOX - Premium Dialogs
   ============================================ */
QMessageBox {
    background-color: #1a1a1a;
}

QMessageBox QLabel {
    color: #e5e5e5;
    font-size: 14pt;
    min-width: 300px;
}

QMessageBox QPushButton {
    min-width: 80px;
    padding: 12px 20px;
}

/* ============================================
   SPIN BOX - Number Inputs
   ============================================ */
QSpinBox, QDoubleSpinBox {
    background-color: #1a1a1a;
    color: #e5e5e5;
    border: 2px solid #2a2a2a;
    padding: 12px 16px;
    border-radius: 8px;
    font-size: 14pt;
    min-height: 40px;
}

QSpinBox:hover, QDoubleSpinBox:hover {
    border: 2px solid #333333;
    background-color: #1f1f1f;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border: 2px solid #3b82f6;
}

QSpinBox::up-button, QDoubleSpinBox::up-button {
    background-color: #242424;
    border-left: 1px solid #2a2a2a;
    border-top-right-radius: 6px;
    width: 20px;
}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {
    background-color: #2d2d2d;
}

QSpinBox::down-button, QDoubleSpinBox::down-button {
    background-color: #242424;
    border-left: 1px solid #2a2a2a;
    border-bottom-right-radius: 6px;
    width: 20px;
}

QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #2d2d2d;
}

/* ============================================
   MENU & CONTEXT MENU - Sleek Menus
   ============================================ */
QMenu {
    background-color: #1f1f1f;
    border: 1px solid #333333;
    border-radius: 8px;
    padding: 4px;
}

QMenu::item {
    padding: 10px 20px;
    border-radius: 6px;
    color: #e5e5e5;
    font-size: 14pt;
}

QMenu::item:selected {
    background-color: #3b82f6;
    color: #ffffff;
}

QMenu::separator {
    height: 1px;
    background-color: #2a2a2a;
    margin: 4px 10px;
}
"""
