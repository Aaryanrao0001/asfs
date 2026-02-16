"""
Application entry point for ASFS desktop UI.
"""

import sys
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from .main_window import MainWindow
from .styles import DARK_THEME

# Configure logging with UTF-8 encoding support
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('asfs_ui.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Configure StreamHandler to use UTF-8 encoding to support Unicode characters on Windows
for handler in logging.root.handlers:
    if isinstance(handler, logging.StreamHandler) and hasattr(handler.stream, 'reconfigure'):
        try:
            handler.stream.reconfigure(encoding='utf-8', errors='replace')
        except Exception as e:
            # If reconfigure fails, log the issue and continue with default encoding
            # This is expected on some older Python versions or non-standard streams
            logging.getLogger(__name__).debug(f"Could not reconfigure stream encoding: {e}")

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
        # Check dependencies before starting
        from validator.dependencies import check_all_dependencies, get_dependency_status_message
        
        logger.info("Checking dependencies...")
        dependencies = check_all_dependencies()
        
        # Log dependency status (using ASCII chars for Windows compatibility)
        for name, (available, message) in dependencies.items():
            if available:
                logger.info(f"[OK] {name}: {message}")
            else:
                logger.warning(f"[MISSING] {name}: {message}")
        
        app = create_app()
        
        # Create and show main window
        window = MainWindow()
        
        # Show dependency warnings if any are missing
        missing = [name for name, (available, _) in dependencies.items() if not available]
        if missing:
            from PySide6.QtWidgets import QMessageBox
            from validator.dependencies import get_installation_instructions
            
            warning_msg = "Some dependencies are missing:\n\n"
            for dep in missing:
                warning_msg += f"• {dep}\n"
            
            warning_msg += "\nThe application will start, but some features may not work properly.\n\n"
            warning_msg += "See the log file (asfs_ui.log) for installation instructions."
            
            QMessageBox.warning(
                window,
                "Missing Dependencies",
                warning_msg
            )
            
            # Log installation instructions
            for dep in missing:
                logger.info(get_installation_instructions(dep))
        
        window.show()
        
        logger.info("Application started successfully")
        
        # Run event loop
        return app.exec()
    
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == '__main__':
    sys.exit(run_app())
