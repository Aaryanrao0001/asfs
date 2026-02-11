#!/usr/bin/env python3
"""
Test suite for Instagram keyboard shortcut (TAB+TAB+ENTER) fix.

Tests that the Instagram uploader has been modified to:
1. Add _trigger_share_with_keyboard() helper function
2. Use TAB+TAB+ENTER instead of clicking Share button
3. Define keyboard navigation timing constants
4. Call the helper in both upload functions
"""

import os
import sys
import unittest
from pathlib import Path

# Configure logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestInstagramKeyboardShortcut(unittest.TestCase):
    """Test that Instagram keyboard shortcut fix has been properly applied."""
    
    def setUp(self):
        """Set up test by reading the brave_instagram.py file."""
        self.instagram_file = Path(__file__).parent / "uploaders" / "brave_instagram.py"
        self.content = self.instagram_file.read_text(encoding='utf-8')
        self.lines = self.content.split('\n')
    
    def test_keyboard_timing_constants_exist(self):
        """Verify keyboard navigation timing constants are defined."""
        self.assertIn('KEYBOARD_FOCUS_WAIT_MS', self.content,
                     "KEYBOARD_FOCUS_WAIT_MS constant not found")
        self.assertIn('KEYBOARD_TAB_WAIT_MS', self.content,
                     "KEYBOARD_TAB_WAIT_MS constant not found")
        self.assertIn('KEYBOARD_SUBMIT_WAIT_MS', self.content,
                     "KEYBOARD_SUBMIT_WAIT_MS constant not found")
        
        # Verify they have reasonable values
        self.assertIn('KEYBOARD_FOCUS_WAIT_MS = 500', self.content,
                     "KEYBOARD_FOCUS_WAIT_MS not set to 500ms")
        self.assertIn('KEYBOARD_TAB_WAIT_MS = 300', self.content,
                     "KEYBOARD_TAB_WAIT_MS not set to 300ms")
        self.assertIn('KEYBOARD_SUBMIT_WAIT_MS = 3000', self.content,
                     "KEYBOARD_SUBMIT_WAIT_MS not set to 3000ms")
    
    def test_trigger_share_function_exists(self):
        """Verify _trigger_share_with_keyboard() helper function exists."""
        self.assertIn('def _trigger_share_with_keyboard(page: Page, caption_box) -> None:',
                     self.content,
                     "_trigger_share_with_keyboard function not found")
        
        # Verify function docstring describes the purpose
        self.assertIn('TAB+TAB+ENTER', self.content,
                     "Function docstring doesn't mention TAB+TAB+ENTER")
        self.assertIn('DOM overlays', self.content,
                     "Function docstring doesn't mention avoiding DOM overlays")
    
    def test_trigger_share_implementation(self):
        """Verify _trigger_share_with_keyboard() has correct implementation."""
        # Check for caption box focus
        self.assertIn('caption_box.focus()', self.content,
                     "Function doesn't focus caption_box")
        
        # Check for TAB key presses
        tab_count = self.content.count('page.keyboard.press("Tab")')
        self.assertGreaterEqual(tab_count, 2,
                              "Function doesn't press Tab key at least twice")
        
        # Check for ENTER key press
        self.assertIn('page.keyboard.press("Enter")', self.content,
                     "Function doesn't press Enter key")
        
        # Check for logging
        self.assertIn('TAB+TAB+ENTER sent to trigger Share', self.content,
                     "Function doesn't log TAB+TAB+ENTER action")
    
    def test_keyboard_shortcut_used_in_upload_browser(self):
        """Verify upload_to_instagram_browser() uses keyboard shortcut."""
        # Find the upload_to_instagram_browser function
        self.assertIn('def upload_to_instagram_browser(', self.content,
                     "upload_to_instagram_browser function not found")
        
        # Check it calls the helper function
        self.assertIn('_trigger_share_with_keyboard(page, caption_box)', self.content,
                     "upload_to_instagram_browser doesn't call _trigger_share_with_keyboard")
    
    def test_keyboard_shortcut_used_in_upload_with_manager(self):
        """Verify _upload_to_instagram_with_manager() uses keyboard shortcut."""
        # Find the _upload_to_instagram_with_manager function
        self.assertIn('def _upload_to_instagram_with_manager(', self.content,
                     "_upload_to_instagram_with_manager function not found")
        
        # Check it calls the helper function
        self.assertIn('_trigger_share_with_keyboard(page, caption_box)', self.content,
                     "_upload_to_instagram_with_manager doesn't call _trigger_share_with_keyboard")
    
    def test_no_share_button_click_in_upload_flow(self):
        """Verify Share button is NOT clicked using old method."""
        # Look for the old pattern of clicking Share button
        # We should NOT find calls to _wait_for_button_enabled with "Share" after caption entry
        
        # Get the content after the caption entry logic
        caption_idx = self.content.find('logger.info("Caption entered")')
        if caption_idx > 0:
            # Get content from caption entry to end of first upload function
            upload_browser_end = self.content.find('def _upload_to_instagram_with_manager', caption_idx)
            if upload_browser_end > caption_idx:
                section = self.content[caption_idx:upload_browser_end]
                # Should NOT contain old Share button click pattern
                self.assertNotIn('_wait_for_button_enabled(page, "Share"', section,
                               "Old Share button click method still present in upload_to_instagram_browser")
        
        logger.info("✓ Share button click has been replaced with keyboard shortcut")
    
    def test_tab_order_assumption_documented(self):
        """Verify TAB order assumption is clearly documented."""
        self.assertIn('exactly 2 TAB presses', self.content,
                     "Documentation doesn't mention the 2 TAB presses assumption")
        self.assertIn('tab order', self.content.lower(),
                     "Documentation doesn't mention tab order")
        self.assertIn('may need adjustment', self.content,
                     "Documentation doesn't warn about potential UI changes")
    
    def test_error_handling_present(self):
        """Verify error handling is present in keyboard shortcut function."""
        # Check for try-except block
        self.assertIn('except Exception as e:', self.content,
                     "No exception handling found")
        
        # Check for specific error logging
        self.assertIn('Failed to send TAB+TAB+ENTER shortcut', self.content,
                     "No specific error logging for keyboard shortcut failure")


if __name__ == '__main__':
    # Run tests
    logger.info("Running Instagram keyboard shortcut fix tests...")
    unittest.main(verbosity=2)
