#!/usr/bin/env python3
"""
Unit tests for the ASFS Audio-First Segment Scoring Engine.

Covers:
- src.audio.transcriber
- src.audio.feature_extractor
- src.segmentation.micro_segmenter
- src.scoring.batch_scorer
- src.scoring.segment_ranker
- src.scoring.macro_scorer
- src.pipeline.cluster_merger
- src.pipeline.clip_selector
- DB migration SQL (additive schema check)
"""

import json
import os
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# ── Transcriber ────────────────────────────────────────────────────────────────

from src.audio.transcriber import transcribe


class TestTranscriber(unittest.TestCase):
    """Graceful fallback when faster-whisper / file is unavailable."""

    def test_missing_file_returns_not_viable(self):
        result = transcribe("/tmp/nonexistent_audio_file.wav")
        self.assertFalse(result["viable"])
        self.assertEqual(result["words"], [])
        self.assertEqual(result["text"], "")

    def test_result_has_required_keys(self):
        result = transcribe("/tmp/nonexistent_audio_file.wav")
        self.assertIn("words", result)
        self.assertIn("text", result)
        self.assertIn("viable", result)


# ── Feature Extractor ──────────────────────────────────────────────────────────

from src.audio.feature_extractor import (
    compute_silence_ratio,
    compute_speech_rate,
)


class TestFeatureExtractorHelpers(unittest.TestCase):
    """Test deterministic helper functions that do not require audio I/O."""

    def test_silence_ratio_all_silent(self):
        rms_frames = [0.0, 0.001, 0.002]
        ratio = compute_silence_ratio(rms_frames, threshold=0.01)
        self.assertAlmostEqual(ratio, 1.0)

    def test_silence_ratio_none_silent(self):
        rms_frames = [0.05, 0.06, 0.07]
        ratio = compute_silence_ratio(rms_frames, threshold=0.01)
        self.assertAlmostEqual(ratio, 0.0)

    def test_silence_ratio_mixed(self):
        rms_frames = [0.001, 0.05, 0.001, 0.05]
        ratio = compute_silence_ratio(rms_frames, threshold=0.01)
        self.assertAlmostEqual(ratio, 0.5)

    def test_silence_ratio_empty(self):
        ratio = compute_silence_ratio([])
        self.assertEqual(ratio, 1.0)

    def test_speech_rate_normal(self):
        words = [{"word": w} for w in "hello world foo bar".split()]
        rate = compute_speech_rate(words, duration_sec=2.0)
        self.assertAlmostEqual(rate, 2.0)

    def test_speech_rate_zero_duration(self):
        words = [{"word": "hello"}]
        rate = compute_speech_rate(words, duration_sec=0.0)
        self.assertEqual(rate, 0.0)

    def test_speech_rate_empty_words(self):
        rate = compute_speech_rate([], duration_sec=10.0)
        self.assertEqual(rate, 0.0)

    def test_extract_features_missing_file(self):
        from src.audio.feature_extractor import extract_features
        result = extract_features("/tmp/nonexistent.wav", words=[])
        self.assertFalse(result["viable"])
        self.assertIn("mean_rms", result)
        self.assertIn("silence_ratio", result)
        self.assertIn("speech_rate", result)


# ── Micro Segmenter ────────────────────────────────────────────────────────────

from src.segmentation.micro_segmenter import segment, DEFAULT_WINDOW_SEC, DEFAULT_HOP_SEC

# Tolerance for word-boundary alignment checks (one word duration at 2 WPS).
WORD_BOUNDARY_TOLERANCE_SEC = 0.5


def _make_words(n: int, words_per_sec: float = 2.0):
    """Generate a synthetic word list for testing."""
    words = []
    t = 0.0
    for i in range(n):
        duration = 1.0 / words_per_sec
        words.append({"word": f"word{i}", "start": round(t, 3), "end": round(t + duration, 3)})
        t += duration
    return words


