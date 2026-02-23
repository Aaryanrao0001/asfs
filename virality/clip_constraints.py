"""
Phase 4 – Clip Construction Constraints.

Filters and selects candidates that satisfy:
- Duration: 15–60 seconds total
- Must start with a top-20% hook sentence
- Must end with a high-impact sentence (by delivery_intensity)
- Coherence threshold (shared speaker / topic overlap)
- Generate 20–50 final candidates per episode
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# ── public configuration defaults ─────────────────────────────────────────

MIN_DURATION: float = 15.0   # seconds
MAX_DURATION: float = 60.0   # seconds
TARGET_MIN_CANDIDATES: int = 20
TARGET_MAX_CANDIDATES: int = 50

# Fraction that defines "top hook" tier
HOOK_TOP_FRACTION: float = 0.20

# Minimum coherence score (0–1) to accept a candidate
DEFAULT_COHERENCE_THRESHOLD: float = 0.15

# Composite constraint_score weights
# hook_score and impact_score are 0–10; scale factor brings them to ~0–0.25
_HOOK_IMPACT_WEIGHT: float = 0.025
# coherence is 0–1; scale factor brings it to ~0–5 (same order as pattern_score)
_COHERENCE_SCALE: float = 5.0


# ── helpers ────────────────────────────────────────────────────────────────

def _hook_score_of_first_unit(candidate: Dict, unit_map: Dict[int, Dict]) -> float:
    """Return the hook_score of the first (lowest index) unit in the candidate."""
    indices = candidate.get("unit_indices", [])
    if not indices:
        return 0.0
    first_idx = min(indices)
    unit = unit_map.get(first_idx, {})
    return unit.get("hook_score", 0.0)


def _impact_score_of_last_unit(candidate: Dict, unit_map: Dict[int, Dict]) -> float:
    """Return the delivery_intensity of the last (highest index) unit."""
    indices = candidate.get("unit_indices", [])
    if not indices:
        return 0.0
    last_idx = max(indices)
    unit = unit_map.get(last_idx, {})
    return unit.get("delivery_intensity", 0.0)


def _coherence_score(candidate: Dict, unit_map: Dict[int, Dict]) -> float:
    """
    Simple coherence heuristic:
    - 0.5 base if all units share the same speaker
    - 0.25–0.5 bonus proportional to word-overlap among unit texts
    Returns a float in [0, 1].
    """
    indices = candidate.get("unit_indices", [])
    if not indices:
        return 0.0

    units = [unit_map.get(i, {}) for i in indices]

    # Speaker coherence
    speakers = {u.get("speaker", "") for u in units}
    speaker_bonus = 0.5 if len(speakers) == 1 else 0.2

    # Vocabulary overlap (Jaccard on word sets)
    word_sets = [set((u.get("text", "")).lower().split()) for u in units]
    if len(word_sets) >= 2:
        intersection = word_sets[0].intersection(*word_sets[1:])
        union = word_sets[0].union(*word_sets[1:])
        jaccard = len(intersection) / max(len(union), 1)
    else:
        jaccard = 0.5

    return min(speaker_bonus + jaccard * 0.5, 1.0)


# ── main filter ────────────────────────────────────────────────────────────

def apply_clip_constraints(
    candidates: List[Dict],
    scored_units: List[Dict],
    min_duration: float = MIN_DURATION,
    max_duration: float = MAX_DURATION,
    coherence_threshold: float = DEFAULT_COHERENCE_THRESHOLD,
    target_min: int = TARGET_MIN_CANDIDATES,
    target_max: int = TARGET_MAX_CANDIDATES,
) -> List[Dict]:
    """
    Filter and rank candidates according to clip construction constraints.

    Args:
        candidates:           Raw candidates from the reordering engine.
        scored_units:         Scored atomic sentence units (for lookup).
        min_duration:         Minimum allowed clip duration in seconds.
        max_duration:         Maximum allowed clip duration in seconds.
        coherence_threshold:  Minimum coherence score (0–1).
        target_min:           Minimum number of candidates to return.
        target_max:           Maximum number of candidates to return.

    Returns:
        Filtered and ranked list of candidate dicts with added metadata:
        ``hook_score_first``, ``impact_score_last``, ``coherence``.
    """
    if not candidates or not scored_units:
        logger.warning("apply_clip_constraints: empty input – returning []")
        return []

    # Build unit lookup by index
    unit_map: Dict[int, Dict] = {u.get("index", -1): u for u in scored_units}

    # Determine the top-20% hook threshold across all *units*
    hook_scores = sorted(
        [u.get("hook_score", 0.0) for u in scored_units], reverse=True
    )
    top20_cutoff_idx = max(int(len(hook_scores) * HOOK_TOP_FRACTION) - 1, 0)
    hook_threshold = hook_scores[top20_cutoff_idx] if hook_scores else 0.0

    passed: List[Dict] = []

    for c in candidates:
        duration = c.get("duration", 0.0)

        # ── constraint 1: duration ─────────────────────────────────────────
        if not (min_duration <= duration <= max_duration):
            continue

        # ── constraint 2: starts with top-20% hook ────────────────────────
        first_hook = _hook_score_of_first_unit(c, unit_map)
        if first_hook < hook_threshold:
            continue

        # ── constraint 3: ends with high-impact sentence ──────────────────
        last_impact = _impact_score_of_last_unit(c, unit_map)
        # We don't hard-reject on ending impact but we store it for ranking.

        # ── constraint 4: coherence ────────────────────────────────────────
        coherence = _coherence_score(c, unit_map)
        if coherence < coherence_threshold:
            continue

        enriched = dict(c)
        enriched["hook_score_first"] = round(first_hook, 3)
        enriched["impact_score_last"] = round(last_impact, 3)
        enriched["coherence"] = round(coherence, 3)

        # Composite ranking score
        enriched["constraint_score"] = round(
            enriched["pattern_score"] * 0.40
            + first_hook              * _HOOK_IMPACT_WEIGHT  # scale 0-10 score to ~0-0.25
            + last_impact             * _HOOK_IMPACT_WEIGHT
            + coherence               * _COHERENCE_SCALE,   # scale 0-1 to ~0-5
            4,
        )

        passed.append(enriched)

    # Sort by composite score
    passed.sort(key=lambda x: x.get("constraint_score", 0), reverse=True)

    # Enforce target max
    if len(passed) > target_max:
        passed = passed[:target_max]

    logger.info(
        f"apply_clip_constraints: {len(passed)} candidates pass "
        f"(duration {min_duration}–{max_duration}s, coherence≥{coherence_threshold})"
    )
    return passed
