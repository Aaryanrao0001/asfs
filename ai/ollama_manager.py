"""
Ollama Manager - Process management and status for local LLM inference.

Provides controls for:
- Starting/stopping Ollama server
- Loading/checking models
- Health monitoring
"""

import os
import sys
import subprocess
import logging
import time
import requests
from typing import Optional, Tuple, List
from pathlib import Path

logger = logging.getLogger(__name__)


class OllamaManager:
    """Manage Ollama server process and model operations."""
    
    def __init__(self, endpoint: str = "http://localhost:11434", model_name: str = "qwen2.5:3b-instruct"):
        """
        Initialize Ollama manager.
        
        Args:
            endpoint: Ollama API endpoint (default: http://localhost:11434)
            model_name: Default model to load (default: qwen2.5:3b-instruct)
        """
        self.endpoint = endpoint
        self.model_name = model_name
        self.process: Optional[subprocess.Popen] = None
        self._last_health_check = 0
        self._health_cache = False
        self._health_cache_duration = 2.0  # seconds
        
    def is_running(self, force_check: bool = False) -> bool:
        """
        Check if Ollama server is running.
        
        Args:
            force_check: Force immediate check, bypass cache
            
        Returns:
            True if Ollama is running and responding to health checks
        """
        # Use cached result if recent
        now = time.time()
        if not force_check and (now - self._last_health_check) < self._health_cache_duration:
            return self._health_cache
        
        try:
            response = requests.get(f"{self.endpoint}/", timeout=2)
            is_running = response.status_code == 200
            
            # Update cache
            self._last_health_check = now
            self._health_cache = is_running
            
            return is_running
        except (requests.RequestException, Exception):
            self._last_health_check = now
            self._health_cache = False
            return False
    
    def start_server(self) -> Tuple[bool, str]:
        """
        Start Ollama server as a subprocess.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        # Check if already running
        if self.is_running(force_check=True):
            return True, "Ollama is already running"
        
        # Check if process object exists and is still alive
        if self.process and self.process.poll() is None:
            return True, "Ollama process already started from this manager"
        
        try:
            # Find Ollama executable
            ollama_cmd = self._find_ollama_executable()
            if not ollama_cmd:
                return False, "Ollama executable not found. Please install Ollama from https://ollama.ai"
            
            logger.info(f"Starting Ollama server: {ollama_cmd}")
            
            # Start Ollama server as a background process
            # On Windows, use CREATE_NO_WINDOW flag to hide console
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                
                self.process = subprocess.Popen(
                    [ollama_cmd, "serve"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    startupinfo=startupinfo,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                self.process = subprocess.Popen(
                    [ollama_cmd, "serve"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            
            # Wait for server to start (up to 10 seconds)
            for i in range(20):
                time.sleep(0.5)
                if self.is_running(force_check=True):
                    logger.info("Ollama server started successfully")
                    return True, "Ollama server started successfully"
            
            # Server didn't start in time
            self.stop_server()
            return False, "Ollama server failed to start (timeout)"
            
        except FileNotFoundError:
            return False, "Ollama executable not found. Please install Ollama from https://ollama.ai"
        except Exception as e:
            logger.error(f"Failed to start Ollama: {str(e)}")
            return False, f"Failed to start Ollama: {str(e)}"
    
    def stop_server(self) -> Tuple[bool, str]:
        """
        Stop Ollama server process.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.process:
            return True, "No Ollama process to stop (managed externally or not started)"
        
        try:
            # Terminate the process
            self.process.terminate()
            
            # Wait for clean shutdown (up to 5 seconds)
            try:
                self.process.wait(timeout=5)
                logger.info("Ollama server stopped successfully")
                return True, "Ollama server stopped successfully"
            except subprocess.TimeoutExpired:
                # Force kill if graceful shutdown failed
                self.process.kill()
                self.process.wait()
                logger.warning("Ollama server force killed")
                return True, "Ollama server force stopped"
                
        except Exception as e:
            logger.error(f"Failed to stop Ollama: {str(e)}")
            return False, f"Failed to stop Ollama: {str(e)}"
        finally:
            self.process = None
    
    def load_model(self, model_name: Optional[str] = None) -> Tuple[bool, str]:
        """
        Load (pull) a model from Ollama registry.
        
        Args:
            model_name: Model to load (default: use configured model)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        model = model_name or self.model_name
        
        # Check if server is running
        if not self.is_running(force_check=True):
            return False, "Ollama server is not running. Please start it first."
        
        try:
            # Find Ollama executable
            ollama_cmd = self._find_ollama_executable()
            if not ollama_cmd:
                return False, "Ollama executable not found"
            
            logger.info(f"Loading model: {model}")
            
            # Pull the model
            # Note: This is a blocking operation that can take time
            result = subprocess.run(
                [ollama_cmd, "pull", model],
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout for large models
            )
            
            if result.returncode == 0:
                logger.info(f"Model {model} loaded successfully")
                return True, f"Model {model} loaded successfully"
            else:
                error_msg = result.stderr or result.stdout or "Unknown error"
                logger.error(f"Failed to load model: {error_msg}")
                return False, f"Failed to load model: {error_msg}"
                
        except subprocess.TimeoutExpired:
            return False, f"Model loading timed out (>10 minutes). Check your network connection."
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            return False, f"Failed to load model: {str(e)}"
    
    def is_model_loaded(self, model_name: Optional[str] = None) -> bool:
        """
        Check if a model is loaded/available locally.
        
        Args:
            model_name: Model to check (default: use configured model)
            
        Returns:
            True if model is loaded
        """
        model = model_name or self.model_name
        
        try:
            # Find Ollama executable
            ollama_cmd = self._find_ollama_executable()
            if not ollama_cmd:
                return False
            
            # List available models
            result = subprocess.run(
                [ollama_cmd, "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Check if model is in the list
                # Format: NAME           ID           SIZE   MODIFIED
                # Example: qwen2.5:3b-instruct   abc123  2.0GB  2 days ago
                lines = result.stdout.strip().split('\n')
                for line in lines[1:]:  # Skip header
                    if line.strip().startswith(model):
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check model status: {str(e)}")
            return False
    
    def list_models(self) -> List[str]:
        """
        List all locally available models.
        
        Returns:
            List of model names
        """
        try:
            ollama_cmd = self._find_ollama_executable()
            if not ollama_cmd:
                return []
            
            result = subprocess.run(
                [ollama_cmd, "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                models = []
                lines = result.stdout.strip().split('\n')
                for line in lines[1:]:  # Skip header
                    if line.strip():
                        # Extract model name (first column)
                        model_name = line.split()[0]
                        models.append(model_name)
                return models
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to list models: {str(e)}")
            return []
    
    def _find_ollama_executable(self) -> Optional[str]:
        """
        Find Ollama executable on the system.
        
        Returns:
            Path to ollama executable, or None if not found
        """
        # Check common installation paths
        if sys.platform == "win32":
            # Windows paths
            paths = [
                os.path.expanduser("~\\AppData\\Local\\Programs\\Ollama\\ollama.exe"),
                "C:\\Program Files\\Ollama\\ollama.exe",
                "C:\\Program Files (x86)\\Ollama\\ollama.exe",
            ]
        elif sys.platform == "darwin":
            # macOS paths
            paths = [
                "/usr/local/bin/ollama",
                "/opt/homebrew/bin/ollama",
                os.path.expanduser("~/.ollama/bin/ollama"),
            ]
        else:
            # Linux paths
            paths = [
                "/usr/local/bin/ollama",
                "/usr/bin/ollama",
                os.path.expanduser("~/.ollama/bin/ollama"),
            ]
        
        # Check each path
        for path in paths:
            if os.path.exists(path):
                return path
        
        # Try PATH
        import shutil
        ollama_in_path = shutil.which("ollama")
        if ollama_in_path:
            return ollama_in_path
        
        return None
    
    def get_status(self) -> dict:
        """
        Get complete status of Ollama server and model.
        
        Returns:
            Dictionary with status information
        """
        is_running = self.is_running(force_check=True)
        model_loaded = self.is_model_loaded() if is_running else False
        
        return {
            "running": is_running,
            "model_loaded": model_loaded,
            "model_name": self.model_name,
            "endpoint": self.endpoint,
            "available_models": self.list_models() if is_running else []
        }


# Singleton instance for global access
_ollama_manager: Optional[OllamaManager] = None


def get_ollama_manager(endpoint: str = "http://localhost:11434", 
                       model_name: str = "qwen2.5:3b-instruct") -> OllamaManager:
    """
    Get or create the global Ollama manager instance.
    
    Args:
        endpoint: Ollama API endpoint
        model_name: Default model name
        
    Returns:
        OllamaManager instance
    """
    global _ollama_manager
    if _ollama_manager is None:
        _ollama_manager = OllamaManager(endpoint, model_name)
    return _ollama_manager
