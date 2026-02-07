"""
TikTok uploader using Brave browser automation.

Navigates to TikTok upload page and automates the upload process.
"""

import os
import random
import logging
from typing import Optional
from .brave_base import BraveBrowserBase

logger = logging.getLogger(__name__)

# TikTok network error messages
TIKTOK_NETWORK_ERROR_MESSAGES = [
    "[FAIL] Network error accessing TikTok - possible causes:",
    "  1. Internet connection issue",
    "  2. TikTok may be blocked in your region",
    "  3. Firewall or antivirus blocking access",
    "  4. TikTok service may be temporarily down"
]


def upload_to_tiktok_browser(
    video_path: str,
    title: str,
    description: str,
    tags: str,
    brave_path: Optional[str] = None,
    user_data_dir: Optional[str] = None,
    profile_directory: str = "Default"
) -> Optional[str]:
    """
    Upload video to TikTok via Brave browser automation.
    
    Args:
        video_path: Path to video file
        title: Video title
        description: Video description
        tags: Space-separated tags (e.g., "#viral #trending")
        brave_path: Path to Brave executable (optional, auto-detect)
        user_data_dir: Path to Brave user data directory (optional, for login session reuse)
        profile_directory: Profile directory name (e.g., "Default", "Profile 1")
        
    Returns:
        Success message if upload completed, None if failed
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    logger.info("Starting TikTok browser upload")
    
    try:
        browser = BraveBrowserBase(brave_path, user_data_dir, profile_directory)
        page = browser.launch(headless=False)
        
        # Navigate to TikTok upload page with network error handling
        logger.info("Navigating to TikTok upload page")
        try:
            page.goto("https://www.tiktok.com/upload", wait_until="networkidle", timeout=30000)
        except Exception as nav_error:
            error_msg = str(nav_error).lower()
            if "net::" in error_msg or "timeout" in error_msg:
                for msg in TIKTOK_NETWORK_ERROR_MESSAGES:
                    logger.error(msg)
                raise Exception(f"Network error: Cannot reach TikTok upload page - {nav_error}")
            else:
                raise
        
        browser.human_delay(2, 4)
        
        # Check if user is logged in
        # If login page appears, wait for manual login
        if "login" in page.url.lower():
            logger.warning("TikTok login required - please log in manually")
            logger.info("Waiting 60 seconds for manual login...")
            page.wait_for_url("**/upload**", timeout=60000)
            logger.info("Login successful, continuing upload")
        
        # Upload video file
        # TikTok uses an iframe for upload - selectors may vary
        # Common selectors (update as needed based on current TikTok UI):
        # - input[type="file"]
        # - [data-e2e="upload-input"]
        logger.info("Uploading video file")
        try:
            # Try primary selector
            file_input_selector = 'input[type="file"]'
            browser.upload_file(file_input_selector, video_path)
        except Exception as e:
            logger.warning(f"Primary file selector failed, trying alternative: {e}")
            # Try alternative selector
            file_input_selector = '[data-e2e="upload-input"]'
            browser.upload_file(file_input_selector, video_path)
        
        browser.human_delay(3, 5)
        
        # Wait for video to process
        logger.info("Waiting for video processing...")
        page.wait_for_timeout(5000)
        
        # Fill in caption (title + description + tags)
        # TikTok combines everything into a single caption field
        full_caption = f"{title}\n\n{description}\n\n{tags}".strip()
        
        logger.info("Filling caption")
        try:
            # Common caption selectors (update as needed):
            # - [data-e2e="caption-input"]
            # - textarea[placeholder*="caption"]
            # - div[contenteditable="true"][data-text*="describe"]
            caption_selector = '[data-e2e="caption-input"]'
            browser.human_type(caption_selector, full_caption)
        except Exception as e:
            logger.warning(f"Primary caption selector failed, trying alternative: {e}")
            # Try contenteditable div
            caption_selector = 'div[contenteditable="true"]'
            browser.human_type(caption_selector, full_caption)
        
        browser.human_delay(2, 3)
        
        # Optional: Set privacy to Public (usually default)
        # Selector may be: [data-e2e="privacy-select"]
        
        # Click Post/Upload button
        logger.info("Clicking Post button")
        try:
            # Common post button selectors:
            # - [data-e2e="post-button"]
            # - button containing "Post"
            post_button_selector = '[data-e2e="post-button"]'
            page.wait_for_selector(post_button_selector, timeout=5000)
            browser.click_and_wait(post_button_selector, delay=3)
        except Exception as e:
            logger.warning(f"Primary post button selector failed, trying alternative: {e}")
            # Try text-based selector
            post_button_selector = 'button:has-text("Post")'
            browser.click_and_wait(post_button_selector, delay=3)
        
        # Wait for upload confirmation
        logger.info("Waiting for upload confirmation...")
        page.wait_for_timeout(5000)
        
        # Check for success indicators
        # TikTok usually redirects or shows a success message
        current_url = page.url
        
        if "upload" not in current_url.lower() or "success" in page.content().lower():
            logger.info("TikTok upload completed successfully")
            result = "TikTok upload successful"
        else:
            logger.warning("Upload status unclear - manual verification recommended")
            result = "TikTok upload submitted (verify manually)"
        
        browser.human_delay(2, 3)
        browser.close()
        
        return result
        
    except Exception as e:
        logger.error(f"TikTok browser upload failed: {str(e)}")
        if 'browser' in locals():
            browser.close()
        return None


# Backward compatibility wrapper
def upload_to_tiktok(
    video_path: str,
    caption: str,
    hashtags: list,
    credentials: dict
) -> Optional[str]:
    """
    Upload to TikTok (browser-based).
    
    This maintains API compatibility with the old API-based uploader.
    Now uses BraveBrowserManager if available for shared browser context.
    
    Args:
        video_path: Path to video file
        caption: Video caption
        hashtags: List of hashtags
        credentials: Dictionary with optional brave_path and profile_path
        
    Returns:
        Upload ID/result if successful, None if failed
    """
    from .brave_manager import BraveBrowserManager
    
    # Extract browser settings from credentials
    brave_path = credentials.get("brave_path")
    user_data_dir = credentials.get("brave_user_data_dir")
    profile_directory = credentials.get("brave_profile_directory", "Default")
    
    # Format hashtags
    tags = " ".join(hashtags) if hashtags else ""
    
    # Check if BraveBrowserManager is initialized (pipeline mode)
    manager = BraveBrowserManager.get_instance()
    if manager.is_initialized:
        # Use shared browser context (pipeline mode)
        logger.info("Using shared browser context from BraveBrowserManager")
        return _upload_to_tiktok_with_manager(
            video_path=video_path,
            title=caption[:100],
            description=caption,
            tags=tags
        )
    else:
        # Standalone mode - use direct browser launch
        logger.info("Using standalone browser mode")
        return upload_to_tiktok_browser(
            video_path=video_path,
            title=caption[:100],  # TikTok title has limits
            description=caption,
            tags=tags,
            brave_path=brave_path,
            user_data_dir=user_data_dir,
            profile_directory=profile_directory
        )


def _upload_to_tiktok_with_manager(
    video_path: str,
    title: str,
    description: str,
    tags: str
) -> Optional[str]:
    """
    Upload to TikTok using shared browser from BraveBrowserManager.
    
    This function is called when pipeline has initialized the manager.
    It gets a page from the shared context instead of creating a new browser.
    """
    from .brave_manager import BraveBrowserManager
    
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    logger.info("Starting TikTok browser upload with shared context")
    
    page = None
    try:
        manager = BraveBrowserManager.get_instance()
        page = manager.get_page()
        
        # Navigate to TikTok upload page with network error handling
        logger.info("Navigating to TikTok upload page")
        try:
            page.goto("https://www.tiktok.com/upload", wait_until="networkidle", timeout=30000)
        except Exception as nav_error:
            error_msg = str(nav_error).lower()
            if "net::" in error_msg or "timeout" in error_msg:
                for msg in TIKTOK_NETWORK_ERROR_MESSAGES:
                    logger.error(msg)
                raise Exception(f"Network error: Cannot reach TikTok upload page - {nav_error}")
            else:
                raise
        
        page.wait_for_timeout(random.randint(2000, 4000))
        
        # Check if user is logged in
        if "login" in page.url.lower():
            logger.warning("TikTok login required - please log in manually")
            logger.info("Waiting 60 seconds for manual login...")
            page.wait_for_url("**/upload**", timeout=60000)
            logger.info("Login successful, continuing upload")
        
        # Upload video file
        logger.info("Uploading video file")
        try:
            file_input_selector = 'input[type="file"]'
            file_input = page.wait_for_selector(file_input_selector, state="attached", timeout=10000)
            file_input.set_input_files(video_path)
        except Exception as e:
            logger.warning(f"Primary file selector failed, trying alternative: {e}")
            file_input_selector = '[data-e2e="upload-input"]'
            file_input = page.wait_for_selector(file_input_selector, state="attached", timeout=10000)
            file_input.set_input_files(video_path)
        
        page.wait_for_timeout(random.randint(3000, 5000))
        
        # Wait for video to process
        logger.info("Waiting for video processing...")
        page.wait_for_timeout(5000)
        
        # Fill in caption (title + description + tags)
        full_caption = f"{title}\n\n{description}\n\n{tags}".strip()
        
        logger.info("Filling caption")
        try:
            caption_selector = '[data-e2e="caption-input"]'
            element = page.wait_for_selector(caption_selector, timeout=10000)
            element.click()
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            for char in full_caption:
                element.type(char, delay=random.uniform(50, 150))
        except Exception as e:
            logger.warning(f"Primary caption selector failed, trying alternative: {e}")
            caption_selector = 'div[contenteditable="true"]'
            element = page.wait_for_selector(caption_selector, timeout=10000)
            element.click()
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            for char in full_caption:
                element.type(char, delay=random.uniform(50, 150))
        
        page.wait_for_timeout(random.randint(2000, 3000))
        
        # Click Post/Upload button
        logger.info("Clicking Post button")
        try:
            post_button_selector = '[data-e2e="post-button"]'
            page.wait_for_selector(post_button_selector, timeout=5000)
            post_button = page.query_selector(post_button_selector)
            post_button.click()
            page.wait_for_timeout(3000)
        except Exception as e:
            logger.warning(f"Primary post button selector failed, trying alternative: {e}")
            post_button_selector = 'button:has-text("Post")'
            post_button = page.wait_for_selector(post_button_selector, timeout=5000)
            post_button.click()
            page.wait_for_timeout(3000)
        
        # Wait for upload confirmation
        logger.info("Waiting for upload confirmation...")
        page.wait_for_timeout(5000)
        
        # Check for success indicators
        current_url = page.url
        
        if "upload" not in current_url.lower() or "success" in page.content().lower():
            logger.info("TikTok upload completed successfully")
            result = "TikTok upload successful"
        else:
            logger.warning("Upload status unclear - manual verification recommended")
            result = "TikTok upload submitted (verify manually)"
        
        # Navigate to about:blank for next uploader
        manager.navigate_to_blank(page)
        manager.close_page(page)
        
        return result
        
    except Exception as e:
        logger.error(f"TikTok browser upload failed: {str(e)}")
        if page:
            try:
                manager = BraveBrowserManager.get_instance()
                manager.close_page(page)
            except:
                pass
        return None
