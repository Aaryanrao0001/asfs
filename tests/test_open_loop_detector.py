#!/usr/bin/env python3
"""Unit tests for segmenter/open_loop_detector.py."""

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from segmenter.open_loop_detector import (
    has_open_loop,
    has_bad_opening,
    close_open_loops,
    snap_start_boundary,
    snap_end_boundary,
    check_curiosity_gap,
    MAX_MERGED_DURATION,
)


class TestHasOpenLoop(unittest.TestCase):
    """Tests for has_open_loop()."""

    def test_trailing_connector_and(self):
        self.assertTrue(has_open_loop("I was walking and"))

    def test_trailing_connector_but(self):
        self.assertTrue(has_open_loop("She said yes but"))

    def test_trailing_connector_because(self):
        self.assertTrue(has_open_loop("I did it because"))

    def test_setup_phrase_heres_what_happened(self):
        self.assertTrue(has_open_loop("here's what happened"))

    def test_setup_phrase_you_wont_believe(self):
        self.assertTrue(has_open_loop("you won't believe"))

    def test_setup_phrase_i_was_about_to(self):
        self.assertTrue(has_open_loop("I was about to"))

    def test_no_terminal_punctuation(self):
        self.assertTrue(has_open_loop("This is a sentence without punctuation"))

    def test_incomplete_list_first_without_second(self):
        self.assertTrue(has_open_loop("First, you need to do this."))

    def test_complete_list_with_second(self):
        self.assertFalse(has_open_loop("First, do A. Second, do B."))

    def test_question_without_answer(self):
        self.assertTrue(has_open_loop("What should we do?"))

    def test_question_with_answer(self):
        self.assertFalse(has_open_loop("What should we do? We should run."))

    def test_complete_sentence(self):
        self.assertFalse(has_open_loop("This is a complete sentence."))

    def test_complete_exclamation(self):
        self.assertFalse(has_open_loop("That was amazing!"))

    def test_empty_string(self):
        self.assertFalse(has_open_loop(""))

    def test_whitespace_only(self):
        self.assertFalse(has_open_loop("   "))


class TestHasBadOpening(unittest.TestCase):
    """Tests for has_bad_opening()."""

    def test_starts_with_and(self):
        self.assertTrue(has_bad_opening("And then it happened."))

    def test_starts_with_but(self):
        self.assertTrue(has_bad_opening("But that's not all."))

    def test_starts_with_so(self):
        self.assertTrue(has_bad_opening("So I decided to go."))

    def test_starts_with_furthermore(self):
        self.assertTrue(has_bad_opening("Furthermore, this is important."))

    def test_starts_with_additionally(self):
        self.assertTrue(has_bad_opening("Additionally, we found out."))

    def test_normal_opening(self):
        self.assertFalse(has_bad_opening("I woke up this morning."))

    def test_capital_normal(self):
        self.assertFalse(has_bad_opening("The cat sat on the mat."))

    def test_empty_string(self):
        self.assertFalse(has_bad_opening(""))

    def test_single_continuation_word(self):
        self.assertTrue(has_bad_opening("also"))


class TestCloseOpenLoops(unittest.TestCase):
    """Tests for close_open_loops()."""

    def _make_segments(self, texts, start=0.0, duration=5.0):
        """Helper to build a list of segment dicts."""
        segs = []
        t = start
        for text in texts:
            segs.append({"start": t, "end": t + duration, "text": text})
            t += duration
        return segs

    def test_empty_list(self):
        self.assertEqual(close_open_loops([]), [])

    def test_no_open_loops(self):
        segs = self._make_segments([
            "This is complete.",
            "So is this one.",
            "And this too!",
        ])
        result = close_open_loops(segs)
        self.assertEqual(len(result), 3)

    def test_merges_open_loop_forward(self):
        segs = self._make_segments([
            "I was about to",       # open loop
            "hit the button.",      # payoff
            "And it worked.",
        ])
        result = close_open_loops(segs)
        # First two should be merged
        self.assertEqual(len(result), 2)
        self.assertIn("hit the button", result[0]["text"])

    def test_does_not_exceed_max_duration(self):
        # Create many short segments all with open loops
        segs = []
        t = 0.0
        for i in range(30):
            segs.append({"start": t, "end": t + 5.0, "text": f"segment {i} and"})
            t += 5.0
        result = close_open_loops(segs)
        # Should stop merging when MAX_MERGED_DURATION is reached
        for seg in result:
            dur = seg["end"] - seg["start"]
            self.assertLessEqual(dur, MAX_MERGED_DURATION + 5.0)  # small tolerance

    def test_merges_words_field(self):
        segs = [
            {"start": 0.0, "end": 5.0, "text": "hello and", "words": [{"word": "hello", "start": 0.0, "end": 0.5}]},
            {"start": 5.0, "end": 10.0, "text": "goodbye.", "words": [{"word": "goodbye", "start": 5.0, "end": 5.5}]},
        ]
        result = close_open_loops(segs)
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0]["words"]), 2)


class TestSnapBoundaries(unittest.TestCase):
    """Tests for snap_start_boundary() and snap_end_boundary()."""

    def _make_segments(self, texts):
        segs = []
        for i, text in enumerate(texts):
            segs.append({"start": float(i * 5), "end": float((i + 1) * 5), "text": text})
        return segs

    def test_snap_start_no_change_needed(self):
        segs = self._make_segments(["This is fine.", "And this continues."])
        idx = snap_start_boundary(segs, 0)
        self.assertEqual(idx, 0)

    def test_snap_start_walks_back(self):
        segs = self._make_segments(["Start here.", "And continues."])
        # Index 1 has bad opening; should walk back to 0
        idx = snap_start_boundary(segs, 1)
        self.assertEqual(idx, 0)

    def test_snap_end_no_change_needed(self):
        segs = self._make_segments(["Complete sentence.", "Another one."])
        idx = snap_end_boundary(segs, 0)
        self.assertEqual(idx, 0)

    def test_snap_end_walks_forward(self):
        segs = self._make_segments(["I was about to", "do something."])
        idx = snap_end_boundary(segs, 0)
        self.assertEqual(idx, 1)

    def test_snap_end_does_not_exceed_list(self):
        segs = self._make_segments(["Last segment and"])
        idx = snap_end_boundary(segs, 0)
        self.assertEqual(idx, 0)  # Can't go beyond end


class TestCheckCuriosityGap(unittest.TestCase):
    """Tests for check_curiosity_gap()."""

    def test_no_question(self):
        result = check_curiosity_gap("This has no question.")
        self.assertFalse(result["has_question"])
        self.assertEqual(result["answer_distance_words"], 0)

    def test_question_at_end_of_segment(self):
        result = check_curiosity_gap("What is the secret?")
        self.assertTrue(result["has_question"])
        self.assertEqual(result["answer_distance_words"], 9999)

    def test_question_answered_immediately(self):
        result = check_curiosity_gap("What is it? A dog.")
        self.assertTrue(result["has_question"])
        self.assertLessEqual(result["answer_distance_words"], 5)

    def test_question_answered_far_away(self):
        result = check_curiosity_gap(
            "What is the meaning of life? Well, after a long journey "
            "through philosophy, science, and personal experience, "
            "I believe it is to find joy."
        )
        self.assertTrue(result["has_question"])
        self.assertGreater(result["answer_distance_words"], 5)


if __name__ == "__main__":
    success = unittest.main(verbosity=2, exit=False).result.wasSuccessful()
    sys.exit(0 if success else 1)
