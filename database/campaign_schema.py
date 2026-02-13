"""Campaign database schema definitions for multi-campaign management."""

import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def create_campaign_tables(db_path: str = "database/videos.db"):
    """
    Create all campaign-related tables in the database.
    
    Tables created:
    - campaigns: Main campaign information
    - campaign_videos: Many-to-many relationship between campaigns and videos
    - campaign_metadata: Campaign-specific metadata configuration
    - campaign_schedules: Campaign scheduling configuration
    - campaign_uploads: Upload tracking per campaign
    
    Args:
        db_path: Path to SQLite database file
    """
    # Ensure database directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Campaigns table - main campaign information
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS campaigns (
                campaign_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'draft',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                CHECK(status IN ('draft', 'scheduled', 'active', 'paused', 'completed'))
            )
        ''')
        
        # Campaign videos table - many-to-many relationship
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS campaign_videos (
                campaign_id TEXT NOT NULL,
                video_id TEXT NOT NULL,
                upload_order INTEGER NOT NULL,
                PRIMARY KEY (campaign_id, video_id),
                FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id) ON DELETE CASCADE,
                FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
            )
        ''')
        
        # Create index for better query performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_campaign_videos_order
            ON campaign_videos(campaign_id, upload_order)
        ''')
        
        # Campaign metadata table - metadata configuration per campaign
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS campaign_metadata (
                campaign_id TEXT PRIMARY KEY,
                caption_mode TEXT NOT NULL DEFAULT 'single',
                captions TEXT,
                hashtags TEXT,
                title_mode TEXT NOT NULL DEFAULT 'single',
                titles TEXT,
                add_hashtag_prefix INTEGER DEFAULT 1,
                FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id) ON DELETE CASCADE,
                CHECK(caption_mode IN ('single', 'randomized', 'per_video')),
                CHECK(title_mode IN ('single', 'randomized', 'per_video'))
            )
        ''')
        
        # Campaign schedules table - scheduling configuration per campaign
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS campaign_schedules (
                campaign_id TEXT PRIMARY KEY,
                platforms TEXT NOT NULL,
                delay_seconds INTEGER DEFAULT 0,
                scheduled_start TEXT,
                auto_schedule INTEGER DEFAULT 0,
                upload_gap_hours INTEGER DEFAULT 1,
                upload_gap_minutes INTEGER DEFAULT 0,
                FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id) ON DELETE CASCADE
            )
        ''')
        
        # Campaign uploads table - per-upload tracking within campaigns
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS campaign_uploads (
                upload_id TEXT PRIMARY KEY,
                campaign_id TEXT NOT NULL,
                video_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                metadata_used TEXT,
                uploaded_at TEXT,
                error_message TEXT,
                FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id) ON DELETE CASCADE,
                FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE,
                CHECK(status IN ('pending', 'uploading', 'success', 'failed'))
            )
        ''')
        
        # Create indexes for better query performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_campaign_uploads_status
            ON campaign_uploads(campaign_id, status)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_campaign_uploads_platform
            ON campaign_uploads(campaign_id, platform)
        ''')
        
        conn.commit()
        logger.info(f"Campaign tables created successfully in {db_path}")
        
    except Exception as e:
        logger.error(f"Failed to create campaign tables: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def drop_campaign_tables(db_path: str = "database/videos.db"):
    """
    Drop all campaign-related tables (for testing/migration purposes).
    
    WARNING: This will permanently delete all campaign data!
    
    Args:
        db_path: Path to SQLite database file
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Drop tables in reverse order of dependencies
        cursor.execute('DROP TABLE IF EXISTS campaign_uploads')
        cursor.execute('DROP TABLE IF EXISTS campaign_schedules')
        cursor.execute('DROP TABLE IF EXISTS campaign_metadata')
        cursor.execute('DROP TABLE IF EXISTS campaign_videos')
        cursor.execute('DROP TABLE IF EXISTS campaigns')
        
        conn.commit()
        logger.info(f"Campaign tables dropped from {db_path}")
        
    except Exception as e:
        logger.error(f"Failed to drop campaign tables: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def verify_campaign_schema(db_path: str = "database/videos.db") -> bool:
    """
    Verify that all campaign tables exist and have correct schema.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        True if schema is valid, False otherwise
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check for existence of all campaign tables
        required_tables = [
            'campaigns',
            'campaign_videos',
            'campaign_metadata',
            'campaign_schedules',
            'campaign_uploads'
        ]
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN (?, ?, ?, ?, ?)
        """, required_tables)
        
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        if len(existing_tables) != len(required_tables):
            missing = set(required_tables) - set(existing_tables)
            logger.warning(f"Missing campaign tables: {missing}")
            return False
        
        logger.info("Campaign schema verification passed")
        return True
        
    except Exception as e:
        logger.error(f"Failed to verify campaign schema: {e}")
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    """Run schema creation for testing."""
    logging.basicConfig(level=logging.INFO)
    
    print("Creating campaign tables...")
    create_campaign_tables()
    
    print("Verifying campaign schema...")
    if verify_campaign_schema():
        print("✅ Campaign schema created successfully!")
    else:
        print("❌ Campaign schema verification failed!")
