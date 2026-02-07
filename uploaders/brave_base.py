"""
Base Brave browser automation using Playwright.

Provides:
- Brave browser launch with custom profile
- Human-like delays and typing
- Common upload utilities
"""

import os
import sys
import time
import random
import logging
import subprocess
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
    
    DEFAULT_USER_DATA_DIRS = {
        "win32": os.path.expanduser(r"~\AppData\Local\BraveSoftware\Brave-Browser\User Data"),
        "darwin": os.path.expanduser("~/Library/Application Support/BraveSoftware/Brave-Browser"),
        "linux": os.path.expanduser("~/.config/BraveSoftware/Brave-Browser")
    }
    
    def __init__(
        self, 
        brave_path: Optional[str] = None, 
        user_data_dir: Optional[str] = None,
        profile_directory: str = "Default"
    ):
        """
        Initialize Brave browser automation.
        
        Args:
            brave_path: Path to Brave executable (default: auto-detect)
            user_data_dir: Path to Brave user data directory (e.g., C:\\Users\\user\\AppData\\Local\\BraveSoftware\\Brave-Browser\\User Data)
            profile_directory: Profile directory name (e.g., "Default", "Profile 1", "Profile 2")
        """
        self.brave_path = brave_path or self._detect_brave_path()
        self.user_data_dir = user_data_dir
        self.profile_directory = profile_directory
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None  # For fallback mode without user_data_dir
        self.context = None  # Changed from browser to context for persistent context
        self.page: Optional[Page] = None
        
        if not self.brave_path or not os.path.exists(self.brave_path):
            raise FileNotFoundError(
                f"Brave browser not found at: {self.brave_path}\n"
                "Please install Brave or specify the correct path."
            )
        
        # Validate profile exists if user_data_dir is specified
        if self.user_data_dir:
            self._validate_profile()
    
    def _detect_brave_path(self) -> str:
        """Auto-detect Brave browser executable path."""
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
    
    def _validate_profile(self):
        """
        Validate that the profile directory exists.
        
        Raises:
            RuntimeError: If profile directory is missing
        """
        if not self.user_data_dir:
            return
        
        profile_full_path = os.path.join(self.user_data_dir, self.profile_directory)
        
        if not os.path.exists(self.user_data_dir):
            raise RuntimeError(
                f"Brave user data directory not found: {self.user_data_dir}\n"
                f"Please specify a valid Brave user data directory path.\n"
                f"Example (Windows): C:\\Users\\<USER>\\AppData\\Local\\BraveSoftware\\Brave-Browser\\User Data"
            )
        
        if not os.path.exists(profile_full_path):
            raise RuntimeError(
                f"Brave profile not found: {profile_full_path}\n"
                f"User Data Dir: {self.user_data_dir}\n"
                f"Profile Directory: {self.profile_directory}\n\n"
                f"Use an existing logged-in profile. Temp profiles are NOT allowed.\n"
                f"Available profiles in user data dir:\n" +
                "\n".join([f"  - {d}" for d in os.listdir(self.user_data_dir) 
                          if os.path.isdir(os.path.join(self.user_data_dir, d)) 
                          and (d == "Default" or d.startswith("Profile"))])
            )
    
    @staticmethod
    def get_available_profiles(user_data_dir: str) -> list:
        """
        Get list of available profile directories in user data dir.
        
        Args:
            user_data_dir: Path to Brave user data directory
            
        Returns:
            List of profile directory names (e.g., ["Default", "Profile 1", "Profile 2"])
        """
        if not os.path.exists(user_data_dir):
            return []
        
        profiles = []
        for item in os.listdir(user_data_dir):
            item_path = os.path.join(user_data_dir, item)
            if os.path.isdir(item_path) and (item == "Default" or item.startswith("Profile")):
                profiles.append(item)
        
        return sorted(profiles)
    
    def _kill_brave_processes(self):
        """Kill any running Brave browser processes to avoid profile lock conflicts."""
        logger.info("Checking for running Brave processes...")
        
        try:
            if sys.platform == "win32":
                # Kill brave.exe on Windows
                result = subprocess.run(
                    ["taskkill", "/F", "/IM", "brave.exe"],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    logger.info("Killed running Brave processes")
                    time.sleep(3)  # Wait for cleanup on Windows
                else:
                    logger.debug("No Brave processes found to kill")
            elif sys.platform == "darwin":
                result = subprocess.run(
                    ["pkill", "-f", "Brave Browser"],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    logger.info("Killed running Brave processes")
                else:
                    logger.debug("No Brave processes found to kill")
                time.sleep(2)
            else:
                result = subprocess.run(
                    ["pkill", "-f", "brave"],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    logger.info("Killed running Brave processes")
                else:
                    logger.debug("No Brave processes found to kill")
                time.sleep(2)
        except Exception as e:
            logger.warning(f"Failed to kill Brave processes: {e}")
    
    def launch(self, headless: bool = False) -> Page:
        """
        Launch Brave browser using persistent context and return page.
        
        CRITICAL: Uses launch_persistent_context() to maintain real profile sessions.
        This is required for Google login and other platform authentications.
        
        Args:
            headless: Run in headless mode (default: False, browser visible)
                     NOTE: headless=True will break Google login - use only for testing
            
        Returns:
            Playwright Page object
        """
        logger.info(f"Launching Brave browser: {self.brave_path}")
        
        # Kill any running Brave processes to avoid profile lock
        if self.user_data_dir:
            self._kill_brave_processes()
        
        self.playwright = sync_playwright().start()
        
        # Build launch arguments for anti-detection
        launch_args = [
            "--disable-blink-features=AutomationControlled",  # Hide automation
            "--start-maximized",  # Better UX
        ]
        
        # Add profile directory if using persistent context
        if self.user_data_dir:
            launch_args.append(f"--profile-directory={self.profile_directory}")
            logger.info(f"Using User Data Dir: {self.user_data_dir}")
            logger.info(f"Using Profile Directory: {self.profile_directory}")
        
        # CRITICAL: Use launch_persistent_context() to reuse real profile
        # This is the ONLY way to maintain login sessions (Google, TikTok, etc.)
        if self.user_data_dir:
            # Persistent context with real profile
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                executable_path=self.brave_path,
                headless=headless,
                
                # CRITICAL: Prevent Playwright from injecting bot-oriented defaults
                # that break real Brave profiles
                ignore_default_args=[
                    "--disable-extensions",
                    "--disable-component-extensions-with-background-pages",
                    "--disable-background-networking",
                    "--disable-sync",
                    "--no-first-run",
                    "--disable-default-browser-check",
                    "--no-sandbox",
                ],
                
                args=launch_args,
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            # Get or create page
            if len(self.context.pages) > 0:
                self.page = self.context.pages[0]
            else:
                self.page = self.context.new_page()
        else:
            # Fallback: regular launch without profile (will create temp profile)
            logger.warning(
                "No user_data_dir specified - using temporary profile.\n"
                "This may cause login failures on Google and other platforms.\n"
                "Specify user_data_dir and profile_directory for production use."
            )
            self.browser = self.playwright.chromium.launch(
                executable_path=self.brave_path,
                headless=headless,
                args=launch_args,
                ignore_default_args=["--no-sandbox"],
            )
            
            self.context = self.browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            self.page = self.context.new_page()
        
        logger.info("Brave browser launched successfully")
        
        return self.page
    
    def close(self):
        """Close browser and cleanup."""
        if self.page:
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser:  # For fallback mode
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
