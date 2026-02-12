#!/usr/bin/env python3
"""
Test suite to verify Instagram and TikTok automation efficiency.

This test ensures that the automation code does NOT contain inefficient patterns
commonly found in naive Playwright recordings, such as:
1. Redundant/duplicate clicks
2. Individual character keystrokes (keyDown/keyUp pairs)
3. Multiple selector attempts on same elements
4. Unnecessary waiting and UI navigation

The optimized implementations should use:
- Single operations for UI interactions
- Batch text input with human-like delays
- Stable, semantic selectors with prioritized fallbacks
- Minimal core steps (~20-25 for full upload flow)
"""

import os
import sys
import unittest
from pathlib import Path
import re

# Configure logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestInstagramAutomationEfficiency(unittest.TestCase):
    """Test that Instagram automation is optimized and efficient."""
    
    def setUp(self):
        """Set up test by reading the brave_instagram.py file."""
        self.instagram_file = Path(__file__).parent / "uploaders" / "brave_instagram.py"
        self.content = self.instagram_file.read_text(encoding='utf-8')
    
    def test_no_individual_keystroke_operations(self):
        """Verify no individual keyDown/keyUp operations."""
        # Check that we're NOT using individual keyboard.press for each character
        # The code should use .type() or batch operations
        
        # Count keyboard.press calls - should be minimal (only for Control+A, Backspace, etc.)
        press_count = self.content.count('keyboard.press(')
        
        # Should have only a few keyboard.press calls for special keys
        # Not one for each character of text input
        self.assertLess(press_count, 10, 
                       f"Found {press_count} keyboard.press calls - may indicate character-by-character input")
        
        # Verify we're using keyboard.type for text input
        self.assertIn('keyboard.type', self.content,
                     "Should use keyboard.type for efficient text input")
    
    def test_single_share_button_click(self):
        """Verify Share button is clicked only once per upload."""
        # Check that Share button click appears only in the necessary places
        share_clicks = self.content.count('_wait_for_button_enabled(page, "Share"')
        
        # Should appear exactly twice (once in each upload function)
        self.assertEqual(share_clicks, 2, 
                        f"Share button should be clicked exactly twice (once per function), found {share_clicks}")
    
    def test_no_redundant_create_button_clicks(self):
        """Verify Create button is clicked only once per flow."""
        # Find all Create button click locations
        lines = self.content.split('\n')
        create_clicks = []
        
        for i, line in enumerate(lines):
            if 'create_button.click()' in line.lower():
                create_clicks.append(i)
        
        # Should have exactly 2 (one in each upload function)
        self.assertEqual(len(create_clicks), 2,
                        f"Create button should be clicked exactly twice, found {len(create_clicks)}")
    
    def test_efficient_caption_input(self):
        """Verify caption is entered efficiently with delays, not character-by-character events."""
        # Check for the efficient pattern: for char in text
        self.assertIn('for char in full_caption', self.content,
                     "Caption should use efficient for-loop with delays")
        
        # Check for delay parameter
        self.assertIn('delay=random.randint(50, 150)', self.content,
                     "Should use human-like delays in text input")
        
        # Should NOT have individual keyDown/keyUp sequences
        self.assertNotIn('keyDown', self.content,
                        "Should not use low-level keyDown events")
        self.assertNotIn('keyUp', self.content,
                        "Should not use low-level keyUp events")
    
    def test_no_double_click_operations(self):
        """Verify no unnecessary double-click operations."""
        # Check for double-click patterns
        self.assertNotIn('dblclick', self.content,
                        "Should not use double-click operations")
        self.assertNotIn('click_count=2', self.content,
                        "Should not use click_count=2 (double-click)")
    
    def test_upload_function_length(self):
        """Verify upload functions are reasonably sized (not bloated with redundant steps)."""
        lines = self.content.split('\n')
        
        # Find both upload functions
        functions = []
        current_func = None
        func_lines = []
        indent_level = None
        
        for i, line in enumerate(lines):
            if 'def upload_to_instagram_browser(' in line or 'def _upload_to_instagram_with_manager(' in line:
                if current_func:
                    functions.append((current_func, func_lines))
                current_func = line.strip()
                func_lines = [line]
                indent_level = None
            elif current_func:
                if not line.strip():  # Empty line
                    func_lines.append(line)
                elif line.startswith('def ') and not line.startswith('    '):
                    # New function at module level, end current function
                    functions.append((current_func, func_lines))
                    current_func = None
                    func_lines = []
                else:
                    func_lines.append(line)
        
        if current_func:
            functions.append((current_func, func_lines))
        
        # Each function should be reasonably sized
        for func_name, func_lines_list in functions:
            # Filter out empty lines and comments-only lines
            code_lines = [l for l in func_lines_list if l.strip() and not l.strip().startswith('#')]
            
            # Should be between 50-150 lines (efficient but complete)
            self.assertGreater(len(code_lines), 50,
                             f"{func_name} is too small ({len(code_lines)} lines) - may be incomplete")
            self.assertLess(len(code_lines), 200,
                           f"{func_name} is too large ({len(code_lines)} lines) - may have redundant steps")


