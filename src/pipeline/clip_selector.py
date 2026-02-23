"""
Clip Selector — final blended-score selection and FFmpeg clip export.

Selects the top macro candidates by ``blended_score`` and exports each as
an MP4 clip using FFmpeg (via ffmpeg-python).  Gracefully degrades when
FFmpeg is unavailable — returns selection metadata without exporting.

Activated only when ``ASFS_AUDIO_SCORING=true``.
"""

import logging
import os
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Guard for optional ffmpeg-python dependency.
try:
    import ffmpeg  # type: ignore

    _FFMPEG_AVAILABLE = True
except ImportError:
    _FFMPEG_AVAILABLE = False
    logger.debug("ffmpeg-python not installed; clip export will be skipped.")

# Default selection parameters.
DEFAULT_MAX_CLIPS = 5
DEFAULT_MIN_BLENDED_SCORE = 4.5


def select(
    scored_macros: List[Dict],
    max_clips: int = DEFAULT_MAX_CLIPS,
    min_score: float = DEFAULT_MIN_BLENDED_SCORE,
) -> List[Dict]:
    """
    Select the top macro candidates by blended score.

    Parameters
    ----------
    scored_macros : list[dict]
        Macro candidates enriched with ``blended_score`` (from macro_scorer).
    max_clips : int
        Maximum number of clips to select.
    min_score : float
        Minimum blended score threshold; candidates below this are excluded.

    Returns
    -------
    list[dict]
        Selected candidates sorted descending by ``blended_score``.
        Returns an empty list when no candidates pass the threshold.
    """
    if not scored_macros:
        return []

    passing = [m for m in scored_macros if m.get("blended_score", 0.0) >= min_score]
    passing.sort(key=lambda m: m["blended_score"], reverse=True)
    selected = passing[:max_clips]

    logger.info(
        "ClipSelector: %d/%d macro candidates selected (min_score=%.1f).",
        len(selected),
        len(scored_macros),
        min_score,
    )
    return selected


def export_clip(
    source_path: str,
    start: float,
    end: float,
    output_path: str,
) -> bool:
    """
    Export a clip from *source_path* between *start* and *end* seconds.

    Parameters
    ----------
    source_path : str
        Path to the source audio/video file.
    start : float
        Clip start time in seconds.
    end : float
        Clip end time in seconds.
    output_path : str
        Destination MP4 path.

    Returns
    -------
    bool
        ``True`` if export succeeded, ``False`` otherwise (including when
        ffmpeg-python is not installed).
    """
    if not _FFMPEG_AVAILABLE:
        logger.warning("ClipSelector: ffmpeg-python not available — export skipped.")
        return False

    if not os.path.exists(source_path):
        logger.error("ClipSelector: source file not found — %s", source_path)
        return False

    duration = end - start
    if duration <= 0:
        logger.error("ClipSelector: invalid clip duration (%.2f s).", duration)
        return False

    try:
        (
            ffmpeg
            .input(source_path, ss=start, t=duration)
            .output(output_path, vcodec="copy", acodec="copy")
            .overwrite_output()
            .run(quiet=True)
        )
        logger.info("ClipSelector: exported clip to %s (%.1f s).", output_path, duration)
        return True
    except Exception as exc:
        logger.error("ClipSelector: FFmpeg error — %s", exc)
        return False


def export_clips(
    selected: List[Dict],
    source_path: str,
    output_dir: str,
) -> List[Dict]:
    """
    Export all selected macro clips to *output_dir*.

    Parameters
    ----------
    selected : list[dict]
        Selected macro candidate dicts (from :func:`select`).
    source_path : str
        Path to the source audio/video file.
    output_dir : str
        Directory where exported clips are written.

    Returns
    -------
    list[dict]
        Each input dict enriched with:
        ``output_path``  – file path of the exported clip (str or None)
        ``exported``     – True if FFmpeg export succeeded
    """
    os.makedirs(output_dir, exist_ok=True)
    results = []
    for clip in selected:
        macro_id = clip.get("macro_id", 0)
        start = clip.get("start", 0.0)
        end = clip.get("end", 0.0)
        out_path = os.path.join(output_dir, f"clip_{macro_id:03d}.mp4")

        exported = export_clip(source_path, start, end, out_path)
        enriched = dict(clip)
        enriched["output_path"] = out_path if exported else None
        enriched["exported"] = exported
        results.append(enriched)

    return results
