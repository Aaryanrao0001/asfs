#!/usr/bin/env python3
"""
ASFS Web Server - Flask backend for React frontend.

Provides REST API endpoints for all ASFS functionality:
- Pipeline control (start/stop/status)
- Settings management
- Video registry
- Live log streaming
"""

import os
import sys
import json
import logging
import threading
import queue
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import ASFS modules
from pipeline import run_pipeline
from database.video_registry import VideoRegistry
from config import model as config_model

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder='frontend/build', static_url_path='')
CORS(app)  # Enable CORS for development

# Global state
pipeline_thread = None
pipeline_status = {
    'running': False,
    'progress': 0,
    'stage': 'idle',
    'video_path': None,
    'output_dir': None
}
pipeline_status_lock = threading.Lock()  # Thread-safe access to pipeline_status
log_queue = queue.Queue()
stop_pipeline_flag = threading.Event()

# Settings storage (in production, use database)
settings_cache = {
    'ai': {
        'model_name': 'gpt-4o',
        'api_endpoint': None,
        'scoring_threshold': 7.0,
        'max_clips': 10,
        'segment_duration': 60
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
        'output_dir': 'output',
        'use_cache': True
    }
}

# Initialize video registry
video_registry = VideoRegistry()


class LogCapture(logging.Handler):
    """Custom logging handler to capture logs for streaming."""
    
    def emit(self, record):
        try:
            msg = self.format(record)
            log_queue.put({
                'timestamp': datetime.now().isoformat(),
                'level': record.levelname,
                'message': msg
            })
        except Exception:
            pass


# Add log capture handler
log_capture = LogCapture()
log_capture.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
logging.getLogger().addHandler(log_capture)


def run_pipeline_thread(video_path: str, output_dir: str, use_cache: bool = True):
    """Run pipeline in background thread."""
    global pipeline_status
    
    try:
        with pipeline_status_lock:
            pipeline_status['running'] = True
            pipeline_status['stage'] = 'starting'
            pipeline_status['video_path'] = video_path
            pipeline_status['output_dir'] = output_dir
        
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
        else:
            logger.info("\n" + "=" * 80)
            logger.info("PIPELINE STOPPED BY USER")
            logger.info("=" * 80)
            with pipeline_status_lock:
                pipeline_status['stage'] = 'stopped'
            
    except Exception as e:
        logger.error(f"Pipeline error: {str(e)}")
        with pipeline_status_lock:
            pipeline_status['stage'] = 'error'
    finally:
        with pipeline_status_lock:
            pipeline_status['running'] = False
        stop_pipeline_flag.clear()


# ============================================================================
# API Routes
# ============================================================================

@app.route('/')
def index():
    """Serve React app."""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    """Serve static files or React app."""
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')


# Pipeline endpoints
@app.route('/api/pipeline/start', methods=['POST'])
def start_pipeline():
    """Start the video processing pipeline."""
    global pipeline_thread, pipeline_status
    
    with pipeline_status_lock:
        if pipeline_status['running']:
            return jsonify({'error': 'Pipeline is already running'}), 400
    
    data = request.json
    video_path = data.get('video_path')
    output_dir = data.get('output_dir', 'output')
    use_cache = data.get('use_cache', True)
    
    if not video_path:
        return jsonify({'error': 'video_path is required'}), 400
    
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
    
    return jsonify({
        'success': True,
        'message': 'Pipeline started',
        'status': status_copy
    })


@app.route('/api/pipeline/stop', methods=['POST'])
def stop_pipeline():
    """Stop the running pipeline."""
    global pipeline_status
    
    with pipeline_status_lock:
        if not pipeline_status['running']:
            return jsonify({'error': 'No pipeline is running'}), 400
        pipeline_status['stage'] = 'stopping'
    
    stop_pipeline_flag.set()
    
    return jsonify({
        'success': True,
        'message': 'Pipeline stop requested'
    })


@app.route('/api/pipeline/status', methods=['GET'])
def get_pipeline_status():
    """Get current pipeline status."""
    with pipeline_status_lock:
        status_copy = pipeline_status.copy()
    return jsonify(status_copy)


