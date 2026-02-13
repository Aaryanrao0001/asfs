"""Campaign Manager - SQLite-based campaign and video assignment system."""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class CampaignManager:
    """
    Campaign manager for creating and managing multiple independent campaigns.
    
    Each campaign can have:
    - Its own set of videos
    - Independent schedules
    - Unique captions, hashtags, and titles
    - Different platform selections
    
    Manages two tables:
    - campaigns: Master registry of all campaigns
    - campaign_videos: Video assignments to campaigns with campaign-specific metadata
    """
    
    def __init__(self, db_path: str = "database/campaigns.db"):
        """
        Initialize campaign manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        
        # Create directory if needed
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Create database tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Campaigns table - master registry
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TEXT NOT NULL,
                platforms TEXT NOT NULL,
                schedule_enabled INTEGER DEFAULT 0,
                schedule_gap_hours INTEGER DEFAULT 1,
                schedule_gap_minutes INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        # Campaign videos table - video assignments with campaign-specific metadata
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS campaign_videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id INTEGER NOT NULL,
                video_id TEXT NOT NULL,
                title TEXT,
                caption TEXT,
                hashtags TEXT,
                added_at TEXT NOT NULL,
                upload_order INTEGER DEFAULT 0,
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE,
                UNIQUE(campaign_id, video_id)
            )
        ''')
        
        # Create indexes for faster lookups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_campaign_videos_campaign
            ON campaign_videos(campaign_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_campaign_videos_video
            ON campaign_videos(video_id)
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info(f"Campaign manager database initialized: {self.db_path}")
    
    def create_campaign(
        self,
        name: str,
        description: str = "",
        platforms: List[str] = None,
        schedule_enabled: bool = False,
        schedule_gap_hours: int = 1,
        schedule_gap_minutes: int = 0
    ) -> Optional[int]:
        """
        Create a new campaign.
        
        Args:
            name: Campaign name (must be unique)
            description: Campaign description
            platforms: List of platform names (Instagram, TikTok, YouTube)
            schedule_enabled: Whether scheduling is enabled
            schedule_gap_hours: Hours between scheduled uploads
            schedule_gap_minutes: Minutes between scheduled uploads
            
        Returns:
            Campaign ID if successful, None otherwise
        """
        if platforms is None:
            platforms = ["Instagram", "TikTok", "YouTube"]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO campaigns 
                (name, description, created_at, platforms, schedule_enabled, 
                 schedule_gap_hours, schedule_gap_minutes, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                name,
                description,
                datetime.now().isoformat(),
                json.dumps(platforms),
                1 if schedule_enabled else 0,
                schedule_gap_hours,
                schedule_gap_minutes,
                1
            ))
            
            campaign_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Campaign created: {name} (ID: {campaign_id})")
            return campaign_id
            
        except sqlite3.IntegrityError:
            logger.warning(f"Campaign with name '{name}' already exists")
            return None
        except Exception as e:
            logger.error(f"Failed to create campaign: {e}")
            return None
        finally:
            conn.close()
    
    def update_campaign(
        self,
        campaign_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        platforms: Optional[List[str]] = None,
        schedule_enabled: Optional[bool] = None,
        schedule_gap_hours: Optional[int] = None,
        schedule_gap_minutes: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> bool:
        """
        Update campaign settings.
        
        Args:
            campaign_id: Campaign ID
            name: New campaign name
            description: New description
            platforms: New platform list
            schedule_enabled: New schedule enabled status
            schedule_gap_hours: New schedule gap hours
            schedule_gap_minutes: New schedule gap minutes
            is_active: New active status
            
        Returns:
            True if successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Build update query dynamically based on provided parameters
            updates = []
            values = []
            
            if name is not None:
                updates.append("name = ?")
                values.append(name)
            if description is not None:
                updates.append("description = ?")
                values.append(description)
            if platforms is not None:
                updates.append("platforms = ?")
                values.append(json.dumps(platforms))
            if schedule_enabled is not None:
                updates.append("schedule_enabled = ?")
                values.append(1 if schedule_enabled else 0)
            if schedule_gap_hours is not None:
                updates.append("schedule_gap_hours = ?")
                values.append(schedule_gap_hours)
            if schedule_gap_minutes is not None:
                updates.append("schedule_gap_minutes = ?")
                values.append(schedule_gap_minutes)
            if is_active is not None:
                updates.append("is_active = ?")
                values.append(1 if is_active else 0)
            
            if not updates:
                logger.warning("No updates provided for campaign")
                return False
            
            values.append(campaign_id)
            query = f"UPDATE campaigns SET {', '.join(updates)} WHERE id = ?"
            
            cursor.execute(query, values)
            conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"Campaign {campaign_id} updated")
                return True
            else:
                logger.warning(f"Campaign {campaign_id} not found")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update campaign: {e}")
            return False
        finally:
            conn.close()
    
    def delete_campaign(self, campaign_id: int) -> bool:
        """
        Delete a campaign and all its video assignments.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            True if successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM campaigns WHERE id = ?', (campaign_id,))
            conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"Campaign {campaign_id} deleted")
                return True
            else:
                logger.warning(f"Campaign {campaign_id} not found")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete campaign: {e}")
            return False
        finally:
            conn.close()
    
    def get_campaign(self, campaign_id: int) -> Optional[Dict]:
        """
        Get campaign details.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            Campaign dictionary or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM campaigns WHERE id = ?', (campaign_id,))
            row = cursor.fetchone()
            
            if row:
                campaign = dict(row)
                campaign['platforms'] = json.loads(campaign['platforms'])
                campaign['schedule_enabled'] = bool(campaign['schedule_enabled'])
                campaign['is_active'] = bool(campaign['is_active'])
                return campaign
            return None
            
        except Exception as e:
            logger.error(f"Failed to get campaign: {e}")
            return None
        finally:
            conn.close()
    
    def list_campaigns(self, active_only: bool = False) -> List[Dict]:
        """
        List all campaigns.
        
        Args:
            active_only: If True, only return active campaigns
            
        Returns:
            List of campaign dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            if active_only:
                cursor.execute('SELECT * FROM campaigns WHERE is_active = 1 ORDER BY created_at DESC')
            else:
                cursor.execute('SELECT * FROM campaigns ORDER BY created_at DESC')
            
            campaigns = []
            for row in cursor.fetchall():
                campaign = dict(row)
                campaign['platforms'] = json.loads(campaign['platforms'])
                campaign['schedule_enabled'] = bool(campaign['schedule_enabled'])
                campaign['is_active'] = bool(campaign['is_active'])
                campaigns.append(campaign)
            
            return campaigns
            
        except Exception as e:
            logger.error(f"Failed to list campaigns: {e}")
            return []
        finally:
            conn.close()
    
    def add_video_to_campaign(
        self,
        campaign_id: int,
        video_id: str,
        title: Optional[str] = None,
        caption: Optional[str] = None,
        hashtags: Optional[str] = None,
        upload_order: int = 0
    ) -> bool:
        """
        Add a video to a campaign with campaign-specific metadata.
        
        Args:
            campaign_id: Campaign ID
            video_id: Video ID from video registry
            title: Campaign-specific title
            caption: Campaign-specific caption
            hashtags: Campaign-specific hashtags (comma-separated)
            upload_order: Order in the campaign's upload queue
            
        Returns:
            True if successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO campaign_videos
                (campaign_id, video_id, title, caption, hashtags, added_at, upload_order)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                campaign_id,
                video_id,
                title or "",
                caption or "",
                hashtags or "",
                datetime.now().isoformat(),
                upload_order
            ))
            
            conn.commit()
            logger.info(f"Video {video_id} added to campaign {campaign_id}")
            return True
            
        except sqlite3.IntegrityError:
            logger.warning(f"Video {video_id} already in campaign {campaign_id}")
            return False
        except Exception as e:
            logger.error(f"Failed to add video to campaign: {e}")
            return False
        finally:
            conn.close()
    
    def remove_video_from_campaign(self, campaign_id: int, video_id: str) -> bool:
        """
        Remove a video from a campaign.
        
        Args:
            campaign_id: Campaign ID
            video_id: Video ID
            
        Returns:
            True if successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                DELETE FROM campaign_videos
                WHERE campaign_id = ? AND video_id = ?
            ''', (campaign_id, video_id))
            
            conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"Video {video_id} removed from campaign {campaign_id}")
                return True
            else:
                logger.warning(f"Video {video_id} not in campaign {campaign_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to remove video from campaign: {e}")
            return False
        finally:
            conn.close()
    
    def update_campaign_video_metadata(
        self,
        campaign_id: int,
        video_id: str,
        title: Optional[str] = None,
        caption: Optional[str] = None,
        hashtags: Optional[str] = None,
        upload_order: Optional[int] = None
    ) -> bool:
        """
        Update metadata for a video in a campaign.
        
        Args:
            campaign_id: Campaign ID
            video_id: Video ID
            title: New title
            caption: New caption
            hashtags: New hashtags
            upload_order: New upload order
            
        Returns:
            True if successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            updates = []
            values = []
            
            if title is not None:
                updates.append("title = ?")
                values.append(title)
            if caption is not None:
                updates.append("caption = ?")
                values.append(caption)
            if hashtags is not None:
                updates.append("hashtags = ?")
                values.append(hashtags)
            if upload_order is not None:
                updates.append("upload_order = ?")
                values.append(upload_order)
            
            if not updates:
                return False
            
            values.extend([campaign_id, video_id])
            query = f"UPDATE campaign_videos SET {', '.join(updates)} WHERE campaign_id = ? AND video_id = ?"
            
            cursor.execute(query, values)
            conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"Metadata updated for video {video_id} in campaign {campaign_id}")
                return True
            else:
                logger.warning(f"Video {video_id} not found in campaign {campaign_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update campaign video metadata: {e}")
            return False
        finally:
            conn.close()
    
    def get_campaign_videos(self, campaign_id: int) -> List[Dict]:
        """
        Get all videos in a campaign with their metadata.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            List of video dictionaries with campaign-specific metadata
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT * FROM campaign_videos
                WHERE campaign_id = ?
                ORDER BY upload_order, added_at
            ''', (campaign_id,))
            
            videos = []
            for row in cursor.fetchall():
                videos.append(dict(row))
            
            return videos
            
        except Exception as e:
            logger.error(f"Failed to get campaign videos: {e}")
            return []
        finally:
            conn.close()
    
    def get_video_campaigns(self, video_id: str) -> List[Dict]:
        """
        Get all campaigns a video belongs to.
        
        Args:
            video_id: Video ID
            
        Returns:
            List of campaign dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT c.*, cv.title as video_title, cv.caption, cv.hashtags
                FROM campaigns c
                JOIN campaign_videos cv ON c.id = cv.campaign_id
                WHERE cv.video_id = ?
                ORDER BY c.created_at DESC
            ''', (video_id,))
            
            campaigns = []
            for row in cursor.fetchall():
                campaign = dict(row)
                campaign['platforms'] = json.loads(campaign['platforms'])
                campaign['schedule_enabled'] = bool(campaign['schedule_enabled'])
                campaign['is_active'] = bool(campaign['is_active'])
                campaigns.append(campaign)
            
            return campaigns
            
        except Exception as e:
            logger.error(f"Failed to get video campaigns: {e}")
            return []
        finally:
            conn.close()
