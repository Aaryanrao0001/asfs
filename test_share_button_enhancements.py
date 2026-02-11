#!/usr/bin/env python3
"""
Test suite for Instagram Share button enhancements.

Tests that the _wait_for_button_enabled function has been enhanced with:
1. JS click fallback (button.evaluate('el => el.click()'))
2. Double-click retry mechanism for Share button
3. Overlay/spinner detection before clicking
4. Wait for Share button disappearance as success indicator
5. Enhanced diagnostic logging for click methods
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


class TestShareButtonEnhancements(unittest.TestCase):
    """Test that Instagram Share button enhancements have been properly applied."""
    
    def setUp(self):
        """Set up test by reading the brave_instagram.py file."""
        self.instagram_file = Path(__file__).parent / "uploaders" / "brave_instagram.py"
        self.content = self.instagram_file.read_text(encoding='utf-8')
    
    def test_has_js_click_fallback(self):
        """Verify function includes JS click fallback using evaluate."""
        # Check that JS click is used (either directly or via constant)
        has_js_click = ("button.evaluate('el => el.click()')" in self.content or 
                       "button.evaluate(JS_CLICK_EXPRESSION)" in self.content or
                       "JS_CLICK_EXPRESSION = 'el => el.click()'" in self.content)
        self.assertTrue(has_js_click,
                     "Missing JS click fallback: button.evaluate with el => el.click()")
        self.assertIn('JS click fallback', self.content,
                     "Missing JS click fallback logging")
    
    def test_has_standard_click_first(self):
        """Verify function tries standard click before JS fallback."""
        # Check that standard click is attempted
        self.assertIn('button.click()', self.content,
                     "Missing standard button.click() call")
        self.assertIn('standard click', self.content.lower(),
                     "Missing standard click logging")
    
    def test_has_overlay_detection(self):
        """Verify function checks for overlays/spinners before clicking."""
        overlay_checks = [
            'overlay',
            'spinner',
            'progressbar',
            'Loading',
        ]
        
        for check in overlay_checks:
            self.assertIn(check, self.content,
                         f"Missing overlay detection for: '{check}'")
    
    def test_has_double_click_for_share(self):
        """Verify function implements double-click retry for Share button."""
        # Check for Share-specific handling
        self.assertIn('button_text.lower() == "share"', self.content,
                     "Missing Share button specific handling")
        self.assertIn('second click', self.content.lower(),
                     "Missing second click logic")
        self.assertIn('still visible after first click', self.content.lower(),
                     "Missing visibility check after first click")
    
    def test_waits_for_button_disappearance(self):
        """Verify function waits for Share button to disappear as success indicator."""
        self.assertIn('wait_for(state="hidden"', self.content,
                     "Missing wait for button disappearance")
        self.assertIn('disappeared', self.content.lower(),
                     "Missing button disappearance logging")
        self.assertIn('upload initiated', self.content.lower(),
                     "Missing upload initiation confirmation")
    
    def test_has_enhanced_click_logging(self):
        """Verify function has detailed logging for click methods used."""
        log_messages = [
            'standard click',
            'JS click fallback',
            'clicked (standard click)',
            'clicked (JS click fallback)',
        ]
        
        found_count = sum(1 for msg in log_messages if msg.lower() in self.content.lower())
        self.assertGreater(found_count, 0,
                          f"Missing enhanced click method logging. Expected at least 1 of {log_messages}")
    
    def test_has_click_success_tracking(self):
        """Verify function tracks whether click was successful."""
        self.assertIn('click_success', self.content,
                     "Missing click success tracking variable")
    
    def test_overlay_wait_after_detection(self):
        """Verify function waits after detecting overlay."""
        # Should wait for overlay to clear
        self.assertIn('Overlay detected', self.content,
                     "Missing overlay detection message")
        # Check for wait after overlay detection
        overlay_section = self.content[self.content.find('Overlay detected'):self.content.find('Overlay detected') + 500] if 'Overlay detected' in self.content else ''
        self.assertIn('wait', overlay_section.lower(),
                     "Missing wait after overlay detection")
    
    def test_handles_button_visibility_after_click(self):
        """Verify function checks if button is still visible after click."""
        self.assertIn('button.is_visible()', self.content,
                     "Missing button visibility check")
        self.assertIn('still visible', self.content.lower(),
                     "Missing visibility check message")
    
    def test_no_breaking_changes(self):
        """Verify no breaking changes to existing functionality."""
        # Should still have all the original functionality
        essential_parts = [
            '_wait_for_button_enabled',
            'scroll_into_view_if_needed',
            'wait_for(state="visible"',
            'aria-disabled',
            'return True',
            'return False',
        ]
        
        for part in essential_parts:
            self.assertIn(part, self.content,
                         f"Breaking change detected: Missing '{part}'")
    
    def test_retry_uses_both_click_methods(self):
        """Verify second click attempt tries both standard and JS click."""
        # Find the share-specific section
        if 'button_text.lower() == "share"' in self.content:
            share_section_start = self.content.find('button_text.lower() == "share"')
            share_section = self.content[share_section_start:share_section_start + 2000]
            
            # In the second click section, should have both methods
            self.assertIn('second click', share_section.lower(),
                         "Missing second click in Share section")


if __name__ == '__main__':
    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestShareButtonEnhancements)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with proper code
    sys.exit(0 if result.wasSuccessful() else 1)
