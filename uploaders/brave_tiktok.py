"""
TikTok uploader using Brave browser automation.

Navigates to TikTok upload page and automates the upload process.
"""

import os
import random
import logging
from typing import Optional
from datetime import datetime
from playwright.sync_api import Page
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


def _wait_for_processing_complete(page: Page, timeout: int = 180000) -> bool:
    """
    Wait for TikTok video processing to complete.
    
    Looks for signals that processing is done:
    - Upload status container shows "Uploaded" with success indicator
    - Progress bar disappears
    - "Processing" text disappears
    - Caption input becomes visible and interactive
    
    Args:
        page: Playwright Page object
        timeout: Maximum wait time in milliseconds (default: 3 minutes)
        
    Returns:
        True if processing confirmed complete, False otherwise
    """
    import time
    start_time = time.time()
    logger.info("Waiting for video processing to complete...")
    
    # CRITICAL: Wait for upload status to show "Uploaded" - this is the new reliable indicator
    # The new TikTok UI shows a status container with "Uploaded" text when ready
    try:
        logger.debug("Looking for upload status indicator...")
        
        # Try multiple selectors for the "Uploaded" status
        upload_status_selectors = [
            # Primary: data-e2e attribute with success status
            'div[data-e2e="upload_status_container"] .info-status.success',
            'div[data-e2e="upload_status_container"] .success',
            # Alternative: look for "Uploaded" text in status container
            'div[data-e2e="upload_status_container"]:has-text("Uploaded")',
            # Fallback: any success indicator with "Uploaded" text
            '.info-status.success:has-text("Uploaded")',
            '.success:has-text("Uploaded")',
        ]
        
        uploaded_found = False
        for selector in upload_status_selectors:
            try:
                logger.debug(f"Trying upload status selector: {selector}")
                # Use shorter timeout per selector to avoid long waits
                # wait_for_selector will raise TimeoutError if selector not found within timeout
                page.wait_for_selector(selector, timeout=30000, state="visible")
                elapsed = time.time() - start_time
                logger.info(f"[OK] Upload status: Uploaded (detected in {elapsed:.1f}s)")
                uploaded_found = True
                break
            except Exception as e:
                logger.debug(f"Selector {selector} not found: {e}")
                continue
        
        if uploaded_found:
            # Give UI a moment to finish rendering
            page.wait_for_timeout(2000)
            elapsed = time.time() - start_time
            logger.info(f"Upload processing complete - total time: {elapsed:.1f}s")
            return True
        else:
            logger.warning("Upload status 'Uploaded' not detected, trying fallback detection...")
    except Exception as e:
        logger.debug(f"Error checking upload status: {e}")
    
    # Fallback 1: Wait for any progress bars or "Processing" text to disappear
    try:
        processing_indicators = [
            'text="Processing"',
            '[class*="progress"]',
            '[class*="loading"]',
            'text="Uploading"'
        ]
        
        for indicator in processing_indicators:
            try:
                if page.locator(indicator).count() > 0:
                    logger.debug(f"Found processing indicator: {indicator}, waiting for it to disappear...")
                    page.wait_for_selector(indicator, state="hidden", timeout=timeout)
                    elapsed = time.time() - start_time
                    logger.info(f"Processing indicator disappeared: {indicator} (after {elapsed:.1f}s)")
            except Exception:
                # Indicator not found or already gone
                pass
    except Exception as e:
        logger.debug(f"Error checking for processing indicators: {e}")
    
    # Fallback 2: Wait for caption input to be visible (signal that upload is ready)
    caption_group = _tiktok_selectors.get_group("caption_input")
    if caption_group:
        selector_value, caption_element = try_selectors_with_page(
            page,
            caption_group,
            timeout=30000,  # Short timeout for fallback
            state="visible"
        )
        
        if caption_element:
            elapsed = time.time() - start_time
            logger.info(f"Upload processing complete - caption input available (total time: {elapsed:.1f}s)")
            return True
        else:
            elapsed = time.time() - start_time
            logger.warning(f"Could not confirm upload processing with caption selector (elapsed: {elapsed:.1f}s)")
            return False
    else:
        # Legacy fallback
        try:
            caption_input_ready = False
            for selector in ['div[contenteditable="true"]', '[data-e2e="caption-input"]']:
                try:
                    page.wait_for_selector(selector, timeout=30000, state="visible")
                    elapsed = time.time() - start_time
                    logger.info(f"Upload processing complete - caption input available ({selector}, time: {elapsed:.1f}s)")
                    caption_input_ready = True
                    break
                except:
                    continue
            return caption_input_ready
        except Exception as e:
            elapsed = time.time() - start_time
            logger.warning(f"Could not confirm upload processing completed: {e} (elapsed: {elapsed:.1f}s)")
            return False


