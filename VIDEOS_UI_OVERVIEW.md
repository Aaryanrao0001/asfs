# Videos Tab - UI Overview

## Visual Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│ Video Registry & Upload Management                                  │
│                                                                      │
│ [🔄 Refresh]  [⬆ Upload All Pending]                               │
├─────────────────────────────────────────────────────────────────────┤
│ Videos                                                               │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ Title    │ Duration │ 📷 │ 🎵 │ ▶ │ Duplicates │ Actions │ Path │ │
│ ├──────────┼──────────┼────┼────┼───┼────────────┼─────────┼──────┤ │
│ │ Clip 001 │ 30.5s    │ ✔  │ ⚪ │ ⚪ │ ☑         │ 📷🎵▶  │ /... │ │
│ │ Clip 002 │ 25.0s    │ ✔  │ ✔  │ ⏳ │ ☐         │ 📷🎵▶  │ /... │ │
│ │ Clip 003 │ 28.3s    │ ✖  │ ✔  │ ✔  │ ☐         │ 📷🎵▶  │ /... │ │
│ │ Clip 004 │ 32.1s    │ ❌ │ ⚪ │ ⚪ │ ☑         │ 📷🎵▶  │ /... │ │
│ └──────────┴──────────┴────┴────┴───┴────────────┴─────────┴──────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## Column Descriptions

### 1. Title
- **Display**: Video title from database
- **Default**: Clip ID if no title set
- **Sortable**: Yes
- **Example**: "Clip_001", "Epic Moment", "Gaming Highlight"

### 2. Duration
- **Display**: Video length in seconds
- **Format**: "XX.Xs"
- **Example**: "30.5s", "25.0s"
- **Tooltip**: Full duration with milliseconds

### 3. Platform Columns (📷 Instagram, 🎵 TikTok, ▶ YouTube)

**Status Indicators**:

| Icon | Status | Meaning | Color Hint |
|------|--------|---------|------------|
| ✔ | SUCCESS | Successfully uploaded | Green |
| ✖ | FAILED/FAILED_FINAL | Upload failed | Red |
| ⏳ | IN_PROGRESS | Currently uploading | Yellow |
| ❌ | BLOCKED | Duplicate upload blocked | Red |
| 🔁 | RATE_LIMITED | Rate limit reached | Orange |
| ⚪ | None | Not uploaded yet | Gray |

**Tooltip on Hover**:
```
Status: SUCCESS
Timestamp: 2026-02-11T08:00:00
Post ID: ABC123
Retries: 0
```

### 4. Duplicates Column
- **Display**: Checkbox
- **Checked**: Duplicate uploads allowed
- **Unchecked**: Duplicate uploads blocked (default)
- **Interactive**: Click to toggle
- **Effect**: Immediately updates database

### 5. Actions Column
- **Display**: Three upload buttons
- **Buttons**:
  - 📷 = Upload to Instagram
  - 🎵 = Upload to TikTok
  - ▶ = Upload to YouTube
- **Interactive**: Click to upload
- **Confirmation**: Dialog before upload

### 6. Path Column
- **Display**: Full file path
- **Truncated**: May be truncated in view
- **Tooltip**: Full path on hover
- **Example**: `/home/user/asfs/output/clips/clip_001.mp4`

## User Interactions

### Refresh Button (🔄 Refresh)
```
Click → Immediately refresh table from database
        Show latest upload status
        Update all indicators
```

### Upload All Pending Button (⬆ Upload All Pending)
```
Click → Show confirmation dialog
        "Upload all videos to all platforms where they 
         haven't been uploaded yet?"
        
        [Yes] → Start background bulk upload
                Show progress in status indicators
                Display completion summary
        
        [No]  → Cancel operation
```

### Duplicate Toggle (Checkbox)
```
Unchecked → Click → Checked
                    Enable duplicate uploads for this video
                    Database updated immediately
                    Can now upload multiple times to same platform

Checked   → Click → Unchecked
                    Disable duplicate uploads for this video
                    Database updated immediately
                    Future uploads to same platform will be blocked
```

### Platform Upload Button (📷/🎵/▶)
```
Click → Check if upload allowed
        
        If BLOCKED (duplicate):
            Show dialog:
            "Video already uploaded to [Platform] at [Time]
             
             Do you want to enable duplicate uploads 
             for this video and try again?"
             
             [Yes] → Enable duplicates
                    Show: "Click upload button again to proceed"
            
             [No]  → Cancel
        
        If ALLOWED:
            Show confirmation:
            "Upload video [ID] to [Platform]?"
            
            [Yes] → Start async upload worker
                    Update status to ⏳ (IN_PROGRESS)
                    Show completion notification
                    Update status to ✔ (SUCCESS) or ✖ (FAILED)
            
            [No]  → Cancel
```

## Real-Time Updates

### Auto-Refresh Timer
```
Every 5 seconds:
    ├─ Query database for all videos
    ├─ Update table rows
    ├─ Update status indicators
    └─ Refresh without scrolling table
```

