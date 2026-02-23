#!/usr/bin/env python3
"""
Unit tests for the Dynamic Clip Reconstruction Engine (Phases 1–5).
"""

import sys
import os
import unittest
import logging

# Ensure repo root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _make_transcript(segments):
    """Wrap a list of segment dicts into a transcript_data dict."""
    return {"segments": segments}


def _simple_segments():
    return [
        {
            "start": 0.0,
            "end": 5.0,
            "text": "Nobody ever told you this shocking secret about money.",
            "speaker": "alice",
        },
        {
            "start": 5.0,
            "end": 12.0,
            "text": "I made $10,000 in 30 days using a proven method.",
            "speaker": "alice",
        },
        {
            "start": 12.0,
            "end": 20.0,
            "text": "Everyone thinks it's impossible, but here is the truth you need to know.",
            "speaker": "alice",
        },
        {
            "start": 20.0,
            "end": 30.0,
            "text": "Wait! This changes everything you believed about success.",
            "speaker": "bob",
        },
        {
            "start": 30.0,
            "end": 45.0,
            "text": "Studies show 80% of people make this exact mistake every single day.",
            "speaker": "bob",
        },
        {
            "start": 45.0,
            "end": 60.0,
            "text": "Listen carefully – this is the one thing that separates winners from losers!",
            "speaker": "alice",
        },
    ]


# ---------------------------------------------------------------------------
# Phase 1 – Atomic Units
# ---------------------------------------------------------------------------

class TestAtomicUnits(unittest.TestCase):
    """Tests for virality.atomic_units.build_atomic_units."""

    @classmethod
    def setUpClass(cls):
        logging.disable(logging.WARNING)

    @classmethod
    def tearDownClass(cls):
        logging.disable(logging.NOTSET)

    def setUp(self):
        from virality.atomic_units import build_atomic_units
        self.build = build_atomic_units

    def test_returns_list(self):
        units = self.build(_make_transcript(_simple_segments()))
        self.assertIsInstance(units, list)

    def test_non_empty(self):
        units = self.build(_make_transcript(_simple_segments()))
        self.assertGreater(len(units), 0)

    def test_unit_fields(self):
        units = self.build(_make_transcript(_simple_segments()))
        for u in units:
            self.assertIn("text", u)
            self.assertIn("start", u)
            self.assertIn("end", u)
            self.assertIn("speaker", u)
            self.assertIn("word_count", u)
            self.assertIn("index", u)

    def test_indices_are_sequential(self):
        units = self.build(_make_transcript(_simple_segments()))
        indices = [u["index"] for u in units]
        self.assertEqual(indices, list(range(len(units))))

    def test_start_end_ordering(self):
        units = self.build(_make_transcript(_simple_segments()))
        for u in units:
            self.assertLessEqual(u["start"], u["end"])

    def test_empty_segments(self):
        units = self.build(_make_transcript([]))
        self.assertEqual(units, [])

    def test_word_timestamps(self):
        """Units built with word-level data should still have valid timestamps."""
        seg_with_words = [
            {
                "start": 0.0,
                "end": 6.0,
                "text": "Nobody knew this secret.",
                "speaker": "alice",
                "words": [
                    {"word": "Nobody", "start": 0.0, "end": 0.5},
                    {"word": "knew",   "start": 0.5, "end": 1.0},
                    {"word": "this",   "start": 1.0, "end": 1.5},
                    {"word": "secret", "start": 1.5, "end": 2.5},
                ],
            }
        ]
        units = self.build(_make_transcript(seg_with_words))
        self.assertGreater(len(units), 0)
        for u in units:
            self.assertGreaterEqual(u["end"], u["start"])

    def test_default_speaker_applied(self):
        segs = [{"start": 0.0, "end": 5.0, "text": "Some text here."}]
        units = self.build(_make_transcript(segs), default_speaker="narrator")
        for u in units:
            self.assertEqual(u["speaker"], "narrator")


# ---------------------------------------------------------------------------
# Phase 2 – Sentence Scorer
# ---------------------------------------------------------------------------

