#!/usr/bin/env python3
"""
Test suite for Instagram and TikTok selector improvements.

Tests that both uploaders use stable, semantic selectors:
1. ARIA labels (aria-label) instead of hashed CSS classes
2. Role attributes (role="button", role="textbox")
3. Text-based selectors with role combinations
4. Data attributes (data-e2e) for TikTok
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


class TestInstagramStableSelectors(unittest.TestCase):
    """Test that Instagram uses stable, semantic selectors."""
    
    def setUp(self):
        """Set up test by reading the brave_instagram.py file."""
        self.instagram_file = Path(__file__).parent / "uploaders" / "brave_instagram.py"
        self.content = self.instagram_file.read_text(encoding='utf-8')
    
    def test_create_button_uses_aria_label(self):
        """Verify Create button prioritizes svg[aria-label="New post"]."""
        # Check that exact ARIA label is the first selector
        self.assertIn('svg[aria-label="New post"]', self.content,
                     "Missing stable svg[aria-label=\"New post\"] selector")
        
        # Verify it's in the INSTAGRAM_CREATE_SELECTORS list
        lines = self.content.split('\n')
        in_selectors_block = False
        found_exact_match = False
        
        for line in lines:
            if 'INSTAGRAM_CREATE_SELECTORS' in line:
                in_selectors_block = True
            elif in_selectors_block and 'svg[aria-label="New post"]' in line:
                found_exact_match = True
                break
            elif in_selectors_block and line.strip() == ']':
                break
        
        self.assertTrue(found_exact_match, 
                       "svg[aria-label=\"New post\"] should be in INSTAGRAM_CREATE_SELECTORS")
    
    def test_no_hashed_class_selectors(self):
        """Verify no usage of hashed CSS class names like x1i10hfl."""
        # Common patterns for React CSS module hashes
        hashed_patterns = [
            'x1i10hfl',  # Example from problem statement
            'xjqpnuy',
            'xc5r6h4',
            # More generic patterns
            '.x[0-9]',  # Classes starting with x followed by number
        ]
        
        for pattern in hashed_patterns[:3]:  # Check specific examples
            self.assertNotIn(pattern, self.content,
                           f"Found hashed class name pattern: {pattern}")
    
    def test_next_button_uses_role_selector(self):
        """Verify Next button uses div[role="button"] selector."""
        # Check for the parameterized version (more flexible, handles both Next and Share)
        self.assertIn('div[role="button"]:has-text("{button_text}")', self.content,
                     "Next button should use role-based selector with button_text parameter")
        # Verify documentation mentions Next button usage
        self.assertIn('"Next"', self.content,
                     "Documentation should mention Next button usage")
        
        # Also check for comment explaining it's React-heavy
        self.assertIn('Instagram is React-heavy', self.content,
                     "Should have comment about React state transitions")
    
    def test_caption_uses_role_textbox(self):
        """Verify caption field uses div[role="textbox"] selector."""
        self.assertIn('div[role="textbox"]', self.content,
                     "Caption field should use role=\"textbox\" selector")
        
        # Check for aria-label in caption selector
        self.assertIn('[aria-label*="caption"]', self.content,
                     "Caption should use aria-label attribute")
    
    def test_share_button_uses_role_selector(self):
        """Verify Share button uses div[role="button"] selector."""
        # Check for the parameterized version (more flexible, handles both Next and Share)
        self.assertIn('div[role="button"]:has-text("{button_text}")', self.content,
                     "Share button should use role-based selector with button_text parameter")
        # Verify documentation mentions Share button usage
        self.assertIn('"Share"', self.content,
                     "Documentation should mention Share button usage")
    
    def test_file_upload_uses_input_type(self):
        """Verify file upload uses input[type="file"] directly."""
        self.assertIn('input[type="file"]', self.content,
                     "File upload should use input[type=\"file\"] selector")
        
        # Verify we're not clicking UI buttons for file selection
        # (we should use set_input_files or similar direct approach)
        self.assertIn('.upload_file(', self.content,
                     "Should use upload_file method")
    
    def test_comment_quality(self):
        """Verify comments explain selector stability."""
        # Check for comments about stable selectors
        stability_comments = [
            'stable',
            'ARIA',
            'role',
            'semantic',
        ]
        
        found_comments = 0
        for keyword in stability_comments:
            if keyword in self.content:
                found_comments += 1
        
        self.assertGreaterEqual(found_comments, 2,
                               "Should have comments explaining stable selector usage")


class TestTikTokStableSelectors(unittest.TestCase):
    """Test that TikTok uses stable, semantic selectors."""
    
    def setUp(self):
        """Set up test by reading the brave_tiktok.py file."""
        self.tiktok_file = Path(__file__).parent / "uploaders" / "brave_tiktok.py"
        self.content = self.tiktok_file.read_text(encoding='utf-8')
    
    def test_uses_data_e2e_attributes(self):
        """Verify TikTok uses data-e2e test attributes."""
        # TikTok provides data-e2e attributes for testing
        data_e2e_attrs = [
            'data-e2e="caption-input"',
            'data-e2e="post-button"',
        ]
        
        for attr in data_e2e_attrs:
            self.assertIn(attr, self.content,
                         f"Should use stable {attr} attribute")
    
    def test_caption_uses_contenteditable(self):
        """Verify caption uses contenteditable with fallbacks."""
        self.assertIn('div[contenteditable="true"]', self.content,
                     "Caption should support contenteditable selector")
    
    def test_post_button_has_role_fallback(self):
        """Verify Post button uses role-based fallback."""
        self.assertIn('div[role="button"]:has-text("Post")', self.content,
                     "Post button should have role-based fallback")
    
    def test_file_upload_uses_input_type(self):
        """Verify file upload uses input[type="file"] directly."""
        self.assertIn('input[type="file"]', self.content,
                     "File upload should use input[type=\"file\"] selector")
    
    def test_no_hashed_class_selectors(self):
        """Verify no usage of hashed CSS class names."""
        # TikTok also uses CSS modules, avoid hashed classes
        hashed_patterns = [
            'x1i10hfl',
            'xjqpnuy',
        ]
        
        for pattern in hashed_patterns:
            self.assertNotIn(pattern, self.content,
                           f"Found hashed class name pattern: {pattern}")
    
    def test_comment_quality(self):
        """Verify comments explain selector choices."""
        # Check for explanatory comments
        self.assertIn('data-e2e', self.content,
                     "Should mention data-e2e attributes")
        self.assertIn('Stable selectors', self.content,
                     "Should have comment about stable selectors")


class TestSelectorPriority(unittest.TestCase):
    """Test that selectors are prioritized correctly."""
    
    def test_instagram_create_button_priority(self):
        """Verify Instagram Create button selectors are in correct priority order."""
        instagram_file = Path(__file__).parent / "uploaders" / "brave_instagram.py"
        content = instagram_file.read_text(encoding='utf-8')
        
        # Extract the INSTAGRAM_CREATE_SELECTORS list
        lines = content.split('\n')
        selectors = []
        in_list = False
        
        for line in lines:
            if 'INSTAGRAM_CREATE_SELECTORS = [' in line:
                in_list = True
            elif in_list:
                if ']' in line and not line.strip().startswith("'"):
                    break
                # Extract selector from line like "    'svg[aria-label="New post"]',  # Comment"
                if "'" in line:
                    selector = line.strip().split("'")[1]
                    selectors.append(selector)
        
        # First selector should be exact ARIA label
        self.assertTrue(len(selectors) > 0, "Should have selectors")
        self.assertEqual(selectors[0], 'svg[aria-label="New post"]',
                        "First selector should be exact ARIA label match")


if __name__ == '__main__':
    # Run tests
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with proper code
    sys.exit(0 if result.wasSuccessful() else 1)
