# NEW FEATURES GUIDE

This document describes the new features added to ASFS for enhanced video management and upload capabilities.

## 1. Videos Tab - Multi-Video Import & Management

### Overview
The Videos tab provides a centralized interface for managing videos from any source, not just pipeline-generated clips. You can import ready-to-share videos and upload them to all platforms with full metadata and preprocessing support.

### Features

#### Add Videos from Any Folder
- Click **"➕ Add Videos"** button
- Multi-select videos from any directory on your system
- Supported formats: MP4, MOV, AVI, MKV, WebM
- Videos are automatically registered in the database with duration detection

#### Video Registry Table
Displays all registered videos with:
- **Title**: Video name (filename by default)
- **Duration**: Video length in seconds
- **Platform Status Icons**:
  - ✔ (Checkmark): Successfully uploaded
  - ✖ (X mark): Failed upload
  - ⏳ (Hourglass): Upload in progress
  - ⚪ (Empty): Not uploaded yet
  - 🔁 (Loop): Rate limited, will retry
- **Allow Duplicates**: Toggle to allow re-uploading to same platform
- **Actions**: One-click upload buttons for Instagram (📷), TikTok (🎵), YouTube (▶)
- **File Path**: Full path to video file

#### Upload Features
- **Single Upload**: Click platform button to upload one video
- **Bulk Upload**: "⬆ Upload All Pending" uploads all videos to all platforms
- **Duplicate Protection**: Prevents accidental re-uploads unless explicitly allowed
- **Auto-Refresh**: Table refreshes every 5 seconds to show latest status

### Usage Example

1. Click "➕ Add Videos" in Videos tab
2. Select multiple ready-to-share videos (hold Ctrl/Cmd to multi-select)
3. Videos appear in the table with their details
4. Configure metadata in Tab 3 (captions, hook phrases, logo)
5. Click platform icons to upload, or use "Upload All Pending"
6. Watch status icons update as uploads complete

---

## 2. Custom Captions with Random Selection

### Overview
Add multiple caption options and let the system randomly select one for each upload, creating varied content from the same videos.

### Configuration

In **Tab 3: Metadata Settings**:

1. **Mode Selection**:
   - **Uniform**: Use the same caption for all uploads
   - **Randomized**: Randomly select from comma-separated options

2. **Caption Input**:
   - Single mode: Enter one caption
   - Randomized mode: Enter multiple captions separated by commas

### Example

**Uniform Mode**:
```
Caption: "Check out this amazing moment! 🔥"
```
Result: All uploads use this exact caption.

**Randomized Mode**:
```
Caption: "This is insane!, Wait for the ending, You won't believe this, Absolutely wild"
```
Result: Each upload randomly selects one of the four captions.

### Benefits
- **Content Variation**: Avoid repetitive captions across uploads
- **A/B Testing**: Test different caption styles naturally
- **Platform Optimization**: Different captions for different audiences
- **Engagement Boost**: Fresh captions keep content feeling unique

---

## 3. Hook Phrase Overlay for Reels/Shorts

### Overview
Add attention-grabbing text overlays to your videos to boost engagement. Hook phrases appear at strategic positions (not center) to catch viewers' attention in the first few seconds.

### Configuration

In **Tab 3: Metadata Settings** → **Hook Phrase (Video Overlay)**:

1. **Hook Phrase Input**:
   - Enter your attention-grabbing text
   - Examples: "Wait for it...", "This is insane!", "You need to see this"

2. **Position Selection**:
   - **Top Left**: Classic position, doesn't block main content
   - **Top Right**: Alternative to avoid UI elements
   - **Bottom Left**: Good for vertical videos
   - **Bottom Right**: Popular for shorts
   - **Top Center**: Maximum visibility

### Technical Details

- **Font**: DejaVu Sans Bold (or system default)
- **Size**: 48px (optimized for mobile viewing)
- **Color**: White text with 3px black border/shadow
- **Placement**: Positioned with margins (40px horizontal, 80px vertical)
- **Format**: Applied using FFmpeg drawtext filter during preprocessing

