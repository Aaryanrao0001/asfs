# Campaign Management Guide

## Overview

The multi-campaign management system allows you to organize and execute multiple independent video upload campaigns. Each campaign can have its own videos, metadata (captions, hashtags, titles), scheduling, and target platforms.

## Key Features

- **Multiple Independent Campaigns**: Run multiple campaigns simultaneously without interference
- **Randomized Metadata**: Use comma-separated values for captions and titles that are randomly selected per upload
- **Flexible Scheduling**: Configure delays between uploads and schedule campaigns for execution
- **Platform Targeting**: Select different platforms for each campaign (Instagram, TikTok, YouTube)
- **Upload Tracking**: Monitor upload success/failure per campaign with detailed analytics
- **Pause/Resume/Cancel**: Control campaign execution in real-time

## Quick Start

### 1. Create a Campaign

```bash
curl -X POST http://localhost:5000/api/campaigns \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Summer Product Launch",
    "description": "Promotional videos for summer collection",
    "status": "draft"
  }'
```

**Response:**
```json
{
  "success": true,
  "campaign_id": "abc123-def456-ghi789",
  "message": "Campaign \"Summer Product Launch\" created successfully"
}
```

### 2. Add Videos to Campaign

First, make sure your videos are registered in the video registry. Then add them to the campaign:

```bash
curl -X PUT http://localhost:5000/api/campaigns/abc123-def456-ghi789 \
  -H "Content-Type: application/json" \
  -d '{
    "video_ids": ["video_001", "video_002", "video_003"]
  }'
```

### 3. Configure Campaign Metadata

Set up captions, hashtags, and titles for the campaign:

```bash
curl -X PUT http://localhost:5000/api/campaigns/abc123-def456-ghi789 \
  -H "Content-Type: application/json" \
  -d '{
    "metadata": {
      "caption_mode": "randomized",
      "captions": "New summer vibes!, Check out our latest collection!, Summer is here!, Fresh seasonal arrivals!",
      "hashtags": "summer,fashion,newcollection,style,ootd",
      "title_mode": "single",
      "titles": "Summer Collection 2024",
      "add_hashtag_prefix": true
    }
  }'
```

**Metadata Modes:**
- **single**: Use the same caption/title for all uploads
- **randomized**: Pick a random caption/title from comma-separated list for each upload
- **per_video**: Custom metadata per video (future enhancement)

### 4. Configure Campaign Schedule

Set platforms, delays, and scheduling options:

```bash
curl -X PUT http://localhost:5000/api/campaigns/abc123-def456-ghi789 \
  -H "Content-Type: application/json" \
  -d '{
    "schedule": {
      "platforms": ["Instagram", "TikTok"],
      "delay_seconds": 300,
      "auto_schedule": false,
      "upload_gap_hours": 2,
      "upload_gap_minutes": 0
    }
  }'
```

**Schedule Options:**
- `platforms`: Array of platform names (Instagram, TikTok, YouTube)
- `delay_seconds`: Wait time between uploads (0 for immediate succession)
- `auto_schedule`: Enable background auto-scheduler (experimental)
- `upload_gap_hours/minutes`: For auto-scheduler, time between uploads

### 5. Execute Campaign

Start the campaign execution:

```bash
curl -X POST http://localhost:5000/api/campaigns/abc123-def456-ghi789/execute?background=true
```

**Response:**
```json
{
  "success": true,
  "message": "Campaign execution started (background mode)",
  "tasks_created": 6
}
```

### 6. Monitor Campaign Status

Check campaign execution status:

```bash
curl http://localhost:5000/api/campaigns/abc123-def456-ghi789/status
```

**Response:**
```json
{
  "success": true,
  "campaign_status": "active",
  "execution_status": {
    "status": "running",
    "paused": false,
    "start_time": "2024-02-13T12:00:00"
  },
  "is_active": true,
  "upload_stats": {
    "success": 3,
    "failed": 0,
    "pending": 3
  }
}
```

### 7. View Campaign Analytics

Get detailed analytics:

