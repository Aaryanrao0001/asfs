"""Video overlay utilities for adding text (hook phrases) and logos to videos."""

import os
import subprocess
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def get_hook_position_coordinates(position: str, video_width: int = 1080, video_height: int = 1920) -> Tuple[str, str]:
    """
    Get FFmpeg drawtext coordinates for hook phrase position.
    
    Args:
        position: Position name (Top Left, Top Right, Bottom Left, Bottom Right, Top Center)
        video_width: Video width in pixels
        video_height: Video height in pixels
        
    Returns:
        Tuple of (x, y) coordinates as strings for FFmpeg
    """
    # Define margins
    margin_x = 40
    margin_y = 80
    
    positions = {
        "Top Left": (str(margin_x), str(margin_y)),
        "Top Right": (f"w-tw-{margin_x}", str(margin_y)),
        "Bottom Left": (str(margin_x), f"h-th-{margin_y}"),
        "Bottom Right": (f"w-tw-{margin_x}", f"h-th-{margin_y}"),
        "Top Center": ("(w-tw)/2", str(margin_y))
    }
    
    return positions.get(position, positions["Top Left"])


def get_system_font_path() -> str:
    """
    Get system font path for drawtext filter, with fallbacks for different OS.
    
    Returns:
        Path to a suitable font file, or empty string if none found
    """
    import sys
    import os
    
    # Try common font paths by OS
    if sys.platform == "win32":
        # Windows fonts
        candidates = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/verdana.ttf"
        ]
    elif sys.platform == "darwin":
        # macOS fonts
        candidates = [
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/SFNSDisplay.ttf"
        ]
    else:
        # Linux fonts
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"
        ]
    
    # Find first available font
    for font_path in candidates:
        if os.path.exists(font_path):
            return font_path
    
    # No font found - FFmpeg will use default
    logger.warning("No suitable font found, FFmpeg will use default font")
    return ""


def apply_video_overlays(
    input_video: str,
    output_video: str,
    hook_phrase: Optional[str] = None,
    hook_position: str = "Top Left",
    logo_path: Optional[str] = None
) -> bool:
    """
    Apply text overlay (hook phrase) and/or logo to a video.
    
    Args:
        input_video: Path to input video file
        output_video: Path to output video file
        hook_phrase: Text to overlay on video (optional)
        hook_position: Position for hook phrase
        logo_path: Path to logo image file (optional)
        
    Returns:
        True if successful, False otherwise
    """
    if not os.path.exists(input_video):
        logger.error(f"Input video not found: {input_video}")
        return False
    
    # If no overlays requested, just copy the file
    if not hook_phrase and not logo_path:
        logger.info("No overlays requested, returning original video")
        return True
    
    try:
        # Build FFmpeg filter chain
        filter_complex_parts = []
        input_count = 1
        
        # Add logo overlay if provided
        if logo_path and os.path.exists(logo_path):
            input_count = 2  # Main video + logo
            # Position logo at bottom center with margin
            logo_filter = f"[0:v][1:v]overlay=(W-w)/2:H-h-40"
            filter_complex_parts.append(logo_filter)
            logger.info(f"Adding logo overlay: {logo_path}")
        
        # Add text overlay if provided
        if hook_phrase:
            x, y = get_hook_position_coordinates(hook_position)
            
            # Escape special characters for FFmpeg
            escaped_text = hook_phrase.replace("'", "\\'").replace(":", "\\:")
            
            # Get system-appropriate font path
            font_path = get_system_font_path()
            
            # Build drawtext filter
            # Use bold font, white text with black shadow for readability
            text_filter = (
                f"drawtext=text='{escaped_text}'"
                f":x={x}:y={y}"
                f":fontsize=48"
                f":fontcolor=white"
                f":borderw=3"
                f":bordercolor=black"
            )
            
            # Add font path if available
            if font_path:
                text_filter += f":fontfile={font_path}"
            
            if filter_complex_parts:
                # Chain with previous filter
                filter_complex_parts.append(text_filter)
            else:
                filter_complex_parts.append(text_filter)
            
            logger.info(f"Adding text overlay: '{hook_phrase}' at {hook_position}")
        
        # Build FFmpeg command
        cmd = ['ffmpeg', '-y']
        
        # Input files
        cmd.extend(['-i', input_video])
        if logo_path and os.path.exists(logo_path):
            cmd.extend(['-i', logo_path])
        
        # Add filter complex if we have overlays
        if filter_complex_parts:
            if len(filter_complex_parts) == 2:
                # Both logo and text
                filter_complex = f"{filter_complex_parts[0]}[v1];[v1]{filter_complex_parts[1]}"
            else:
                # Just one overlay
                filter_complex = filter_complex_parts[0]
            
            cmd.extend(['-filter_complex', filter_complex])
        
        # Output options
        cmd.extend([
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-c:a', 'copy',  # Copy audio without re-encoding
            '-movflags', '+faststart',
            output_video
        ])
        
        logger.info(f"Applying overlays: {input_video} -> {output_video}")
        logger.debug(f"FFmpeg command: {' '.join(cmd)}")
        
        # Calculate timeout based on video size (minimum 5 minutes, add 1 min per 100MB)
        try:
            video_size_mb = os.path.getsize(input_video) / (1024 * 1024)
            timeout = max(300, 300 + int(video_size_mb / 100) * 60)  # 5min + 1min per 100MB
        except:
            timeout = 300
        
        # Execute FFmpeg
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        if result.returncode != 0:
            logger.error(f"FFmpeg failed: {result.stderr}")
            return False
        
        # Verify output exists
        if not os.path.exists(output_video):
            logger.error(f"Output video not created: {output_video}")
            return False
        
        file_size = os.path.getsize(output_video)
        logger.info(f"Overlays applied successfully: {output_video} ({file_size / (1024*1024):.2f} MB)")
        
        return True
        
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout applying overlays to {input_video}")
        return False
    except Exception as e:
        logger.error(f"Error applying overlays: {str(e)}")
        return False


def preprocess_video_for_upload(
    video_path: str,
    output_dir: str,
    metadata: dict
) -> Optional[str]:
    """
    Preprocess a video by applying overlays (hook phrase and logo) before upload.
    
    Args:
        video_path: Path to original video
        output_dir: Directory to save preprocessed video
        metadata: Dictionary containing hook_phrase, hook_position, logo_path
        
    Returns:
        Path to preprocessed video, or original video path if no preprocessing needed
    """
    hook_phrase = metadata.get("hook_phrase")
    hook_position = metadata.get("hook_position", "Top Left")
    logo_path = metadata.get("logo_path")
    
    # Check if any preprocessing is needed
    if not hook_phrase and not logo_path:
        logger.info("No preprocessing needed, using original video")
        return video_path
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output filename
    video_name = os.path.basename(video_path)
    name_without_ext = os.path.splitext(video_name)[0]
    output_path = os.path.join(output_dir, f"{name_without_ext}_processed.mp4")
    
    # Apply overlays
    success = apply_video_overlays(
        input_video=video_path,
        output_video=output_path,
        hook_phrase=hook_phrase,
        hook_position=hook_position,
        logo_path=logo_path
    )
    
    if success:
        return output_path
    else:
        logger.warning("Preprocessing failed, using original video")
        return video_path
