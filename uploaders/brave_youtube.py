"""
YouTube Shorts uploader using Brave browser automation.

Navigates to YouTube Studio and automates the Shorts upload process.
"""

import os
import random
import logging
from typing import Optional
from .brave_base import BraveBrowserBase

logger = logging.getLogger(__name__)


def upload_to_youtube_browser(
    video_path: str,
    title: str,
    description: str,
    tags: str,
    brave_path: Optional[str] = None,
    user_data_dir: Optional[str] = None,
    profile_directory: str = "Default"
) -> Optional[str]:
    """
    Upload video to YouTube Shorts via Brave browser automation.
    
    Args:
        video_path: Path to video file
        title: Video title
        description: Video description
        tags: Comma or space-separated tags
        brave_path: Path to Brave executable (optional, auto-detect)
        user_data_dir: Path to Brave user data directory (optional, for login session reuse)
        profile_directory: Profile directory name (e.g., "Default", "Profile 1")
        
    Returns:
        Success message if upload completed, None if failed
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    logger.info("Starting YouTube Shorts browser upload")
    
    try:
        browser = BraveBrowserBase(brave_path, user_data_dir, profile_directory)
        page = browser.launch(headless=False)
        
        # Navigate to YouTube Studio upload
        logger.info("Navigating to YouTube Studio")
        page.goto("https://studio.youtube.com/", wait_until="networkidle")
        browser.human_delay(2, 4)
        
        # Check if user is logged in
        if "accounts.google.com" in page.url:
            logger.warning("YouTube login required - please log in manually")
            logger.info("Waiting 60 seconds for manual login...")
            page.wait_for_url("**/studio.youtube.com/**", timeout=60000)
            logger.info("Login successful, continuing upload")
        
        # Click "Create" button (video camera icon)
        logger.info("Clicking Create button")
        try:
            # YouTube Studio upload button
            create_selector = 'button[aria-label*="Create"], ytcp-button#create-icon'
            page.wait_for_selector(create_selector, timeout=10000)
            browser.click_and_wait(create_selector, delay=2)
        except Exception as e:
            logger.warning(f"Primary Create selector failed: {e}")
        
        # Click "Upload videos"
        logger.info("Clicking Upload videos")
        try:
            upload_selector = 'tp-yt-paper-item:has-text("Upload videos")'
            page.wait_for_selector(upload_selector, timeout=5000)
            browser.click_and_wait(upload_selector, delay=2)
        except Exception as e:
            logger.warning(f"Upload videos selector failed, trying alternative: {e}")
            page.click('text="Upload videos"')
            browser.human_delay(2, 3)
        
        # Upload video file
        logger.info("Uploading video file")
        try:
            file_input_selector = 'input[type="file"][name="Filedata"]'
            browser.upload_file(file_input_selector, video_path)
        except Exception as e:
            logger.warning(f"Primary file selector failed: {e}")
            # Alternative selector
            browser.upload_file('input[type="file"]', video_path)
        
        browser.human_delay(3, 5)
        
        # Wait for upload to start
        logger.info("Waiting for upload processing...")
        page.wait_for_timeout(5000)
        
        # Fill in title
        logger.info("Filling title")
        try:
            # Title input (contenteditable div or textbox)
            title_selector = 'div[aria-label*="title" i][contenteditable="true"], ytcp-social-suggestions-textbox[label*="Title" i] input'
            page.wait_for_selector(title_selector, timeout=10000)
            
            # Clear and type title
            element = page.query_selector(title_selector)
            element.click()
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            element.type(title, delay=100)
        except Exception as e:
            logger.warning(f"Failed to fill title: {e}")
        
        browser.human_delay(1, 2)
        
        # Fill in description
        logger.info("Filling description")
        try:
            description_selector = 'div[aria-label*="description" i][contenteditable="true"], ytcp-social-suggestions-textbox[label*="Description" i] textarea'
            element = page.wait_for_selector(description_selector, timeout=5000)
            element.click()
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            
            # Combine description and tags
            full_description = f"{description}\n\n{tags}".strip()
            element.type(full_description, delay=50)
        except Exception as e:
            logger.warning(f"Failed to fill description: {e}")
        
        browser.human_delay(2, 3)
        
        # Mark as "Not made for kids" (required)
        logger.info("Setting audience (Not made for kids)")
        try:
            # YouTube requires audience selection
            not_for_kids_selector = 'tp-yt-paper-radio-button[name="VIDEO_MADE_FOR_KIDS_NOT_MFK"]'
            page.wait_for_selector(not_for_kids_selector, timeout=5000)
            browser.click_and_wait(not_for_kids_selector, delay=1)
        except Exception as e:
            logger.warning(f"Failed to set audience: {e}")
        
        # Click "Next" through the upload steps
        logger.info("Navigating through upload steps")
        for i in range(3):  # Video elements, Checks, Visibility
            try:
                next_button = page.wait_for_selector('ytcp-button#next-button', timeout=5000)
                if next_button and next_button.is_enabled():
                    next_button.click()
                    browser.human_delay(2, 3)
            except:
                break
        
        # Set visibility to Public (or Unlisted/Private as needed)
        logger.info("Setting visibility to Public")
        try:
            # Public radio button
            public_selector = 'tp-yt-paper-radio-button[name="PUBLIC"]'
            page.wait_for_selector(public_selector, timeout=5000)
            browser.click_and_wait(public_selector, delay=2)
        except Exception as e:
            logger.warning(f"Failed to set visibility: {e}")
        
        # Click "Publish"
        logger.info("Clicking Publish button")
        try:
            publish_button = page.wait_for_selector('ytcp-button#done-button', timeout=10000)
            publish_button.click()
            browser.human_delay(3, 5)
        except Exception as e:
            logger.error(f"Failed to click Publish: {e}")
        
        # Wait for confirmation
        logger.info("Waiting for upload confirmation...")
        page.wait_for_timeout(5000)
        
        # Check for success
        content = page.content().lower()
        
        if "uploaded" in content or "published" in content or "processing" in content:
            logger.info("YouTube upload completed successfully")
            result = "YouTube upload successful"
        else:
            logger.warning("Upload status unclear - manual verification recommended")
            result = "YouTube upload submitted (verify manually)"
        
        browser.human_delay(2, 3)
        browser.close()
        
        return result
        
    except Exception as e:
        logger.error(f"YouTube browser upload failed: {str(e)}")
        if 'browser' in locals():
            browser.close()
        return None


# Backward compatibility wrapper
def upload_to_youtube(
    video_path: str,
    caption: str,
    hashtags: list,
    credentials: dict
) -> Optional[str]:
    """
    Upload to YouTube Shorts (browser-based).
    
    This maintains API compatibility with the old API-based uploader.
    Now uses BraveBrowserManager if available for shared browser context.
    
    Args:
        video_path: Path to video file
        caption: Video caption (used as description)
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
        return _upload_to_youtube_with_manager(
            video_path=video_path,
            title=caption[:100],
            description=caption,
            tags=tags
        )
    else:
        # Standalone mode - use direct browser launch
        logger.info("Using standalone browser mode")
        return upload_to_youtube_browser(
            video_path=video_path,
            title=caption[:100],  # YouTube title limit is 100 chars
            description=caption,
            tags=tags,
            brave_path=brave_path,
            user_data_dir=user_data_dir,
            profile_directory=profile_directory
        )


