"""
Weight Advisor — correlation analysis and recommendation engine.

Runs after 100+ clips have performance data.  Produces a human-readable
markdown report correlating component scores with real engagement metrics,
broken down by platform and variant type.

Does **not** auto-modify weights.  Output is advisory only.
"""

import logging
import sqlite3
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

MIN_CLIPS_FOR_REPORT = 100

# Component score columns to correlate against engagement
SCORE_COLUMNS = [
    "controversy_score",
    "novelty_score",
    "hook_timestamp",
]

ENGAGEMENT_COLUMNS = [
    "avg_watch_pct",
    "comments",
    "shares",
    "saves",
    "views",
]


def _pearson(xs: List[float], ys: List[float]) -> float:
    """Compute Pearson correlation coefficient for two equal-length lists."""
    n = len(xs)
    if n < 2:
        return 0.0
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den_x = sum((x - mean_x) ** 2 for x in xs) ** 0.5
    den_y = sum((y - mean_y) ** 2 for y in ys) ** 0.5
    if den_x == 0 or den_y == 0:
        return 0.0
    return round(num / (den_x * den_y), 4)


def _fetch_joined_data(db_path: str) -> List[Dict]:
    """
    Fetch clips joined with their performance data.

    Returns a list of dicts with both score and engagement fields.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT c.variant_type, c.controversy_score, c.novelty_score,
                   c.hook_timestamp, c.hashtag_mode_used,
                   p.platform, p.views, p.impressions, p.avg_watch_pct,
                   p.comments, p.shares, p.saves
            FROM clips c
            JOIN clip_performance p ON c.id = p.clip_id
            """
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def generate_report(db_path: str) -> str:
    """
    Generate a human-readable markdown weight-adjustment report.

    Parameters
    ----------
    db_path : str
        Path to the SQLite database.

    Returns
    -------
    str
        Markdown-formatted report.
    """
    data = _fetch_joined_data(db_path)

    if len(data) < MIN_CLIPS_FOR_REPORT:
        return (
            f"# Weight Advisor Report\n\n"
            f"**Not enough data.** {len(data)} clips have performance data "
            f"(minimum {MIN_CLIPS_FOR_REPORT} required).\n"
        )

    lines = ["# Weight Advisor Report\n"]
    lines.append(f"**Clips analyzed:** {len(data)}\n")

    # Group by platform
    platforms = sorted({d.get("platform", "unknown") for d in data})

    for platform in platforms:
        subset = [d for d in data if d.get("platform") == platform]
        if not subset:
            continue

        lines.append(f"\n## Platform: {platform} ({len(subset)} clips)\n")
        lines.append("| Score Component | vs avg_watch_pct | vs comments/1k views |")
        lines.append("|---|---|---|")

        for sc in SCORE_COLUMNS:
            xs = [float(d.get(sc, 0) or 0) for d in subset]
            ys_watch = [float(d.get("avg_watch_pct", 0) or 0) for d in subset]
            views = [float(d.get("views", 0) or 0) for d in subset]
            comments = [float(d.get("comments", 0) or 0) for d in subset]
            ys_cpm = [
                (c / v * 1000) if v > 0 else 0.0
                for c, v in zip(comments, views)
            ]

            r_watch = _pearson(xs, ys_watch)
            r_cpm = _pearson(xs, ys_cpm)
            lines.append(f"| {sc} | {r_watch:+.3f} | {r_cpm:+.3f} |")

    # Variant breakdown
    variants = sorted({d.get("variant_type", "unknown") for d in data})
    if variants:
        lines.append("\n## Variant Performance\n")
        lines.append("| Variant | Avg Watch % | Avg Comments/1k |")
        lines.append("|---|---|---|")
        for vt in variants:
            sub = [d for d in data if d.get("variant_type") == vt]
            avg_w = sum(float(d.get("avg_watch_pct", 0) or 0) for d in sub) / max(len(sub), 1)
            views = [float(d.get("views", 0) or 0) for d in sub]
            comments = [float(d.get("comments", 0) or 0) for d in sub]
            avg_cpm = sum(
                (c / v * 1000) if v > 0 else 0.0
                for c, v in zip(comments, views)
            ) / max(len(sub), 1)
            lines.append(f"| {vt} | {avg_w:.1f}% | {avg_cpm:.1f} |")

    lines.append("\n---\n*This report is advisory only. No weights were auto-modified.*\n")

    report = "\n".join(lines)
    logger.info("Weight advisor report generated (%d clips)", len(data))
    return report