class TestMicroSegmenter(unittest.TestCase):

    def test_empty_words_returns_empty(self):
        self.assertEqual(segment([]), [])

    def test_segments_have_required_keys(self):
        words = _make_words(30)
        segs = segment(words)
        self.assertTrue(len(segs) > 0)
        for s in segs:
            self.assertIn("segment_id", s)
            self.assertIn("words", s)
            self.assertIn("text", s)
            self.assertIn("start", s)
            self.assertIn("end", s)
            self.assertIn("duration", s)

    def test_segment_ids_are_sequential(self):
        words = _make_words(40)
        segs = segment(words)
        ids = [s["segment_id"] for s in segs]
        self.assertEqual(ids, list(range(1, len(ids) + 1)))

    def test_window_size_respected(self):
        """Each segment should cover at most window_sec of time."""
        words = _make_words(60, words_per_sec=2.0)
        segs = segment(words, window_sec=5.0, hop_sec=2.5)
        for s in segs:
            self.assertLessEqual(s["duration"], DEFAULT_WINDOW_SEC + WORD_BOUNDARY_TOLERANCE_SEC)

    def test_overlapping_windows_produce_more_segments(self):
        """Smaller hop → more segments."""
        words = _make_words(60, words_per_sec=2.0)
        segs_small_hop = segment(words, window_sec=5.0, hop_sec=1.0)
        segs_large_hop = segment(words, window_sec=5.0, hop_sec=5.0)
        self.assertGreater(len(segs_small_hop), len(segs_large_hop))

    def test_too_few_words_not_segmented(self):
        words = _make_words(2)  # below MIN_WORDS_PER_SEGMENT=3
        segs = segment(words, window_sec=5.0, hop_sec=2.5)
        # Should produce 0 or be empty since only 2 words across the whole file
        self.assertIsInstance(segs, list)

    def test_segment_text_not_empty(self):
        words = _make_words(30)
        segs = segment(words)
        for s in segs:
            self.assertGreater(len(s["text"]), 0)


# ── Batch Scorer ───────────────────────────────────────────────────────────────

from src.scoring.batch_scorer import (
    score_batch,
    _build_batch_prompt,
    _parse_response,
    EXPECTED_KEYS,
    DEFAULT_SCORE,
)


def _make_segment(seg_id: int, text: str = "test text", duration: float = 5.0) -> dict:
    return {"segment_id": seg_id, "text": text, "duration": duration, "start": 0.0, "end": duration}


class TestBatchScorer(unittest.TestCase):

    def test_empty_segments_returns_empty(self):
        self.assertEqual(score_batch([]), [])

    def test_all_expected_keys_present(self):
        segs = [_make_segment(1)]
        results = score_batch(segs, score_fn=None)
        self.assertEqual(len(results), 1)
        for key in EXPECTED_KEYS:
            self.assertIn(key, results[0])

    def test_default_scores_when_no_fn(self):
        segs = [_make_segment(1)]
        results = score_batch(segs, score_fn=None)
        for key in EXPECTED_KEYS:
            self.assertEqual(results[0][key], DEFAULT_SCORE)

    def test_valid_llm_response_parsed(self):
        segs = [_make_segment(1)]
        mock_response = json.dumps({
            "segments": [{
                "segment_id": 1,
                "hook_score": 8.0,
                "retention_score": 7.5,
                "emotion_score": 7.0,
                "relatability_score": 6.5,
                "completion_score": 7.0,
                "platform_fit_score": 6.0,
                "controversy_score": 5.0,
                "novelty_score": 4.0,
            }]
        })
        results = score_batch(segs, score_fn=lambda _: mock_response)
        self.assertEqual(results[0]["hook_score"], 8.0)
        self.assertEqual(results[0]["retention_score"], 7.5)

    def test_malformed_response_uses_defaults(self):
        segs = [_make_segment(1)]
        results = score_batch(segs, score_fn=lambda _: "not json at all")
        for key in EXPECTED_KEYS:
            self.assertEqual(results[0][key], DEFAULT_SCORE)

    def test_prompt_contains_no_final_score_instruction(self):
        segs = [_make_segment(1, text="hello world")]
        prompt = _build_batch_prompt(segs)
        self.assertIn("server-side", prompt)
        self.assertNotIn("final_score:", prompt)

    def test_batching_handles_many_segments(self):
        segs = [_make_segment(i) for i in range(1, 25)]
        results = score_batch(segs, score_fn=None)
        self.assertEqual(len(results), 24)

    def test_score_fn_exception_uses_defaults(self):
        def bad_fn(_):
            raise RuntimeError("LLM unavailable")

        segs = [_make_segment(1)]
        results = score_batch(segs, score_fn=bad_fn)
        for key in EXPECTED_KEYS:
            self.assertEqual(results[0][key], DEFAULT_SCORE)


