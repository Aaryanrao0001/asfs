"""
Phase 5 – Competitive Evaluation.

Treats clip candidates as competitors and ranks them using LLM scoring
across five dimensions:

  1. scroll_stop_probability  – would a viewer stop scrolling?
  2. share_trigger            – likelihood of being shared
  3. debate_potential         – will it spark comments / discussion?
  4. clarity                  – is the message clear and punchy?
  5. ending_strength          – does it end in a memorable / impactful way?

Each dimension is scored 0–10.  A composite ``competitive_score`` is
computed as a weighted average.

When no LLM scorer function is provided the module falls back to a fast
heuristic scorer so the pipeline can run offline.
"""

import logging
import re
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# Maximum score for any single dimension
MAX_SCORE: float = 10.0

# Weights for the composite score
_DIMENSION_WEIGHTS: Dict[str, float] = {
    "scroll_stop_probability": 0.30,
    "share_trigger":           0.20,
    "debate_potential":        0.15,
    "clarity":                 0.20,
    "ending_strength":         0.15,
}

# Top-N candidates to keep after competitive evaluation.
# Set to 15 to ensure enough candidates survive for downstream filtering
# (hook filter and time-diversity constraints).  Adjust as needed.
TOP_N_KEEP: int = 15


# ── heuristic fallback ─────────────────────────────────────────────────────

def _heuristic_scroll_stop(text: str) -> float:
    """Estimate scroll-stop probability from text patterns."""
    patterns = [
        r'\b(?:nobody|never|always|shocking|secret|truth|exposed)\b',
        r'\b(?:you won\'?t believe|can\'?t believe|incredible)\b',
        r'\?$',
        r'[!]+',
    ]
    hits = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
    return min(hits / len(patterns) * MAX_SCORE, MAX_SCORE)


def _heuristic_share_trigger(text: str) -> float:
    patterns = [
        r'\b(?:share|tell|show|pass|forward|repost)\b',
        r'\b(?:everyone needs to|you need to know|important)\b',
        r'\b(?:save this|bookmark|screenshot)\b',
    ]
    hits = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
    return min(hits / max(len(patterns), 1) * MAX_SCORE, MAX_SCORE)


def _heuristic_debate_potential(text: str) -> float:
    patterns = [
        r'\b(?:wrong|disagree|controversial|unpopular opinion|fight me)\b',
        r'\b(?:actually|in fact|contrary|opposite|myth|lie)\b',
        r'\b(?:change my mind|prove me wrong|hot take)\b',
    ]
    hits = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
    return min(hits / max(len(patterns), 1) * MAX_SCORE, MAX_SCORE)


def _heuristic_clarity(text: str) -> float:
    """Longer and more structured = potentially clearer up to a point."""
    words = text.split()
    wc = len(words)
    # Ideal range: 30–100 words for a clear short clip
    if wc < 10:
        return 2.0
    if wc > 200:
        return 5.0
    return min((wc / 100.0) * MAX_SCORE, MAX_SCORE)


def _heuristic_ending_strength(text: str, last_sentence: str = "") -> float:
    target = last_sentence if last_sentence else text
    patterns = [
        r'[!]+$',
        r'\?$',
        r'\b(?:remember|think about|that\'?s the truth|that\'?s it)\b',
        r'\b(?:and that\'?s why|this is what|bottom line|the point is)\b',
    ]
    hits = sum(1 for p in patterns if re.search(p, target, re.IGNORECASE))
    return min(hits / max(len(patterns), 1) * MAX_SCORE, MAX_SCORE)


def _heuristic_score_candidate(candidate: Dict) -> Dict:
    """Score a single candidate using heuristics."""
    text = candidate.get("text", "")
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    last_sentence = sentences[-1] if sentences else text

    scores = {
        "scroll_stop_probability": _heuristic_scroll_stop(text),
        "share_trigger":           _heuristic_share_trigger(text),
        "debate_potential":        _heuristic_debate_potential(text),
        "clarity":                 _heuristic_clarity(text),
        "ending_strength":         _heuristic_ending_strength(text, last_sentence),
    }

    composite = sum(
        scores[dim] * _DIMENSION_WEIGHTS[dim] for dim in _DIMENSION_WEIGHTS
    )

    result = dict(candidate)
    result.update(scores)
    result["competitive_score"] = round(composite, 3)
    return result


# ── public API ─────────────────────────────────────────────────────────────

def competitive_evaluate(
    candidates: List[Dict],
    llm_scorer: Optional[Callable[[List[Dict]], List[Dict]]] = None,
    top_n: int = TOP_N_KEEP,
) -> List[Dict]:
    """
    Run competitive evaluation and return the top-N candidates.

    Each candidate is scored on five dimensions.  When an *llm_scorer*
    callable is supplied it is expected to accept and return a list of
    candidate dicts, adding the five dimension keys plus
    ``competitive_score``.  If it raises an exception or is not provided,
    the module falls back to the heuristic scorer.

    Args:
        candidates:  Filtered candidate dicts from clip_constraints.
        llm_scorer:  Optional callable ``(candidates) -> candidates`` that
                     adds LLM-based competitive scores.
        top_n:       Number of top candidates to keep.

    Returns:
        Top-N candidates sorted by ``competitive_score`` descending, each
        annotated with ``scroll_stop_probability``, ``share_trigger``,
        ``debate_potential``, ``clarity``, ``ending_strength``, and
        ``competitive_score``.
    """
    if not candidates:
        logger.warning("competitive_evaluate: no candidates provided")
        return []

    evaluated: List[Dict] = []

    if llm_scorer is not None:
        try:
            evaluated = llm_scorer(candidates)
            logger.info(
                f"competitive_evaluate: LLM scored {len(evaluated)} candidates"
            )
        except Exception as exc:
            logger.error(
                f"competitive_evaluate: LLM scorer failed ({exc}); "
                f"falling back to heuristics"
            )
            evaluated = []

    if not evaluated:
        logger.info(
            "competitive_evaluate: using heuristic scoring "
            f"({len(candidates)} candidates)"
        )
        evaluated = [_heuristic_score_candidate(c) for c in candidates]

    evaluated.sort(key=lambda x: x.get("competitive_score", 0), reverse=True)

    top = evaluated[:top_n]
    logger.info(
        f"competitive_evaluate: keeping top {len(top)}/{len(evaluated)} candidates"
    )
    return top