@app.route('/api/pipeline/logs', methods=['GET'])
def stream_logs():
    """Stream live logs using Server-Sent Events."""
    def generate():
        while True:
            try:
                # Get log message with timeout
                log_msg = log_queue.get(timeout=1)
                yield f"data: {json.dumps(log_msg)}\n\n"
            except queue.Empty:
                # Send heartbeat
                yield f": heartbeat\n\n"
    
    return Response(generate(), mimetype='text/event-stream')


# Video endpoints
@app.route('/api/video/info', methods=['POST'])
def get_video_info():
    """Get information about a video file."""
    data = request.json
    video_path = data.get('video_path')
    
    if not video_path or not os.path.exists(video_path):
        return jsonify({'error': 'Invalid video path'}), 400
    
    # Get basic file info
    try:
        import ffmpeg
        probe = ffmpeg.probe(video_path)
        video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        
        return jsonify({
            'path': video_path,
            'duration': float(probe['format']['duration']),
            'width': int(video_info['width']),
            'height': int(video_info['height']),
            'size': os.path.getsize(video_path)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Settings endpoints
@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get all application settings."""
    return jsonify(settings_cache)


@app.route('/api/settings', methods=['POST'])
def save_settings():
    """Save application settings."""
    global settings_cache
    
    data = request.json
    category = data.get('category')
    
    if category and category in settings_cache:
        settings_cache[category].update(data.get('settings', {}))
    else:
        # Update all settings
        settings_cache.update(data)
    
    return jsonify({
        'success': True,
        'settings': settings_cache
    })


@app.route('/api/ai/settings', methods=['POST'])
def update_ai_settings():
    """Update AI/model settings."""
    data = request.json
    settings_cache['ai'].update(data)
    
    return jsonify({
        'success': True,
        'settings': settings_cache['ai']
    })


# Video registry endpoints
@app.route('/api/videos', methods=['GET'])
def list_videos():
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
        
        return jsonify({'videos': result})
    except Exception as e:
        logger.error(f"Error listing videos: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/videos/add', methods=['POST'])
def add_video():
    """Add a video to the registry."""
    data = request.json
    file_path = data.get('file_path')
    title = data.get('title', '')
    duration = data.get('duration')
    
    if not file_path:
        return jsonify({'error': 'file_path is required'}), 400
    
    try:
        video_id = video_registry.register_video(
            file_path=file_path,
            title=title,
            duration=duration
        )
        
        return jsonify({
            'success': True,
            'video_id': video_id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/upload/start', methods=['POST'])
def start_upload():
    """Start video upload to platforms."""
    data = request.json
    video_id = data.get('video_id')
    platforms = data.get('platforms', [])
    
    if not video_id:
        return jsonify({'error': 'video_id is required'}), 400
    
    # TODO: Implement upload functionality
    # This would integrate with the uploaders module
    
    return jsonify({
        'success': True,
        'message': 'Upload started',
        'video_id': video_id,
        'platforms': platforms
    })


@app.route('/api/upload/status', methods=['GET'])
def get_upload_status():
    """Get upload status for a video."""
    video_id = request.args.get('video_id')
    
    if not video_id:
        return jsonify({'error': 'video_id is required'}), 400
    
    # Get status from registry
    platforms = ['tiktok', 'instagram', 'youtube']
    status = {}
    
    for platform in platforms:
        platform_status = video_registry.get_upload_status(video_id, platform)
        status[platform] = platform_status or 'pending'
    
    return jsonify({'video_id': video_id, 'status': status})


# Health check
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat()
    })


def run_server(host='127.0.0.1', port=5000, debug=False, open_browser=True):
    """
    Run the Flask web server.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        debug: Enable debug mode
        open_browser: Automatically open browser
    """
    logger.info("=" * 80)
    logger.info("ASFS Web Server")
    logger.info("=" * 80)
    logger.info(f"Starting server at http://{host}:{port}")
    logger.info("Press Ctrl+C to stop")
    logger.info("")
    
    # Open browser automatically
    if open_browser:
        import webbrowser
        def open_browser_delayed():
            time.sleep(1.5)  # Wait for server to start
            webbrowser.open(f'http://{host}:{port}')
        
        browser_thread = threading.Thread(target=open_browser_delayed)
        browser_thread.daemon = True
        browser_thread.start()
    
    # Run Flask app
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == '__main__':
    # Note: Do not use debug=True in production
    # For development only
    import os
    is_dev = os.environ.get('FLASK_ENV') == 'development'
    run_server(debug=is_dev)
