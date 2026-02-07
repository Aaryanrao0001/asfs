"""
TikTok uploader using Brave browser automation.

Navigates to TikTok upload page and automates the upload process.
"""

import os
import logging
from typing import Optional
from .brave_base import BraveBrowserBase

logger = logging.getLogger(__name__)


def upload_to_tiktok_browser(
    video_path: str,
    title: str,
    description: str,
    tags: str,
    brave_path: Optional[str] = None,
    profile_path: Optional[str] = None
) -> Optional[str]:
    """
    Upload video to TikTok via Brave browser automation.
    
    Args:
        video_path: Path to video file
        title: Video title
        description: Video description
        tags: Space-separated tags (e.g., "#viral #trending")
        brave_path: Path to Brave executable (optional, auto-detect)
        profile_path: Path to Brave profile to reuse login (optional)
        
    Returns:
        Success message if upload completed, None if failed
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    logger.info("Starting TikTok browser upload")
    
    try:
        browser = BraveBrowserBase(brave_path, profile_path)
        page = browser.launch(headless=False)
        
        # Navigate to TikTok upload page
        logger.info("Navigating to TikTok upload page")
        page.goto("https://www.tiktok.com/upload", wait_until="networkidle")
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
    return upload_to_tiktok_browser(
        video_path=video_path,
        title=caption[:100],  # TikTok title has limits
        description=caption,
        tags=tags,
        brave_path=brave_path,
        profile_path=profile_path
    )
