# ASFS Web UI

## Overview
React-based web application with VaultMatrix cybersecurity design aesthetic.

## Architecture
- **Backend**: Flask REST API (`server.py`)
- **Frontend**: React 18+ (`frontend/`)

## Development

### Backend Setup
```bash
# Install Python dependencies
pip install -r ../requirements.txt

# Run Flask server
python server.py
```

### Frontend Setup
```bash
cd frontend

# Install Node dependencies
npm install

# Start development server
npm start
```

The React dev server will proxy API requests to Flask backend at `http://localhost:5000`.

## Production Build

```bash
cd frontend
npm run build
```

The Flask server will serve the built React app from `frontend/build/`.

## API Endpoints

### Pipeline Control
- `POST /api/pipeline/start` - Start video processing pipeline
- `POST /api/pipeline/stop` - Stop running pipeline
- `GET /api/pipeline/status` - Get pipeline status
- `GET /api/pipeline/logs` - Stream live logs (SSE)

### Settings
- `GET /api/settings` - Get all settings
- `POST /api/settings` - Save settings
- `POST /api/ai/settings` - Update AI settings

### Video Registry
- `GET /api/videos` - List all videos
- `POST /api/videos/add` - Add video to registry

### Upload
- `POST /api/upload/start` - Start upload to platforms
- `GET /api/upload/status` - Get upload status

### Video Info
- `POST /api/video/info` - Get video file information

### Health
- `GET /api/health` - Health check

## Design System

### Colors
- Background: `#031b14` → `#052e21` → `#02110c`
- Accent: `#00ff88` (primary), `#10d97a` (secondary)
- Text: `#e8fff6` (primary), `#9edbc3` (secondary)

### Components
- GlassPanel - Glassmorphism containers
- GlowButton - Primary CTAs with green glow
- SecondaryButton - Transparent with border
- TextInput/TextArea - Dark inputs with focus glow
- Checkbox/Radio/Toggle - Custom styled
- ProgressBar - Gradient fill with shimmer
- StatusBadge - Color-coded status indicators
- LogViewer - Terminal-style log display
- Modal - Glass overlay with backdrop blur

### Typography
- Font: Inter (body) + JetBrains Mono (code/logs)
- Weights: 600 (headings), 500 (labels), 400 (body)

## Tabs

1. **Input** - Video selection, output config, cache settings
2. **AI** - Model config, scoring threshold, max clips
3. **Metadata** - Title, description, tags, caption
4. **Upload** - Platform selection, Brave browser config
5. **Videos** - Registry table, upload management
6. **Run** - Pipeline control, live logs, progress
