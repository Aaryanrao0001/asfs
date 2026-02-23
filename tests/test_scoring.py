#!/usr/bin/env python3
"""Unit tests for scoring v2 (controversy & novelty detection, deterministic final score)."""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from src.prompts.scoring_v2 import (
    compute_final_score_v2,
    build_scoring_v2_prompt,
    PLATFORM_CONTROVERSY_WEIGHT,
    BASE_WEIGHTS,
)


class TestControversyDetection(unittest.TestCase):
    """Scenario E — controversy_score affects final score."""

    def test_high_controversy_boosts_tiktok(self):
        base_data = {
            "hook_score": 7.0,
            "retention_score": 7.0,
            "emotion_score": 7.0,
            "relatability_score": 6.0,
            "completion_score": 6.0,
            "platform_fit_score": 6.0,
            "controversy_score": 0.0,
            "novelty_score": 0.0,
        }
        low_score = compute_final_score_v2(base_data, platform="tiktok")

        high_data = dict(base_data)
        high_data["controversy_score"] = 8.5
        high_score = compute_final_score_v2(high_data, platform="tiktok")

        self.assertGreater(high_score, low_score)

    def test_controversy_boost_higher_on_tiktok_than_shorts(self):
        data = {
            "hook_score": 7.0,
            "retention_score": 7.0,
            "emotion_score": 7.0,
            "relatability_score": 6.0,
            "completion_score": 6.0,
            "platform_fit_score": 6.0,
            "controversy_score": 8.0,
            "novelty_score": 0.0,
        }
        tiktok_score = compute_final_score_v2(data, platform="tiktok")
        shorts_score = compute_final_score_v2(data, platform="shorts")
        self.assertGreater(tiktok_score, shorts_score)


class TestDeterministicFinalScore(unittest.TestCase):
    """Final score is computed deterministically — no LLM call."""

    def test_same_input_same_output(self):
        data = {
            "hook_score": 8.0,
            "retention_score": 7.5,
            "emotion_score": 7.0,
            "relatability_score": 6.5,
            "completion_score": 7.0,
            "platform_fit_score": 6.0,
            "controversy_score": 5.0,
            "novelty_score": 4.0,
        }
        s1 = compute_final_score_v2(data, "tiktok")
        s2 = compute_final_score_v2(data, "tiktok")
        self.assertEqual(s1, s2)

    def test_returns_numeric(self):
        data = {
            "hook_score": 5.0,
            "retention_score": 5.0,
            "emotion_score": 5.0,
            "relatability_score": 5.0,
            "completion_score": 5.0,
            "platform_fit_score": 5.0,
            "controversy_score": 5.0,
            "novelty_score": 5.0,
        }
        result = compute_final_score_v2(data)
        self.assertIsInstance(result, float)

    def test_novelty_multiplier_effect(self):
        base = {
            "hook_score": 7.0,
            "retention_score": 7.0,
            "emotion_score": 7.0,
            "relatability_score": 6.0,
            "completion_score": 6.0,
            "platform_fit_score": 6.0,
            "controversy_score": 0.0,
            "novelty_score": 0.0,
        }
        score_no_novelty = compute_final_score_v2(base)

        high_novelty = dict(base)
        high_novelty["novelty_score"] = 10.0
        score_with_novelty = compute_final_score_v2(high_novelty)

        self.assertGreater(score_with_novelty, score_no_novelty)

    def test_base_weights_sum_to_one(self):
        self.assertAlmostEqual(sum(BASE_WEIGHTS.values()), 1.0, places=5)


class TestScoringV2Prompt(unittest.TestCase):
    """Prompt includes controversy and novelty fields."""

    def test_prompt_contains_new_fields(self):
        segments = [{"text": "Test text", "duration": 20.0}]
        prompt = build_scoring_v2_prompt(segments)
        self.assertIn("controversy_score", prompt)
        self.assertIn("novelty_score", prompt)
        self.assertIn("suggested_title", prompt)

    def test_prompt_anti_hallucination(self):
        segments = [{"text": "Test", "duration": 10.0}]
        prompt = build_scoring_v2_prompt(segments)
        self.assertIn("Return ONLY valid JSON", prompt)
        self.assertIn("No markdown", prompt)

    def test_prompt_instructs_no_final_score(self):
        segments = [{"text": "Test", "duration": 10.0}]
        prompt = build_scoring_v2_prompt(segments)
        self.assertIn("server-side", prompt)


if __name__ == "__main__":
    success = unittest.main(verbosity=2, exit=False).result.wasSuccessful()
    sys.exit(0 if success else 1)
