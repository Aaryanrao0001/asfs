# 🎬 ASFS - Automated Short-Form Content System

A **fully automated web application** that transforms long-form videos into viral-worthy short clips optimized for TikTok, Instagram Reels, and YouTube Shorts.

## ✨ What's New in v2.1

**🎯 Multi-Campaign Management System** (NEW!)
- Create and manage multiple independent upload campaigns
- Campaign-specific metadata (captions, hashtags, titles)
- Randomized caption/title selection per upload
- Independent scheduling and execution
- Real-time campaign tracking and analytics
- Pause/resume/cancel campaigns in-flight
- See [CAMPAIGNS_GUIDE.md](CAMPAIGNS_GUIDE.md) for complete guide

## ✨ What's New in v2.0

**🌐 Web-Based UI with VaultMatrix Design**
- Modern React 18+ web interface with cybersecurity aesthetic
- FastAPI REST API backend for seamless integration
- Glassmorphism design with premium green accents
- Real-time pipeline monitoring with live log streaming
- Responsive design for desktop, tablet, and mobile
- No desktop installation required - runs in browser

**🖥️ Redesigned Architecture**
- React frontend with component-based architecture
- FastAPI backend serving REST API endpoints
- Server-Sent Events (SSE) for live log streaming
- Persistent settings management
- Video registry with upload tracking
- Cross-platform compatibility (Windows, macOS, Linux)

**🌐 Browser Automation**
- Upload via Brave browser automation (Playwright)
- Reuse existing browser sessions (stay logged in!)
- No API credentials needed for uploads
- Human-like delays to avoid detection

**🤖 AI Model Integration**
- GitHub Models API integration (gpt-4o, gpt-4o-mini)
- Configurable scoring thresholds
- Multi-factor virality analysis
- Segment-based clip extraction

**🧠 Enhanced Viral Detection**
- Multi-layer viral clip detection with psychological scoring
- Emotion analysis using VADER + NRC emotion lexicons
- Hook quality enforcement (first 7 seconds analysis)
- Narrative arc detection (hook → tension → payoff)
- Semantic deduplication (removes similar clips)
- Auto-generates titles, captions, hashtags, and overlays
- Two-stage pipeline: fast filtering → deep LLM analysis
- 6-factor virality model (Curiosity 25%, Emotion 20%, Contrarian 20%, etc.)
- See [VIRAL_DETECTION_GUIDE.md](VIRAL_DETECTION_GUIDE.md) for details

## 🎯 Overview

This system intelligently:
- **Analyzes** long-form video content
- **Identifies** high-engagement, viral-potential segments
- **Extracts** platform-optimized short videos (9:16 aspect ratio)
- **Generates** captions and hashtags
- **Uploads** to TikTok, Instagram Reels, and YouTube Shorts via browser automation
- **Manages** multi-campaign uploads with independent scheduling
- **Provides** a beautiful web UI for the entire workflow

**This is a real production system** — fully implemented, no placeholders, no mock data.

---

## 🚀 Quick Start (Web UI)

### Prerequisites

1. **Python 3.8+** installed
2. **Node.js 16+** and npm (for frontend development)
3. **FFmpeg** - Must be installed and available in PATH
   ```bash
   # Ubuntu/Debian
   sudo apt-get install ffmpeg
   
   # macOS
   brew install ffmpeg
   
   # Windows
   # Download from https://ffmpeg.org/download.html
   ```

4. **Brave Browser** (recommended for uploads)
   - Download: https://brave.com/download/
   - Or configure path to any Chromium browser

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Goutamdhanani/asfs.git
   cd asfs
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers** (for browser automation)
   ```bash
   playwright install chromium
   ```

4. **Build the frontend** (for production deployment)
   ```bash
   cd web/frontend
   npm install
   npm run build
   cd ../..
   ```

### Running the Web Application

**Launch the web UI** (default):
```bash
python main.py
# or explicitly:
python main.py --web
```

The server will start at `http://localhost:5000` and automatically open in your browser.

**Custom port/host**:
```bash
python main.py --web --port 8080 --host 0.0.0.0
```

**Without auto-opening browser**:
```bash
python main.py --web --no-browser
```

The web application has 6 tabs:
1. **📹 Input** - Select video file(s) and configure output
2. **🤖 AI** - Configure AI model and scoring settings
3. **📝 Metadata** - Set titles, descriptions, tags, captions
4. **🚀 Upload** - Select platforms and browser settings
5. **📊 Videos** - View video registry and upload status
6. **▶️ Run** - Execute pipeline and monitor live logs

### First-Time Setup

1. **AI Configuration (AI Tab)**:
   - Set model name (default: gpt-4o)
   - Configure API endpoint if needed
   - Adjust scoring threshold (0-10)
   - Set max clips per video
   - Configure segment duration

2. **Browser Configuration (Upload Tab)**:
   - Browse to Brave executable (or leave empty for auto-detect)
   - Set user data directory to reuse login sessions
   - Select browser profile
   - Log into TikTok/Instagram/YouTube in Brave beforehand
   - Test browser connection

