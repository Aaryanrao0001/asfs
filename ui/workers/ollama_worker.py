"""
Ollama Worker - Background thread for Ollama operations.
"""

import logging
from PySide6.QtCore import QThread, Signal
from ai.ollama_manager import get_ollama_manager

logger = logging.getLogger(__name__)


class OllamaWorker(QThread):
    """Worker thread for Ollama server and model operations."""
    
    # Signals
    operation_complete = Signal(bool, str)  # success, message
    status_update = Signal(dict)  # status dictionary
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = get_ollama_manager()
        self.operation = None
        self.model_name = None
    
    def start_server(self):
        """Queue server start operation."""
        self.operation = "start"
        self.start()
    
    def stop_server(self):
        """Queue server stop operation."""
        self.operation = "stop"
        self.start()
    
    def load_model(self, model_name: str):
        """Queue model load operation."""
        self.operation = "load"
        self.model_name = model_name
        self.start()
    
    def check_status(self):
        """Queue status check operation."""
        self.operation = "status"
        self.start()
    
    def run(self):
        """Execute the queued operation."""
        try:
            if self.operation == "start":
                logger.info("Starting Ollama server...")
                success, message = self.manager.start_server()
                self.operation_complete.emit(success, message)
            
            elif self.operation == "stop":
                logger.info("Stopping Ollama server...")
                success, message = self.manager.stop_server()
                self.operation_complete.emit(success, message)
            
            elif self.operation == "load":
                logger.info(f"Loading model: {self.model_name}")
                success, message = self.manager.load_model(self.model_name)
                self.operation_complete.emit(success, message)
            
            elif self.operation == "status":
                status = self.manager.get_status()
                self.status_update.emit(status)
            
        except Exception as e:
            logger.error(f"Ollama worker error: {str(e)}")
            self.operation_complete.emit(False, f"Error: {str(e)}")
        
        finally:
            self.operation = None
            self.model_name = None
