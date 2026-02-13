"""Test campaign management functionality."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import CampaignManager, VideoRegistry


class TestCampaignManagement(unittest.TestCase):
    """Test campaign management features."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary database files
        self.temp_dir = tempfile.mkdtemp()
        self.campaigns_db = os.path.join(self.temp_dir, "test_campaigns.db")
        self.videos_db = os.path.join(self.temp_dir, "test_videos.db")
        
        # Initialize managers
        self.campaign_manager = CampaignManager(db_path=self.campaigns_db)
        self.video_registry = VideoRegistry(db_path=self.videos_db)
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary files
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_create_campaign(self):
        """Test creating a campaign."""
        campaign_id = self.campaign_manager.create_campaign(
            name="Test Campaign 1",
            description="A test campaign",
            platforms=["Instagram", "TikTok"],
            schedule_enabled=True,
            schedule_gap_hours=2,
            schedule_gap_minutes=30
        )
        
        self.assertIsNotNone(campaign_id)
        self.assertIsInstance(campaign_id, int)
        
        # Verify campaign was created
        campaign = self.campaign_manager.get_campaign(campaign_id)
        self.assertIsNotNone(campaign)
        self.assertEqual(campaign['name'], "Test Campaign 1")
        self.assertEqual(campaign['description'], "A test campaign")
        self.assertEqual(campaign['platforms'], ["Instagram", "TikTok"])
        self.assertTrue(campaign['schedule_enabled'])
        self.assertEqual(campaign['schedule_gap_hours'], 2)
        self.assertEqual(campaign['schedule_gap_minutes'], 30)
    
    def test_create_duplicate_campaign_name(self):
        """Test that duplicate campaign names are rejected."""
        # Create first campaign
        campaign_id = self.campaign_manager.create_campaign(
            name="Unique Campaign",
            platforms=["Instagram"]
        )
        self.assertIsNotNone(campaign_id)
        
        # Try to create another with same name
        duplicate_id = self.campaign_manager.create_campaign(
            name="Unique Campaign",
            platforms=["TikTok"]
        )
        self.assertIsNone(duplicate_id)
    
    def test_update_campaign(self):
        """Test updating campaign settings."""
        # Create campaign
        campaign_id = self.campaign_manager.create_campaign(
            name="Update Test",
            platforms=["Instagram"]
        )
        
        # Update campaign
        success = self.campaign_manager.update_campaign(
            campaign_id,
            name="Updated Name",
            platforms=["Instagram", "TikTok", "YouTube"],
            schedule_enabled=True,
            schedule_gap_hours=3
        )
        
        self.assertTrue(success)
        
        # Verify updates
        campaign = self.campaign_manager.get_campaign(campaign_id)
        self.assertEqual(campaign['name'], "Updated Name")
        self.assertEqual(len(campaign['platforms']), 3)
        self.assertTrue(campaign['schedule_enabled'])
        self.assertEqual(campaign['schedule_gap_hours'], 3)
    
    def test_delete_campaign(self):
        """Test deleting a campaign."""
        # Create campaign
        campaign_id = self.campaign_manager.create_campaign(
            name="Delete Test",
            platforms=["Instagram"]
        )
        
        # Delete campaign
        success = self.campaign_manager.delete_campaign(campaign_id)
        self.assertTrue(success)
        
        # Verify it's gone
        campaign = self.campaign_manager.get_campaign(campaign_id)
        self.assertIsNone(campaign)
    
    def test_list_campaigns(self):
        """Test listing campaigns."""
        # Create multiple campaigns
        self.campaign_manager.create_campaign(
            name="Campaign 1",
            platforms=["Instagram"]
        )
        self.campaign_manager.create_campaign(
            name="Campaign 2",
            platforms=["TikTok"]
        )
        
        # List all campaigns
        campaigns = self.campaign_manager.list_campaigns()
        self.assertEqual(len(campaigns), 2)
        
        # Check they're in reverse chronological order (newest first)
        self.assertEqual(campaigns[0]['name'], "Campaign 2")
        self.assertEqual(campaigns[1]['name'], "Campaign 1")
    
    def test_add_video_to_campaign(self):
        """Test adding videos to a campaign."""
        # Create campaign
        campaign_id = self.campaign_manager.create_campaign(
            name="Video Test Campaign",
            platforms=["Instagram"]
        )
        
        # Register a test video
        video_id = "test_video_001"
        self.video_registry.register_video(
            video_id=video_id,
            file_path="/tmp/test_video.mp4",
            title="Test Video"
        )
        
        # Add video to campaign with metadata
        success = self.campaign_manager.add_video_to_campaign(
            campaign_id=campaign_id,
            video_id=video_id,
            title="Campaign Title",
            caption="Campaign Caption",
            hashtags="#campaign #test",
            upload_order=1
        )
        
        self.assertTrue(success)
        
        # Verify video is in campaign
        videos = self.campaign_manager.get_campaign_videos(campaign_id)
        self.assertEqual(len(videos), 1)
        self.assertEqual(videos[0]['video_id'], video_id)
        self.assertEqual(videos[0]['title'], "Campaign Title")
        self.assertEqual(videos[0]['caption'], "Campaign Caption")
        self.assertEqual(videos[0]['hashtags'], "#campaign #test")
    
    def test_remove_video_from_campaign(self):
        """Test removing a video from a campaign."""
        # Create campaign and add video
        campaign_id = self.campaign_manager.create_campaign(
            name="Remove Test",
            platforms=["Instagram"]
        )
        
        video_id = "test_video_002"
        self.video_registry.register_video(
            video_id=video_id,
            file_path="/tmp/test_video_2.mp4",
            title="Test Video 2"
        )
        
        self.campaign_manager.add_video_to_campaign(
            campaign_id=campaign_id,
            video_id=video_id
        )
        
        # Remove video
        success = self.campaign_manager.remove_video_from_campaign(
            campaign_id=campaign_id,
            video_id=video_id
        )
        
        self.assertTrue(success)
        
        # Verify it's removed
        videos = self.campaign_manager.get_campaign_videos(campaign_id)
        self.assertEqual(len(videos), 0)
    
    def test_update_campaign_video_metadata(self):
        """Test updating video metadata in a campaign."""
        # Setup
        campaign_id = self.campaign_manager.create_campaign(
            name="Metadata Test",
            platforms=["Instagram"]
        )
        
        video_id = "test_video_003"
        self.video_registry.register_video(
            video_id=video_id,
            file_path="/tmp/test_video_3.mp4",
            title="Test Video 3"
        )
        
        self.campaign_manager.add_video_to_campaign(
            campaign_id=campaign_id,
            video_id=video_id,
            title="Original Title",
            caption="Original Caption"
        )
        
        # Update metadata
        success = self.campaign_manager.update_campaign_video_metadata(
            campaign_id=campaign_id,
            video_id=video_id,
            title="Updated Title",
            caption="Updated Caption",
            hashtags="#updated",
            upload_order=5
        )
        
        self.assertTrue(success)
        
        # Verify updates
        videos = self.campaign_manager.get_campaign_videos(campaign_id)
        self.assertEqual(videos[0]['title'], "Updated Title")
        self.assertEqual(videos[0]['caption'], "Updated Caption")
        self.assertEqual(videos[0]['hashtags'], "#updated")
        self.assertEqual(videos[0]['upload_order'], 5)
    
    def test_multiple_campaigns_independence(self):
        """Test that campaigns are independent of each other."""
        # Create two campaigns
        campaign1_id = self.campaign_manager.create_campaign(
            name="Campaign A",
            platforms=["Instagram"],
            schedule_gap_hours=1
        )
        
        campaign2_id = self.campaign_manager.create_campaign(
            name="Campaign B",
            platforms=["TikTok"],
            schedule_gap_hours=2
        )
        
        # Register videos
        video1_id = "video_a_001"
        video2_id = "video_b_001"
        
        self.video_registry.register_video(video1_id, "/tmp/video_a.mp4", "Video A")
        self.video_registry.register_video(video2_id, "/tmp/video_b.mp4", "Video B")
        
        # Add video1 to campaign1 with specific metadata
        self.campaign_manager.add_video_to_campaign(
            campaign1_id,
            video1_id,
            title="Title for Campaign A",
            caption="Caption for Campaign A"
        )
        
        # Add video2 to campaign2 with different metadata
        self.campaign_manager.add_video_to_campaign(
            campaign2_id,
            video2_id,
            title="Title for Campaign B",
            caption="Caption for Campaign B"
        )
        
        # Verify campaigns are independent
        campaign1_videos = self.campaign_manager.get_campaign_videos(campaign1_id)
        campaign2_videos = self.campaign_manager.get_campaign_videos(campaign2_id)
        
        self.assertEqual(len(campaign1_videos), 1)
        self.assertEqual(len(campaign2_videos), 1)
        
        self.assertEqual(campaign1_videos[0]['video_id'], video1_id)
        self.assertEqual(campaign1_videos[0]['caption'], "Caption for Campaign A")
        
        self.assertEqual(campaign2_videos[0]['video_id'], video2_id)
        self.assertEqual(campaign2_videos[0]['caption'], "Caption for Campaign B")
        
        # Verify campaign settings are independent
        campaign1 = self.campaign_manager.get_campaign(campaign1_id)
        campaign2 = self.campaign_manager.get_campaign(campaign2_id)
        
        self.assertEqual(campaign1['schedule_gap_hours'], 1)
        self.assertEqual(campaign2['schedule_gap_hours'], 2)
        
        self.assertEqual(campaign1['platforms'], ["Instagram"])
        self.assertEqual(campaign2['platforms'], ["TikTok"])


if __name__ == '__main__':
    unittest.main()
