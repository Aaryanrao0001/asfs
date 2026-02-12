#!/usr/bin/env python3
"""
Test suite for TikTok and Instagram upload fixes.

Tests that:
1. TikTok uploader waits for "Uploaded" status indicator
2. TikTok has updated caption input selectors
3. Instagram button detection properly checks disabled state
"""

import unittest
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestTikTokUploadStatusFix(unittest.TestCase):
    """Test that TikTok upload status detection has been fixed."""
    
    def setUp(self):
        """Set up test by reading the brave_tiktok.py file."""
        self.tiktok_file = Path(__file__).parent / "uploaders" / "brave_tiktok.py"
        self.content = self.tiktok_file.read_text(encoding='utf-8')
    
    def test_upload_status_container_selector(self):
        """Verify that upload status container selector is present."""
        # Check for the data-e2e upload_status_container selector
        self.assertIn('upload_status_container', self.content,
                     "Missing 'upload_status_container' selector")
        self.assertIn('.info-status.success', self.content,
                     "Missing '.info-status.success' selector")
        
    def test_uploaded_text_detection(self):
        """Verify that code checks for 'Uploaded' text."""
        self.assertIn(':has-text("Uploaded")', self.content,
                     "Missing ':has-text(\"Uploaded\")' check")
    
    def test_elapsed_time_logging(self):
        """Verify that elapsed time is logged."""
        # Check for time tracking
        self.assertIn('import time', self.content,
                     "Missing 'import time' for elapsed time tracking")
        self.assertIn('start_time = time.time()', self.content,
                     "Missing start_time tracking")
        self.assertIn('elapsed', self.content,
                     "Missing elapsed time calculation")
        # Check for elapsed time in log messages
        self.assertIn('elapsed:.1f', self.content,
                     "Missing elapsed time in log messages")
    
    def test_timeout_reduced(self):
        """Verify that default timeout is reasonable (not too long)."""
        # Should be 180000ms (3 minutes) or less, not 360000ms (6 minutes)
        lines = self.content.split('\n')
        for line in lines:
            if 'def _wait_for_processing_complete' in line:
                # Find the timeout parameter default
                if 'timeout: int = ' in line:
                    # Extract timeout value
                    import re
                    match = re.search(r'timeout: int = (\d+)', line)
                    if match:
                        timeout_ms = int(match.group(1))
                        self.assertLessEqual(timeout_ms, 180000,
                                           f"Timeout {timeout_ms}ms is too long (should be ≤ 180000ms)")


class TestTikTokCaptionSelectorFix(unittest.TestCase):
    """Test that TikTok caption selectors have been updated."""
    
    def setUp(self):
        """Set up test by reading the selectors.py file."""
        self.selectors_file = Path(__file__).parent / "uploaders" / "selectors.py"
        self.content = self.selectors_file.read_text(encoding='utf-8')
    
    def test_plaintext_only_selector(self):
        """Verify that plaintext-only contenteditable selector is present."""
        self.assertIn('contenteditable="plaintext-only"', self.content,
                     "Missing 'contenteditable=\"plaintext-only\"' selector")
    
    def test_role_textbox_selector(self):
        """Verify that role=textbox selector is present."""
        self.assertIn('role="textbox"', self.content,
                     "Missing 'role=\"textbox\"' selector")
    
    def test_spellcheck_selector(self):
        """Verify that spellcheck selector is present."""
        self.assertIn('[spellcheck]', self.content,
                     "Missing '[spellcheck]' selector")
    
    def test_drafteditor_selector(self):
        """Verify that DraftJS editor selector is present for current TikTok UI."""
        # Verify the complete selector with all attributes is present
        complete_selector = 'div.notranslate.public-DraftEditor-content[contenteditable="true"][role="combobox"]'
        self.assertIn(complete_selector, self.content,
                     f"Missing complete DraftJS editor selector: {complete_selector}")


class TestInstagramButtonFix(unittest.TestCase):
    """Test that Instagram button detection has been fixed."""
    
    def setUp(self):
        """Set up test by reading the brave_instagram.py file."""
        self.instagram_file = Path(__file__).parent / "uploaders" / "brave_instagram.py"
        self.content = self.instagram_file.read_text(encoding='utf-8')
    
    def test_disabled_state_check(self):
        """Verify that aria-disabled and disabled attributes are checked."""
        self.assertIn('aria-disabled', self.content,
                     "Missing 'aria-disabled' attribute check")
        self.assertIn('get_attribute', self.content,
                     "Missing get_attribute() call for state checking")
    
    def test_multiple_selectors(self):
        """Verify that multiple button selectors are tried."""
        # Check for selector fallback strategy
        self.assertIn('selectors = [', self.content,
                     "Missing multiple selector strategy")
        # Should have at least div[role="button"] and button selectors
        self.assertIn('div[role="button"]', self.content,
                     "Missing 'div[role=\"button\"]' selector")
        self.assertIn('button:has-text', self.content,
                     "Missing 'button:has-text' selector")
    
    def test_elapsed_time_logging(self):
        """Verify that elapsed time is logged for button detection."""
        # Check for time tracking in _wait_for_button_enabled
        # Simply check if 'import time' and 'elapsed' appear in the file
        # since the function uses time tracking for elapsed time logging
        self.assertIn('import time', self.content,
                     "Missing 'import time' in button detection")
        self.assertIn('elapsed', self.content,
                     "Missing elapsed time tracking in button detection")
    
    def test_no_invalid_enabled_state(self):
        """Verify that invalid 'enabled' state is not used in wait_for()."""
        # The wait_for() method doesn't support 'enabled' state
        # Look for the pattern but be more lenient about false positives
        # since we're checking the entire file, not parsing AST
        import re
        
        # Find all instances of wait_for with state parameter
        pattern = r'\.wait_for\s*\(\s*state\s*=\s*["\']enabled["\']'
        matches = re.findall(pattern, self.content)
        
        if matches:
            # Check if these are in actual code (not comments/strings)
            # This is a simplified check - in real code review, AST parsing would be better
            lines_with_enabled = [i for i, line in enumerate(self.content.split('\n')) 
                                 if 'wait_for(state="enabled"' in line or "wait_for(state='enabled'" in line]
            
            # Filter out obvious false positives (lines starting with # or in docstrings)
            false_positives = 0
            for line_num in lines_with_enabled:
                line = self.content.split('\n')[line_num].strip()
                if line.startswith('#') or line.startswith('"""') or line.startswith("'''"):
                    false_positives += 1
            
            actual_issues = len(lines_with_enabled) - false_positives
            if actual_issues > 0:
                self.fail(f"Found {actual_issues} instance(s) of invalid 'enabled' state in wait_for()")


if __name__ == '__main__':
    unittest.main()
