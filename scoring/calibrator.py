"""Server-side final score calculation. LLM never computes the final score."""

from typing import Dict
from scoring.config import WEIGHTS, HOOK_CAP, EMOTION_CAP, MAX_DURATION

# Position multipliers — higher weight for signals that matter most in the first few seconds
POSITION_WEIGHTS = {
    "hook": 1.5,        # First 3 seconds matter most
    "retention": 1.2,   # Keep-watching signal
    "emotion": 1.0,
    "completion": 1.0,
    "relatability": 1.0,
    "platform": 1.0,
}


def peak_density_bonus(scores: Dict) -> float:
    """
    Award a bonus when multiple component scores are strong simultaneously.

    Clips with several high scores across dimensions outperform clips that
    excel in only one dimension.

    Args:
        scores: Dict containing the component scores (0-10 scale).

    Returns:
        Bonus points to add to the final score (0, 1, 3, or 5).
    """
    component_keys = [
        "hook_score", "retention_score", "emotion_score",
        "completion_score", "relatability_score", "platform_fit_score",
    ]
    strong_count = sum(
        1 for key in component_keys if scores.get(key, 0) >= 7.0
    )
    if strong_count >= 4:
        return 5.0
    if strong_count == 3:
        return 3.0
    if strong_count == 2:
        return 1.0
    return 0.0


def compute_final_score(data: dict, duration: float) -> int:
    """
    Compute the deterministic final viral score from component scores.

    Applies position multipliers (hook×1.5, retention×1.2) and a peak density
    bonus when multiple component scores are strong.

    Args:
        data: Dict containing hook_score, retention_score, emotion_score,
              completion_score, relatability_score, platform_fit_score (all 0-10).
        duration: Clip duration in seconds.

    Returns:
        Integer final score in range [0, 100].
    """
    score = (
        data["hook_score"] * WEIGHTS["hook"] * POSITION_WEIGHTS["hook"]
        + data["retention_score"] * WEIGHTS["retention"] * POSITION_WEIGHTS["retention"]
        + data["emotion_score"] * WEIGHTS["emotion"] * POSITION_WEIGHTS["emotion"]
        + data["completion_score"] * WEIGHTS["completion"] * POSITION_WEIGHTS["completion"]
        + data["relatability_score"] * WEIGHTS["relatability"] * POSITION_WEIGHTS["relatability"]
        + data["platform_fit_score"] * WEIGHTS["platform"] * POSITION_WEIGHTS["platform"]
    ) * 10

    # Peak density bonus
    score += peak_density_bonus(data)

    # Override rules applied after base calculation
    if data["hook_score"] < HOOK_CAP:
        score = min(score, 45)

    if data["emotion_score"] < EMOTION_CAP:
        score = min(score, 45)

    if duration > MAX_DURATION:
        score -= 20

    return max(0, round(score))
