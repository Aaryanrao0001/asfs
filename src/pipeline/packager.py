"""
Packaging Engine — Mandatory packaging for every output clip.

Generates three variant objects per clip (Curiosity, Contrarian, Relatable),
enforces subtitle styling rules, appends a CTA frame, and derives a headline
from the suggested_title field (not verbatim transcript).
"""

import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------- CTA Library ----------
CTA_LIBRARY = {
    "comment": [
        "Agree or disagree? Comment YES or NO.",
        "Comment your biggest mistake below.",
        "Drop your answer in the comments.",
    ],
    "poll": [
        "Comment A or B.",
        "Which side are you on? Comment below.",
    ],
    "tag": [
        "Tag someone who needs to see this.",
        "Tag a friend who does this.",
    ],
}

# ---------- Subtitle Defaults ----------
SUBTITLE_DEFAULTS = {
    "font_size_min": 70,
    "font_size_max": 90,
    "font_style": "bold",
    "font_color": "white",
    "outline_size": 8,
    "outline_color": "black",
    "max_lines": 3,
    "max_chars_per_line": 32,
    "pause_break_threshold": 0.4,
}

# CTA frame duration in seconds
CTA_FRAME_DURATION = 1.5

# Filler words stripped from headline fallback
_FILLER = {"um", "uh", "so", "like", "well", "and", "but", "hey", "ok", "okay", "a", "the"}


def _select_cta(controversy_score: float, cta_type: str) -> str:
    """Pick a CTA string from the library based on score and type."""
    bucket = CTA_LIBRARY.get(cta_type, CTA_LIBRARY["comment"])
    if controversy_score > 7.0 and cta_type == "comment":
        # Prefer the polarising prompt for high-controversy clips
        return bucket[0]
    return bucket[-1] if len(bucket) > 1 else bucket[0]


def _derive_headline(
    suggested_title: Optional[str],
    hook_text: Optional[str],
    curiosity_score: float,
    max_words: int = 6,
) -> str:
    """
    Derive headline overlay text.

    Rules:
    - Use *suggested_title* if present and ≤ 8 words.
    - Otherwise fall back to first 6 non-filler words of *hook_text*,
      appending '?' if curiosity_score > 6.
    """
    if suggested_title:
        words = suggested_title.strip().split()
        if len(words) <= 8:
            return suggested_title.strip()

    if hook_text:
        words = [w for w in hook_text.split() if w.lower() not in _FILLER]
        headline = " ".join(words[:max_words])
        if curiosity_score > 6 and not headline.endswith("?"):
            headline += "?"
        return headline

    return ""


def _build_variant(
    variant_type: str,
    headline: str,
    controversy_score: float,
    cta_type: str,
) -> Dict:
    """Build a single variant dict."""
    overlay_templates = {
        "Curiosity": "What they don't tell you",
        "Contrarian": "The myth nobody talks about",
        "Relatable": "If you've ever failed at this…",
    }

    overlay_line = overlay_templates.get(variant_type, "")
    cta_text = _select_cta(controversy_score, cta_type)

    return {
        "variant_type": variant_type,
        "headline_text": headline,
        "overlay_line": overlay_line,
        "cta_text": cta_text,
        "cta_type": cta_type,
    }


def generate_variants(
    clip: Dict,
    suggested_title: Optional[str] = None,
    hook_text: Optional[str] = None,
) -> List[Dict]:
    """
    Generate three packaging variants for a clip.

    Parameters
    ----------
    clip : dict
        Clip dict expected to have ``controversy_score``, ``emotion_score``,
        ``relatability_score``, and optionally ``curiosity_score``.
    suggested_title : str | None
        LLM-suggested title for headline derivation.
    hook_text : str | None
        Transcript text of the hook moment (fallback for headline).

    Returns
    -------
    list[dict]
        Three variant dicts: Curiosity, Contrarian, Relatable — ordered so the
        primary variant (based on score thresholds) is first.
    """
    controversy = clip.get("controversy_score", 0.0)
    emotion = clip.get("emotion_score", 0.0)
    relatability = clip.get("relatability_score", 0.0)
    curiosity = clip.get("curiosity_score", 0.0)

    headline = _derive_headline(suggested_title, hook_text, curiosity)

    variants = [
        _build_variant("Curiosity", headline, controversy, "comment"),
        _build_variant("Contrarian", headline, controversy, "comment"),
        _build_variant("Relatable", headline, controversy, "tag"),
    ]

    # Determine primary variant ordering
    if controversy > 7.0:
        primary_type = "Contrarian"
    elif emotion > 7.0 and relatability > 6.0:
        primary_type = "Relatable"
    else:
        primary_type = "Curiosity"

    # Move primary to front
    variants.sort(key=lambda v: 0 if v["variant_type"] == primary_type else 1)

    return variants


def build_subtitle_spec() -> Dict:
    """Return the enforced subtitle specification dict."""
    return dict(SUBTITLE_DEFAULTS)


def package_clip(
    clip: Dict,
    suggested_title: Optional[str] = None,
    hook_text: Optional[str] = None,
) -> Dict:
    """
    Apply full packaging to a clip and return the enriched clip dict.

    Attaches:
    - ``variants``: list of 3 variant dicts
    - ``subtitle_spec``: enforced subtitle styling
    - ``cta_frame_duration``: CTA duration in seconds
    - ``packaging_applied``: True
    """
    variants = generate_variants(clip, suggested_title, hook_text)

    clip["variants"] = variants
    clip["variant_type"] = variants[0]["variant_type"]
    clip["subtitle_spec"] = build_subtitle_spec()
    clip["cta_frame_duration"] = CTA_FRAME_DURATION
    clip["packaging_applied"] = True

    logger.info(
        "Packaged clip — primary variant: %s, headline: %s",
        clip["variant_type"],
        variants[0]["headline_text"],
    )

    return clip