### Usage Example

1. Go to Tab 3: Metadata Settings
2. Enter hook phrase: `"Wait for it... 😱"`
3. Select position: "Top Left"
4. Add videos to Videos tab or run pipeline
5. Videos are automatically preprocessed with the text overlay before upload

### Best Practices

- **Keep it short**: 3-5 words maximum
- **Use emojis**: Add visual interest (🔥, 😱, 👀)
- **Create curiosity**: "You won't believe...", "This changes everything..."
- **Position strategically**: Avoid blocking important video content
- **Test different phrases**: Use randomized mode with multiple options

---

## 4. Logo Overlay

### Overview
Brand your videos by automatically adding your logo to the bottom of every video before upload. Supports transparent PNGs for professional-looking overlays.

### Configuration

In **Tab 3: Metadata Settings** → **Logo Overlay**:

1. Click **"Browse..."** button
2. Select your logo image file
3. Supported formats: PNG (recommended), JPG, JPEG, SVG, GIF
4. Logo is automatically placed at bottom center of videos

### Technical Details

- **Position**: Bottom center with 40px margin from bottom
- **Scaling**: Automatically scaled to fit video width
- **Transparency**: PNG alpha channel preserved
- **Format**: Applied using FFmpeg overlay filter during preprocessing
- **Performance**: Minimal impact, processed once before upload

### Logo Requirements

**Recommended Specifications**:
- **Format**: PNG with transparent background
- **Size**: 200-400px wide (height proportional)
- **Aspect Ratio**: Horizontal (wider than tall)
- **Color**: High contrast colors for visibility
- **Style**: Simple, recognizable design

**What to Avoid**:
- Very large files (>5MB) - slower processing
- Low contrast logos - hard to see on video
- Tall/vertical logos - take too much vertical space
- Complex designs - may not be visible at small sizes

### Usage Example

1. Prepare your logo (PNG with transparency recommended)
2. Go to Tab 3: Metadata Settings
3. Click "Browse..." in Logo Overlay section
4. Select your logo file
5. Path appears in field (click "Clear" to remove)
6. Add videos to Videos tab or run pipeline
7. All videos automatically include logo at bottom

### Benefits

- **Consistent Branding**: All uploads include your brand
- **Professionalism**: Polished, branded content
- **Attribution**: Clear source for your videos
- **Cross-Platform**: Works on Instagram, TikTok, YouTube

---

## 5. Auto-Schedule & Background Upload

### Overview
Automatically upload videos at scheduled intervals without manual intervention. The scheduler runs in the background and uploads videos from the registry with configurable time gaps between uploads.

### Configuration

In **Tab 4: Upload Platforms** → **Auto-Schedule & Background Upload**:

1. **Enable Checkbox**: Toggle "Enable Auto-Scheduling"
2. **Time Gap Configuration**:
   - Hours: Set gap between uploads (0-24 hours)
   - Minutes: Fine-tune with additional minutes (0-59)
   - Example: 1 hour 30 minutes = uploads every 90 minutes

3. **Platform Selection**: Check platforms to include in auto-upload
   - Instagram
   - TikTok
   - YouTube Shorts

### How It Works

1. **Background Service**: Scheduler runs as daemon thread
2. **Video Queue**: Scans registry for pending uploads
3. **Platform Rotation**: Uploads to different platforms in sequence
4. **Time Management**: Waits configured gap between uploads
5. **Metadata Application**: Applies current metadata settings to each upload
6. **Preprocessing**: Hook phrases and logos applied automatically
7. **Status Tracking**: Updates registry with success/failure

### Scheduler Logic

```
1. Wait for time gap to elapse since last upload
2. Find next pending upload in registry
3. Apply current metadata settings (captions, hook, logo)
4. Preprocess video if needed
5. Execute upload
6. Update registry status
7. Repeat
```

### Usage Example

