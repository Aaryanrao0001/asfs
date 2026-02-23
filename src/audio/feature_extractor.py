"""
Audio Feature Extractor — RMS energy, silence ratio, and speech-rate features.

Uses numpy for core signal processing.  librosa is used when available for more
accurate RMS computation (e.g. hop-length aware framing), but all features
degrade gracefully to numpy-only implementations when librosa is absent.

All public functions operate on raw PCM samples (float32 arrays) plus a sample
rate.  The :func:`extract_features` entry point accepts a file path and handles
loading via librosa when available.

Activated only when ``ASFS_AUDIO_SCORING=true``.
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

# Optional librosa import — gracefully degraded when missing.
try:
    import librosa  # type: ignore
    import numpy as _np  # type: ignore

    _LIBROSA_AVAILABLE = True
    _NUMPY_AVAILABLE = True
except ImportError:
    _LIBROSA_AVAILABLE = False
    try:
        import numpy as _np  # type: ignore

        _NUMPY_AVAILABLE = True
    except ImportError:
        _NUMPY_AVAILABLE = False

# Silence threshold: samples below this RMS amplitude are considered silent.
SILENCE_RMS_THRESHOLD = 0.01
# Frame size (seconds) used for RMS windowing when numpy-only.
RMS_FRAME_SEC = 0.025
# Default hop size relative to frame size.
RMS_HOP_RATIO = 0.5
# Decimal places for rounding all returned float features.
FEATURE_PRECISION = 4


def _rms_numpy(samples, sample_rate: int) -> List[float]:
    """Compute per-frame RMS using pure numpy."""
    frame_len = max(1, int(RMS_FRAME_SEC * sample_rate))
    hop_len = max(1, int(frame_len * RMS_HOP_RATIO))
    rms_frames = []
    i = 0
    n = len(samples)
    while i + frame_len <= n:
        frame = samples[i : i + frame_len]
        rms_frames.append(float(_np.sqrt(_np.mean(frame ** 2))))
        i += hop_len
    return rms_frames if rms_frames else [0.0]


def _rms_librosa(samples, sample_rate: int) -> List[float]:
    """Compute per-frame RMS using librosa."""
    rms = librosa.feature.rms(y=samples)[0]
    return [float(v) for v in rms]


def _load_audio(audio_path: str):
    """
    Load audio file and return (samples, sample_rate).

    Returns (None, None) on failure.
    """
    if _LIBROSA_AVAILABLE:
        try:
            samples, sr = librosa.load(audio_path, sr=None, mono=True)
            return samples, sr
        except Exception as exc:
            logger.warning("Feature extractor: librosa load failed — %s", exc)
            return None, None

    # numpy-only: cannot load arbitrary audio files without librosa/soundfile.
    logger.warning("Feature extractor: librosa unavailable — cannot load audio from path.")
    return None, None


def compute_rms_frames(samples, sample_rate: int) -> List[float]:
    """
    Return per-frame RMS values for *samples*.

    Uses librosa when available, otherwise pure numpy.
    """
    if not _NUMPY_AVAILABLE:
        return [0.0]
    if _LIBROSA_AVAILABLE:
        return _rms_librosa(samples, sample_rate)
    return _rms_numpy(samples, sample_rate)


def compute_silence_ratio(rms_frames: List[float], threshold: float = SILENCE_RMS_THRESHOLD) -> float:
    """
    Return the fraction of frames whose RMS is below *threshold*.

    Parameters
    ----------
    rms_frames : list[float]
        Per-frame RMS values.
    threshold : float
        Silence boundary.

    Returns
    -------
    float
        Silence ratio in [0, 1].
    """
    if not rms_frames:
        return 1.0
    silent = sum(1 for r in rms_frames if r < threshold)
    return round(silent / len(rms_frames), 4)


def compute_speech_rate(words: List[Dict], duration_sec: float) -> float:
    """
    Compute words-per-second speech rate.

    Parameters
    ----------
    words : list[dict]
        Word dicts with ``"word"`` key (from transcriber output).
    duration_sec : float
        Total audio duration in seconds.

    Returns
    -------
    float
        Words per second, or 0.0 if duration ≤ 0.
    """
    if duration_sec <= 0 or not words:
        return 0.0
    return round(len(words) / duration_sec, 4)


def extract_features(audio_path: str, words: List[Dict]) -> Dict:
    """
    Extract audio features from *audio_path* given transcribed *words*.

    Parameters
    ----------
    audio_path : str
        Path to the audio file.
    words : list[dict]
        Word-timestamp dicts from :func:`src.audio.transcriber.transcribe`.

    Returns
    -------
    dict with keys:
        ``mean_rms``       – mean RMS energy across all frames (float)
        ``silence_ratio``  – fraction of silent frames (float)
        ``speech_rate``    – words per second (float)
        ``viable``         – False when audio could not be loaded
    """
    samples, sample_rate = _load_audio(audio_path)

    if samples is None or sample_rate is None:
        return {
            "mean_rms": 0.0,
            "silence_ratio": 1.0,
            "speech_rate": 0.0,
            "viable": False,
        }

    rms_frames = compute_rms_frames(samples, sample_rate)
    mean_rms = round(float(sum(rms_frames) / len(rms_frames)) if rms_frames else 0.0, FEATURE_PRECISION)
    silence_ratio = compute_silence_ratio(rms_frames)

    duration_sec = len(samples) / sample_rate if sample_rate > 0 else 0.0
    speech_rate = compute_speech_rate(words, duration_sec)

    return {
        "mean_rms": mean_rms,
        "silence_ratio": silence_ratio,
        "speech_rate": speech_rate,
        "viable": True,
    }
