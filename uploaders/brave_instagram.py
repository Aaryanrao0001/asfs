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
from .selectors import get_instagram_selectors, try_selectors_with_page

logger = logging.getLogger(__name__)

# Initialize Instagram selector manager (with intelligence)
_instagram_selectors = get_instagram_selectors()

# Maximum number of buttons to log for debugging when selector fails
MAX_BUTTONS_TO_LOG = 10

# Instagram Create button selector - ONLY use the stable one
# Instagram's UI is modal-based and this is the only consistently reliable trigger
# If this selector fails, Instagram changed UI - log hard error and STOP
INSTAGRAM_CREATE_SELECTORS = [
    'svg[aria-label="New post"]',  # Single reliable selector
]
INSTAGRAM_CREATE_SELECTOR = INSTAGRAM_CREATE_SELECTORS[0]

# Share button keyboard navigation timeouts (in milliseconds)
# These control the TAB+TAB+ENTER keyboard shortcut approach
KEYBOARD_FOCUS_WAIT_MS = 500   # Wait after focusing caption input
KEYBOARD_TAB_WAIT_MS = 300     # Wait between TAB key presses
KEYBOARD_SUBMIT_WAIT_MS = 3000 # Wait after pressing ENTER to trigger upload

# Legacy button click enhancement timeouts (in milliseconds)
# These are kept for backwards compatibility with Next button logic
OVERLAY_CLEAR_WAIT_MS = 2000  # Wait time after detecting overlay

# JS click expression for fallback when standard click fails
JS_CLICK_EXPRESSION = 'el => el.click()'


def _try_js_click(button, button_text: str = "button") -> bool:
    """
    Attempt to click a button using JavaScript evaluation.
    
    Instagram's React-based buttons sometimes have JS event handlers that don't
    respond to standard Playwright clicks. This function uses JS evaluation to
    trigger the click event directly.
    
    Args:
        button: Playwright Locator object for the button
        button_text: Text of the button for logging purposes
        
    Returns:
        True if click succeeded, False otherwise
    """
    try:
        button.evaluate(JS_CLICK_EXPRESSION)
        logger.info(f"{button_text} clicked using JS (el.click())")
        return True
    except Exception as e:
        logger.debug(f"JS click failed for {button_text}: {e}")
        return False


