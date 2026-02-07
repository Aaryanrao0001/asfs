# 🎬 Automated Short-Form Content Clipping & Distribution System

A **fully automated, production-ready system** that transforms long-form videos into viral-worthy short clips optimized for TikTok, Instagram Reels, and YouTube Shorts.

## 🎯 Overview

This system intelligently:
- **Analyzes** long-form video content
- **Identifies** high-engagement, viral-potential segments
- **Extracts** platform-optimized short videos
- **Generates** captions and hashtags
- **Schedules** uploads with rate limiting
- **Publishes** to TikTok, Instagram Reels, and YouTube Shorts via official APIs

**This is a real production system** — fully implemented, no placeholders, no mock data.

## 🏗️ Architecture

```
Input Video
    ↓
Audio Extraction (FFmpeg - fast)
    ↓
Transcript + Timestamps (Whisper)
    ↓
Transcript Quality Validation
    ↓
Candidate Segment Builder (Sentence + Pause Windows)
    ↓
AI Highlight Scoring (GitHub Models)
    ↓
Clip Validation & Deduplication
    ↓
FFmpeg Clip Extraction from Original Video + 9:16 Crop
    ↓
Metadata & Caption Generation
    ↓
Queue & Rate-Control Scheduler
    ↓
Official Platform Upload APIs
    ↓
Audit Logs & Retry System
```

## 📁 Project Structure

```
asfs/
├── ingest/              # Video normalization (not used in MVP)
│   ├── __init__.py
│   └── normalize.py     # FFmpeg video standardization
├── transcript/          # Transcription & quality
│   ├── __init__.py
│   ├── transcribe.py    # Faster-Whisper transcription (multi-threaded)
│   ├── audio_extract.py # Fast audio extraction
│   └── quality_check.py # Transcript validation
├── segmenter/           # Candidate segment building
│   ├── __init__.py
│   ├── sentence_window.py  # Sentence-based windowing
│   └── pause_window.py     # Pause-based windowing
├── ai/                  # AI highlight scoring
│   ├── __init__.py
│   ├── scorer.py        # GitHub Models integration
│   └── prompt.txt       # Scoring prompt template
├── cache/               # Pipeline state caching (NEW)
│   ├── __init__.py
│   └── checkpoint.py    # Resume from last completed stage
├── validator/           # Clip validation
│   ├── __init__.py
│   ├── dedup.py         # Semantic deduplication
│   └── overlap.py       # Overlap removal
├── clipper/             # Clip extraction
│   ├── __init__.py
│   └── extract.py       # FFmpeg clip extraction
├── metadata/            # Caption & hashtag generation
│   ├── __init__.py
│   ├── captions.py      # Platform-specific captions
│   └── hashtags.py      # Hashtag strategies
├── scheduler/           # Upload scheduling
│   ├── __init__.py
│   └── queue.py         # Rate limiting & retry logic
├── uploaders/           # Platform upload APIs
│   ├── __init__.py
│   ├── tiktok.py        # TikTok Content Posting API
│   ├── instagram.py     # Instagram Graph API
│   └── youtube.py       # YouTube Data API v3
├── audit/               # Logging & audit trail
│   ├── __init__.py
│   └── logger.py        # SQLite audit logging
├── config/              # Configuration files
│   ├── platforms.json   # Platform specifications
│   ├── rate_limits.json # Upload rate limits
│   └── model.yaml       # AI model configuration
├── main.py              # Main orchestrator
├── requirements.txt     # Python dependencies
├── CACHE_FEATURE.md     # Caching documentation
└── README.md           # This file
```

## 🚀 Quick Start

### Prerequisites

1. **FFmpeg** - Must be installed and available in PATH
   ```bash
   # Ubuntu/Debian
   sudo apt-get install ffmpeg
   
   # macOS
   brew install ffmpeg
   
   # Windows
   # Download from https://ffmpeg.org/download.html
   ```

2. **Python 3.8+**