```bash
curl http://localhost:5000/api/campaigns/abc123-def456-ghi789/analytics
```

**Response:**
```json
{
  "success": true,
  "analytics": {
    "total_uploads": 6,
    "success_count": 5,
    "failed_count": 1,
    "pending_count": 0,
    "success_rate": 83.33,
    "video_count": 3,
    "platforms": ["Instagram", "TikTok"],
    "created_at": "2024-02-13T11:00:00",
    "updated_at": "2024-02-13T12:30:00"
  }
}
```

## Campaign Control

### Pause Campaign

```bash
curl -X POST http://localhost:5000/api/campaigns/abc123-def456-ghi789/pause
```

The campaign will pause after the current upload completes.

### Resume Campaign

```bash
curl -X POST http://localhost:5000/api/campaigns/abc123-def456-ghi789/resume
```

### Cancel Campaign

```bash
curl -X POST http://localhost:5000/api/campaigns/abc123-def456-ghi789/cancel
```

Campaign will stop after current upload and remaining uploads will be marked as cancelled.

## List All Campaigns

### All Campaigns

```bash
curl http://localhost:5000/api/campaigns
```

### Filter by Status

```bash
curl http://localhost:5000/api/campaigns?status=active
```

**Available statuses:** draft, scheduled, active, paused, completed

## Complete Example Workflow

Here's a complete example using Python:

```python
import requests

BASE_URL = "http://localhost:5000/api"

# 1. Create campaign
response = requests.post(f"{BASE_URL}/campaigns", json={
    "name": "Tutorial Series Q1 2024",
    "description": "Educational video series for Q1",
    "status": "draft"
})
campaign_id = response.json()["campaign_id"]
print(f"Created campaign: {campaign_id}")

# 2. Add videos (assuming videos are already registered)
video_ids = ["tutorial_01", "tutorial_02", "tutorial_03", "tutorial_04", "tutorial_05"]
requests.put(f"{BASE_URL}/campaigns/{campaign_id}", json={
    "video_ids": video_ids
})

# 3. Configure metadata
requests.put(f"{BASE_URL}/campaigns/{campaign_id}", json={
    "metadata": {
        "caption_mode": "randomized",
        "captions": "Learn the secrets!, Master this technique!, Pro tips inside!, Unlock your potential!",
        "hashtags": "tutorial,howto,learn,tips,education",
        "title_mode": "randomized",
        "titles": "Quick Tutorial, Essential Guide, Must-Know Tips, Pro Techniques",
        "add_hashtag_prefix": True
    }
})

# 4. Configure schedule
requests.put(f"{BASE_URL}/campaigns/{campaign_id}", json={
    "schedule": {
        "platforms": ["YouTube", "Instagram"],
        "delay_seconds": 600,  # 10 minutes between uploads
        "auto_schedule": False
    }
})

# 5. Start campaign
response = requests.post(f"{BASE_URL}/campaigns/{campaign_id}/execute?background=true")
print(f"Campaign started: {response.json()}")

# 6. Monitor progress
import time
while True:
    response = requests.get(f"{BASE_URL}/campaigns/{campaign_id}/status")
    status = response.json()
    
    if not status["is_active"]:
        print("Campaign completed!")
        break
    
    stats = status["upload_stats"]
    print(f"Progress: {stats.get('success', 0)} success, {stats.get('failed', 0)} failed, {stats.get('pending', 0)} pending")
    time.sleep(30)

# 7. View final analytics
response = requests.get(f"{BASE_URL}/campaigns/{campaign_id}/analytics")
analytics = response.json()["analytics"]
print(f"Final Results: {analytics['success_rate']}% success rate")
print(f"  Success: {analytics['success_count']}")
print(f"  Failed: {analytics['failed_count']}")
```

## Use Cases

### Use Case 1: Product Launch Campaign

**Scenario:** Launch 10 product showcase videos across Instagram and TikTok with varied captions

