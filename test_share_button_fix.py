#!/usr/bin/env python3
"""
Test suite for Instagram Share button selector fix.

Tests that the _wait_for_button_enabled function has been updated to:
1. Use robust fallback selector strategy
2. Try div[role="button"][tabindex="0"] with text filtering
3. Handle multiple buttons by selecting the last visible one
4. Scroll into view before clicking
5. Add detailed logging for debugging
6. Log all found buttons on failure
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


class TestShareButtonFix(unittest.TestCase):
    """Test that Instagram Share button fix has been properly applied."""
    
    def setUp(self):
        """Set up test by reading the brave_instagram.py file."""
        self.instagram_file = Path(__file__).parent / "uploaders" / "brave_instagram.py"
        self.content = self.instagram_file.read_text(encoding='utf-8')
    
    def test_uses_role_button_tabindex_selector(self):
        """Verify function includes div[role="button"][tabindex="0"] selector."""
        self.assertIn('div[role="button"][tabindex="0"]', self.content,
                     "Missing 'div[role=\"button\"][tabindex=\"0\"]' selector for robust fallback")
    
    def test_filters_by_text_content(self):
        """Verify function filters buttons by text content."""
        # Check for text filtering logic
        self.assertIn('text_content', self.content,
                     "Missing text_content filtering logic")
        self.assertIn('.lower()', self.content,
                     "Missing case-insensitive text comparison")
        self.assertIn('.strip()', self.content,
                     "Missing text trimming logic")
    
    def test_selects_last_visible_button(self):
        """Verify function selects last button when multiple matches found."""
        # Check for logic to select last button from matching buttons
        self.assertIn('[-1]', self.content,
                     "Missing logic to select last button from matches")
        self.assertIn('matching_buttons', self.content,
                     "Missing matching_buttons collection")
    
    def test_scrolls_into_view(self):
        """Verify function scrolls button into view before clicking."""
        self.assertIn('scroll_into_view_if_needed', self.content,
                     "Missing scroll_into_view_if_needed call")
    
    def test_has_detailed_logging(self):
        """Verify function has detailed logging for debugging."""
        log_messages = [
            'Searching for',
            'button found with selector',
            'role-based with manual filtering',
            'selected last of',
        ]
        
        for msg in log_messages:
            self.assertIn(msg, self.content,
                         f"Missing log message: '{msg}'")
    
    def test_logs_all_buttons_on_failure(self):
        """Verify function logs all buttons on failure for auditing."""
        audit_messages = [
            'Attempting to log all',
            'Button',
            'for audit',
        ]
        
        for msg in audit_messages:
            self.assertIn(msg, self.content,
                         f"Missing audit log message: '{msg}'")
    
    def test_has_fallback_strategy_documentation(self):
        """Verify function documents the fallback strategy."""
        doc_items = [
            'robust selector fallback strategy',
            'Try text-based selectors',
            'Fallback to role-based',
            'multiple matches',
            'Scroll into view',
        ]
        
        for item in doc_items:
            self.assertIn(item, self.content,
                         f"Missing documentation item: '{item}'")
    
    def test_handles_visibility_check(self):
        """Verify function checks button visibility."""
        self.assertIn('is_visible()', self.content,
                     "Missing visibility check for buttons")
    
    def test_logs_button_attributes(self):
        """Verify function logs button attributes for debugging."""
        attributes = [
            'aria-disabled',
            'tabindex',
            'text=',
            'visible=',
        ]
        
        for attr in attributes:
            self.assertIn(attr, self.content,
                         f"Missing attribute logging: '{attr}'")
    
    def test_no_breaking_changes_to_calls(self):
        """Verify existing calls to _wait_for_button_enabled still work."""
        # Check that Share button is still called correctly
        self.assertIn('_wait_for_button_enabled(page, "Share"', self.content,
                     "Share button calls have been broken")
        
        # Check that Next button is still called correctly
        self.assertIn('_wait_for_button_enabled(page, "Next"', self.content,
                     "Next button calls have been broken")
        
        # Count Share button calls (should be at least 2)
        share_calls = self.content.count('_wait_for_button_enabled(page, "Share"')
        self.assertGreaterEqual(share_calls, 2,
                               f"Expected at least 2 Share button calls, found {share_calls}")


if __name__ == '__main__':
    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestShareButtonFix)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with proper code
    sys.exit(0 if result.wasSuccessful() else 1)