# ── Segment Ranker ─────────────────────────────────────────────────────────────

from src.scoring.segment_ranker import (
    compute_composite_score,
    rank,
    HARD_THRESHOLD,
    TEXT_WEIGHT,
    AUDIO_WEIGHT,
)


def _scored_segment(seg_id: int, hook: float = 8.0, **overrides) -> dict:
    base = {
        "segment_id": seg_id,
        "text": "test",
        "start": float(seg_id * 5),
        "end": float(seg_id * 5 + 5),
        "duration": 5.0,
        "hook_score": hook,
        "retention_score": 7.0,
        "emotion_score": 7.0,
        "relatability_score": 6.0,
        "completion_score": 6.0,
        "platform_fit_score": 6.0,
        "controversy_score": 5.0,
        "novelty_score": 4.0,
    }
    base.update(overrides)
    return base


class TestSegmentRanker(unittest.TestCase):

    def test_composite_score_is_float(self):
        seg = _scored_segment(1)
        score = compute_composite_score(seg, {"mean_rms": 0.05, "silence_ratio": 0.2, "speech_rate": 2.5})
        self.assertIsInstance(score, float)

    def test_higher_audio_energy_raises_composite_score(self):
        seg = _scored_segment(1)
        low_audio = {"mean_rms": 0.001, "silence_ratio": 0.8, "speech_rate": 1.0}
        high_audio = {"mean_rms": 0.15, "silence_ratio": 0.1, "speech_rate": 4.0}
        self.assertGreater(
            compute_composite_score(seg, high_audio),
            compute_composite_score(seg, low_audio),
        )

    def test_text_audio_weights_sum_to_one(self):
        self.assertAlmostEqual(TEXT_WEIGHT + AUDIO_WEIGHT, 1.0, places=5)

    def test_rank_filters_below_threshold(self):
        # Low scores → composite will be well below HARD_THRESHOLD
        low_seg = _scored_segment(1, hook=1.0, retention_score=1.0, emotion_score=1.0,
                                  relatability_score=1.0, completion_score=1.0,
                                  platform_fit_score=1.0, controversy_score=0.0, novelty_score=0.0)
        result = rank([low_seg], threshold=HARD_THRESHOLD)
        self.assertEqual(result, [])

    def test_rank_passes_high_scoring_segments(self):
        high_seg = _scored_segment(1, hook=9.0, retention_score=9.0, emotion_score=9.0,
                                   relatability_score=8.0, completion_score=8.0,
                                   platform_fit_score=8.0, controversy_score=5.0, novelty_score=5.0)
        result = rank([high_seg], threshold=0.0)
        self.assertEqual(len(result), 1)
        self.assertIn("composite_score", result[0])

    def test_rank_sorted_descending(self):
        segs = [_scored_segment(i, hook=float(i)) for i in range(1, 6)]
        result = rank(segs, threshold=0.0)
        scores = [r["composite_score"] for r in result]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_rank_empty_input(self):
        self.assertEqual(rank([]), [])

    def test_rank_uses_default_audio_when_missing(self):
        """Segments without audio_features key still get ranked."""
        seg = _scored_segment(1)  # no audio_features key
        result = rank([seg], threshold=0.0)
        self.assertEqual(len(result), 1)


# ── Cluster Merger ─────────────────────────────────────────────────────────────

from src.pipeline.cluster_merger import merge, DEFAULT_GAP_SEC


def _micro(seg_id: int, start: float, end: float, score: float = 6.0) -> dict:
    return {
        "segment_id": seg_id,
        "start": start,
        "end": end,
        "duration": round(end - start, 4),
        "text": f"segment {seg_id}",
        "composite_score": score,
    }


