"""Video transcription using Faster-Whisper (optimized for speed)."""

import os
import json
import logging
from faster_whisper import WhisperModel
from typing import List, Dict

logger = logging.getLogger(__name__)


def transcribe_video(video_path: str, output_dir: str, model_size: str = "base") -> str:
    """
    Transcribe video/audio using Faster-Whisper with multi-threading.
    
    Faster-Whisper uses CTranslate2 for 4x speed improvement over original Whisper
    while maintaining the same quality. Supports CPU and GPU acceleration.
    
    Args:
        video_path: Path to video or audio file
        output_dir: Directory to save transcript JSON
        model_size: Whisper model size (tiny, base, small, medium, large-v1, large-v2, large-v3)
                    Note: faster-whisper supports all standard Whisper model sizes
        
    Returns:
        Path to transcript JSON file
        
    Raises:
        FileNotFoundError: If video file doesn't exist
        RuntimeError: If transcription fails
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video/audio file not found: {video_path}")
    
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "transcript.json")
    
    logger.info(f"Loading Faster-Whisper model: {model_size}")
    
    try:
        # Initialize Faster-Whisper model
        # device: "cpu" or "cuda" (auto-detected)
        # compute_type: "int8" for CPU (faster), "float16" for GPU
        # cpu_threads: number of threads for CPU inference (default: 0 = auto)
        # num_workers: number of workers for batching (improves speed)
        model = WhisperModel(
            model_size,
            device="cpu",  # Use "cuda" if GPU available
            compute_type="int8",  # Faster on CPU
            cpu_threads=4,  # Use 4 threads for parallel processing
            num_workers=1  # Single worker for sequential processing
        )
        
        logger.info(f"Transcribing: {video_path}")
        logger.info("Using multi-threaded inference for faster processing...")
        
        # Transcribe with word-level timestamps
        # beam_size: larger = more accurate but slower (5 is good balance)
        # vad_filter: Voice Activity Detection to skip silence
        # vad_parameters: tuned for better silence detection
        segments, info = model.transcribe(
            video_path,
            beam_size=5,
            word_timestamps=True,
            vad_filter=True,  # Skip silence for faster processing
            vad_parameters=dict(
                min_silence_duration_ms=500,  # Minimum silence to detect
                speech_pad_ms=400  # Padding around speech
            )
        )
        
        # Extract structured transcript data
        transcript_data = {
            "language": info.language,
            "language_probability": info.language_probability,
            "duration": info.duration,
            "segments": []
        }
        
        # Convert segments to our format (iterator needs to be consumed)
        logger.info("Processing transcription segments...")
        for segment in segments:
            segment_data = {
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip(),
                "words": []
            }
            
            # Include word-level data if available
            if hasattr(segment, 'words') and segment.words:
                for word in segment.words:
                    segment_data["words"].append({
                        "word": word.word.strip(),
                        "start": word.start,
                        "end": word.end,
                        "probability": word.probability
                    })
            
            transcript_data["segments"].append(segment_data)
        
        # Save transcript to JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(transcript_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Transcription completed: {len(transcript_data['segments'])} segments")
        logger.info(f"Language detected: {transcript_data['language']} "
                   f"(confidence: {transcript_data['language_probability']:.2f})")
        logger.info(f"Duration: {transcript_data['duration']:.2f}s")
        logger.info(f"Transcript saved to: {output_path}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"Transcription failed: {str(e)}")
        raise RuntimeError(f"Failed to transcribe video: {str(e)}")


def load_transcript(transcript_path: str) -> Dict:
    """
    Load transcript from JSON file.
    
    Args:
        transcript_path: Path to transcript JSON
        
    Returns:
        Transcript data dictionary
    """
    if not os.path.exists(transcript_path):
        raise FileNotFoundError(f"Transcript file not found: {transcript_path}")
    
    with open(transcript_path, 'r', encoding='utf-8') as f:
        return json.load(f)