3. **Windows-specific setup** (if using Windows)
   
   For proper Unicode support in console output:
   ```powershell
   # Option 1: Set UTF-8 for current session
   [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
   
   # Option 2: Set system-wide (requires admin)
   # Control Panel > Region > Administrative > Change system locale...
   # Check "Beta: Use Unicode UTF-8 for worldwide language support"
   ```
   
   **Note:** The system automatically configures UTF-8 encoding for Python's stdout/stderr to prevent encoding errors.

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Aaryanrao0001/asfs.git
   cd asfs
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up API credentials** (see Configuration section)

### Configuration

#### Required Environment Variables

Create a `.env` file or set environment variables:

```bash
# GitHub Models (required for AI scoring)
export GITHUB_TOKEN="your_github_token"

# TikTok (optional - for uploads)
export TIKTOK_ACCESS_TOKEN="your_tiktok_token"

# Instagram (optional - for uploads)
export INSTAGRAM_ACCESS_TOKEN="your_instagram_token"
export INSTAGRAM_USER_ID="your_instagram_user_id"

# YouTube (optional - for uploads)
export YOUTUBE_CREDENTIALS_FILE="path/to/credentials.json"
export YOUTUBE_TOKEN_FILE="path/to/token.json"
```

#### GitHub Models Setup

1. Get a GitHub Personal Access Token from https://github.com/settings/tokens
2. Set `GITHUB_TOKEN` environment variable
3. The system uses GitHub Models (OpenAI-compatible API) for free

#### Local LLM Support (Optional)

The system now supports **local inference** using Ollama with automatic fallback to remote APIs.

**Quick Setup:**
1. Install Ollama: https://ollama.ai/download
2. Pull a supported model: `ollama pull qwen3:latest`
3. Install Python SDK: `pip install ollama`
4. Configure in `config/model.yaml`:
   ```yaml
   llm_backend: "auto"  # auto | local | api
   local_model_name: "qwen3:latest"  # or qwen3:8b, qwen3:14b
   ```

**Backend Modes:**
- `auto` (default): Try local → fallback to API if unavailable
- `local`: Require local → fallback to API with warning if unavailable
- `api`: Use API only, skip local

**Benefits:** No API costs, no rate limits, works offline, faster inference.

**VRAM Requirements & Model Selection:**

| Model | VRAM Required | Performance | Use Case |
|-------|--------------|-------------|----------|
| `qwen3:4b` | 3-4 GB | Fast, good quality | Low-end GPUs, laptops |
| `qwen3:8b` | 6-8 GB | Better quality | Mid-range GPUs |
| `qwen3:14b` | 10-14 GB | Best quality | High-end GPUs |

**CPU-Only Mode (for systems with insufficient VRAM):**
```bash
# Windows PowerShell
$env:OLLAMA_NO_GPU=1
ollama serve

# Linux/macOS
export OLLAMA_NO_GPU=1
ollama serve
```

**Configuration Best Practices:**

Memory Management:
- Set `local_keep_alive: "5m"` in `config/model.yaml` to reduce model reload times
- Use `"10m"` or `"-1"` (indefinite) if processing many videos continuously
- Default is `"5m"` (5 minutes)

GPU Requirements:
- `qwen3:8b` requires ~6GB VRAM
- For GPUs with <6GB VRAM, use CPU mode: `OLLAMA_NO_GPU=1 ollama serve`
- Or use smaller models like `qwen3:4b`

Model Names:
- Use exact names from `ollama list`
- Example: `qwen3:8b` not `qwen3:latest` unless explicitly pulled with that tag
- The system will auto-detect and use the exact available model name

Troubleshooting:
- **Empty responses from Ollama**: The system automatically disables streaming (`stream=False`). If issues persist, check Ollama logs.
- **Model name mismatch (404 errors)**: Run `ollama list` to see exact model names. Update `local_model_name` in `config/model.yaml` to match exactly (e.g., `qwen3:8b` not `qwen3:latest`).
- **Memory allocation errors**: 
  - The system has a circuit breaker that automatically switches to API after 3 consecutive failures
  - Use CPU mode: `OLLAMA_NO_GPU=1` (see above)
  - Try smaller model: `qwen3:4b` instead of `qwen3:8b`
  - Increase system RAM/VRAM
  - Check other GPU-intensive processes