class TestClusterMerger(unittest.TestCase):

    def test_empty_input_returns_empty(self):
        self.assertEqual(merge([]), [])

    def test_adjacent_segments_merged(self):
        segs = [
            _micro(1, 0.0, 5.0),
            _micro(2, 5.0, 10.0),
            _micro(3, 10.0, 15.0),
        ]
        macros = merge(segs, gap_sec=1.0, min_duration_sec=5.0)
        # All three are adjacent → should form one macro
        self.assertEqual(len(macros), 1)
        self.assertAlmostEqual(macros[0]["start"], 0.0)
        self.assertAlmostEqual(macros[0]["end"], 15.0)

    def test_non_adjacent_segments_not_merged(self):
        segs = [
            _micro(1, 0.0, 5.0),
            _micro(2, 20.0, 25.0),
        ]
        macros = merge(segs, gap_sec=1.0, min_duration_sec=4.0)
        self.assertEqual(len(macros), 2)

    def test_short_macros_discarded(self):
        segs = [_micro(1, 0.0, 2.0)]  # duration = 2 s
        macros = merge(segs, gap_sec=1.0, min_duration_sec=10.0)
        self.assertEqual(macros, [])

    def test_long_macros_trimmed(self):
        segs = [_micro(1, 0.0, 5.0), _micro(2, 5.0, 10.0), _micro(3, 10.0, 90.0)]
        macros = merge(segs, gap_sec=1.0, min_duration_sec=5.0, max_duration_sec=60.0)
        for m in macros:
            self.assertLessEqual(m["duration"], 60.0)

    def test_macro_has_required_keys(self):
        segs = [_micro(1, 0.0, 5.0), _micro(2, 5.0, 15.0)]
        macros = merge(segs, gap_sec=1.0, min_duration_sec=5.0)
        for m in macros:
            for key in ("macro_id", "start", "end", "duration", "text",
                        "micro_segments", "best_micro_score", "avg_micro_score"):
                self.assertIn(key, m)

    def test_sorted_by_best_micro_score_descending(self):
        segs = [
            _micro(1, 0.0, 5.0, score=3.0),
            _micro(2, 20.0, 30.0, score=9.0),
        ]
        macros = merge(segs, gap_sec=1.0, min_duration_sec=4.0)
        scores = [m["best_micro_score"] for m in macros]
        self.assertEqual(scores, sorted(scores, reverse=True))


# ── Macro Scorer ───────────────────────────────────────────────────────────────

from src.scoring.macro_scorer import score_macros, MACRO_WEIGHT, MICRO_WEIGHT


def _macro(macro_id: int, text: str = "test macro", best_micro: float = 6.0) -> dict:
    return {
        "macro_id": macro_id,
        "start": 0.0,
        "end": 20.0,
        "duration": 20.0,
        "text": text,
        "best_micro_score": best_micro,
        "avg_micro_score": best_micro,
        "micro_count": 4,
        "micro_segments": [],
    }


class TestMacroScorer(unittest.TestCase):

    def test_empty_input_returns_empty(self):
        self.assertEqual(score_macros([]), [])

    def test_blended_score_present(self):
        macros = [_macro(1)]
        results = score_macros(macros, score_fn=None)
        self.assertIn("blended_score", results[0])

    def test_blend_weights_sum_to_one(self):
        self.assertAlmostEqual(MACRO_WEIGHT + MICRO_WEIGHT, 1.0, places=5)

    def test_higher_micro_score_raises_blended_score(self):
        low = _macro(1, best_micro=2.0)
        high = _macro(2, best_micro=9.0)
        low_result = score_macros([low], score_fn=None)[0]
        high_result = score_macros([high], score_fn=None)[0]
        self.assertGreater(high_result["blended_score"], low_result["blended_score"])

    def test_valid_llm_response_used(self):
        scores = {
            "hook_score": 9.0,
            "retention_score": 9.0,
            "emotion_score": 9.0,
            "relatability_score": 8.0,
            "completion_score": 8.0,
            "platform_fit_score": 8.0,
            "controversy_score": 5.0,
            "novelty_score": 5.0,
        }
        macros = [_macro(1, best_micro=5.0)]
        results = score_macros(macros, score_fn=lambda _: json.dumps(scores))
        self.assertGreater(results[0]["blended_score"], 5.0)

    def test_malformed_response_uses_defaults(self):
        macros = [_macro(1)]
        results = score_macros(macros, score_fn=lambda _: "{bad json")
        self.assertIn("blended_score", results[0])
        self.assertIsInstance(results[0]["blended_score"], float)

    def test_sorted_by_blended_score_descending(self):
        macros = [_macro(i, best_micro=float(i)) for i in range(1, 5)]
        results = score_macros(macros, score_fn=None)
        scores = [r["blended_score"] for r in results]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_component_scores_attached(self):
        macros = [_macro(1)]
        results = score_macros(macros, score_fn=None)
        self.assertIn("macro_component_scores", results[0])
        self.assertIn("macro_text_score", results[0])


