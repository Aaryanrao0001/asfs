# Video Management UI - Feature Documentation

## Overview

The Video Management UI has been completely redesigned with an ultra-modern, Uber-style interface that provides comprehensive video library management and upload control.

## Key Features

### 1. Video Deletion
- **Single Video Deletion**: Delete individual videos with a confirmation dialog
- **Bulk Deletion**: Select multiple videos using checkboxes and delete them all at once
- **Safety**: Deletion only removes database records and upload history - actual video files remain on disk
- **Confirmation**: All deletions require user confirmation to prevent accidental data loss

### 2. Video Title Editing
- **Inline Editing**: Click the edit button (✏️) next to any video to open the title editor
- **Simple Dialog**: Clean, focused dialog for editing video titles
- **Real-time Updates**: Changes reflect immediately in the video table
- **Validation**: Prevents empty titles and handles errors gracefully

### 3. Search & Filter
- **Real-time Search**: Search box filters videos as you type
- **Case-insensitive**: Searches work regardless of capitalization
- **Title-based**: Currently searches video titles (extensible to other fields)
- **Live Results**: Table updates instantly as you search

### 4. Advanced Sorting
Six sorting options available via dropdown:
- **Title (A-Z)**: Alphabetical ascending
- **Title (Z-A)**: Alphabetical descending  
- **Duration (Short)**: Shortest videos first
- **Duration (Long)**: Longest videos first
- **Date Added (Newest)**: Most recently added first
- **Date Added (Oldest)**: Oldest videos first

### 5. Video Details View
- **Comprehensive Info**: Click the info button (ℹ️) to view full video details
- **Detailed Display**:
  - Video ID
  - Full file path
  - Duration (formatted as MM:SS and seconds)
  - File size (human-readable format: KB, MB, GB)
  - Date added
  - Duplicate upload settings
  - Upload status for all platforms (Instagram, TikTok, YouTube)
  - Post IDs for successful uploads
  - Error messages for failed uploads

### 6. Toast Notifications
- **Non-intrusive**: Small notifications that appear at the top of the screen
- **Auto-dismiss**: Automatically fade out after 3 seconds
- **Color-coded**: 
  - ✅ Green for success
  - ❌ Red for errors
  - ⚠️ Orange for warnings
  - ℹ️ Blue for info
- **Smooth Animations**: Fade in and fade out transitions
- **Use Cases**:
  - Video added successfully
  - Video deleted
  - Title updated
  - Upload completed
  - Operation errors

### 7. Batch Selection
- **Multi-select**: Select multiple videos using checkboxes in the first column
- **Visual Feedback**: Delete button enables when videos are selected
- **Batch Operations**: Delete multiple videos at once
- **Selection Count**: Shows how many videos are selected

### 8. Enhanced UI Elements

#### Modern Table Design
- **Clean Layout**: No grid lines, alternating row colors
- **Responsive Columns**: Auto-sizing for optimal display
- **Status Indicators**: Visual emojis for upload status
  - ✅ Success
  - ❌ Failed
  - ⏳ In Progress
  - 🚫 Blocked
  - 🔄 Rate Limited
  - ⚪ Not Uploaded
- **Tooltips**: Hover over status icons for detailed information

#### Action Buttons
Each video row has quick action buttons:
- **ℹ️ View Details**: Open detailed info dialog
- **✏️ Edit Title**: Open title editor
- **📷 Instagram**: Upload to Instagram
- **🎵 TikTok**: Upload to TikTok
- **▶️ YouTube**: Upload to YouTube
- **🗑️ Delete**: Remove from registry

#### Statistics Display
- **Video Count**: Real-time count of videos in the library
- **Responsive**: Updates with filtering and searching

### 9. File Size Display
- **Human-readable Format**: Automatically converts bytes to KB, MB, GB, TB
- **Precision**: Shows one decimal place for accuracy
- **Availability**: Checks if file exists before displaying size

### 10. Database Enhancements

New methods added to VideoRegistry:
- `delete_video(video_id)`: Remove video and all upload records
- `update_video_title(video_id, new_title)`: Update video title
- `get_file_size(video_id)`: Get file size in bytes

## UI Design Philosophy

### Uber-Style Modern Design
- **Dark Theme**: Consistent with app's luxury aesthetic
- **Generous Spacing**: 32px padding, 20px gaps between sections
- **Large Touch Targets**: 46px minimum height for buttons
- **Clear Hierarchy**: Headings, subheadings, and body text clearly differentiated
- **Smooth Interactions**: Hover states, transitions, and animations
- **Color Consistency**: Uses app's color palette (blue gradients, status colors)

### Accessibility
- **High Contrast**: White text on dark backgrounds
- **Clear Labels**: All buttons have tooltips
- **Keyboard Navigation**: Full keyboard support
- **Screen Reader Support**: Proper ARIA labels and structure

