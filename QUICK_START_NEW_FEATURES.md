# Quick Start Guide - New Features

This guide covers the new features added to ASFS for metadata management and bulk uploads.

## 1. Using CSV Metadata for Randomized Content

### Why Use CSV Metadata?

CSV metadata allows you to create variety in your uploads automatically:
- Different titles/captions for each upload
- Better engagement with varied hooks
- A/B test different messaging
- Scale content production without manual intervention

### How to Use

#### Step 1: Create Your CSV File

Create a CSV file with these columns (all optional):
- `title` - Video titles
- `caption` - Video captions (Instagram/TikTok)
- `description` - Video descriptions (YouTube)
- `tags` - Hashtags (comma-separated within cell)

Example (`my_metadata.csv`):
```csv
title,caption,description,tags
This is insane!,Check out this moment 🔥,Amazing video content,viral,trending,awesome
You won't believe this!,Mind = blown 😱,Unbelievable footage,shocking,incredible
Wait for it...,Patience pays off 👀,Best ending ever,suspense,mustwatch
```

**Tip**: See `metadata/example_metadata.csv` for a complete template.

#### Step 2: Configure in UI

1. Open ASFS application
2. Go to **Metadata** tab
3. Set **Mode** to "Randomized"
4. In **Import from CSV** section, click **Browse...**
5. Select your CSV file
6. (Optional) Add extra values in the text fields above
7. The app will merge CSV + UI values for maximum variety

#### Step 3: Upload Videos

Now when you upload videos:
- Each upload gets a **randomly selected** title from your pool
- Each upload gets a **randomly selected** caption from your pool
- Tags are **shuffled** for variety
- No manual intervention needed!

### Tips for Best Results

1. **More is Better**: Create 10-20 variants for maximum variety
2. **A/B Test**: Include different hooks to see what performs best
3. **Emojis Work**: Use emojis in titles/captions for engagement
4. **Platform-Specific**: Tailor your CSV for your target platforms
5. **Update Often**: Refresh your CSV with new trends and hooks

## 2. Bulk Upload with Delays

### Why Use Delays?

Adding delays between uploads helps:
- **Prevent Rate Limiting**: Platforms may block rapid successive uploads
- **Avoid Spam Detection**: Spaced uploads look more natural
- **Better Engagement**: Spread content over time for consistent presence
- **A/B Testing**: Time gaps help isolate performance metrics

### How to Use

#### Step 1: Configure Delay

1. Go to **Videos** tab
2. Find **Bulk Upload Settings** section
3. Set **Delay between uploads** (0-3600 seconds)
   - 60s = 1 minute (default, good for testing)
   - 300s = 5 minutes (recommended for real uploads)
   - 3600s = 1 hour (for maximum spacing)

#### Step 2: Start Bulk Upload

1. Add multiple videos to the registry
2. Click **Upload All Pending**
3. The app will:
   - Upload first video immediately
   - Wait for your configured delay
   - Upload next video
   - Repeat until all done

#### Recommended Delays by Use Case

| Use Case | Delay | Why |
|----------|-------|-----|
| Testing | 60s (1 min) | Quick verification |
| Daily Content | 300s (5 min) | Gentle spacing |
| Scheduled Posts | 1800s (30 min) | Professional spacing |
| Max Safety | 3600s (1 hour) | Maximum rate limit protection |

### Example Workflow

**Scenario**: Upload 10 videos over 1 hour

1. Add 10 videos to registry
2. Set delay to 360 seconds (6 minutes)
3. Click "Upload All Pending"
4. Result: 10 videos uploaded with 6-minute gaps
   - Total time: ~60 minutes
   - Natural, spaced uploads
   - No rate limiting issues

## 3. Handling Missing Dependencies

### What Are Dependencies?

ASFS needs these external tools:
- **FFmpeg**: Video processing and conversion
- **FFprobe**: Video metadata extraction (part of FFmpeg)
- **Playwright**: Browser automation for uploads

### What Happens If Missing?

At startup, ASFS checks for dependencies:

**If All Present**: ✓ App starts normally

**If Missing**: 
- ⚠ Warning dialog shows what's missing
- 📝 Installation instructions in log file
- ✅ App still starts (degraded mode)

### Installing Missing Dependencies

#### FFmpeg & FFprobe

**Windows**:
```powershell
# Using Chocolatey
choco install ffmpeg

# Or download from: https://ffmpeg.org/download.html
```

**macOS**:
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt update
sudo apt install ffmpeg
```

#### Playwright Browsers

After installing Playwright Python package:
```bash
playwright install chromium
```

### Checking Dependencies

After installation, restart ASFS. The warning should disappear if all dependencies are found.

## 4. Complete Example Workflow

Let's put it all together with a real-world example:

### Goal: Upload 5 videos with varied metadata, spaced 5 minutes apart

#### Preparation
1. Create `viral_hooks.csv`:
```csv
title,caption,tags
This changed my life,Life-changing moment 🙌,lifechanging,motivation,viral
You need to see this,Don't skip this! 👀,mustwatch,trending,viral
Wait for the ending,Best ending ever 😱,suspense,amazing,viral
I can't believe this,Mind = blown 🤯,shocking,incredible,viral
This is insane,Absolutely crazy 🔥,insane,wild,viral
```

#### In ASFS
1. **Metadata Tab**:
   - Mode: Randomized
   - Import CSV: Select `viral_hooks.csv`
   - Add extra tags: "awesome,trending"

2. **Videos Tab**:
   - Add 5 videos from folder
   - Set delay: 300 seconds (5 minutes)
   - Click "Upload All Pending"

#### Result
- Video 1 uploads immediately with random title/caption from CSV
- 5 minute wait
- Video 2 uploads with different random metadata
- 5 minute wait
- ... continues for all 5 videos
- Total time: ~20 minutes
- Each video has unique, varied metadata
- Natural spacing prevents rate limits

## Troubleshooting

### CSV Not Loading?
- Check file encoding (must be UTF-8)
- Verify column names: `title`, `caption`, `description`, `tags`
- Look for errors in the log file (`asfs_ui.log`)

### Bulk Upload Not Working?
- Check if videos are in registry (Videos tab)
- Verify platforms are enabled (Upload tab)
- Check for upload blocks (duplicate prevention)

### Dependencies Warning?
- Follow installation instructions in log file
- Restart app after installing dependencies
- Check system PATH includes ffmpeg location

## Best Practices

1. **Start Small**: Test with 2-3 videos first
2. **Monitor Results**: Track which metadata performs best
3. **Update CSV**: Refresh with new hooks regularly
4. **Use Delays**: Always use delays for bulk uploads
5. **Check Logs**: Review `asfs_ui.log` for any issues

## Support

For issues or questions:
1. Check log file: `asfs_ui.log`
2. Review documentation in `metadata/CSV_METADATA_GUIDE.md`
3. Check implementation summary: `IMPLEMENTATION_SUMMARY_METADATA_FIXES.md`

---

**Happy uploading!** 🚀