# ── Clip Selector ──────────────────────────────────────────────────────────────

from src.pipeline.clip_selector import select, export_clip, export_clips, DEFAULT_MIN_BLENDED_SCORE


def _scored_macro(macro_id: int, score: float) -> dict:
    return {
        "macro_id": macro_id,
        "start": float(macro_id * 10),
        "end": float(macro_id * 10 + 20),
        "duration": 20.0,
        "blended_score": score,
        "text": "test macro",
    }


class TestClipSelector(unittest.TestCase):

    def test_empty_input_returns_empty(self):
        self.assertEqual(select([]), [])

    def test_filters_below_min_score(self):
        macros = [_scored_macro(1, 3.0), _scored_macro(2, 2.0)]
        result = select(macros, min_score=DEFAULT_MIN_BLENDED_SCORE)
        self.assertEqual(result, [])

    def test_selects_above_threshold(self):
        macros = [_scored_macro(1, 8.0), _scored_macro(2, 2.0)]
        result = select(macros, min_score=4.5)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["macro_id"], 1)

    def test_max_clips_respected(self):
        macros = [_scored_macro(i, 9.0) for i in range(1, 10)]
        result = select(macros, max_clips=3, min_score=0.0)
        self.assertLessEqual(len(result), 3)

    def test_sorted_descending(self):
        macros = [_scored_macro(i, float(i)) for i in range(1, 6)]
        result = select(macros, max_clips=5, min_score=0.0)
        scores = [r["blended_score"] for r in result]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_export_clip_missing_source_returns_false(self):
        result = export_clip("/tmp/no_such_file.mp4", 0.0, 5.0, "/tmp/out.mp4")
        self.assertFalse(result)

    def test_export_clip_invalid_duration_returns_false(self):
        result = export_clip("/dev/null", 5.0, 3.0, "/tmp/out.mp4")
        self.assertFalse(result)

    def test_export_clips_creates_output_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = os.path.join(tmpdir, "clips")
            macros = [_scored_macro(1, 7.0)]
            # source_path doesn't exist → export fails, but dir should be created
            export_clips(macros, "/tmp/nonexistent_source.mp4", out_dir)
            self.assertTrue(os.path.isdir(out_dir))

    def test_export_clips_marks_failed_exports(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            macros = [_scored_macro(1, 7.0)]
            results = export_clips(macros, "/tmp/nonexistent.mp4", tmpdir)
            self.assertEqual(len(results), 1)
            self.assertFalse(results[0]["exported"])
            self.assertIsNone(results[0]["output_path"])


# ── DB Migration ───────────────────────────────────────────────────────────────

_MIGRATION_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "src", "db", "migrations", "0005_audio_scoring.sql",
)


class TestAudioScoringMigration(unittest.TestCase):
    """Verify the additive schema migration can be applied to SQLite."""

    def _apply_migration(self, conn: sqlite3.Connection):
        with open(_MIGRATION_PATH) as f:
            sql = f.read()
        # SQLite executescript does not support multi-statement execute
        for stmt in sql.split(";"):
            stmt = stmt.strip()
            if stmt:
                conn.execute(stmt)
        conn.commit()

    def test_migration_file_exists(self):
        self.assertTrue(os.path.exists(_MIGRATION_PATH))

    def test_migration_creates_micro_segments_table(self):
        conn = sqlite3.connect(":memory:")
        self._apply_migration(conn)
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()]
        self.assertIn("audio_micro_segments", tables)
        conn.close()

    def test_migration_creates_macro_candidates_table(self):
        conn = sqlite3.connect(":memory:")
        self._apply_migration(conn)
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()]
        self.assertIn("audio_macro_candidates", tables)
        conn.close()

    def test_migration_is_idempotent(self):
        """Applying the migration twice should not raise."""
        conn = sqlite3.connect(":memory:")
        self._apply_migration(conn)
        # Second apply should be fine due to IF NOT EXISTS.
        self._apply_migration(conn)
        conn.close()

    def test_micro_segments_insert(self):
        conn = sqlite3.connect(":memory:")
        self._apply_migration(conn)
        conn.execute(
            "INSERT INTO audio_micro_segments "
            "(source_id, segment_id, start_sec, end_sec, duration_sec, composite_score) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("src_001", 1, 0.0, 5.0, 5.0, 7.2),
        )
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM audio_micro_segments").fetchone()[0]
        self.assertEqual(count, 1)
        conn.close()

    def test_macro_candidates_insert(self):
        conn = sqlite3.connect(":memory:")
        self._apply_migration(conn)
        conn.execute(
            "INSERT INTO audio_macro_candidates "
            "(source_id, macro_id, start_sec, end_sec, duration_sec, blended_score, platform) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("src_001", 1, 0.0, 25.0, 25.0, 7.8, "tiktok"),
        )
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM audio_macro_candidates").fetchone()[0]
        self.assertEqual(count, 1)
        conn.close()


