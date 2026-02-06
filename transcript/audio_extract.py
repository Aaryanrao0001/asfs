"""Fast audio extraction for transcription."""

import subprocess
import os
import logging

logger = logging.getLogger(__name__)


def extract_audio(video_path: str, output_dir: str) -> str:
    """
    Extract audio from video for transcription.
    
    Optimized for Whisper:
    - 16kHz sample rate (Whisper's preferred format)
    - Mono audio (transcription doesn't need stereo)
    - PCM WAV format (uncompressed, fastest to process)
    
    This is 10-50x faster than re-encoding full video.
    
    Args:
        video_path: Path to input video file
        output_dir: Directory to save audio file
        
    Returns:
        Path to extracted audio file (.wav)
        
    Raises:
        FileNotFoundError: If video doesn't exist
        RuntimeError: If FFmpeg extraction fails
        
    Note:
        If audio.wav already exists in output_dir, it will be overwritten.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    os.makedirs(output_dir, exist_ok=True)
    audio_path = os.path.join(output_dir, "audio.wav")
    
    logger.info(f"Extracting audio from: {video_path}")
    
    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-vn",                    # No video
        "-acodec", "pcm_s16le",   # 16-bit PCM
        "-ar", "16000",           # 16kHz (Whisper optimal)
        "-ac", "1",               # Mono
        "-y",
        audio_path
    ]
    
    logger.info(f"Running FFmpeg: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        
        if not os.path.exists(audio_path):
            raise RuntimeError("Audio file was not created")
        
        file_size = os.path.getsize(audio_path)
        logger.info(f"✓ Audio extracted: {file_size / (1024*1024):.2f} MB")
        
        return audio_path
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Audio extraction failed: {e.stderr}")
        raise RuntimeError(f"Audio extraction failed: {e.stderr}")