### Upload Completion
```
When upload finishes:
    ├─ Emit signal from worker thread
    ├─ Update database
    ├─ Show notification dialog
    ├─ Refresh table
    └─ Update status indicator
```

## Example Workflows

### Workflow 1: Manual Upload
```
1. User sees video in table with ⚪ status for Instagram
2. User clicks 📷 button
3. Confirmation dialog appears
4. User clicks "Yes"
5. Status changes to ⏳ (IN_PROGRESS)
6. Background worker executes upload
7. Status changes to ✔ (SUCCESS) or ✖ (FAILED)
8. Success/failure notification shown
9. Table refreshes
```

### Workflow 2: Duplicate Upload Attempt
```
1. User sees video with ✔ status for TikTok
2. Duplicate checkbox is unchecked (☐)
3. User clicks 🎵 button
4. Blocking dialog appears:
   "Video already uploaded to TikTok at 2026-02-11T08:00:00
    (Post ID: XYZ789)
    
    Do you want to enable duplicate uploads?"
    
5. User clicks "Yes"
6. Checkbox becomes checked (☑)
7. Message: "Click upload button again to proceed"
8. User clicks 🎵 button again
9. Normal upload flow proceeds
```

### Workflow 3: Bulk Upload
```
1. User has 10 videos, some uploaded, some not
2. User clicks "⬆ Upload All Pending"
3. Confirmation dialog:
   "Upload all videos to all platforms where 
    they haven't been uploaded yet?"
4. User clicks "Yes"
5. Bulk upload worker starts
6. For each video × platform combination:
   - If not uploaded: Status → ⏳ → ✔/✖
   - If already uploaded: Skip
7. Progress visible in real-time (auto-refresh)
8. Completion notification:
   "Uploaded 15 videos successfully
    3 failed"
9. Table shows final status
```

### Workflow 4: Retry After Failure
```
1. Video shows ✖ (FAILED) status for YouTube
2. User clicks ▶ button to retry
3. System checks retry count
   - If < 3: Allow retry
   - If = 3: Status is FAILED_FINAL
4. Retry proceeds normally
5. If successful: ✖ → ✔
6. If failed again: Increment retry count
7. If 3rd failure: ✖ → FAILED_FINAL (no more auto-retries)
8. Manual override still possible
```

## Status Progression Examples

### Successful Upload
```
⚪ (Not uploaded)
  ↓
⏳ (Upload started)
  ↓
✔ (Upload succeeded)
```

### Failed Upload (Retriable)
```
⚪ (Not uploaded)
  ↓
⏳ (Upload started)
  ↓
✖ (Upload failed, retry 1/3)
  ↓ [User retries]
⏳ (Upload started)
  ↓
✔ (Upload succeeded)
```

### Failed Upload (Max Retries)
```
⚪ (Not uploaded)
  ↓
⏳ (Retry 1) → ✖ (Failed)
  ↓
⏳ (Retry 2) → ✖ (Failed)
  ↓
⏳ (Retry 3) → ✖ (FAILED_FINAL)
```

### Duplicate Block
```
✔ (Already uploaded, duplicates disabled)
  ↓ [User tries to upload]
❌ (Blocked by duplicate prevention)
  ↓ [User enables duplicates]
⚪ (Ready for new upload)
  ↓
⏳ → ✔ (New upload succeeds)
```

### Rate Limited
```
⚪ (Ready to upload)
  ↓ [Upload attempted when rate limit active]
🔁 (Rate limited, will retry later)
  ↓ [Rate limit expires]
⏳ (Upload started)
  ↓
✔ (Upload succeeded)
```

## Design Tokens (from styles.py)

The UI uses these design tokens for consistency:

### Colors
- **Background**: `#1e1e1e` (dark)
- **Surface**: `#252525` (slightly lighter)
- **Primary**: `#0e639c` (blue)
- **Success**: `#4ec9b0` (green)
- **Error**: `#f48771` (red)
- **Text**: `#d4d4d4` (light gray)

### Typography
- **Font**: Segoe UI, Arial, sans-serif
- **Heading**: 12pt, bold
- **Body**: 10pt, regular
- **Subheading**: 10pt, bold, gray

### Components
- **Button Hover**: `#1177bb` (lighter blue)
- **Button Pressed**: `#0d5689` (darker blue)
- **Disabled**: `#3e3e3e` (dark gray)

## Accessibility

- **Keyboard Navigation**: Tab through all interactive elements
- **Screen Readers**: All buttons have aria labels
- **Color Blind**: Status icons don't rely solely on color
- **High Contrast**: Meets WCAG AA standards
- **Tooltips**: Provide text alternatives for all icons

## Performance

- **Table Rendering**: Efficient with 100+ videos
- **Auto-Refresh**: Only updates changed rows
- **Worker Threads**: Upload doesn't block UI
- **Database Queries**: Indexed for speed
- **Memory**: Minimal footprint, lazy loading

This UI provides a professional, production-grade interface for video registry and upload management.
