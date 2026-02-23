#!/usr/bin/env python3
"""Unit tests for the scoring module."""

import json
import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestConfig(unittest.TestCase):
    """Verify config constants are present and sane."""

    def test_model_name(self):
        from scoring.config import MODEL_NAME
        self.assertEqual(MODEL_NAME, "gpt-4o-mini")

    def test_weights_sum_to_one(self):
        from scoring.config import WEIGHTS
        self.assertAlmostEqual(sum(WEIGHTS.values()), 1.0, places=5)

    def test_endpoint_is_azure(self):
        from scoring.config import ENDPOINT
        self.assertIn("azure", ENDPOINT)


class TestCalibrator(unittest.TestCase):
    """Verify deterministic score calculation."""

    def _data(self, **kwargs):
        base = {
            "hook_score": 8.0,
            "retention_score": 7.0,
            "emotion_score": 7.0,
            "completion_score": 7.0,
            "relatability_score": 6.0,
            "platform_fit_score": 6.0,
        }
        base.update(kwargs)
        return base

    def test_basic_score_range(self):
        from scoring.calibrator import compute_final_score
        score = compute_final_score(self._data(), duration=30)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_low_hook_caps_at_50(self):
        from scoring.calibrator import compute_final_score
        score = compute_final_score(self._data(hook_score=3.0), duration=30)
        self.assertLessEqual(score, 50)

    def test_low_emotion_caps_at_60(self):
        from scoring.calibrator import compute_final_score
        score = compute_final_score(self._data(emotion_score=2.0), duration=30)
        self.assertLessEqual(score, 60)

    def test_long_duration_penalty(self):
        from scoring.calibrator import compute_final_score
        short_score = compute_final_score(self._data(), duration=30)
        long_score = compute_final_score(self._data(), duration=90)
        self.assertGreater(short_score, long_score)

    def test_score_never_negative(self):
        from scoring.calibrator import compute_final_score
        zeros = {k: 0.0 for k in self._data()}
        score = compute_final_score(zeros, duration=120)
        self.assertGreaterEqual(score, 0)

    def test_returns_integer(self):
        from scoring.calibrator import compute_final_score
        score = compute_final_score(self._data(), duration=30)
        self.assertIsInstance(score, int)


class TestParser(unittest.TestCase):
    """Verify JSON extraction and score clamping."""

    def test_clean_json(self):
        from scoring.parser import parse_json
        raw = '{"segments": [{"hook_score": 7}]}'
        data = parse_json(raw)
        self.assertIn("segments", data)

    def test_markdown_wrapped_json(self):
        from scoring.parser import parse_json
        raw = '```json\n{"hook_score": 7}\n```'
        data = parse_json(raw)
        self.assertEqual(data["hook_score"], 7)

    def test_raises_on_empty(self):
        from scoring.parser import parse_json
        with self.assertRaises(ValueError):
            parse_json("")

    def test_extract_score_clamped(self):
        from scoring.parser import extract_score
        self.assertEqual(extract_score({"hook_score": 15}, "hook_score"), 10.0)
        self.assertEqual(extract_score({"hook_score": -5}, "hook_score"), 0.0)

    def test_extract_score_default(self):
        from scoring.parser import extract_score
        self.assertEqual(extract_score({}, "hook_score", default=5.0), 5.0)

    def test_validate_batch_response(self):
        from scoring.parser import validate_batch_response
        data = {"segments": [{"hook_score": 7}, {"hook_score": 6}]}
        segs = validate_batch_response(data, 2)
        self.assertEqual(len(segs), 2)


class TestPromptBuilder(unittest.TestCase):
    """Verify prompt construction."""

    def test_contains_segment_count(self):
        from scoring.prompt_builder import build_batch_prompt
        segments = [
            {"text": "This is shocking news!", "duration": 20},
            {"text": "Another great clip", "duration": 30},
        ]
        prompt = build_batch_prompt(segments)
        self.assertIn("2", prompt)
        self.assertIn("SEGMENT 1", prompt)
        self.assertIn("SEGMENT 2", prompt)

    def test_contains_segment_text(self):
        from scoring.prompt_builder import build_batch_prompt
        segments = [{"text": "unique_marker_text", "duration": 15}]
        prompt = build_batch_prompt(segments)
        self.assertIn("unique_marker_text", prompt)

    def test_instructs_no_final_score(self):
        from scoring.prompt_builder import build_batch_prompt
        segments = [{"text": "test text", "duration": 25}]
        prompt = build_batch_prompt(segments)
        self.assertIn("server-side", prompt)


