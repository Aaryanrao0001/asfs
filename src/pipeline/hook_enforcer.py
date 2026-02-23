"""
Hook Enforcement Module — 2-second hook detection and mid-segment recut.

Applied after clip selection, before packaging.
Ensures every clip has a strong interrupt signal within the first 2 seconds.
If no hook is found, attempts a mid-segment recut centered on the strongest
emotional/curiosity peak.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Filler tokens to ignore when checking for hook presence
FILLER_TOKENS = {"um", "uh", "so", "hey", "like", "well", "and", "but", "ok", "okay"}

# Emotional keywords that count as interrupt signals
EMOTION_KEYWORDS = {
    "shock": ["bankrupt", "died", "fired", "shocked", "insane", "crazy", "unbelievable"],
    "anger": ["wrong", "lied", "scam", "fraud", "terrible", "worst", "hate"],
    "vulnerability": ["failed", "broke", "cried", "lost", "alone", "scared", "afraid"],
    "curiosity": ["secret", "truth", "nobody", "never", "myth", "hidden", "actually"],
}

# Flattened set for fast lookup
_ALL_EMOTION_WORDS = {w for words in EMOTION_KEYWORDS.values() for w in words}

# Minimum and maximum clip durations after recut
MIN_CLIP_DURATION = 15.0
MAX_CLIP_DURATION = 26.0
PREFERRED_MIN_DURATION = 18.0

# Hook detection window
HOOK_WINDOW = 2.0
PRE_HOOK_BUFFER = 1.6
MIN_SEGMENT_FOR_RECUT = 10.0


def _has_interrupt_signal(tokens: List[Dict], window_end: float = 2.0) -> bool:
    """
    Check whether any interrupt signal fires before *window_end* seconds.

    An interrupt signal is:
    - A question mark in the text
    - An emotional keyword
    - A non-filler first token appearing before t=1.5s
    """
    for token in tokens:
        t_start = token.get("start", 0.0)
        if t_start >= window_end:
            break
        text = token.get("text", "").strip().lower()
        words = re.findall(r"[a-z']+", text)

        # Question mark → interrupt
        if "?" in token.get("text", ""):
            return True

        # Emotional keyword → interrupt
        for w in words:
            if w in _ALL_EMOTION_WORDS:
                return True

        # Non-filler first token before 1.5s
        if t_start < 1.5:
            non_filler = [w for w in words if w not in FILLER_TOKENS]
            if non_filler:
                return True

    return False


def _score_window(tokens: List[Dict], center: float, window: float = 1.0) -> float:
    """
    Score a 1-second window around *center* by counting curiosity + emotion cues.
    """
    score = 0.0
    for token in tokens:
        t = token.get("start", 0.0)
        if abs(t - center) > window:
            continue
        text = token.get("text", "").strip().lower()
        words = re.findall(r"[a-z']+", text)
        for w in words:
            if w in _ALL_EMOTION_WORDS:
                score += 2.0
        if "?" in token.get("text", ""):
            score += 1.5
    return score


def _find_best_peak(tokens: List[Dict], segment_duration: float) -> Optional[float]:
    """
    Scan the full segment in 1-second windows and return the timestamp of the
    highest curiosity + emotion peak.

    When multiple peaks are within 3s of each other, selects the one with the
    highest combined score (not just the first).
    """
    if not tokens:
        return None

    best_time = None
    best_score = 0.0
    step = 1.0

    t = 0.0
    while t <= segment_duration:
        s = _score_window(tokens, t, window=1.0)
        if s > best_score:
            best_score = s
            best_time = t
        t += step

    return best_time if best_score > 0 else None


def enforce_hook(
    segment: Dict,
    transcript_tokens: List[Dict],
    segment_start: float,
    segment_end: float,
) -> Dict:
    """
    Apply 2-second hook enforcement to a clip segment.

    Parameters
    ----------
    segment : dict
        The clip candidate dict.  Modified in-place and returned.
    transcript_tokens : list[dict]
        Word-level transcript tokens with ``start``, ``end``, ``text`` keys.
    segment_start : float
        Start time of the selected segment in the source media.
    segment_end : float
        End time of the selected segment in the source media.

    Returns
    -------
    dict
        The segment dict with ``hook_metadata`` attached.
    """
    segment_duration = segment_end - segment_start

    # Tokens within this segment
    seg_tokens = [
        t for t in transcript_tokens
        if segment_start <= t.get("start", 0.0) < segment_end
    ]

    hook_metadata: Dict = {
        "hook_found": False,
        "hook_timestamp": 0.0,
        "recut_applied": False,
        "recut_source": None,
    }

    # --- Check first 2 seconds ---
    first_2s_tokens = [
        t for t in seg_tokens
        if (t.get("start", 0.0) - segment_start) < HOOK_WINDOW
    ]

    if _has_interrupt_signal(first_2s_tokens, window_end=HOOK_WINDOW):
        hook_metadata["hook_found"] = True
        hook_metadata["hook_timestamp"] = segment_start
        segment["hook_metadata"] = hook_metadata
        return segment

    # --- Segment too short for recut ---
    if segment_duration < MIN_SEGMENT_FOR_RECUT:
        hook_metadata["hook_found"] = False
        segment["hook_metadata"] = hook_metadata
        return segment

    # --- Scan for best peak (offset relative to segment start) ---
    peak_offset = _find_best_peak(seg_tokens, segment_duration)

    if peak_offset is None:
        hook_metadata["hook_found"] = False
        segment["recut_failed"] = True
        segment["hook_metadata"] = hook_metadata
        return segment

    # Compute new start: pre-hook buffer before peak
    new_start = segment_start + peak_offset - PRE_HOOK_BUFFER
    new_start = max(new_start, segment_start)  # clamp to segment start

    # Compute new end: preferred duration from new_start, clamped
    new_end = new_start + MAX_CLIP_DURATION
    if new_end > segment_end:
        new_end = segment_end
    # Ensure minimum duration
    if (new_end - new_start) < MIN_CLIP_DURATION:
        # Try extending from peak
        new_start = max(segment_start, new_end - PREFERRED_MIN_DURATION)

    hook_metadata["hook_found"] = True
    hook_metadata["hook_timestamp"] = segment_start + peak_offset
    hook_metadata["recut_applied"] = True
    hook_metadata["recut_source"] = "mid_segment"

    segment["start"] = new_start
    segment["end"] = new_end
    segment["hook_metadata"] = hook_metadata

    logger.info(
        "Recut applied: new window %.1f–%.1f (peak at %.1f)",
        new_start, new_end, segment_start + peak_offset,
    )

    return segment
