"""
Micro Segmenter — sliding word-boundary window segmentation.

Produces overlapping micro-segments from a word-timestamp list using a
configurable window size (default 5 s) and hop size (default 2.5 s), aligned
to actual word boundaries so that no word is split mid-utterance.

All segmentation logic is deterministic and requires only the standard library.
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

# Default window and hop lengths in seconds.
DEFAULT_WINDOW_SEC = 5.0
DEFAULT_HOP_SEC = 2.5

# Minimum words required for a segment to be considered viable.
MIN_WORDS_PER_SEGMENT = 3


def segment(
    words: List[Dict],
    window_sec: float = DEFAULT_WINDOW_SEC,
    hop_sec: float = DEFAULT_HOP_SEC,
) -> List[Dict]:
    """
    Produce overlapping micro-segments aligned to word boundaries.

    Parameters
    ----------
    words : list[dict]
        Word dicts with ``{"word": str, "start": float, "end": float}``.
    window_sec : float
        Length of each segment window in seconds.
    hop_sec : float
        Step between consecutive window start times in seconds.

    Returns
    -------
    list[dict]
        Each item has:
        ``words``      – list of word dicts in this window
        ``text``       – concatenated word text
        ``start``      – actual start time of first word (float)
        ``end``        – actual end time of last word (float)
        ``duration``   – end - start (float)
        ``segment_id`` – 1-based integer index
    """
    if not words:
        logger.warning("MicroSegmenter: empty word list — returning no segments.")
        return []

    total_duration = words[-1]["end"]
    if total_duration <= 0:
        return []

    segments: List[Dict] = []
    window_start = 0.0
    seg_id = 1

    while window_start < total_duration:
        window_end = window_start + window_sec

        # Find word indices that fall within [window_start, window_end)
        seg_words = [
            w for w in words
            if w["start"] >= window_start and w["start"] < window_end
        ]

        if len(seg_words) >= MIN_WORDS_PER_SEGMENT:
            actual_start = seg_words[0]["start"]
            actual_end = seg_words[-1]["end"]
            text = " ".join(w["word"] for w in seg_words)
            segments.append(
                {
                    "segment_id": seg_id,
                    "words": seg_words,
                    "text": text,
                    "start": actual_start,
                    "end": actual_end,
                    "duration": round(actual_end - actual_start, 4),
                }
            )
            seg_id += 1
        else:
            logger.debug(
                "MicroSegmenter: window %.1f–%.1f has only %d words (< %d) — skipped.",
                window_start,
                window_end,
                len(seg_words),
                MIN_WORDS_PER_SEGMENT,
            )

        window_start += hop_sec

    logger.info("MicroSegmenter: produced %d micro-segments.", len(segments))
    return segments
