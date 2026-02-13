"""Test platform selection and metadata handling fixes."""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPlatformSelection(unittest.TestCase):
    """Test platform selection in upload operations."""
    
    def test_selected_platforms_from_settings(self):
        """Test that only selected platforms are used for uploads."""
        # Mock upload settings with only Instagram selected
        upload_settings = {
            "platforms": {
                "instagram": True,
                "tiktok": False,
                "youtube": False
            }
        }
        
        # Extract selected platforms (simulating the logic in videos_tab.py)
        selected_platforms = []
        platforms_config = upload_settings.get("platforms", {})
        
        if platforms_config.get("instagram"):
            selected_platforms.append("Instagram")
        if platforms_config.get("tiktok"):
            selected_platforms.append("TikTok")
        if platforms_config.get("youtube"):
            selected_platforms.append("YouTube")
        
        # Should only have Instagram
        self.assertEqual(selected_platforms, ["Instagram"])
        self.assertEqual(len(selected_platforms), 1)
    
    def test_multiple_platforms_selected(self):
        """Test with multiple platforms selected."""
        upload_settings = {
            "platforms": {
                "instagram": True,
                "tiktok": True,
                "youtube": False
            }
        }
        
        selected_platforms = []
        platforms_config = upload_settings.get("platforms", {})
        
        if platforms_config.get("instagram"):
            selected_platforms.append("Instagram")
        if platforms_config.get("tiktok"):
            selected_platforms.append("TikTok")
        if platforms_config.get("youtube"):
            selected_platforms.append("YouTube")
        
        self.assertEqual(set(selected_platforms), {"Instagram", "TikTok"})
        self.assertEqual(len(selected_platforms), 2)
    
    def test_no_platforms_selected(self):
        """Test with no platforms selected."""
        upload_settings = {
            "platforms": {
                "instagram": False,
                "tiktok": False,
                "youtube": False
            }
        }
        
        selected_platforms = []
        platforms_config = upload_settings.get("platforms", {})
        
        if platforms_config.get("instagram"):
            selected_platforms.append("Instagram")
        if platforms_config.get("tiktok"):
            selected_platforms.append("TikTok")
        if platforms_config.get("youtube"):
            selected_platforms.append("YouTube")
        
        self.assertEqual(selected_platforms, [])
    
    def test_all_platforms_selected(self):
        """Test with all platforms selected."""
        upload_settings = {
            "platforms": {
                "instagram": True,
                "tiktok": True,
                "youtube": True
            }
        }
        
        selected_platforms = []
        platforms_config = upload_settings.get("platforms", {})
        
        if platforms_config.get("instagram"):
            selected_platforms.append("Instagram")
        if platforms_config.get("tiktok"):
            selected_platforms.append("TikTok")
        if platforms_config.get("youtube"):
            selected_platforms.append("YouTube")
        
        self.assertEqual(set(selected_platforms), {"Instagram", "TikTok", "YouTube"})
        self.assertEqual(len(selected_platforms), 3)


class TestMetadataHandling(unittest.TestCase):
    """Test metadata (description and caption) handling."""
    
    def test_metadata_includes_description(self):
        """Test that metadata settings include description field."""
        from metadata import MetadataConfig
        from metadata.resolver import resolve_metadata
        
        config = MetadataConfig.from_ui_values(
            mode="uniform",
            title_input="Test Title",
            description_input="Test Description",
            caption_input="Test Caption",
            tags_input="#test #video",
            hashtag_prefix=True
        )
        
        metadata = resolve_metadata(config)
        
        self.assertIn("title", metadata)
        self.assertIn("description", metadata)
        self.assertIn("caption", metadata)
        self.assertEqual(metadata["title"], "Test Title")
        self.assertEqual(metadata["description"], "Test Description")
        self.assertEqual(metadata["caption"], "Test Caption")
    
    def test_metadata_randomized_mode(self):
        """Test metadata in randomized mode."""
        from metadata import MetadataConfig
        from metadata.resolver import resolve_metadata
        
        config = MetadataConfig.from_ui_values(
            mode="randomized",
            title_input="Title 1, Title 2",
            description_input="Desc 1, Desc 2",
            caption_input="Caption 1, Caption 2",
            tags_input="#tag1, #tag2",
            hashtag_prefix=True
        )
        
        metadata = resolve_metadata(config)
        
        # Should have one of the randomized values
        self.assertIn(metadata["title"], ["Title 1", "Title 2"])
        self.assertIn(metadata["description"], ["Desc 1", "Desc 2"])
        self.assertIn(metadata["caption"], ["Caption 1", "Caption 2"])
    
    def test_empty_metadata_fields(self):
        """Test handling of empty metadata fields."""
        from metadata import MetadataConfig
        from metadata.resolver import resolve_metadata
        
        config = MetadataConfig.from_ui_values(
            mode="uniform",
            title_input="",
            description_input="",
            caption_input="",
            tags_input="",
            hashtag_prefix=True
        )
        
        metadata = resolve_metadata(config)
        
        # Should handle empty values gracefully
        self.assertEqual(metadata["title"], "")
        self.assertEqual(metadata["description"], "")
        self.assertEqual(metadata["caption"], "")
        self.assertEqual(metadata["tags"], "")


if __name__ == '__main__':
    unittest.main()