class TestSentenceScorer(unittest.TestCase):
    """Tests for virality.sentence_scorer."""

    def setUp(self):
        from virality.sentence_scorer import score_sentence_unit, score_all_units
        self.score_one = score_sentence_unit
        self.score_all = score_all_units

    def _unit(self, text, index=0):
        return {
            "text": text,
            "start": 0.0,
            "end": 5.0,
            "speaker": "s",
            "word_count": len(text.split()),
            "index": index,
        }

    def test_score_fields_present(self):
        scored = self.score_one(self._unit("Nobody tells you this shocking secret!"))
        for field in (
            "hook_score",
            "emotional_charge",
            "claim_strength",
            "identity_trigger",
            "energy_score",
            "delivery_intensity",
        ):
            self.assertIn(field, scored)

    def test_scores_in_range(self):
        scored = self.score_one(self._unit("This is amazing! You need to know this now!"))
        for field in (
            "hook_score", "emotional_charge", "claim_strength",
            "identity_trigger", "energy_score", "delivery_intensity",
        ):
            self.assertGreaterEqual(scored[field], 0.0)
            self.assertLessEqual(scored[field], 10.0)

    def test_high_hook_text(self):
        high = self.score_one(self._unit("Nobody tells you this secret about success!"))
        low  = self.score_one(self._unit("The weather is fine today."))
        self.assertGreater(high["hook_score"], low["hook_score"])

    def test_score_all_preserves_count(self):
        units = [self._unit(f"Sentence {i}", i) for i in range(5)]
        scored = self.score_all(units)
        self.assertEqual(len(scored), 5)

    def test_original_not_mutated(self):
        u = self._unit("Shocking! You must hear this.")
        original_keys = set(u.keys())
        self.score_one(u)
        # Original dict should still have only its original keys
        self.assertEqual(set(u.keys()), original_keys)


# ---------------------------------------------------------------------------
# Phase 3 – Reorder Engine
# ---------------------------------------------------------------------------

class TestReorderEngine(unittest.TestCase):
    """Tests for virality.reorder_engine.generate_candidates."""

    def setUp(self):
        from virality.atomic_units import build_atomic_units
        from virality.sentence_scorer import score_all_units
        from virality.reorder_engine import generate_candidates

        units = build_atomic_units(_make_transcript(_simple_segments()))
        self.scored_units = score_all_units(units)
        self.generate = generate_candidates

    def test_returns_list(self):
        result = self.generate(self.scored_units)
        self.assertIsInstance(result, list)

    def test_candidate_fields(self):
        result = self.generate(self.scored_units)
        self.assertGreater(len(result), 0)
        for c in result:
            self.assertIn("start", c)
            self.assertIn("end", c)
            self.assertIn("text", c)
            self.assertIn("pattern", c)
            self.assertIn("pattern_score", c)
            self.assertIn("unit_indices", c)

    def test_no_duplicate_unit_combinations(self):
        result = self.generate(self.scored_units, k=3)
        keys = [frozenset(c["unit_indices"]) for c in result]
        self.assertEqual(len(keys), len(set(keys)))

    def test_sorted_by_pattern_score(self):
        result = self.generate(self.scored_units)
        scores = [c["pattern_score"] for c in result]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_empty_input(self):
        result = self.generate([])
        self.assertEqual(result, [])

    def test_known_patterns(self):
        result = self.generate(self.scored_units)
        patterns_found = {c["pattern"] for c in result}
        # At least one of the three patterns should appear
        expected = {
            "hook_context_punchline",
            "claim_data_stronger",
            "punchline_explanation_reinforcement",
        }
        self.assertTrue(patterns_found & expected)


# ---------------------------------------------------------------------------
# Phase 4 – Clip Constraints
# ---------------------------------------------------------------------------

class TestClipConstraints(unittest.TestCase):
    """Tests for virality.clip_constraints.apply_clip_constraints."""

    def setUp(self):
        from virality.atomic_units import build_atomic_units
        from virality.sentence_scorer import score_all_units
        from virality.reorder_engine import generate_candidates
        from virality.clip_constraints import apply_clip_constraints

        units = build_atomic_units(_make_transcript(_simple_segments()))
        self.scored_units = score_all_units(units)
        raw = generate_candidates(self.scored_units, k=5)
        self.raw_candidates = raw
        self.apply = apply_clip_constraints

    def test_returns_list(self):
        result = self.apply(self.raw_candidates, self.scored_units)
        self.assertIsInstance(result, list)

    def test_constraint_score_present(self):
        result = self.apply(self.raw_candidates, self.scored_units)
        for c in result:
            self.assertIn("constraint_score", c)
            self.assertIn("coherence", c)
            self.assertIn("hook_score_first", c)
            self.assertIn("impact_score_last", c)

    def test_empty_candidates(self):
        result = self.apply([], self.scored_units)
        self.assertEqual(result, [])

    def test_max_candidates_respected(self):
        result = self.apply(
            self.raw_candidates, self.scored_units,
            target_max=5
        )
        self.assertLessEqual(len(result), 5)