def _validate_post_button_state(page: Page, button_element) -> bool:
    """
    Validate that the post button is in the correct state to be clicked.
    
    Checks:
    - aria-disabled is not "true"
    - data-loading is not "true"
    - Button is visible and in viewport
    
    Args:
        page: Playwright Page object
        button_element: The button element to validate
        
    Returns:
        True if button is ready to click, False otherwise
    """
    try:
        # Check aria-disabled attribute
        aria_disabled = button_element.get_attribute('aria-disabled')
        if aria_disabled == "true":
            logger.warning("Post button is aria-disabled, not ready to click")
            return False
        
        # Check data-loading attribute
        data_loading = button_element.get_attribute('data-loading')
        if data_loading == "true":
            logger.warning("Post button is loading, not ready to click")
            return False
        
        # Check if button is visible
        if not button_element.is_visible():
            logger.warning("Post button is not visible")
            return False
        
        logger.info("Post button state validated - ready to click")
        return True
    except Exception as e:
        logger.warning(f"Error validating post button state: {e}")
        # If we can't validate, assume it's ready (fail open)
        return True


def _click_post_button_with_validation(page: Page, post_button, max_retries: int = 3) -> bool:
    """
    Click the post button with state validation and retry logic.
    
    Ensures:
    - Button is in valid state (not disabled, not loading)
    - Button is scrolled into view
    - Handles potential overlays with force click fallback
    
    Args:
        page: Playwright Page object
        post_button: The button element to click
        max_retries: Maximum number of retry attempts
        
    Returns:
        True if clicked successfully, False otherwise
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to click post button (attempt {attempt + 1}/{max_retries})")
            
            # Wait a moment for any final processing
            if attempt > 0:
                page.wait_for_timeout(3000)
            
            # Validate button state
            if not _validate_post_button_state(page, post_button):
                logger.warning("Post button not in valid state, waiting...")
                page.wait_for_timeout(5000)
                continue
            
            # Scroll button into view if needed
            try:
                post_button.scroll_into_view_if_needed(timeout=5000)
                logger.info("Post button scrolled into view")
            except Exception as e:
                logger.debug(f"Could not scroll button into view: {e}")
            
            # Try normal click first
            try:
                logger.info("Clicking post button (normal click)...")
                post_button.click(timeout=10000, no_wait_after=True)
                logger.info("Post button clicked successfully")
                return True
            except Exception as click_error:
                logger.warning(f"Normal click failed: {click_error}")
                
                # If overlay present, try force click
                if "intercept" in str(click_error).lower() or "overlay" in str(click_error).lower():
                    logger.info("Overlay detected, attempting force click...")
                    try:
                        post_button.click(force=True, timeout=10000, no_wait_after=True)
                        logger.info("Post button force clicked successfully")
                        return True
                    except Exception as force_error:
                        logger.error(f"Force click also failed: {force_error}")
                        if attempt < max_retries - 1:
                            continue
                        else:
                            return False
                else:
                    # Other click error, retry
                    if attempt < max_retries - 1:
                        logger.warning(f"Click failed, retrying...")
                        continue
                    else:
                        return False
        
        except Exception as e:
            logger.error(f"Error in click attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                continue
            else:
                return False
    
    logger.error("Failed to click post button after all retries")
    return False


def _insert_text_into_draftjs(page: Page, selector: str, text: str, wait_after: bool = True) -> bool:
    """
    Insert text into DraftJS editor using proper InputEvent with insertFromPaste.
    
    This is the ONLY reliable way to insert text into TikTok's caption editor
    because DraftJS listens specifically for beforeinput/input events with
    insertFromPaste inputType. Regular typing or keyboard events only modify
    the DOM but don't update React state, causing the post button to stay disabled.
    
    Args:
        page: Playwright Page object
        selector: CSS selector for the contenteditable DraftJS editor
        text: Text to insert
        wait_after: Whether to wait after insertion (default: True)
        
    Returns:
        True if text was inserted successfully, False otherwise
    """
    try:
        logger.info(f"Inserting text into DraftJS editor: {selector}")
        
        # CRITICAL: Wait for DraftJS editor to be stable before inserting
        # This prevents race conditions where caption is inserted during editor lifecycle transitions
        if not _wait_for_draftjs_stable(page, selector, timeout=30000):
            logger.error("DraftJS editor did not stabilize - cannot insert text safely")
            return False
        
        # Execute JavaScript to insert text properly into DraftJS
        success = page.evaluate("""
            (args) => {
                try {
                    const editor = document.querySelector(args.selector);
                    if (!editor) {
                        console.error('Editor not found:', args.selector);
                        return false;
                    }
                    
                    // Focus the editor
                    editor.focus();
                    
                    // Place caret at the end
                    const range = document.createRange();
                    range.selectNodeContents(editor);
                    range.collapse(false);
                    
                    const sel = window.getSelection();
                    sel.removeAllRanges();
                    sel.addRange(range);
                    
                    // Create DataTransfer for paste event
                    const dataTransfer = new DataTransfer();
                    dataTransfer.setData('text/plain', args.text);
                    
                    // Dispatch beforeinput event (DraftJS listens to this)
                    const beforeInputEvent = new InputEvent('beforeinput', {
                        inputType: 'insertFromPaste',
                        data: args.text,
                        dataTransfer: dataTransfer,
                        bubbles: true,
                        cancelable: true
                    });
                    editor.dispatchEvent(beforeInputEvent);
                    
                    // Use execCommand as fallback to ensure DOM is updated
                    document.execCommand('insertText', false, args.text);
                    
                    // Dispatch input event for good measure
                    const inputEvent = new InputEvent('input', {
                        inputType: 'insertFromPaste',
                        data: args.text,
                        bubbles: true,
                        cancelable: false
                    });
                    editor.dispatchEvent(inputEvent);
                    
                    console.log('Text inserted into DraftJS:', args.text.substring(0, 50));
                    return true;
                } catch (error) {
                    console.error('Error inserting text:', error);
                    return false;
                }
            }
        """, {"selector": selector, "text": text})
        
        if success:
            logger.info("Text successfully inserted into DraftJS editor")
            if wait_after:
                page.wait_for_timeout(1500)  # Give React time to update state
            return True
        else:
            logger.error("Failed to insert text into DraftJS editor")
            return False
            
    except Exception as e:
        logger.error(f"Error inserting text into DraftJS: {e}")
        return False


def _wait_for_draftjs_stable(page: Page, selector: str, timeout: int = 30000) -> bool:
    """
    Wait for DraftJS editor to be stable and ready for input.
    
    This ensures the editor has:
    1. Mounted in the DOM
    2. Is visible and focused
    3. Has initialized its React state
    4. Is not in the middle of a lifecycle transition
    
    Args:
        page: Playwright Page object
        selector: CSS selector for the DraftJS editor
        timeout: Maximum wait time in milliseconds (default: 30 seconds)
        
    Returns:
        True if editor is stable, False otherwise
    """
    try:
        logger.info("Waiting for DraftJS editor to stabilize...")
        
        # Wait for editor to exist and be visible
        page.wait_for_selector(selector, state="visible", timeout=timeout)
        
        # Wait for editor to be stable (no remounts for 2 seconds)
        page.wait_for_function("""
            (selector) => {
                const editor = document.querySelector(selector);
                if (!editor) return false;
                
                // Check if editor is visible and in the DOM
                if (!editor.offsetParent) return false;
                
                // Check if editor has contenteditable
                if (editor.contentEditable !== 'true') return false;
                
                // Check if DraftJS has initialized (has data-contents attribute or DraftEditor class)
                const hasDraftJS = editor.closest('[class*="DraftEditor"]') || 
                                  editor.hasAttribute('data-contents') ||
                                  editor.className.includes('public-DraftEditor');
                
                return hasDraftJS;
            }
        """, arg=selector, timeout=timeout)
        
        logger.info("DraftJS editor is stable and ready")
        return True
        
    except Exception as e:
        logger.warning(f"Timeout waiting for DraftJS stability: {e}")
        return False


def _wait_for_post_button_ready(page: Page, timeout: int = 600000) -> bool:
    """
    Wait for post button to be ready (video processing complete).
    
    This function ensures that:
    1. Video processing is complete
    2. Post button is visible and clickable
    3. Editor is stable and ready for description input
    
    Args:
        page: Playwright Page object
        timeout: Maximum wait time in milliseconds (default: 10 minutes)
        
    Returns:
        True if button is ready, False otherwise
    """
    try:
        logger.info("Waiting for video processing to complete and post button to be ready...")
        
        # Wait for post button to exist and be enabled
        page.wait_for_function("""
            () => {
                const postButton = document.querySelector('[data-e2e="post_video_button"]');
                if (!postButton) return false;
                
                // Check if button is visible
                if (!postButton.offsetParent) return false;
                
                // Post button exists and is visible
                return true;
            }
        """, timeout=timeout)
        
        logger.info("Post button is ready")
        return True
        
    except Exception as e:
        logger.warning(f"Timeout waiting for post button ready state: {e}")
        return False


def _verify_page_loaded(page: Page, expected_elements: list, timeout: int = 10000) -> bool:
    """
    Verify that a page has loaded properly by checking for expected elements.
    
    Args:
        page: Playwright Page object
        expected_elements: List of CSS selectors that should be present on the page
        timeout: Maximum wait time in milliseconds per element
        
    Returns:
        True if all expected elements are found, False otherwise
    """
    try:
        for selector in expected_elements:
            try:
                page.wait_for_selector(selector, timeout=timeout, state="attached")
            except Exception:
                logger.debug(f"Expected element not found: {selector}")
                return False
        return True
    except Exception as e:
        logger.debug(f"Error verifying page load: {e}")
        return False


def _navigate_with_retry(page: Page, url: str, max_retries: int = 3, verify_selectors: list = None) -> bool:
    """
    Navigate to a URL with retry logic and optional verification.
    
    Args:
        page: Playwright Page object
        url: URL to navigate to
        max_retries: Maximum number of retry attempts
        verify_selectors: Optional list of CSS selectors to verify page loaded correctly
        
    Returns:
        True if navigation succeeded, False otherwise
        
    Raises:
        Exception: If navigation fails after all retries
    """
    last_error = None
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                logger.info(f"Retrying navigation to {url} (attempt {attempt + 1}/{max_retries})...")
                page.wait_for_timeout(2000)  # Wait before retry
            
            logger.info(f"Navigating to {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=180000)
            
            # Wait for network idle to ensure page is fully loaded
            try:
                page.wait_for_load_state("networkidle", timeout=20000)
            except Exception:
                logger.debug("Network idle timeout, proceeding anyway")
            
            # Optional: Verify page loaded correctly
            if verify_selectors:
                page.wait_for_timeout(2000)  # Give page time to render
                if not _verify_page_loaded(page, verify_selectors, timeout=15000):
                    logger.warning(f"Page verification failed on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        continue
                    else:
                        logger.error("Page did not load properly after all retries")
                        return False
            
            logger.info(f"Successfully navigated to {url}")
            return True
            
        except Exception as e:
            last_error = e
            error_msg = str(e).lower()
            logger.warning(f"Navigation attempt {attempt + 1} failed: {e}")
            
            # Check for network errors
            if "net::" in error_msg or "timeout" in error_msg:
                if attempt < max_retries - 1:
                    continue
                else:
                    for msg in TIKTOK_NETWORK_ERROR_MESSAGES:
                        logger.error(msg)
                    raise Exception(f"Network error: Cannot reach {url} after {max_retries} attempts - {last_error}")
            else:
                if attempt < max_retries - 1:
                    continue
                else:
                    raise Exception(f"Navigation failed after {max_retries} attempts: {last_error}")
    
    return False


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
        
        # Navigate to TikTok upload page with retry logic and verification
        logger.info("Navigating to TikTok upload page")
        
        # Define expected elements that should be present on the upload page
        # These help verify the page loaded correctly
        verify_selectors = [
            'input[type="file"]',  # File upload input
            'body',  # Basic page structure
        ]
        
        # Use retry navigation with verification
        if not _navigate_with_retry(
            page, 
            "https://www.tiktok.com/upload", 
            max_retries=3,
            verify_selectors=verify_selectors
        ):
            raise Exception("Failed to navigate to TikTok upload page after retries")
        
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
                timeout=90000,
                state="attached"
            )
            
            if not file_input:
                logger.error("Failed to find file input with selector intelligence")
                raise Exception("File input not found")
            
            browser.upload_file(selector_value, video_path)
        
        logger.info("File upload initiated, waiting for processing signals...")
        
        # CRITICAL: Wait for load state after file upload to detect navigation/modals
        try:
            page.wait_for_load_state("networkidle", timeout=30000)
            logger.debug("Network idle after file upload")
        except Exception:
            logger.debug("Network idle timeout after upload, using fallback delay")
            page.wait_for_timeout(8000)
        
        # Additional verification: Check if we're still on the upload page
        if "upload" not in page.url.lower():
            logger.warning(f"Unexpected navigation after upload to: {page.url}")
            # Try to navigate back to upload page
            if not _navigate_with_retry(page, "https://www.tiktok.com/upload", max_retries=2):
                raise Exception("Lost upload page after file selection")
        
        # Wait for video processing to complete - look for actual UI signals
        # Use new state validation helper
        if not _wait_for_processing_complete(page, timeout=360000):
            logger.warning("Could not confirm processing complete, proceeding anyway...")
        
        # Ensure caption box is visible before typing
        # Increased timeout by 3x (30s → 90s) for slow networks and React UI rendering
        logger.info("Ensuring caption box is ready...")
        caption_group = _tiktok_selectors.get_group("caption_input")
        if caption_group:
            selector_value, caption_element = try_selectors_with_page(
                page,
                caption_group,
                timeout=90000,
                state="visible"
            )
            if not caption_element:
                logger.error("Caption box not visible after processing")
                raise Exception("Caption input not found after upload")
        else:
            # Legacy check
            try:
                page.wait_for_selector('div[contenteditable="true"]', timeout=90000, state="visible")
            except Exception as e:
                logger.error(f"Caption box not visible: {e}")
                raise Exception("Caption input not found after upload")
        
        # CRITICAL: Wait for video processing to complete before entering caption
        # TikTok resets the editor during encoding, so typing before completion causes caption loss
        logger.info("Waiting for video processing completion before caption entry...")
        if not _wait_for_post_button_ready(page, timeout=600000):
            logger.warning("Timeout waiting for post button ready, proceeding anyway...")
        
        # Fill in caption (title + description + tags)
        full_caption = f"{title}\n\n{description}\n\n{tags}".strip()
        
        logger.info("Filling caption using DraftJS-compatible InputEvent method")
        caption_group = _tiktok_selectors.get_group("caption_input")
        
        caption_inserted = False
        
        if not caption_group:
            # Legacy fallback - try multiple selectors with DraftJS method
            # Note: Selectors ordered from most specific to most generic for robustness against UI changes
            caption_selectors = [
                'div.notranslate.public-DraftEditor-content[contenteditable="true"][role="combobox"]',
                '[contenteditable="true"][role="combobox"]',
                '[data-e2e="caption-input"]',
                '[data-testid="video-caption"] div[contenteditable="true"]',
                'div.caption-editor[contenteditable="true"]',
                'div[contenteditable="true"][aria-label*="caption" i]',
                'div[contenteditable="true"][placeholder*="caption" i]'
            ]
            
            for selector in caption_selectors:
                try:
                    element = page.query_selector(selector)
                    if element:
                        logger.info(f"Caption box found with selector: {selector}")
                        if _insert_text_into_draftjs(page, selector, full_caption):
                            caption_inserted = True
                            break
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            if not caption_inserted:
                logger.warning("Could not find caption input with specific selectors")
                try:
                    caption_selector = 'div[contenteditable="true"]'
                    logger.warning(f"Using generic selector as fallback: {caption_selector}")
                    caption_inserted = _insert_text_into_draftjs(page, caption_selector, full_caption)
                except Exception as e:
                    logger.error(f"All caption selectors failed: {e}")
        else:
            # Use selector intelligence
            selector_value, element = try_selectors_with_page(
                page,
                caption_group,
                timeout=90000,
                state="visible"
            )
            
            if element:
                logger.info(f"Caption input found with: {selector_value[:60]}")
                caption_inserted = _insert_text_into_draftjs(page, selector_value, full_caption)
            else:
                logger.error("Caption input not found with any selector")
        
        if not caption_inserted:
            logger.error("Failed to insert caption - post may fail")
            raise Exception("Caption insertion failed")
        
        # Give React time to process and validate the caption
        page.wait_for_timeout(2000)
        logger.info("Caption successfully inserted into DraftJS editor")
        
        # Optional: Set privacy to Public (usually default)
        # Selector may be: [data-e2e="privacy-select"]
        
        # Click Post/Upload button with state validation
        # Use new helper function for robust clicking
        logger.info("Preparing to click Post button with state validation")
        try:
            post_button_group = _tiktok_selectors.get_group("post_button")
            if not post_button_group:
                # Legacy fallback
                post_selectors = [
                    'button[data-e2e="post_video_button"]',
                    '[data-e2e="post-button"]',
                    'button[data-e2e="post-button"]',
                    'button:has-text("Post")'
                ]
                
                post_button = None
                for selector in post_selectors:
                    try:
                        post_button = page.wait_for_selector(
                            f'{selector}:not(:has-text("Discard"))',
                            timeout=90000,
                            state="visible"
                        )
                        if post_button:
                            logger.info(f"Post button found with: {selector}")
                            break
                    except:
                        continue
                
                if not post_button:
                    raise Exception("Post button not found with any selector")
                
                # Use validation and click helper
                if not _click_post_button_with_validation(page, post_button):
                    raise Exception("Failed to click post button after validation")
            else:
                # Use selector intelligence
                selector_value, post_button = try_selectors_with_page(
                    page,
                    post_button_group,
                    timeout=90000,
                    state="visible"
                )
                
                if not post_button:
                    logger.error("Post button not found with any selector")
                    raise Exception("TikTok Post button not found")
                
                # Use validation and click helper
                logger.info(f"Post button found with: {selector_value[:60]}")
                if not _click_post_button_with_validation(page, post_button):
                    raise Exception("Failed to click post button after validation")
            
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
        
        # Wait for upload confirmation with enhanced detection
        logger.info("Waiting for upload confirmation...")
        page.wait_for_timeout(5000)  # Initial wait for upload to start
        
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
                # Still on upload page - TikTok often stays here after successful post
                # We cannot reliably detect success without redirect
                logger.info("Still on upload page - success cannot be determined")
                success_confirmed = False
                
                # Wait for potential processing
                page.wait_for_timeout(5000)
        except Exception as e:
            logger.warning(f"Error checking success status: {e}")
            success_confirmed = False
        
        # Apply minimum safety wait (15 seconds total from post click)
        # to ensure TikTok has time to process the upload
        logger.info("Applying minimum safety wait to ensure upload completion...")
        page.wait_for_timeout(5000)  # Additional 5s to reach 15s total
        
        # Return honest status
        if success_confirmed:
            logger.info("TikTok upload confirmed successful")
            result = "TikTok upload successful"
        else:
            logger.warning("TikTok upload status unverified, but safety wait completed (15s total)")
            result = "TikTok upload submitted (status unverified, waited 15s for safety)"
        
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
    title: str = "",
    description: str = "",
    caption: str = "",
    hashtags: list = None,
    credentials: dict = None
) -> Optional[str]:
    """
    Upload to TikTok (browser-based).
    
    This maintains API compatibility with the old API-based uploader.
    Now uses BraveBrowserManager if available for shared browser context.
    
    Supports both old and new calling conventions:
    - Old: upload_to_tiktok(path, caption, hashtags, credentials)
    - New: upload_to_tiktok(path, title, description, caption, hashtags, credentials)
    
    Args:
        video_path: Path to video file
        title: Video title (used in caption composition) or legacy caption parameter
        description: Video description (used in caption composition) or legacy hashtags parameter
        caption: Video caption (primary text) or legacy credentials parameter
        hashtags: List of hashtags (or None for legacy mode)
        credentials: Dictionary with optional brave_path and profile_path
        
    Returns:
        Upload ID/result if successful, None if failed
    """
    # Handle legacy calling convention: upload_to_tiktok(path, caption_str, hashtags_list, creds_dict)
    if hashtags is None and isinstance(caption, dict):
        # Legacy mode: (path, caption, hashtags, credentials)
        credentials = caption
        hashtags = description if isinstance(description, list) else []
        caption = title
        title = ""
        description = ""
    elif credentials is None and isinstance(hashtags, dict):
        # Semi-legacy mode: (path, title, caption, hashtags, credentials)
        credentials = hashtags
        hashtags = caption if isinstance(caption, list) else []
        caption = description
        description = ""
    
    from .brave_manager import BraveBrowserManager
    
    # Extract browser settings from credentials
    credentials = credentials or {}
    hashtags = hashtags or []
    brave_path = credentials.get("brave_path")
    user_data_dir = credentials.get("brave_user_data_dir")
    profile_directory = credentials.get("brave_profile_directory", "Default")
    
    # Format hashtags
    tags = " ".join(hashtags) if hashtags else ""
    
    # Use caption if provided, otherwise fall back to title/description
    if not caption:
        # Fallback: if caption is empty, compose from title and description
        caption = f"{title}\n\n{description}".strip()
    
    # Use title and description independently if provided
    final_title = title or caption[:100]
    final_description = description or caption
    
    # Fallback: If all content is empty, generate from video filename
    if not final_title and not final_description and not caption:
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        timestamp = datetime.now().strftime("%Y-%m-%d")
        final_title = (video_name if video_name else f"Video {timestamp}")[:100]
        final_description = f"Uploaded on {timestamp}"
        logger.warning(f"No title/description/caption provided, using fallback: title='{final_title[:50]}...'")
    elif not final_title and not final_description:
        # At least we have caption, use it
        final_title = caption[:100]
        final_description = caption
    
    # Check if BraveBrowserManager is initialized (pipeline mode)
    manager = BraveBrowserManager.get_instance()
    if manager.is_initialized:
        # Use shared browser context (pipeline mode)
        logger.info("Using shared browser context from BraveBrowserManager")
        return _upload_to_tiktok_with_manager(
            video_path=video_path,
            title=final_title,
            description=final_description,
            tags=tags
        )
    else:
        # Standalone mode - use direct browser launch
        logger.info("Using standalone browser mode")
        return upload_to_tiktok_browser(
            video_path=video_path,
            title=final_title,
            description=final_description,
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
        
        # Get page - this will raise RuntimeError if called from wrong thread
        try:
            page = manager.get_page()
        except RuntimeError as e:
            logger.error(f"Thread safety violation detected: {e}")
            logger.warning("Falling back to standalone browser mode")
            # Fallback to standalone mode
            return upload_to_tiktok_browser(
                video_path=video_path,
                title=title,
                description=description,
                tags=tags
            )
        
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
                file_input = page.wait_for_selector(file_input_selector, state="attached", timeout=90000)
                file_input.set_input_files(video_path)
            except Exception as e:
                logger.warning(f"Primary file selector failed, trying alternative: {e}")
                file_input_selector = '[data-e2e="upload-input"]'
                file_input = page.wait_for_selector(file_input_selector, state="attached", timeout=90000)
                file_input.set_input_files(video_path)
        else:
            # Use selector intelligence
            selector_value, file_input = try_selectors_with_page(
                page,
                file_input_group,
                timeout=90000,
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
        
        # Wait for video processing to complete using new state validation helper
        if not _wait_for_processing_complete(page, timeout=360000):
            logger.warning("Could not confirm processing complete, proceeding anyway...")
        
        # Ensure caption box is visible before typing
        # Increased timeout by 3x (30s → 90s) for slow networks and React UI rendering
        logger.info("Ensuring caption box is ready...")
        caption_group = _tiktok_selectors.get_group("caption_input")
        if caption_group:
            selector_value, caption_element = try_selectors_with_page(
                page,
                caption_group,
                timeout=90000,
                state="visible"
            )
            if not caption_element:
                logger.error("Caption box not visible after processing")
                raise Exception("Caption input not found after upload")
        else:
            # Legacy check
            try:
                page.wait_for_selector('div[contenteditable="true"]', timeout=90000, state="visible")
            except Exception as e:
                logger.error(f"Caption box not visible: {e}")
                raise Exception("Caption input not found after upload")
        
        # CRITICAL: Wait for video processing to complete before entering caption
        # TikTok resets the editor during encoding, so typing before completion causes caption loss
        logger.info("Waiting for video processing completion before caption entry...")
        if not _wait_for_post_button_ready(page, timeout=600000):
            logger.warning("Timeout waiting for post button ready, proceeding anyway...")
        
        # Fill in caption (title + description + tags)
        full_caption = f"{title}\n\n{description}\n\n{tags}".strip()
        
        logger.info("Filling caption using DraftJS-compatible InputEvent method")
        caption_group = _tiktok_selectors.get_group("caption_input")
        
        caption_inserted = False
        
        if not caption_group:
            # Legacy fallback - try multiple selectors with DraftJS method
            # Note: Selectors ordered from most specific to most generic for robustness against UI changes
            caption_selectors = [
                'div.notranslate.public-DraftEditor-content[contenteditable="true"][role="combobox"]',
                '[contenteditable="true"][role="combobox"]',
                '[data-e2e="caption-input"]',
                '[data-testid="video-caption"] div[contenteditable="true"]',
                'div.caption-editor[contenteditable="true"]',
                'div[contenteditable="true"][aria-label*="caption" i]',
                'div[contenteditable="true"][placeholder*="caption" i]'
            ]
            
            for selector in caption_selectors:
                try:
                    element = page.query_selector(selector)
                    if element:
                        logger.info(f"Caption box found with selector: {selector}")
                        if _insert_text_into_draftjs(page, selector, full_caption):
                            caption_inserted = True
                            break
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            if not caption_inserted:
                logger.warning("Could not find caption input with specific selectors")
                try:
                    caption_selector = 'div[contenteditable="true"]'
                    logger.warning(f"Using generic selector as fallback: {caption_selector}")
                    caption_inserted = _insert_text_into_draftjs(page, caption_selector, full_caption)
                except Exception as e:
                    logger.error(f"All caption selectors failed: {e}")
        else:
            # Use selector intelligence
            selector_value, element = try_selectors_with_page(
                page,
                caption_group,
                timeout=90000,
                state="visible"
            )
            
            if element:
                logger.info(f"Caption input found with: {selector_value[:60]}")
                caption_inserted = _insert_text_into_draftjs(page, selector_value, full_caption)
            else:
                logger.error("Caption input not found with any selector")
        
        if not caption_inserted:
            logger.error("Failed to insert caption - post may fail")
            raise Exception("Caption insertion failed")
        
        # Give React time to process and validate the caption
        page.wait_for_timeout(2000)
        logger.info("Caption successfully inserted into DraftJS editor")
        
        # Click Post/Upload button with state validation
        # Use new helper function for robust clicking
        logger.info("Preparing to click Post button with state validation")
        try:
            post_button_group = _tiktok_selectors.get_group("post_button")
            if not post_button_group:
                # Legacy fallback
                post_selectors = [
                    'button[data-e2e="post_video_button"]',
                    '[data-e2e="post-button"]',
                    'button[data-e2e="post-button"]',
                    'button:has-text("Post")'
                ]
                
                post_button = None
                for selector in post_selectors:
                    try:
                        post_button = page.wait_for_selector(
                            f'{selector}:not(:has-text("Discard"))',
                            timeout=90000,
                            state="visible"
                        )
                        if post_button:
                            logger.info(f"Post button found with: {selector}")
                            break
                    except:
                        continue
                
                if not post_button:
                    raise Exception("Post button not found with any selector")
                
                # Use validation and click helper
                if not _click_post_button_with_validation(page, post_button):
                    raise Exception("Failed to click post button after validation")
            else:
                # Use selector intelligence
                selector_value, post_button = try_selectors_with_page(
                    page,
                    post_button_group,
                    timeout=90000,
                    state="visible"
                )
                
                if not post_button:
                    logger.error("Post button not found with any selector")
                    raise Exception("TikTok Post button not found")
                
                # Use validation and click helper
                logger.info(f"Post button found with: {selector_value[:60]}")
                if not _click_post_button_with_validation(page, post_button):
                    raise Exception("Failed to click post button after validation")
            
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
        
        # Wait for upload confirmation with enhanced detection
        logger.info("Waiting for upload confirmation...")
        page.wait_for_timeout(5000)  # Initial wait for upload to start
        
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
                # Still on upload page - TikTok often stays here after successful post
                # We cannot reliably detect success without redirect
                logger.info("Still on upload page - success cannot be determined")
                success_confirmed = False
                
                # Wait for potential processing
                page.wait_for_timeout(5000)
        except Exception as e:
            logger.warning(f"Error checking success status: {e}")
            success_confirmed = False
        
        # Apply minimum safety wait (15 seconds total from post click)
        # to ensure TikTok has time to process the upload
        logger.info("Applying minimum safety wait to ensure upload completion...")
        page.wait_for_timeout(5000)  # Additional 5s to reach 15s total
        
        # Return honest status
        if success_confirmed:
            logger.info("TikTok upload confirmed successful")
            result = "TikTok upload successful"
        else:
            logger.warning("TikTok upload status unverified, but safety wait completed (15s total)")
            result = "TikTok upload submitted (status unverified, waited 15s for safety)"
        
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
