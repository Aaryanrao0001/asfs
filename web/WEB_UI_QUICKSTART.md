# ASFS Web UI - Quick Start Guide

## Prerequisites

- Python 3.8+
- Node.js 16+ and npm
- ffmpeg (optional, for video metadata extraction)

## Backend Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Start the FastAPI backend:
```bash
cd web
python3 backend_app.py
```

The backend will start on `http://localhost:5000`

## Frontend Setup

1. Install Node dependencies:
```bash
cd web/frontend
npm install
```

2. Start the React development server:
```bash
npm start
```

The frontend will start on `http://localhost:3000` and proxy API requests to the backend.

## Features

### Real Backend Integration
- ✅ File upload with drag & drop
- ✅ Real video metadata extraction
- ✅ Settings persistence (ui_settings.json)
- ✅ WebSocket log streaming
- ✅ Ollama/AI model management
- ✅ Pipeline control with validation
- ✅ Auto-save with debounce (500ms)
- ✅ Toast notifications for errors/success
- ✅ Real-time progress updates

### Tabs

1. **Input Tab**: Upload videos, configure output directory, cache settings
2. **AI Tab**: Ollama server control, model management, scoring parameters
3. **Metadata Tab**: Configure titles, descriptions, tags with live preview
4. **Upload Tab**: Select platforms (TikTok, Instagram, YouTube), Brave browser config
5. **Run Tab**: Start pipeline, WebSocket log streaming, real-time progress
6. **Videos Tab**: Video registry and upload management

## API Endpoints

- `POST /api/upload-video` - Upload video file
- `POST /api/pipeline/start` - Start processing pipeline
- `POST /api/pipeline/stop` - Stop running pipeline
- `GET /api/pipeline/status` - Get pipeline status
- `WS /ws/logs` - WebSocket for live logs
- `GET /api/settings` - Get all settings
- `POST /api/settings` - Save settings
- `GET /api/ollama/status` - Get Ollama server status
- `POST /api/ollama/start` - Start Ollama server
- `POST /api/ollama/stop` - Stop Ollama server
- `GET /api/ollama/models` - List available models
- `POST /api/ollama/load-model` - Load/pull a model
- `POST /api/metadata/save` - Save metadata settings
- `GET /api/metadata/preview` - Preview metadata
- `POST /api/upload/configure` - Configure upload platforms
- `GET /api/videos` - List videos from registry

## Settings Persistence

All settings are automatically saved to `ui_settings.json` in the repository root with a 500ms debounce. Settings are automatically loaded when you open the app.

## Troubleshooting

### Backend won't start
- Make sure all Python dependencies are installed: `pip install -r requirements.txt`
- Check if port 5000 is already in use

### Frontend won't connect to backend
- Verify backend is running on port 5000
- Check the proxy configuration in `web/frontend/package.json`

### Video upload fails
- Ensure ffmpeg is installed for metadata extraction
- Check file format (MP4, MOV, AVI, MKV supported)

### WebSocket logs not working
- Verify WebSocket connection in browser console
- Check that backend WebSocket endpoint is accessible

## Development

The React app uses:
- React 18
- React Router for navigation
- Custom glassmorphism UI components
- WebSocket for real-time updates
- Debounced auto-save for all settings

The FastAPI backend uses:
- FastAPI for REST API
- WebSocket for log streaming
- File-based settings persistence
- Integration with existing ASFS pipeline code