**Scenario**: Upload 10 videos across 3 platforms with 1-hour gaps

1. Import 10 videos using Videos tab
2. Configure metadata (captions, hook phrase, logo) in Tab 3
3. In Tab 4:
   - Check "Enable Auto-Scheduling"
   - Set gap: 1 hour, 0 minutes
   - Select all platforms
4. Save settings
5. Scheduler starts automatically
6. Videos upload one at a time, every hour
7. Check Videos tab to monitor progress

### Benefits

- **Automated Posting**: Set it and forget it
- **Consistent Schedule**: Regular uploads for algorithm favor
- **Cross-Platform**: Covers all platforms automatically
- **Rate Limit Friendly**: Respects time gaps to avoid bans
- **24/7 Operation**: Runs continuously in background
- **Smart Queue**: Handles duplicates and failures intelligently

### Important Notes

- **App Must Run**: Scheduler requires app to be running (background operation)
- **Duplicate Settings**: Respects "Allow Duplicates" per video
- **Manual Override**: Can still upload manually anytime
- **Stop/Start**: Disable checkbox to stop, re-enable to restart
- **State Persistence**: Scheduler state is NOT currently persisted across app restarts (future enhancement)

---

## Integration & Workflow

### Complete Workflow Example

**Goal**: Upload 20 branded videos with varied captions to all platforms over 2 days

1. **Prepare Videos**:
   - Go to Videos tab
   - Click "➕ Add Videos"
   - Select 20 ready-to-share videos
   - Videos registered with durations

2. **Configure Branding**:
   - Go to Tab 3: Metadata Settings
   - Upload logo PNG in Logo Overlay section
   - Enter hook phrase: "Don't miss this! 🔥"
   - Select position: "Top Left"

3. **Configure Captions**:
   - Set mode to "Randomized"
   - Enter captions (comma-separated):
     ```
     This is incredible!, Wait for the twist, You need to see this, Absolutely wild, Mind-blowing moment
     ```

4. **Configure Tags**:
   - Enter tags: `viral, trending, amazing, mustwatch`
   - Check "Add # prefix"

5. **Configure Scheduling**:
   - Go to Tab 4: Upload Platforms
   - Select all platforms (Instagram, TikTok, YouTube)
   - Enable "Auto-Scheduling"
   - Set gap: 2 hours, 0 minutes

6. **Start & Monitor**:
   - Settings save automatically
   - Scheduler starts in background
   - Go to Videos tab to watch progress
   - Each upload:
     - Random caption selected
     - Hook phrase overlaid
     - Logo added
     - Uploaded to next platform
   - 20 videos × 3 platforms = 60 uploads
   - At 2-hour intervals = 5 days total

### Best Practices

1. **Test First**: Upload one video manually to verify preprocessing
2. **Check Logs**: Monitor Run tab for any errors
3. **Vary Content**: Use randomized captions and titles
4. **Brand Consistently**: Use same logo and hook style
5. **Respect Platforms**: Don't set gaps too short (< 30 min)
6. **Monitor Status**: Check Videos tab regularly
7. **Adjust Settings**: Can change metadata anytime (applies to future uploads)

---

## Troubleshooting

### Videos Not Uploading
- Check "Allow Duplicates" if video already uploaded
- Verify platform credentials in environment variables
- Check Run tab logs for error messages
- Ensure video files still exist at registered paths

### Hook Phrase Not Appearing
- Verify hook phrase text is entered
- Check FFmpeg is installed and in PATH
- Look for preprocessed videos in `output/preprocessed/`
- Check logs for FFmpeg errors

### Logo Not Appearing
- Verify logo file path is correct and file exists
- Use PNG with transparency for best results
- Check logo file is not corrupted
- Ensure file size is reasonable (< 5MB)

### Scheduler Not Working
- Check "Enable Auto-Scheduling" checkbox is enabled
- Verify at least one platform is selected
- Ensure videos exist in registry
- Check that duplicates are allowed if needed
- Look for scheduler errors in logs

