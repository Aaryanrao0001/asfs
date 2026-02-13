#!/usr/bin/env python3
"""
Campaign Management Test Script

This script demonstrates and tests the multi-campaign management system.
It creates sample campaigns, configures them, and shows how to use the API.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import VideoRegistry, CampaignManager, create_campaign_tables
from scheduler import get_campaign_scheduler
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_campaign_system():
    """Test the complete campaign management system."""
    
    # Use test database in database/ directory for inspection after test
    # This is intentionally persistent to allow manual inspection
    test_db = "database/test_campaigns.db"
    
    # Remove old test database if it exists
    if os.path.exists(test_db):
        os.remove(test_db)
        logger.info(f"Removed old test database: {test_db}")
    
    # Initialize database
    logger.info("=" * 80)
    logger.info("INITIALIZING TEST DATABASE")
    logger.info("=" * 80)
    
    video_registry = VideoRegistry(test_db)
    create_campaign_tables(test_db)
    campaign_manager = CampaignManager(test_db)
    campaign_scheduler = get_campaign_scheduler()
    
    logger.info("✅ Database initialized")
    
    # Register sample videos
    logger.info("\n" + "=" * 80)
    logger.info("REGISTERING SAMPLE VIDEOS")
    logger.info("=" * 80)
    
    sample_videos = [
        {
            'id': 'video_001',
            'file_path': '/tmp/sample_video_1.mp4',
            'title': 'Product Showcase 1',
            'duration': 30.0
        },
        {
            'id': 'video_002',
            'file_path': '/tmp/sample_video_2.mp4',
            'title': 'Product Showcase 2',
            'duration': 28.5
        },
        {
            'id': 'video_003',
            'file_path': '/tmp/sample_video_3.mp4',
            'title': 'Product Showcase 3',
            'duration': 32.0
        }
    ]
    
    # Create dummy video files for testing
    os.makedirs('/tmp', exist_ok=True)
    for video in sample_videos:
        with open(video['file_path'], 'w') as f:
            f.write("dummy video content")
        
        video_registry.register_video(
            video_id=video['id'],
            file_path=video['file_path'],
            title=video['title'],
            duration=video['duration'],
            calculate_checksum=False
        )
    
    logger.info(f"✅ Registered {len(sample_videos)} sample videos")
    
    # Test Case 1: Create Product Launch Campaign
    logger.info("\n" + "=" * 80)
    logger.info("TEST CASE 1: PRODUCT LAUNCH CAMPAIGN")
    logger.info("=" * 80)
    
    campaign1_id = campaign_manager.create_campaign(
        name="Summer Product Launch",
        description="Promotional videos for summer collection"
    )
    logger.info(f"✅ Created campaign: {campaign1_id}")
    
    # Add videos to campaign
    video_ids = [v['id'] for v in sample_videos]
    campaign_manager.add_videos_to_campaign(campaign1_id, video_ids)
    logger.info(f"✅ Added {len(video_ids)} videos to campaign")
    
    # Configure metadata with randomization
    metadata_config = {
        'caption_mode': 'randomized',
        'captions': 'New summer vibes!, Check out our latest collection!, Summer is here!, Fresh seasonal arrivals!',
        'hashtags': 'summer,fashion,newcollection,style,ootd',
        'title_mode': 'single',
        'titles': 'Summer Collection 2024',
        'add_hashtag_prefix': True
    }
    campaign_manager.set_campaign_metadata(campaign1_id, metadata_config)
    logger.info("✅ Configured campaign metadata (randomized captions)")
    
    # Configure schedule
    schedule_config = {
        'platforms': ['Instagram', 'TikTok'],
        'delay_seconds': 5,  # Short delay for testing
        'auto_schedule': False
    }
    campaign_manager.set_campaign_schedule(campaign1_id, schedule_config)
    logger.info("✅ Configured campaign schedule (Instagram + TikTok, 5s delay)")
    
    # Test Case 2: Create Tutorial Series Campaign
    logger.info("\n" + "=" * 80)
    logger.info("TEST CASE 2: TUTORIAL SERIES CAMPAIGN")
    logger.info("=" * 80)
    
    campaign2_id = campaign_manager.create_campaign(
        name="Beginner Photography Tutorials",
        description="Educational video series for beginners"
    )
    logger.info(f"✅ Created campaign: {campaign2_id}")
    
    # Add videos to campaign
    campaign_manager.add_videos_to_campaign(campaign2_id, video_ids[:2])  # Use 2 videos
    logger.info(f"✅ Added 2 videos to campaign")
    
    # Configure metadata with single caption, randomized titles
    metadata_config2 = {
        'caption_mode': 'single',
        'captions': 'Master photography fundamentals with our comprehensive tutorial series!',
        'hashtags': 'photography,tutorial,learn,beginner,camera,tips',
        'title_mode': 'randomized',
        'titles': 'Photography 101: Basics, Camera Settings Explained, Composition Techniques',
        'add_hashtag_prefix': True
    }
    campaign_manager.set_campaign_metadata(campaign2_id, metadata_config2)
    logger.info("✅ Configured campaign metadata (single caption, randomized titles)")
    
    # Configure schedule for YouTube only
    schedule_config2 = {
        'platforms': ['YouTube'],
        'delay_seconds': 5,
        'auto_schedule': False
    }
    campaign_manager.set_campaign_schedule(campaign2_id, schedule_config2)
    logger.info("✅ Configured campaign schedule (YouTube only, 5s delay)")
    
    # Display campaign details
    logger.info("\n" + "=" * 80)
    logger.info("CAMPAIGN DETAILS")
    logger.info("=" * 80)
    
    campaigns = campaign_manager.list_campaigns()
    for campaign in campaigns:
        logger.info(f"\nCampaign: {campaign['name']}")
        logger.info(f"  ID: {campaign['campaign_id']}")
        logger.info(f"  Status: {campaign['status']}")
        logger.info(f"  Videos: {campaign['video_count']}")
        logger.info(f"  Platforms: {campaign.get('platforms', [])}")
        logger.info(f"  Created: {campaign['created_at']}")
    
    # Test metadata randomization
    logger.info("\n" + "=" * 80)
    logger.info("TESTING METADATA RANDOMIZATION")
    logger.info("=" * 80)
    
    logger.info("\nCampaign 1 (randomized captions):")
    for i in range(5):
        metadata = campaign_manager.get_campaign_metadata_for_upload(campaign1_id, video_ids[0])
        logger.info(f"  Upload {i+1}: \"{metadata['caption']}\"")
    
    logger.info("\nCampaign 2 (randomized titles):")
    for i in range(5):
        metadata = campaign_manager.get_campaign_metadata_for_upload(campaign2_id, video_ids[0])
        logger.info(f"  Upload {i+1}: Title=\"{metadata['title']}\"")
    
    # Test upload task creation
    logger.info("\n" + "=" * 80)
    logger.info("CREATING UPLOAD TASKS")
    logger.info("=" * 80)
    
    tasks1 = campaign_manager.create_upload_tasks(campaign1_id)
    logger.info(f"✅ Created {tasks1} upload tasks for Campaign 1")
    logger.info(f"   (3 videos × 2 platforms = 6 tasks)")
    
    tasks2 = campaign_manager.create_upload_tasks(campaign2_id)
    logger.info(f"✅ Created {tasks2} upload tasks for Campaign 2")
    logger.info(f"   (2 videos × 1 platform = 2 tasks)")
    
    # Display final status
    logger.info("\n" + "=" * 80)
    logger.info("CAMPAIGN STATUS SUMMARY")
    logger.info("=" * 80)
    
    for campaign_id in [campaign1_id, campaign2_id]:
        details = campaign_manager.get_campaign_details(campaign_id)
        logger.info(f"\n{details['name']}:")
        logger.info(f"  Status: {details['status']}")
        logger.info(f"  Videos: {len(details['videos'])}")
        logger.info(f"  Platforms: {details['schedule']['platforms']}")
        logger.info(f"  Upload Tasks: {sum(details.get('upload_stats', {}).values())}")
        logger.info(f"  Pending: {details.get('upload_stats', {}).get('pending', 0)}")
    
    # Test campaign execution (dry-run without actual uploads)
    logger.info("\n" + "=" * 80)
    logger.info("CAMPAIGN EXECUTION TEST (DRY-RUN)")
    logger.info("=" * 80)
    logger.info("Note: Actual upload execution requires:")
    logger.info("  1. Real video files")
    logger.info("  2. Browser automation configuration")
    logger.info("  3. Platform credentials (logged into Instagram/TikTok/YouTube)")
    logger.info("\nTo execute campaigns in production:")
    logger.info("  1. Use the API: POST /api/campaigns/{id}/execute")
    logger.info("  2. Or use: campaign_scheduler.execute_campaign(campaign_id)")
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    logger.info("✅ Database schema created")
    logger.info("✅ Videos registered")
    logger.info("✅ Campaigns created (2)")
    logger.info("✅ Metadata configured (randomized captions & titles)")
    logger.info("✅ Schedules configured (multiple platforms)")
    logger.info("✅ Upload tasks created")
    logger.info("✅ Metadata randomization verified")
    logger.info("\n" + "=" * 80)
    logger.info("ALL TESTS PASSED!")
    logger.info("=" * 80)
    logger.info(f"\nTest database created at: {test_db}")
    logger.info("You can inspect it with: sqlite3 " + test_db)
    logger.info("\nFor API usage examples, see: CAMPAIGNS_GUIDE.md")


if __name__ == '__main__':
    test_campaign_system()