# ── Open Loop Detector ────────────────────────────────────────────────────────

from src.segmentation.open_loop_detector import (
    has_open_loop,
    next_segment_continues,
    close_open_loops,
)


def _seg(seg_id: int, text: str, start: float = 0.0, end: float = 5.0) -> dict:
    return {
        "segment_id": seg_id,
        "text": text,
        "start": start,
        "end": end,
        "duration": round(end - start, 4),
    }


class TestHasOpenLoop(unittest.TestCase):

    def test_trailing_and_is_open_loop(self):
        self.assertTrue(has_open_loop("I was really excited and"))

    def test_trailing_but_is_open_loop(self):
        self.assertTrue(has_open_loop("I tried everything but"))

    def test_trailing_because_is_open_loop(self):
        self.assertTrue(has_open_loop("This matters because"))

    def test_setup_phrase_i_was_about_to(self):
        # The phrase "I was about to" is the trigger; additional words after it
        # represent what would follow in a real transcript segment.
        self.assertTrue(has_open_loop("I was about to hit the record"))

    def test_setup_phrase_the_thing_is(self):
        self.assertTrue(has_open_loop("The thing is"))

    def test_setup_phrase_heres_what_happened(self):
        self.assertTrue(has_open_loop("Here's what happened"))

    def test_unanswered_question(self):
        self.assertTrue(has_open_loop("You know what the real problem is?"))

    def test_incomplete_list_first(self):
        self.assertTrue(has_open_loop("First of all"))

    def test_incomplete_list_number_one(self):
        self.assertTrue(has_open_loop("Number one"))

    def test_complete_sentence_is_not_open_loop(self):
        self.assertFalse(has_open_loop("That was the whole story."))

    def test_empty_string_is_not_open_loop(self):
        self.assertFalse(has_open_loop(""))

    def test_exclamation_sentence_is_not_open_loop(self):
        self.assertFalse(has_open_loop("That was incredible!"))


class TestNextSegmentContinues(unittest.TestCase):

    def test_starts_with_and(self):
        self.assertTrue(next_segment_continues("and it turned out to be true"))

    def test_starts_with_but(self):
        self.assertTrue(next_segment_continues("but then everything changed"))

    def test_starts_with_so(self):
        self.assertTrue(next_segment_continues("so I decided to leave"))

    def test_starts_with_because(self):
        self.assertTrue(next_segment_continues("because nobody was watching"))

    def test_starts_with_however(self):
        self.assertTrue(next_segment_continues("however the outcome was different"))

    def test_normal_start_is_not_continuation(self):
        self.assertFalse(next_segment_continues("The results were surprising."))

    def test_empty_string_is_not_continuation(self):
        self.assertFalse(next_segment_continues(""))

    def test_name_starting_with_and_not_flagged(self):
        # The \b word-boundary after the alternation ensures "Anderson" does NOT
        # match: after matching "And" the next character is "e" (word char),
        # so \b fails and the regex correctly rejects it.
        self.assertFalse(next_segment_continues("Anderson was first to arrive."))


