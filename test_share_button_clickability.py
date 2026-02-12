#!/usr/bin/env python3
"""
Test suite for Instagram Share button clickability enhancements.

Tests that the enhanced Share button logic includes:
1. JavaScript helper to check clickability (bounding box, z-index, pointer-events, opacity)
2. _find_best_share_button function to select the truly clickable button
3. Enhanced button selection for Share buttons specifically
4. MANDATORY button disappearance for Share button success
5. Clear error logging when upload cannot be confirmed
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


class TestShareButtonClickability(unittest.TestCase):
    """Test that Instagram Share button clickability enhancements have been properly applied."""
    
    def setUp(self):
        """Set up test by reading the brave_instagram.py file."""
        self.instagram_file = Path(__file__).parent / "uploaders" / "brave_instagram.py"
        self.content = self.instagram_file.read_text(encoding='utf-8')
    
    def test_has_clickability_check_js(self):
        """Verify JavaScript helper for clickability checking exists."""
        self.assertIn('JS_CHECK_CLICKABLE', self.content,
                     "Missing JS_CHECK_CLICKABLE constant")
        self.assertIn('getBoundingClientRect', self.content,
                     "Missing getBoundingClientRect for bounding box check")
        self.assertIn('getComputedStyle', self.content,
                     "Missing getComputedStyle for style checking")
        self.assertIn('zIndex', self.content,
                     "Missing z-index check in clickability logic")
        self.assertIn('pointerEvents', self.content,
                     "Missing pointer-events check in clickability logic")
        self.assertIn('opacity', self.content,
                     "Missing opacity check in clickability logic")
    
    def test_checks_element_at_point(self):
        """Verify clickability check includes elementFromPoint to detect covering elements."""
        self.assertIn('elementFromPoint', self.content,
                     "Missing elementFromPoint to check if element is topmost")
        self.assertIn('isTopmost', self.content,
                     "Missing isTopmost flag in clickability check")
    
    def test_has_find_best_share_button_function(self):
        """Verify _find_best_share_button function exists."""
        self.assertIn('def _find_best_share_button', self.content,
                     "Missing _find_best_share_button function")
        self.assertIn('Find the best clickable Share button', self.content,
                     "Missing documentation for _find_best_share_button")
    
    def test_find_best_share_button_checks_visibility(self):
        """Verify _find_best_share_button checks visibility and enabled state."""
        # Find the function
        func_start = self.content.find('def _find_best_share_button')
        self.assertGreater(func_start, 0, "_find_best_share_button function not found")
        
        # Get function content (next 3000 chars should cover the function)
        func_content = self.content[func_start:func_start + 3000]
        
        self.assertIn('is_visible()', func_content,
                     "_find_best_share_button should check visibility")
        self.assertIn('aria-disabled', func_content,
                     "_find_best_share_button should check aria-disabled")
    
    def test_find_best_share_button_uses_clickability_info(self):
        """Verify _find_best_share_button uses _get_clickable_button_info."""
        func_start = self.content.find('def _find_best_share_button')
        func_content = self.content[func_start:func_start + 3000]
        
        self.assertIn('_get_clickable_button_info', func_content,
                     "_find_best_share_button should use _get_clickable_button_info")
        self.assertIn('isClickable', func_content,
                     "_find_best_share_button should check isClickable flag")
    
    def test_find_best_share_button_logs_diagnostics(self):
        """Verify _find_best_share_button logs diagnostic information."""
        func_start = self.content.find('def _find_best_share_button')
        func_content = self.content[func_start:func_start + 3000]
        
        diagnostic_logs = [
            'Analyzing',
            'candidates',
            'NOT clickable',
            'CLICKABLE',
            'zIndex',
            'rect',
        ]
        
        for log_msg in diagnostic_logs:
            self.assertIn(log_msg, func_content,
                         f"_find_best_share_button should log: {log_msg}")
    
    def test_enhanced_selection_used_for_share_buttons(self):
        """Verify enhanced selection is used for Share buttons in button finding logic."""
        # Check that Share button uses _find_best_share_button
        self.assertIn('button_text.lower() == "share"', self.content,
                     "Share button special handling not found")
        
        # Find the button selection section
        selection_sections = []
        pos = 0
        while True:
            pos = self.content.find('button_text.lower() == "share"', pos)
            if pos == -1:
                break
            selection_sections.append(self.content[pos:pos + 500])
            pos += 1
        
        # At least one should have _find_best_share_button call
        has_enhanced_selection = any('_find_best_share_button' in section 
                                     for section in selection_sections)
        self.assertTrue(has_enhanced_selection,
                       "Share button should use _find_best_share_button for selection")
    
    def test_share_button_disappearance_is_mandatory(self):
        """Verify Share button disappearance is MANDATORY for success."""
        # Find Share button handling section
        share_section_start = self.content.find('# For Share button specifically')
        self.assertGreater(share_section_start, 0, "Share button section not found")
        
        share_section = self.content[share_section_start:share_section_start + 3000]  # Increased to 3000
        
        # Should return False if button doesn't disappear
        self.assertIn('return False', share_section,
                     "Share button section should return False on failure")
        
        # Should have CRITICAL or error logging
        self.assertIn('CRITICAL', share_section,
                     "Share button section should have CRITICAL error logging")
        
        # Should mention upload not confirmed
        self.assertIn('NOT confirmed', share_section,
                     "Share button section should clearly state upload NOT confirmed")
    
    def test_share_failure_has_detailed_logging(self):
        """Verify Share button failure has detailed diagnostic logging."""
        share_section_start = self.content.find('# For Share button specifically')
        share_section = self.content[share_section_start:share_section_start + 3000]  # Increased to 3000
        
        # All critical error messages must be present
        critical_messages = [
            'CRITICAL',
            'Upload NOT confirmed',
            'Manual review',
        ]
        
        for msg in critical_messages:
            self.assertIn(msg, share_section,
                         f"Share failure logging must include: '{msg}'")
    
    def test_has_get_clickable_button_info_function(self):
        """Verify _get_clickable_button_info helper function exists."""
        self.assertIn('def _get_clickable_button_info', self.content,
                     "Missing _get_clickable_button_info function")
        self.assertIn('JS_CHECK_CLICKABLE', self.content,
                     "_get_clickable_button_info should use JS_CHECK_CLICKABLE")
    
    def test_bounding_box_logged_in_diagnostics(self):
        """Verify bounding box is logged in diagnostic output."""
        self.assertIn('rect=', self.content,
                     "Bounding box (rect) should be logged in diagnostics")
    
    def test_pointer_events_logged_in_diagnostics(self):
        """Verify pointer-events is logged in diagnostic output."""
        self.assertIn('pointerEvents=', self.content,
                     "pointer-events should be logged in diagnostics")
    
    def test_no_breaking_changes_to_non_share_buttons(self):
        """Verify non-Share buttons still work with original logic."""
        # Should still select last button for non-Share buttons
        self.assertIn('# For non-Share buttons, use original logic', self.content,
                     "Non-Share buttons should use original logic")
        self.assertIn('matching_buttons[-1]', self.content,
                     "Non-Share buttons should still select last button")
    
    def test_overlay_detection_includes_pointer_events(self):
        """Verify overlay detection considers pointer-events style."""
        # The JS_CHECK_CLICKABLE should check pointer-events
        js_check_start = self.content.find('JS_CHECK_CLICKABLE')
        js_check = self.content[js_check_start:js_check_start + 1500]
        
        self.assertIn('pointerEvents', js_check,
                     "JS clickability check should include pointer-events")
        self.assertIn("pointerEvents !== 'none'", js_check,
                     "JS clickability check should verify pointer-events is not 'none'")
    
    def test_opacity_threshold_in_clickability(self):
        """Verify opacity threshold is used in clickability check."""
        js_check_start = self.content.find('JS_CHECK_CLICKABLE')
        js_check = self.content[js_check_start:js_check_start + 1500]
        
        self.assertIn('opacity', js_check,
                     "JS clickability check should check opacity")
        # Should have some opacity threshold (e.g., > 0.5 or similar)
        has_opacity_check = 'opacity >' in js_check or 'opacity <' in js_check
        self.assertTrue(has_opacity_check,
                       "JS clickability check should have opacity threshold")


if __name__ == '__main__':
    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestShareButtonClickability)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with proper code
    sys.exit(0 if result.wasSuccessful() else 1)
