"""
Instagram uploader using Brave browser automation.

Navigates to Instagram and automates the Reels upload process.

IMPORTANT LIMITATIONS (2025 Instagram Web Reality):
- Instagram uses modal-based workflow (no URL changes)
- No deterministic success confirmation available on web
- React-heavy UI with dynamic components
- Upload status is submitted but not verified
"""

import os
import random
import logging
from typing import Optional
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from .brave_base import BraveBrowserBase

logger = logging.getLogger(__name__)

# Instagram Create button selector - ONLY use the stable one
# Instagram's UI is modal-based and this is the only consistently reliable trigger
# If this selector fails, Instagram changed UI - log hard error and STOP
INSTAGRAM_CREATE_SELECTORS = [
    'svg[aria-label="New post"]',  # Single reliable selector
]
INSTAGRAM_CREATE_SELECTOR = INSTAGRAM_CREATE_SELECTORS[0]


def _wait_for_button_enabled(page: Page, button_text: str, timeout: int = 90000) -> bool:
    """
    Click button only when it's enabled and ready.
    
    Instagram disables buttons while processing uploads/crops.
    Clicking early results in ignored clicks.
    
    Uses stable selectors:
    - div[role="button"]:has-text("Next") for Next button
    - div[role="button"]:has-text("Share") for Share button
    
    Args:
        page: Playwright Page object
        button_text: Text of the button (e.g., "Next", "Share")
        timeout: Timeout in milliseconds (default: 90000, 3x increased)
        
    Returns:
        True if button clicked successfully, False otherwise
    """
    try:
        # Use locator for better state checking
        button = page.locator(f'div[role="button"]:has-text("{button_text}")')
        
        # Wait for visible
        button.wait_for(state="visible", timeout=timeout)
        logger.debug(f"{button_text} button visible")
        
        # Critical: Wait for enabled state (button not disabled while processing)
        button.wait_for(state="enabled", timeout=timeout)
        logger.debug(f"{button_text} button enabled")
        
        # Now safe to click
        button.click()
        logger.info(f"{button_text} button clicked")
        return True
    except PlaywrightTimeoutError:
        logger.error(f"{button_text} button did not become enabled in time")
        return False
    except Exception as e:
        logger.error(f"Error clicking {button_text} button: {e}")
        return False


def _find_caption_input(page: Page):
    """
    Find the caption input field using specific selectors.
    
    Instagram has multiple div[role="textbox"] elements.
    We need to target the caption specifically to avoid typing into wrong fields.
    
    Args:
        page: Playwright Page object
        
    Returns:
        Caption input element or None if not found
    """
    # Primary selectors (most stable)
    caption_selectors = [
        'div[role="textbox"][aria-label*="caption"]',  # Most reliable
        'textarea[aria-label*="caption"]',  # Fallback
        'div[role="textbox"][aria-label*="Write a caption"]',  # English-specific
    ]
    
    for selector in caption_selectors:
        try:
            caption_box = page.wait_for_selector(selector, timeout=15000)
            if caption_box:
                logger.info(f"Caption box found: {selector}")
                return caption_box
        except PlaywrightTimeoutError:
            logger.debug(f"Caption selector {selector} not found, trying next")
            continue
        except Exception as e:
            logger.debug(f"Error with caption selector {selector}: {e}")
            continue
    
    logger.error("Caption input not found with any selector")
    return None


