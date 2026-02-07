"""
Base Brave browser automation using Playwright.

Provides:
- Brave browser launch with custom profile
- Human-like delays and typing
- Common upload utilities
"""

import os
import time
import random
import logging
from pathlib import Path
from typing import Optional
from playwright.sync_api import sync_playwright, Browser, Page, Playwright

logger = logging.getLogger(__name__)


class BraveBrowserBase:
    """Base class for Brave browser automation."""
    
    DEFAULT_BRAVE_PATHS = {
        "win32": "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
        "darwin": "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        "linux": "/usr/bin/brave-browser"
    }
    
    def __init__(self, brave_path: Optional[str] = None, profile_path: Optional[str] = None):
        """
        Initialize Brave browser automation.
        
        Args:
            brave_path: Path to Brave executable (default: auto-detect)
            profile_path: Path to Brave user data directory (optional)
        """
        self.brave_path = brave_path or self._detect_brave_path()
        self.profile_path = profile_path
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
        if not self.brave_path or not os.path.exists(self.brave_path):
            raise FileNotFoundError(
                f"Brave browser not found at: {self.brave_path}\n"
                "Please install Brave or specify the correct path."
            )
    
    def _detect_brave_path(self) -> str:
        """Auto-detect Brave browser executable path."""
        import sys
        platform = sys.platform
        
        # Try platform-specific default path
        default_path = self.DEFAULT_BRAVE_PATHS.get(platform, "")
        if default_path and os.path.exists(default_path):
            return default_path
        
        # Windows: Check common installation paths
        if platform == "win32":
            paths = [
                "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
                "C:\\Program Files (x86)\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
                os.path.expanduser("~\\AppData\\Local\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"),
            ]
            for path in paths:
                if os.path.exists(path):
                    return path
        
        # macOS: Check Applications
        elif platform == "darwin":
            paths = [
                "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
                os.path.expanduser("~/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"),
            ]
            for path in paths:
                if os.path.exists(path):
                    return path
        
        # Linux: Check common paths
        else:
            paths = [
                "/usr/bin/brave-browser",
                "/usr/bin/brave",
                "/snap/bin/brave",
            ]
            for path in paths:
                if os.path.exists(path):
                    return path
        
        # Return empty string if not found (will raise error in __init__)
        return ""
    
    def launch(self, headless: bool = False) -> Page:
        """
        Launch Brave browser and return page.
        
        Args:
            headless: Run in headless mode (default: False, browser visible)
            
        Returns:
            Playwright Page object
        """
        logger.info(f"Launching Brave browser: {self.brave_path}")
        
        self.playwright = sync_playwright().start()
        
        # Build launch arguments
        launch_args = []
        
        # Add user data directory if specified (reuse existing profile)
        if self.profile_path:
            launch_args.append(f"--user-data-dir={self.profile_path}")
            logger.info(f"Using profile: {self.profile_path}")
        
        # Launch Brave with Chromium driver
        self.browser = self.playwright.chromium.launch(
            executable_path=self.brave_path,
            headless=headless,
            args=launch_args
        )
        
        # Create a new page
        context = self.browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        self.page = context.new_page()
        logger.info("Brave browser launched successfully")
        
        return self.page
    
    def close(self):
        """Close browser and cleanup."""
        if self.page:
            self.page.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        
        logger.info("Brave browser closed")
    
    def human_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """
        Add human-like delay.
        
        Args:
            min_seconds: Minimum delay in seconds
            max_seconds: Maximum delay in seconds
        """
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def human_type(self, selector: str, text: str, delay_range: tuple = (0.05, 0.15)):
        """
        Type text with human-like delays between characters.
        
        Args:
            selector: CSS selector for input element
            text: Text to type
            delay_range: Min/max delay between keystrokes in seconds
        """
        if not self.page:
            raise RuntimeError("Browser not launched")
        
        element = self.page.wait_for_selector(selector, timeout=10000)
        element.click()
        
        # Clear existing text
        self.page.keyboard.press("Control+A")
        self.page.keyboard.press("Backspace")
        
        # Type with delays
        for char in text:
            element.type(char, delay=random.uniform(delay_range[0], delay_range[1]) * 1000)
    
    def upload_file(self, selector: str, file_path: str):
        """
        Upload file via file input.
        
        Args:
            selector: CSS selector for file input
            file_path: Path to file to upload
        """
        if not self.page:
            raise RuntimeError("Browser not launched")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Wait for file input
        file_input = self.page.wait_for_selector(selector, timeout=10000)
        
        # Set files
        file_input.set_input_files(file_path)
        logger.info(f"File uploaded: {file_path}")
    
    def wait_for_navigation(self, timeout: int = 30000):
        """
        Wait for page navigation to complete.
        
        Args:
            timeout: Timeout in milliseconds
        """
        if not self.page:
            raise RuntimeError("Browser not launched")
        
        self.page.wait_for_load_state("networkidle", timeout=timeout)
    
    def click_and_wait(self, selector: str, delay: float = 2.0):
        """
        Click element and wait with human delay.
        
        Args:
            selector: CSS selector
            delay: Delay after click in seconds
        """
        if not self.page:
            raise RuntimeError("Browser not launched")
        
        element = self.page.wait_for_selector(selector, timeout=10000)
        element.click()
        time.sleep(delay)
    
    def __enter__(self):
        """Context manager entry."""
        self.launch()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