- **Circuit breaker triggered**: After 3 consecutive local failures, the system automatically switches to API mode for remaining segments. Check logs for root cause.
- **Model not found**: Run `ollama list` and update `local_model_name` in config to match exactly
- **Test inference successful but scoring fails**: May indicate memory pressure. The system now uses realistic test prompts to catch this early.
- **Windows Unicode errors**: Should be automatically fixed. If you see encoding errors, ensure UTF-8 is configured (see Windows-specific setup above).

#### Platform API Setup

**TikTok:**
1. Register at https://developers.tiktok.com/
2. Create an app and get OAuth2 credentials
3. Complete OAuth flow to get access token

**Instagram:**
1. Set up Facebook Developer account
2. Create an app with Instagram Graph API permissions
3. Get access token and user ID

**YouTube:**
1. Create project in Google Cloud Console
2. Enable YouTube Data API v3
3. Download OAuth2 credentials JSON
4. First run will open browser for authentication

### Usage

**Basic usage (with caching enabled by default):**
```bash
python main.py /path/to/video.mp4
```

**Custom output directory:**
```bash
python main.py /path/to/video.mp4 -o /path/to/output
```

**Verbose logging:**
```bash
python main.py /path/to/video.mp4 -v
```

**Disable caching (force full reprocessing):**
```bash
python main.py /path/to/video.mp4 --no-cache
```

### 🔄 Pipeline Caching & Resume Feature

The pipeline **automatically caches** intermediate results and can **resume from the last completed stage** if interrupted or if processing the same video again.

**Benefits:**
- ⚡ **2-5 minute time savings** on re-runs
- 🔁 Resume interrupted pipelines
- 🧪 Perfect for testing configuration changes
- 🚀 Faster development iteration

**Cached Stages:**
- Audio Extraction (~10s → <1s)
- Transcription (~60-120s → <1s) 
- Segmentation (~5s → <1s)
- AI Scoring (~60-300s → <1s) ⭐ **Most valuable**

**Example when resuming:**
```
✓ Found cached state from 2024-02-07T02:30:45
✓ Last completed stage: ai_scoring

STAGE 1: AUDIO EXTRACTION
✓ SKIPPED (using cached result)
...
```

**Cache Management:**
```bash
# View cache files
ls -lh output/cache/

# Clear caches
rm -rf output/cache/
```

📖 See [CACHE_FEATURE.md](CACHE_FEATURE.md) for detailed documentation.

## 📊 Pipeline Stages

### 1. Video Normalization
- Normalizes codec to H.264
- Converts to 30fps
- Standardizes audio to AAC 44100Hz stereo
- Preserves original aspect ratio (no cropping)
- Ensures platform compatibility

**Note:** Aspect ratio conversion is deferred to clip extraction stage for better performance.

### 2. Transcript Generation
- Uses Faster-Whisper (4x faster than standard Whisper)
- Multi-threaded CPU inference with CTranslate2
- Voice Activity Detection (VAD) to skip silence
- Generates sentence-level timestamps
- Provides word-level timing data

### 3. Quality Validation
- Checks timestamp continuity
- Validates word density (words/second)
- Detects excessive filler words
- Confirms language confidence

**Pass criteria:** Overall quality score ≥ 0.6

### 4. Candidate Segmentation
- **Sentence windows:** 10-75 second overlapping windows
- **Pause windows:** Natural speech breaks
- Generates 50-200+ candidates per video

### 5. AI Highlight Scoring
- Uses GitHub Models (GPT-4) for analysis
- Evaluates:
  - Hook strength (first 2 seconds)
  - Emotional resonance
  - Clarity and completeness
  - Virality potential
  - Platform fit
- Generates captions and hashtags
- Recommends best platforms

**Threshold:** Only segments scoring ≥ 6.0/10 proceed

### 6. Validation & Deduplication
- **Overlap removal:** Eliminates time-overlapping clips
- **Semantic dedup:** Removes similar content (Jaccard similarity)
- Keeps highest-scoring clips

