#!/usr/bin/env python3
"""
Test suite for Instagram timeout fix.

Tests that the Instagram uploader has been modified to:
1. Use 60-second timeout instead of default 30 seconds
2. Use "domcontentloaded" instead of "networkidle" wait condition
3. Include proper error handling with detailed timeout messages
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


class TestInstagramTimeoutFix(unittest.TestCase):
    """Test that Instagram timeout fix has been properly applied."""
    
    def setUp(self):
        """Set up test by reading the brave_instagram.py file."""
        self.instagram_file = Path(__file__).parent / "uploaders" / "brave_instagram.py"
        self.content = self.instagram_file.read_text(encoding='utf-8')
    
    def test_domcontentloaded_wait_condition(self):
        """Verify both functions use 'domcontentloaded' instead of 'networkidle'."""
        # Check that domcontentloaded is used
        self.assertIn('wait_until="domcontentloaded"', self.content,
                     "Missing 'wait_until=\"domcontentloaded\"' in Instagram navigation")
        
        # Check that networkidle is NOT used in goto calls
        # We need to be more specific - check the actual goto lines
        lines = self.content.split('\n')
        goto_lines = [line for line in lines if 'page.goto' in line and 'instagram.com' in line]
        
        for line in goto_lines:
            self.assertNotIn('wait_until="networkidle"', line,
                           f"Found networkidle in line: {line}")
            # Either should have domcontentloaded or no wait_until (which is also ok)
            if 'wait_until' in line:
                self.assertIn('domcontentloaded', line,
                            f"wait_until should be domcontentloaded in: {line}")
    
    def test_60_second_timeout(self):
        """Verify both functions use 60-second timeout (60000ms)."""
        # Check that 60000ms timeout is used
        self.assertIn('timeout=60000', self.content,
                     "Missing 'timeout=60000' in Instagram navigation")
        
        # Count occurrences - should have at least 2 (one for each function)
        count = self.content.count('timeout=60000')
        self.assertGreaterEqual(count, 2,
                               f"Expected at least 2 occurrences of timeout=60000, found {count}")
    
    def test_timeout_error_handling(self):
        """Verify proper error handling for timeout errors."""
        # Check for try-catch around navigation
        self.assertIn('try:', self.content,
                     "Missing try block for error handling")
        
        # Check for timeout-specific error handling
        self.assertIn('if "Timeout" in str(e):', self.content,
                     "Missing timeout-specific error handling")
        
        # Check for detailed error messages
        error_messages = [
            "Instagram navigation timed out",
            "Slow internet connection",
            "Instagram may be temporarily unavailable",
            "Network firewall blocking Instagram"
        ]
        
        for msg in error_messages:
            self.assertIn(msg, self.content,
                         f"Missing error message: '{msg}'")
    
    def test_both_functions_updated(self):
        """Verify both upload_to_instagram_browser and _upload_to_instagram_with_manager are updated."""
        # Check that both functions exist
        self.assertIn('def upload_to_instagram_browser(', self.content,
                     "Function upload_to_instagram_browser not found")
        self.assertIn('def _upload_to_instagram_with_manager(', self.content,
                     "Function _upload_to_instagram_with_manager not found")
        
        # Find both function bodies and verify they have the fixes
        lines = self.content.split('\n')
        
        # Find line numbers for both functions
        browser_func_start = None
        manager_func_start = None
        
        for i, line in enumerate(lines):
            if 'def upload_to_instagram_browser(' in line:
                browser_func_start = i
            elif 'def _upload_to_instagram_with_manager(' in line:
                manager_func_start = i
        
        self.assertIsNotNone(browser_func_start, "upload_to_instagram_browser function not found")
        self.assertIsNotNone(manager_func_start, "_upload_to_instagram_with_manager function not found")
        
        # Extract function bodies (roughly - up to 200 lines each)
        browser_func_body = '\n'.join(lines[browser_func_start:browser_func_start+200])
        manager_func_body = '\n'.join(lines[manager_func_start:manager_func_start+200])
        
        # Verify browser function has the fixes
        self.assertIn('timeout=60000', browser_func_body,
                     "upload_to_instagram_browser missing timeout=60000")
        self.assertIn('domcontentloaded', browser_func_body,
                     "upload_to_instagram_browser missing domcontentloaded")
        
        # Verify manager function has the fixes
        self.assertIn('timeout=60000', manager_func_body,
                     "_upload_to_instagram_with_manager missing timeout=60000")
        self.assertIn('domcontentloaded', manager_func_body,
                     "_upload_to_instagram_with_manager missing domcontentloaded")
    
    def test_no_breaking_changes(self):
        """Verify we didn't break existing functionality."""
        # Check that the file still has expected structure
        expected_elements = [
            'import os',
            'import random',
            'import logging',
            'from .brave_base import BraveBrowserBase',
            'INSTAGRAM_CREATE_SELECTORS',
            'logger = logging.getLogger(__name__)',
        ]
        
        for element in expected_elements:
            self.assertIn(element, self.content,
                         f"Missing expected element: '{element}'")


if __name__ == '__main__':
    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestInstagramTimeoutFix)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with proper code
    sys.exit(0 if result.wasSuccessful() else 1)
