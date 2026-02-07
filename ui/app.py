"""
Application entry point for ASFS desktop UI.
"""

import sys
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from .main_window import MainWindow
from .styles import DARK_THEME

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('asfs_ui.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def create_app():
    """Create and configure the QApplication."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("ASFS")
    app.setOrganizationName("ASFS")
    app.setApplicationVersion("2.0.0")
    
    # Apply dark theme
    app.setStyleSheet(DARK_THEME)
    
    return app


def run_app():
    """Run the ASFS desktop application."""
    logger.info("=" * 80)
    logger.info("ASFS - Automated Short-Form Content System")
    logger.info("Desktop Application v2.0.0")
    logger.info("=" * 80)
    
    try:
        app = create_app()
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        logger.info("Application started successfully")
        
        # Run event loop
        return app.exec()
    
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        return 1


if __name__ == '__main__':
    sys.exit(run_app())
