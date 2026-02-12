#!/usr/bin/env python3
"""
ASFS Backend API - FastAPI server for React frontend.

Provides real REST API endpoints and WebSocket support for all ASFS functionality:
- Video upload and processing
- Pipeline control (start/stop/status)
- Settings management with persistence
- AI/Model management
- Metadata generation
- Platform upload configuration
- Live log streaming via WebSocket
"""

import os
import sys
import json
import logging
import threading
import queue
import time
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect, HTTPException, Body
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

# Import ASFS modules
from pipeline import run_pipeline
from database.video_registry import VideoRegistry
from config import model as config_model
from metadata.resolver import resolve_metadata
from metadata.config import MetadataConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="ASFS API", version="2.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
pipeline_thread = None
pipeline_status = {
    'running': False,
    'progress': 0,
    'stage': 'idle',
    'video_path': None,
    'output_dir': None,
    'error': None
}
pipeline_status_lock = threading.Lock()
log_queue = queue.Queue()
stop_pipeline_flag = threading.Event()

# Settings file path
SETTINGS_FILE = Path("ui_settings.json")

# Default settings
DEFAULT_SETTINGS = {
    'ai': {
        'model_name': 'gpt-4o',
        'api_endpoint': '',
        'scoring_threshold': 7.0,
        'max_clips': 10,
        'segment_duration': 60,
        'ollama_status': 'stopped',
        'available_models': []
    },
    'metadata': {
        'mode': 'uniform',
        'title': '',
        'description': '',
        'tags': '',
        'hashtag_prefix': True,
        'caption': ''
    },
    'upload': {
        'platforms': {
            'tiktok': False,
            'instagram': False,
            'youtube': False
        },
        'brave_path': '',
        'user_data_dir': '',
        'profile_dir': '',
        'upload_delay': 30,
        'headless': False,
        'wait_confirmation': True,
        'auto_retry': True
    },
    'input': {
        'selection_mode': 'single',
        'video_path': '',
        'output_dir': 'output',
        'use_cache': True,
        'video_info': None
    }
}

# Initialize video registry
video_registry = VideoRegistry()

# WebSocket connections
websocket_connections = []


# ============================================================================
# Pydantic Models
# ============================================================================

class PipelineStartRequest(BaseModel):
    video_path: str
    output_dir: str = "output"
    use_cache: bool = True


class SettingsUpdateRequest(BaseModel):
    category: Optional[str] = None
    settings: Dict


class MetadataSaveRequest(BaseModel):
    mode: str
    title: str = ""
    description: str = ""
    tags: str = ""
    caption: str = ""
    hashtag_prefix: bool = True


class UploadConfigRequest(BaseModel):
    platforms: Dict[str, bool]
    brave_path: str = ""
    user_data_dir: str = ""
    profile_dir: str = ""


class OllamaModelRequest(BaseModel):
    model_name: str


# ============================================================================
# Settings Management
# ============================================================================

def load_settings() -> Dict:
    """Load settings from file or return defaults."""
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r') as f:
                loaded = json.load(f)
                # Merge with defaults to ensure all keys exist
                settings = DEFAULT_SETTINGS.copy()
                for category in settings:
                    if category in loaded:
                        settings[category].update(loaded[category])
                return settings
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
    return DEFAULT_SETTINGS.copy()


def save_settings(settings: Dict):
    """Save settings to file."""
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
        logger.info(f"Settings saved to {SETTINGS_FILE}")
    except Exception as e:
        logger.error(f"Failed to save settings: {e}")
        raise


# Global settings cache
settings_cache = load_settings()


# ============================================================================
# Log Capture
# ============================================================================

class LogCapture(logging.Handler):
    """Custom logging handler to capture logs for streaming."""
    
    def emit(self, record):
        try:
            msg = self.format(record)
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'level': record.levelname,
                'message': msg
            }
            log_queue.put(log_entry)
        except Exception:
            pass


# Add log capture handler
log_capture = LogCapture()
log_capture.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
logging.getLogger().addHandler(log_capture)


# ============================================================================
# Pipeline Management
# ============================================================================

