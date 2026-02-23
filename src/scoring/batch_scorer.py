"""
Batch Scorer — fast batch LLM virality scoring for micro-segments.

Sends micro-segments to the LLM in a single batched prompt and returns
per-segment component scores.  The LLM returns ONLY component scores;
all final score computation is done deterministically server-side via
:func:`src.scoring.segment_ranker.rank`.

This module does NOT call the LLM directly during unit tests — callers
should inject a ``score_fn`` for testing.

Activated only when ``ASFS_AUDIO_SCORING=true``.
"""

import json
import logging
import os
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# Maximum number of segments per LLM batch call.
MAX_BATCH_SIZE = int(os.environ.get("ASFS_BATCH_SIZE", "10"))

# LLM component score keys expected in each response object.
EXPECTED_KEYS = {
    "hook_score",
    "retention_score",
    "emotion_score",
    "relatability_score",
    "completion_score",
    "platform_fit_score",
    "controversy_score",
    "novelty_score",
}

# Default score used when LLM omits a field.
DEFAULT_SCORE = 5.0


def _build_batch_prompt(segments: List[Dict]) -> str:
    """
    Build the LLM prompt for a batch of micro-segments.

    Parameters
    ----------
    segments : list[dict]
        Micro-segment dicts each with ``text`` and ``duration``.

    Returns
    -------
    str
        Prompt string requesting JSON component scores only.
    """
    blocks = []
    for seg in segments:
        blocks.append(
            f"\n\n--- SEGMENT {seg['segment_id']} ---\n"
            f"Text: {seg['text']}\n"
            f"Duration: {seg.get('duration', 0):.1f}s\n"
        )

    return (
        f"Score the following {len(segments)} podcast/video micro-segment(s) for virality.\n"
        f"{''.join(blocks)}\n\n"
        "Return ONLY valid JSON. No markdown. No explanation.\n"
        "Format:\n"
        '{"segments": [{\n'
        '  "segment_id": <int>,\n'
        '  "hook_score": <0-10>,\n'
        '  "retention_score": <0-10>,\n'
        '  "emotion_score": <0-10>,\n'
        '  "relatability_score": <0-10>,\n'
        '  "completion_score": <0-10>,\n'
        '  "platform_fit_score": <0-10>,\n'
        '  "controversy_score": <0-10>,\n'
        '  "novelty_score": <0-10>\n'
        "}]}\n"
        "Do NOT compute final_score — that is calculated server-side."
    )


def _parse_response(raw: str, segments: List[Dict]) -> List[Dict]:
    """
    Parse LLM JSON response and align results to *segments*.

    Missing fields are filled with :data:`DEFAULT_SCORE`.
    Malformed JSON returns default scores for all segments.
    """
    try:
        data = json.loads(raw)
        results = data.get("segments", [])
    except (json.JSONDecodeError, AttributeError):
        logger.warning("BatchScorer: malformed LLM response — using defaults.")
        results = []

    # Build a lookup by segment_id.
    by_id = {r.get("segment_id"): r for r in results if isinstance(r, dict)}

    out = []
    for seg in segments:
        sid = seg["segment_id"]
        raw_scores = by_id.get(sid, {})
        scored = dict(seg)
        for key in EXPECTED_KEYS:
            scored[key] = float(raw_scores.get(key, DEFAULT_SCORE))
        out.append(scored)

    return out


def score_batch(
    segments: List[Dict],
    score_fn: Optional[Callable[[str], str]] = None,
) -> List[Dict]:
    """
    Score *segments* using a batch LLM call.

    Parameters
    ----------
    segments : list[dict]
        Micro-segment dicts (output of micro_segmenter).
    score_fn : callable | None
        Function ``(prompt: str) -> str`` that calls the LLM and returns the
        raw JSON response string.  When ``None``, defaults are returned for
        every segment (useful for offline testing).

    Returns
    -------
    list[dict]
        Each input segment dict enriched with component score keys.
    """
    if not segments:
        return []

    results: List[Dict] = []

    # Process in batches.
    for i in range(0, len(segments), MAX_BATCH_SIZE):
        batch = segments[i : i + MAX_BATCH_SIZE]
        prompt = _build_batch_prompt(batch)

        if score_fn is None:
            logger.warning(
                "BatchScorer: no score_fn provided — assigning default scores for %d segments.",
                len(batch),
            )
            raw = json.dumps(
                {"segments": [{"segment_id": s["segment_id"]} for s in batch]}
            )
        else:
            try:
                raw = score_fn(prompt)
            except Exception as exc:
                logger.error("BatchScorer: score_fn raised %s — using defaults.", exc)
                raw = json.dumps(
                    {"segments": [{"segment_id": s["segment_id"]} for s in batch]}
                )

        results.extend(_parse_response(raw, batch))

    logger.info("BatchScorer: scored %d segments.", len(results))
    return results
