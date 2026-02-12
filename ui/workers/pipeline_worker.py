"""
Pipeline Worker - Background thread for running the video processing pipeline.
"""

import logging
import sys
from io import StringIO
from PySide6.QtCore import QThread, Signal

logger = logging.getLogger(__name__)


class PipelineWorker(QThread):
    """Worker thread for executing the video processing pipeline."""
    
    # Signals
    log_message = Signal(str)  # Log messages
    progress_update = Signal(int, int, str)  # current_stage, total_stages, stage_name
    finished = Signal(bool)  # success
    error_occurred = Signal(str)  # error_message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_path = None
        self.output_dir = None
        self.config = {}
        self.use_cache = True  # Default to using cache
        self.should_stop = False
    
    def configure(self, video_path: str, output_dir: str, config: dict, use_cache: bool = True):
        """
        Configure the pipeline parameters.
        
        Args:
            video_path: Path to input video
            output_dir: Output directory
            config: Configuration dictionary with all settings
            use_cache: Whether to use cached results (default: True)
        """
        self.video_path = video_path
        self.output_dir = output_dir
        self.config = config
        self.use_cache = use_cache
    
    def stop(self):
        """Signal the worker to stop."""
        self.should_stop = True
    
    def run(self):
        """Execute the pipeline in a background thread."""
        try:
            self.should_stop = False
            self.log_message.emit("=" * 80)
            self.log_message.emit("STARTING PIPELINE")
            self.log_message.emit("=" * 80)
            self.log_message.emit(f"Video: {self.video_path}")
            self.log_message.emit(f"Output: {self.output_dir}")
            self.log_message.emit("")
            
            # Import pipeline function
            # We'll import here to avoid circular dependencies and to capture output
            from pipeline import run_pipeline
            
            # Create a custom logging handler to capture logs
            log_capture = LogCapture(self.log_message)
            logging.getLogger().addHandler(log_capture)
            
            # Update pipeline config from UI settings
            # This will be passed to the pipeline execution
            # For now, we'll call the existing run_pipeline function
            # In a full implementation, we'd modify run_pipeline to accept these configs
            
            try:
                # Run the pipeline
                # Note: This will run in the thread's context
                run_pipeline(
                    video_path=self.video_path,
                    output_dir=self.output_dir,
                    use_cache=self.use_cache
                )
                
                if not self.should_stop:
                    self.log_message.emit("\n" + "=" * 80)
                    self.log_message.emit("PIPELINE COMPLETED SUCCESSFULLY")
                    self.log_message.emit("=" * 80)
                    self.finished.emit(True)
                else:
                    self.log_message.emit("\n" + "=" * 80)
                    self.log_message.emit("PIPELINE STOPPED BY USER")
                    self.log_message.emit("=" * 80)
                    self.finished.emit(False)
                
            except Exception as e:
                error_msg = f"Pipeline error: {str(e)}"
                logger.error(error_msg)
                self.error_occurred.emit(error_msg)
                self.finished.emit(False)
            
            finally:
                # Remove the log handler
                logging.getLogger().removeHandler(log_capture)
        
        except Exception as e:
            error_msg = f"Worker error: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            self.finished.emit(False)


class LogCapture(logging.Handler):
    """Custom logging handler to capture logs and emit them as Qt signals."""
    
    def __init__(self, signal):
        super().__init__()
        self.signal = signal
        
        # Set format
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.setFormatter(formatter)
    
    def emit(self, record):
        """Emit log record to Qt signal."""
        try:
            msg = self.format(record)
            self.signal.emit(msg)
        except Exception:
            # Silently fail if signal emission fails
            pass