def run_pipeline_thread(video_path: str, output_dir: str, use_cache: bool = True):
    """Run pipeline in background thread."""
    global pipeline_status
    
    try:
        with pipeline_status_lock:
            pipeline_status['running'] = True
            pipeline_status['stage'] = 'starting'
            pipeline_status['video_path'] = video_path
            pipeline_status['output_dir'] = output_dir
            pipeline_status['error'] = None
        
        logger.info("=" * 80)
        logger.info("STARTING PIPELINE")
        logger.info("=" * 80)
        logger.info(f"Video: {video_path}")
        logger.info(f"Output: {output_dir}")
        logger.info("")
        
        # Run the pipeline
        run_pipeline(
            video_path=video_path,
            output_dir=output_dir,
            use_cache=use_cache
        )
        
        if not stop_pipeline_flag.is_set():
            logger.info("\n" + "=" * 80)
            logger.info("PIPELINE COMPLETED SUCCESSFULLY")
            logger.info("=" * 80)
            with pipeline_status_lock:
                pipeline_status['stage'] = 'completed'
                pipeline_status['progress'] = 100
        else:
            logger.info("\n" + "=" * 80)
            logger.info("PIPELINE STOPPED BY USER")
            logger.info("=" * 80)
            with pipeline_status_lock:
                pipeline_status['stage'] = 'stopped'
            
    except Exception as e:
        logger.error(f"Pipeline error: {str(e)}", exc_info=True)
        with pipeline_status_lock:
            pipeline_status['stage'] = 'error'
            pipeline_status['error'] = str(e)
    finally:
        with pipeline_status_lock:
            pipeline_status['running'] = False
        stop_pipeline_flag.clear()


# ============================================================================
# API Routes
# ============================================================================

@app.get("/")
async def root():
    """API root."""
    return {"message": "ASFS API Server", "version": "2.0.0"}


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        'status': 'ok',
        'timestamp': datetime.now().isoformat()
    }


# ============================================================================
# Video Upload
# ============================================================================