def _select_post_option(page: Page, timeout: int = 45000) -> bool:
    """
    Click the Post/Create option after opening Create menu.
    
    Instagram A/B tests multiple UI variants:
    - "Post" (classic)
    - "Create post" (newer)
    - "Post to feed" (alternative)
    - "Reel" (fallback - also opens file upload)
    
    Try all variants with retries for React animation delays.
    
    Args:
        page: Playwright Page object
        timeout: Timeout in milliseconds (default: 45000, 3x increased)
        
    Returns:
        True if clicked successfully, False otherwise
    """
    # Priority order - most specific first
    possible_selectors = [
        'div[role="button"]:has-text("Post")',
        'div[role="button"]:has-text("Create post")',
        'div[role="button"]:has-text("Post to feed")',
        'div[role="button"]:has-text("Reel")'  # Fallback - also allows file upload
    ]
    
    max_retries = 5  # Increased retries for slow networks
    attempted_selectors = []
    
    for attempt in range(max_retries):
        logger.debug(f"Attempt {attempt + 1}/{max_retries} to find Post option")
        
        for selector in possible_selectors:
            try:
                button = page.locator(selector)
                
                # Increased timeout by 3x for slow networks (3s → 9s)
                # Try to interact with the first matching element
                button.first.wait_for(state="visible", timeout=9000)
                button.first.wait_for(state="enabled", timeout=9000)
                logger.info(f"Found Post option: {selector}")
                button.first.click()
                logger.info("Post option clicked successfully")
                return True
            except Exception as e:
                attempted_selectors.append(selector)
                logger.debug(f"Selector {selector} failed: {e}")
                continue
        
        # React animation may be slow - wait longer and retry (3s → 9s)
        if attempt < max_retries - 1:
            logger.debug("Menu may still be animating, waiting 9s before retry...")
            page.wait_for_timeout(9000)
    
    logger.error(f"Post option button not found with any variant. Attempted selectors: {attempted_selectors}")
    return False


def upload_to_instagram_browser(
    video_path: str,
    title: str,
    description: str,
    tags: str,
    brave_path: Optional[str] = None,
    user_data_dir: Optional[str] = None,
    profile_directory: str = "Default"
) -> Optional[str]:
    """
    Upload video to Instagram Reels via Brave browser automation.
    
    IMPORTANT LIMITATIONS:
    - Instagram provides no deterministic confirmation on web uploads
    - This function submits the upload but cannot verify its status
    - Manual verification is recommended
    
    Args:
        video_path: Path to video file
        title: Video title (used in caption)
        description: Video description
        tags: Space-separated tags (e.g., "#viral #trending")
        brave_path: Path to Brave executable (optional, auto-detect)
        user_data_dir: Path to Brave user data directory (optional, for login session reuse)
        profile_directory: Profile directory name (e.g., "Default", "Profile 1")
        
    Returns:
        Success message if upload submitted, None if failed
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    logger.info("Starting Instagram browser upload")
    
    try:
        browser = BraveBrowserBase(brave_path, user_data_dir, profile_directory)
        page = browser.launch(headless=False)
        
        # Navigate to Instagram
        logger.info("Navigating to Instagram")
        try:
            # Increased timeout by 3x (60s → 180s) for slow networks
            page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=180000)
            # Wait for UI to be ready instead of networkidle (more reliable with websockets)
            # Increased timeout by 3x (30s → 90s)
            page.wait_for_selector('svg[aria-label="New post"]', timeout=90000)
            logger.info("Page loaded and UI ready")
            browser.human_delay(3, 6)  # Increased by 3x (2-4s → 6-12s for actual implementation)
        except Exception as e:
            if "Timeout" in str(e):
                logger.error("Instagram navigation timed out. Possible causes:")
                logger.error("  1. Slow internet connection")
                logger.error("  2. Instagram may be temporarily unavailable")
                logger.error("  3. Network firewall blocking Instagram")
                raise Exception(f"Instagram navigation timeout: {e}")
            raise
        
        # Check if user is logged in
        if "login" in page.url.lower() or page.query_selector('input[name="username"]'):
            logger.warning("Instagram login required - please log in manually")
            logger.info("Waiting 60 seconds for manual login...")
            page.wait_for_timeout(60000)
            logger.info("Continuing with upload")
        
        # Click "Create" button - use ONLY the reliable selector
        logger.info("Clicking Create button")
        try:
            create_button = page.wait_for_selector(INSTAGRAM_CREATE_SELECTOR, timeout=30000)
            create_button.click()
            logger.info("Create button clicked")
            # Wait for menu to fully render - increased for better reliability
            # Instagram's React-based menu needs time to animate and mount
            page.wait_for_timeout(random.randint(7500, 13500))
        except PlaywrightTimeoutError:
            raise Exception("Instagram Create button not found - UI may have changed or user not logged in")
        
        # Select "Post" option from Create menu
        logger.info("Selecting Post option from Create menu")
        if not _select_post_option(page):
            raise Exception("Post option not found - cannot proceed with upload")
        # Wait for file dialog to mount - increased by 3x (2-4s → 6-12s)
        page.wait_for_timeout(random.randint(6000, 12000))
        
        # Upload video file
        # The file input appears AFTER selecting Post option
        logger.info("Waiting for file input to appear")
        try:
            file_input_selector = 'input[type="file"][accept*="video"], input[type="file"][accept*="image"]'
            browser.upload_file(file_input_selector, video_path)
            logger.info("File upload initiated")
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            raise
        
        # Wait for upload + server processing - increased by 3x (3-6s → 9-18s)
        page.wait_for_timeout(random.randint(9000, 18000))
        
        # Wait for upload processing - increased by 3x (5s → 15s)
        logger.info("Waiting for video processing...")
        page.wait_for_timeout(15000)
        
        # Click "Next" through the editing steps with proper state checking
        logger.info("Navigating through editing steps")
        # Instagram is React-heavy - wait for state transitions
        
        # First Next (crop step)
        if not _wait_for_button_enabled(page, "Next"):
            raise Exception("Upload processing failed - Next button never enabled")
        # Wait for next modal (React state sync)
        page.wait_for_timeout(random.randint(1500, 3000))
        
        # Second Next (filter step - may not always appear)
        try:
            if not _wait_for_button_enabled(page, "Next", timeout=30000):
                logger.info("Second Next button not needed (single-step flow)")
        except Exception:
            logger.info("Second Next button not needed (single-step flow)")
        # Wait for next modal (React state sync)
        page.wait_for_timeout(random.randint(1500, 3000))
        
        # Fill in caption (title + description + tags)
        full_caption = f"{title}\n\n{description}\n\n{tags}".strip()
        
        logger.info("Filling caption")
        caption_box = _find_caption_input(page)
        if not caption_box:
            raise Exception("Caption input not found - cannot safely enter caption. UI may have changed.")
        
        # Type caption with human-like delays for better bot detection avoidance
        caption_box.click()
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        for char in full_caption:
            page.keyboard.type(char, delay=random.randint(50, 150))
        logger.info("Caption entered")
        
        browser.human_delay(2, 3)
        
        # Click "Share" button with state checking
        logger.info("Clicking Share button")
        if not _wait_for_button_enabled(page, "Share", timeout=30000):
            raise Exception("Share button failed - cannot complete upload")
        
        # Wait a moment for submission
        page.wait_for_timeout(3000)
        
        # Be HONEST about what we know
        logger.warning("Instagram upload submitted - no deterministic confirmation available")
        result = "Instagram upload submitted (status unverified)"
        
        browser.human_delay(2, 3)
        browser.close()
        
        return result
        
    except Exception as e:
        logger.error(f"Instagram browser upload failed: {str(e)}")
        if 'browser' in locals():
            browser.close()
        return None


# Backward compatibility wrapper
def upload_to_instagram(
    video_path: str,
    caption: str,
    hashtags: list,
    credentials: dict
) -> Optional[str]:
    """
    Upload to Instagram (browser-based).
    
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
        return _upload_to_instagram_with_manager(
            video_path=video_path,
            title=caption[:100],
            description=caption,
            tags=tags
        )
    else:
        # Standalone mode - use direct browser launch
        logger.info("Using standalone browser mode")
        return upload_to_instagram_browser(
            video_path=video_path,
            title=caption[:100],
            description=caption,
            tags=tags,
            brave_path=brave_path,
            user_data_dir=user_data_dir,
            profile_directory=profile_directory
        )