### 7. Clip Extraction
- FFmpeg-based precise extraction
- Re-encodes for platform compatibility
- Applies vertical format (1080x1920) to selected clips only
- Generates individual MP4 files

**Performance:** By cropping only selected clips (instead of the entire video during normalization), 
processing time is significantly reduced, especially for long videos.

### 8. Metadata Generation
- **Captions:** Platform-specific, with CTAs
- **Hashtags:** Mix of niche + broad tags
- **Filenames:** Structured clip IDs

### 9. Upload Scheduling
- Rate limiting per platform (default: 1/hour)
- Priority-based queue
- Exponential backoff retry logic
- Respects platform quotas

### 10. Platform Uploads
- **TikTok:** Content Posting API
- **Instagram:** Graph API (requires hosted video)
- **YouTube:** Data API v3 with OAuth2
- Comprehensive error handling
- Upload status tracking

### 11. Audit Logging
- SQLite database for all events
- Tracks pipeline stages
- Records upload attempts
- Supports failure recovery

## 📝 Configuration Files

### `config/model.yaml`
```yaml
model:
  endpoint: "https://models.inference.ai.azure.com"
  model_name: "gpt-4o"
  temperature: 0.7
  max_tokens: 500
  max_segments_to_score: 50
  min_score_threshold: 6.0
```

### `config/platforms.json`
Platform specifications (duration limits, resolution, API endpoints)

### `config/rate_limits.json`
Upload frequency controls:
- Cooldown periods
- Daily/hourly limits
- Retry configurations

## 🎥 Output

After running the pipeline, you'll find:

```
output/
├── work/
│   ├── audio.wav           # Extracted audio (for transcription)
│   └── transcript.json     # Full transcript with timestamps
├── clips/
│   ├── clip_001.mp4        # Extracted + cropped clip 1 (9:16)
│   ├── clip_002.mp4        # Extracted + cropped clip 2 (9:16)
│   └── ...
└── pipeline.log            # Detailed execution log

audit/
└── events.db               # SQLite audit database
```

**Note:** No normalized video is created. Clips are extracted directly from the original video.

## 🔍 Monitoring & Debugging

### View Pipeline Logs
```bash
tail -f pipeline.log
```

### Query Audit Database
```python
from audit import AuditLogger

audit = AuditLogger()

# Get upload history
uploads = audit.get_upload_history(platform="TikTok")

# Get pipeline summary
summary = audit.get_pipeline_summary()
```

### Common Issues

**No clips generated:**
- Check transcript quality score
- Lower `min_score_threshold` in config/model.yaml
- Verify video has clear speech

**Upload failures:**
- Verify API credentials are set
- Check rate limits in logs
- Review platform-specific errors

**FFmpeg errors:**
- Ensure FFmpeg is installed: `ffmpeg -version`
- Check video codec compatibility
- Review FFmpeg logs in pipeline.log

**Whisper errors:**
- May require GPU for large models
- Try smaller model: edit transcribe.py, use "tiny" or "base"
- Check available disk space

## 🩺 Troubleshooting Guide

### Local LLM (Ollama) Issues

**Symptom: "Empty or invalid response" from Ollama**
- **Cause:** Streaming is enabled by default in Ollama API
- **Fix:** The system automatically sets `stream=False`. If issues persist:
  - Check Ollama service: `ollama list` to verify model is loaded
  - Review Ollama logs for errors
  - Restart Ollama service

**Symptom: "Model 'qwen3:latest' not found (404)"**
- **Cause:** Model name mismatch between config and Ollama's registry
- **Fix:** 
  1. Check available models: `ollama list`
  2. Update `local_model_name` in `config/model.yaml` with exact name (e.g., `qwen3:8b`)
  3. Or pull the model: `ollama pull qwen3:latest`

