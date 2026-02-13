"""Campaign Manager - CRUD operations and business logic for campaign management."""

import sqlite3
import json
import uuid
import logging
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class CampaignManager:
    """
    Campaign manager for multi-campaign video upload management.
    
    Features:
    - Create and manage multiple independent campaigns
    - Assign videos to campaigns with ordering
    - Configure campaign-specific metadata (captions, hashtags, titles)
    - Support for randomized metadata selection
    - Campaign scheduling configuration
    - Upload tracking per campaign
    """
    
    def __init__(self, db_path: str = "database/videos.db"):
        """
        Initialize campaign manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        
        # Ensure database exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Import and initialize campaign schema
        from database.campaign_schema import create_campaign_tables, verify_campaign_schema
        
        # Create tables if they don't exist
        if not verify_campaign_schema(db_path):
            create_campaign_tables(db_path)
    
    def create_campaign(
        self,
        name: str,
        description: Optional[str] = None,
        status: str = 'draft'
    ) -> str:
        """
        Create a new campaign.
        
        Args:
            name: Campaign name (required)
            description: Campaign description (optional)
            status: Initial status (default: 'draft')
            
        Returns:
            Campaign ID (UUID)
            
        Raises:
            ValueError: If name is empty or status is invalid
        """
        if not name or not name.strip():
            raise ValueError("Campaign name is required")
        
        valid_statuses = ['draft', 'scheduled', 'active', 'paused', 'completed']
        if status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
        
        campaign_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO campaigns (campaign_id, name, description, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (campaign_id, name, description, status, now, now))
            
            conn.commit()
            logger.info(f"Campaign created: {campaign_id} ({name})")
            return campaign_id
            
        except Exception as e:
            logger.error(f"Failed to create campaign: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def add_videos_to_campaign(
        self,
        campaign_id: str,
        video_ids: List[str],
        replace_existing: bool = False
    ) -> bool:
        """
        Add videos to a campaign with automatic ordering.
        
        Args:
            campaign_id: Campaign identifier
            video_ids: List of video IDs to add
            replace_existing: If True, remove existing videos before adding
            
        Returns:
            True if successful, False otherwise
        """
        if not video_ids:
            logger.warning("No video IDs provided")
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Verify campaign exists
            cursor.execute('SELECT campaign_id FROM campaigns WHERE campaign_id = ?', (campaign_id,))
            if not cursor.fetchone():
                logger.error(f"Campaign not found: {campaign_id}")
                return False
            
            # Replace existing if requested
            if replace_existing:
                cursor.execute('DELETE FROM campaign_videos WHERE campaign_id = ?', (campaign_id,))
            
            # Get current max order for this campaign
            cursor.execute('''
                SELECT COALESCE(MAX(upload_order), 0) FROM campaign_videos
                WHERE campaign_id = ?
            ''', (campaign_id,))
            max_order = cursor.fetchone()[0]
            
            # Add videos with incremental ordering
            for i, video_id in enumerate(video_ids, start=1):
                # Verify video exists in video registry
                cursor.execute('SELECT id FROM videos WHERE id = ?', (video_id,))
                if not cursor.fetchone():
                    logger.warning(f"Video not found in registry: {video_id}, skipping")
                    continue
                
                # Insert or update video in campaign
                cursor.execute('''
                    INSERT OR REPLACE INTO campaign_videos (campaign_id, video_id, upload_order)
                    VALUES (?, ?, ?)
                ''', (campaign_id, video_id, max_order + i))
            
            # Update campaign timestamp
            cursor.execute('''
                UPDATE campaigns SET updated_at = ? WHERE campaign_id = ?
            ''', (datetime.now().isoformat(), campaign_id))
            
            conn.commit()
            logger.info(f"Added {len(video_ids)} videos to campaign {campaign_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add videos to campaign: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def set_campaign_metadata(
        self,
        campaign_id: str,
        metadata_config: Dict
    ) -> bool:
        """
        Set metadata configuration for a campaign.
        
        Args:
            campaign_id: Campaign identifier
            metadata_config: Dictionary with metadata settings:
                - caption_mode: 'single', 'randomized', or 'per_video'
                - captions: Text (comma-separated for randomized)
                - hashtags: Text (comma-separated)
                - title_mode: 'single', 'randomized', or 'per_video'
                - titles: Text (comma-separated for randomized)
                - add_hashtag_prefix: Boolean (default True)
                
        Returns:
            True if successful, False otherwise
        """
        # Validate modes
        caption_mode = metadata_config.get('caption_mode', 'single')
        title_mode = metadata_config.get('title_mode', 'single')
        
        valid_modes = ['single', 'randomized', 'per_video']
        if caption_mode not in valid_modes or title_mode not in valid_modes:
            raise ValueError(f"Invalid mode. Must be one of: {valid_modes}")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Verify campaign exists
            cursor.execute('SELECT campaign_id FROM campaigns WHERE campaign_id = ?', (campaign_id,))
            if not cursor.fetchone():
                logger.error(f"Campaign not found: {campaign_id}")
                return False
            
            # Insert or update metadata
            cursor.execute('''
                INSERT OR REPLACE INTO campaign_metadata
                (campaign_id, caption_mode, captions, hashtags, title_mode, titles, add_hashtag_prefix)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                campaign_id,
                caption_mode,
                metadata_config.get('captions', ''),
                metadata_config.get('hashtags', ''),
                title_mode,
                metadata_config.get('titles', ''),
                1 if metadata_config.get('add_hashtag_prefix', True) else 0
            ))
            
            # Update campaign timestamp
            cursor.execute('''
                UPDATE campaigns SET updated_at = ? WHERE campaign_id = ?
            ''', (datetime.now().isoformat(), campaign_id))
            
            conn.commit()
            logger.info(f"Metadata configured for campaign {campaign_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set campaign metadata: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def set_campaign_schedule(
        self,
        campaign_id: str,
        schedule_config: Dict
    ) -> bool:
        """
        Set scheduling configuration for a campaign.
        
        Args:
            campaign_id: Campaign identifier
            schedule_config: Dictionary with schedule settings:
                - platforms: List of platforms (e.g., ["Instagram", "TikTok"])
                - delay_seconds: Delay between uploads (default 0)
                - scheduled_start: ISO timestamp for scheduled start (optional)
                - auto_schedule: Boolean for background scheduling
                - upload_gap_hours: Hours between uploads for auto-schedule
                - upload_gap_minutes: Minutes between uploads for auto-schedule
                
        Returns:
            True if successful, False otherwise
        """
        platforms = schedule_config.get('platforms', [])
        if not platforms:
            raise ValueError("At least one platform must be specified")
        
        # Convert platforms list to JSON string
        platforms_json = json.dumps(platforms)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Verify campaign exists
            cursor.execute('SELECT campaign_id FROM campaigns WHERE campaign_id = ?', (campaign_id,))
            if not cursor.fetchone():
                logger.error(f"Campaign not found: {campaign_id}")
                return False
            
            # Insert or update schedule
            cursor.execute('''
                INSERT OR REPLACE INTO campaign_schedules
                (campaign_id, platforms, delay_seconds, scheduled_start, 
                 auto_schedule, upload_gap_hours, upload_gap_minutes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                campaign_id,
                platforms_json,
                schedule_config.get('delay_seconds', 0),
                schedule_config.get('scheduled_start'),
                1 if schedule_config.get('auto_schedule', False) else 0,
                schedule_config.get('upload_gap_hours', 1),
                schedule_config.get('upload_gap_minutes', 0)
            ))
            
            # Update campaign timestamp
            cursor.execute('''
                UPDATE campaigns SET updated_at = ? WHERE campaign_id = ?
            ''', (datetime.now().isoformat(), campaign_id))
            
            conn.commit()
            logger.info(f"Schedule configured for campaign {campaign_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set campaign schedule: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_campaign_metadata_for_upload(
        self,
        campaign_id: str,
        video_id: str
    ) -> Dict:
        """
        Get metadata for a specific upload within a campaign.
        Handles randomized selection for caption/title modes.
        
        Args:
            campaign_id: Campaign identifier
            video_id: Video identifier
            
        Returns:
            Dictionary with caption, title, hashtags
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT * FROM campaign_metadata WHERE campaign_id = ?
            ''', (campaign_id,))
            
            metadata = cursor.fetchone()
            
            if not metadata:
                logger.warning(f"No metadata found for campaign {campaign_id}")
                return {'caption': '', 'title': '', 'hashtags': ''}
            
            # Select caption based on mode
            caption = ''
            if metadata['caption_mode'] == 'single':
                caption = metadata['captions'] or ''
            elif metadata['caption_mode'] == 'randomized':
                captions_list = [c.strip() for c in (metadata['captions'] or '').split(',') if c.strip()]
                caption = random.choice(captions_list) if captions_list else ''
            
            # Select title based on mode
            title = ''
            if metadata['title_mode'] == 'single':
                title = metadata['titles'] or ''
            elif metadata['title_mode'] == 'randomized':
                titles_list = [t.strip() for t in (metadata['titles'] or '').split(',') if t.strip()]
                title = random.choice(titles_list) if titles_list else ''
            
            # Process hashtags
            hashtags = metadata['hashtags'] or ''
            add_prefix = bool(metadata['add_hashtag_prefix'])
            
            if hashtags and add_prefix:
                # Add # prefix to hashtags that don't have it
                hashtag_list = [h.strip() for h in hashtags.split(',') if h.strip()]
                hashtag_list = [f"#{h}" if not h.startswith('#') else h for h in hashtag_list]
                hashtags = ' '.join(hashtag_list)
            
            return {
                'caption': caption,
                'title': title,
                'hashtags': hashtags
            }
            
        except Exception as e:
            logger.error(f"Failed to get campaign metadata: {e}")
            return {'caption': '', 'title': '', 'hashtags': ''}
        finally:
            conn.close()
    
    def get_campaign_details(self, campaign_id: str) -> Optional[Dict]:
        """
        Get complete campaign details including videos, metadata, and schedule.
        
        Args:
            campaign_id: Campaign identifier
            
        Returns:
            Dictionary with campaign details or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # Get campaign info
            cursor.execute('SELECT * FROM campaigns WHERE campaign_id = ?', (campaign_id,))
            campaign = cursor.fetchone()
            
            if not campaign:
                return None
            
            campaign_dict = dict(campaign)
            
            # Get videos
            cursor.execute('''
                SELECT cv.video_id, cv.upload_order, v.file_path, v.title, v.duration
                FROM campaign_videos cv
                JOIN videos v ON cv.video_id = v.id
                WHERE cv.campaign_id = ?
                ORDER BY cv.upload_order
            ''', (campaign_id,))
            campaign_dict['videos'] = [dict(row) for row in cursor.fetchall()]
            
            # Get metadata
            cursor.execute('SELECT * FROM campaign_metadata WHERE campaign_id = ?', (campaign_id,))
            metadata = cursor.fetchone()
            campaign_dict['metadata'] = dict(metadata) if metadata else None
            
            # Get schedule
            cursor.execute('SELECT * FROM campaign_schedules WHERE campaign_id = ?', (campaign_id,))
            schedule = cursor.fetchone()
            if schedule:
                schedule_dict = dict(schedule)
                # Parse platforms JSON
                schedule_dict['platforms'] = json.loads(schedule_dict['platforms'])
                campaign_dict['schedule'] = schedule_dict
            else:
                campaign_dict['schedule'] = None
            
            # Get upload statistics
            cursor.execute('''
                SELECT status, COUNT(*) as count
                FROM campaign_uploads
                WHERE campaign_id = ?
                GROUP BY status
            ''', (campaign_id,))
            
            stats = {row['status']: row['count'] for row in cursor.fetchall()}
            campaign_dict['upload_stats'] = stats
            
            return campaign_dict
            
        except Exception as e:
            logger.error(f"Failed to get campaign details: {e}")
            return None
        finally:
            conn.close()
    
    def list_campaigns(self, status_filter: Optional[str] = None) -> List[Dict]:
        """
        List all campaigns with optional status filter.
        
        Args:
            status_filter: Optional status to filter by
            
        Returns:
            List of campaign dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            if status_filter:
                cursor.execute('''
                    SELECT * FROM campaigns 
                    WHERE status = ?
                    ORDER BY created_at DESC
                ''', (status_filter,))
            else:
                cursor.execute('SELECT * FROM campaigns ORDER BY created_at DESC')
            
            campaigns = [dict(row) for row in cursor.fetchall()]
            
            # Add video count and upload stats to each campaign
            for campaign in campaigns:
                campaign_id = campaign['campaign_id']
                
                # Get video count
                cursor.execute('''
                    SELECT COUNT(*) as count FROM campaign_videos WHERE campaign_id = ?
                ''', (campaign_id,))
                campaign['video_count'] = cursor.fetchone()['count']
                
                # Get upload stats
                cursor.execute('''
                    SELECT status, COUNT(*) as count
                    FROM campaign_uploads
                    WHERE campaign_id = ?
                    GROUP BY status
                ''', (campaign_id,))
                
                stats = {row['status']: row['count'] for row in cursor.fetchall()}
                campaign['upload_stats'] = stats
                
                # Get platforms
                cursor.execute('''
                    SELECT platforms FROM campaign_schedules WHERE campaign_id = ?
                ''', (campaign_id,))
                schedule = cursor.fetchone()
                if schedule:
                    campaign['platforms'] = json.loads(schedule['platforms'])
                else:
                    campaign['platforms'] = []
            
            return campaigns
            
        except Exception as e:
            logger.error(f"Failed to list campaigns: {e}")
            return []
        finally:
            conn.close()
    
    def update_campaign_status(self, campaign_id: str, new_status: str) -> bool:
        """
        Update campaign status.
        
        Args:
            campaign_id: Campaign identifier
            new_status: New status value
            
        Returns:
            True if successful, False otherwise
        """
        valid_statuses = ['draft', 'scheduled', 'active', 'paused', 'completed']
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE campaigns 
                SET status = ?, updated_at = ?
                WHERE campaign_id = ?
            ''', (new_status, datetime.now().isoformat(), campaign_id))
            
            conn.commit()
            
            if cursor.rowcount == 0:
                logger.warning(f"Campaign not found: {campaign_id}")
                return False
            
            logger.info(f"Campaign {campaign_id} status updated to {new_status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update campaign status: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def delete_campaign(self, campaign_id: str) -> bool:
        """
        Delete a campaign and all associated data.
        
        Args:
            campaign_id: Campaign identifier
            
        Returns:
            True if successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Delete from campaigns (cascade will handle related tables)
            cursor.execute('DELETE FROM campaigns WHERE campaign_id = ?', (campaign_id,))
            
            conn.commit()
            
            if cursor.rowcount == 0:
                logger.warning(f"Campaign not found: {campaign_id}")
                return False
            
            logger.info(f"Campaign deleted: {campaign_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete campaign: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_next_upload_task(self, campaign_id: str) -> Optional[Dict]:
        """
        Get the next pending upload task for a campaign.
        
        Args:
            campaign_id: Campaign identifier
            
        Returns:
            Dictionary with upload task details or None if no pending uploads
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # Find next pending upload
            cursor.execute('''
                SELECT cu.upload_id, cu.video_id, cu.platform, v.file_path, v.title
                FROM campaign_uploads cu
                JOIN videos v ON cu.video_id = v.id
                WHERE cu.campaign_id = ? AND cu.status = 'pending'
                ORDER BY cu.upload_id
                LIMIT 1
            ''', (campaign_id,))
            
            task = cursor.fetchone()
            
            if task:
                return dict(task)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get next upload task: {e}")
            return None
        finally:
            conn.close()
    
    def record_campaign_upload(
        self,
        campaign_id: str,
        video_id: str,
        platform: str,
        success: bool,
        metadata_used: Dict,
        error_message: Optional[str] = None
    ) -> str:
        """
        Record a campaign upload attempt.
        
        Args:
            campaign_id: Campaign identifier
            video_id: Video identifier
            platform: Platform name
            success: Whether upload succeeded
            metadata_used: Metadata used for this upload
            error_message: Error message if failed
            
        Returns:
            Upload ID
        """
        upload_id = str(uuid.uuid4())
        status = 'success' if success else 'failed'
        now = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO campaign_uploads
                (upload_id, campaign_id, video_id, platform, status, 
                 metadata_used, uploaded_at, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                upload_id,
                campaign_id,
                video_id,
                platform,
                status,
                json.dumps(metadata_used),
                now,
                error_message
            ))
            
            conn.commit()
            logger.info(f"Campaign upload recorded: {upload_id} ({status})")
            return upload_id
            
        except Exception as e:
            logger.error(f"Failed to record campaign upload: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def create_upload_tasks(self, campaign_id: str) -> int:
        """
        Create upload tasks for all videos and platforms in a campaign.
        
        Args:
            campaign_id: Campaign identifier
            
        Returns:
            Number of tasks created
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # Get campaign videos
            cursor.execute('''
                SELECT video_id FROM campaign_videos
                WHERE campaign_id = ?
                ORDER BY upload_order
            ''', (campaign_id,))
            video_ids = [row['video_id'] for row in cursor.fetchall()]
            
            # Get campaign platforms
            cursor.execute('''
                SELECT platforms FROM campaign_schedules
                WHERE campaign_id = ?
            ''', (campaign_id,))
            schedule = cursor.fetchone()
            
            if not schedule:
                logger.error(f"No schedule found for campaign {campaign_id}")
                return 0
            
            platforms = json.loads(schedule['platforms'])
            
            # Create upload tasks
            tasks_created = 0
            for video_id in video_ids:
                for platform in platforms:
                    upload_id = str(uuid.uuid4())
                    
                    cursor.execute('''
                        INSERT INTO campaign_uploads
                        (upload_id, campaign_id, video_id, platform, status)
                        VALUES (?, ?, ?, ?, 'pending')
                    ''', (upload_id, campaign_id, video_id, platform))
                    
                    tasks_created += 1
            
            conn.commit()
            logger.info(f"Created {tasks_created} upload tasks for campaign {campaign_id}")
            return tasks_created
            
        except Exception as e:
            logger.error(f"Failed to create upload tasks: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()
