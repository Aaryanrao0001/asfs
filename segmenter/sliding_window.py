"""Sliding-window candidate generator for transcript segments.

Slides a variable-size window across the entire transcript in small steps so
that the best clips are never missed because they happen to fall between the
fixed batch boundaries used by the legacy sentence_window approach.
"""

import re
import logging
from typing import Dict, List, Optional

from .open_loop_detector import close_open_loops

logger = logging.getLogger(__name__)


def compute_pace(segment: Dict) -> float:
    """
    Calculate words per second for a transcript segment.

    Args:
        segment: A segment dict with at minimum "text", "start", and "end" keys.

    Returns:
        Words per second (float).  Returns 0.0 if duration is zero or negative.
    """
    text = segment.get("text", "")
    word_count = len(text.split())
    start = segment.get("start", 0.0)
    end = segment.get("end", 0.0)
    duration = end - start
    if duration <= 0:
        return 0.0
    return word_count / duration


def _snap_to_word_start(
    words: List[Dict], target_time: float, direction: str = "backward"
) -> float:
    """
    Snap a target time to the nearest word boundary.

    Args:
        words: List of word dicts with "start" and "end" keys (Whisper format).
        target_time: Desired boundary time in seconds.
        direction: "backward" to snap to the word that starts before target,
                   "forward" to snap to the word that ends after target.

    Returns:
        Snapped time value (seconds).
    """
    if not words:
        return target_time

    if direction == "backward":
        best = words[0]["start"]
        for w in words:
            if w["start"] <= target_time:
                best = w["start"]
        return best
    else:
        best = words[-1]["end"]
        for w in reversed(words):
            if w["end"] >= target_time:
                best = w["end"]
        return best


def _snaps_to_sentence_boundary(text: str, start: float, end: float, words: List[Dict]) -> float:
    """
    Calculate a boundary quality score for a candidate window.

    Returns:
        1.0 if the window starts at a sentence start (capital letter after
        terminal punctuation) and ends at a sentence end (.!?).
        0.5 otherwise.
    """
    stripped = text.strip()
    if not stripped:
        return 0.5

    # End quality: ends with terminal punctuation
    ends_ok = stripped[-1] in ".!?"

    # Start quality: first character is uppercase (approximates sentence start)
    starts_ok = stripped[0].isupper() if stripped else False

    return 1.0 if (starts_ok and ends_ok) else 0.5


def build_sliding_windows(
    transcript_data: Dict,
    min_duration: float = 20.0,
    max_duration: float = 55.0,
    step_seconds: float = 3.0,
) -> List[Dict]:
    """
    Slide a variable-size window across the entire transcript.

    Unlike the legacy sentence_window approach (which uses large jumps between
    windows), this function tests every position in small increments so the
    actual best clip is never skipped because of boundary misalignment.

    Steps:
    1. Run ``close_open_loops()`` on all segments to merge incomplete thoughts.
    2. Slide a window from start to finish in ``step_seconds`` increments.
    3. At each position, test multiple window sizes (min→max duration).
    4. Snap boundaries to exact word starts/ends when word-level timestamps
       are available.
    5. Each candidate is tagged with ``boundary_quality``, ``pace_wps``, and
       ``slow_start`` fields.

    Args:
        transcript_data: Transcript dict from transcribe.py, containing a
                         "segments" list.  Each segment may optionally contain
                         a "words" list of word-level timestamps.
        min_duration: Minimum candidate window duration in seconds.
        max_duration: Maximum candidate window duration in seconds.
        step_seconds: Increment between window start positions in seconds.

    Returns:
        List of candidate dicts, each with keys:
        start, end, duration, text, segment_count, type, boundary_quality,
        pace_wps, slow_start.
    """
    raw_segments = transcript_data.get("segments", [])
    if not raw_segments:
        logger.warning("build_sliding_windows: no segments in transcript")
        return []

    # Step 1: merge open loops
    segments = close_open_loops(raw_segments)

    if not segments:
        return []

    # Flatten all word-level timestamps for fast boundary snapping
    all_words: List[Dict] = []
    for seg in segments:
        all_words.extend(seg.get("words", []))

    total_start = segments[0]["start"]
    total_end = segments[-1]["end"]

    candidates: List[Dict] = []

    # Step 2 & 3: slide window
    window_start_time = total_start
    while window_start_time < total_end - min_duration:
        # Test multiple window sizes at this position
        window_end_time = window_start_time + min_duration

        while window_end_time <= window_start_time + max_duration and window_end_time <= total_end:
            duration = window_end_time - window_start_time

            # Collect segments that fall within this window
            window_segs = [
                s for s in segments
                if s["start"] < window_end_time and s["end"] > window_start_time
            ]

            if not window_segs:
                window_end_time += step_seconds
                continue

            # Determine actual start/end (clamp to segment boundaries)
            actual_start = max(window_start_time, window_segs[0]["start"])
            actual_end = min(window_end_time, window_segs[-1]["end"])

            # Step 4: snap to word-level boundaries if available
            if all_words:
                actual_start = _snap_to_word_start(all_words, actual_start, "backward")
                actual_end = _snap_to_word_start(all_words, actual_end, "forward")

            actual_duration = actual_end - actual_start
            if actual_duration < min_duration * 0.8:
                window_end_time += step_seconds
                continue

            # Build text from covered segments (partial coverage included)
            text_parts = []
            for seg in window_segs:
                seg_text = seg.get("text", "").strip()
                text_parts.append(seg_text)
            text = " ".join(text_parts).strip()

            if not text:
                window_end_time += step_seconds
                continue

            # Snap to nearest sentence boundaries in text
            # (snap start forward to first uppercase after a boundary)
            snapped_text = _try_snap_text_boundaries(text)

            # Boundary quality
            boundary_quality = _snaps_to_sentence_boundary(
                snapped_text, actual_start, actual_end, all_words
            )

            # Compute pace using first 5 seconds
            first_5s_words = [
                w for w in all_words
                if actual_start <= w.get("start", 0) < actual_start + 5.0
            ]
            first_5s_word_count = len(first_5s_words)
            pace_wps = first_5s_word_count / 5.0 if first_5s_word_count > 0 else (
                compute_pace({"text": text, "start": actual_start, "end": actual_end})
            )
            slow_start = pace_wps < 2.0

            # Overall pace (full window)
            overall_pace = compute_pace(
                {"text": text, "start": actual_start, "end": actual_end}
            )

            candidate = {
                "start": actual_start,
                "end": actual_end,
                "duration": actual_end - actual_start,
                "text": snapped_text,
                "segment_count": len(window_segs),
                "type": "sliding_window",
                "boundary_quality": boundary_quality,
                "pace_wps": overall_pace,
                "slow_start": slow_start,
            }
            candidates.append(candidate)

            window_end_time += step_seconds

        window_start_time += step_seconds

    logger.info(f"build_sliding_windows: generated {len(candidates)} raw candidates")
    return candidates


