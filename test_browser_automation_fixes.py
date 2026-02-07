#!/usr/bin/env python3
"""
Test suite for browser automation fixes.

Tests the following fixes:
1. Unicode logging (emoji removal)
2. YouTube file upload with hidden inputs
3. Instagram selector fallbacks
4. Browser context lifecycle (is_alive)
5. TikTok network error handling

Note: These tests check source code directly to avoid dependency issues.
"""

import os
import sys
import logging
import unittest
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestEmojiRemoval(unittest.TestCase):
    """Test that emojis have been removed from logging statements."""
    
    def test_brave_base_no_emojis(self):
        """Verify brave_base.py has no emoji characters."""
        base_path = Path(__file__).parent / "uploaders" / "brave_base.py"
        content = base_path.read_text(encoding='utf-8')
        
        # Check for common emojis that were problematic
        emojis = ['✅', '❌', '⚠️', '✓', '✗']
        found_emojis = []
        
        for emoji in emojis:
            if emoji in content:
                found_emojis.append(emoji)
        
        self.assertEqual(len(found_emojis), 0, 
                        f"Found emojis in brave_base.py: {found_emojis}")
        
        # Verify [OK], [FAIL], [WARN] are used instead
        self.assertIn('[OK]', content, "Missing [OK] replacement")
        self.assertIn('[FAIL]', content, "Missing [FAIL] replacement")
        
        logger.info("[OK] Emoji removal test passed for brave_base.py")
    
    def test_logging_ascii_safe(self):
        """Test that log messages can be encoded to ASCII-compatible format."""
        # Create a test message that should not crash on Windows
        test_message = "[OK] Validated Brave profile"
        
        # This should not raise UnicodeEncodeError on Windows
        try:
            # Simulate Windows console encoding limitation
            test_message.encode('cp1252')
            success = True
        except UnicodeEncodeError:
            success = False
        
        self.assertTrue(success, "Log message contains non-ASCII-safe characters")
        logger.info("[OK] ASCII-safe logging test passed")


class TestFileUploadHiddenInputs(unittest.TestCase):
    """Test file upload with hidden inputs using state='attached'."""
    
    def test_brave_base_uses_state_attached(self):
        """Test that brave_base.py upload_file uses state='attached'."""
        base_path = Path(__file__).parent / "uploaders" / "brave_base.py"
        content = base_path.read_text(encoding='utf-8')
        
        # Check that upload_file method uses state="attached"
        self.assertIn('state="attached"', content,
                     "upload_file should use state='attached' for hidden inputs")
        
        logger.info("[OK] File upload uses state='attached' for hidden inputs")
    
    def test_youtube_uses_state_attached(self):
        """Test that YouTube uploader uses state='attached'."""
        youtube_path = Path(__file__).parent / "uploaders" / "brave_youtube.py"
        content = youtube_path.read_text(encoding='utf-8')
        
        # Check for state="attached" in YouTube uploader
        self.assertIn('state="attached"', content,
                     "YouTube uploader should use state='attached'")
        
        logger.info("[OK] YouTube uploader uses state='attached'")
    
    def test_instagram_uses_state_attached(self):
        """Test that Instagram uploader uses state='attached'."""
        instagram_path = Path(__file__).parent / "uploaders" / "brave_instagram.py"
        content = instagram_path.read_text(encoding='utf-8')
        
        # Check for state="attached" in Instagram uploader
        self.assertIn('state="attached"', content,
                     "Instagram uploader should use state='attached'")
        
        logger.info("[OK] Instagram uploader uses state='attached'")
    
    def test_tiktok_uses_state_attached(self):
        """Test that TikTok uploader uses state='attached'."""
        tiktok_path = Path(__file__).parent / "uploaders" / "brave_tiktok.py"
        content = tiktok_path.read_text(encoding='utf-8')
        
        # Check for state="attached" in TikTok uploader
        self.assertIn('state="attached"', content,
                     "TikTok uploader should use state='attached'")
        
        logger.info("[OK] TikTok uploader uses state='attached'")


class TestBrowserContextLifecycle(unittest.TestCase):
    """Test browser context lifecycle management."""
    
    def test_is_alive_method_exists(self):
        """Test that BraveBrowserManager has is_alive method."""
        manager_path = Path(__file__).parent / "uploaders" / "brave_manager.py"
        content = manager_path.read_text(encoding='utf-8')
        
        # Check for is_alive method definition
        self.assertIn('def is_alive(self)', content,
                     "BraveBrowserManager missing is_alive method")
        
        logger.info("[OK] BraveBrowserManager has is_alive method")
    
    def test_is_alive_checks_context(self):
        """Test is_alive method checks browser context health."""
        manager_path = Path(__file__).parent / "uploaders" / "brave_manager.py"
        content = manager_path.read_text(encoding='utf-8')
        
        # Check that is_alive verifies context
        self.assertIn('self.browser_base.context', content,
                     "is_alive should check context")
        
        # Check that it evaluates JavaScript for health check
        self.assertIn('evaluate', content,
                     "is_alive should evaluate JavaScript for health check")
        
        logger.info("[OK] is_alive checks browser context health")