**Symptom: "Memory layout cannot be allocated" or "VRAM error"**
- **Cause:** Insufficient GPU memory for model
- **Fix Options:**
  1. **Use CPU mode** (recommended for <8GB VRAM):
     ```bash
     # Windows
     $env:OLLAMA_NO_GPU=1
     ollama serve
     
     # Linux/macOS
     export OLLAMA_NO_GPU=1
     ollama serve
     ```
  2. **Use smaller model**: Change `qwen3:8b` → `qwen3:4b` in config
  3. **Close other GPU applications**: Free up VRAM
  4. The system has a circuit breaker that switches to API after 3 consecutive memory errors

**Symptom: "Circuit breaker triggered - disabling local LLM"**
- **Cause:** 3+ consecutive failures from local model
- **Behavior:** System automatically switches to API for remaining segments
- **Fix:** Address root cause (memory, model name, etc.) and restart pipeline

**Symptom: Test inference succeeds but actual scoring fails**
- **Cause:** Test uses short prompt; real prompts are longer and need more memory
- **Fix:** The system now uses realistic test prompts. If still failing, use CPU mode or smaller model

**Symptom: "Using Azure SDK" appears in local mode**
- **Cause:** (Fixed in latest version) API client was initialized unconditionally
- **Fix:** Update to latest version. In pure local mode, this message should NOT appear

### Windows-Specific Issues

**Symptom: UnicodeEncodeError with emojis or special characters**
- **Cause:** Windows console defaults to cp1252 encoding
- **Fix:** 
  - The system automatically configures UTF-8 (fixed in latest version)
  - Manually set: `[Console]::OutputEncoding = [System.Text.Encoding]::UTF8`
  - Or enable system-wide in Control Panel (see Prerequisites)

**Symptom: Garbled log output or missing lines**
- **Cause:** Console buffer limitations with heavy logging
- **Fix:** (Fixed in latest version) Log verbosity reduced, emojis removed

### API & Rate Limiting Issues

**Symptom: "Rate limit exceeded: retry after Xs"**
- **Cause:** Too many API requests
- **Prevention:** 
  - Use local LLM mode to avoid API limits
  - Increase `inter_request_delay` in `config/model.yaml`
  - Reduce `batch_size` for slower, safer processing

**Symptom: All segments score 0**
- **Cause:** API authentication or response parsing issue
- **Fix:**
  1. Verify `GITHUB_TOKEN` is set and valid
  2. Check token has access to model endpoint
  3. Review logs for API errors
  4. Check `response_format` is supported by model

## 🔐 Security & Privacy

- **No hardcoded credentials** - All secrets via environment variables
- **Official APIs only** - No browser automation or scraping
- **Local processing** - Videos stay on your machine
- **Audit trail** - Complete logging of all operations

## 🚨 Rate Limits & Best Practices

### Default Rate Limits
- **TikTok:** 1 upload/hour, 10/day
- **Instagram:** 1 upload/hour, 10/day
- **YouTube:** 1 upload/hour, 10/day

### Recommendations
1. Start with conservative rate limits
2. Monitor platform responses
3. Adjust based on account status
4. Use test accounts initially

## 🛠️ Development

### Adding New Platforms

1. Create uploader in `uploaders/new_platform.py`
2. Implement `upload_to_platform()` function
3. Add configuration to `config/platforms.json`
4. Add rate limits to `config/rate_limits.json`
5. Update `main.py` to include new platform

### Customizing AI Prompts

Edit `ai/prompt.txt` to adjust scoring criteria and output format.

### Extending Segmentation

Add new windowing strategies in `segmenter/` directory.

## 📄 License

This project is provided as-is for educational and commercial use.

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## ⚠️ Disclaimer

- **Platform Policies:** Ensure compliance with TikTok, Instagram, and YouTube Terms of Service
- **Content Rights:** Only process videos you have rights to
- **Rate Limits:** Respect platform upload limits to avoid account restrictions
- **API Quotas:** Monitor your API usage and quotas

## 📞 Support

For issues, questions, or feature requests, please open an issue on GitHub.

---

**Built with:** Python, FFmpeg, Faster-Whisper, GitHub Models, Platform APIs

**Status:** Production-ready, fully implemented, no placeholders