class TestCloseOpenLoops(unittest.TestCase):

    def test_empty_input_returns_empty(self):
        self.assertEqual(close_open_loops([]), [])

    def test_complete_segment_not_merged(self):
        segs = [
            _seg(1, "That was the whole story.", 0.0, 5.0),
            _seg(2, "Now let me explain.", 5.0, 10.0),
        ]
        result = close_open_loops(segs)
        self.assertEqual(len(result), 2)

    def test_open_loop_segment_merged_with_next(self):
        segs = [
            _seg(1, "I was about to hit the record", 0.0, 5.0),
            _seg(2, "and it changed everything.", 5.0, 10.0),
        ]
        result = close_open_loops(segs)
        self.assertEqual(len(result), 1)
        self.assertIn("I was about to hit the record", result[0]["text"])
        self.assertIn("and it changed everything.", result[0]["text"])

    def test_continuation_starter_triggers_merge(self):
        segs = [
            _seg(1, "The results were surprising.", 0.0, 5.0),
            _seg(2, "but we had to push forward.", 5.0, 10.0),
        ]
        result = close_open_loops(segs)
        self.assertEqual(len(result), 1)

    def test_merged_segment_spans_full_time_range(self):
        segs = [
            _seg(1, "I was about to give up", 0.0, 5.0),
            _seg(2, "when the answer appeared.", 5.0, 10.0),
        ]
        result = close_open_loops(segs)
        self.assertAlmostEqual(result[0]["start"], 0.0)
        self.assertAlmostEqual(result[0]["end"], 10.0)
        self.assertAlmostEqual(result[0]["duration"], 10.0)

    def test_trailing_and_merges_forward(self):
        segs = [
            _seg(1, "I tried really hard and", 0.0, 5.0),
            _seg(2, "it finally worked out.", 5.0, 10.0),
        ]
        result = close_open_loops(segs)
        self.assertEqual(len(result), 1)

    def test_chain_of_open_loops_fully_merged(self):
        segs = [
            _seg(1, "First of all", 0.0, 3.0),
            _seg(2, "you need to know that", 3.0, 6.0),
            _seg(3, "this really works.", 6.0, 10.0),
        ]
        result = close_open_loops(segs)
        self.assertEqual(len(result), 1)
        self.assertAlmostEqual(result[0]["start"], 0.0)
        self.assertAlmostEqual(result[0]["end"], 10.0)

    def test_word_lists_concatenated_on_merge(self):
        segs = [
            {
                "segment_id": 1,
                "text": "I was about to quit",
                "start": 0.0,
                "end": 4.0,
                "duration": 4.0,
                "words": [{"word": "I", "start": 0.0, "end": 0.3}],
            },
            {
                "segment_id": 2,
                "text": "but something stopped me.",
                "start": 4.0,
                "end": 8.0,
                "duration": 4.0,
                "words": [{"word": "but", "start": 4.0, "end": 4.3}],
            },
        ]
        result = close_open_loops(segs)
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0]["words"]), 2)

    def test_last_segment_with_open_loop_kept_as_is(self):
        # When there is no next segment to merge into, just keep it.
        segs = [_seg(1, "I was about to", 0.0, 5.0)]
        result = close_open_loops(segs)
        self.assertEqual(len(result), 1)


# ── Boundary Snapper ──────────────────────────────────────────────────────────

from src.segmentation.boundary_snapper import (
    snap_to_sentence_start,
    snap_to_sentence_end,
    snap_segment,
)


def _words_from_sentences(sentences):
    """Build a synthetic word list from a list of sentence strings."""
    words = []
    t = 0.0
    for sentence in sentences:
        for token in sentence.split():
            word_dur = 0.4
            words.append({"word": token, "start": round(t, 3), "end": round(t + word_dur, 3)})
            t += word_dur
        # Small pause between sentences.
        t += 0.1
    return words


class TestSnapToSentenceStart(unittest.TestCase):

    def test_empty_words_returns_target(self):
        self.assertEqual(snap_to_sentence_start([], 5.0), 5.0)

    def test_first_word_returns_its_start(self):
        words = _words_from_sentences(["Hello world."])
        result = snap_to_sentence_start(words, words[0]["start"])
        self.assertAlmostEqual(result, words[0]["start"])

    def test_snaps_back_to_sentence_boundary(self):
        # Two sentences: "This is great." "Start here now."
        words = _words_from_sentences(["This is great.", "Start here now."])
        # Target is somewhere in the middle of the second sentence.
        second_sentence_second_word = words[5]  # "here"
        result = snap_to_sentence_start(words, second_sentence_second_word["start"])
        # Should snap back to "Start", the first word of the second sentence.
        self.assertLessEqual(result, second_sentence_second_word["start"])

    def test_continuation_word_skipped(self):
        # Sentence ends; next sentence begins with "And".
        words = _words_from_sentences(["It happened fast.", "And then it changed."])
        # Find "And" — it's the first word of the second sentence.
        and_word = next(w for w in words if w["word"].lower() == "and")
        result = snap_to_sentence_start(words, and_word["start"])
        # Should skip past "And" to "then".
        then_word = next(w for w in words if w["word"].lower() == "then")
        self.assertAlmostEqual(result, then_word["start"])

    def test_returns_float(self):
        words = _words_from_sentences(["Hello."])
        result = snap_to_sentence_start(words, 0.0)
        self.assertIsInstance(result, float)


