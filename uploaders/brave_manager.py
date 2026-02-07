"""
Brave Browser Manager - Singleton for shared browser context across multiple uploaders.

Solves the critical bugs in the pipeline:
- Single Playwright instance (no profile lock conflicts)
- Single persistent context (shared browser session)
- Kill processes only once at startup
- Thread-safe singleton pattern
- Each uploader gets a new page (tab) from shared context
"""

import logging
import threading
from typing import Optional
from playwright.sync_api import Page
from .brave_base import BraveBrowserBase

logger = logging.getLogger(__name__)


class BraveBrowserManager:
    """
    Singleton manager for shared Brave browser instance across multiple uploaders.
    
    This ensures:
    1. Only ONE Playwright instance for the entire pipeline
    2. Only ONE persistent context (no profile lock conflicts)
    3. Kill Brave processes only ONCE at the start
    4. Each uploader gets a new page (tab) from the shared context
    5. Browser cleanup happens only once at the end
    """
    
    _instance: Optional['BraveBrowserManager'] = None
    _lock = threading.Lock()
    
    def __init__(self):
        """Private constructor - use get_instance() instead."""
        self.browser_base: Optional[BraveBrowserBase] = None
        self.is_initialized = False
        self.active_pages = []
        
    @classmethod
    def get_instance(cls) -> 'BraveBrowserManager':
        """
        Get singleton instance (thread-safe).
        
        Returns:
            BraveBrowserManager singleton instance
        """
        if cls._instance is None:
            with cls._lock:
                # Double-check locking pattern
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """
        Reset singleton instance (for testing).
        
        CAUTION: Only use in tests or after calling close().
        """
        with cls._lock:
            if cls._instance is not None:
                if cls._instance.is_initialized:
                    cls._instance.close()
            cls._instance = None
    
    def initialize(
        self,
        brave_path: Optional[str] = None,
        user_data_dir: Optional[str] = None,
        profile_directory: str = "Default"
    ):
        """
        Initialize the shared browser instance.
        
        MUST be called before get_page(). Only initializes once.
        
        Args:
            brave_path: Path to Brave executable (optional, auto-detect)
            user_data_dir: Path to Brave user data directory (REQUIRED for persistent login)
            profile_directory: Profile directory name (e.g., "Default", "Profile 1")
        
        Raises:
            RuntimeError: If browser fails to launch
        """
        if self.is_initialized:
            logger.info("BraveBrowserManager already initialized, skipping")
            return
        
        logger.info("Initializing shared Brave browser instance")
        
        try:
            # Create BraveBrowserBase instance
            self.browser_base = BraveBrowserBase(
                brave_path=brave_path,
                user_data_dir=user_data_dir,
                profile_directory=profile_directory
            )
            
            # Launch browser (this will kill processes and start Playwright once)
            self.browser_base.launch(headless=False)
            
            self.is_initialized = True
            logger.info("Shared Brave browser initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Brave browser: {e}")
            self.is_initialized = False
            raise RuntimeError(f"Brave browser initialization failed: {e}")
    
    def get_page(self) -> Page:
        """
        Get a new page (tab) from the shared browser context.
        
        Each uploader should call this to get its own page.
        
        Returns:
            Playwright Page object (new tab in shared browser)
        
        Raises:
            RuntimeError: If manager not initialized
        """
        if not self.is_initialized or not self.browser_base or not self.browser_base.context:
            raise RuntimeError(
                "BraveBrowserManager not initialized. Call initialize() first."
            )
        
        # Create a new page (tab) in the shared context
        page = self.browser_base.context.new_page()
        self.active_pages.append(page)
        
        logger.info(f"Created new page (total active: {len(self.active_pages)})")
        
        return page
    
    def close_page(self, page: Page):
        """
        Close a specific page (tab).
        
        Args:
            page: Page to close
        """
        try:
            if page in self.active_pages:
                self.active_pages.remove(page)
            page.close()
            logger.info(f"Closed page (remaining active: {len(self.active_pages)})")
        except Exception as e:
            logger.warning(f"Failed to close page: {e}")
    
    def navigate_to_blank(self, page: Page):
        """
        Navigate page to about:blank to clean up before next use.
        
        Args:
            page: Page to navigate
        """
        try:
            page.goto("about:blank", wait_until="load", timeout=5000)
            logger.debug("Navigated page to about:blank")
        except Exception as e:
            logger.warning(f"Failed to navigate to about:blank: {e}")
    
    def close(self):
        """
        Close the shared browser instance and cleanup.
        
        MUST be called at the end of the pipeline (in a finally block).
        """
        if not self.is_initialized:
            logger.info("BraveBrowserManager not initialized, nothing to close")
            return
        
        logger.info("Closing shared Brave browser instance")
        
        try:
            # Close all active pages
            for page in self.active_pages[:]:  # Copy list to avoid modification during iteration
                try:
                    page.close()
                except Exception as e:
                    logger.warning(f"Failed to close page: {e}")
            
            self.active_pages.clear()
            
            # Close browser via BraveBrowserBase
            if self.browser_base:
                self.browser_base.close()
                self.browser_base = None
            
            self.is_initialized = False
            logger.info("Shared Brave browser closed successfully")
            
        except Exception as e:
            logger.error(f"Error closing Brave browser: {e}")
            self.is_initialized = False
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