def _upload_to_youtube_with_manager(
    video_path: str,
    title: str,
    description: str,
    tags: str
) -> Optional[str]:
    """
    Upload to YouTube using shared browser from BraveBrowserManager.
    
    This function is called when pipeline has initialized the manager.
    It gets a page from the shared context instead of creating a new browser.
    """
    from .brave_manager import BraveBrowserManager
    
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    logger.info("Starting YouTube Shorts browser upload with shared context")
    
    page = None
    try:
        manager = BraveBrowserManager.get_instance()
        page = manager.get_page()
        
        # Navigate to YouTube Studio upload
        logger.info("Navigating to YouTube Studio")
        page.goto("https://studio.youtube.com/", wait_until="networkidle")
        page.wait_for_timeout(random.randint(2000, 4000))
        
        # Check if user is logged in
        if "accounts.google.com" in page.url:
            logger.warning("YouTube login required - please log in manually")
            logger.info("Waiting 60 seconds for manual login...")
            page.wait_for_url("**/studio.youtube.com/**", timeout=60000)
            logger.info("Login successful, continuing upload")
        
        # Click "Create" button (video camera icon)
        logger.info("Clicking Create button")
        try:
            create_selector = 'button[aria-label*="Create"], ytcp-button#create-icon'
            page.wait_for_selector(create_selector, timeout=10000)
            element = page.query_selector(create_selector)
            element.click()
            page.wait_for_timeout(2000)
        except Exception as e:
            logger.warning(f"Primary Create selector failed: {e}")
        
        # Click "Upload videos"
        logger.info("Clicking Upload videos")
        try:
            upload_selector = 'tp-yt-paper-item:has-text("Upload videos")'
            page.wait_for_selector(upload_selector, timeout=5000)
            element = page.query_selector(upload_selector)
            element.click()
            page.wait_for_timeout(2000)
        except Exception as e:
            logger.warning(f"Upload videos selector failed, trying alternative: {e}")
            page.click('text="Upload videos"')
            page.wait_for_timeout(random.randint(2000, 3000))
        
        # Upload video file
        logger.info("Uploading video file")
        try:
            # YouTube hides file inputs, so use state="attached" instead of visible
            file_input_selector = 'input[type="file"][name="Filedata"]'
            file_input = page.wait_for_selector(file_input_selector, state="attached", timeout=10000)
            file_input.set_input_files(video_path)
        except Exception as e:
            logger.warning(f"Primary file selector failed: {e}")
            # Fallback to any file input (hidden or visible)
            file_input = page.wait_for_selector('input[type="file"]', state="attached", timeout=10000)
            file_input.set_input_files(video_path)
        
        page.wait_for_timeout(random.randint(3000, 5000))
        
        # Wait for upload to start
        logger.info("Waiting for upload processing...")
        page.wait_for_timeout(5000)
        
        # Fill in title
        logger.info("Filling title")
        try:
            title_selector = 'div[aria-label*="title" i][contenteditable="true"], ytcp-social-suggestions-textbox[label*="Title" i] input'
            page.wait_for_selector(title_selector, timeout=10000)
            
            element = page.query_selector(title_selector)
            element.click()
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            element.type(title, delay=100)
        except Exception as e:
            logger.warning(f"Failed to fill title: {e}")
        
        page.wait_for_timeout(random.randint(1000, 2000))
        
        # Fill in description
        logger.info("Filling description")
        try:
            description_selector = 'div[aria-label*="description" i][contenteditable="true"], ytcp-social-suggestions-textbox[label*="Description" i] textarea'
            element = page.wait_for_selector(description_selector, timeout=5000)
            element.click()
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            
            full_description = f"{description}\n\n{tags}".strip()
            element.type(full_description, delay=50)
        except Exception as e:
            logger.warning(f"Failed to fill description: {e}")
        
        page.wait_for_timeout(random.randint(2000, 3000))
        
        # Mark as "Not made for kids" (required)
        logger.info("Setting audience (Not made for kids)")
        try:
            not_for_kids_selector = 'tp-yt-paper-radio-button[name="VIDEO_MADE_FOR_KIDS_NOT_MFK"]'
            page.wait_for_selector(not_for_kids_selector, timeout=5000)
            element = page.query_selector(not_for_kids_selector)
            element.click()
            page.wait_for_timeout(1000)
        except Exception as e:
            logger.warning(f"Failed to set audience: {e}")
        
        # Click "Next" through the upload steps
        logger.info("Navigating through upload steps")
        for i in range(3):
            try:
                next_button = page.wait_for_selector('ytcp-button#next-button', timeout=5000)
                if next_button and next_button.is_enabled():
                    next_button.click()
                    page.wait_for_timeout(random.randint(2000, 3000))
            except:
                break
        
        # Set visibility to Public
        logger.info("Setting visibility to Public")
        try:
            public_selector = 'tp-yt-paper-radio-button[name="PUBLIC"]'
            page.wait_for_selector(public_selector, timeout=5000)
            element = page.query_selector(public_selector)
            element.click()
            page.wait_for_timeout(2000)
        except Exception as e:
            logger.warning(f"Failed to set visibility: {e}")
        
        # Click "Publish"
        logger.info("Clicking Publish button")
        try:
            publish_button = page.wait_for_selector('ytcp-button#done-button', timeout=10000)
            publish_button.click()
            page.wait_for_timeout(random.randint(3000, 5000))
        except Exception as e:
            logger.error(f"Failed to click Publish: {e}")
        
        # Wait for confirmation
        logger.info("Waiting for upload confirmation...")
        page.wait_for_timeout(5000)
        
        # Check for success
        content = page.content().lower()
        
        if "uploaded" in content or "published" in content or "processing" in content:
            logger.info("YouTube upload completed successfully")
            result = "YouTube upload successful"
        else:
            logger.warning("Upload status unclear - manual verification recommended")
            result = "YouTube upload submitted (verify manually)"
        
        # Navigate to about:blank for next uploader
        manager.navigate_to_blank(page)
        manager.close_page(page)
        
        return result
        
    except Exception as e:
        logger.error(f"YouTube browser upload failed: {str(e)}")
        if page:
            try:
                manager = BraveBrowserManager.get_instance()
                manager.close_page(page)
            except:
                pass
        return None
