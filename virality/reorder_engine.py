"""
Phase 3 – Reordering Engine: candidate generator for non-contiguous clips.

Constructs clip candidates by combining scored sentence units into
narrative patterns:

  1. Hook → Context → Punchline
  2. Strong claim → Data → Stronger claim
  3. Punchline first → Explanation → Reinforcement

Candidates are non-contiguous (sentences need not be adjacent in the
original transcript) but the reordering preserves logical flow.
"""

import logging
from typing import Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── pattern roles ──────────────────────────────────────────────────────────

def _role_hook(unit: Dict) -> float:
    """Score a unit's suitability as the *hook* position."""
    return (
        unit.get("hook_score", 0) * 0.5
        + unit.get("emotional_charge", 0) * 0.3
        + unit.get("energy_score", 0) * 0.2
    )


def _role_context(unit: Dict) -> float:
    """Score a unit's suitability as a *context/data* position."""
    return (
        unit.get("claim_strength", 0) * 0.4
        + unit.get("identity_trigger", 0) * 0.3
        + unit.get("emotional_charge", 0) * 0.3
    )


def _role_punchline(unit: Dict) -> float:
    """Score a unit's suitability as the *punchline/closing* position."""
    return (
        unit.get("delivery_intensity", 0) * 0.4
        + unit.get("claim_strength", 0) * 0.3
        + unit.get("hook_score", 0) * 0.3
    )


# ── helpers ────────────────────────────────────────────────────────────────

def _top_k(units: List[Dict], score_fn: Callable[[Dict], float], k: int) -> List[Dict]:
    """Return the *k* units with the highest score from *score_fn*."""
    return sorted(units, key=score_fn, reverse=True)[:k]


def _make_candidate(
    pattern_name: str,
    parts: List[Dict],
    pattern_score: float,
) -> Dict:
    """Assemble a candidate dict from a list of unit parts."""
    # Sort parts by original index so the clip reads in logical order.
    ordered = sorted(parts, key=lambda u: u.get("index", 0))
    text = " ".join(u.get("text", "") for u in ordered)
    start = min(u.get("start", 0.0) for u in ordered)
    end = max(u.get("end", 0.0) for u in ordered)

    # Collect constituent indices for traceability.
    indices = [u.get("index", -1) for u in ordered]
    is_contiguous = all(
        indices[i + 1] - indices[i] == 1 for i in range(len(indices) - 1)
    )

    # For non-contiguous clips the actual playback duration is the sum of
    # individual unit durations, not the full timeline span (end - start).
    if is_contiguous:
        duration = round(end - start, 3)
    else:
        duration = round(
            sum(u.get("end", 0.0) - u.get("start", 0.0) for u in ordered), 3
        )

    return {
        "start": start,
        "end": end,
        "duration": duration,
        "text": text,
        "pattern": pattern_name,
        "pattern_score": round(pattern_score, 3),
        "unit_indices": indices,
        "is_contiguous": is_contiguous,
        "type": "reconstructed",
    }


# ── pattern builders ───────────────────────────────────────────────────────

def _pattern_hook_context_punchline(
    units: List[Dict], k: int = 5
) -> List[Dict]:
    """Pattern: Hook → Context → Punchline."""
    hooks      = _top_k(units, _role_hook,      k)
    contexts   = _top_k(units, _role_context,   k)
    punchlines = _top_k(units, _role_punchline, k)

    candidates = []
    seen: set = set()

    for h in hooks:
        for c in contexts:
            for p in punchlines:
                trio = frozenset([h.get("index"), c.get("index"), p.get("index")])
                if len(trio) < 3 or trio in seen:
                    continue
                seen.add(trio)

                score = (
                    _role_hook(h) * 0.4
                    + _role_context(c) * 0.3
                    + _role_punchline(p) * 0.3
                )
                candidates.append(
                    _make_candidate("hook_context_punchline", [h, c, p], score)
                )

    return candidates


def _pattern_claim_data_stronger(
    units: List[Dict], k: int = 5
) -> List[Dict]:
    """Pattern: Strong claim → Data → Stronger claim."""
    claims_sorted = sorted(units, key=lambda u: u.get("claim_strength", 0), reverse=True)
    strong  = claims_sorted[:k]
    data    = _top_k(units, _role_context, k)
    stronger = claims_sorted[:k]  # reuse top-claim units for 'stronger claim'

    candidates = []
    seen: set = set()

    for s1 in strong:
        for d in data:
            for s2 in stronger:
                trio = frozenset([s1.get("index"), d.get("index"), s2.get("index")])
                if len(trio) < 3 or trio in seen:
                    continue
                seen.add(trio)

                score = (
                    s1.get("claim_strength", 0) * 0.35
                    + d.get("claim_strength", 0) * 0.25
                    + s2.get("claim_strength", 0) * 0.40
                )
                candidates.append(
                    _make_candidate("claim_data_stronger", [s1, d, s2], score)
                )

    return candidates


def _pattern_punchline_explanation_reinforcement(
    units: List[Dict], k: int = 5
) -> List[Dict]:
    """Pattern: Punchline first → Explanation → Reinforcement."""
    punchlines    = _top_k(units, _role_punchline, k)
    explanations  = _top_k(units, _role_context,   k)
    reinforcements = _top_k(units, _role_hook,     k)

    candidates = []
    seen: set = set()

    for p in punchlines:
        for e in explanations:
            for r in reinforcements:
                trio = frozenset([p.get("index"), e.get("index"), r.get("index")])
                if len(trio) < 3 or trio in seen:
                    continue
                seen.add(trio)

                score = (
                    _role_punchline(p) * 0.45
                    + _role_context(e)  * 0.25
                    + _role_hook(r)     * 0.30
                )
                candidates.append(
                    _make_candidate(
                        "punchline_explanation_reinforcement", [p, e, r], score
                    )
                )

    return candidates


# ── public API ─────────────────────────────────────────────────────────────

def generate_candidates(
    scored_units: List[Dict],
    k: int = 5,
) -> List[Dict]:
    """
    Generate clip candidates by reordering sentence units.

    Combines all three patterns and returns a de-duplicated list
    sorted by pattern_score descending.

    Args:
        scored_units: Scored atomic units (from sentence_scorer).
        k: Number of top-units per role to consider (limits combinatorics).

    Returns:
        List of candidate dicts with start/end/text/pattern metadata.
    """
    if not scored_units:
        logger.warning("generate_candidates: no scored units provided")
        return []

    all_candidates: List[Dict] = []
    all_candidates += _pattern_hook_context_punchline(scored_units, k)
    all_candidates += _pattern_claim_data_stronger(scored_units, k)
    all_candidates += _pattern_punchline_explanation_reinforcement(scored_units, k)

    # De-duplicate by unit_indices frozenset
    seen: set = set()
    unique: List[Dict] = []
    for c in all_candidates:
        key = frozenset(c.get("unit_indices", []))
        if key not in seen:
            seen.add(key)
            unique.append(c)

    unique.sort(key=lambda x: x.get("pattern_score", 0), reverse=True)

    logger.info(
        f"generate_candidates: {len(unique)} unique candidates from "
        f"{len(all_candidates)} total (k={k})"
    )
    return unique
