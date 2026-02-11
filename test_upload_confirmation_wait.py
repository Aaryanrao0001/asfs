#!/usr/bin/env python3
"""
Test suite for Instagram and TikTok upload confirmation wait logic.

Tests that the uploaders have been modified to:
1. Wait for upload confirmation after submitting
2. Apply minimum safety wait before closing browser
3. Log explicit outcomes (confirmed, timeout, or unverified)
4. Prevent race conditions by not closing browser prematurely
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


class TestUploadConfirmationWait(unittest.TestCase):
    """Test that upload confirmation wait logic has been properly implemented."""
    
    def setUp(self):
        """Set up test by reading the uploader files."""
        self.instagram_file = Path(__file__).parent / "uploaders" / "brave_instagram.py"
        self.tiktok_file = Path(__file__).parent / "uploaders" / "brave_tiktok.py"
        self.instagram_content = self.instagram_file.read_text(encoding='utf-8')
        self.tiktok_content = self.tiktok_file.read_text(encoding='utf-8')
    
    def test_instagram_confirmation_constants_exist(self):
        """Verify Instagram upload confirmation constants are defined."""
        self.assertIn('UPLOAD_CONFIRMATION_WAIT_MS', self.instagram_content,
                     "UPLOAD_CONFIRMATION_WAIT_MS constant not found")
        self.assertIn('UPLOAD_MIN_SAFETY_WAIT_MS', self.instagram_content,
                     "UPLOAD_MIN_SAFETY_WAIT_MS constant not found")
        
        # Verify they have reasonable values (at least 10 seconds)
        self.assertIn('UPLOAD_CONFIRMATION_WAIT_MS = 15000', self.instagram_content,
                     "UPLOAD_CONFIRMATION_WAIT_MS should be 15000ms (15s)")
        self.assertIn('UPLOAD_MIN_SAFETY_WAIT_MS = 10000', self.instagram_content,
                     "UPLOAD_MIN_SAFETY_WAIT_MS should be 10000ms (10s)")
    
    def test_instagram_confirmation_function_exists(self):
        """Verify Instagram _wait_for_upload_confirmation() helper function exists."""
        self.assertIn('def _wait_for_upload_confirmation(page: Page) -> tuple[bool, str]:',
                     self.instagram_content,
                     "_wait_for_upload_confirmation function not found")
        
        # Verify function docstring describes the purpose
        self.assertIn('Wait for Instagram upload confirmation', self.instagram_content,
                     "Function docstring doesn't mention upload confirmation")
        self.assertIn('race condition', self.instagram_content.lower(),
                     "Function docstring doesn't mention race condition prevention")
    
    def test_instagram_confirmation_implementation(self):
        """Verify _wait_for_upload_confirmation() has correct implementation."""
        # Check for dialog disappearance detection
        self.assertIn('aria-hidden="false"', self.instagram_content,
                     "Function doesn't check for dialog (aria-hidden)")
        
        # Check for progress indicator detection
        self.assertIn('role="progressbar"', self.instagram_content,
                     "Function doesn't check for progress indicator")
        
        # Check for minimum safety wait
        self.assertIn('UPLOAD_MIN_SAFETY_WAIT_MS', self.instagram_content,
                     "Function doesn't apply minimum safety wait")
        
        # Check for proper return tuple
        self.assertIn('return confirmed, message', self.instagram_content,
                     "Function doesn't return (confirmed, message) tuple")
    
    def test_instagram_confirmation_used_in_upload_browser(self):
        """Verify upload_to_instagram_browser() uses confirmation wait."""
        # Find the upload_to_instagram_browser function
        self.assertIn('def upload_to_instagram_browser(', self.instagram_content,
                     "upload_to_instagram_browser function not found")
        
        # Check it calls the helper function
        self.assertIn('_wait_for_upload_confirmation(page)', self.instagram_content,
                     "upload_to_instagram_browser doesn't call _wait_for_upload_confirmation")
        
        # Check for critical comment about race condition
        self.assertIn('CRITICAL: Wait for upload confirmation before closing browser',
                     self.instagram_content,
                     "Missing critical comment about confirmation wait")
    
    def test_instagram_confirmation_used_in_upload_with_manager(self):
        """Verify _upload_to_instagram_with_manager() uses confirmation wait."""
        # Find the _upload_to_instagram_with_manager function
        self.assertIn('def _upload_to_instagram_with_manager(', self.instagram_content,
                     "_upload_to_instagram_with_manager function not found")
        
        # Check it calls the helper function
        count = self.instagram_content.count('_wait_for_upload_confirmation(page)')
        self.assertGreaterEqual(count, 2,
                               f"Expected at least 2 calls to _wait_for_upload_confirmation, found {count}")
    
    def test_instagram_no_immediate_close_after_submit(self):
        """Verify Instagram doesn't close immediately after submit."""
        # Should NOT have the old pattern of immediate close
        # Old pattern: _trigger_share_with_keyboard followed immediately by browser.close()
        # New pattern: _trigger_share_with_keyboard followed by _wait_for_upload_confirmation
        
        # Find instances where we call _trigger_share_with_keyboard
        trigger_share_count = self.instagram_content.count('_trigger_share_with_keyboard(page, caption_box)')
        self.assertGreaterEqual(trigger_share_count, 2,
                               "Expected at least 2 calls to _trigger_share_with_keyboard")
        
        # Verify we call confirmation wait after trigger
        self.assertIn('_trigger_share_with_keyboard(page, caption_box)', self.instagram_content)
        
        # Check that old immediate-close pattern components are gone
        # Test for individual components that made up the old pattern
        self.assertNotIn('Instagram upload submitted - no deterministic confirmation available',
                        self.instagram_content,
                        "Old warning message still exists")
        
        # Verify new pattern exists: confirmation wait is called
        self.assertIn('_wait_for_upload_confirmation(page)', self.instagram_content,
                     "New confirmation wait pattern not found")
    
    def test_tiktok_enhanced_confirmation_wait(self):
        """Verify TikTok has enhanced confirmation wait logic."""
        # TikTok should have at least 15 seconds total wait
        self.assertIn('Waiting for upload confirmation', self.tiktok_content,
                     "TikTok doesn't log confirmation wait")
        
        # Check for safety wait messaging
        self.assertIn('safety wait', self.tiktok_content.lower(),
                     "TikTok doesn't mention safety wait")
        
        # Check for improved result message
        self.assertIn('waited 15s for safety', self.tiktok_content,
                     "TikTok result message doesn't mention 15s safety wait")
    
    def test_tiktok_confirmation_in_both_functions(self):
        """Verify both TikTok upload functions have confirmation wait."""
        # Check upload_to_tiktok_browser
        self.assertIn('def upload_to_tiktok_browser(', self.tiktok_content,
                     "upload_to_tiktok_browser function not found")
        
        # Check _upload_to_tiktok_with_manager
        self.assertIn('def _upload_to_tiktok_with_manager(', self.tiktok_content,
                     "_upload_to_tiktok_with_manager function not found")
        
        # Both should have confirmation wait logic
        confirmation_count = self.tiktok_content.count('Waiting for upload confirmation')
        self.assertGreaterEqual(confirmation_count, 2,
                               f"Expected at least 2 confirmation waits, found {confirmation_count}")
    
    def test_logging_explicit_outcomes(self):
        """Verify both platforms log explicit outcomes."""
        # Instagram should log confirmed or unverified
        self.assertIn('Instagram upload confirmed successfully', self.instagram_content,
                     "Instagram doesn't log confirmed success")
        self.assertIn('Instagram upload status unverified, but safety wait completed',
                     self.instagram_content,
                     "Instagram doesn't log unverified with safety wait")
        
        # TikTok should log similar messages
        self.assertIn('TikTok upload confirmed successful', self.tiktok_content,
                     "TikTok doesn't log confirmed success")
        self.assertIn('TikTok upload status unverified', self.tiktok_content,
                     "TikTok doesn't log unverified status")


if __name__ == '__main__':
    unittest.main()
