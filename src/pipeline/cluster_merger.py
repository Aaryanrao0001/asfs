"""
Cluster Merger — proximity-based macro candidate construction.

Groups micro-segments that are temporally close into macro candidates
(longer clips) by merging overlapping or near-adjacent segments.

Algorithm:
1. Sort segments by ``start`` time.
2. Greedily merge any two segments whose temporal gap is ≤ ``gap_sec``.
3. Each merged cluster becomes a macro candidate spanning from the earliest
   start to the latest end of its constituent segments.
4. Macro candidates shorter than ``min_duration_sec`` are discarded.

All logic is deterministic and requires only the standard library.
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

# Maximum gap (seconds) between segment ends/starts to still be merged.
DEFAULT_GAP_SEC = 3.0

# Minimum macro candidate duration (seconds).
DEFAULT_MIN_DURATION_SEC = 10.0

# Maximum macro candidate duration (seconds).
DEFAULT_MAX_DURATION_SEC = 60.0


def _merge_overlapping(segments: List[Dict], gap_sec: float) -> List[List[Dict]]:
    """
    Group segments into clusters where consecutive items are within *gap_sec*.

    Parameters
    ----------
    segments : list[dict]
        Sorted (by start time) segment dicts with ``start`` and ``end``.
    gap_sec : float
        Maximum allowed gap between end of one segment and start of the next.

    Returns
    -------
    list[list[dict]]
        Each inner list is a cluster of segments to be merged.
    """
    if not segments:
        return []

    clusters = []
    current_cluster = [segments[0]]

    for seg in segments[1:]:
        prev_end = current_cluster[-1]["end"]
        if seg["start"] - prev_end <= gap_sec:
            current_cluster.append(seg)
        else:
            clusters.append(current_cluster)
            current_cluster = [seg]

    clusters.append(current_cluster)
    return clusters


def _build_macro(cluster: List[Dict], macro_id: int) -> Dict:
    """Build a single macro candidate dict from a cluster of micro-segments."""
    start = min(s["start"] for s in cluster)
    end = max(s["end"] for s in cluster)
    text = " ".join(s.get("text", "") for s in cluster)
    # Carry through the best composite score of the cluster members.
    scores = [s.get("composite_score", 0.0) for s in cluster]
    best_score = max(scores) if scores else 0.0
    avg_score = round(sum(scores) / len(scores), 4) if scores else 0.0

    return {
        "macro_id": macro_id,
        "start": start,
        "end": end,
        "duration": round(end - start, 4),
        "text": text.strip(),
        "micro_segments": cluster,
        "micro_count": len(cluster),
        "best_micro_score": best_score,
        "avg_micro_score": avg_score,
    }


def merge(
    segments: List[Dict],
    gap_sec: float = DEFAULT_GAP_SEC,
    min_duration_sec: float = DEFAULT_MIN_DURATION_SEC,
    max_duration_sec: float = DEFAULT_MAX_DURATION_SEC,
) -> List[Dict]:
    """
    Merge ranked micro-segments into macro candidates.

    Parameters
    ----------
    segments : list[dict]
        Micro-segment dicts with ``start``, ``end``, and optionally
        ``composite_score``.
    gap_sec : float
        Maximum gap between segments to still merge them.
    min_duration_sec : float
        Macro candidates shorter than this are discarded.
    max_duration_sec : float
        Macro candidates longer than this are trimmed to *max_duration_sec*
        from the start.

    Returns
    -------
    list[dict]
        Macro candidate dicts sorted by ``best_micro_score`` descending.
    """
    if not segments:
        return []

    # Sort by start time before clustering.
    sorted_segs = sorted(segments, key=lambda s: s["start"])
    clusters = _merge_overlapping(sorted_segs, gap_sec)

    macros = []
    for idx, cluster in enumerate(clusters, 1):
        macro = _build_macro(cluster, macro_id=idx)

        # Discard too-short candidates.
        if macro["duration"] < min_duration_sec:
            logger.debug(
                "ClusterMerger: macro %d too short (%.1f s < %.1f s) — dropped.",
                idx,
                macro["duration"],
                min_duration_sec,
            )
            continue

        # Trim over-long candidates.
        if macro["duration"] > max_duration_sec:
            macro["end"] = round(macro["start"] + max_duration_sec, 4)
            macro["duration"] = max_duration_sec
            logger.debug("ClusterMerger: macro %d trimmed to %.0f s.", idx, max_duration_sec)

        macros.append(macro)

    # Sort by best micro score descending.
    macros.sort(key=lambda m: m["best_micro_score"], reverse=True)

    logger.info("ClusterMerger: produced %d macro candidates.", len(macros))
    return macros