class TestViralScoringEngine(unittest.TestCase):
    """Test the engine orchestration with a stubbed LLM."""

    def _make_llm_response(self, n: int, hook: float = 8, emotion: float = 7):
        """Build a fake JSON response for n segments."""
        segs = [
            {
                "segment_id": i + 1,
                "hook_score": hook,
                "retention_score": 7.0,
                "emotion_score": emotion,
                "completion_score": 7.0,
                "relatability_score": 6.0,
                "platform_fit_score": 6.0,
                "key_strengths": ["good hook"],
                "key_weaknesses": [],
                "first_3_seconds": "test",
                "primary_emotion": "shock",
                "optimal_platform": "tiktok",
            }
            for i in range(n)
        ]
        return json.dumps({"segments": segs})

    def test_returns_same_count(self):
        from scoring.engine import ViralScoringEngine
        engine = ViralScoringEngine.__new__(ViralScoringEngine)
        engine.batch_size = 5

        segments = [{"text": f"seg {i}", "duration": 25} for i in range(4)]
        results = engine.score_segments(
            segments,
            llm_scorer_func=lambda p: self._make_llm_response(4),
        )
        self.assertEqual(len(results), 4)

    def test_final_score_computed_serverside(self):
        """final_score must be an int computed by calibrator, not from LLM."""
        from scoring.engine import ViralScoringEngine
        engine = ViralScoringEngine.__new__(ViralScoringEngine)
        engine.batch_size = 5

        segments = [{"text": "test", "duration": 30}]
        results = engine.score_segments(
            segments,
            llm_scorer_func=lambda p: self._make_llm_response(1, hook=8, emotion=7),
        )
        self.assertIsInstance(results[0]["final_score"], int)

    def test_verdicts_assigned(self):
        from scoring.engine import ViralScoringEngine
        engine = ViralScoringEngine.__new__(ViralScoringEngine)
        engine.batch_size = 5

        segments = [{"text": f"seg {i}", "duration": 25} for i in range(10)]
        results = engine.score_segments(
            segments,
            llm_scorer_func=lambda p: self._make_llm_response(len(segments)),
        )
        verdicts = {r["verdict"] for r in results}
        # With identical scores, first segment is "viral", rest varies
        self.assertTrue(verdicts.issubset({"viral", "maybe", "skip"}))

    def test_top_segment_is_viral(self):
        """Segment with highest score must receive 'viral' verdict."""
        from scoring.engine import ViralScoringEngine
        engine = ViralScoringEngine.__new__(ViralScoringEngine)
        engine.batch_size = 10

        def varied_response(prompt):
            # Return 10 segments with declining scores
            segs = [
                {
                    "segment_id": i + 1,
                    "hook_score": max(0, 9 - i),
                    "retention_score": max(0, 9 - i),
                    "emotion_score": max(0, 9 - i),
                    "completion_score": 7.0,
                    "relatability_score": 6.0,
                    "platform_fit_score": 6.0,
                    "key_strengths": [],
                    "key_weaknesses": [],
                    "first_3_seconds": "",
                    "primary_emotion": "neutral",
                    "optimal_platform": "tiktok",
                }
                for i in range(10)
            ]
            return json.dumps({"segments": segs})

        segments = [{"text": f"seg {i}", "duration": 25} for i in range(10)]
        results = engine.score_segments(segments, llm_scorer_func=varied_response)
        self.assertEqual(results[0]["verdict"], "viral")

    def test_fallback_on_bad_llm_response(self):
        from scoring.engine import ViralScoringEngine
        engine = ViralScoringEngine.__new__(ViralScoringEngine)
        engine.batch_size = 5

        segments = [{"text": "test", "duration": 30}]
        results = engine.score_segments(
            segments,
            llm_scorer_func=lambda p: "not valid json at all!!!!",
        )
        self.assertEqual(len(results), 1)
        # Score must be 0 — percentile verdict depends on relative ranking
        self.assertEqual(results[0]["final_score"], 0)
        self.assertIn("AI scoring failed", results[0]["key_weaknesses"])

    def test_empty_segments_returns_empty(self):
        from scoring.engine import ViralScoringEngine
        engine = ViralScoringEngine.__new__(ViralScoringEngine)
        engine.batch_size = 5
        self.assertEqual(engine.score_segments([]), [])

    def test_rank_percentile_static(self):
        from scoring.engine import ViralScoringEngine
        segments = [{"final_score": s} for s in [90, 70, 50, 40, 30, 20, 10]]
        ranked = ViralScoringEngine._rank_percentile(segments)
        self.assertEqual(ranked[0]["verdict"], "viral")
        self.assertEqual(ranked[-1]["verdict"], "skip")


if __name__ == "__main__":
    success = unittest.main(verbosity=2, exit=False).result.wasSuccessful()
    sys.exit(0 if success else 1)
