"""
Audio Transcriber — word-timestamp transcription for the audio-first scoring pipeline.

Wraps faster-whisper (CPU-only, no GPU required) to produce per-word timestamps
needed by the micro-segmenter.  Falls back gracefully when faster-whisper is not
installed or the audio file is unreadable.

Activated only when ``ASFS_AUDIO_SCORING=true``.
"""

import logging
import os
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Guard: faster-whisper is an optional dependency for this sub-pipeline.
try:
    from faster_whisper import WhisperModel  # type: ignore

    _WHISPER_AVAILABLE = True
except ImportError:  # pragma: no cover
    _WHISPER_AVAILABLE = False
    logger.debug("faster-whisper not installed; transcriber will return empty results.")

# Default model size — small balances speed vs. accuracy on CPU.
DEFAULT_MODEL_SIZE = os.environ.get("ASFS_WHISPER_MODEL", "small")


def _whisper_model() -> Optional[object]:
    """Return a cached WhisperModel instance, or None if unavailable."""
    if not _WHISPER_AVAILABLE:
        return None
    try:
        return WhisperModel(DEFAULT_MODEL_SIZE, device="cpu", compute_type="int8")
    except Exception as exc:  # pragma: no cover
        logger.warning("WhisperModel init failed: %s", exc)
        return None


def transcribe(audio_path: str) -> Dict:
    """
    Transcribe *audio_path* and return a dict with word-level timestamps.

    Parameters
    ----------
    audio_path : str
        Absolute path to the audio/video file (WAV, MP3, MP4, etc.).

    Returns
    -------
    dict with keys:
        ``words``  – list of ``{"word": str, "start": float, "end": float}``
        ``text``   – full transcript as a single string
        ``viable`` – ``True`` if transcription succeeded and produced words

    Failure modes (non-viable):
        - File not found / unreadable
        - faster-whisper not installed
        - Model inference error
        - Empty transcript (< 3 words)
    """
    if not os.path.exists(audio_path):
        logger.warning("Transcriber: file not found — %s", audio_path)
        return {"words": [], "text": "", "viable": False}

    model = _whisper_model()
    if model is None:
        logger.warning("Transcriber: faster-whisper unavailable.")
        return {"words": [], "text": "", "viable": False}

    try:
        segments, _ = model.transcribe(
            audio_path,
            word_timestamps=True,
            vad_filter=True,
        )
        words: List[Dict] = []
        for seg in segments:
            if seg.words:
                for w in seg.words:
                    words.append({"word": w.word.strip(), "start": w.start, "end": w.end})

        full_text = " ".join(w["word"] for w in words)
        viable = len(words) >= 3

        if not viable:
            logger.warning(
                "Transcriber: transcript too short (%d words) — marking non-viable.", len(words)
            )

        return {"words": words, "text": full_text, "viable": viable}

    except Exception as exc:  # pragma: no cover
        logger.error("Transcriber: inference error — %s", exc)
        return {"words": [], "text": "", "viable": False}
