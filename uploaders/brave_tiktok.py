"""
TikTok uploader using Brave browser automation.

Navigates to TikTok upload page and automates the upload process.
"""

import os
import random
import logging
from typing import Optional
from .brave_base import BraveBrowserBase
from .selectors import get_tiktok_selectors, try_selectors_with_page

logger = logging.getLogger(__name__)

# Initialize TikTok selector manager (with intelligence)
_tiktok_selectors = get_tiktok_selectors()

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
            page.goto("https://www.tiktok.com/upload", wait_until="domcontentloaded", timeout=180000)
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
            logger.info("Waiting 90 seconds for manual login...")
            # Wait for upload interface to become available (functional check, not URL-based)
            try:
                page.wait_for_selector('input[type="file"]', timeout=270000, state="attached")
                logger.info("Login successful - upload interface detected")
            except Exception:
                # Check if still on login page
                if "login" in page.url.lower():
                    raise Exception("Manual login failed or timed out - still on login page")
                else:
                    raise Exception("Upload interface not found after login - TikTok UI may have changed")
        
        # Upload video file using selector intelligence with adaptive ranking
        # Automatically tries multiple selector strategies based on success history
        logger.info("Uploading video file")
        
        file_input_group = _tiktok_selectors.get_group("file_input")
        if not file_input_group:
            # Fallback to legacy behavior
            try:
                file_input_selector = 'input[type="file"]'
                browser.upload_file(file_input_selector, video_path)
            except Exception as e:
                logger.warning(f"Primary file selector failed, trying alternative: {e}")
                file_input_selector = '[data-e2e="upload-input"]'
                browser.upload_file(file_input_selector, video_path)
        else:
            # Use selector intelligence
            selector_value, file_input = try_selectors_with_page(
                page,
                file_input_group,
                timeout=30000,
                state="attached"
            )
            
            if not file_input:
                logger.error("Failed to find file input with selector intelligence")
                raise Exception("File input not found")
            
            browser.upload_file(selector_value, video_path)
        
        logger.info("File upload initiated, waiting for processing signals...")
        
        # CRITICAL: Wait for load state after file upload to detect navigation/modals
        try:
            page.wait_for_load_state("networkidle", timeout=20000)
            logger.debug("Network idle after file upload")
        except Exception:
            logger.debug("Network idle timeout after upload, using fallback delay")
            page.wait_for_timeout(5000)
        
        # Wait for video processing to complete - look for actual UI signals
        # Use selector intelligence to detect caption input (indicates upload processed)
        logger.info("Waiting for upload processing to complete...")
        
        caption_group = _tiktok_selectors.get_group("caption_input")
        if caption_group:
            # Try with extended timeout for upload processing
            selector_value, caption_element = try_selectors_with_page(
                page,
                caption_group,
                timeout=360000,  # 6 minutes for large video processing
                state="visible"
            )
            
            if caption_element:
                logger.info(f"Upload processing complete - caption input available")
            else:
                logger.warning("Could not confirm upload processing with caption selector")
                page.wait_for_timeout(15000)
        else:
            # Legacy fallback
            try:
                caption_input_ready = False
                for selector in ['[data-e2e="caption-input"]', 'div[contenteditable="true"]']:
                    try:
                        page.wait_for_selector(selector, timeout=360000, state="visible")
                        logger.info(f"Upload processing complete - caption input available ({selector})")
                        caption_input_ready = True
                        break
                    except:
                        continue
                if not caption_input_ready:
                    raise Exception("Caption input not found after upload")
            except Exception as e:
                logger.warning(f"Could not confirm upload processing completed: {e}")
                page.wait_for_timeout(15000)
        
        # Fill in caption (title + description + tags)
        full_caption = f"{title}\n\n{description}\n\n{tags}".strip()
        
        logger.info("Filling caption with selector intelligence")
        caption_group = _tiktok_selectors.get_group("caption_input")
        
        if not caption_group:
            # Legacy fallback
            caption_selectors = [
                '[data-e2e="caption-input"]',
                '[data-testid="video-caption"] div[contenteditable="true"]',
                'div.caption-editor[contenteditable="true"]',
                'div[contenteditable="true"][aria-label*="caption" i]',
                'div[contenteditable="true"][placeholder*="caption" i]'
            ]
            
            caption_found = False
            for selector in caption_selectors:
                try:
                    element = page.query_selector(selector)
                    if element:
                        logger.info(f"Caption box found with selector: {selector}")
                        browser.human_type(selector, full_caption)
                        caption_found = True
                        break
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            if not caption_found:
                logger.warning("Could not find caption input with specific selectors - upload may fail")
                try:
                    caption_selector = 'div[contenteditable="true"]'
                    logger.warning(f"Using generic selector as fallback: {caption_selector}")
                    browser.human_type(caption_selector, full_caption)
                except:
                    logger.error("All caption selectors failed - caption not entered")
        else:
            # Use selector intelligence
            selector_value, element = try_selectors_with_page(
                page,
                caption_group,
                timeout=30000,
                state="visible"
            )
            
            if element:
                logger.info(f"Caption input found with: {selector_value[:60]}")
                browser.human_type(selector_value, full_caption)
            else:
                logger.error("Caption input not found with any selector")
                raise Exception("Caption input not found")
        
        browser.human_delay(2, 3)
        
        # Optional: Set privacy to Public (usually default)
        # Selector may be: [data-e2e="privacy-select"]
        
        # Click Post/Upload button using selector intelligence
        # Stable selectors: data-e2e + role-based + text fallbacks (prioritized)
        logger.info("Clicking Post button")
        try:
            post_button_group = _tiktok_selectors.get_group("post_button")
            if not post_button_group:
                # Legacy fallback
                post_selectors = [
                    '[data-e2e="post-button"]',
                    'div[role="button"]:has-text("Post")',
                    'button:has-text("Post")'
                ]
                post_button_selector = ', '.join([f'{s}:not(:has-text("Discard"))' for s in post_selectors])
                
                post_button = page.wait_for_selector(post_button_selector, timeout=30000, state="visible")
                
                logger.info("Submitting post (preventing premature navigation)...")
                post_button.click(no_wait_after=True)
                logger.info("Post button clicked successfully")
            else:
                # Use selector intelligence
                selector_value, post_button = try_selectors_with_page(
                    page,
                    post_button_group,
                    timeout=30000,
                    state="visible"
                )
                
                if not post_button:
                    logger.error("Post button not found with any selector")
                    raise Exception("TikTok Post button not found")
                
                # CRITICAL: Use no_wait_after=True to prevent browser context closure
                logger.info("Submitting post (preventing premature navigation)...")
                post_button.click(no_wait_after=True)
                logger.info("Post button clicked successfully")
            
            # CRITICAL: Wait for load state after post to detect success/navigation
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
                logger.debug("Network idle after post submission")
            except Exception:
                logger.debug("Network idle timeout after post, continuing...")
                page.wait_for_timeout(9000)
        except Exception as e:
            logger.error(f"Failed to click Post button: {e}")
            # Re-raise with context to preserve exception chain
            raise Exception(f"TikTok Post button click failed: {e}") from e
        
        # Wait for upload confirmation
        logger.info("Waiting for upload confirmation...")
        page.wait_for_timeout(15000)
        
        # Check for success indicators - be honest about what we can detect
        current_url = page.url
        success_confirmed = False
        
        # Try to detect actual success signals
        try:
            # Check if we got redirected away from upload page
            if "upload" not in current_url.lower():
                logger.info("Redirected away from upload page - likely successful")
                success_confirmed = True
            else:
                # Still on upload page - check for success elements
                # Note: We cannot reliably detect success if still on /upload
                # TikTok often stays on upload page after successful post
                logger.info("Still on upload page - success cannot be confirmed")
                success_confirmed = False
        except Exception as e:
            logger.warning(f"Error checking success status: {e}")
            success_confirmed = False
        
        # Return honest status
        if success_confirmed:
            logger.info("Upload confirmed successful")
            result = "TikTok upload successful"
        else:
            logger.warning("Upload submitted - success not verified (manual verification recommended)")
            result = "TikTok upload submitted (status unverified)"
        
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
            page.goto("https://www.tiktok.com/upload", wait_until="domcontentloaded", timeout=180000)
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
            logger.info("Waiting 90 seconds for manual login...")
            # Wait for upload interface to become available (functional check, not URL-based)
            try:
                page.wait_for_selector('input[type="file"]', timeout=270000, state="attached")
                logger.info("Login successful - upload interface detected")
            except Exception:
                # Check if still on login page
                if "login" in page.url.lower():
                    raise Exception("Manual login failed or timed out - still on login page")
                else:
                    raise Exception("Upload interface not found after login - TikTok UI may have changed")
        
        # Upload video file using selector intelligence with adaptive ranking
        # Automatically tries multiple selector strategies based on success history
        logger.info("Uploading video file")
        
        file_input_group = _tiktok_selectors.get_group("file_input")
        if not file_input_group:
            # Legacy fallback
            try:
                file_input_selector = 'input[type="file"]'
                file_input = page.wait_for_selector(file_input_selector, state="attached", timeout=30000)
                file_input.set_input_files(video_path)
            except Exception as e:
                logger.warning(f"Primary file selector failed, trying alternative: {e}")
                file_input_selector = '[data-e2e="upload-input"]'
                file_input = page.wait_for_selector(file_input_selector, state="attached", timeout=30000)
                file_input.set_input_files(video_path)
        else:
            # Use selector intelligence
            selector_value, file_input = try_selectors_with_page(
                page,
                file_input_group,
                timeout=30000,
                state="attached"
            )
            
            if not file_input:
                logger.error("Failed to find file input with selector intelligence")
                raise Exception("File input not found")
            
            file_input.set_input_files(video_path)
        
        logger.info("File upload initiated, waiting for processing signals...")
        
        # CRITICAL: Wait for load state after file upload
        try:
            page.wait_for_load_state("networkidle", timeout=20000)
            logger.debug("Network idle after file upload")
        except Exception:
            logger.debug("Network idle timeout after upload, using fallback delay")
            page.wait_for_timeout(5000)
        
        # Wait for video processing to complete using selector intelligence
        logger.info("Waiting for upload processing to complete...")
        
        caption_group = _tiktok_selectors.get_group("caption_input")
        if caption_group:
            # Try with extended timeout for upload processing
            selector_value, caption_element = try_selectors_with_page(
                page,
                caption_group,
                timeout=360000,  # 6 minutes for large video processing
                state="visible"
            )
            
            if caption_element:
                logger.info(f"Upload processing complete - caption input available")
            else:
                logger.warning("Could not confirm upload processing with caption selector")
                page.wait_for_timeout(15000)
        else:
            # Legacy fallback
            try:
                caption_input_ready = False
                for selector in ['[data-e2e="caption-input"]', 'div[contenteditable="true"]']:
                    try:
                        page.wait_for_selector(selector, timeout=360000, state="visible")
                        logger.info(f"Upload processing complete - caption input available ({selector})")
                        caption_input_ready = True
                        break
                    except:
                        continue
                if not caption_input_ready:
                    raise Exception("Caption input not found after upload")
            except Exception as e:
                logger.warning(f"Could not confirm upload processing completed: {e}")
                page.wait_for_timeout(15000)
        
        # Fill in caption (title + description + tags)
        full_caption = f"{title}\n\n{description}\n\n{tags}".strip()
        
        logger.info("Filling caption with selector intelligence")
        caption_group = _tiktok_selectors.get_group("caption_input")
        
        if not caption_group:
            # Legacy fallback
            caption_selectors = [
                '[data-e2e="caption-input"]',
                '[data-testid="video-caption"] div[contenteditable="true"]',
                'div.caption-editor[contenteditable="true"]',
                'div[contenteditable="true"][aria-label*="caption" i]',
                'div[contenteditable="true"][placeholder*="caption" i]'
            ]
            
            caption_found = False
            for selector in caption_selectors:
                try:
                    element = page.query_selector(selector)
                    if element:
                        logger.info(f"Caption box found with selector: {selector}")
                        element.click()
                        page.keyboard.press("Control+A")
                        page.keyboard.press("Backspace")
                        for char in full_caption:
                            element.type(char, delay=random.uniform(50, 150))
                        caption_found = True
                        break
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            if not caption_found:
                logger.warning("Could not find caption input with specific selectors - upload may fail")
                try:
                    caption_selector = 'div[contenteditable="true"]'
                    logger.warning(f"Using generic selector as fallback: {caption_selector}")
                    element = page.wait_for_selector(caption_selector, timeout=30000)
                    element.click()
                    page.keyboard.press("Control+A")
                    page.keyboard.press("Backspace")
                    for char in full_caption:
                        element.type(char, delay=random.uniform(50, 150))
                except:
                    logger.error("All caption selectors failed - caption not entered")
        else:
            # Use selector intelligence
            selector_value, element = try_selectors_with_page(
                page,
                caption_group,
                timeout=30000,
                state="visible"
            )
            
            if element:
                logger.info(f"Caption input found with: {selector_value[:60]}")
                element.click()
                page.keyboard.press("Control+A")
                page.keyboard.press("Backspace")
                for char in full_caption:
                    element.type(char, delay=random.uniform(50, 150))
            else:
                logger.error("Caption input not found with any selector")
                raise Exception("Caption input not found")
        
        page.wait_for_timeout(random.randint(6000, 9000))
        
        # Click Post/Upload button using selector intelligence
        # Stable selectors: data-e2e + role-based + text fallbacks (prioritized)
        logger.info("Clicking Post button")
        try:
            post_button_group = _tiktok_selectors.get_group("post_button")
            if not post_button_group:
                # Legacy fallback
                post_selectors = [
                    '[data-e2e="post-button"]',
                    'div[role="button"]:has-text("Post")',
                    'button:has-text("Post")'
                ]
                post_button_selector = ', '.join([f'{s}:not(:has-text("Discard"))' for s in post_selectors])
                
                post_button = page.wait_for_selector(post_button_selector, timeout=30000, state="visible")
                
                logger.info("Submitting post (preventing premature navigation)...")
                post_button.click(no_wait_after=True)
                logger.info("Post button clicked successfully")
            else:
                # Use selector intelligence
                selector_value, post_button = try_selectors_with_page(
                    page,
                    post_button_group,
                    timeout=30000,
                    state="visible"
                )
                
                if not post_button:
                    logger.error("Post button not found with any selector")
                    raise Exception("TikTok Post button not found")
                
                # CRITICAL: Use no_wait_after=True to prevent browser context closure
                logger.info("Submitting post (preventing premature navigation)...")
                post_button.click(no_wait_after=True)
                logger.info("Post button clicked successfully")
            
            # CRITICAL: Wait for load state after post to detect success/navigation
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
                logger.debug("Network idle after post submission")
            except Exception:
                logger.debug("Network idle timeout after post, continuing...")
                page.wait_for_timeout(9000)
        except Exception as e:
            logger.error(f"Failed to click Post button: {e}")
            # Re-raise with context to preserve exception chain
            raise Exception(f"TikTok Post button click failed: {e}") from e
        
        # Wait for upload confirmation
        logger.info("Waiting for upload confirmation...")
        page.wait_for_timeout(15000)
        
        # Check for success indicators - be honest about what we can detect
        current_url = page.url
        success_confirmed = False
        
        # Try to detect actual success signals
        try:
            # Check if we got redirected away from upload page
            if "upload" not in current_url.lower():
                logger.info("Redirected away from upload page - likely successful")
                success_confirmed = True
            else:
                # Still on upload page - check for success elements
                # Note: We cannot reliably detect success if still on /upload
                # TikTok often stays on upload page after successful post
                logger.info("Still on upload page - success cannot be confirmed")
                success_confirmed = False
        except Exception as e:
            logger.warning(f"Error checking success status: {e}")
            success_confirmed = False
        
        # Return honest status
        if success_confirmed:
            logger.info("Upload confirmed successful")
            result = "TikTok upload successful"
        else:
            logger.warning("Upload submitted - success not verified (manual verification recommended)")
            result = "TikTok upload submitted (status unverified)"
        
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
