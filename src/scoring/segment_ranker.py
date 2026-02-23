"""
Segment Ranker — deterministic weighted score ranking with hard thresholding.

Combines LLM component scores (from batch_scorer) with audio features
(from feature_extractor) into a single composite score, then filters and
ranks segments.

Formula::

    audio_bonus = clamp((mean_rms / HIGH_ENERGY_THRESHOLD), 0, 1) * AUDIO_ENERGY_WEIGHT
                + clamp(1 - silence_ratio, 0, 1) * AUDIO_SILENCE_WEIGHT
                + clamp(speech_rate / HIGH_SPEECH_RATE_WPS, 0, 1) * AUDIO_RATE_WEIGHT

    text_score  = compute_final_score_v2(component_scores, platform)

    composite   = text_score * TEXT_WEIGHT + audio_bonus * 10 * AUDIO_WEIGHT

All final scores are deterministic — the LLM does not influence the formula.
"""

import logging
from typing import Dict, List

from src.prompts.scoring_v2 import compute_final_score_v2

logger = logging.getLogger(__name__)

# Composite weight split between text-based and audio-based scores.
TEXT_WEIGHT = 0.7
AUDIO_WEIGHT = 0.3

# Audio sub-weights (must sum to 1.0).
AUDIO_ENERGY_WEIGHT = 0.5
AUDIO_SILENCE_WEIGHT = 0.3
AUDIO_RATE_WEIGHT = 0.2

assert (
    abs(AUDIO_ENERGY_WEIGHT + AUDIO_SILENCE_WEIGHT + AUDIO_RATE_WEIGHT - 1.0) < 1e-9
), "AUDIO_*_WEIGHT constants must sum to 1.0"

# Normalisation references for audio features.
HIGH_ENERGY_THRESHOLD = 0.1   # RMS value considered "high energy"
HIGH_SPEECH_RATE_WPS = 4.0    # words/sec considered fast delivery

# Minimum composite score required to pass hard threshold.
HARD_THRESHOLD = 4.5

# Default audio feature values used when audio is not viable.
_DEFAULT_AUDIO = {"mean_rms": 0.0, "silence_ratio": 0.5, "speech_rate": 2.0, "viable": False}


def _audio_bonus(features: Dict) -> float:
    """
    Compute normalised audio bonus in [0, 1].

    Parameters
    ----------
    features : dict
        Audio feature dict (from :func:`src.audio.feature_extractor.extract_features`).

    Returns
    -------
    float
        Audio bonus in [0, 1].
    """
    energy_score = min(features.get("mean_rms", 0.0) / HIGH_ENERGY_THRESHOLD, 1.0)
    silence_score = max(0.0, 1.0 - features.get("silence_ratio", 0.5))
    rate_score = min(features.get("speech_rate", 0.0) / HIGH_SPEECH_RATE_WPS, 1.0)

    return (
        energy_score * AUDIO_ENERGY_WEIGHT
        + silence_score * AUDIO_SILENCE_WEIGHT
        + rate_score * AUDIO_RATE_WEIGHT
    )


def compute_composite_score(
    component_scores: Dict,
    audio_features: Dict,
    platform: str = "tiktok",
) -> float:
    """
    Combine text component scores and audio features into a composite score.

    Parameters
    ----------
    component_scores : dict
        LLM component score dict (from batch_scorer output).
    audio_features : dict
        Audio feature dict (from feature_extractor output).
    platform : str
        Target platform for controversy weighting.

    Returns
    -------
    float
        Composite score (not clamped — typically in 0–10 range).
    """
    text_score = compute_final_score_v2(component_scores, platform)
    bonus = _audio_bonus(audio_features)
    composite = text_score * TEXT_WEIGHT + bonus * 10.0 * AUDIO_WEIGHT
    return round(composite, 4)


def rank(
    scored_segments: List[Dict],
    platform: str = "tiktok",
    threshold: float = HARD_THRESHOLD,
) -> List[Dict]:
    """
    Compute composite scores, apply hard threshold, and return sorted segments.

    Parameters
    ----------
    scored_segments : list[dict]
        Segment dicts enriched with LLM component scores (from batch_scorer)
        and optionally with ``audio_features`` nested dict.
    platform : str
        Target platform.
    threshold : float
        Minimum composite score; segments below this are excluded.

    Returns
    -------
    list[dict]
        Segments that pass the threshold, sorted descending by
        ``composite_score``.  Each segment gains a ``composite_score`` key.
    """
    results = []
    for seg in scored_segments:
        audio = seg.get("audio_features", _DEFAULT_AUDIO)
        score = compute_composite_score(seg, audio, platform)
        enriched = dict(seg)
        enriched["composite_score"] = score
        results.append(enriched)

    # Hard threshold filter.
    passing = [s for s in results if s["composite_score"] >= threshold]

    # Sort descending.
    passing.sort(key=lambda s: s["composite_score"], reverse=True)

    logger.info(
        "SegmentRanker: %d/%d segments passed threshold %.1f.",
        len(passing),
        len(results),
        threshold,
    )
    return passing