def _upload_to_instagram_with_manager(
    video_path: str,
    title: str,
    description: str,
    tags: str
) -> Optional[str]:
    """
    Upload to Instagram using shared browser from BraveBrowserManager.
    
    This function is called when pipeline has initialized the manager.
    It gets a page from the shared context instead of creating a new browser.
    
    IMPORTANT LIMITATIONS:
    - Instagram provides no deterministic confirmation on web uploads
    - This function submits the upload but cannot verify its status
    - Manual verification is recommended
    """
    from .brave_manager import BraveBrowserManager
    
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    logger.info("Starting Instagram browser upload with shared context")
    
    page = None
    try:
        manager = BraveBrowserManager.get_instance()
        page = manager.get_page()
        
        # Navigate to Instagram
        logger.info("Navigating to Instagram")
        try:
            page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=180000)
            # Wait for UI to be ready instead of networkidle (more reliable with websockets)
            page.wait_for_selector('svg[aria-label="New post"]', timeout=90000)
            logger.info("Page loaded and UI ready")
            page.wait_for_timeout(random.randint(6000, 12000))
        except Exception as e:
            if "Timeout" in str(e):
                logger.error("Instagram navigation timed out. Possible causes:")
                logger.error("  1. Slow internet connection")
                logger.error("  2. Instagram may be temporarily unavailable")
                logger.error("  3. Network firewall blocking Instagram")
                raise Exception(f"Instagram navigation timeout: {e}")
            raise
        
        # Check if user is logged in
        if "login" in page.url.lower() or page.query_selector('input[name="username"]'):
            logger.warning("Instagram login required - please log in manually")
            logger.info("Waiting 60 seconds for manual login...")
            page.wait_for_timeout(60000)
            logger.info("Continuing with upload")
        
        # Click "Create" button - use ONLY the reliable selector
        logger.info("Clicking Create button")
        try:
            create_button = page.wait_for_selector(INSTAGRAM_CREATE_SELECTOR, timeout=30000)
            create_button.click()
            logger.info("Create button clicked")
            # Wait for menu to fully render - increased for better reliability
            # Instagram's React-based menu needs time to animate and mount
            page.wait_for_timeout(random.randint(7500, 13500))
        except PlaywrightTimeoutError:
            raise Exception("Instagram Create button not found - UI may have changed or user not logged in")
        
        # Select "Post" option from Create menu
        logger.info("Selecting Post option from Create menu")
        if not _select_post_option(page):
            raise Exception("Post option not found - cannot proceed with upload")
        # Wait for file dialog to mount (human-like delay)
        page.wait_for_timeout(random.randint(6000, 12000))
        
        # Upload video file
        # The file input appears AFTER selecting Post option
        logger.info("Waiting for file input to appear")
        try:
            file_input = page.wait_for_selector(
                'input[type="file"][accept*="video"], input[type="file"][accept*="image"]',
                state="attached",
                timeout=15000
            )
            logger.info("File input found, uploading file")
            file_input.set_input_files(video_path)
            logger.info("File upload initiated")
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            raise
        
        # Wait for upload + server processing (human-like delay)
        page.wait_for_timeout(random.randint(3000, 6000))
        
        # Wait for upload processing
        logger.info("Waiting for video processing...")
        page.wait_for_timeout(5000)
        
        # Click "Next" through the editing steps with proper state checking
        logger.info("Navigating through editing steps")
        # Instagram is React-heavy - wait for state transitions
        
        # First Next (crop step)
        if not _wait_for_button_enabled(page, "Next"):
            raise Exception("Upload processing failed - Next button never enabled")
        # Wait for next modal (React state sync)
        page.wait_for_timeout(random.randint(1500, 3000))
        
        # Second Next (filter step - may not always appear)
        try:
            if not _wait_for_button_enabled(page, "Next", timeout=30000):
                logger.info("Second Next button not needed (single-step flow)")
        except Exception:
            logger.info("Second Next button not needed (single-step flow)")
        # Wait for next modal (React state sync)
        page.wait_for_timeout(random.randint(1500, 3000))
        
        # Fill in caption (title + description + tags)
        full_caption = f"{title}\n\n{description}\n\n{tags}".strip()
        
        logger.info("Filling caption")
        caption_box = _find_caption_input(page)
        if not caption_box:
            raise Exception("Caption input not found - cannot safely enter caption. UI may have changed.")
        
        # Type caption with human-like delays
        caption_box.click()
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        for char in full_caption:
            page.keyboard.type(char, delay=random.randint(50, 150))
        logger.info("Caption entered")
        
        page.wait_for_timeout(random.randint(6000, 9000))
        
        # Click "Share" button with state checking
        logger.info("Clicking Share button")
        if not _wait_for_button_enabled(page, "Share", timeout=30000):
            raise Exception("Share button failed - cannot complete upload")
        
        # Wait a moment for submission
        page.wait_for_timeout(3000)
        
        # Be HONEST about what we know
        logger.warning("Instagram upload submitted - no deterministic confirmation available")
        result = "Instagram upload submitted (status unverified)"
        
        # Navigate to about:blank for next uploader
        manager.navigate_to_blank(page)
        manager.close_page(page)
        
        return result
        
    except Exception as e:
        logger.error(f"Instagram browser upload failed: {str(e)}")
        if page:
            try:
                manager = BraveBrowserManager.get_instance()
                manager.close_page(page)
            except:
                pass
        return None
