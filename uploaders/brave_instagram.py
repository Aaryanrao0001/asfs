"""
Instagram uploader using Brave browser automation.

Navigates to Instagram and automates the Reels upload process.
"""

import os
import logging
from typing import Optional
from .brave_base import BraveBrowserBase

logger = logging.getLogger(__name__)


def upload_to_instagram_browser(
    video_path: str,
    title: str,
    description: str,
    tags: str,
    brave_path: Optional[str] = None,
    profile_path: Optional[str] = None
) -> Optional[str]:
    """
    Upload video to Instagram Reels via Brave browser automation.
    
    Args:
        video_path: Path to video file
        title: Video title (used in caption)
        description: Video description
        tags: Space-separated tags (e.g., "#viral #trending")
        brave_path: Path to Brave executable (optional, auto-detect)
        profile_path: Path to Brave profile to reuse login (optional)
        
    Returns:
        Success message if upload completed, None if failed
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    logger.info("Starting Instagram browser upload")
    
    try:
        browser = BraveBrowserBase(brave_path, profile_path)
        page = browser.launch(headless=False)
        
        # Navigate to Instagram
        logger.info("Navigating to Instagram")
        page.goto("https://www.instagram.com/", wait_until="networkidle")
        browser.human_delay(2, 4)
        
        # Check if user is logged in
        if "login" in page.url.lower() or page.query_selector('input[name="username"]'):
            logger.warning("Instagram login required - please log in manually")
            logger.info("Waiting 60 seconds for manual login...")
            page.wait_for_timeout(60000)
            logger.info("Continuing with upload")
        
        # Click "Create" button (+ icon)
        logger.info("Clicking Create button")
        try:
            # Common selectors for Create button:
            # - svg[aria-label="New post"]
            # - a[href="#"] containing "Create"
            # - [role="link"] containing Create text
            create_selector = 'svg[aria-label*="New"], a[href*="create"], [role="menuitem"]:has-text("Create")'
            page.wait_for_selector(create_selector, timeout=10000)
            browser.click_and_wait(create_selector, delay=2)
        except Exception as e:
            logger.warning(f"Primary Create selector failed, trying alternative: {e}")
            # Alternative: look for specific icon or text
            page.click('text="Create"')
            browser.human_delay(2, 3)
        
        # Upload video file
        logger.info("Uploading video file")
        try:
            # File input is usually hidden, trigger it via button click then file selection
            file_input_selector = 'input[type="file"]'
            browser.upload_file(file_input_selector, video_path)
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            # Instagram may require clicking "Select from computer" first
            try:
                page.click('button:has-text("Select from computer")')
                browser.human_delay(1, 2)
                browser.upload_file('input[type="file"]', video_path)
            except:
                raise
        
        browser.human_delay(3, 5)
        
        # Wait for upload processing
        logger.info("Waiting for video processing...")
        page.wait_for_timeout(5000)
        
        # Click "Next" through the editing steps
        logger.info("Navigating through editing steps")
        for i in range(3):  # Usually 2-3 "Next" clicks needed
            try:
                next_button = page.wait_for_selector('button:has-text("Next")', timeout=5000)
                if next_button:
                    next_button.click()
                    browser.human_delay(2, 3)
            except:
                break  # No more Next buttons
        
        # Fill in caption (title + description + tags)
        full_caption = f"{title}\n\n{description}\n\n{tags}".strip()
        
        logger.info("Filling caption")
        try:
            # Caption field selector
            caption_selector = 'textarea[aria-label*="caption"], textarea[placeholder*="caption"]'
            browser.human_type(caption_selector, full_caption)
        except Exception as e:
            logger.warning(f"Caption input failed: {e}")
        
        browser.human_delay(2, 3)
        
        # Click "Share" button
        logger.info("Clicking Share button")
        try:
            share_button_selector = 'button:has-text("Share")'
            page.wait_for_selector(share_button_selector, timeout=5000)
            browser.click_and_wait(share_button_selector, delay=3)
        except Exception as e:
            logger.error(f"Failed to click Share: {e}")
        
        # Wait for upload confirmation
        logger.info("Waiting for upload confirmation...")
        page.wait_for_timeout(5000)
        
        # Check for success indicators
        # Instagram shows "Your reel has been shared" or similar
        content = page.content().lower()
        
        if "shared" in content or "posted" in content:
            logger.info("Instagram upload completed successfully")
            result = "Instagram upload successful"
        else:
            logger.warning("Upload status unclear - manual verification recommended")
            result = "Instagram upload submitted (verify manually)"
        
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
    
    Args:
        video_path: Path to video file
        caption: Video caption
        hashtags: List of hashtags
        credentials: Dictionary with optional brave_path and profile_path
        
    Returns:
        Upload ID/result if successful, None if failed
    """
    # Extract browser settings from credentials
    brave_path = credentials.get("brave_path")
    profile_path = credentials.get("brave_profile_path")
    
    # Format hashtags
    tags = " ".join(hashtags) if hashtags else ""
    
    # Use caption as both title and description
    return upload_to_instagram_browser(
        video_path=video_path,
        title=caption[:100],
        description=caption,
        tags=tags,
        brave_path=brave_path,
        profile_path=profile_path
    )
