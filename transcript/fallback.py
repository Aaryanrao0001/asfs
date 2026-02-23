"""
Fallback title and description generation from transcript segments.

Used when a clip has no explicit title/description set before uploading.

Logic
-----
1. If transcript already exists in the work directory, load it.
2. If no transcript exists, extract the first 30 seconds of audio and run
   Whisper (``base`` model) on that short clip — never re-transcribe the
   whole video.
3. Clean filler words from the best segment, capitalise it, and trim to a
   safe length for the platform title field.
4. Build a short description from the leading transcript text.
"""

import json
import logging
import os
import re
import subprocess
import tempfile
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Filler words to strip from spoken text before using it as a title.
FILLER_WORDS: frozenset = frozenset(
    {
        "um", "uh", "er", "ah", "like", "you know", "you know what",
        "i mean", "basically", "literally", "actually", "so", "well",
        "right", "okay", "ok",
    }
)

# Regex that matches whole-word filler occurrences (case-insensitive).
# Built once at import time for performance.
_FILLER_PATTERN = re.compile(
    r"\b(?:" + "|".join(re.escape(w) for w in sorted(FILLER_WORDS, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)

# Title length limits (characters)
TITLE_MIN_LENGTH = 10
TITLE_MAX_LENGTH = 100  # safe ceiling; platform allows 150 but shorter is safer

# Description length limits (characters)
DESC_MIN_LENGTH = 50
DESC_MAX_LENGTH = 400


# ---------------------------------------------------------------------------
# Text cleaning helpers
# ---------------------------------------------------------------------------

def clean_filler_words(text: str) -> str:
    """
    Remove spoken filler words from *text* and normalise whitespace.

    Parameters
    ----------
    text : str
        Raw transcript segment text.

    Returns
    -------
    str
        Cleaned text with filler words removed.
    """
    cleaned = _FILLER_PATTERN.sub("", text)
    # Collapse multiple spaces / leading-trailing whitespace
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    # Remove orphaned punctuation left after stripping (e.g. ", , ,")
    cleaned = re.sub(r"([,;])\s*([,;])", r"\1", cleaned)
    cleaned = re.sub(r"\s+([,;.])", r"\1", cleaned)
    return cleaned


def _score_sentence(text: str) -> int:
    """
    Simple scoring heuristic: prefer longer sentences with more words,
    penalise very short fragments.
    """
    words = text.split()
    word_count = len(words)
    if word_count < 4:
        return 0
    # Reward informationally dense sentences
    return word_count


# ---------------------------------------------------------------------------
# Transcript-to-metadata converters
# ---------------------------------------------------------------------------

def generate_fallback_title(transcript: Dict) -> str:
    """
    Generate a clean, platform-ready title from transcript data.

    Steps:
    1. Iterate over segments, clean filler words.
    2. Pick the highest-scoring (longest coherent) sentence.
    3. Capitalise first letter, trim to ``TITLE_MAX_LENGTH``.

    Parameters
    ----------
    transcript : dict
        Transcript dict with a ``"segments"`` key containing a list of
        ``{"text": str, ...}`` dicts.

    Returns
    -------
    str
        Fallback title string, or an empty string if no usable text found.
    """
    segments = transcript.get("segments", [])
    if not segments:
        logger.warning("generate_fallback_title: transcript has no segments")
        return ""

    best_text = ""
    best_score = -1

    for seg in segments:
        raw = seg.get("text", "").strip()
        if not raw:
            continue
        cleaned = clean_filler_words(raw)
        score = _score_sentence(cleaned)
        if score > best_score:
            best_score = score
            best_text = cleaned

    if not best_text or best_score < 1:
        logger.warning("generate_fallback_title: no usable segment found")
        return ""

    # Capitalise and trim
    title = (best_text[0].upper() + best_text[1:]) if len(best_text) > 1 else best_text.upper()
    if len(title) > TITLE_MAX_LENGTH:
        # Cut at the last word boundary within the limit
        title = title[:TITLE_MAX_LENGTH].rsplit(" ", 1)[0].rstrip(",.;:")

    logger.info("Generated fallback title (%d chars): %s", len(title), title)
    return title


def generate_fallback_description(transcript: Dict) -> str:
    """
    Generate a short description from the first few transcript segments.

    Concatenates cleaned segment text until we reach ``DESC_MAX_LENGTH``
    characters, then returns the accumulated text.

    Parameters
    ----------
    transcript : dict
        Transcript dict with ``"segments"`` list.

    Returns
    -------
    str
        Fallback description string (300–500 chars target, hard-capped at
        ``DESC_MAX_LENGTH``).
    """
    segments = transcript.get("segments", [])
    if not segments:
        logger.warning("generate_fallback_description: transcript has no segments")
        return ""

    parts = []
    total_len = 0

    for seg in segments:
        raw = seg.get("text", "").strip()
        if not raw:
            continue
        cleaned = clean_filler_words(raw)
        if not cleaned:
            continue

        # Add segment text, stop when we have enough content
        if total_len + len(cleaned) + 1 > DESC_MAX_LENGTH:
            # Trim the last part to fit
            remaining = DESC_MAX_LENGTH - total_len - 1
            if remaining > 20:  # only add if there's meaningful content
                parts.append(cleaned[:remaining].rsplit(" ", 1)[0])
            break

        parts.append(cleaned)
        total_len += len(cleaned) + 1  # +1 for space separator

        if total_len >= DESC_MIN_LENGTH:
            break  # We have enough text

    description = " ".join(parts).strip()
    logger.info(
        "Generated fallback description (%d chars)", len(description)
    )
    return description


# ---------------------------------------------------------------------------
# Transcript loading / partial transcription
# ---------------------------------------------------------------------------

def load_transcript_if_exists(video_path: str) -> Optional[Dict]:
    """
    Try to load an existing ``transcript.json`` for *video_path*.

    Looks in ``<parent_of_clips_dir>/work/transcript.json`` — the standard
    location used by the main pipeline.

    Parameters
    ----------
    video_path : str
        Path to the clip or video file.

    Returns
    -------
    dict | None
        Parsed transcript dict if a valid file is found, otherwise ``None``.
    """
    # Derive the work directory: video is in output/clips/XXX.mp4,
    # transcript is in output/work/transcript.json
    clips_dir = os.path.dirname(os.path.abspath(video_path))
    output_dir = os.path.dirname(clips_dir)
    candidate = os.path.join(output_dir, "work", "transcript.json")

    if not os.path.exists(candidate):
        logger.debug("load_transcript_if_exists: not found at %s", candidate)
        return None

    try:
        with open(candidate, "r", encoding="utf-8") as fh:
            data = json.load(fh)

        if not isinstance(data.get("segments"), list) or not data["segments"]:
            logger.warning("load_transcript_if_exists: file invalid or empty")
            return None

        logger.info("load_transcript_if_exists: loaded %d segments", len(data["segments"]))
        return data

    except Exception as exc:
        logger.warning("load_transcript_if_exists: failed to load %s — %s", candidate, exc)
        return None


def transcribe_first_30_seconds(video_path: str, work_dir: Optional[str] = None) -> Dict:
    """
    Extract the first 30 seconds of *video_path* and transcribe with Whisper.

    This is the lightweight fallback path — it never processes the full video.

    Parameters
    ----------
    video_path : str
        Path to the video file.
    work_dir : str | None
        Directory for temporary audio files.  Defaults to a system temp dir.

    Returns
    -------
    dict
        Transcript dict with ``"segments"`` list (may be empty on failure).
    """
    if not os.path.exists(video_path):
        logger.error("transcribe_first_30_seconds: file not found: %s", video_path)
        return {"segments": []}

    # Use a temporary directory if no work_dir provided
    use_temp = work_dir is None
    tmp_dir_obj = None

    try:
        if use_temp:
            tmp_dir_obj = tempfile.mkdtemp(prefix="asfs_fallback_")
            work_dir = tmp_dir_obj

        os.makedirs(work_dir, exist_ok=True)
        audio_path = os.path.join(work_dir, "fallback_30s.wav")

        # Extract first 30 seconds with ffmpeg
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-t", "30",          # Stop after 30 seconds
            "-vn",               # No video
            "-acodec", "pcm_s16le",
            "-ar", "16000",      # 16 kHz — Whisper optimal
            "-ac", "1",          # Mono
            "-y",
            audio_path,
        ]

        logger.info("Extracting first 30 s for fallback transcription: %s", video_path)
        subprocess.run(cmd, check=True, capture_output=True, text=True)

        if not os.path.exists(audio_path):
            logger.error("transcribe_first_30_seconds: ffmpeg did not produce output")
            return {"segments": []}

        # Transcribe with Whisper base model (fast enough for 30 s)
        from faster_whisper import WhisperModel

        model = WhisperModel(
            "base",
            device="cpu",
            compute_type="int8",
            cpu_threads=2,
            num_workers=1,
        )

        segments_iter, _info = model.transcribe(
            audio_path,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500, speech_pad_ms=400),
        )

        segments = [
            {
                "start": seg.start,
                "end": seg.end,
                "text": seg.text.strip(),
            }
            for seg in segments_iter
        ]

        logger.info(
            "transcribe_first_30_seconds: got %d segments from first 30 s",
            len(segments),
        )
        return {"segments": segments}

    except subprocess.CalledProcessError as exc:
        logger.error("transcribe_first_30_seconds: ffmpeg failed — %s", exc.stderr)
        return {"segments": []}
    except Exception as exc:
        logger.error("transcribe_first_30_seconds: error — %s", exc)
        return {"segments": []}
    finally:
        # Clean up temporary audio file
        if tmp_dir_obj and os.path.isdir(tmp_dir_obj):
            import shutil
            shutil.rmtree(tmp_dir_obj, ignore_errors=True)