```json
{
  "name": "Spring Product Launch",
  "metadata": {
    "caption_mode": "randomized",
    "captions": "New arrivals!, Spring collection drop!, Fresh styles just landed!, Must-have pieces!",
    "hashtags": "spring,fashion,newcollection,style,ootd,shopping",
    "title_mode": "single",
    "titles": "Spring 2024 Collection",
    "add_hashtag_prefix": true
  },
  "schedule": {
    "platforms": ["Instagram", "TikTok"],
    "delay_seconds": 7200
  }
}
```

**Result:** 10 videos × 2 platforms = 20 uploads with varied captions to avoid repetition

### Use Case 2: Tutorial Series

**Scenario:** 5 educational videos to YouTube with consistent branding

```json
{
  "name": "Beginner Photography Tutorial Series",
  "metadata": {
    "caption_mode": "single",
    "captions": "Master the fundamentals of photography with our comprehensive tutorial series. Perfect for beginners!",
    "hashtags": "photography,tutorial,learn,beginner,camera,tips",
    "title_mode": "randomized",
    "titles": "Photography 101: Basics, Camera Settings Explained, Composition Techniques, Lighting Fundamentals, Editing Basics",
    "add_hashtag_prefix": true
  },
  "schedule": {
    "platforms": ["YouTube"],
    "delay_seconds": 1800
  }
}
```

**Result:** Organized series with unique titles but consistent description

### Use Case 3: Parallel Campaigns

**Scenario:** Run two separate campaigns simultaneously without interference

**Campaign 1 - Morning Motivation:**
- 5 motivational videos
- Instagram only
- Upload every morning at 9 AM (via scheduled_start)
- Randomized inspirational captions

**Campaign 2 - Tech Reviews:**
- 10 product review videos
- YouTube + TikTok
- Upload every 6 hours
- Product-specific metadata

Both campaigns run independently - delays in Campaign 1 don't affect Campaign 2.

## Advanced Configuration

### Hashtag Formatting

The `add_hashtag_prefix` option automatically adds `#` to hashtags:

```json
{
  "hashtags": "viral,trending,amazing",
  "add_hashtag_prefix": true
}
```

**Result:** `#viral #trending #amazing`

If hashtags already have `#`, they won't be duplicated:

```json
{
  "hashtags": "#viral,trending,#amazing",
  "add_hashtag_prefix": true
}
```

**Result:** `#viral #trending #amazing`

### Randomized Metadata

Randomized mode picks a random item for each upload:

```json
{
  "caption_mode": "randomized",
  "captions": "Option A, Option B, Option C, Option D"
}
```

For 5 uploads, you might get: B, A, D, A, C (random selection with replacement)

### Upload Delays

Configure delays to avoid rate limiting and appear more natural:

- **0 seconds**: Upload as fast as possible (not recommended)
- **300 seconds (5 min)**: Quick succession for bulk uploads
- **1800 seconds (30 min)**: Moderate pacing
- **3600 seconds (1 hour)**: Slow, steady uploads
- **7200 seconds (2 hours)**: Maximum spacing for daily campaigns

## Campaign Independence

Key features ensuring campaigns don't interfere:

1. **Separate Metadata**: Each campaign has its own captions, hashtags, titles
2. **Independent Execution**: Campaigns run in separate threads
3. **Isolated Scheduling**: Campaign A's delays don't affect Campaign B
4. **Individual Control**: Pause/resume one campaign without affecting others
5. **Separate Tracking**: Upload success/failure tracked per campaign

## Database Structure

The campaign system uses 5 SQLite tables:

1. **campaigns**: Campaign metadata (name, description, status)
2. **campaign_videos**: Many-to-many relationship (campaign ↔ videos)
3. **campaign_metadata**: Metadata configuration per campaign
4. **campaign_schedules**: Scheduling configuration per campaign
5. **campaign_uploads**: Upload tracking per campaign

All tables use CASCADE delete - deleting a campaign removes all associated data.

## Backward Compatibility

The campaign system is fully backward compatible:

