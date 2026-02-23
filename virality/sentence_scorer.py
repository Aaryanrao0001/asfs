"""
Phase 2 – Sentence Scoring: per-sentence virality dimensions.

Scores each atomic unit for:
- hook_score          – attention-grabbing opening quality
- emotional_charge    – emotional intensity / valence
- claim_strength      – strength of assertion or claim
- identity_trigger    – personal relevance / "you" framing
- energy_score        – pace / punctuation / exclamatory language
- delivery_intensity  – combined energy + emotion proxy

All scores are normalised to 0–10.
"""

import logging
import re
from typing import Dict, List

logger = logging.getLogger(__name__)

# ── pattern banks ──────────────────────────────────────────────────────────

_HOOK_PATTERNS = [
    r'^\s*(?:wait|stop|listen|look|imagine|picture this|here(?:\'s)?|this is)',
    r'\b(?:you won\'?t believe|you need to know|you have to|you must)\b',
    r'\b(?:nobody tells you|nobody talks about|the secret|the truth)\b',
    r'\b(?:this is why|here(?:\'s)? why|the reason)\b',
    r'\?$',
]

_EMOTION_PATTERNS = [
    r'\b(?:shocked|stunned|insane|crazy|unbelievable|wild|amazing|incredible)\b',
    r'\b(?:angry|furious|devastated|heartbroken|terrified|scared|thrilled)\b',
    r'\b(?:love|hate|fear|joy|disgust|surprise|sad|happy|excited)\b',
    r'[!]{1,}',
]

_CLAIM_PATTERNS = [
    r'\b(?:always|never|every|all|none|nobody|everybody|everyone)\b',
    r'\b(?:fact|proven|study shows|research says|data shows)\b',
    r'\b(?:guarantee|promise|swear|certain|absolutely|definitely)\b',
    r'\b\d+\s*%\b',          # percentage
    r'\$\d[\d,]*',           # money
    r'\b\d+[xX]\b',          # multiplier
    r'\b\d+\s*(?:days?|weeks?|months?|hours?|years?)\b',  # time
]

_IDENTITY_PATTERNS = [
    r'\b(?:you|your|you\'?re|you\'?ve|you\'?ll|yourself)\b',
    r'\b(?:we all|anyone who|if you\'?ve|people like)\b',
    r'\b(?:as a|being a|when you\'?re|for you)\b',
]

_ENERGY_PATTERNS = [
    r'[!]+',                  # exclamation marks
    r'\b(?:now|right now|immediately|instantly|quickly|fast)\b',
    r'\b(?:massive|huge|giant|enormous|tiny|zero|every single)\b',
    r'[A-Z]{3,}',             # ALL-CAPS words
]


def _count_matches(text: str, patterns: List[str]) -> int:
    return sum(
        1 for p in patterns
        if re.search(p, text, re.IGNORECASE)
    )


def _normalise(count: int, max_count: int = 3) -> float:
    """Map raw match count to 0–10."""
    return min(count / max(max_count, 1) * 10.0, 10.0)


def score_sentence_unit(unit: Dict) -> Dict:
    """
    Compute virality dimension scores for a single atomic unit.

    Adds the following keys to a *copy* of the unit (originals
    are not mutated):
        hook_score, emotional_charge, claim_strength,
        identity_trigger, energy_score, delivery_intensity

    Args:
        unit: Atomic unit dict (from build_atomic_units).

    Returns:
        New dict with all original keys plus the six score fields.
    """
    text = unit.get("text", "")

    hook_score       = _normalise(_count_matches(text, _HOOK_PATTERNS), 2)
    emotional_charge = _normalise(_count_matches(text, _EMOTION_PATTERNS), 3)
    claim_strength   = _normalise(_count_matches(text, _CLAIM_PATTERNS), 3)
    identity_trigger = _normalise(_count_matches(text, _IDENTITY_PATTERNS), 3)
    energy_score     = _normalise(_count_matches(text, _ENERGY_PATTERNS), 2)
    delivery_intensity = (emotional_charge * 0.6 + energy_score * 0.4)

    scored = dict(unit)
    scored.update(
        hook_score=round(hook_score, 2),
        emotional_charge=round(emotional_charge, 2),
        claim_strength=round(claim_strength, 2),
        identity_trigger=round(identity_trigger, 2),
        energy_score=round(energy_score, 2),
        delivery_intensity=round(delivery_intensity, 2),
    )
    return scored


def score_all_units(units: List[Dict]) -> List[Dict]:
    """
    Score every atomic unit in the list.

    Args:
        units: List of atomic unit dicts.

    Returns:
        List of scored unit dicts (new objects; inputs unchanged).
    """
    scored = [score_sentence_unit(u) for u in units]
    logger.info(f"score_all_units: scored {len(scored)} sentence units")
    return scored
