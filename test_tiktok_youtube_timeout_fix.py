#!/usr/bin/env python3
"""
Test suite for TikTok and YouTube timeout fixes.

Tests that both uploaders have been modified to:
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


class TestTikTokTimeoutFix(unittest.TestCase):
    """Test that TikTok timeout fix has been properly applied."""
    
    def setUp(self):
        """Set up test by reading the brave_tiktok.py file."""
        self.tiktok_file = Path(__file__).parent / "uploaders" / "brave_tiktok.py"
        self.content = self.tiktok_file.read_text(encoding='utf-8')
    
    def test_domcontentloaded_wait_condition(self):
        """Verify both functions use 'domcontentloaded' instead of 'networkidle'."""
        # Check that domcontentloaded is used
        self.assertIn('wait_until="domcontentloaded"', self.content,
                     "Missing 'wait_until=\"domcontentloaded\"' in TikTok navigation")
        
        # Check that networkidle is NOT used in goto calls for TikTok upload page
        lines = self.content.split('\n')
        goto_lines = [line for line in lines if 'page.goto' in line and 'tiktok.com/upload' in line]
        
        for line in goto_lines:
            self.assertNotIn('wait_until="networkidle"', line,
                           f"Found networkidle in line: {line}")
            if 'wait_until' in line:
                self.assertIn('domcontentloaded', line,
                            f"wait_until should be domcontentloaded in: {line}")
    
    def test_60_second_timeout(self):
        """Verify both functions use extended timeout (180000ms/180 seconds)."""
        # Check that 180000ms timeout is used (3x longer for slow networks)
        self.assertIn('timeout=180000', self.content,
                     "Missing 'timeout=180000' in TikTok navigation")
        
        # Check we no longer use short 30000ms for TikTok upload
        goto_lines = [line for line in self.content.split('\n') 
                      if 'page.goto' in line and 'tiktok.com/upload' in line]
        for line in goto_lines:
            self.assertNotIn('timeout=30000', line,
                           f"Still using 30000ms timeout in: {line}")
    
    def test_both_functions_updated(self):
        """Verify both upload_to_tiktok_browser and _upload_to_tiktok_with_manager are updated."""
        # Check that both functions exist
        self.assertIn('def upload_to_tiktok_browser(', self.content,
                     "Function upload_to_tiktok_browser not found")
        self.assertIn('def _upload_to_tiktok_with_manager(', self.content,
                     "Function _upload_to_tiktok_with_manager not found")
        
        # Find both functions and verify they have the fixes
        lines = self.content.split('\n')
        
        browser_func_start = None
        manager_func_start = None
        
        for i, line in enumerate(lines):
            if 'def upload_to_tiktok_browser(' in line:
                browser_func_start = i
            elif 'def _upload_to_tiktok_with_manager(' in line:
                manager_func_start = i
        
        self.assertIsNotNone(browser_func_start, "upload_to_tiktok_browser function not found")
        self.assertIsNotNone(manager_func_start, "_upload_to_tiktok_with_manager function not found")
        
        # Extract function bodies
        browser_func_body = '\n'.join(lines[browser_func_start:browser_func_start+200])
        manager_func_body = '\n'.join(lines[manager_func_start:manager_func_start+200])
        
        # Verify browser function has the fixes
        self.assertIn('timeout=180000', browser_func_body,
                     "upload_to_tiktok_browser missing timeout=180000")
        self.assertIn('domcontentloaded', browser_func_body,
                     "upload_to_tiktok_browser missing domcontentloaded")
        
        # Verify manager function has the fixes
        self.assertIn('timeout=180000', manager_func_body,
                     "_upload_to_tiktok_with_manager missing timeout=180000")
        self.assertIn('domcontentloaded', manager_func_body,
                     "_upload_to_tiktok_with_manager missing domcontentloaded")


class TestYouTubeTimeoutFix(unittest.TestCase):
    """Test that YouTube timeout fix has been properly applied."""
    
    def setUp(self):
        """Set up test by reading the brave_youtube.py file."""
        self.youtube_file = Path(__file__).parent / "uploaders" / "brave_youtube.py"
        self.content = self.youtube_file.read_text(encoding='utf-8')
    
    def test_domcontentloaded_wait_condition(self):
        """Verify both functions use 'domcontentloaded' instead of 'networkidle'."""
        # Check that domcontentloaded is used
        self.assertIn('wait_until="domcontentloaded"', self.content,
                     "Missing 'wait_until=\"domcontentloaded\"' in YouTube navigation")
        
        # Check that networkidle is NOT used in goto calls for YouTube Studio
        lines = self.content.split('\n')
        goto_lines = [line for line in lines if 'page.goto' in line and 'studio.youtube.com' in line]
        
        for line in goto_lines:
            self.assertNotIn('wait_until="networkidle"', line,
                           f"Found networkidle in line: {line}")
            if 'wait_until' in line:
                self.assertIn('domcontentloaded', line,
                            f"wait_until should be domcontentloaded in: {line}")
    
    def test_60_second_timeout(self):
        """Verify both functions use extended timeout (180000ms)."""
        # Check that 180000ms timeout is used
        self.assertIn('timeout=180000', self.content,
                     "Missing 'timeout=180000' in YouTube navigation")
        
        # Count occurrences - should have at least 2 (one for each function)
        count = self.content.count('timeout=180000')
        self.assertGreaterEqual(count, 2,
                               f"Expected at least 2 occurrences of timeout=180000, found {count}")
    
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
            "YouTube Studio navigation timed out",
            "Slow internet connection",
            "YouTube may be temporarily unavailable",
            "Network firewall blocking YouTube"
        ]
        
        for msg in error_messages:
            self.assertIn(msg, self.content,
                         f"Missing error message: '{msg}'")
    
    def test_both_functions_updated(self):
        """Verify both upload_to_youtube_browser and _upload_to_youtube_with_manager are updated."""
        # Check that both functions exist
        self.assertIn('def upload_to_youtube_browser(', self.content,
                     "Function upload_to_youtube_browser not found")
        self.assertIn('def _upload_to_youtube_with_manager(', self.content,
                     "Function _upload_to_youtube_with_manager not found")
        
        # Find both functions and verify they have the fixes
        lines = self.content.split('\n')
        
        browser_func_start = None
        manager_func_start = None
        
        for i, line in enumerate(lines):
            if 'def upload_to_youtube_browser(' in line:
                browser_func_start = i
            elif 'def _upload_to_youtube_with_manager(' in line:
                manager_func_start = i
        
        self.assertIsNotNone(browser_func_start, "upload_to_youtube_browser function not found")
        self.assertIsNotNone(manager_func_start, "_upload_to_youtube_with_manager function not found")
        
        # Extract function bodies
        browser_func_body = '\n'.join(lines[browser_func_start:browser_func_start+200])
        manager_func_body = '\n'.join(lines[manager_func_start:manager_func_start+200])
        
        # Verify browser function has the fixes
        self.assertIn('timeout=180000', browser_func_body,
                     "upload_to_youtube_browser missing timeout=180000")
        self.assertIn('domcontentloaded', browser_func_body,
                     "upload_to_youtube_browser missing domcontentloaded")
        
        # Verify manager function has the fixes
        self.assertIn('timeout=180000', manager_func_body,
                     "_upload_to_youtube_with_manager missing timeout=180000")
        self.assertIn('domcontentloaded', manager_func_body,
                     "_upload_to_youtube_with_manager missing domcontentloaded")


class TestAllUploadersConsistent(unittest.TestCase):
    """Test that all three uploaders use consistent timeout and wait strategies."""
    
    def test_all_use_60_second_timeout(self):
        """Verify Instagram, TikTok, and YouTube all use extended timeout (180000ms)."""
        instagram_file = Path(__file__).parent / "uploaders" / "brave_instagram.py"
        tiktok_file = Path(__file__).parent / "uploaders" / "brave_tiktok.py"
        youtube_file = Path(__file__).parent / "uploaders" / "brave_youtube.py"
        
        for uploader_file in [instagram_file, tiktok_file, youtube_file]:
            content = uploader_file.read_text(encoding='utf-8')
            self.assertIn('timeout=180000', content,
                         f"{uploader_file.name} missing timeout=180000")
    
    def test_all_use_domcontentloaded(self):
        """Verify Instagram, TikTok, and YouTube all use domcontentloaded."""
        instagram_file = Path(__file__).parent / "uploaders" / "brave_instagram.py"
        tiktok_file = Path(__file__).parent / "uploaders" / "brave_tiktok.py"
        youtube_file = Path(__file__).parent / "uploaders" / "brave_youtube.py"
        
        for uploader_file in [instagram_file, tiktok_file, youtube_file]:
            content = uploader_file.read_text(encoding='utf-8')
            self.assertIn('wait_until="domcontentloaded"', content,
                         f"{uploader_file.name} missing domcontentloaded")


if __name__ == '__main__':
    # Run tests
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with proper code
    sys.exit(0 if result.wasSuccessful() else 1)
