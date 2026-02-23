#!/usr/bin/env python3
"""Unit tests for the hook enforcement module."""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from src.pipeline.hook_enforcer import (
    enforce_hook,
    _has_interrupt_signal,
    _find_best_peak,
    MIN_CLIP_DURATION,
    MIN_SEGMENT_FOR_RECUT,
)


def _make_tokens(words_with_times):
    """Helper: list of (text, start, end) → token dicts."""
    return [
        {"text": w, "start": s, "end": e}
        for w, s, e in words_with_times
    ]


class TestInterruptSignal(unittest.TestCase):
    """Test the 2-second interrupt detection."""

    def test_question_mark_is_interrupt(self):
        tokens = _make_tokens([("Why?", 0.5, 1.0)])
        self.assertTrue(_has_interrupt_signal(tokens))

    def test_emotion_keyword_is_interrupt(self):
        tokens = _make_tokens([("bankrupt", 0.8, 1.2)])
        self.assertTrue(_has_interrupt_signal(tokens))

    def test_filler_only_no_interrupt(self):
        tokens = _make_tokens([("um", 0.2, 0.5), ("so", 0.6, 0.9), ("like", 1.0, 1.3)])
        self.assertFalse(_has_interrupt_signal(tokens))

    def test_non_filler_before_1_5s_is_interrupt(self):
        tokens = _make_tokens([("amazing", 0.3, 0.7)])
        self.assertTrue(_has_interrupt_signal(tokens))

    def test_token_after_window_ignored(self):
        tokens = _make_tokens([("um", 0.2, 0.5), ("bankrupt", 2.5, 3.0)])
        self.assertFalse(_has_interrupt_signal(tokens))


class TestHookEnforcer(unittest.TestCase):
    """Test hook enforcement and recut logic."""

    def test_hook_found_in_first_2s(self):
        """Scenario A: hook already present — no recut needed."""
        tokens = _make_tokens([
            ("Why?", 0.5, 1.0),
            ("because", 1.5, 2.0),
            ("it", 2.5, 3.0),
            ("matters", 3.5, 4.0),
        ])
        seg = {"start": 0.0, "end": 20.0}
        result = enforce_hook(seg, tokens, 0.0, 20.0)

        self.assertTrue(result["hook_metadata"]["hook_found"])
        self.assertFalse(result["hook_metadata"]["recut_applied"])

    def test_mid_segment_recut(self):
        """Scenario A delayed hook: filler at start, emotion peak later."""
        tokens = _make_tokens([
            ("um", 0.2, 0.4),
            ("so", 0.5, 0.8),
            ("like", 1.0, 1.3),
            ("uh", 1.5, 1.8),
            ("we", 2.0, 2.3),
            ("almost", 3.0, 3.3),
            ("went", 3.5, 3.8),
            ("bankrupt", 4.8, 5.3),
            ("three", 5.5, 5.8),
            ("times", 6.0, 6.3),
        ])
        seg = {"start": 0.0, "end": 30.0}
        result = enforce_hook(seg, tokens, 0.0, 30.0)

        self.assertTrue(result["hook_metadata"]["hook_found"])
        self.assertTrue(result["hook_metadata"]["recut_applied"])
        self.assertEqual(result["hook_metadata"]["recut_source"], "mid_segment")
        # New start should be before the peak
        self.assertGreater(result["start"], 0.0)

    def test_short_segment_no_recut(self):
        """Edge case: segment < 10s skips recut."""
        tokens = _make_tokens([
            ("um", 0.2, 0.5),
            ("so", 1.0, 1.3),
        ])
        seg = {"start": 0.0, "end": 8.0}
        result = enforce_hook(seg, tokens, 0.0, 8.0)

        self.assertFalse(result["hook_metadata"]["hook_found"])
        self.assertFalse(result["hook_metadata"]["recut_applied"])

    def test_no_peak_found(self):
        """All filler, no emotion keywords — recut_failed flag set."""
        tokens = _make_tokens([
            ("um", 0.2, 0.5),
            ("so", 1.0, 1.3),
            ("uh", 3.0, 3.3),
            ("well", 5.0, 5.3),
            ("and", 7.0, 7.3),
        ])
        seg = {"start": 0.0, "end": 20.0}
        result = enforce_hook(seg, tokens, 0.0, 20.0)

        self.assertFalse(result["hook_metadata"]["hook_found"])
        self.assertTrue(result.get("recut_failed", False))

    def test_recut_clamps_to_segment_end(self):
        """Recut end should not exceed segment boundary."""
        tokens = _make_tokens([
            ("um", 0.2, 0.5),
            ("like", 1.0, 1.3),
            ("secret", 25.0, 25.5),
        ])
        seg = {"start": 0.0, "end": 28.0}
        result = enforce_hook(seg, tokens, 0.0, 28.0)

        self.assertLessEqual(result.get("end", 28.0), 28.0)


class TestFindBestPeak(unittest.TestCase):
    """Test peak detection across segment."""

    def test_single_peak(self):
        tokens = _make_tokens([("bankrupt", 5.0, 5.5)])
        peak = _find_best_peak(tokens, 10.0)
        self.assertIsNotNone(peak)
        self.assertAlmostEqual(peak, 5.0, delta=1.5)

    def test_multiple_peaks_selects_strongest(self):
        tokens = _make_tokens([
            ("secret", 3.0, 3.5),
            ("bankrupt", 7.0, 7.5),
            ("died", 7.2, 7.6),
        ])
        peak = _find_best_peak(tokens, 10.0)
        # The cluster at 7.0-7.2 has 2 keywords → should be highest
        self.assertIsNotNone(peak)
        self.assertGreaterEqual(peak, 6.0)

    def test_empty_tokens(self):
        self.assertIsNone(_find_best_peak([], 10.0))


if __name__ == "__main__":
    success = unittest.main(verbosity=2, exit=False).result.wasSuccessful()
    sys.exit(0 if success else 1)