class TestTikTokAutomationEfficiency(unittest.TestCase):
    """Test that TikTok automation is optimized and efficient."""
    
    def setUp(self):
        """Set up test by reading the brave_tiktok.py file."""
        self.tiktok_file = Path(__file__).parent / "uploaders" / "brave_tiktok.py"
        self.content = self.tiktok_file.read_text(encoding='utf-8')
    
    def test_no_individual_keystroke_operations(self):
        """Verify no individual keyDown/keyUp operations for text input."""
        # Should NOT have individual keyboard events
        self.assertNotIn('keyDown', self.content,
                        "Should not use low-level keyDown events")
        self.assertNotIn('keyUp', self.content,
                        "Should not use low-level keyUp events")
        
        # Should use efficient .type() with delays
        self.assertIn('.type(', self.content,
                     "Should use .type() for text input")
    
    def test_no_show_more_duplicate_clicks(self):
        """Verify no duplicate 'Show more' button clicks."""
        # Check for any "Show more" references
        show_more_count = self.content.lower().count('show more')
        
        # Should have 0 or 1 (if needed), not duplicate
        self.assertLess(show_more_count, 2,
                       f"Found {show_more_count} 'Show more' references - may have duplicates")
    
    def test_no_multiple_caption_editor_clicks(self):
        """Verify caption editor is clicked once, not multiple times."""
        # Count click operations on caption-related selectors
        # Should find the element once and use it, not click multiple times
        
        # Pattern: element.click() should appear a reasonable number of times
        lines = self.content.split('\n')
        caption_section_clicks = 0
        in_caption_section = False
        
        for line in lines:
            if 'Fill in caption' in line or 'Filling caption' in line:
                in_caption_section = True
            elif 'Click Post' in line or 'Clicking Post' in line:
                in_caption_section = False
            elif in_caption_section and '.click()' in line:
                caption_section_clicks += 1
        
        # Should be 1-2 clicks max in caption section (click to focus)
        self.assertLess(caption_section_clicks, 3,
                       f"Found {caption_section_clicks} clicks in caption section - may have redundant clicks")
    
    def test_no_double_click_operations(self):
        """Verify no unnecessary double-click operations."""
        self.assertNotIn('dblclick', self.content,
                        "Should not use double-click operations")
        self.assertNotIn('click_count=2', self.content,
                        "Should not use click_count=2 (double-click)")
    
    def test_efficient_caption_input(self):
        """Verify caption is entered efficiently."""
        # Should use .type() with delays
        self.assertIn('delay=random.uniform(50, 150)', self.content,
                     "Should use human-like delays in text input")
        
        # Check for efficient loop pattern
        self.assertIn('for char in full_caption', self.content,
                     "Caption should use efficient for-loop")
    
    def test_upload_function_length(self):
        """Verify upload functions are compact (~200 lines), not bloated with redundant steps."""
        lines = self.content.split('\n')
        
        # Find both upload functions
        functions = []
        current_func = None
        func_lines = []
        
        for i, line in enumerate(lines):
            if 'def upload_to_tiktok_browser(' in line or 'def _upload_to_tiktok_with_manager(' in line:
                if current_func:
                    functions.append((current_func, func_lines))
                current_func = line.strip()
                func_lines = [line]
            elif current_func:
                if not line.strip():
                    func_lines.append(line)
                elif line.startswith('def ') and not line.startswith('    '):
                    functions.append((current_func, func_lines))
                    current_func = None
                    func_lines = []
                else:
                    func_lines.append(line)
        
        if current_func:
            functions.append((current_func, func_lines))
        
        # Each function should be compact
        for func_name, func_lines_list in functions:
            code_lines = [l for l in func_lines_list if l.strip() and not l.strip().startswith('#')]
            
            # TikTok functions should be ~100-200 lines (efficient but complete)
            self.assertGreater(len(code_lines), 50,
                             f"{func_name} is too small ({len(code_lines)} lines)")
            self.assertLess(len(code_lines), 250,
                           f"{func_name} is too large ({len(code_lines)} lines) - should be ~200 lines")
    
    def test_prioritized_selector_fallbacks(self):
        """Verify selectors use prioritized fallbacks, not multiple attempts on same target."""
        # Check for caption_selectors list
        self.assertIn('caption_selectors = [', self.content,
                     "Should have prioritized caption selector list")
        
        # Should iterate through selectors once, not multiple times
        self.assertIn('for selector in caption_selectors:', self.content,
                     "Should use single iteration through selector fallbacks")
    
    def test_single_post_button_click(self):
        """Verify Post button is clicked only once."""
        # Check post button click locations
        post_button_clicks = self.content.count('post_button.click(')
        
        # Should appear exactly twice (once in each upload function)
        self.assertEqual(post_button_clicks, 2,
                        f"Post button should be clicked exactly twice, found {post_button_clicks}")


class TestOverallEfficiency(unittest.TestCase):
    """Test overall automation efficiency metrics."""
    
    def test_instagram_uses_batch_operations(self):
        """Verify Instagram uses batch operations over individual events."""
        instagram_file = Path(__file__).parent / "uploaders" / "brave_instagram.py"
        content = instagram_file.read_text(encoding='utf-8')
        
        # Should use batch type operations
        self.assertIn('for char in', content,
                     "Should use batch text operations")
    
    def test_tiktok_uses_batch_operations(self):
        """Verify TikTok uses batch operations over individual events."""
        tiktok_file = Path(__file__).parent / "uploaders" / "brave_tiktok.py"
        content = tiktok_file.read_text(encoding='utf-8')
        
        # Should use batch type operations
        self.assertIn('for char in', content,
                     "Should use batch text operations")
    
    def test_both_use_human_delays(self):
        """Verify both implementations use human-like delays for bot detection avoidance."""
        instagram_file = Path(__file__).parent / "uploaders" / "brave_instagram.py"
        tiktok_file = Path(__file__).parent / "uploaders" / "brave_tiktok.py"
        
        instagram_content = instagram_file.read_text(encoding='utf-8')
        tiktok_content = tiktok_file.read_text(encoding='utf-8')
        
        # Both should use random delays
        self.assertIn('random', instagram_content.lower(),
                     "Instagram should use random delays")
        self.assertIn('random', tiktok_content.lower(),
                     "TikTok should use random delays")


if __name__ == '__main__':
    # Run tests
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with proper code
    sys.exit(0 if result.wasSuccessful() else 1)
