"""Open loop detection for transcript segments.

Detects incomplete thoughts at segment boundaries and merges segments to
ensure the full thought (setup + payoff) is captured in a single candidate.
"""

import re
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# Words that, when a segment ends with them, indicate an incomplete thought
TRAILING_CONNECTORS = {
    "and", "but", "so", "because", "which", "that", "however",
    "or", "then", "when", "while", "if", "before", "after", "although",
}

# Phrases that set up a payoff that lives in the next segment
SETUP_PHRASES = [
    "i was about to",
    "here's what happened",
    "the thing is",
    "you won't believe",
    "and then",
    "here's the deal",
    "what happened was",
    "let me tell you",
    "guess what",
    "the reason is",
    "what i found was",
]

# Words that signal the end of a thought (natural completion markers)
COMPLETION_MARKERS = {"right", "okay", "exactly", "that's it", "anyway"}

# Words that signal a continuation (bad opening)
CONTINUATION_WORDS = {
    "and", "but", "so", "because", "which", "that", "however",
    "or", "also", "plus", "furthermore", "additionally", "moreover",
}

# Maximum duration (seconds) allowed for a merged segment
MAX_MERGED_DURATION = 90.0


def has_open_loop(text: str) -> bool:
    """
    Detect whether text ends with an incomplete thought.

    Checks for:
    - Trailing connectors (e.g. ends with "and", "but")
    - Setup phrases without a payoff
    - Incomplete lists (first/number one without continuation)
    - Questions without answers
    - Sentences ending without terminal punctuation

    Args:
        text: The transcript text to check.

    Returns:
        True if the text appears to end with an open loop.
    """
    stripped = text.strip()
    if not stripped:
        return False

    # Check for missing terminal punctuation
    if stripped[-1] not in ".!?":
        # Might just be a missing period, so combine with other checks
        # Check trailing connector
        last_word = stripped.split()[-1].lower().rstrip(",:;") if stripped.split() else ""
        if last_word in TRAILING_CONNECTORS:
            return True

        # Check setup phrase (case-insensitive)
        lower = stripped.lower()
        for phrase in SETUP_PHRASES:
            if lower.endswith(phrase):
                return True

        # No terminal punctuation at all signals open loop
        return True

    # Terminal punctuation present — check other signals
    lower = stripped.lower()

    # Check trailing connector before the final punctuation
    # e.g. "I was walking and." — strip punctuation from last word
    words = re.findall(r"[a-zA-Z']+", lower)
    if words and words[-1] in TRAILING_CONNECTORS:
        return True

    # Check setup phrases
    for phrase in SETUP_PHRASES:
        if lower.rstrip(".!?").endswith(phrase):
            return True

    # Incomplete list: "first" or "number one" without "second"/"number two"/etc.
    has_list_start = bool(re.search(r"\b(first|number one)\b", lower))
    has_list_continuation = bool(
        re.search(r"\b(second|third|number two|number three|also|additionally)\b", lower)
    )
    if has_list_start and not has_list_continuation:
        return True

    # Question without answer in same segment
    # A segment that ends with "?" is always an open loop
    if stripped.endswith("?"):
        return True
    # A question mark anywhere that is the last sentence boundary is an open loop
    sentences_with_delimiters = re.split(r"([.!?]+)", stripped)
    # Find if the last non-empty delimiter is a question mark
    delimiters = [p for p in sentences_with_delimiters if re.match(r"[.!?]+", p)]
    if delimiters and "?" in delimiters[-1]:
        return True

    return False


def has_bad_opening(text: str) -> bool:
    """
    Detect whether text starts with a continuation word signalling missing context.

    Args:
        text: The transcript text to check.

    Returns:
        True if the text opens with a continuation marker.
    """
    stripped = text.strip()
    if not stripped:
        return False

    words = stripped.split()
    if not words:
        return False

    first_word = words[0].lower().rstrip(",:;")
    return first_word in CONTINUATION_WORDS


def _segment_duration(segment: Dict) -> float:
    """Return the duration of a segment in seconds."""
    return segment.get("end", 0) - segment.get("start", 0)


