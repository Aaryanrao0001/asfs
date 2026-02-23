#!/usr/bin/env python3
"""Unit tests for transcript fallback title / description generation."""

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock

# Mock faster_whisper before importing any transcript module so that tests
# can run without the optional ML dependency installed.
sys.modules.setdefault("faster_whisper", MagicMock())

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from transcript.fallback import (
    clean_filler_words,
    generate_fallback_description,
    generate_fallback_title,
    load_transcript_if_exists,
    TITLE_MAX_LENGTH,
    DESC_MAX_LENGTH,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_transcript(*texts):
    """Build a minimal transcript dict from a sequence of segment texts."""
    return {
        "segments": [
            {"start": i * 5.0, "end": (i + 1) * 5.0, "text": t}
            for i, t in enumerate(texts)
        ]
    }


# ---------------------------------------------------------------------------
# clean_filler_words
# ---------------------------------------------------------------------------


class TestCleanFillerWords(unittest.TestCase):
    def test_removes_um(self):
        self.assertNotIn("um", clean_filler_words("um this is a test"))

    def test_removes_uh(self):
        self.assertNotIn("uh", clean_filler_words("uh wait a second"))

    def test_removes_you_know(self):
        result = clean_filler_words("you know this is important")
        self.assertNotIn("you know", result)

    def test_removes_i_mean(self):
        result = clean_filler_words("I mean the data shows growth")
        self.assertNotIn("i mean", result.lower())

    def test_preserves_meaningful_words(self):
        result = clean_filler_words("The market grew by 20 percent")
        self.assertIn("market", result)
        self.assertIn("20", result)

    def test_handles_empty_string(self):
        self.assertEqual(clean_filler_words(""), "")

    def test_collapses_extra_spaces(self):
        result = clean_filler_words("hello   world")
        self.assertNotIn("  ", result)

    def test_case_insensitive(self):
        result = clean_filler_words("Um this is a test")
        self.assertFalse(result.lower().startswith("um "))


# ---------------------------------------------------------------------------
# generate_fallback_title
# ---------------------------------------------------------------------------


class TestGenerateFallbackTitle(unittest.TestCase):
    def test_returns_string(self):
        t = _make_transcript("um so the stock market is up today")
        result = generate_fallback_title(t)
        self.assertIsInstance(result, str)

    def test_removes_filler_words(self):
        t = _make_transcript("um uh you know this is really important")
        result = generate_fallback_title(t)
        self.assertNotIn("um", result.lower())
        self.assertNotIn("uh", result.lower())

    def test_capitalised(self):
        t = _make_transcript("the quick brown fox jumps over the lazy dog")
        result = generate_fallback_title(t)
        if result:
            self.assertTrue(result[0].isupper())

    def test_respects_max_length(self):
        long_text = "This is a very long sentence " * 20
        t = _make_transcript(long_text)
        result = generate_fallback_title(t)
        self.assertLessEqual(len(result), TITLE_MAX_LENGTH)

    def test_empty_transcript(self):
        result = generate_fallback_title({"segments": []})
        self.assertEqual(result, "")

    def test_picks_longest_segment(self):
        t = _make_transcript(
            "Hi",
            "Artificial intelligence is transforming the healthcare industry rapidly",
        )
        result = generate_fallback_title(t)
        # The longer segment should be preferred
        self.assertIn("Artificial", result)

    def test_no_segments_key(self):
        result = generate_fallback_title({})
        self.assertEqual(result, "")


# ---------------------------------------------------------------------------
# generate_fallback_description
# ---------------------------------------------------------------------------


class TestGenerateFallbackDescription(unittest.TestCase):
    def test_returns_string(self):
        t = _make_transcript("This is an interesting topic about machine learning")
        result = generate_fallback_description(t)
        self.assertIsInstance(result, str)

    def test_respects_max_length(self):
        long_text = "This segment contains a lot of information. " * 30
        t = _make_transcript(long_text)
        result = generate_fallback_description(t)
        self.assertLessEqual(len(result), DESC_MAX_LENGTH)

    def test_empty_transcript(self):
        result = generate_fallback_description({"segments": []})
        self.assertEqual(result, "")

    def test_concatenates_multiple_segments(self):
        t = _make_transcript(
            "First important point here.",
            "Second key takeaway you need to know.",
            "Third insight for the audience.",
        )
        result = generate_fallback_description(t)
        self.assertGreater(len(result), 0)

    def test_removes_filler_words(self):
        t = _make_transcript("um uh you know basically this is important")
        result = generate_fallback_description(t)
        self.assertNotIn("um", result.lower())


# ---------------------------------------------------------------------------
# load_transcript_if_exists
# ---------------------------------------------------------------------------


class TestLoadTranscriptIfExists(unittest.TestCase):
    def _write_transcript(self, output_dir, segments):
        work_dir = os.path.join(output_dir, "work")
        os.makedirs(work_dir, exist_ok=True)
        path = os.path.join(work_dir, "transcript.json")
        data = {"segments": segments}
        with open(path, "w") as fh:
            json.dump(data, fh)
        # Fake clip path: output_dir/clips/clip_001.mp4
        clips_dir = os.path.join(output_dir, "clips")
        os.makedirs(clips_dir, exist_ok=True)
        return os.path.join(clips_dir, "clip_001.mp4")

    def test_loads_valid_transcript(self):
        with tempfile.TemporaryDirectory() as tmp:
            segments = [{"start": 0, "end": 5, "text": "Hello world"}]
            clip_path = self._write_transcript(tmp, segments)
            result = load_transcript_if_exists(clip_path)
            self.assertIsNotNone(result)
            self.assertEqual(len(result["segments"]), 1)

    def test_returns_none_if_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            clip_path = os.path.join(tmp, "clips", "clip_001.mp4")
            os.makedirs(os.path.dirname(clip_path), exist_ok=True)
            result = load_transcript_if_exists(clip_path)
            self.assertIsNone(result)

    def test_returns_none_for_empty_segments(self):
        with tempfile.TemporaryDirectory() as tmp:
            clip_path = self._write_transcript(tmp, [])
            result = load_transcript_if_exists(clip_path)
            self.assertIsNone(result)

    def test_returns_none_for_corrupt_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = os.path.join(tmp, "work")
            os.makedirs(work_dir, exist_ok=True)
            with open(os.path.join(work_dir, "transcript.json"), "w") as fh:
                fh.write("not valid json {{{")
            clips_dir = os.path.join(tmp, "clips")
            os.makedirs(clips_dir, exist_ok=True)
            clip_path = os.path.join(clips_dir, "clip_001.mp4")
            result = load_transcript_if_exists(clip_path)
            self.assertIsNone(result)


if __name__ == "__main__":
    success = unittest.main(verbosity=2, exit=False).result.wasSuccessful()
    sys.exit(0 if success else 1)