def _try_snap_text_boundaries(text: str) -> str:
    """
    Attempt to snap text to sentence boundaries.

    Trim leading text up to the first capital letter (that follows a space or
    is at position 0), and trim trailing text to the last terminal punctuation.

    Args:
        text: Raw text to snap.

    Returns:
        Text with best-effort sentence-boundary trimming.
    """
    if not text:
        return text

    # Snap start: find first capital letter (sentence start heuristic)
    match = re.search(r"(^|(?<=[.!?]\s))[A-Z]", text)
    if match:
        text = text[match.start():]

    # Snap end: trim to last terminal punctuation
    last_terminal = max(
        text.rfind("."),
        text.rfind("!"),
        text.rfind("?"),
    )
    if last_terminal > len(text) // 2:  # Only trim if punctuation is in second half
        text = text[: last_terminal + 1]

    return text.strip()


def deduplicate_windows(
    candidates: List[Dict],
    overlap_threshold: float = 0.7,
) -> List[Dict]:
    """
    Collapse highly-overlapping sliding-window candidates.

    If two candidates share more than ``overlap_threshold`` of their content
    duration, keep only the one with the better ``boundary_quality`` score.

    Args:
        candidates: List of candidate dicts from ``build_sliding_windows``.
        overlap_threshold: Fraction of shared duration above which two
                           candidates are considered duplicates (0.0–1.0).

    Returns:
        Deduplicated list of candidates.
    """
    if not candidates:
        return []

    # Sort by boundary_quality descending, then duration descending
    sorted_candidates = sorted(
        candidates,
        key=lambda c: (c.get("boundary_quality", 0.0), c.get("duration", 0.0)),
        reverse=True,
    )

    kept: List[Dict] = []

    for candidate in sorted_candidates:
        c_start = candidate["start"]
        c_end = candidate["end"]
        c_dur = c_end - c_start

        is_duplicate = False
        for kept_c in kept:
            k_start = kept_c["start"]
            k_end = kept_c["end"]
            k_dur = k_end - k_start

            overlap_start = max(c_start, k_start)
            overlap_end = min(c_end, k_end)
            overlap_dur = max(0.0, overlap_end - overlap_start)

            # Overlap as fraction of the shorter candidate
            min_dur = min(c_dur, k_dur) if min(c_dur, k_dur) > 0 else 1.0
            if overlap_dur / min_dur > overlap_threshold:
                is_duplicate = True
                break

        if not is_duplicate:
            kept.append(candidate)

    logger.info(
        f"deduplicate_windows: {len(candidates)} → {len(kept)} after deduplication"
    )
    return kept
