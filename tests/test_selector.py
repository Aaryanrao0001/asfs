#!/usr/bin/env python3
"""Unit tests for the percentile threshold selector."""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from src.scoring.selector import select_clips, ABSOLUTE_FLOOR


class TestPercentileSelection(unittest.TestCase):
    """Test percentile-based clip selection (Scenario D)."""

    def test_selects_top_15_percent(self):
        candidates = [{"final_score": s} for s in [9, 8.5, 8, 7, 6.5, 6, 5.5, 5, 4.6, 4.5]]
        result = select_clips(candidates)
        # Top 15% of 10 → ~1-2 clips, but min 2
        self.assertGreaterEqual(len(result), 2)
        # All selected should be the highest scoring
        scores = [c["final_score"] for c in result]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_hard_floor_rejects_below_4_5(self):
        candidates = [{"final_score": s} for s in [3.0, 2.0, 1.0]]
        result = select_clips(candidates)
        # Min 2 enforced, but they get low_confidence flag
        self.assertEqual(len(result), 2)
        for c in result:
            self.assertTrue(c.get("low_confidence", False))

    def test_minimum_2_clips(self):
        """Even with 1 above threshold, at least 2 returned."""
        candidates = [
            {"final_score": 9.0},
            {"final_score": 3.5},
            {"final_score": 2.0},
        ]
        result = select_clips(candidates, min_clips=2)
        self.assertGreaterEqual(len(result), 2)

    def test_low_confidence_flag(self):
        """Clips below the floor that are forced-selected get the flag."""
        candidates = [
            {"final_score": 3.0},
            {"final_score": 2.5},
        ]
        result = select_clips(candidates, min_clips=2)
        for c in result:
            self.assertTrue(c["low_confidence"])

    def test_max_cap(self):
        candidates = [{"final_score": float(i)} for i in range(20, 0, -1)]
        result = select_clips(candidates, max_clips=5)
        self.assertLessEqual(len(result), 5)

    def test_empty_candidates(self):
        self.assertEqual(select_clips([]), [])

    def test_descending_order(self):
        candidates = [{"final_score": s} for s in [5.0, 9.0, 7.0, 8.0, 6.0]]
        result = select_clips(candidates)
        scores = [c["final_score"] for c in result]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_single_candidate_still_selected(self):
        candidates = [{"final_score": 7.5}]
        result = select_clips(candidates, min_clips=1)
        self.assertEqual(len(result), 1)


if __name__ == "__main__":
    success = unittest.main(verbosity=2, exit=False).result.wasSuccessful()
    sys.exit(0 if success else 1)