- **Existing uploads** continue to work through the Videos tab
- **Single video uploads** work as before (non-campaign uploads)
- **Video registry** is shared (campaigns reference existing videos)
- **Uploader modules** unchanged (brave_instagram, brave_tiktok, brave_youtube)
- **Rate limiting** still applies globally per platform

Campaigns are an organizational layer on top of the existing system.

## Troubleshooting

### Campaign Not Starting

**Problem:** Campaign execution returns success but doesn't start

**Solutions:**
1. Verify videos are registered in video registry: `GET /api/videos`
2. Check campaign has metadata configured: `GET /api/campaigns/{id}`
3. Check campaign has schedule configured with at least one platform
4. Ensure browser credentials are configured (BRAVE_PATH, etc.)

### Uploads Failing

**Problem:** All uploads in campaign fail

**Solutions:**
1. Check individual upload errors in campaign analytics
2. Verify browser automation is working (test single upload first)
3. Check platform credentials (logged into Instagram/TikTok/YouTube)
4. Review upload logs for specific error messages

### Randomization Not Working

**Problem:** Same caption used for all uploads

**Solutions:**
1. Verify `caption_mode` is set to "randomized", not "single"
2. Check captions are comma-separated: "Caption A, Caption B, Caption C"
3. Ensure whitespace around commas is preserved (automatically trimmed)

### Campaign Stuck in "Active" Status

**Problem:** Campaign shows active but not progressing

**Solutions:**
1. Check execution status: `GET /api/campaigns/{id}/status`
2. Campaign may be paused - try resume: `POST /api/campaigns/{id}/resume`
3. Check for errors in backend logs
4. Cancel and restart if necessary

## Best Practices

1. **Test with Small Campaigns**: Start with 2-3 videos to verify setup
2. **Use Meaningful Names**: Clear campaign names help with organization
3. **Vary Your Metadata**: Use randomized captions to avoid repetition
4. **Respect Rate Limits**: Use appropriate delays (5-30 minutes minimum)
5. **Monitor Progress**: Check status regularly during execution
6. **Plan for Failures**: Some uploads may fail - have retry strategy
7. **Platform-Specific Content**: Create separate campaigns for different platforms when content varies
8. **Clean Up Completed Campaigns**: Delete old campaigns to keep database tidy

## API Reference

See the complete API documentation:

### Endpoints

- `POST /api/campaigns` - Create campaign
- `GET /api/campaigns` - List campaigns
- `GET /api/campaigns/{id}` - Get campaign details
- `PUT /api/campaigns/{id}` - Update campaign
- `DELETE /api/campaigns/{id}` - Delete campaign
- `POST /api/campaigns/{id}/execute` - Start campaign
- `POST /api/campaigns/{id}/pause` - Pause campaign
- `POST /api/campaigns/{id}/resume` - Resume campaign
- `POST /api/campaigns/{id}/cancel` - Cancel campaign
- `GET /api/campaigns/{id}/status` - Get status
- `GET /api/campaigns/{id}/analytics` - Get analytics

### Status Codes

- `200 OK` - Request successful
- `400 Bad Request` - Invalid request (e.g., campaign not active)
- `404 Not Found` - Campaign doesn't exist
- `500 Internal Server Error` - Server error

## Future Enhancements

Potential improvements for future versions:

1. **Per-Video Metadata**: Custom caption/title for each video in campaign
2. **Scheduled Start Times**: Set exact date/time for campaign to start
3. **Campaign Templates**: Save and reuse campaign configurations
4. **Bulk Import**: Import video lists and metadata from CSV
5. **Webhook Notifications**: Get notified when campaign completes
6. **Retry Failed Uploads**: Automatically retry failed uploads
7. **Campaign Cloning**: Duplicate existing campaign with modifications
8. **Platform-Specific Metadata**: Different captions for different platforms

## Support

For issues or questions:
1. Check this guide first
2. Review backend logs for errors
3. Test with single video upload to isolate issues
4. Verify browser automation is configured correctly
5. Open an issue on GitHub with logs and campaign configuration

---

**Last Updated:** February 13, 2024
**Version:** 1.0.0
