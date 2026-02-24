"""
Cluster Merger — continuous forward-only macro candidate construction.

Groups micro-segments into macro candidates using a forward-only scan.
Only directly adjacent (no gap) segments are merged. A hard 60 s duration
cap is enforced at every step — no negotiation.

Algorithm:
1. Sort segments by ``start`` time.
2. Walk forward: when a strong segment (score ≥ STRONG_THRESHOLD) is found,
   start a new cluster.
3. Extend the cluster with the next segment only when it is directly adjacent
   (start of next ≤ end of current + small float tolerance) and the cluster
   would not exceed ``max_duration_sec``.
4. Momentum smoothing: a single below-threshold segment between two strong
   segments is included to preserve natural flow, provided it still clears
   ``WEAK_THRESHOLD`` and the cluster stays within the duration cap.
5. Macro candidates shorter than ``min_duration_sec`` are discarded.

All logic is deterministic and requires only the standard library.
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

# Absolute score threshold for a "strong" segment.
STRONG_THRESHOLD = 6.0

# Minimum score for a segment eligible for momentum smoothing.
WEAK_THRESHOLD = 5.2

# Allow one weak segment between two strong ones (momentum smoothing).
ALLOW_ONE_WEAK = True

# Hard maximum duration cap in seconds — never exceeded.
DEFAULT_MAX_DURATION_SEC = 60.0

# Minimum macro candidate duration in seconds.
DEFAULT_MIN_DURATION_SEC = 10.0

# Key used to read each micro-segment's score.
DEFAULT_SCORE_KEY = "composite_score"

# Maximum gap in seconds between two adjacent segments that are still
# considered continuous (used in adjacency check).  Exposed as a public
# constant so callers can reference the default without hard-coding it.
DEFAULT_GAP_SEC = 0.05

# Internal alias kept for readability; callers should use DEFAULT_GAP_SEC.
_ADJACENCY_TOL = DEFAULT_GAP_SEC


def merge(
    segments: List[Dict],
    score_key: str = DEFAULT_SCORE_KEY,
    strong_threshold: float = STRONG_THRESHOLD,
    weak_threshold: float = WEAK_THRESHOLD,
    allow_one_weak: bool = ALLOW_ONE_WEAK,
    min_duration_sec: float = DEFAULT_MIN_DURATION_SEC,
    max_duration_sec: float = DEFAULT_MAX_DURATION_SEC,
    gap_sec: float = DEFAULT_GAP_SEC,
) -> List[Dict]:
    """
    Merge adjacent micro-segments into macro candidates.

    Parameters
    ----------
    segments : list[dict]
        Micro-segment dicts with ``start``, ``end``, and *score_key*.
    score_key : str
        Field name carrying the per-segment score.
    strong_threshold : float
        Minimum score for a "strong" segment (cluster seed or continuation).
    weak_threshold : float
        Minimum score for a segment eligible for momentum smoothing.
    allow_one_weak : bool
        When True, include a single weak segment between two strong ones.
    min_duration_sec : float
        Discard macro candidates shorter than this.
    max_duration_sec : float
        Hard cap that stops growing a cluster before exceeding this duration.
        Additionally, any completed macro candidates whose total duration
        exceeds this limit are discarded.
    gap_sec : float
        Maximum gap in seconds between two segments that are still considered
        adjacent and eligible for merging.  Defaults to :data:`DEFAULT_GAP_SEC`.

    Returns
    -------
    list[dict]
        Macro candidate dicts sorted by ``best_micro_score`` descending.
        Each dict has: ``macro_id``, ``start``, ``end``, ``duration``,
        ``text``, ``micro_segments``, ``micro_count``,
        ``best_micro_score``, ``avg_micro_score``.
    """
    if not segments:
        return []

    sorted_segs = sorted(segments, key=lambda s: s["start"])
    n = len(sorted_segs)
    clusters: List[List[Dict]] = []

    i = 0
    while i < n:
        seg = sorted_segs[i]

        if seg.get(score_key, 0.0) < strong_threshold:
            i += 1
            continue

        # Seed a new cluster with this strong segment.
        cluster: List[Dict] = [seg]
        cluster_start = seg["start"]
        j = i + 1

        while j < n:
            prev = cluster[-1]
            nxt = sorted_segs[j]

            # Hard duration guard — stop before the cluster would exceed the cap.
            if nxt["end"] - cluster_start > max_duration_sec:
                break

            # Adjacency: next segment must start no later than prev end + gap_sec.
            if nxt["start"] > prev["end"] + gap_sec:
                break

            score_j = nxt.get(score_key, 0.0)

            if score_j >= strong_threshold:
                # Strong continuation — always include.
                cluster.append(nxt)
                j += 1

            elif (
                allow_one_weak
                and score_j >= weak_threshold
                and nxt["end"] - cluster_start <= max_duration_sec
                and j + 1 < n
                and sorted_segs[j + 1].get(score_key, 0.0) >= strong_threshold
                and sorted_segs[j + 1]["end"] - cluster_start <= max_duration_sec
                and sorted_segs[j + 1]["start"] <= nxt["end"] + gap_sec
            ):
                # Momentum smoothing: one weak segment between two strong ones.
                cluster.append(nxt)
                j += 1

            else:
                break

        clusters.append(cluster)
        i = j

    macros: List[Dict] = []
    for idx, cluster in enumerate(clusters, 1):
        start = cluster[0]["start"]
        end = cluster[-1]["end"]
        duration = round(end - start, 4)

        if duration < min_duration_sec:
            logger.debug(
                "ClusterMerger: cluster %d too short (%.1f s < %.1f s) — dropped.",
                idx,
                duration,
                min_duration_sec,
            )
            continue

        if duration > max_duration_sec:
            logger.debug(
                "ClusterMerger: cluster %d too long (%.1f s > %.1f s) — dropped.",
                idx,
                duration,
                max_duration_sec,
            )
            continue

        text = " ".join(s.get("text", "") for s in cluster)
        scores = [s.get(score_key, 0.0) for s in cluster]
        best_score = max(scores)
        avg_score = round(sum(scores) / len(scores), 4)

        macros.append(
            {
                "macro_id": idx,
                "start": start,
                "end": end,
                "duration": duration,
                "text": text.strip(),
                "micro_segments": cluster,
                "micro_count": len(cluster),
                "best_micro_score": best_score,
                "avg_micro_score": avg_score,
            }
        )

    macros.sort(key=lambda m: m["best_micro_score"], reverse=True)
    logger.info("ClusterMerger: produced %d macro candidates.", len(macros))
    return macros