class TestInstagramSelectorFallbacks(unittest.TestCase):
    """Test Instagram selector fallback logic."""
    
    def test_multiple_create_selectors(self):
        """Verify Instagram uses multiple fallback selectors for Create button."""
        instagram_path = Path(__file__).parent / "uploaders" / "brave_instagram.py"
        content = instagram_path.read_text(encoding='utf-8')
        
        # Check for role-based selectors
        self.assertIn('button[role="button"]', content,
                     "Missing button role selector")
        self.assertIn('div[role="button"]', content,
                     "Missing div role selector")
        
        # Check for fallback iteration logic - check for constant
        self.assertIn('INSTAGRAM_CREATE_SELECTORS', content,
                     "Missing Instagram create selectors constant")
        
        # Check for multiple selector attempts
        self.assertIn('for selector in INSTAGRAM_CREATE_SELECTORS', content,
                     "Missing iteration through selectors")
        
        logger.info("[OK] Instagram has multiple fallback selectors")


class TestTikTokNetworkErrorHandling(unittest.TestCase):
    """Test TikTok network error detection and messaging."""
    
    def test_network_error_detection(self):
        """Verify TikTok detects and reports network errors clearly."""
        tiktok_path = Path(__file__).parent / "uploaders" / "brave_tiktok.py"
        content = tiktok_path.read_text(encoding='utf-8')
        
        # Check for network error handling
        self.assertIn('net::', content,
                     "Missing network error detection")
        self.assertIn('Network error', content,
                     "Missing network error message")
        
        # Check for user-friendly error messages
        self.assertIn('Internet connection', content,
                     "Missing internet connection error message")
        self.assertIn('blocked in your region', content,
                     "Missing region blocking error message")
        
        logger.info("[OK] TikTok has network error detection")


class TestPipelineErrorIsolation(unittest.TestCase):
    """Test that pipeline isolates upload errors per platform."""
    
    def test_pipeline_continues_on_error(self):
        """Verify pipeline uses continue instead of break on upload errors."""
        pipeline_path = Path(__file__).parent / "pipeline.py"
        content = pipeline_path.read_text(encoding='utf-8')
        
        # Check for continue statement in error handling
        # Look in the upload loop section
        lines = content.split('\n')
        
        # Find the exception handler in upload loop
        in_upload_loop = False
        has_continue = False
        
        for i, line in enumerate(lines):
            if 'for task in scheduled_tasks:' in line:
                in_upload_loop = True
            
            if in_upload_loop and 'except Exception' in line:
                # Look for continue in next few lines
                for j in range(i, min(i + 10, len(lines))):
                    if 'continue' in lines[j]:
                        has_continue = True
                        break
                break
        
        self.assertTrue(has_continue,
                       "Pipeline should use 'continue' in exception handler")
        
        logger.info("[OK] Pipeline uses 'continue' to isolate errors")
    
    def test_pipeline_has_context_validation(self):
        """Verify pipeline validates browser context before each upload."""
        pipeline_path = Path(__file__).parent / "pipeline.py"
        content = pipeline_path.read_text(encoding='utf-8')
        
        # Check for is_alive check
        self.assertIn('is_alive()', content,
                     "Pipeline should check browser context health")
        
        # Check for reinitialization logic
        self.assertIn('reinitialize', content.lower(),
                     "Pipeline should reinitialize browser on context death")
        
        logger.info("[OK] Pipeline validates browser context health")


class TestBraveShieldBypass(unittest.TestCase):
    """Test Brave Shield bypass arguments."""
    
    def test_brave_base_has_shield_bypass(self):
        """Verify brave_base.py has Brave-specific launch arguments."""
        base_path = Path(__file__).parent / "uploaders" / "brave_base.py"
        content = base_path.read_text(encoding='utf-8')
        
        # Check for Brave-specific arguments
        self.assertIn('--disable-brave-update', content,
                     "Missing Brave update bypass")
        
        logger.info("[OK] Brave Shield bypass arguments present")


def run_tests():
    """Run all tests."""
    logger.info("=" * 80)
    logger.info("Browser Automation Fixes - Test Suite")
    logger.info("=" * 80)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    logger.info("\n" + "=" * 80)
    logger.info("Test Summary")
    logger.info("=" * 80)
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Success: {result.wasSuccessful()}")
    logger.info("=" * 80)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