def _wait_for_button_enabled(page: Page, button_text: str, timeout: int = 90000) -> bool:
    """
    Click button only when it's enabled and ready.
    
    Instagram disables buttons while processing uploads/crops.
    Clicking early results in ignored clicks.
    
    Uses robust selector fallback strategy:
    1. Try text-based selectors with has-text()
    2. Fallback to role-based selector with manual text filtering (tabindex="0" required)
    3. Last resort: role-based selector without tabindex requirement
    4. For multiple matches, select last visible and enabled button
    5. Scroll into view if needed before clicking
    
    Enhanced click strategy:
    1. Check for overlays/spinners before clicking
    2. Try standard Playwright click first
    3. Fallback to JS click (evaluate) if standard click fails
    
    Args:
        page: Playwright Page object
        button_text: Text of the button (e.g., "Next")
        timeout: Timeout in milliseconds (default: 90000, 3x increased)
        
    Returns:
        True if button clicked successfully, False otherwise
    """
    import time
    try:
        button = None
        successful_selector = None
        
        # Strategy 1: Try text-based selectors (Playwright's :has-text() pseudo-selector)
        text_selectors = [
            f'div[role="button"]:has-text("{button_text}")',
            f'button:has-text("{button_text}")',
            f'[role="button"]:has-text("{button_text}")',
        ]
        
        logger.info(f"Searching for '{button_text}' button with text-based selectors")
        for selector in text_selectors:
            try:
                btn = page.locator(selector).first
                btn.wait_for(state="visible", timeout=10000)
                button = btn
                successful_selector = selector
                logger.info(f"{button_text} button found with selector: {selector}")
                break
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue
        
        # Strategy 2: Fallback to role-based selector with manual text filtering
        if not button:
            logger.info(f"Text-based selectors failed, trying role-based with manual filtering")
            try:
                # Find all div[role="button"][tabindex="0"] elements
                role_selector = 'div[role="button"][tabindex="0"]'
                all_buttons = page.locator(role_selector).all()
                
                logger.info(f"Found {len(all_buttons)} div[role='button'][tabindex='0'] elements")
                
                # Filter by text content (case insensitive, trimmed)
                matching_buttons = []
                for btn in all_buttons:
                    try:
                        text_content = btn.text_content()
                        if text_content and button_text.lower() in text_content.strip().lower():
                            # Check if button is visible
                            if btn.is_visible():
                                matching_buttons.append(btn)
                                logger.debug(f"Found matching button with text: '{text_content.strip()}'")
                    except Exception:
                        continue
                
                if matching_buttons:
                    # Use last matching button (Instagram tends to create clones)
                    button = matching_buttons[-1]
                    successful_selector = f"{role_selector} (filtered by text '{button_text}', selected last of {len(matching_buttons)})"
                    logger.info(f"{button_text} button found with role-based selector: {successful_selector}")
                else:
                    logger.warning(f"No visible buttons with text '{button_text}' found among {len(all_buttons)} role buttons")
            except Exception as e:
                logger.warning(f"Role-based selector strategy failed: {e}")
        
        # Strategy 3: Last resort - try without tabindex requirement
        if not button:
            logger.info(f"Trying fallback without tabindex requirement")
            try:
                fallback_selector = f'div[role="button"]'
                all_buttons = page.locator(fallback_selector).all()
                
                logger.info(f"Found {len(all_buttons)} div[role='button'] elements (no tabindex filter)")
                
                matching_buttons = []
                for btn in all_buttons:
                    try:
                        text_content = btn.text_content()
                        if text_content and button_text.lower() in text_content.strip().lower():
                            if btn.is_visible():
                                matching_buttons.append(btn)
                                logger.debug(f"Found matching button with text: '{text_content.strip()}'")
                    except Exception:
                        continue
                
                if matching_buttons:
                    # Use last matching button (Instagram tends to create clones)
                    button = matching_buttons[-1]
                    successful_selector = f"{fallback_selector} (filtered by text '{button_text}', selected last of {len(matching_buttons)})"
                    logger.info(f"{button_text} button found with fallback selector: {successful_selector}")
            except Exception as e:
                logger.warning(f"Fallback selector strategy failed: {e}")
        
        if not button:
            # Log all buttons found for debugging
            logger.error(f"{button_text} button not found with any selector strategy")
            try:
                logger.error("Attempting to log all role='button' elements for audit:")
                all_role_buttons = page.locator('[role="button"]').all()
                for i, btn in enumerate(all_role_buttons[:MAX_BUTTONS_TO_LOG]):
                    try:
                        text = btn.text_content()
                        is_visible = btn.is_visible()
                        aria_disabled = btn.get_attribute('aria-disabled')
                        tabindex = btn.get_attribute('tabindex')
                        logger.error(f"  Button {i+1}: text='{text.strip() if text else ''}', visible={is_visible}, "
                                   f"aria-disabled={aria_disabled}, tabindex={tabindex}")
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"Could not log buttons for audit: {e}")
            return False
        
        # Scroll button into view if needed
        try:
            button.scroll_into_view_if_needed(timeout=5000)
            logger.debug(f"{button_text} button scrolled into view")
        except Exception as e:
            logger.debug(f"Could not scroll button into view (may already be visible): {e}")
        
        # Wait for button to be visible and attached
        button.wait_for(state="visible", timeout=timeout)
        logger.debug(f"{button_text} button visible")
        
        # Wait for button to be enabled (not disabled)
        # Instagram buttons are disabled via aria-disabled or disabled attribute
        start_time = time.time()
        max_wait = timeout / 1000  # Convert to seconds
        
        while True:
            elapsed = time.time() - start_time
            if elapsed > max_wait:
                logger.error(f"{button_text} button did not become enabled in {max_wait}s")
                return False
            
            # Check if button is disabled
            is_disabled = False
            try:
                aria_disabled = button.get_attribute('aria-disabled')
                disabled_attr = button.get_attribute('disabled')
                
                # Check for disabled state
                # - aria-disabled='true' indicates disabled
                # - disabled attribute present indicates disabled (HTML standard)
                # Note: In standard HTML, presence of 'disabled' means disabled regardless of value,
                # but Instagram/React may use aria-disabled for dynamic state instead
                if aria_disabled == 'true' or disabled_attr is not None:
                    is_disabled = True
                    logger.debug(f"{button_text} button still disabled, waiting... (elapsed: {elapsed:.1f}s)")
                    # Conservative 500ms polling interval to balance responsiveness with CPU usage
                    page.wait_for_timeout(500)
                else:
                    # Button is enabled
                    logger.info(f"{button_text} button enabled after {elapsed:.1f}s, ready to click")
                    break
            except Exception as e:
                # If we can't check attributes, assume it's ready
                logger.debug(f"Could not check disabled state, assuming ready: {e}")
                break
        
        # Now safe to click - Use enhanced click strategy for Share button
        # Instagram Share button sometimes requires special handling:
        # - Standard click may not trigger JS handlers
        # - JS click (evaluate) as fallback
        # - Double-click retry if first attempt doesn't work
        # - Wait for button disappearance as success indicator
        
        # Check for overlays or spinners that might block the click
        try:
            # Look for common overlay/spinner patterns
            overlay_selectors = [
                'div[role="progressbar"]',
                'svg[aria-label*="Loading"]',
                '.spinner',
            ]
            has_overlay = False
            for overlay_sel in overlay_selectors:
                try:
                    if page.locator(overlay_sel).count() > 0:
                        has_overlay = True
                        logger.warning(f"Detected overlay/spinner with selector: {overlay_sel}")
                        break
                except Exception:
                    pass
            
            if has_overlay:
                logger.warning(f"Overlay detected before click, waiting {OVERLAY_CLEAR_WAIT_MS}ms for it to clear")
                page.wait_for_timeout(OVERLAY_CLEAR_WAIT_MS)
        except Exception as e:
            logger.debug(f"Could not check for overlays: {e}")
        
        # Strategy 1: Try standard Playwright click first
        click_success = False
        try:
            button.click()
            logger.info(f"{button_text} button clicked (standard click) using selector: {successful_selector}")
            click_success = True
        except Exception as e:
            logger.warning(f"Standard click failed: {e}, will try JS click fallback")
        
        # Strategy 2: Fallback to JS click if standard click failed
        if not click_success:
            if _try_js_click(button, f"{button_text} button (JS fallback)"):
                logger.info(f"{button_text} button clicked (JS click fallback) using selector: {successful_selector}")
                click_success = True
            else:
                logger.error(f"JS click fallback also failed for {button_text} button with selector: {successful_selector}")
                return False
        
        return True
    except PlaywrightTimeoutError:
        logger.error(f"{button_text} button did not become visible/ready in time")
        return False
    except Exception as e:
        logger.error(f"Error clicking {button_text} button: {e}")
        return False


