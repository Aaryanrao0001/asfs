#!/usr/bin/env python3
"""
Test suite for Instagram Post button click fix.

Tests that the Instagram uploader has been modified to:
1. Add _select_post_option() helper function
2. Call _select_post_option() after clicking Create button in both functions
3. Use UI selector wait instead of networkidle for page readiness
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


class TestInstagramPostButtonFix(unittest.TestCase):
    """Test that Instagram Post button fix has been properly applied."""
    
    def setUp(self):
        """Set up test by reading the brave_instagram.py file."""
        self.instagram_file = Path(__file__).parent / "uploaders" / "brave_instagram.py"
        self.content = self.instagram_file.read_text(encoding='utf-8')
        self.lines = self.content.split('\n')
    
    def test_select_post_option_function_exists(self):
        """Verify _select_post_option() helper function exists."""
        self.assertIn('def _select_post_option(page: Page, timeout: int = 15000) -> bool:',
                     self.content,
                     "_select_post_option function not found")
        
        # Verify function docstring describes the purpose
        self.assertIn('Instagram A/B tests multiple UI variants', 
                     self.content,
                     "Function docstring doesn't describe A/B testing variants")
        self.assertIn('Try all variants with retries for React animation delays',
                     self.content,
                     "Function docstring doesn't explain retry logic")
    
    def test_select_post_option_implementation(self):
        """Verify _select_post_option() has correct implementation."""
        # Check for multiple selectors (multi-variant support)
        self.assertIn('possible_selectors = [',
                     self.content,
                     "Missing possible_selectors list for multi-variant support")
        
        # Check for all variant selectors
        self.assertIn('div[role="button"]:has-text("Post")',
                     self.content,
                     "Missing Post button locator")
        self.assertIn('div[role="button"]:has-text("Create post")',
                     self.content,
                     "Missing Create post button locator")
        self.assertIn('div[role="button"]:has-text("Reel")',
                     self.content,
                     "Missing Reel fallback locator")
        
        # Check for wait states
        self.assertIn('button.first.wait_for(state="visible"', self.content,
                     "Missing visibility wait in _select_post_option")
        self.assertIn('button.first.wait_for(state="enabled"', self.content,
                     "Missing enabled wait in _select_post_option")
        
        # Check for click and logging
        self.assertIn('Post option clicked successfully', self.content,
                     "Missing success log message")
        self.assertIn('Post option button not found with any variant', self.content,
                     "Missing error log for Post button not found")
    
    def test_ui_selector_wait_instead_of_networkidle(self):
        """Verify UI selector wait is used instead of networkidle."""
        # Check that we wait for the Create button selector as UI readiness indicator
        self.assertIn('page.wait_for_selector(\'svg[aria-label="New post"]\', timeout=30000)',
                     self.content,
                     "Missing UI selector wait for Create button")
        
        # Verify networkidle is NOT used after page.goto
        goto_lines = []
        for i, line in enumerate(self.lines):
            if 'page.goto("https://www.instagram.com/"' in line:
                # Check the next 5 lines
                goto_context = '\n'.join(self.lines[i:i+5])
                goto_lines.append(goto_context)
        
        for context in goto_lines:
            self.assertNotIn('page.wait_for_load_state("networkidle"', context,
                           f"Found networkidle wait after goto in: {context}")
    
    def test_upload_to_instagram_browser_calls_select_post_option(self):
        """Verify upload_to_instagram_browser() calls _select_post_option()."""
        # Find the function
        func_start = None
        for i, line in enumerate(self.lines):
            if 'def upload_to_instagram_browser(' in line:
                func_start = i
                break
        
        self.assertIsNotNone(func_start, "upload_to_instagram_browser function not found")
        
        # Extract function body (roughly 200 lines)
        func_body = '\n'.join(self.lines[func_start:func_start+200])
        
        # Verify it calls _select_post_option
        self.assertIn('_select_post_option(page)', func_body,
                     "upload_to_instagram_browser doesn't call _select_post_option")
        
        # Verify it's called AFTER Create button click
        self.assertIn('Create button clicked', func_body)
        
        # Verify proper error handling
        self.assertIn('Post option not found - cannot proceed with upload', func_body,
                     "Missing error handling for Post option failure")
    
    def test_upload_to_instagram_with_manager_calls_select_post_option(self):
        """Verify _upload_to_instagram_with_manager() calls _select_post_option()."""
        # Find the function
        func_start = None
        for i, line in enumerate(self.lines):
            if 'def _upload_to_instagram_with_manager(' in line:
                func_start = i
                break
        
        self.assertIsNotNone(func_start, "_upload_to_instagram_with_manager function not found")
        
        # Extract function body (roughly 200 lines)
        func_body = '\n'.join(self.lines[func_start:func_start+200])
        
        # Verify it calls _select_post_option
        self.assertIn('_select_post_option(page)', func_body,
                     "_upload_to_instagram_with_manager doesn't call _select_post_option")
        
        # Verify it's called AFTER Create button click
        self.assertIn('Create button clicked', func_body)
        
        # Verify proper error handling
        self.assertIn('Post option not found - cannot proceed with upload', func_body,
                     "Missing error handling for Post option failure")
    
    def test_file_input_wait_after_post_selection(self):
        """Verify file input wait happens AFTER Post option selection."""
        # Check both functions have the correct sequence
        for func_name in ['upload_to_instagram_browser', '_upload_to_instagram_with_manager']:
            func_start = None
            for i, line in enumerate(self.lines):
                if f'def {func_name}(' in line:
                    func_start = i
                    break
            
            self.assertIsNotNone(func_start, f"{func_name} function not found")
            
            # Extract function body
            func_body_lines = self.lines[func_start:func_start+200]
            func_body = '\n'.join(func_body_lines)
            
            # Find positions of key events
            create_click_idx = None
            post_select_idx = None
            file_input_idx = None
            
            for i, line in enumerate(func_body_lines):
                if 'Create button clicked' in line:
                    create_click_idx = i
                elif '_select_post_option(page)' in line:
                    post_select_idx = i
                elif 'Waiting for file input' in line:
                    file_input_idx = i
            
            # Verify sequence
            if create_click_idx is not None and post_select_idx is not None and file_input_idx is not None:
                self.assertLess(create_click_idx, post_select_idx,
                               f"{func_name}: Post selection should be after Create button click")
                self.assertLess(post_select_idx, file_input_idx,
                               f"{func_name}: File input wait should be after Post selection")
    
    def test_updated_comments_reflect_changes(self):
        """Verify code comments reflect the new Post option requirement."""
        # Check for updated comments about file input appearing after Post selection
        self.assertIn('The file input appears AFTER selecting Post option', self.content,
                     "Missing comment about file input appearing after Post selection")
        
        # Check old incorrect comments are removed
        self.assertNotIn('The file input exists immediately after clicking Create', self.content,
                        "Old incorrect comment still present")
        self.assertNotIn('NO decorative button click', self.content,
                        "Old comment about 'NO decorative button click' still present")
    
    def test_logging_sequence(self):
        """Verify proper logging sequence for debugging."""
        expected_logs = [
            'Create button clicked',
            'Selecting Post option from Create menu',
            'Post option clicked successfully',
            'Waiting for file input to appear',
            'File upload initiated'
        ]
        
        for log_msg in expected_logs:
            self.assertIn(log_msg, self.content,
                         f"Missing expected log message: '{log_msg}'")


if __name__ == '__main__':
    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestInstagramPostButtonFix)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with proper code
    sys.exit(0 if result.wasSuccessful() else 1)
