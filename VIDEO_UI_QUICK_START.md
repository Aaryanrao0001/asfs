# Video Management UI - Quick Start Guide

## 🎯 What's New

The Videos tab has been completely redesigned with an ultra-modern, Uber-style interface. Here's everything you need to know to use it effectively.

## 🖼️ UI Layout Overview

```
┌─────────────────────────────────────────────────────────────┐
│  Video Library                            0 videos           │
├─────────────────────────────────────────────────────────────┤
│  🔍 Search videos by name...     [Sort by: Title (A-Z) ▼]  │
├─────────────────────────────────────────────────────────────┤
│  [➕ Add Videos] [🗑️ Delete Selected] [🔄 Refresh]          │
│                                    [⬆️ Upload All Pending]   │
├─────────────────────────────────────────────────────────────┤
│  ⚙️ Bulk Upload Settings                                     │
│  Delay between uploads: [60 ▼] seconds                      │
├─────────────────────────────────────────────────────────────┤
│  📹 Your Videos                                              │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Title  │ Duration │ Size │ 📷 │ 🎵 │ ▶️ │ Dup │ Actions││
│  ├───────────────────────────────────────────────────────┤ │
│  │ video1 │ 1:23     │ 5.2M │ ✅ │ ⚪ │ ⚪ │ ☐   │ [Btns] ││
│  │ video2 │ 0:45     │ 2.1M │ ⚪ │ ⚪ │ ⚪ │ ☑   │ [Btns] ││
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 📖 Feature Guide

### 1. Adding Videos

**How to:**
1. Click "➕ Add Videos" button (top left)
2. Select one or more video files
3. Videos are automatically added to the registry

**What happens:**
- Duration is extracted using FFmpeg
- File path is stored
- Title is set to filename (editable later)
- Toast notification shows how many were added

**Supported formats:** MP4, MOV, AVI, MKV, WEBM

---

### 2. Searching Videos

**How to:**
1. Type in the search box at the top
2. Results filter instantly as you type
3. Clear the box to see all videos

**Features:**
- Case-insensitive search
- Searches video titles
- Instant results (no lag)
- Works with any text

**Example:** Type "tutorial" to find all tutorial videos

---

### 3. Sorting Videos

**How to:**
1. Click the "Sort by" dropdown
2. Select your preferred sorting option

**Available sorts:**
- **Title (A-Z)**: Alphabetical order
- **Title (Z-A)**: Reverse alphabetical
- **Duration (Short)**: Shortest first
- **Duration (Long)**: Longest first
- **Date Added (Newest)**: Most recent first
- **Date Added (Oldest)**: Oldest first

---

### 4. Viewing Video Details

**How to:**
1. Find the video in the table
2. Click the "ℹ️" button in the Actions column
3. Review all information
4. Click "Close" when done

**Information shown:**
- Video ID
- Complete file path
- Duration (formatted and raw)
- File size (human-readable)
- Date added to registry
- Duplicate upload setting
- Upload status for each platform
- Post IDs (for successful uploads)
- Error messages (for failed uploads)

---

### 5. Editing Video Title

**How to:**
1. Click the "✏️" button next to the video
2. Enter new title in the dialog
3. Click "OK" to save

**Features:**
- Simple, focused dialog
- Current title is pre-selected
- Real-time table update
- Toast notification confirms success

**Tip:** Use descriptive titles to make searching easier!

---

### 6. Deleting Videos

#### Single Video Deletion
**How to:**
1. Click the "🗑️" button in the Actions column
2. Confirm deletion in dialog
3. Video is removed from registry

#### Bulk Deletion
**How to:**
1. Select multiple videos by clicking their rows
   - Click = select one
   - Ctrl+Click = select multiple
   - Shift+Click = select range
2. Click "🗑️ Delete Selected" at the top
3. Confirm deletion
4. All selected videos are removed

**Important:** 
- Only removes database records
- Actual video files remain on disk
- Upload history is deleted
- Requires confirmation

---

### 7. Uploading Videos

#### Single Upload
**How to:**
1. Click platform button in Actions column:
   - 📷 for Instagram
   - 🎵 for TikTok
   - ▶️ for YouTube
2. Confirm upload
3. Wait for completion

#### Bulk Upload
**How to:**
1. Go to Upload tab and select platforms
2. Return to Videos tab
3. Click "⬆️ Upload All Pending"
4. Set delay between uploads if needed
5. Confirm bulk upload
6. Watch status indicators update

**Status Indicators:**
- ✅ Successfully uploaded
- ❌ Failed to upload
- ⏳ Upload in progress
- 🚫 Upload blocked
- 🔄 Rate limited
- ⚪ Not uploaded yet

**Tip:** Hover over status icons for detailed information!

---

### 8. Managing Duplicate Uploads

**How to:**
1. Find the "Allow Duplicates" column
2. Check/uncheck the box for each video
3. Changes save automatically

**What it does:**
- **Checked**: Allows re-uploading to same platform
- **Unchecked**: Blocks duplicate uploads

**Use case:** Enable for videos you want to re-post periodically

---

## 💡 Pro Tips

### Efficient Workflow
1. **Add all videos first** using bulk add
2. **Edit titles** to be descriptive and searchable
3. **Use search** to find videos quickly
4. **Sort by duration** to find short/long videos
5. **Check status** before uploading again

### Keyboard Shortcuts
- **Ctrl+Click**: Select multiple videos
- **Shift+Click**: Select range of videos
- **Ctrl+A**: Select all visible videos
- **Delete**: (when selection exists) triggers delete dialog

### Organization
- Use descriptive titles (e.g., "Tutorial - Python Basics - Part 1")
- Enable duplicates only when needed
- Regularly delete old videos from registry
- Use search to create "virtual folders" (search "tutorial", "demo", etc.)

### Upload Strategy
- Set appropriate delays (60s recommended)
- Check status indicators before re-uploading
- Enable duplicates for periodic content
- Use bulk upload for efficiency

## 🎨 Understanding the UI

### Colors & Indicators

**Status Colors:**
- 🟢 Green: Success
- 🔴 Red: Error/Failed
- 🟠 Orange: Warning
- 🔵 Blue: Info
- ⚪ Gray: Neutral/Not started

**Button Types:**
- **Blue gradient**: Primary actions (Add, Upload)
- **Dark gray**: Secondary actions (Refresh)
- **Red gradient**: Destructive actions (Delete)

### Toast Notifications

Appear at the top of the screen for 3 seconds:
- ✅ **Success**: Operation completed successfully
- ❌ **Error**: Operation failed
- ⚠️ **Warning**: Operation partially completed
- ℹ️ **Info**: Additional information

### Table Features

**Multi-select:**
- Click row to select
- Ctrl+Click for multiple
- Shift+Click for range

**Columns:**
1. **Title**: Video name (editable)
2. **Duration**: Video length (MM:SS)
3. **Size**: File size (KB/MB/GB)
4. **📷**: Instagram status
5. **🎵**: TikTok status
6. **▶️**: YouTube status
7. **Allow Duplicates**: Checkbox
8. **Actions**: Quick action buttons
9. **File Path**: Full path to file

**Hover Effects:**
- Rows highlight on hover
- Status icons show tooltips
- Action buttons animate

## 🔍 Troubleshooting

### Videos Not Appearing
**Solution:**
- Click "🔄 Refresh" button
- Check if files exist at their paths
- Verify database is accessible

### Search Not Working
**Solution:**
- Clear search box and try again
- Ensure videos have titles
- Check for typos

### Delete Button Disabled
**Solution:**
- Select at least one video (click the row)
- Look for row highlighting
- Try clicking the row again

### Upload Blocked
**Solution:**
1. Check if "Allow Duplicates" is enabled
2. View video details to see error
3. Enable duplicates if you want to re-upload

### Notifications Not Showing
**Solution:**
- Ensure Videos tab is active
- Wait 3 seconds (they auto-dismiss)
- Check top of the tab area

## 📊 Statistics

**Current Status:**
- Video count updates in real-time
- Shows filtered count when searching
- Properly pluralized ("1 video" vs "2 videos")

**File Sizes:**
- Automatically formatted (KB, MB, GB, etc.)
- Shows "N/A" if file not found
- Calculated on-demand (not cached)

## 🎓 Learning Path

**Beginner:**
1. Add a few videos
2. Try searching and sorting
3. Edit a video title
4. View video details

**Intermediate:**
5. Delete a single video
6. Select multiple videos
7. Bulk delete videos
8. Upload to one platform

**Advanced:**
9. Configure bulk upload delays
10. Manage duplicate settings
11. Monitor upload status
12. Use keyboard shortcuts

## 📞 Need Help?

**Resources:**
- Full documentation: `VIDEO_MANAGEMENT_UI.md`
- Before/after comparison: `VIDEO_UI_IMPROVEMENTS.md`
- Implementation details: `IMPLEMENTATION_COMPLETE_VIDEO_UI.md`

**Common Questions:**

**Q: Does deleting remove the actual file?**
A: No, only removes from database. Files stay on disk.

**Q: Can I undo a deletion?**
A: No, but you can re-add the video from disk.

**Q: Why can't I upload again?**
A: Enable "Allow Duplicates" for that video.

**Q: How do I bulk edit titles?**
A: Not available yet - edit individually for now.

**Q: Can I see video thumbnails?**
A: Not yet - planned for future version.

---

## 🚀 Quick Reference Card

```
Action              | Button/Method
--------------------|------------------
Add videos          | ➕ Add Videos
Search              | Type in search box
Sort                | Sort by dropdown
View details        | ℹ️ button
Edit title          | ✏️ button
Delete one          | 🗑️ button
Delete multiple     | Select + 🗑️ Delete Selected
Upload Instagram    | 📷 button
Upload TikTok       | 🎵 button
Upload YouTube      | ▶️ button
Upload all          | ⬆️ Upload All Pending
Refresh             | 🔄 Refresh
Multi-select        | Ctrl+Click rows
Range select        | Shift+Click rows
```

---

**Enjoy your new ultra-modern video management interface! 🎉**
