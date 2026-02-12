"""SQLite-based audit logging system."""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Audit logger for tracking pipeline events and uploads.
    """
    
    def __init__(self, db_path: str = "audit/events.db"):
        """
        Initialize audit logger.
        
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
        
        # Pipeline events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pipeline_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                video_path TEXT,
                stage TEXT NOT NULL,
                status TEXT NOT NULL,
                details TEXT,
                error_message TEXT
            )
        ''')
        
        # Upload events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS upload_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                clip_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                status TEXT NOT NULL,
                upload_id TEXT,
                retry_count INTEGER DEFAULT 0,
                error_message TEXT,
                metadata TEXT
            )
        ''')
        
        # Clips table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clip_id TEXT UNIQUE NOT NULL,
                video_path TEXT,
                start_time REAL,
                end_time REAL,
                duration REAL,
                file_path TEXT,
                score REAL,
                created_at TEXT,
                metadata TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info(f"Audit database initialized: {self.db_path}")
    
    def log_pipeline_event(
        self,
        stage: str,
        status: str,
        video_path: Optional[str] = None,
        details: Optional[Dict] = None,
        error_message: Optional[str] = None
    ):
        """
        Log a pipeline stage event.
        
        Args:
            stage: Pipeline stage name
            status: Event status (started, completed, failed)
            video_path: Input video path
            details: Additional details dictionary
            error_message: Error message if failed
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO pipeline_events 
            (timestamp, video_path, stage, status, details, error_message)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            video_path,
            stage,
            status,
            json.dumps(details) if details else None,
            error_message
        ))
        
        conn.commit()
        conn.close()
        
        logger.debug(f"Pipeline event logged: {stage} - {status}")
    
    def log_upload_event(
        self,
        clip_id: str,
        platform: str,
        status: str,
        upload_id: Optional[str] = None,
        retry_count: int = 0,
        error_message: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Log an upload event.
        
        Args:
            clip_id: Clip identifier (video_id)
            platform: Platform name
            status: Upload status (pending, uploading, success, failed)
            upload_id: Platform-specific upload ID
            retry_count: Number of retry attempts
            error_message: Error message if failed
            metadata: Additional metadata
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO upload_events
            (timestamp, clip_id, platform, status, upload_id, retry_count, error_message, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            clip_id,
            platform,
            status,
            upload_id,
            retry_count,
            error_message,
            json.dumps(metadata) if metadata else None
        ))
        
        conn.commit()
        conn.close()
        
        logger.debug(f"Upload event logged: {clip_id} to {platform} - {status}")
        
        # Also log to structured JSON file
        self._log_upload_to_json(clip_id, platform, status, upload_id, 
                                 retry_count, error_message, metadata)
    
    def _log_upload_to_json(
        self,
        video_id: str,
        platform: str,
        status: str,
        upload_id: Optional[str] = None,
        retry_count: int = 0,
        error_message: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Log upload event to structured JSON file.
        
        Args:
            video_id: Video identifier
            platform: Platform name
            status: Upload status
            upload_id: Platform post ID
            retry_count: Retry count
            error_message: Error message
            metadata: Additional metadata
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "video_id": video_id,
            "platform": platform,
            "status": status,
            "upload_id": upload_id,
            "retry_count": retry_count,
            "error_message": error_message,
            "metadata": metadata
        }
        
        # Ensure logs directory exists
        Path("logs").mkdir(exist_ok=True)
        
        # Append to uploads.log
        try:
            with open("logs/uploads.log", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to write to uploads.log: {e}")
    
    def log_clip(self, clip: Dict):
        """
        Log a generated clip.
        
        Args:
            clip: Clip dictionary with metadata
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO clips
                (clip_id, video_path, start_time, end_time, duration, file_path, score, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                clip.get("clip_id"),
                clip.get("source_video"),
                clip.get("start"),
                clip.get("end"),
                clip.get("duration"),
                clip.get("file_path"),
                clip.get("overall_score"),
                datetime.now().isoformat(),
                json.dumps(clip)
            ))
            
            conn.commit()
        except sqlite3.IntegrityError:
            logger.warning(f"Clip {clip.get('clip_id')} already exists in database")
        finally:
            conn.close()
    
    def get_upload_history(
        self,
        clip_id: Optional[str] = None,
        platform: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Query upload history.
        
        Args:
            clip_id: Filter by clip ID
            platform: Filter by platform
            limit: Maximum number of results
            
        Returns:
            List of upload event dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM upload_events WHERE 1=1"
        params = []
        
        if clip_id:
            query += " AND clip_id = ?"
            params.append(clip_id)
        
        if platform:
            query += " AND platform = ?"
            params.append(platform)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        
        results = []
        for row in cursor.fetchall():
            results.append(dict(row))
        
        conn.close()
        
        return results
    
    def get_pipeline_summary(self, video_path: Optional[str] = None) -> Dict:
        """
        Get pipeline execution summary.
        
        Args:
            video_path: Filter by video path
            
        Returns:
            Summary dictionary with stage statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT stage, status, COUNT(*) as count FROM pipeline_events"
        params = []
        
        if video_path:
            query += " WHERE video_path = ?"
            params.append(video_path)
        
        query += " GROUP BY stage, status"
        
        cursor.execute(query, params)
        
        summary = {}
        for row in cursor.fetchall():
            stage, status, count = row
            if stage not in summary:
                summary[stage] = {}
            summary[stage][status] = count
        
        conn.close()
        
        return summary