def _find_caption_input(page: Page):
    """
    Find the caption input field using selector intelligence.
    
    Instagram has multiple div[role="textbox"] elements.
    We need to target the caption specifically to avoid typing into wrong fields.
    Uses selectors with ARIA labels: [aria-label*="caption"]
    
    Args:
        page: Playwright Page object
        
    Returns:
        Caption input element or None if not found
    """
    caption_group = _instagram_selectors.get_group("caption_input")
    if not caption_group:
        logger.error("Caption selector group not found in selector manager")
        return None
    
    selector_value, element = try_selectors_with_page(
        page, 
        caption_group, 
        timeout=15000,
        state="visible"
    )
    
    if element:
        logger.info(f"Caption box found with selector: {selector_value[:60]}")
        return element
    
    logger.error("Caption input not found with any selector")
    return None


def _trigger_share_with_keyboard(page: Page, caption_box) -> None:
    """
    Trigger Instagram Share button using keyboard navigation (TAB 11x + ENTER).
    
    This approach avoids DOM overlays, spinners, and phantom Share button clones
    that cause traditional click-based automation to fail.
    
    IMPORTANT: This assumes Instagram's UI tab order places the Share button
    exactly 11 TAB presses away from the caption input. If the first attempt
    fails, we refocus the caption, type a dummy character, and retry.
    
    Args:
        page: Playwright Page object
        caption_box: Caption input element (must be already found and filled)
        
    Returns:
        None on success
        
    Raises:
        Exception: If keyboard shortcut fails after fallback
    """
    logger.info("Focusing caption input and using TAB 11x + ENTER to trigger Share")
    
    def _attempt_tab_navigation(attempt_num: int = 1) -> bool:
        """
        Internal helper to attempt TAB navigation to Share button.
        
        Args:
            attempt_num: Attempt number for logging
            
        Returns:
            True if successful, False if needs retry
        """
        try:
            # Step 1: Ensure caption input is focused
            logger.info(f"Attempt {attempt_num}: Focusing caption input")
            caption_box.focus()
            page.wait_for_timeout(KEYBOARD_FOCUS_WAIT_MS)
            
            # Step 2: Press TAB 11 times to navigate to Share button
            logger.info(f"Attempt {attempt_num}: Pressing TAB 11 times to reach Share button")
            for i in range(11):
                page.keyboard.press("Tab")
                page.wait_for_timeout(KEYBOARD_TAB_WAIT_MS)
                if (i + 1) % 3 == 0 or (i + 1) == 11:  # Log every 3rd TAB and the final one
                    logger.info(f"Attempt {attempt_num}: Tabbing... ({i + 1}/11)")
            
            logger.info(f"Attempt {attempt_num}: All 11 TABs completed")
            
            # Step 3: Press ENTER to activate Share button
            logger.info(f"Attempt {attempt_num}: Attempting ENTER to activate Share")
            page.keyboard.press("Enter")
            logger.info(f"Attempt {attempt_num}: ENTER pressed - Share should be triggered")
            
            # Wait for upload transition
            page.wait_for_timeout(KEYBOARD_SUBMIT_WAIT_MS)
            
            return True
            
        except Exception as e:
            logger.error(f"Attempt {attempt_num}: Navigation failed: {e}")
            return False
    
    # First attempt
    if _attempt_tab_navigation(attempt_num=1):
        return
    
    # Fallback: Refocus caption, type dummy character, and retry
    logger.warning("First attempt failed, using fallback strategy")
    try:
        logger.info("Fallback: Clicking caption input to refocus")
        caption_box.click()
        page.wait_for_timeout(KEYBOARD_FOCUS_WAIT_MS)
        
        logger.info("Fallback: Typing dummy character (space)")
        page.keyboard.type(" ")
        page.wait_for_timeout(KEYBOARD_TAB_WAIT_MS)
        
        # Retry TAB navigation
        if _attempt_tab_navigation(attempt_num=2):
            logger.info("Fallback successful - Share triggered")
            return
        
        raise Exception("Share button keyboard navigation failed after fallback attempt")
        
    except Exception as e:
        logger.error(f"Fallback failed: {e}")
        raise Exception(f"Share button keyboard shortcut failed - cannot complete upload: {e}")


