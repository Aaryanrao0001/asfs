# Videos Management Module

## Overview

The Videos Management Module is a production-grade upload tracking and video registry system that transforms ASFS from a pipeline-driven flow to a state-driven content lifecycle control panel.

## Features

### 1. Video Registry Database

**Location**: `database/videos.db`

**Tables**:
- `videos`: Master registry of all processed videos
  - `id` (TEXT, PRIMARY KEY): Unique video identifier
  - `file_path` (TEXT): Path to video file
  - `title` (TEXT): Video title
  - `created_at` (TEXT): ISO timestamp of creation
  - `duration` (REAL): Video duration in seconds
  - `checksum` (TEXT): SHA-256 checksum for integrity verification
  - `duplicate_allowed` (INTEGER): Flag to allow/prevent duplicate uploads (0/1)

- `video_uploads`: Per-platform upload tracking
  - `id` (INTEGER, AUTOINCREMENT): Auto-incrementing primary key
  - `video_id` (TEXT, FOREIGN KEY): References videos.id
  - `platform` (TEXT): Platform name (Instagram, TikTok, YouTube)
  - `upload_status` (TEXT): Status (PENDING, IN_PROGRESS, SUCCESS, FAILED, FAILED_FINAL, BLOCKED, RATE_LIMITED)
  - `upload_timestamp` (TEXT): ISO timestamp of last upload attempt
  - `platform_post_id` (TEXT): Platform-specific post ID (if successful)
  - `error_message` (TEXT): Error description (if failed)
  - `retry_count` (INTEGER): Number of retry attempts
  - UNIQUE constraint on (video_id, platform)

### 2. Pipeline Integration

**Stage 9 - Enhanced Scheduling & Video Registration**:
- All clips are automatically registered in the `videos` table
- Video checksums are calculated for integrity verification
- Default duplicate prevention is enabled

**Stage 10 - Enhanced Upload Tracking**:
- All upload attempts are tracked in `video_uploads` table
- Duplicate upload prevention checks before each upload
- Automatic retry counting (max 3 retries)
- Status progression: PENDING → IN_PROGRESS → SUCCESS/FAILED/FAILED_FINAL
- Structured JSON logging to `logs/uploads.log`

### 3. Direct Upload Function

**Function**: `run_upload_stage(video_id, platform, metadata=None)`

**Purpose**: Execute direct uploads without re-running pipeline stages 1-9

**Features**:
- Validates video exists in registry
- Checks file existence
- Enforces duplicate prevention rules
- Supports manual overrides
- Integrates with existing browser automation
- Tracks retry count and enforces max retry limit

**Usage**:
```python
from pipeline import run_upload_stage

# Direct upload
success = run_upload_stage(
    video_id="clip_001",
    platform="Instagram",
    metadata={"caption": "Check this out!", "hashtags": ["#viral"]}
)
```

### 4. UI - Videos Tab

**Location**: `ui/tabs/videos_tab.py`

**Features**:
- **Table View**: Displays all registered videos with columns:
  - Title: Video name
  - Duration: Video length in seconds
  - Instagram/TikTok/YouTube: Platform status with emoji indicators
  - Allow Duplicates: Toggle checkbox for per-video duplicate control
  - Actions: Per-platform upload buttons (📷 Instagram, 🎵 TikTok, ▶ YouTube)
  - File Path: Full path to video file

- **Status Indicators**:
  - ✔ (Checkmark): SUCCESS - uploaded successfully
  - ✖ (X mark): FAILED/FAILED_FINAL - upload failed
  - ⏳ (Hourglass): IN_PROGRESS - currently uploading
  - ❌ (Prohibited): BLOCKED - duplicate upload blocked
  - 🔁 (Loop): RATE_LIMITED - rate limit reached
  - ⚪ (Empty): Not uploaded yet

- **Auto-refresh**: Table refreshes every 5 seconds to show real-time status

- **Duplicate Upload Control**:
  - Toggle per-video to allow/prevent duplicates
  - Blocking dialog when duplicate upload is attempted
  - Option to enable duplicates and retry

- **Upload Actions**:
  - Per-platform upload buttons for manual uploads
  - "Upload All Pending" button for bulk operations
  - Confirmation dialogs before uploads
  - Success/failure notifications

### 5. Audit Logging

**Database Logging** (`audit/events.db`):
- All upload events are logged to the `upload_events` table
- Includes video_id, platform, status, timestamps, and error messages

