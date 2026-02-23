#!/usr/bin/env python3
"""Unit tests for the packaging engine."""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from src.pipeline.packager import (
    generate_variants,
    package_clip,
    build_subtitle_spec,
    _derive_headline,
    CTA_FRAME_DURATION,
    SUBTITLE_DEFAULTS,
)


class TestVariantGeneration(unittest.TestCase):
    """Test packaging variant generation (Scenario B)."""

    def test_three_variants_generated(self):
        clip = {
            "controversy_score": 5.0,
            "emotion_score": 6.0,
            "relatability_score": 5.0,
        }
        variants = generate_variants(clip, suggested_title="Amazing discovery")
        self.assertEqual(len(variants), 3)
        types = {v["variant_type"] for v in variants}
        self.assertEqual(types, {"Curiosity", "Contrarian", "Relatable"})

    def test_contrarian_primary_on_high_controversy(self):
        clip = {"controversy_score": 8.5, "emotion_score": 5.0, "relatability_score": 5.0}
        variants = generate_variants(clip)
        self.assertEqual(variants[0]["variant_type"], "Contrarian")

    def test_relatable_primary_on_high_emotion_and_relatability(self):
        clip = {"controversy_score": 3.0, "emotion_score": 8.0, "relatability_score": 7.0}
        variants = generate_variants(clip)
        self.assertEqual(variants[0]["variant_type"], "Relatable")

    def test_curiosity_default_primary(self):
        clip = {"controversy_score": 3.0, "emotion_score": 5.0, "relatability_score": 4.0}
        variants = generate_variants(clip)
        self.assertEqual(variants[0]["variant_type"], "Curiosity")

    def test_variant_has_required_fields(self):
        clip = {"controversy_score": 5.0, "emotion_score": 5.0, "relatability_score": 5.0}
        variants = generate_variants(clip, suggested_title="Test title")
        for v in variants:
            self.assertIn("variant_type", v)
            self.assertIn("headline_text", v)
            self.assertIn("overlay_line", v)
            self.assertIn("cta_text", v)
            self.assertIn("cta_type", v)


class TestHeadlinePolicy(unittest.TestCase):
    """Headline max 6 words from suggested_title or fallback."""

    def test_suggested_title_used_when_short(self):
        headline = _derive_headline("Short title", None, 5.0)
        self.assertEqual(headline, "Short title")

    def test_long_suggested_title_fallback_to_hook(self):
        headline = _derive_headline(
            "This is a very very very very very long title",
            "secret trick revealed today",
            5.0,
        )
        # suggested_title > 8 words → falls back to hook text
        self.assertIn("secret", headline)

    def test_question_appended_on_high_curiosity(self):
        headline = _derive_headline(None, "secret trick revealed", 7.0)
        self.assertTrue(headline.endswith("?"))

    def test_no_question_on_low_curiosity(self):
        headline = _derive_headline(None, "secret trick revealed", 4.0)
        self.assertFalse(headline.endswith("?"))

    def test_filler_words_stripped(self):
        headline = _derive_headline(None, "um so like amazing discovery today", 4.0)
        self.assertNotIn("um", headline.lower().split())
        self.assertNotIn("so", headline.lower().split())
        self.assertNotIn("like", headline.lower().split())


class TestCTAFrame(unittest.TestCase):
    """CTA frame is appended."""

    def test_cta_appended(self):
        clip = {"controversy_score": 5.0, "emotion_score": 5.0, "relatability_score": 5.0}
        result = package_clip(clip, suggested_title="Test")
        self.assertEqual(result["cta_frame_duration"], CTA_FRAME_DURATION)
        self.assertTrue(result["packaging_applied"])


class TestSubtitleSpec(unittest.TestCase):
    """Verify subtitle styling rules."""

    def test_font_size_range(self):
        spec = build_subtitle_spec()
        self.assertGreaterEqual(spec["font_size_min"], 70)
        self.assertLessEqual(spec["font_size_max"], 90)

    def test_bold_white_style(self):
        spec = build_subtitle_spec()
        self.assertEqual(spec["font_style"], "bold")
        self.assertEqual(spec["font_color"], "white")

    def test_outline(self):
        spec = build_subtitle_spec()
        self.assertEqual(spec["outline_size"], 8)
        self.assertEqual(spec["outline_color"], "black")

    def test_max_lines(self):
        spec = build_subtitle_spec()
        self.assertLessEqual(spec["max_lines"], 3)

    def test_max_chars_per_line(self):
        spec = build_subtitle_spec()
        self.assertLessEqual(spec["max_chars_per_line"], 32)


if __name__ == "__main__":
    success = unittest.main(verbosity=2, exit=False).result.wasSuccessful()
    sys.exit(0 if success else 1)
