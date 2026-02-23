"""
Percentile Threshold Selector — replaces absolute score threshold.

Selects the top 15 % of candidate clips per source video, with:
- A hard floor of 4.5 absolute score (never select genuinely poor content).
- A minimum of 2 clips selected (with ``low_confidence`` flag if below threshold).
- A configurable maximum cap (default 5).
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

DEFAULT_MAX_CLIPS = 5
DEFAULT_MIN_CLIPS = 2
ABSOLUTE_FLOOR = 4.5
PERCENTILE_CUTOFF = 0.85  # top 15 %


def _percentile_value(scores: List[float], pct: float) -> float:
    """
    Compute the *pct*-th percentile of a sorted list of floats.

    Uses nearest-rank method.
    """
    if not scores:
        return 0.0
    sorted_scores = sorted(scores)
    idx = int(pct * (len(sorted_scores) - 1))
    return sorted_scores[idx]


def select_clips(
    candidates: List[Dict],
    score_key: str = "final_score",
    max_clips: int = DEFAULT_MAX_CLIPS,
    min_clips: int = DEFAULT_MIN_CLIPS,
    floor: float = ABSOLUTE_FLOOR,
    percentile: float = PERCENTILE_CUTOFF,
) -> List[Dict]:
    """
    Select clip candidates using percentile-based thresholding.

    Parameters
    ----------
    candidates : list[dict]
        Clip candidate dicts, each must have *score_key*.
    score_key : str
        Key used to read the score from each candidate.
    max_clips : int
        Maximum number of clips to return.
    min_clips : int
        Minimum clips to return (top-N by score), even if below percentile.
    floor : float
        Absolute score below which a candidate is never selected.
    percentile : float
        Percentile threshold (0–1).  ``0.85`` means top 15 %.

    Returns
    -------
    list[dict]
        Selected candidates sorted descending by score, each with
        ``low_confidence`` bool attached.
    """
    if not candidates:
        return []

    scores = [c.get(score_key, 0.0) for c in candidates]
    threshold = _percentile_value(scores, percentile)

    # Select candidates at or above the percentile threshold AND above the floor
    selected = [
        c for c in candidates
        if c.get(score_key, 0.0) >= threshold and c.get(score_key, 0.0) >= floor
    ]

    # Sort descending
    selected.sort(key=lambda c: c.get(score_key, 0.0), reverse=True)

    # Cap at max
    selected = selected[:max_clips]

    # If fewer than min_clips, fill from the top scoring candidates
    if len(selected) < min_clips:
        sorted_all = sorted(candidates, key=lambda c: c.get(score_key, 0.0), reverse=True)
        selected_scores = {c.get(score_key, 0.0) for c in selected}
        for c in sorted_all:
            if c not in selected and len(selected) < min_clips:
                c["low_confidence"] = True
                selected.append(c)

    # Mark confidence flag
    for c in selected:
        if "low_confidence" not in c:
            c["low_confidence"] = c.get(score_key, 0.0) < floor

    # Final sort
    selected.sort(key=lambda c: c.get(score_key, 0.0), reverse=True)

    logger.info(
        "Selector: %d/%d candidates selected (threshold=%.2f, floor=%.1f)",
        len(selected), len(candidates), threshold, floor,
    )

    return selected
