"""
Scoring Prompt v2 — adds controversy_score and novelty_score.

Provides:
- Updated prompt template requesting the two new component scores.
- Deterministic final score calculation that replaces the legacy calibrator
  for v2 pipeline use.
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)

# Platform-specific controversy weight
PLATFORM_CONTROVERSY_WEIGHT: Dict[str, float] = {
    "tiktok": 0.3,
    "reels": 0.2,
    "shorts": 0.1,
}

# Base component weights (same as legacy, used for weighted average)
BASE_WEIGHTS: Dict[str, float] = {
    "hook_score": 0.35,
    "retention_score": 0.25,
    "emotion_score": 0.20,
    "relatability_score": 0.10,
    "completion_score": 0.05,
    "platform_fit_score": 0.05,
}

SCORING_V2_PROMPT_SUFFIX = """

ADDITIONAL COMPONENT SCORES (return these alongside the standard scores):

- "controversy_score" (0-10): Rate the level of controversial or debate-provoking
  content.  Look for: absolute language ("not", "never", "myth", "they lied",
  "everyone is wrong"), identity anchors ("if you eat breakfast"), direct
  challenges to common beliefs, and moral framing.

- "novelty_score" (0-10): Rate how novel or unexpected the content is.
  Look for: rare phrasing, unexpected topic angles, counter-intuitive statements,
  or information that challenges conventional wisdom in a surprising way.

- "suggested_title": A short (max 6 words) punchy headline for the clip overlay.

Return ONLY valid JSON. No markdown. No explanation. No preamble.
"""


def build_scoring_v2_prompt(segments, base_criteria: str = "") -> str:
    """
    Build a v2 scoring prompt that requests controversy_score and novelty_score.

    Parameters
    ----------
    segments : list[dict]
        Segment dicts with ``text`` and ``duration``.
    base_criteria : str
        Optional base criteria text from prompt template.

    Returns
    -------
    str
        The full prompt string.
    """
    segment_blocks = []
    for i, seg in enumerate(segments, 1):
        segment_blocks.append(
            f"\n\n━━━ SEGMENT {i} ━━━\n"
            f"Text: {seg['text']}\n"
            f"Duration: {seg['duration']:.1f}s\n"
        )

    return (
        f"Score the following {len(segments)} video segment(s) using the criteria below.\n\n"
        f"{base_criteria}\n"
        f"{''.join(segment_blocks)}\n\n"
        "Return JSON with an array of component scores ONLY "
        "(do NOT compute final_score or verdict — those are calculated server-side):\n"
        "{\n"
        '  "segments": [\n'
        "    {\n"
        '      "segment_id": 1,\n'
        '      "hook_score": <0-10>,\n'
        '      "retention_score": <0-10>,\n'
        '      "emotion_score": <0-10>,\n'
        '      "relatability_score": <0-10>,\n'
        '      "completion_score": <0-10>,\n'
        '      "platform_fit_score": <0-10>,\n'
        '      "controversy_score": <0-10>,\n'
        '      "novelty_score": <0-10>,\n'
        '      "suggested_title": "max 6 words",\n'
        '      "key_strengths": ["strength 1"],\n'
        '      "key_weaknesses": ["weakness 1"],\n'
        '      "first_3_seconds": "exact quote",\n'
        '      "primary_emotion": "neutral",\n'
        '      "optimal_platform": "tiktok"\n'
        "    }\n"
        "  ]\n"
        "}\n"
        + SCORING_V2_PROMPT_SUFFIX
    )


def compute_final_score_v2(
    data: Dict,
    platform: str = "tiktok",
) -> float:
    """
    Deterministic v2 final score calculation.

    Formula::

        base = weighted_avg(hook, retention, emotion, relatability, completion, platform_fit)
        platform_boost = controversy_score * platform_controversy_weight[platform]
        novelty_multiplier = 1.0 + (novelty_score / 100)
        final_score = (base + platform_boost) * novelty_multiplier

    Parameters
    ----------
    data : dict
        Component scores (all 0–10).
    platform : str
        Target platform (``tiktok``, ``reels``, ``shorts``).

    Returns
    -------
    float
        Final score (not clamped — caller decides rounding / capping).
    """
    base = sum(
        data.get(field, 0.0) * weight
        for field, weight in BASE_WEIGHTS.items()
    )

    controversy = data.get("controversy_score", 0.0)
    novelty = data.get("novelty_score", 0.0)

    pcw = PLATFORM_CONTROVERSY_WEIGHT.get(platform.lower(), 0.1)
    platform_boost = controversy * pcw
    novelty_multiplier = 1.0 + (novelty / 100.0)

    final = (base + platform_boost) * novelty_multiplier
    return round(final, 4)
