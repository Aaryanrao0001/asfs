"""
Open Loop Detector — identifies incomplete thoughts at segment boundaries.

An "open loop" is any statement at the end of a segment that implies more
content is coming but has not yet been delivered.  When the micro-segmenter
or cluster-merger cuts at such a boundary, the resulting clip looks weak in
isolation even though it is the setup half of a strong moment.

Common open-loop signals:
- Trailing connectors: "and", "but", "because", "so", "however" …
- Setup phrases: "I was about to", "the thing is", "here's what happened" …
- Incomplete lists: "first", "number one", "the three reasons are" …
- Unanswered questions at the segment end (ends with "?")

Conversely, if the *next* segment starts with a continuation word ("and",
"but", "so" …) the previous segment was almost certainly cut mid-thought.

Public API
----------
has_open_loop(text)              → bool
next_segment_continues(text)     → bool
close_open_loops(segments, ...)  → list[dict]   # merges forward until closed

All logic is deterministic and requires only the standard library.
"""

import logging
import re
from typing import Dict, List

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Compiled patterns
# ---------------------------------------------------------------------------

# Connector words that should NEVER end a segment (trailing open loop).
_TRAILING_CONNECTORS = re.compile(
    r"""
    \b
    (and | but | because | so | however | although | though | yet |
     nor  | or  | if     | when | since  | while   | which  | that |
     who  | where | then)
    \s*,?\s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Setup phrases anywhere in the last 120 characters signal a payoff is coming.
_OPEN_LOOP_PHRASES = re.compile(
    r"""
    \b(
        i\s+was\s+about\s+to           |
        the\s+thing\s+is               |
        here['']?s?\s+what\s+happened  |
        you\s+won['']?t\s+believe      |
        and\s+then                     |
        before\s+i                     |
        let\s+me\s+tell\s+you          |
        the\s+reason\s+(is|why)        |
        the\s+point\s+is               |
        what\s+happened\s+was          |
        here['']?s?\s+the\s+thing      |
        here['']?s?\s+why              |
        heres?\s+what                  |
        first(\s+of\s+all)?            |
        number\s+one                   |
        the\s+(first|second|third|main)\s+(thing|point|reason|step) |
        the\s+(two|three|four|five)\s+(things?|reasons?|points?|steps?)
    )\b
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Segment ends with a question mark — unanswered question is an open loop.
_ENDS_WITH_QUESTION = re.compile(r"\?\s*$")

# Continuation starters — if the *next* segment begins with one of these the
# previous segment was cut mid-thought.
_CONTINUATION_STARTERS = re.compile(
    r"""
    ^\s*
    (and | but | because | so | however | although | though | yet |
     which\s+means | that\s+means | this\s+means |
     even\s+though | even\s+if)
    \b
    """,
    re.IGNORECASE | re.VERBOSE,
)

# ---------------------------------------------------------------------------
# Public detection helpers
# ---------------------------------------------------------------------------


def has_open_loop(text: str) -> bool:
    """
    Return ``True`` if *text* ends with an incomplete thought (open loop).

    Parameters
    ----------
    text : str
        The text of a segment (or just its final sentence).

    Returns
    -------
    bool
        ``True`` when the last sentence implies more content is coming.
    """
    text = text.strip()
    if not text:
        return False

    # Hard signal: ends with a connector word.
    if _TRAILING_CONNECTORS.search(text):
        return True

    # Setup phrase found in the tail of the text.
    tail = text[-min(len(text), 120):]
    if _OPEN_LOOP_PHRASES.search(tail):
        return True

    # Unanswered question.
    if _ENDS_WITH_QUESTION.search(text):
        return True

    return False


def next_segment_continues(next_text: str) -> bool:
    """
    Return ``True`` if *next_text* starts with a continuation word, which
    means the *previous* segment was cut mid-thought.

    Parameters
    ----------
    next_text : str
        The text of the segment immediately following the one under inspection.

    Returns
    -------
    bool
    """
    if not next_text:
        return False
    return bool(_CONTINUATION_STARTERS.match(next_text.strip()))


# ---------------------------------------------------------------------------
# Merge pass
# ---------------------------------------------------------------------------


def close_open_loops(
    segments: List[Dict],
    text_key: str = "text",
) -> List[Dict]:
    """
    Merge adjacent segments where the earlier one ends with an open loop.

    Iterates forward through *segments*.  When :func:`has_open_loop` returns
    ``True`` for the current segment's text **or** :func:`next_segment_continues`
    returns ``True`` for the next segment's text, the two are merged.
    Merging continues until the loop closes or the list is exhausted.

    The merged segment's ``start`` comes from the first segment and ``end``
    from the last merged segment.  All other fields come from the first
    segment, except:

    - ``text`` (or *text_key*) — concatenated with a single space.
    - ``end`` / ``duration`` — updated to span the full merged range.
    - ``words`` — concatenated if present on both segments.

    Parameters
    ----------
    segments : list[dict]
        Segment dicts each containing at least ``start``, ``end``, and a
        text field (key set by *text_key*).
    text_key : str
        Dict key for the text content.  Defaults to ``"text"``.

    Returns
    -------
    list[dict]
        New list of merged segments (always ``≤ len(segments)``).
    """
    if not segments:
        return []

    merged: List[Dict] = []
    i = 0

    while i < len(segments):
        current = dict(segments[i])

        # Keep pulling subsequent segments as long as the current text is
        # an open loop OR the next segment starts mid-thought.
        while i + 1 < len(segments):
            current_text = current.get(text_key, "")
            next_seg = segments[i + 1]
            next_text = next_seg.get(text_key, "")

            if has_open_loop(current_text) or next_segment_continues(next_text):
                # Merge: extend end and join text.
                current[text_key] = (current_text + " " + next_text).strip()
                current["end"] = next_seg["end"]
                current["duration"] = round(
                    current["end"] - current["start"], 4
                )
                # Concatenate word lists when both exist.
                if "words" in current and "words" in next_seg:
                    current["words"] = list(current["words"]) + list(
                        next_seg["words"]
                    )
                i += 1
            else:
                break

        merged.append(current)
        i += 1

    logger.info(
        "OpenLoopDetector: %d segments → %d after open-loop merging.",
        len(segments),
        len(merged),
    )
    return merged