def _ends_with_completion(text: str) -> bool:
    """Return True if text ends with a natural completion marker or terminal punctuation."""
    stripped = text.strip()
    if not stripped:
        return True
    if stripped[-1] in ".!?":
        return True
    last_word = stripped.split()[-1].lower().rstrip(",:;")
    return last_word in COMPLETION_MARKERS


def close_open_loops(segments: List[Dict]) -> List[Dict]:
    """
    Merge transcript segments forward whenever an open loop is detected.

    Iterates through all segments and, when the current segment ends with an
    open loop, merges it with the next segment.  Keeps merging until:
    - The merged text ends with terminal punctuation or a completion marker, OR
    - The merged duration exceeds MAX_MERGED_DURATION

    Args:
        segments: Full list of transcript segment dicts, each with at minimum
                  "start", "end", and "text" keys.

    Returns:
        New list of segments with open-loop boundaries merged.
    """
    if not segments:
        return []

    merged: List[Dict] = []
    i = 0

    while i < len(segments):
        current = dict(segments[i])  # shallow copy so we don't mutate the original

        # Keep merging forward while the current segment has an open loop
        while i + 1 < len(segments):
            merged_duration = current["end"] - current["start"]
            if merged_duration >= MAX_MERGED_DURATION:
                break
            if not has_open_loop(current.get("text", "")):
                break

            # Merge with next segment
            next_seg = segments[i + 1]
            current = {
                "start": current["start"],
                "end": next_seg["end"],
                "text": current.get("text", "").rstrip() + " " + next_seg.get("text", "").lstrip(),
                # Merge word-level data if present
                "words": current.get("words", []) + next_seg.get("words", []),
            }
            i += 1

            if _ends_with_completion(current.get("text", "")):
                break

        merged.append(current)
        i += 1

    logger.debug(
        f"close_open_loops: {len(segments)} → {len(merged)} segments after merging"
    )
    return merged


def snap_start_boundary(segments: List[Dict], start_idx: int) -> int:
    """
    Walk backwards from start_idx to find where a thought actually started.

    If the segment at start_idx has a bad opening (starts with a continuation
    word), return the index of the earlier segment where the thought begins.

    Args:
        segments: Full list of transcript segments.
        start_idx: Index to begin checking.

    Returns:
        Adjusted index (may be <= start_idx).
    """
    idx = start_idx
    while idx > 0 and has_bad_opening(segments[idx].get("text", "")):
        idx -= 1
    return idx


def snap_end_boundary(segments: List[Dict], end_idx: int) -> int:
    """
    Walk forwards from end_idx to find where a thought actually ends.

    If the segment at end_idx has an open loop, return the index of the later
    segment where the thought completes.

    Args:
        segments: Full list of transcript segments.
        end_idx: Index to begin checking.

    Returns:
        Adjusted index (may be >= end_idx).
    """
    idx = end_idx
    while idx < len(segments) - 1 and has_open_loop(segments[idx].get("text", "")):
        next_end = segments[idx + 1]["end"]
        merged_duration = next_end - segments[end_idx]["start"]
        if merged_duration > MAX_MERGED_DURATION:
            break
        idx += 1
    return idx


def check_curiosity_gap(text: str) -> Dict:
    """
    Check whether a curiosity gap (question) is answered immediately.

    A question answered within 5 words of being asked is NOT a real curiosity
    gap and should NOT boost the viral score.

    Args:
        text: Transcript text to analyse.

    Returns:
        Dict with keys:
        - "has_question" (bool): whether a question was found.
        - "answer_distance_words" (int): number of words between the question
          mark and what appears to be the answer start.  0 if no question.
    """
    if "?" not in text:
        return {"has_question": False, "answer_distance_words": 0}

    # Find the position of the last question mark
    q_pos = text.rfind("?")
    after_question = text[q_pos + 1:].strip()

    if not after_question:
        # Question at end of segment — answer is in next segment (real gap)
        return {"has_question": True, "answer_distance_words": 9999}

    # Count words between question and the start of the answer
    words_after = after_question.split()
    answer_distance = len(words_after)

    return {"has_question": True, "answer_distance_words": answer_distance}