3. **Metadata Settings (Metadata Tab)**:
   - Choose "Uniform" (same metadata) or "Randomized" (vary per clip)
   - Enter titles, descriptions, and tags
   - Enable/disable hashtag prefix
   - Add optional captions

4. **Run Pipeline (Run Tab)**:
   - Select video in Input tab first
   - Click "Start Pipeline"
   - Monitor progress and view live logs in real-time
   - Copy or save logs as needed

---

## 🌐 Web UI Features

### Input Tab
- **Video selection** with drag-drop zone
- **Selection modes**: Single file, Multiple files, or Folder
- **Output directory** configuration
- **Cache toggle** for faster re-runs
- Video info display (duration, resolution, size)

### AI Tab
- **Model configuration**: Set GitHub Models API model name
- **API endpoint**: Custom endpoint support
- **Scoring threshold** slider (0-10)
- **Max clips** slider (1-50)
- **Segment duration** configuration
- Save settings to backend

### Metadata Tab
- **Two Modes**:
  - **Uniform**: Same metadata for all clips
  - **Randomized**: Random selection from comma-separated values
- **Fields**:
  - Title(s)
  - Description(s)
  - Caption(s) - Comma-separated captions with random selection
  - Tags (comma-separated)
  - Hashtag prefix toggle
- Save settings to backend

### Upload Tab
- **Platform Selection**: TikTok, Instagram, YouTube Shorts checkboxes
- **Brave Browser Configuration**:
  - Browser executable path
  - User data directory
  - Profile directory selection
- **Upload Options**:
  - Upload delay configuration (seconds)
  - Headless mode toggle
  - Wait for upload confirmation toggle
  - Auto-retry on failure toggle
- **Test browser connection** button
- Save settings to backend

### Videos Tab
- **Video Registry & Management**:
  - Add multiple videos from any folder (not just pipeline output)
  - Import ready-to-share videos with multi-select
  - View upload status for all platforms (Instagram, TikTok, YouTube)
  - Control duplicate upload permissions per video
  - One-click upload to any platform
  - Bulk upload all pending videos
  - Auto-refresh every 5 seconds
- **Preprocessing Applied**:
### Videos Tab
- **Video Registry & Management**:
  - View all processed videos in a table
  - Track upload status per platform (TikTok, Instagram, YouTube)
  - Add videos manually to registry
  - Refresh video list
  - Upload individual videos or batch upload
  - Color-coded status badges (pending, completed, failed)

### Run Tab
- **Pipeline Controls**:
  - Start Pipeline button (with video path prompt)
  - Stop Pipeline button (when running)
  - Clear Logs button
- **Status Display**:
  - Current pipeline status badge (idle, running, completed, error)
  - Video path and output directory display
  - Progress bar with percentage (when running)
- **Live Logs**:
  - Terminal-style log viewer with JetBrains Mono font
  - Color-coded log levels (info, success, warning, error)
  - Real-time log streaming via Server-Sent Events (SSE)
  - Copy logs to clipboard
  - Save logs to file
  - Auto-scroll to latest logs

---

## 🎯 Multi-Campaign Management

The campaign management system allows you to organize and execute multiple independent video upload campaigns with ease.

### Key Features

- **Create Multiple Campaigns**: Organize videos into separate campaigns (e.g., "Summer Launch", "Tutorial Series")
- **Campaign-Specific Metadata**: Each campaign has its own captions, hashtags, and titles
- **Randomized Content**: Use comma-separated values for captions/titles that are randomly selected per upload
- **Independent Scheduling**: Configure delays, platforms, and timing per campaign
- **Real-Time Control**: Pause, resume, or cancel campaigns in-flight
- **Upload Tracking**: Monitor success/failure rates and analytics per campaign
- **Platform Targeting**: Select different platforms for each campaign (Instagram, TikTok, YouTube)

### Quick Example

```bash
# Create a campaign
curl -X POST http://localhost:5000/api/campaigns \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Product Launch Q1",
    "description": "New product promotional videos"
  }'

# Configure metadata with randomization
curl -X PUT http://localhost:5000/api/campaigns/{campaign_id} \
  -H "Content-Type: application/json" \
  -d '{
    "metadata": {
      "caption_mode": "randomized",
      "captions": "New arrivals!, Fresh styles!, Must-see collection!",
      "hashtags": "fashion,newcollection,style",
      "add_hashtag_prefix": true
    },
    "schedule": {
      "platforms": ["Instagram", "TikTok"],
      "delay_seconds": 300
    }
  }'

# Execute campaign
curl -X POST http://localhost:5000/api/campaigns/{campaign_id}/execute
```

### Use Cases

1. **Product Launch**: 10 videos with varied captions across Instagram & TikTok
2. **Tutorial Series**: Educational content with consistent branding to YouTube
3. **Parallel Campaigns**: Run morning motivation posts and tech reviews simultaneously

### API Endpoints

