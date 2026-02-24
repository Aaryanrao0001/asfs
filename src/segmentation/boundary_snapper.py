"""
Boundary Snapper — word-level clip boundary alignment.

Adjusts a clip's ``start`` and ``end`` times so they align with the word
being spoken at those moments and then walks to the nearest *sentence*
boundary, ensuring every clip:

1. Starts at the beginning of a complete sentence (never mid-clause).
2. Ends at the close of a complete sentence (never mid-thought).

Sentence-end markers recognised: ``.``  ``?``  ``!``  (one or more).

Words that must never begin a clip (continuation starters):
    and, but, so, because, which, that, however, although,
    yet, nor, or, if, when, while, since, though, even.

Public API
----------
snap_to_sentence_start(words, target_time)   → float
snap_to_sentence_end(words, target_time)     → float
snap_segment(segment, words, text_key="text") → dict

All logic is deterministic and requires only the standard library.
"""

import logging
import re
from typing import Dict, List

# Floating-point tolerance when collecting words within a snapped boundary.
# Accounts for minor rounding differences in word-end timestamps.
_TIME_TOLERANCE = 0.01

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Words stripped of punctuation that must never open a clip.
_CONTINUATION_WORDS: frozenset = frozenset(
    {
        "and", "but", "so", "because", "which", "that", "however",
        "although", "yet", "nor", "or", "if", "when", "while",
        "since", "though", "even",
    }
)

# Sentence-ending punctuation at the end of a word token.
_SENTENCE_END_RE = re.compile(r"[.?!]+$")

# Strip everything that isn't a letter so we can do word-form lookups.
_NON_ALPHA_RE = re.compile(r"[^a-zA-Z]")

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _word_index_at(words: List[Dict], time: float) -> int:
    """
    Return the index of the word being spoken at *time*.

    If *time* falls between two words, the index of the next word after
    *time* is returned.  If *time* is past the last word, the last index
    is returned.
    """
    if not words:
        return 0

    # Exact or overlapping match.
    for i, w in enumerate(words):
        if w["start"] <= time <= w["end"]:
            return i

    # Between words — return the first word that starts after *time*.
    for i, w in enumerate(words):
        if w["start"] > time:
            return i

    return len(words) - 1


def _is_sentence_end(word: str) -> bool:
    """Return True if *word* ends with sentence-ending punctuation."""
    return bool(_SENTENCE_END_RE.search(word.strip()))


def _is_continuation_word(word: str) -> bool:
    """Return True if *word* (stripped of punctuation) is a continuation word."""
    token = _NON_ALPHA_RE.sub("", word).lower()
    return token in _CONTINUATION_WORDS


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def snap_to_sentence_start(words: List[Dict], target_time: float) -> float:
    """
    Return the start time of the sentence containing the word at *target_time*.

    Walks *backwards* from the word at *target_time* until it finds a word
    whose predecessor ends with ``.``, ``?``, or ``!``, which means the
    current word is the first word of a new sentence.  Also skips any
    leading continuation words (``and``, ``but``, ``so`` …) so the clip
    never starts mid-clause.

    Parameters
    ----------
    words : list[dict]
        Full word-timestamp list ``{"word": str, "start": float, "end": float}``.
    target_time : float
        Desired clip start time in seconds.

    Returns
    -------
    float
        Adjusted start time (≤ *target_time*).
    """
    if not words:
        return target_time

    idx = _word_index_at(words, target_time)

    # Walk backwards to find the sentence boundary.
    while idx > 0:
        prev_word = words[idx - 1]["word"].strip()
        if _is_sentence_end(prev_word):
            break  # words[idx] is the first word of a new sentence.
        idx -= 1

    # Skip any continuation words at the sentence start.
    while idx < len(words) - 1:
        if _is_continuation_word(words[idx]["word"]):
            idx += 1
        else:
            break

    return words[idx]["start"]


def snap_to_sentence_end(words: List[Dict], target_time: float) -> float:
    """
    Return the end time of the sentence containing the word at *target_time*.

    Walks *forwards* from the word at *target_time* until it finds a word
    that ends with ``.``, ``?``, or ``!``.  If no such word is found, the
    end of the last word is returned.

    Parameters
    ----------
    words : list[dict]
        Full word-timestamp list.
    target_time : float
        Desired clip end time in seconds.

    Returns
    -------
    float
        Adjusted end time (≥ *target_time*).
    """
    if not words:
        return target_time

    idx = _word_index_at(words, target_time)

    # Walk forwards to find the sentence end.
    while idx < len(words):
        word_text = words[idx]["word"].strip()
        if _is_sentence_end(word_text):
            return words[idx]["end"]
        idx += 1

    # No sentence-end punctuation found — use the last word's end.
    return words[-1]["end"]


def snap_segment(
    segment: Dict,
    words: List[Dict],
    text_key: str = "text",
) -> Dict:
    """
    Snap a segment's ``start`` and ``end`` to sentence boundaries.

    Parameters
    ----------
    segment : dict
        Segment dict with at least ``start`` and ``end`` keys.
    words : list[dict]
        Full word-timestamp list for the source content.
    text_key : str
        Key for the text field in *segment*.  Defaults to ``"text"``.

    Returns
    -------
    dict
        New segment dict with updated ``start``, ``end``, ``duration``,
        ``words``, and *text_key* fields.  All other fields are copied
        from *segment* unchanged.
    """
    if not words:
        return dict(segment)

    new_start = snap_to_sentence_start(words, segment.get("start", 0.0))
    new_end = snap_to_sentence_end(words, segment.get("end", 0.0))

    # Ensure start < end (snapping should never invert, but guard anyway).
    if new_start >= new_end:
        return dict(segment)

    # Collect all words fully contained within [new_start, new_end].
    snap_words = [
        w for w in words
        if w["start"] >= new_start and w["end"] <= new_end + _TIME_TOLERANCE
    ]

    result = dict(segment)
    result["start"] = new_start
    result["end"] = new_end
    result["duration"] = round(new_end - new_start, 4)

    if snap_words:
        result["words"] = snap_words
        result[text_key] = " ".join(w["word"] for w in snap_words)

    logger.debug(
        "BoundarySnapper: %.2f–%.2f → %.2f–%.2f (Δstart=%.2f Δend=%.2f)",
        segment.get("start", 0.0),
        segment.get("end", 0.0),
        new_start,
        new_end,
        new_start - segment.get("start", 0.0),
        new_end - segment.get("end", 0.0),
    )
    return result