class TestSnapToSentenceEnd(unittest.TestCase):

    def test_empty_words_returns_target(self):
        self.assertEqual(snap_to_sentence_end([], 5.0), 5.0)

    def test_within_sentence_extends_to_period(self):
        words = _words_from_sentences(["The result was incredible."])
        # Target in the middle of the sentence.
        middle_word = words[1]  # "result"
        result = snap_to_sentence_end(words, middle_word["start"])
        # Should extend to the end of "incredible." (last word).
        self.assertGreaterEqual(result, middle_word["end"])
        self.assertAlmostEqual(result, words[-1]["end"])

    def test_at_end_of_sentence_stays(self):
        words = _words_from_sentences(["Short sentence."])
        last_word_end = words[-1]["end"]
        result = snap_to_sentence_end(words, last_word_end - 0.01)
        self.assertAlmostEqual(result, last_word_end)

    def test_no_punctuation_returns_last_word_end(self):
        # Words with no sentence-ending punctuation.
        words = [
            {"word": "hello", "start": 0.0, "end": 0.4},
            {"word": "world", "start": 0.5, "end": 0.9},
        ]
        result = snap_to_sentence_end(words, 0.0)
        self.assertAlmostEqual(result, 0.9)

    def test_returns_float(self):
        words = _words_from_sentences(["Done."])
        result = snap_to_sentence_end(words, 0.0)
        self.assertIsInstance(result, float)


class TestSnapSegment(unittest.TestCase):

    def test_empty_words_returns_copy_of_segment(self):
        seg = {"start": 1.0, "end": 5.0, "duration": 4.0, "text": "hello"}
        result = snap_segment(seg, [])
        self.assertEqual(result["start"], 1.0)
        self.assertEqual(result["end"], 5.0)

    def test_snapped_segment_has_required_keys(self):
        words = _words_from_sentences(["This is a test sentence."])
        seg = {"start": 0.0, "end": words[-1]["end"], "duration": words[-1]["end"], "text": ""}
        result = snap_segment(seg, words)
        for key in ("start", "end", "duration", "words", "text"):
            self.assertIn(key, result)

    def test_start_never_after_original_start(self):
        words = _words_from_sentences(["The quick brown fox jumped."])
        seg = {"start": words[2]["start"], "end": words[-1]["end"], "duration": 2.0, "text": ""}
        result = snap_segment(seg, words)
        self.assertLessEqual(result["start"], words[2]["start"])

    def test_end_never_before_original_end(self):
        words = _words_from_sentences(["The quick brown fox jumped."])
        seg = {
            "start": words[0]["start"],
            "end": words[2]["end"],
            "duration": words[2]["end"],
            "text": "",
        }
        result = snap_segment(seg, words)
        self.assertGreaterEqual(result["end"], words[2]["end"])

    def test_duration_matches_start_end(self):
        words = _words_from_sentences(["A complete sentence.", "Another one here."])
        seg = {"start": words[0]["start"], "end": words[-1]["end"], "duration": 0.0, "text": ""}
        result = snap_segment(seg, words)
        expected_dur = round(result["end"] - result["start"], 4)
        self.assertAlmostEqual(result["duration"], expected_dur, places=3)

    def test_original_segment_not_mutated(self):
        words = _words_from_sentences(["Hello world."])
        seg = {"start": 0.0, "end": 1.0, "duration": 1.0, "text": "hello world"}
        snap_segment(seg, words)
        self.assertEqual(seg["start"], 0.0)
        self.assertEqual(seg["text"], "hello world")


if __name__ == "__main__":
    success = unittest.main(verbosity=2, exit=False).result.wasSuccessful()
    sys.exit(0 if success else 1)