- `POST /api/campaigns` - Create campaign
- `GET /api/campaigns` - List all campaigns
- `GET /api/campaigns/{id}` - Get campaign details
- `PUT /api/campaigns/{id}` - Update campaign
- `DELETE /api/campaigns/{id}` - Delete campaign
- `POST /api/campaigns/{id}/execute` - Start campaign execution
- `POST /api/campaigns/{id}/pause` - Pause active campaign
- `POST /api/campaigns/{id}/resume` - Resume paused campaign
- `GET /api/campaigns/{id}/status` - Get execution status
- `GET /api/campaigns/{id}/analytics` - Get campaign analytics

For detailed usage, examples, and troubleshooting, see **[CAMPAIGNS_GUIDE.md](CAMPAIGNS_GUIDE.md)**.

---

## ⌨️ CLI Mode (Backward Compatible)

The original CLI interface is still available:

```bash
python main.py --cli <video_path> [options]
```

### CLI Usage

```bash
# Basic usage
python main.py --cli path/to/video.mp4

# Custom output directory
python main.py --cli video.mp4 -o custom_output/

# Disable caching (force full reprocessing)
python main.py --cli video.mp4 --no-cache

# Verbose logging
python main.py --cli video.mp4 -v
```

### CLI Help

```bash
python main.py --cli --help
```


---

## 📦 Building Executable

Build a standalone `.exe` file for distribution:

### Quick Build

```bash
python build.py
```

This creates `dist/asfs.exe` (Windows) or equivalent on other platforms.

### Manual Build with PyInstaller

```bash
pyinstaller main.py --name=asfs --onefile --windowed --add-data=config:config
```

### Notes on Distribution

1. **Playwright Browsers**: End users need to run `playwright install chromium` once
2. **FFmpeg**: Must be installed separately on user's system
3. **Ollama**: Optional - users can install for local AI features
4. **Executable Size**: Expect ~100-200MB due to bundled Python and dependencies

### Alternative: Direct Python

Users can also run directly with Python (no build needed):
```bash
pip install -r requirements.txt
python main.py
```

---

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
├── ui/                  # Desktop application (NEW)
│   ├── __init__.py
│   ├── app.py           # QApplication entry point
│   ├── main_window.py   # Main window with tabs
│   ├── styles.py        # Dark theme stylesheet
│   ├── tabs/            # Individual tab widgets
│   │   ├── input_tab.py      # Video selection
│   │   ├── ai_tab.py         # Ollama controls
│   │   ├── metadata_tab.py   # Metadata settings
│   │   ├── upload_tab.py     # Platform config
│   │   └── run_tab.py        # Pipeline execution
│   └── workers/         # Background threads
│       ├── ollama_worker.py   # Ollama operations
│       └── pipeline_worker.py # Pipeline execution
├── uploaders/           # Browser-based uploaders (UPDATED)
│   ├── __init__.py
│   ├── brave_base.py    # Playwright + Brave automation
│   ├── brave_tiktok.py  # TikTok browser upload
│   ├── brave_instagram.py # Instagram browser upload
│   ├── brave_youtube.py # YouTube Shorts browser upload
│   ├── tiktok.py        # Legacy API uploader (deprecated)
│   ├── instagram.py     # Legacy API uploader (deprecated)
│   └── youtube.py       # Legacy API uploader (deprecated)
├── ai/                  # AI highlight scoring (UPDATED)
│   ├── __init__.py
│   ├── scorer.py        # GitHub Models + Ollama integration
│   ├── ollama_manager.py # Ollama server management (NEW)
│   └── prompt.txt       # Scoring prompt template
├── metadata/            # Caption & metadata (UPDATED)
│   ├── __init__.py
│   ├── captions.py      # Platform-specific captions
│   ├── hashtags.py      # Hashtag strategies
│   ├── config.py        # MetadataConfig class (NEW)
│   └── resolver.py      # Metadata resolution (NEW)
├── transcript/          # Transcription & quality
│   ├── __init__.py
│   ├── transcribe.py    # Faster-Whisper transcription
│   ├── audio_extract.py # Fast audio extraction
│   └── quality_check.py # Transcript validation
├── segmenter/           # Candidate segment building
│   ├── __init__.py
│   ├── sentence_window.py  # Sentence-based windowing
│   └── pause_window.py     # Pause-based windowing
├── cache/               # Pipeline state caching
│   ├── __init__.py
│   └── checkpoint.py    # Resume from last completed stage
├── validator/           # Clip validation
│   ├── __init__.py
│   ├── dedup.py         # Semantic deduplication
│   └── overlap.py       # Overlap removal
├── clipper/             # Clip extraction
│   ├── __init__.py
│   └── extract.py       # FFmpeg clip extraction
├── scheduler/           # Upload scheduling
│   ├── __init__.py
│   └── queue.py         # Rate limiting & retry logic
├── audit/               # Logging & audit trail
│   ├── __init__.py
│   └── logger.py        # SQLite audit logging
├── config/              # Configuration files
│   ├── platforms.json   # Platform specifications
│   ├── rate_limits.json # Upload rate limits
│   └── model.yaml       # AI model configuration
├── main.py              # Main entry point (GUI/CLI router)
├── pipeline.py          # Pipeline logic (CLI mode)
├── build.py             # PyInstaller build script
├── requirements.txt     # Python dependencies
└── README.md            # This file
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