### Performance
- **Auto-refresh**: Table refreshes every 5 seconds to show upload progress
- **Lazy Loading**: Only loads visible data
- **Efficient Filtering**: Client-side filtering for instant results
- **Minimal Queries**: Optimized database access

## Usage Guide

### Adding Videos
1. Click "➕ Add Videos" button
2. Select one or more video files
3. Videos are registered with automatic metadata extraction
4. Toast notification confirms how many were added

### Searching Videos
1. Type in the search box at the top
2. Results filter instantly as you type
3. Clear the search box to see all videos

### Sorting Videos
1. Click the "Sort by" dropdown
2. Select desired sort option
3. Table reorders immediately

### Editing a Video Title
1. Find the video in the table
2. Click the ✏️ button in the Actions column
3. Enter new title in dialog
4. Click OK to save
5. Toast notification confirms success

### Viewing Video Details
1. Find the video in the table
2. Click the ℹ️ button in the Actions column
3. Review comprehensive video information
4. Click Close to return

### Deleting Videos
**Single Video:**
1. Click the 🗑️ button in the Actions column
2. Confirm deletion in dialog
3. Toast notification confirms success

**Multiple Videos:**
1. Check the boxes for videos you want to delete
2. Click "🗑️ Delete Selected" at the top
3. Confirm deletion in dialog
4. Toast notification shows how many were deleted

### Uploading Videos
1. Select platform using Upload Settings tab
2. Click individual platform buttons (📷🎵▶️) for single uploads
3. Or click "⬆️ Upload All Pending" for bulk uploads
4. Configure delay between uploads if needed

## Technical Details

### Technologies Used
- **PySide6**: Qt framework for Python
- **SQLite**: Video registry database
- **Qt Animations**: Smooth fade effects for notifications
- **Qt Signals/Slots**: Event-driven architecture

### File Structure
```
ui/tabs/videos_tab.py
├── ToastNotification (class)
│   └── Animated notification widget
├── EditTitleDialog (class)
│   └── Simple title editing dialog
├── VideoDetailsDialog (class)
│   └── Comprehensive details view
└── VideosTab (class)
    ├── Video table management
    ├── Search and filtering
    ├── Batch operations
    └── Upload coordination
```

### Database Schema
```sql
videos
├── id (TEXT PRIMARY KEY)
├── file_path (TEXT)
├── title (TEXT)
├── created_at (TEXT)
├── duration (REAL)
├── checksum (TEXT)
└── duplicate_allowed (INTEGER)

video_uploads
├── id (INTEGER PRIMARY KEY)
├── video_id (TEXT, FOREIGN KEY)
├── platform (TEXT)
├── upload_status (TEXT)
├── upload_timestamp (TEXT)
├── platform_post_id (TEXT)
├── error_message (TEXT)
└── retry_count (INTEGER)
```

## Future Enhancements

Potential additions for future versions:
- **Video Thumbnails**: Generate and display preview thumbnails
- **Drag & Drop**: Drag files directly into the interface
- **Export/Import**: Batch export video list or import from CSV
- **Advanced Filters**: Filter by platform, upload status, date range
- **Bulk Edit**: Edit multiple video titles at once
- **Video Preview**: Play videos directly in the app
- **Custom Columns**: User-configurable column display
- **Tags/Categories**: Organize videos with custom tags
- **Upload Queue**: Visual queue of pending uploads with progress
- **Analytics**: View statistics on upload success rates

## Troubleshooting

### Videos Not Showing
- Check if database file exists: `database/videos.db`
- Verify file paths are correct and accessible
- Try refreshing with the 🔄 button

### Search Not Working
- Clear search box and try again
- Ensure videos have titles set
- Check for typos in search term

### Notifications Not Appearing
- Notifications appear at top of the Videos tab
- They auto-dismiss after 3 seconds
- Check if window is in focus

### Delete Button Disabled
- Ensure at least one video is selected via checkbox
- Selection must be in the first column (☑️)

## Best Practices

1. **Regular Backups**: Backup `database/videos.db` periodically
2. **Descriptive Titles**: Use clear, searchable video titles
3. **Organize First**: Add all videos, then organize with search/sort
4. **Bulk Operations**: Use batch selection for efficiency
5. **Check Details**: Review video details before uploading
6. **Monitor Status**: Use status indicators to track upload progress
7. **Clean Up**: Regularly delete old or unwanted videos from registry

## Permissions

The application requires:
- **Read Access**: To video files for duration and size
- **Write Access**: To database for CRUD operations
- **No File Deletion**: Video files are never deleted, only database records

## Support

For issues or questions:
1. Check the logs in `pipeline.log`
2. Review database integrity: `sqlite3 database/videos.db ".tables"`
3. Report bugs with:
   - Steps to reproduce
   - Error messages from logs
   - Screenshot of the issue
   - Video count and system info
