"""
Dynamic Clip Reconstruction Engine.

Orchestrates the full reconstruction flow (Phases 1–5):

  Phase 1 – Atomic Units:      build_atomic_units
  Phase 2 – Sentence Scoring:  score_all_units
  Phase 3 – Reordering Engine: generate_candidates
  Phase 4 – Constraints:       apply_clip_constraints
  Phase 5 – Competitive Eval:  competitive_evaluate

Public entry-point: ``reconstruct_clips``
"""

import logging
from typing import Callable, Dict, List, Optional

from .atomic_units import build_atomic_units
from .sentence_scorer import score_all_units
from .reorder_engine import generate_candidates
from .clip_constraints import apply_clip_constraints
from .competitive_eval import competitive_evaluate

logger = logging.getLogger(__name__)


def reconstruct_clips(
    transcript_data: Dict,
    config: Dict = None,
    llm_scorer: Optional[Callable[[List[Dict]], List[Dict]]] = None,
    top_n: int = 3,
) -> List[Dict]:
    """
    Run the full Dynamic Clip Reconstruction Engine.

    Args:
        transcript_data: Transcript dict produced by transcribe.py.
        config:          Optional configuration overrides. Supported keys:
                         ``min_duration``, ``max_duration``,
                         ``coherence_threshold``, ``target_min_candidates``,
                         ``target_max_candidates``, ``reorder_k``,
                         ``default_speaker``.
        llm_scorer:      Optional LLM scoring callable for Phase 5.
        top_n:           Number of top clips to return (default 3).

    Returns:
        List of up to *top_n* clip dicts, each with full metadata including
        ``start``, ``end``, ``duration``, ``text``, ``pattern``,
        ``competitive_score``, and all sentence-score dimensions.
    """
    cfg = config or {}

    logger.info("=" * 60)
    logger.info("DYNAMIC CLIP RECONSTRUCTION ENGINE")
    logger.info("=" * 60)

    # ── Phase 1: Atomic Units ──────────────────────────────────────────────
    logger.info("Phase 1: Building atomic sentence units …")
    units = build_atomic_units(
        transcript_data,
        default_speaker=cfg.get("default_speaker", "speaker_0"),
    )
    if not units:
        logger.warning("No atomic units produced – returning empty list")
        return []
    logger.info(f"  → {len(units)} sentence units")

    # ── Phase 2: Sentence Scoring ──────────────────────────────────────────
    logger.info("Phase 2: Scoring sentence units …")
    scored_units = score_all_units(units)
    logger.info(f"  → {len(scored_units)} scored units")

    # ── Phase 3: Reordering Engine ─────────────────────────────────────────
    logger.info("Phase 3: Generating reordered candidates …")
    k = cfg.get("reorder_k", 5)
    raw_candidates = generate_candidates(scored_units, k=k)
    logger.info(f"  → {len(raw_candidates)} raw candidates")

    if not raw_candidates:
        logger.warning("No candidates from reordering engine – returning []")
        return []

    # ── Phase 4: Clip Construction Constraints ─────────────────────────────
    logger.info("Phase 4: Applying clip construction constraints …")
    constrained = apply_clip_constraints(
        raw_candidates,
        scored_units,
        min_duration=cfg.get("min_duration", 15.0),
        max_duration=cfg.get("max_duration", 60.0),
        coherence_threshold=cfg.get("coherence_threshold", 0.15),
        target_min=cfg.get("target_min_candidates", 20),
        target_max=cfg.get("target_max_candidates", 50),
    )
    logger.info(f"  → {len(constrained)} constrained candidates")

    if not constrained:
        logger.warning("No candidates survived constraints – returning []")
        return []

    # ── Phase 5: Competitive Evaluation ───────────────────────────────────
    logger.info("Phase 5: Competitive evaluation …")
    final = competitive_evaluate(
        constrained,
        llm_scorer=llm_scorer,
        top_n=top_n,
    )

    logger.info("=" * 60)
    logger.info(f"RECONSTRUCTION COMPLETE: {len(final)} clips selected")
    for i, clip in enumerate(final, 1):
        logger.info(
            f"  {i}. [{clip.get('pattern','?')}] "
            f"{clip.get('start', 0):.1f}s–{clip.get('end', 0):.1f}s "
            f"({clip.get('duration', 0):.1f}s) "
            f"score={clip.get('competitive_score', 0):.3f}"
        )
    logger.info("=" * 60)

    return final
