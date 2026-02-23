"""
Phase 1 – Atomic Units: sentence-level unit builder.

Builds atomic sentence units from transcript data, using:
- Word-level timestamps (if available)
- Sentence boundary detection
- Speaker turn tracking

Each unit carries: start, end, speaker, text, word_count, and an index.
"""

import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Simple regex for sentence boundary detection
_SENTENCE_END = re.compile(r'(?<=[.!?])\s+')


def _split_text_into_sentences(text: str) -> List[str]:
    """Split raw text into sentences."""
    parts = _SENTENCE_END.split(text.strip())
    return [p.strip() for p in parts if p.strip()]


def build_atomic_units(
    transcript_data: Dict,
    default_speaker: str = "speaker_0",
) -> List[Dict]:
    """
    Build sentence-level atomic units from transcript data.

    Each unit is a dict with:
        - start (float): start timestamp in seconds
        - end   (float): end timestamp in seconds
        - text  (str):   sentence text
        - speaker (str): speaker label
        - word_count (int): number of words
        - index (int): position in the episode (0-based)

    The function uses word-level timestamps when available.  When
    word timestamps are absent it falls back to interpolating timing
    across the sentences inside each segment.

    Args:
        transcript_data: Transcript dict produced by transcribe.py.
                         Expected keys: ``segments`` (list of dicts with
                         ``start``, ``end``, ``text``, and optional
                         ``words`` / ``speaker`` fields).
        default_speaker: Speaker label used when no per-segment speaker
                         information is present.

    Returns:
        List of atomic unit dicts, ordered by start time.
    """
    segments = transcript_data.get("segments", [])
    if not segments:
        logger.warning("build_atomic_units: no segments in transcript_data")
        return []

    units: List[Dict] = []
    unit_index = 0

    for seg in segments:
        seg_start: float = seg.get("start", 0.0)
        seg_end: float = seg.get("end", seg_start)
        seg_text: str = (seg.get("text") or "").strip()
        speaker: str = seg.get("speaker", default_speaker)
        words_data: List[Dict] = seg.get("words", [])

        if not seg_text:
            continue

        # ---------- sentence splitting ----------
        sentences = _split_text_into_sentences(seg_text)
        if not sentences:
            sentences = [seg_text]

        # ---------- timestamp assignment ----------
        if words_data:
            # Word-level timestamps are available → assign each sentence
            # the timestamp range of the words it contains.
            units_for_seg = _assign_timestamps_from_words(
                sentences, words_data, seg_start, seg_end, speaker
            )
        else:
            # Interpolate timestamps proportionally by word count.
            units_for_seg = _assign_timestamps_proportional(
                sentences, seg_start, seg_end, speaker
            )

        for unit in units_for_seg:
            unit["index"] = unit_index
            unit_index += 1
            units.append(unit)

    logger.info(f"build_atomic_units: produced {len(units)} sentence units")
    return units


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _assign_timestamps_from_words(
    sentences: List[str],
    words_data: List[Dict],
    seg_start: float,
    seg_end: float,
    speaker: str,
) -> List[Dict]:
    """Assign per-sentence timestamps using word-level data."""
    # Flatten word tokens from the segment's word list.
    # Pre-process each token once (strip punctuation) to avoid repeated
    # regex substitutions inside the matching loop.
    word_tokens = []
    for w in words_data:
        raw = (w.get("word") or w.get("text") or "").strip().lower()
        if raw:
            word_tokens.append({
                "word": raw,
                "clean": re.sub(r'[^a-z0-9]', '', raw),
                "start": float(w.get("start", seg_start)),
                "end": float(w.get("end", seg_end)),
            })

    if not word_tokens:
        return _assign_timestamps_proportional(sentences, seg_start, seg_end, speaker)

    units: List[Dict] = []
    word_cursor = 0

    for sent in sentences:
        sent_words = [re.sub(r'[^a-z0-9]', '', w.lower()) for w in sent.split() if w]
        sent_words = [sw for sw in sent_words if sw]
        if not sent_words:
            continue

        # Find the first matching word in the remaining word_tokens
        start_ts: Optional[float] = None
        end_ts: Optional[float] = None
        matched = 0

        for i in range(word_cursor, len(word_tokens)):
            tok = word_tokens[i]["clean"]
            sw = sent_words[matched] if matched < len(sent_words) else ""
            if tok == sw or tok in sw or sw in tok:
                if start_ts is None:
                    start_ts = word_tokens[i]["start"]
                end_ts = word_tokens[i]["end"]
                matched += 1
                if matched >= len(sent_words):
                    word_cursor = i + 1
                    break

        # Fallback: use segment boundaries
        if start_ts is None:
            start_ts = seg_start
        if end_ts is None:
            end_ts = seg_end

        units.append(_make_unit(sent, start_ts, end_ts, speaker))

    return units


def _assign_timestamps_proportional(
    sentences: List[str],
    seg_start: float,
    seg_end: float,
    speaker: str,
) -> List[Dict]:
    """Interpolate timestamps proportionally by word count."""
    seg_duration = max(seg_end - seg_start, 0.0)
    word_counts = [len(s.split()) for s in sentences]
    total_words = sum(word_counts) or 1

    units: List[Dict] = []
    current = seg_start
    for sent, wc in zip(sentences, word_counts):
        fraction = wc / total_words
        duration = seg_duration * fraction
        units.append(_make_unit(sent, current, current + duration, speaker))
        current += duration

    return units


def _make_unit(text: str, start: float, end: float, speaker: str) -> Dict:
    """Create a single atomic unit dict (without index)."""
    return {
        "text": text,
        "start": round(start, 3),
        "end": round(end, 3),
        "speaker": speaker,
        "word_count": len(text.split()),
    }
