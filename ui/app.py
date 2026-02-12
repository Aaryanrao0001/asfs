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
        # Check dependencies before starting
        from validator.dependencies import check_all_dependencies, get_dependency_status_message
        
        logger.info("Checking dependencies...")
        dependencies = check_all_dependencies()
        
        # Log dependency status
        for name, (available, message) in dependencies.items():
            if available:
                logger.info(f"✓ {name}: {message}")
            else:
                logger.warning(f"✗ {name}: {message}")
        
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
