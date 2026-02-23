"""Server-side final score calculation. LLM never computes the final score."""

from scoring.config import WEIGHTS, HOOK_CAP, EMOTION_CAP, MAX_DURATION


def compute_final_score(data: dict, duration: float) -> int:
    """
    Compute the deterministic final viral score from component scores.

    Args:
        data: Dict containing hook_score, retention_score, emotion_score,
              completion_score, relatability_score, platform_fit_score (all 0-10).
        duration: Clip duration in seconds.

    Returns:
        Integer final score in range [0, 100].
    """
    score = (
        data["hook_score"] * WEIGHTS["hook"]
        + data["retention_score"] * WEIGHTS["retention"]
        + data["emotion_score"] * WEIGHTS["emotion"]
        + data["completion_score"] * WEIGHTS["completion"]
        + data["relatability_score"] * WEIGHTS["relatability"]
        + data["platform_fit_score"] * WEIGHTS["platform"]
    ) * 10

    # Override rules applied after base calculation
    if data["hook_score"] < HOOK_CAP:
        score = min(score, 45)

    if data["emotion_score"] < EMOTION_CAP:
        score = min(score, 45)

    if duration > MAX_DURATION:
        score -= 20

    return max(0, round(score))