# ---------------------------------------------------------------------------
# Phase 5 – Competitive Evaluation
# ---------------------------------------------------------------------------

class TestCompetitiveEval(unittest.TestCase):
    """Tests for virality.competitive_eval.competitive_evaluate."""

    def setUp(self):
        from virality.competitive_eval import competitive_evaluate
        self.evaluate = competitive_evaluate

    def _make_candidates(self, n=6):
        return [
            {
                "start": float(i * 10),
                "end": float(i * 10 + 30),
                "duration": 30.0,
                "text": (
                    "Nobody tells you this shocking secret. "
                    "You won't believe what happens next!"
                ),
                "pattern": "hook_context_punchline",
                "pattern_score": float(n - i),
                "unit_indices": [i * 3, i * 3 + 1, i * 3 + 2],
                "constraint_score": float(n - i),
            }
            for i in range(n)
        ]

    def test_top_n_respected(self):
        candidates = self._make_candidates(6)
        result = self.evaluate(candidates, top_n=3)
        self.assertLessEqual(len(result), 3)

    def test_dimension_scores_present(self):
        candidates = self._make_candidates(4)
        result = self.evaluate(candidates, top_n=4)
        for c in result:
            for dim in (
                "scroll_stop_probability",
                "share_trigger",
                "debate_potential",
                "clarity",
                "ending_strength",
                "competitive_score",
            ):
                self.assertIn(dim, c)

    def test_sorted_by_competitive_score(self):
        candidates = self._make_candidates(5)
        result = self.evaluate(candidates, top_n=5)
        scores = [c["competitive_score"] for c in result]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_empty_input(self):
        result = self.evaluate([])
        self.assertEqual(result, [])

    def test_llm_scorer_used_when_provided(self):
        """When an LLM scorer is provided and succeeds, its output is used."""
        def mock_llm(candidates):
            return [
                dict(c, competitive_score=9.9, scroll_stop_probability=9.9,
                     share_trigger=9.9, debate_potential=9.9,
                     clarity=9.9, ending_strength=9.9)
                for c in candidates
            ]

        candidates = self._make_candidates(3)
        result = self.evaluate(candidates, llm_scorer=mock_llm, top_n=3)
        for c in result:
            self.assertAlmostEqual(c["competitive_score"], 9.9)

    def test_llm_scorer_fallback_on_exception(self):
        """Pipeline falls back to heuristics if LLM scorer raises."""
        def bad_llm(candidates):
            raise RuntimeError("LLM unavailable")

        candidates = self._make_candidates(3)
        result = self.evaluate(candidates, llm_scorer=bad_llm, top_n=3)
        # Should still return results via heuristic fallback
        self.assertGreater(len(result), 0)


# ---------------------------------------------------------------------------
# End-to-end: reconstruct_clips
# ---------------------------------------------------------------------------

class TestReconstructClips(unittest.TestCase):
    """End-to-end test for virality.reconstruction_engine.reconstruct_clips."""

    def setUp(self):
        from virality.reconstruction_engine import reconstruct_clips
        self.reconstruct = reconstruct_clips

    def test_returns_list(self):
        td = _make_transcript(_simple_segments())
        result = self.reconstruct(td)
        self.assertIsInstance(result, list)

    def test_top_n_respected(self):
        td = _make_transcript(_simple_segments())
        result = self.reconstruct(td, top_n=3)
        self.assertLessEqual(len(result), 3)

    def test_result_fields(self):
        td = _make_transcript(_simple_segments())
        result = self.reconstruct(td, top_n=3)
        for clip in result:
            self.assertIn("start", clip)
            self.assertIn("end", clip)
            self.assertIn("duration", clip)
            self.assertIn("text", clip)
            self.assertIn("competitive_score", clip)

    def test_empty_transcript(self):
        result = self.reconstruct(_make_transcript([]))
        self.assertEqual(result, [])

    def test_config_overrides_respected(self):
        td = _make_transcript(_simple_segments())
        cfg = {"min_duration": 1.0, "max_duration": 120.0, "reorder_k": 3}
        result = self.reconstruct(td, config=cfg, top_n=3)
        self.assertIsInstance(result, list)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for cls in (
        TestAtomicUnits,
        TestSentenceScorer,
        TestReorderEngine,
        TestClipConstraints,
        TestCompetitiveEval,
        TestReconstructClips,
    ):
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
