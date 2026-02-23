"""
Macro Scorer — LLM scoring for macro candidates with micro-macro score blending.

Sends each macro candidate's consolidated text to the LLM for a holistic virality
assessment, then blends the macro LLM score with the best micro composite score
to produce a final blended score for clip selection.

Blend formula::

    blended = macro_llm_score * MACRO_WEIGHT + best_micro_score * MICRO_WEIGHT

All score computation is deterministic (the LLM only provides raw component
scores, not the final blended score).

Activated only when ``ASFS_AUDIO_SCORING=true``.
"""

import json
import logging
from typing import Callable, Dict, List, Optional

from src.prompts.scoring_v2 import compute_final_score_v2

logger = logging.getLogger(__name__)

# Blend weights — macro LLM view vs best micro composite.
MACRO_WEIGHT = 0.6
MICRO_WEIGHT = 0.4

# Default score used when the LLM response is missing / malformed.
DEFAULT_MACRO_SCORE = 5.0

_EXPECTED_KEYS = {
    "hook_score",
    "retention_score",
    "emotion_score",
    "relatability_score",
    "completion_score",
    "platform_fit_score",
    "controversy_score",
    "novelty_score",
}


def _build_macro_prompt(macro: Dict) -> str:
    """Build the LLM prompt for a single macro candidate."""
    return (
        f"Score this {macro.get('duration', 0):.1f}s video clip for virality.\n\n"
        f"Transcript:\n{macro.get('text', '')}\n\n"
        "Return ONLY valid JSON. No markdown. No explanation.\n"
        "{\n"
        '  "hook_score": <0-10>,\n'
        '  "retention_score": <0-10>,\n'
        '  "emotion_score": <0-10>,\n'
        '  "relatability_score": <0-10>,\n'
        '  "completion_score": <0-10>,\n'
        '  "platform_fit_score": <0-10>,\n'
        '  "controversy_score": <0-10>,\n'
        '  "novelty_score": <0-10>\n'
        "}\n"
        "Do NOT compute final_score — calculated server-side."
    )


def _parse_macro_scores(raw: str) -> Dict:
    """Parse macro LLM response; return defaults on error."""
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("Expected dict")
        scores = {}
        for key in _EXPECTED_KEYS:
            scores[key] = float(data.get(key, DEFAULT_MACRO_SCORE))
        return scores
    except (json.JSONDecodeError, ValueError, TypeError):
        logger.warning("MacroScorer: malformed response — using default scores.")
        return {k: DEFAULT_MACRO_SCORE for k in _EXPECTED_KEYS}


def score_macros(
    macros: List[Dict],
    platform: str = "tiktok",
    score_fn: Optional[Callable[[str], str]] = None,
) -> List[Dict]:
    """
    Score macro candidates and attach a blended final score.

    Parameters
    ----------
    macros : list[dict]
        Macro candidate dicts (from cluster_merger).
    platform : str
        Target platform for controversy weighting.
    score_fn : callable | None
        Function ``(prompt: str) -> str`` that calls the LLM.  When ``None``,
        default scores are used (useful for offline testing).

    Returns
    -------
    list[dict]
        Macro dicts each enriched with:
        ``macro_component_scores`` – raw LLM component scores dict
        ``macro_text_score``       – deterministic text score from v2 formula
        ``blended_score``          – micro-macro blended final score
    """
    results = []
    for macro in macros:
        prompt = _build_macro_prompt(macro)

        if score_fn is None:
            raw = json.dumps({k: DEFAULT_MACRO_SCORE for k in _EXPECTED_KEYS})
        else:
            try:
                raw = score_fn(prompt)
            except Exception as exc:
                logger.error("MacroScorer: score_fn error — %s", exc)
                raw = json.dumps({k: DEFAULT_MACRO_SCORE for k in _EXPECTED_KEYS})

        component_scores = _parse_macro_scores(raw)
        macro_text_score = compute_final_score_v2(component_scores, platform)

        best_micro = macro.get("best_micro_score", 0.0)
        blended = round(
            macro_text_score * MACRO_WEIGHT + best_micro * MICRO_WEIGHT, 4
        )

        enriched = dict(macro)
        enriched["macro_component_scores"] = component_scores
        enriched["macro_text_score"] = macro_text_score
        enriched["blended_score"] = blended
        results.append(enriched)

    # Sort by blended score descending.
    results.sort(key=lambda m: m["blended_score"], reverse=True)

    logger.info("MacroScorer: scored %d macro candidates.", len(results))
    return results