### Preprocessing Takes Long Time
- Normal for first video (FFmpeg initialization)
- Subsequent videos should be faster
- Large logos (>5MB) slow down processing
- Complex hook phrases with special characters may be slower
- Check FFmpeg version supports all filters

---

## Technical Architecture

### Video Preprocessing Pipeline

```
Original Video
    ↓
Check for Hook Phrase
    ↓ (if present)
Apply Text Overlay (FFmpeg drawtext)
    ↓
Check for Logo
    ↓ (if present)
Apply Logo Overlay (FFmpeg overlay filter)
    ↓
Save Preprocessed Video (output/preprocessed/)
    ↓
Upload to Platform
```

### Metadata Resolution

```
UI Settings (Tab 3)
    ↓
MetadataConfig.from_ui_values()
    ↓
resolve_metadata() - Random selection if randomized mode
    ↓
{title, description, caption, tags, hook_phrase, logo_path}
    ↓
Upload Worker receives metadata
    ↓
run_upload_stage() applies preprocessing
```

### Scheduler Architecture

```
Main Window initializes scheduler
    ↓
Scheduler runs in daemon thread
    ↓
Every minute: Check if gap elapsed
    ↓
Find next pending upload
    ↓
Get metadata from UI settings
    ↓
Execute upload via callback
    ↓
Update registry status
    ↓
Wait for gap, repeat
```

---

## API Reference

### VideosTab Methods

```python
def add_videos_from_folder():
    """Multi-select and import videos from any folder."""

def upload_to_platform(video_id: str, platform: str):
    """Upload single video with metadata from parent window."""

def upload_all_pending():
    """Bulk upload all videos to all platforms."""

def set_metadata_callback(callback):
    """Set callback to get metadata from parent window."""
```

### Video Overlay Functions

```python
def apply_video_overlays(
    input_video: str,
    output_video: str,
    hook_phrase: Optional[str] = None,
    hook_position: str = "Top Left",
    logo_path: Optional[str] = None
) -> bool:
    """Apply text and logo overlays to video."""

def preprocess_video_for_upload(
    video_path: str,
    output_dir: str,
    metadata: dict
) -> Optional[str]:
    """Preprocess video before upload."""
```

### Scheduler Methods

```python
scheduler = get_scheduler()
scheduler.configure(upload_gap_hours=1, upload_gap_minutes=30, platforms=["Instagram"])
scheduler.set_upload_callback(callback_function)
scheduler.start()
scheduler.stop()
status = scheduler.get_status()
```

### MetadataConfig

```python
config = MetadataConfig.from_ui_values(
    mode="randomized",
    title_input="Title 1, Title 2, Title 3",
    caption_input="Caption A, Caption B",
    tags_input="tag1, tag2, tag3",
    hook_phrase="Watch this!",
    hook_position="Top Left",
    logo_path="/path/to/logo.png"
)

metadata = resolve_metadata(config)
# Returns: {title, description, caption, tags, hook_phrase, hook_position, logo_path}
```

---

## Future Enhancements

Potential improvements for future versions:

1. **Persistent Scheduler State**: Save/restore scheduler state across app restarts
2. **Specific Upload Times**: Schedule uploads for specific times (e.g., "9 AM daily")
3. **Platform-Specific Gaps**: Different time gaps per platform
4. **Advanced Hook Animations**: Fade in/out effects for text
5. **Multiple Logos**: Different logos for different platforms
6. **Watermark Positioning**: Customizable logo position
7. **Batch Preprocessing**: Preprocess all videos at once
8. **Upload Queue UI**: Visual queue showing upcoming uploads
9. **Analytics Integration**: Track upload performance
10. **Template System**: Save/load metadata templates

---

## Support

For issues or questions:
1. Check this guide first
2. Review logs in Run tab
3. Check `pipeline.log` file
4. Verify FFmpeg installation: `ffmpeg -version`
5. Open GitHub issue with details
