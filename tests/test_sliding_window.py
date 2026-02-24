#!/usr/bin/env python3
"""Unit tests for segmenter/sliding_window.py."""

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from segmenter.sliding_window import (
    build_sliding_windows,
    deduplicate_windows,
    compute_pace,
)


def _make_transcript(texts, seg_duration=10.0):
    """Build a minimal transcript_data dict from a list of texts."""
    segments = []
    t = 0.0
    for text in texts:
        segments.append({
            "start": t,
            "end": t + seg_duration,
            "text": text,
        })
        t += seg_duration
    return {"segments": segments}


class TestComputePace(unittest.TestCase):
    """Tests for compute_pace()."""

    def test_basic_pace(self):
        seg = {"text": "one two three four five", "start": 0.0, "end": 5.0}
        pace = compute_pace(seg)
        self.assertAlmostEqual(pace, 1.0, places=5)  # 5 words / 5 seconds

    def test_zero_duration(self):
        seg = {"text": "hello world", "start": 5.0, "end": 5.0}
        self.assertEqual(compute_pace(seg), 0.0)

    def test_empty_text(self):
        seg = {"text": "", "start": 0.0, "end": 10.0}
        self.assertEqual(compute_pace(seg), 0.0)

    def test_pace_value(self):
        seg = {"text": " ".join(["word"] * 30), "start": 0.0, "end": 10.0}
        self.assertAlmostEqual(compute_pace(seg), 3.0, places=5)


class TestBuildSlidingWindows(unittest.TestCase):
    """Tests for build_sliding_windows()."""

    def test_empty_transcript(self):
        result = build_sliding_windows({})
        self.assertEqual(result, [])

    def test_empty_segments(self):
        result = build_sliding_windows({"segments": []})
        self.assertEqual(result, [])

    def test_returns_list(self):
        transcript = _make_transcript(
            ["Sentence one. Sentence two."] * 10, seg_duration=10.0
        )
        result = build_sliding_windows(transcript, min_duration=20.0, max_duration=55.0, step_seconds=5.0)
        self.assertIsInstance(result, list)

    def test_candidates_have_required_fields(self):
        transcript = _make_transcript(
            ["This is a test sentence."] * 10, seg_duration=10.0
        )
        result = build_sliding_windows(transcript, min_duration=20.0, max_duration=55.0, step_seconds=5.0)
        if result:
            candidate = result[0]
            for field in ("start", "end", "duration", "text", "segment_count", "type",
                          "boundary_quality", "pace_wps", "slow_start"):
                self.assertIn(field, candidate, f"Missing field: {field}")

    def test_candidate_type_is_sliding_window(self):
        transcript = _make_transcript(
            ["Word " * 20] * 10, seg_duration=10.0
        )
        result = build_sliding_windows(transcript, min_duration=20.0, max_duration=55.0, step_seconds=5.0)
        for c in result:
            self.assertEqual(c["type"], "sliding_window")

    def test_candidate_duration_within_bounds(self):
        transcript = _make_transcript(
            ["A sentence here."] * 15, seg_duration=10.0
        )
        result = build_sliding_windows(transcript, min_duration=20.0, max_duration=55.0, step_seconds=5.0)
        for c in result:
            # Allow slight tolerance for boundary snapping
            self.assertGreaterEqual(c["duration"], 15.0)
            self.assertLessEqual(c["duration"], 60.0)

    def test_slow_start_flagged(self):
        # 2 words over 10 seconds = 0.2 wps in first 5s → slow_start should be True
        transcript = _make_transcript(["slow speech"] * 10, seg_duration=10.0)
        result = build_sliding_windows(transcript, min_duration=20.0, max_duration=55.0, step_seconds=5.0)
        # At least some candidates should be slow_start=True
        self.assertTrue(any(c["slow_start"] for c in result))

    def test_boundary_quality_values(self):
        transcript = _make_transcript(
            ["This is complete."] * 10, seg_duration=10.0
        )
        result = build_sliding_windows(transcript, min_duration=20.0, max_duration=55.0, step_seconds=5.0)
        for c in result:
            self.assertIn(c["boundary_quality"], (0.5, 1.0))


class TestDeduplicateWindows(unittest.TestCase):
    """Tests for deduplicate_windows()."""

    def test_empty_list(self):
        self.assertEqual(deduplicate_windows([]), [])

    def test_single_candidate_kept(self):
        candidates = [{"start": 0, "end": 30, "duration": 30, "boundary_quality": 1.0}]
        result = deduplicate_windows(candidates)
        self.assertEqual(len(result), 1)

    def test_non_overlapping_both_kept(self):
        candidates = [
            {"start": 0, "end": 30, "duration": 30, "boundary_quality": 1.0},
            {"start": 60, "end": 90, "duration": 30, "boundary_quality": 1.0},
        ]
        result = deduplicate_windows(candidates)
        self.assertEqual(len(result), 2)

    def test_heavily_overlapping_deduplicated(self):
        candidates = [
            {"start": 0, "end": 30, "duration": 30, "boundary_quality": 1.0},
            {"start": 1, "end": 31, "duration": 30, "boundary_quality": 0.5},
        ]
        result = deduplicate_windows(candidates, overlap_threshold=0.7)
        self.assertEqual(len(result), 1)

    def test_keeps_better_boundary_quality(self):
        candidates = [
            {"start": 0, "end": 30, "duration": 30, "boundary_quality": 0.5},
            {"start": 1, "end": 31, "duration": 30, "boundary_quality": 1.0},
        ]
        result = deduplicate_windows(candidates, overlap_threshold=0.7)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["boundary_quality"], 1.0)

    def test_partial_overlap_both_kept(self):
        # 10s overlap out of 30s = 33% — below 70% threshold
        candidates = [
            {"start": 0, "end": 30, "duration": 30, "boundary_quality": 1.0},
            {"start": 20, "end": 50, "duration": 30, "boundary_quality": 1.0},
        ]
        result = deduplicate_windows(candidates, overlap_threshold=0.7)
        self.assertEqual(len(result), 2)


if __name__ == "__main__":
    success = unittest.main(verbosity=2, exit=False).result.wasSuccessful()
    sys.exit(0 if success else 1)