@app.post("/api/upload-video")
async def upload_video(file: UploadFile = File(...)):
    """
    Upload a video file.
    Returns video metadata (duration, size, resolution).
    """
    try:
        # Create uploads directory
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        # Save uploaded file
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Video uploaded: {file_path}")
        
        # Extract video metadata using ffprobe
        try:
            import ffmpeg
            probe = ffmpeg.probe(str(file_path))
            video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
            
            video_metadata = {
                'path': str(file_path.absolute()),
                'filename': file.filename,
                'duration': float(probe['format']['duration']),
                'width': int(video_info['width']),
                'height': int(video_info['height']),
                'size': os.path.getsize(file_path),
                'format': probe['format']['format_name']
            }
            
            # Update settings with video path
            global settings_cache
            settings_cache['input']['video_path'] = str(file_path.absolute())
            settings_cache['input']['video_info'] = video_metadata
            save_settings(settings_cache)
            
            return {
                'success': True,
                'message': 'Video uploaded successfully',
                'video': video_metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to extract video metadata: {e}")
            return {
                'success': True,
                'message': 'Video uploaded but metadata extraction failed',
                'video': {
                    'path': str(file_path.absolute()),
                    'filename': file.filename,
                    'size': os.path.getsize(file_path)
                }
            }
            
    except Exception as e:
        logger.error(f"Video upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Settings Management
# ============================================================================

@app.get("/api/settings")
async def get_settings():
    """Get all application settings."""
    return settings_cache


@app.post("/api/settings")
async def update_settings(request: SettingsUpdateRequest):
    """Save application settings."""
    global settings_cache
    
    try:
        if request.category and request.category in settings_cache:
            settings_cache[request.category].update(request.settings)
        else:
            # Update all settings
            for category, values in request.settings.items():
                if category in settings_cache:
                    settings_cache[category].update(values)
        
        save_settings(settings_cache)
        
        return {
            'success': True,
            'message': 'Settings saved successfully',
            'settings': settings_cache
        }
    except Exception as e:
        logger.error(f"Failed to save settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Pipeline Control
# ============================================================================

@app.post("/api/pipeline/start")
async def start_pipeline(request: PipelineStartRequest):
    """Start the video processing pipeline."""
    global pipeline_thread, pipeline_status
    
    with pipeline_status_lock:
        if pipeline_status['running']:
            raise HTTPException(status_code=400, detail='Pipeline is already running')
    
    video_path = request.video_path
    output_dir = request.output_dir
    use_cache = request.use_cache
    
    if not video_path:
        raise HTTPException(status_code=400, detail='video_path is required')
    
    if not os.path.exists(video_path):
        raise HTTPException(status_code=400, detail=f'Video file not found: {video_path}')
    
    # Validate settings
    if not any(settings_cache['upload']['platforms'].values()):
        logger.warning("No upload platforms selected")
    
    # Start pipeline in background thread
    stop_pipeline_flag.clear()
    pipeline_thread = threading.Thread(
        target=run_pipeline_thread,
        args=(video_path, output_dir, use_cache)
    )
    pipeline_thread.daemon = True
    pipeline_thread.start()
    
    with pipeline_status_lock:
        status_copy = pipeline_status.copy()
    
    return {
        'success': True,
        'message': 'Pipeline started',
        'status': status_copy
    }


@app.post("/api/pipeline/stop")
async def stop_pipeline():
    """Stop the running pipeline."""
    global pipeline_status
    
    with pipeline_status_lock:
        if not pipeline_status['running']:
            raise HTTPException(status_code=400, detail='No pipeline is running')
        pipeline_status['stage'] = 'stopping'
    
    stop_pipeline_flag.set()
    
    return {
        'success': True,
        'message': 'Pipeline stop requested'
    }


@app.get("/api/pipeline/status")
async def get_pipeline_status():
    """Get current pipeline status."""
    with pipeline_status_lock:
        status_copy = pipeline_status.copy()
    return status_copy


# ============================================================================
# WebSocket for Live Logs
# ============================================================================

@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """WebSocket endpoint for streaming live logs."""
    await websocket.accept()
    websocket_connections.append(websocket)
    logger.info("WebSocket client connected")
    
    try:
        while True:
            try:
                # Get log message with timeout
                log_msg = log_queue.get(timeout=1)
                await websocket.send_json(log_msg)
            except queue.Empty:
                # Send heartbeat
                await websocket.send_json({'type': 'heartbeat'})
            except Exception as e:
                logger.error(f"Error sending log: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    finally:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)


# ============================================================================
# Ollama / AI Model Management
# ============================================================================

@app.get("/api/ollama/status")
async def get_ollama_status():
    """Get Ollama server status."""
    # Check if Ollama is running (simplified check)
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, timeout=5)
        if result.returncode == 0:
            return {
                'status': 'running',
                'available': True
            }
        else:
            return {
                'status': 'stopped',
                'available': True
            }
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return {
            'status': 'stopped',
            'available': False,
            'message': 'Ollama not installed or not in PATH'
        }


@app.post("/api/ollama/start")
async def start_ollama():
    """Start Ollama server."""
    try:
        # This is a simplified implementation
        # In a real scenario, you'd need to manage the Ollama server process
        subprocess.Popen(['ollama', 'serve'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {
            'success': True,
            'message': 'Ollama server start requested'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to start Ollama: {str(e)}')


@app.post("/api/ollama/stop")
async def stop_ollama():
    """Stop Ollama server."""
    try:
        # Find and kill the ollama process
        result = subprocess.run(['pgrep', 'ollama'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            pid = result.stdout.strip().split('\n')[0]  # Get first PID
            subprocess.run(['kill', pid], timeout=5)
            return {
                'success': True,
                'message': 'Ollama server stop requested'
            }
        else:
            return {
                'success': False,
                'message': 'Ollama server not running'
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to stop Ollama: {str(e)}')


@app.get("/api/ollama/models")
async def list_ollama_models():
    """List available Ollama models."""
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            # Parse ollama list output
            lines = result.stdout.strip().split('\n')
            models = []
            if len(lines) > 1:
                for line in lines[1:]:  # Skip header
                    parts = line.split()
                    if parts:
                        models.append({
                            'name': parts[0],
                            'id': parts[0]
                        })
            return {
                'success': True,
                'models': models
            }
        else:
            return {
                'success': False,
                'models': [],
                'error': 'Failed to list models'
            }
    except Exception as e:
        logger.error(f"Failed to list Ollama models: {e}")
        return {
            'success': False,
            'models': [],
            'error': str(e)
        }


@app.post("/api/ollama/load-model")
async def load_ollama_model(request: OllamaModelRequest):
    """Load/pull an Ollama model."""
    try:
        # Pull the model (this may take a while)
        result = subprocess.run(
            ['ollama', 'pull', request.model_name],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            return {
                'success': True,
                'message': f'Model {request.model_name} loaded successfully'
            }
        else:
            return {
                'success': False,
                'error': result.stderr
            }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'Model loading timed out'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Metadata Management
# ============================================================================

@app.post("/api/metadata/save")
async def save_metadata(request: MetadataSaveRequest):
    """Save metadata settings."""
    global settings_cache
    
    try:
        settings_cache['metadata'].update({
            'mode': request.mode,
            'title': request.title,
            'description': request.description,
            'tags': request.tags,
            'caption': request.caption,
            'hashtag_prefix': request.hashtag_prefix
        })
        
        save_settings(settings_cache)
        
        return {
            'success': True,
            'message': 'Metadata saved successfully',
            'metadata': settings_cache['metadata']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/metadata/preview")
async def preview_metadata():
    """Preview metadata with current settings."""
    try:
        meta = settings_cache['metadata']
        
        # Create MetadataConfig
        config = MetadataConfig(
            mode=meta['mode'],
            titles=[meta['title']] if meta['title'] else [],
            descriptions=[meta['description']] if meta['description'] else [],
            captions=[meta['caption']] if meta['caption'] else [],
            tags=meta['tags'].split() if meta['tags'] else [],
            hashtag_prefix=meta['hashtag_prefix']
        )
        
        # Generate preview
        preview = resolve_metadata(config)
        
        return {
            'success': True,
            'preview': preview
        }
    except Exception as e:
        logger.error(f"Failed to preview metadata: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Upload Configuration
# ============================================================================

@app.post("/api/upload/configure")
async def configure_upload(request: UploadConfigRequest):
    """Configure upload platforms and settings."""
    global settings_cache
    
    try:
        settings_cache['upload']['platforms'] = request.platforms
        if request.brave_path:
            settings_cache['upload']['brave_path'] = request.brave_path
        if request.user_data_dir:
            settings_cache['upload']['user_data_dir'] = request.user_data_dir
        if request.profile_dir:
            settings_cache['upload']['profile_dir'] = request.profile_dir
        
        save_settings(settings_cache)
        
        return {
            'success': True,
            'message': 'Upload configuration saved',
            'upload': settings_cache['upload']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Video Registry
# ============================================================================

@app.get("/api/videos")
async def list_videos():
    """List all videos from registry."""
    try:
        videos = video_registry.list_videos()
        
        # Format response
        result = []
        for video in videos:
            video_data = {
                'id': video[0],
                'file_path': video[1],
                'title': video[2],
                'created_at': video[3],
                'duration': video[4],
                'platforms': {}
            }
            
            # Get upload status for each platform
            platforms = ['tiktok', 'instagram', 'youtube']
            for platform in platforms:
                status = video_registry.get_upload_status(video[0], platform)
                video_data['platforms'][platform] = status or 'pending'
            
            result.append(video_data)
        
        return {'videos': result}
    except Exception as e:
        logger.error(f"Error listing videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Static Files (Serve React App in Production)
# ============================================================================

# Mount static files if build exists
build_dir = Path(__file__).parent / "frontend" / "build"
if build_dir.exists():
    app.mount("/", StaticFiles(directory=str(build_dir), html=True), name="static")


def run_server(host='0.0.0.0', port=5000):
    """
    Run the FastAPI server with Uvicorn.
    
    Args:
        host: Host to bind to
        port: Port to bind to
    """
    import uvicorn
    
    logger.info("=" * 80)
    logger.info("ASFS FastAPI Server")
    logger.info("=" * 80)
    logger.info(f"Starting server at http://{host}:{port}")
    logger.info("Press Ctrl+C to stop")
    logger.info("")
    
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == '__main__':
    run_server()
