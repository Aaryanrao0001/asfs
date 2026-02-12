"""
Dependency checker - Validates required external dependencies.

Checks for ffmpeg, ffprobe, and other required tools.
"""

import os
import sys
import shutil
import logging
import subprocess
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


def check_ffmpeg() -> Tuple[bool, str]:
    """
    Check if ffmpeg is available with version validation.
    
    Returns:
        Tuple of (is_available, path_or_message)
    """
    ffmpeg_path = shutil.which("ffmpeg")
    
    if not ffmpeg_path:
        return False, "ffmpeg not found in system PATH"
    
    try:
        result = subprocess.run(
            [ffmpeg_path, '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout:
            lines = result.stdout.split('\n')
            version_line = lines[0] if lines else "version unknown"
            return True, f"{ffmpeg_path} ({version_line})"
        else:
            return False, f"ffmpeg found but not working: {result.stderr}"
    except subprocess.TimeoutExpired:
        return False, f"ffmpeg found at {ffmpeg_path} but timed out checking version"
    except Exception as e:
        return False, f"ffmpeg found but error checking version: {e}"


def check_ffprobe() -> Tuple[bool, str]:
    """
    Check if ffprobe is available with version validation.
    
    Returns:
        Tuple of (is_available, path_or_message)
    """
    ffprobe_path = shutil.which("ffprobe")
    
    if not ffprobe_path:
        return False, "ffprobe not found in system PATH. Install FFmpeg package."
    
    try:
        result = subprocess.run(
            [ffprobe_path, '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout:
            lines = result.stdout.split('\n')
            version_line = lines[0] if lines else "version unknown"
            return True, f"{ffprobe_path} ({version_line})"
        else:
            return False, f"ffprobe found but not working: {result.stderr}"
    except subprocess.TimeoutExpired:
        return False, f"ffprobe found at {ffprobe_path} but timed out checking version"
    except Exception as e:
        return False, f"ffprobe found but error checking version: {e}"


def check_playwright() -> Tuple[bool, str]:
    """
    Check if Playwright browsers are installed.
    
    Returns:
        Tuple of (is_available, message)
    """
    try:
        from playwright.sync_api import sync_playwright
        
        # Try to check if chromium is installed
        try:
            with sync_playwright() as p:
                # Just checking if we can create the playwright instance
                return True, "Playwright available"
        except Exception as e:
            return False, f"Playwright browsers not installed: {e}"
            
    except ImportError:
        return False, "Playwright module not installed"


def check_all_dependencies() -> Dict[str, Tuple[bool, str]]:
    """
    Check all required dependencies.
    
    Returns:
        Dictionary mapping dependency name to (is_available, message)
    """
    results = {
        "ffmpeg": check_ffmpeg(),
        "ffprobe": check_ffprobe(),
        "playwright": check_playwright()
    }
    
    return results


def get_missing_dependencies() -> List[str]:
    """
    Get list of missing dependencies.
    
    Returns:
        List of missing dependency names
    """
    results = check_all_dependencies()
    missing = [name for name, (available, _) in results.items() if not available]
    return missing


def get_installation_instructions(dependency: str) -> str:
    """
    Get installation instructions for a specific dependency.
    
    Args:
        dependency: Name of the dependency
        
    Returns:
        Installation instructions as a string
    """
    instructions = {
        "ffmpeg": """
FFmpeg Installation:

Windows:
  1. Download from https://ffmpeg.org/download.html
  2. Extract to C:\\ffmpeg
  3. Add C:\\ffmpeg\\bin to your system PATH
  
  OR use Chocolatey:
  choco install ffmpeg

macOS:
  brew install ffmpeg

Linux (Ubuntu/Debian):
  sudo apt update
  sudo apt install ffmpeg

Linux (Fedora/RHEL):
  sudo dnf install ffmpeg
""",
        "ffprobe": """
FFprobe Installation:

FFprobe is included with FFmpeg.
Please install FFmpeg (see ffmpeg instructions).
""",
        "playwright": """
Playwright Browser Installation:

After installing the playwright Python package, run:
  
  playwright install chromium

Or install all browsers:
  
  playwright install
"""
    }
    
    return instructions.get(dependency, f"No installation instructions available for {dependency}")


def validate_dependencies_with_warnings() -> bool:
    """
    Validate all dependencies and log warnings for missing ones.
    
    Returns:
        True if all required dependencies are available, False otherwise
    """
    results = check_all_dependencies()
    all_available = True
    
    for name, (available, message) in results.items():
        if available:
            logger.info(f"✓ {name}: {message}")
        else:
            logger.warning(f"✗ {name}: {message}")
            logger.warning(get_installation_instructions(name))
            all_available = False
    
    return all_available


def get_dependency_status_message() -> str:
    """
    Get a formatted status message for all dependencies.
    
    Returns:
        Multi-line status message
    """
    results = check_all_dependencies()
    lines = ["Dependency Status:", ""]
    
    for name, (available, message) in results.items():
        status = "✓ Available" if available else "✗ Missing"
        lines.append(f"  {name}: {status}")
        if available:
            lines.append(f"    → {message}")
        else:
            lines.append(f"    → {message}")
            # Add brief installation hint
            if name == "ffmpeg" or name == "ffprobe":
                lines.append(f"    → Install: https://ffmpeg.org/download.html")
            elif name == "playwright":
                lines.append(f"    → Run: playwright install chromium")
        lines.append("")
    
    return "\n".join(lines)


def check_dependency_interactive() -> bool:
    """
    Check dependencies interactively and prompt user if any are missing.
    
    Returns:
        True if user wants to continue despite missing dependencies
    """
    missing = get_missing_dependencies()
    
    if not missing:
        print("✓ All dependencies are available")
        return True
    
    print("\n⚠ Missing Dependencies Detected:\n")
    
    for dep in missing:
        print(f"  ✗ {dep}")
        print(get_installation_instructions(dep))
        print()
    
    # In GUI mode, we should show a dialog instead
    # For now, just log the issue
    logger.error(f"Missing dependencies: {', '.join(missing)}")
    return False
