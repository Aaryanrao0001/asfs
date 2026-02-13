"""Video Registry - SQLite-based video and upload tracking system."""

import sqlite3
import hashlib
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class VideoRegistry:
    """
    Video registry for tracking videos and their upload status across platforms.
    
    Manages two tables:
    - videos: Master registry of all videos
    - video_uploads: Per-platform upload tracking with retry logic
    """
    
    def __init__(self, db_path: str = "database/videos.db"):
        """
        Initialize video registry.
        
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
        
        # Videos table - master registry
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id TEXT PRIMARY KEY,
                file_path TEXT NOT NULL,
                title TEXT,
                created_at TEXT NOT NULL,
                duration REAL,
                checksum TEXT,
                duplicate_allowed INTEGER DEFAULT 0
            )
        ''')
        
        # Video uploads table - per-platform tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_uploads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                upload_status TEXT NOT NULL,
                upload_timestamp TEXT NOT NULL,
                platform_post_id TEXT,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                FOREIGN KEY (video_id) REFERENCES videos(id),
                UNIQUE(video_id, platform)
            )
        ''')
        
        # Create index for faster lookups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_video_uploads_status 
            ON video_uploads(video_id, platform, upload_status)
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info(f"Video registry database initialized: {self.db_path}")
    
    def _calculate_checksum(self, file_path: str) -> Optional[str]:
        """
        Calculate SHA-256 checksum of a video file.
        
        Args:
            file_path: Path to video file
            
        Returns:
            Hex digest of file checksum or None if file doesn't exist
        """
        if not os.path.exists(file_path):
            return None
        
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                # Read file in chunks to handle large files
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate checksum for {file_path}: {e}")
            return None
    
    def register_video(
        self,
        video_id: str,
        file_path: str,
        title: Optional[str] = None,
        duration: Optional[float] = None,
        duplicate_allowed: bool = False,
        calculate_checksum: bool = True
    ) -> bool:
        """
        Register a video in the database.
        
        Args:
            video_id: Unique video identifier
            file_path: Path to video file
            title: Video title (defaults to filename)
            duration: Video duration in seconds
            duplicate_allowed: Whether duplicate uploads are allowed
            calculate_checksum: Whether to calculate file checksum
            
        Returns:
            True if registration succeeded, False otherwise
        """
        if not os.path.exists(file_path):
            logger.error(f"Cannot register video: file not found: {file_path}")
            return False
        
        # Default title to filename
        if title is None:
            title = Path(file_path).stem
        
        # Calculate checksum if requested
        checksum = None
        if calculate_checksum:
            checksum = self._calculate_checksum(file_path)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO videos (id, file_path, title, created_at, duration, checksum, duplicate_allowed)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                video_id,
                file_path,
                title,
                datetime.now().isoformat(),
                duration,
                checksum,
                1 if duplicate_allowed else 0
            ))
            
            conn.commit()
            logger.info(f"Video registered: {video_id} ({title})")
            return True
            
        except sqlite3.IntegrityError:
            logger.warning(f"Video {video_id} already registered")
            return False
        except Exception as e:
            logger.error(f"Failed to register video {video_id}: {e}")
            return False
        finally:
            conn.close()
    
    def can_upload(self, video_id: str, platform: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a video can be uploaded to a platform.
        
        Args:
            video_id: Video identifier
            platform: Platform name (Instagram, TikTok, YouTube)
            
        Returns:
            Tuple of (can_upload, reason)
            - (True, None) if upload is allowed
            - (False, reason) if upload is blocked
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if video exists and get duplicate_allowed flag
        cursor.execute('SELECT duplicate_allowed FROM videos WHERE id = ?', (video_id,))
        video = cursor.fetchone()
        
        if not video:
            conn.close()
            return False, f"Video {video_id} not registered"
        
        duplicate_allowed = bool(video['duplicate_allowed'])
        
        # Check for existing successful upload
        cursor.execute('''
            SELECT upload_status, upload_timestamp, platform_post_id
            FROM video_uploads
            WHERE video_id = ? AND platform = ? AND upload_status = 'SUCCESS'
            ORDER BY upload_timestamp DESC
            LIMIT 1
        ''', (video_id, platform))
        
        existing_upload = cursor.fetchone()
        conn.close()
        
        if existing_upload and not duplicate_allowed:
            timestamp = existing_upload['upload_timestamp']
            post_id = existing_upload['platform_post_id']
            reason = f"Video already uploaded to {platform} at {timestamp}"
            if post_id:
                reason += f" (Post ID: {post_id})"
            return False, reason
        
        return True, None
    
    def record_upload_attempt(
        self,
        video_id: str,
        platform: str,
        upload_status: str,
        platform_post_id: Optional[str] = None,
        error_message: Optional[str] = None,
        retry_count: int = 0
    ) -> bool:
        """
        Record a video upload attempt.
        
        Args:
            video_id: Video identifier
            platform: Platform name
            upload_status: Upload status (PENDING, IN_PROGRESS, SUCCESS, FAILED, FAILED_FINAL)
            platform_post_id: Platform-specific post ID if successful
            error_message: Error message if failed
            retry_count: Number of retry attempts
            
        Returns:
            True if record succeeded, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if record exists
            cursor.execute('''
                SELECT id, retry_count FROM video_uploads
                WHERE video_id = ? AND platform = ?
            ''', (video_id, platform))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record
                cursor.execute('''
                    UPDATE video_uploads
                    SET upload_status = ?,
                        upload_timestamp = ?,
                        platform_post_id = ?,
                        error_message = ?,
                        retry_count = ?
                    WHERE video_id = ? AND platform = ?
                ''', (
                    upload_status,
                    datetime.now().isoformat(),
                    platform_post_id,
                    error_message,
                    retry_count,
                    video_id,
                    platform
                ))
            else:
                # Insert new record
                cursor.execute('''
                    INSERT INTO video_uploads
                    (video_id, platform, upload_status, upload_timestamp, platform_post_id, error_message, retry_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    video_id,
                    platform,
                    upload_status,
                    datetime.now().isoformat(),
                    platform_post_id,
                    error_message,
                    retry_count
                ))
            
            conn.commit()
            logger.debug(f"Upload attempt recorded: {video_id} to {platform} - {upload_status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to record upload attempt: {e}")
            return False
        finally:
            conn.close()
    
    def get_upload_status(self, video_id: str, platform: str) -> Optional[Dict]:
        """
        Get upload status for a video on a platform.
        
        Args:
            video_id: Video identifier
            platform: Platform name
            
        Returns:
            Dictionary with upload status or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM video_uploads
            WHERE video_id = ? AND platform = ?
        ''', (video_id, platform))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_all_videos(self) -> List[Dict]:
        """
        Get all registered videos with their upload status.
        
        Returns:
            List of video dictionaries with upload status for each platform
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all videos
        cursor.execute('SELECT * FROM videos ORDER BY created_at DESC')
        videos = [dict(row) for row in cursor.fetchall()]
        
        # Get upload status for each video
        for video in videos:
            video_id = video['id']
            
            # Get upload status for each platform
            cursor.execute('''
                SELECT platform, upload_status, upload_timestamp, platform_post_id, error_message, retry_count
                FROM video_uploads
                WHERE video_id = ?
            ''', (video_id,))
            
            uploads = {}
            for row in cursor.fetchall():
                platform = row['platform']
                uploads[platform] = {
                    'status': row['upload_status'],
                    'timestamp': row['upload_timestamp'],
                    'post_id': row['platform_post_id'],
                    'error': row['error_message'],
                    'retry_count': row['retry_count']
                }
            
            video['uploads'] = uploads
        
        conn.close()
        return videos
    
    def set_duplicate_allowed(self, video_id: str, allowed: bool) -> bool:
        """
        Set duplicate upload flag for a video.
        
        Args:
            video_id: Video identifier
            allowed: Whether to allow duplicate uploads
            
        Returns:
            True if update succeeded, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE videos
                SET duplicate_allowed = ?
                WHERE id = ?
            ''', (1 if allowed else 0, video_id))
            
            conn.commit()
            updated = cursor.rowcount > 0
            
            if updated:
                logger.info(f"Video {video_id} duplicate_allowed set to {allowed}")
            else:
                logger.warning(f"Video {video_id} not found")
            
            return updated
            
        except Exception as e:
            logger.error(f"Failed to update duplicate_allowed: {e}")
            return False
        finally:
            conn.close()
    
    def get_video(self, video_id: str) -> Optional[Dict]:
        """
        Get video information by ID.
        
        Args:
            video_id: Video identifier
            
        Returns:
            Video dictionary or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM videos WHERE id = ?', (video_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def increment_retry_count(self, video_id: str, platform: str) -> int:
        """
        Increment retry count for a video upload atomically.
        
        Args:
            video_id: Video identifier
            platform: Platform name
            
        Returns:
            New retry count or -1 if failed
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Atomic increment using single UPDATE statement
            cursor.execute('''
                UPDATE video_uploads
                SET retry_count = retry_count + 1
                WHERE video_id = ? AND platform = ?
            ''', (video_id, platform))
            
            if cursor.rowcount == 0:
                logger.warning(f"Upload record not found: {video_id} on {platform}")
                return -1
            
            # Get the new count
            cursor.execute('''
                SELECT retry_count FROM video_uploads
                WHERE video_id = ? AND platform = ?
            ''', (video_id, platform))
            
            row = cursor.fetchone()
            conn.commit()
            
            if row:
                new_count = row[0]
                logger.debug(f"Retry count incremented to {new_count} for {video_id} on {platform}")
                return new_count
            else:
                return -1
                
        except Exception as e:
            logger.error(f"Failed to increment retry count: {e}")
            return -1
        finally:
            conn.close()
    
    def list_videos(self) -> List[Dict]:
        """
        List all registered videos.
        
        Returns:
            List of video dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM videos ORDER BY created_at DESC')
            videos = []
            for row in cursor.fetchall():
                videos.append(dict(row))
            return videos
        except Exception as e:
            logger.error(f"Failed to list videos: {e}")
            return []
        finally:
            conn.close()