**Structured JSON Logging** (`logs/uploads.log`):
- Each upload attempt is logged as a JSON line
- Format:
  ```json
  {
    "timestamp": "2026-02-11T08:00:00.000000",
    "video_id": "clip_001",
    "platform": "Instagram",
    "status": "SUCCESS",
    "upload_id": "ABC123",
    "retry_count": 0,
    "error_message": null,
    "metadata": {}
  }
  ```

### 6. PlatformUploader Interface

**Location**: `uploaders/__init__.py`

**Purpose**: Abstract interface for future platform uploader implementations

**Interface**:
```python
class PlatformUploader(ABC):
    @abstractmethod
    def upload(self, video_path: str, metadata: Dict) -> UploadResult:
        pass

@dataclass
class UploadResult:
    success: bool
    platform_post_id: Optional[str] = None
    error_message: Optional[str] = None
```

## Usage Examples

### Running the Pipeline

The pipeline automatically registers videos during Stage 9:

```bash
python pipeline.py my_video.mp4
```

### Direct Upload from UI

1. Open ASFS desktop application
2. Navigate to "🎬 Videos" tab
3. Find your video in the table
4. Click the platform button (📷/🎵/▶) to upload
5. Confirm upload in dialog
6. Watch status update in real-time

### Bulk Upload

1. Click "⬆ Upload All Pending" button
2. Confirm bulk upload
3. System uploads all videos to all platforms where not already uploaded
4. Respects duplicate prevention settings

### Managing Duplicates

**Enable Duplicates for a Video**:
1. Check the "Allow Duplicates" checkbox for that video
2. Video can now be uploaded multiple times to the same platform

**Disable Duplicates**:
1. Uncheck the "Allow Duplicates" checkbox
2. Subsequent uploads to same platform will be blocked

## Database Query Examples

### Get All Videos
```python
from database import VideoRegistry

registry = VideoRegistry()
videos = registry.get_all_videos()

for video in videos:
    print(f"{video['id']}: {video['title']}")
    print(f"  Uploads: {video['uploads']}")
```

### Check Upload Status
```python
status = registry.get_upload_status("clip_001", "Instagram")
print(f"Status: {status['upload_status']}")
print(f"Timestamp: {status['upload_timestamp']}")
```

### Manual Upload Control
```python
# Check if upload allowed
can_upload, reason = registry.can_upload("clip_001", "Instagram")

if not can_upload:
    print(f"Blocked: {reason}")
    
    # Enable duplicates and try again
    registry.set_duplicate_allowed("clip_001", True)
```

## Retry Logic

The system implements automatic retry with exponential backoff:

1. **First Failure**: Status = FAILED, retry_count = 1
2. **Second Failure**: Status = FAILED, retry_count = 2
3. **Third Failure**: Status = FAILED, retry_count = 3
4. **Fourth Failure**: Status = FAILED_FINAL (no more automatic retries)

**Manual Override**: User can manually retry even after FAILED_FINAL by clicking upload button in UI.

## Security & Rate Limiting

- File existence is validated before upload
- Checksum verification prevents corruption
- Rate limiting is enforced via existing UploadQueue
- Browser automation uses existing Brave profile management
- All uploads logged for audit trail

## Future Enhancements

- Thumbnail generation and display in UI
- Platform-specific metadata editing
- Upload scheduling/queuing
- Analytics dashboard
- Export to CSV/JSON
- Webhook notifications on upload completion
- Multi-threaded bulk uploads
- Progress bars for individual uploads
- Video preview in UI

## Troubleshooting

### "Video file not found" Error
- Verify file path in database matches actual file location
- Check file permissions
- Ensure file wasn't deleted after registration

### "Max retries exceeded" (FAILED_FINAL)
- Check browser automation logs
- Verify platform credentials
- Check network connectivity
- Try manual upload from UI

### Duplicate Upload Blocked
- Check "Allow Duplicates" setting for that video
- Or manually enable duplicates and retry

### UI Not Refreshing
- Auto-refresh runs every 5 seconds
- Click "🔄 Refresh" button for immediate update
- Check database file isn't locked

## Technical Notes

- Database: SQLite with WAL mode for concurrent access
- UI Framework: PySide6 (Qt6)
- Browser Automation: Playwright with Brave
- Logging: Python logging + structured JSON
- Retry Strategy: Exponential backoff (implicit via count)
- Status Transitions: Linear state machine (PENDING → IN_PROGRESS → SUCCESS/FAILED)
