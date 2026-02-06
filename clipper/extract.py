"""Extract video clips using FFmpeg."""

import os
import subprocess
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


def extract_clips(
    video_path: str,
    clips: List[Dict],
    output_dir: str
) -> List[Dict]:
    """
    Extract video clips using FFmpeg with platform-optimized settings.
    
    This function extracts clips from the source video and applies 9:16 aspect
    ratio conversion. By applying the crop here (instead of during normalization),
    we only process selected clips rather than the entire source video, which
    significantly improves performance for long videos.
    
    Args:
        video_path: Path to source video file
        clips: List of clip dictionaries with start, end, and metadata
        output_dir: Directory to save extracted clips
        
    Returns:
        List of clips with added 'file_path' field
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    extracted_clips = []
    
    for idx, clip in enumerate(clips):
        start_time = clip["start"]
        end_time = clip["end"]
        duration = end_time - start_time
        
        # Generate clip filename
        clip_id = f"clip_{idx + 1:03d}"
        output_filename = f"{clip_id}.mp4"
        output_path = os.path.join(output_dir, output_filename)
        
        logger.info(f"Extracting clip {idx + 1}/{len(clips)}: "
                   f"{start_time:.1f}s to {end_time:.1f}s ({duration:.1f}s)")
        
        # FFmpeg command for clip extraction
        # -ss before -i for faster seeking
        # Always re-encode for platform compatibility
        # Apply 9:16 vertical crop here (after segment selection)
        # This is more efficient than cropping the entire video during normalization
        cmd = [
            'ffmpeg',
            '-ss', str(start_time),
            '-i', video_path,
            '-t', str(duration),
            '-vf', 'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black',
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-c:a', 'aac',
            '-ar', '44100',
            '-ac', '2',
            '-movflags', '+faststart',
            '-y',
            output_path
        ]
        
        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout per clip
            )
            
            # Verify output file exists
            if not os.path.exists(output_path):
                logger.error(f"Clip file was not created: {output_path}")
                continue
            
            file_size = os.path.getsize(output_path)
            logger.info(f"Clip extracted: {output_filename} ({file_size / (1024*1024):.2f} MB)")
            
            # Add file path to clip data
            clip_with_path = {
                **clip,
                "clip_id": clip_id,
                "file_path": output_path,
                "file_size": file_size
            }
            
            extracted_clips.append(clip_with_path)
            
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout extracting clip {idx + 1}")
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg failed for clip {idx + 1}: {e.stderr}")
        except Exception as e:
            logger.error(f"Unexpected error extracting clip {idx + 1}: {str(e)}")
    
    logger.info(f"Successfully extracted {len(extracted_clips)}/{len(clips)} clips")
    
    return extracted_clips