def _select_post_option(page: Page, timeout: int = 45000) -> bool:
    """
    Click the Post/Create option after opening Create menu.
    
    Instagram A/B tests multiple UI variants and now uses <a role="link"> elements.
    Waits for menu container to be ready, then uses prioritized selectors:
    1. a:has(svg[aria-label="Post"]) - most stable
    2. a:has-text("Post") - text-based
    3. a[role="link"]:has-text("Post") - hybrid
    4. Legacy div[role="button"] selectors - fallback
    
    Args:
        page: Playwright Page object
        timeout: Timeout in milliseconds (default: 45000, 3x increased)
        
    Returns:
        True if clicked successfully, False otherwise
    """
    import json
    from pathlib import Path
    
    # Wait for menu container to be fully open and ready
    logger.info("Waiting for Create menu container to be ready...")
    try:
        # Wait for menu container to appear (aria-hidden="false" indicates open menu)
        menu_container = page.wait_for_selector(
            'div[aria-hidden="false"]',
            timeout=15000,
            state="visible"
        )
        logger.info("Create menu container is open and ready")
        # Give React time to fully render menu items
        page.wait_for_timeout(2000)
    except Exception as e:
        logger.warning(f"Could not confirm menu container ready: {e}")
    
    # Log menu items for debugging and self-healing
    try:
        logger.info("Analyzing menu items...")
        menu_items = page.locator('a[role="link"]').all()
        menu_data = []
        
        for idx, item in enumerate(menu_items[:10]):  # Limit to first 10 items
            try:
                text = item.inner_text(timeout=1000) if item.is_visible() else ""
                aria_label = item.get_attribute('aria-label') or ""
                
                # Check for SVG aria-label inside the link
                svg_aria = ""
                try:
                    svg = item.locator('svg').first
                    if svg:
                        svg_aria = svg.get_attribute('aria-label') or ""
                except:
                    pass
                
                item_info = {
                    "order": idx,
                    "text": text.strip(),
                    "aria_label": aria_label,
                    "svg_aria_label": svg_aria
                }
                menu_data.append(item_info)
                logger.debug(f"Menu item {idx}: text='{text.strip()}', svg_aria='{svg_aria}'")
            except Exception as e:
                logger.debug(f"Could not analyze menu item {idx}: {e}")
                continue
        
        # Save menu variants to knowledge directory for self-healing
        if menu_data:
            # Use relative path from project root
            knowledge_dir = Path(__file__).parent.parent / "knowledge"
            knowledge_dir.mkdir(exist_ok=True)
            variants_file = knowledge_dir / "instagram_menu_variants.json"
            
            try:
                # Load existing variants if file exists
                existing_variants = []
                if variants_file.exists():
                    with open(variants_file, 'r') as f:
                        existing_variants = json.load(f)
                
                # Add timestamp to new data
                from datetime import datetime
                new_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "menu_items": menu_data
                }
                
                # Append new entry (keep last 50 entries)
                existing_variants.append(new_entry)
                existing_variants = existing_variants[-50:]
                
                # Save back to file
                with open(variants_file, 'w') as f:
                    json.dump(existing_variants, f, indent=2)
                
                logger.info(f"Logged {len(menu_data)} menu items to {variants_file}")
            except Exception as e:
                logger.warning(f"Could not save menu variants: {e}")
    except Exception as e:
        logger.warning(f"Could not analyze menu items: {e}")
    
    post_option_group = _instagram_selectors.get_group("post_option")
    if not post_option_group:
        logger.error("Post option selector group not found in selector manager")
        return False
    
    max_retries = 5  # Increased retries for slow networks
    
    for attempt in range(max_retries):
        logger.debug(f"Attempt {attempt + 1}/{max_retries} to find Post option")
        
        # Try all selectors ranked by intelligence system
        for selector in post_option_group.get_ranked_selectors():
            try:
                button = page.locator(selector.value)
                
                # Increased timeout by 3x for slow networks (3s → 9s)
                # Try to interact with the first matching element
                button.first.wait_for(state="visible", timeout=9000)
                
                # For link elements, just click (they don't have enabled/disabled state)
                if 'a[role="link"]' in selector.value or 'a:has' in selector.value:
                    logger.info(f"Found Post option (link): {selector.value}")
                else:
                    # For button elements, check if not disabled
                    aria_disabled = button.first.get_attribute('aria-disabled')
                    if aria_disabled == 'true':
                        logger.debug(f"Button is disabled, skipping: {selector.value}")
                        continue
                    logger.info(f"Found Post option (button): {selector.value}")
                
                button.first.click()
                logger.info("Post option clicked successfully")
                
                # Record success for adaptive learning
                post_option_group.record_success(selector.value)
                return True
            except Exception as e:
                logger.debug(f"Selector {selector.value} failed: {e}")
                post_option_group.record_failure(selector.value)
                continue
        
        # React animation may be slow - wait longer and retry (3s → 9s)
        if attempt < max_retries - 1:
            logger.debug("Menu may still be animating, waiting 9s before retry...")
            page.wait_for_timeout(9000)
    
    # Fallback: Try to click first visible menu item if all selectors failed
    logger.warning("All Post selectors failed - attempting fallback: click first menu item")
    try:
        first_item = page.locator('a[role="link"]').first
        if first_item.is_visible():
            first_item.click()
            logger.warning("Clicked first menu item as fallback")
            return True
    except Exception as e:
        logger.error(f"Fallback also failed: {e}")
    
    logger.error(f"Post option button not found with any variant after {max_retries} retries")
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
        
        # CRITICAL: Wait for load state after menu selection to prevent premature navigation
        # This prevents closing browser context/pages due to navigation or popups
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
            logger.debug("Network idle after Post option selection")
        except Exception:
            # Fallback to timeout if networkidle hangs
            logger.debug("Network idle timeout, using fallback delay")
            page.wait_for_timeout(random.randint(6000, 12000))
        
        # Upload video file
        # The file input appears AFTER selecting Post option
        logger.info("Waiting for file input to appear")
        
        file_input_group = _instagram_selectors.get_group("file_input")
        if not file_input_group:
            # Fallback to legacy behavior
            file_input_selector = 'input[type="file"][accept*="video"], input[type="file"][accept*="image"]'
            logger.warning("Using legacy file input selector")
        else:
            # Use selector intelligence
            selector_value, file_input = try_selectors_with_page(
                page,
                file_input_group,
                timeout=15000,
                state="attached"  # File inputs are often hidden
            )
            
            if not file_input:
                logger.error("Failed to find file input with selector intelligence")
                raise Exception("File input not found")
            
            file_input_selector = selector_value
        
        try:
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
        
        # Use keyboard shortcut to trigger Share button
        _trigger_share_with_keyboard(page, caption_box)
        
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
        
        # CRITICAL: Wait for load state after menu selection
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
            logger.debug("Network idle after Post option selection")
        except Exception:
            logger.debug("Network idle timeout, using fallback delay")
            page.wait_for_timeout(random.randint(6000, 12000))
        
        # Upload video file using selector intelligence
        logger.info("Waiting for file input to appear")
        
        file_input_group = _instagram_selectors.get_group("file_input")
        if not file_input_group:
            # Fallback to legacy
            file_input = page.wait_for_selector(
                'input[type="file"][accept*="video"], input[type="file"][accept*="image"]',
                state="attached",
                timeout=15000
            )
            logger.warning("Using legacy file input selector")
        else:
            # Use selector intelligence
            selector_value, file_input = try_selectors_with_page(
                page,
                file_input_group,
                timeout=15000,
                state="attached"
            )
            
            if not file_input:
                logger.error("Failed to find file input")
                raise Exception("File input not found")
        
        try:
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
        
        # Use keyboard shortcut to trigger Share button
        _trigger_share_with_keyboard(page, caption_box)
        
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
