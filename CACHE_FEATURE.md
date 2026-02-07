# Pipeline Caching & Resume Feature

## Overview

The pipeline now supports **automatic caching and resumption** of interrupted runs. If the same video is processed again, or if the pipeline is interrupted, it will automatically resume from the last completed stage instead of starting over.

## How It Works

### Video Identification

Each video is identified by a hash of its absolute path and file size. This allows the system to:
- Detect when the same video is being processed again
- Resume from the last completed stage
- Skip expensive operations (transcription, AI scoring)

### Cached Stages

The following stages are cached:

1. **Audio Extraction** - Saves extracted audio file path
2. **Transcription** - Saves transcript file path and segment count
3. **Segmentation** - Saves all candidate segments
4. **AI Scoring** - Saves all scored segments (most expensive to recompute!)

### Cache Storage

Cache files are stored in `output/cache/` with the following structure:

```
output/
├── cache/
│   └── {video_hash}.json
├── work/
│   ├── audio.wav
│   └── transcript.json
└── clips/
    └── ...
```

Each cache file contains:
```json
{
  "last_stage": "ai_scoring",
  "last_updated": "2024-02-07T02:30:45.123456",
  "video_path": "/absolute/path/to/video.mp4",
  "audio_extraction": {
    "completed": true,
    "audio_path": "output/work/audio.wav"
  },
  "transcription": {
    "completed": true,
    "transcript_path": "output/work/transcript.json",
    "segment_count": 145
  },
  "segmentation": {
    "completed": true,
    "candidates": [...],
    "sentence_count": 89,
    "pause_count": 56
  },
  "ai_scoring": {
    "completed": true,
    "scored_segments": [...],
    "high_quality_count": 12
  }
}
```

## Usage

### Default Behavior (Cache Enabled)

```bash
# First run - processes everything
python main.py video.mp4

# Second run - resumes from cache
python main.py video.mp4
```

Example output when resuming:
```
============================================================
CHECKING FOR CACHED STATE
============================================================
✓ Found cached state from 2024-02-07T02:30:45.123456
✓ Last completed stage: ai_scoring
✓ Will resume from last completed stage
  (Use --no-cache to force full reprocessing)

============================================================
STAGE 1: AUDIO EXTRACTION
============================================================
✓ SKIPPED (using cached result): output/work/audio.wav

============================================================
STAGE 2: TRANSCRIPT GENERATION
============================================================
✓ SKIPPED (using cached result): output/work/transcript.json

============================================================
STAGE 4: CANDIDATE SEGMENT BUILDING
============================================================
✓ SKIPPED (using cached result): 145 candidates

============================================================
STAGE 5: AI HIGHLIGHT SCORING
============================================================
✓ SKIPPED (using cached result): 145 scored segments
[OK] High-quality segments (score >= 6.0): 12
```

### Force Reprocessing (Disable Cache)

```bash
# Disable cache and force full pipeline
python main.py video.mp4 --no-cache
```

### When Cache is Used

✅ **Cache IS used when:**
- Same video file is processed again
- Pipeline is interrupted and restarted
- Testing different configurations (metadata, uploads, etc.)

❌ **Cache is NOT used when:**
- `--no-cache` flag is specified
- Video file is modified (size changes)
- Cache file is manually deleted
- Different video file is processed

## Benefits

### Time Savings

Typical time savings when resuming:

| Stage | Original Time | Cached Time | Savings |
|-------|--------------|-------------|---------|
| Audio Extraction | ~5-10s | <1s | 90%+ |
| Transcription | ~30-120s | <1s | 99%+ |
| Segmentation | ~2-5s | <1s | 80%+ |
| AI Scoring | ~60-300s | <1s | 99%+ |

**Total savings: 2-5 minutes for a typical 10-minute video**

### Use Cases

1. **Testing prompt changes** - Modify AI prompt without re-transcribing
2. **Adjusting thresholds** - Change score thresholds without re-scoring
3. **Debugging** - Stop and restart pipeline without losing progress
4. **Batch processing** - Process same video with different settings
5. **Development** - Faster iteration during feature development

## Cache Management

### View Cache Files

```bash
ls -lh output/cache/
```

### Clear Cache for Specific Video

```python
from cache import PipelineCache

cache = PipelineCache()
cache.clear_cache('path/to/video.mp4')
```

### Clear All Caches

```bash
rm -rf output/cache/
```

## Implementation Details

### PipelineCache Class

```python
from cache import PipelineCache

# Initialize
cache = PipelineCache(cache_dir='output/cache')

# Load state
state = cache.load_state('video.mp4')

# Check if stage completed
if cache.has_completed_stage(state, 'transcription'):
    transcript_path = cache.get_stage_result(state, 'transcription', 'transcript_path')

# Save state after completing a stage
pipeline_state['transcription'] = {
    'completed': True,
    'transcript_path': 'output/work/transcript.json'
}
cache.save_state('video.mp4', pipeline_state, 'transcription')
```

### Video Hash Function

```python
from cache import get_video_hash

# Get unique identifier for video
video_hash = get_video_hash('path/to/video.mp4')
# Returns: 'a1b2c3d4e5f6...'
```

## Safety & Validation

### File Existence Checks

The cache system verifies that cached files still exist:

```python
if cache.has_completed_stage(state, 'audio_extraction'):
    audio_path = cache.get_stage_result(state, 'audio_extraction', 'audio_path')
    
    # Verify file still exists
    if not os.path.exists(audio_path):
        logger.warning("Cached audio file not found, re-extracting...")
        cache_hit = False
```

### Cache Invalidation

Cache is automatically invalidated when:
- Video file size changes
- Video file path changes
- Cache file is corrupted

## Best Practices

### During Development

1. Use cache by default for faster iteration
2. Use `--no-cache` when testing changes to early stages
3. Clear cache when changing transcription model

### In Production

1. Enable cache for batch processing
2. Implement periodic cache cleanup (e.g., delete >7 days old)
3. Monitor cache directory size

### Troubleshooting

**Problem:** Pipeline uses old results after code changes

**Solution:** Use `--no-cache` or clear cache:
```bash
rm -rf output/cache/
```

**Problem:** Cache files getting too large

**Solution:** Cache only essential data, not full results
```python
# Good - cache only paths
'audio_path': 'output/work/audio.wav'

# Bad - cache large binary data
'audio_data': b'\x00\x01\x02...'  # Don't do this!
```

## Future Enhancements

Potential improvements:
- [ ] Cache expiration (auto-delete old caches)
- [ ] Selective cache clearing by stage
- [ ] Cache compression for large states
- [ ] Distributed caching for multi-machine pipelines
- [ ] Cache warmup for batch processing
