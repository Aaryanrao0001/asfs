#!/usr/bin/env python3
"""Unit tests for the metadata resolver."""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from src.pipeline.metadata_resolver import (
    resolve_hashtags,
    resolve_description,
    resolve_metadata,
)


class TestResolveHashtagsStrict(unittest.TestCase):
    """Scenario C — strict mode replaces LLM output entirely."""

    def test_strict_uses_only_user_tags(self):
        user = ["#MyBrand", "#FitnessOver40", "#GymTok"]
        llm = ["#fitness", "#workout", "#motivation", "#health", "#gym"]
        result = resolve_hashtags("strict", user, llm)
        self.assertEqual(result, user)

    def test_strict_ignores_llm_completely(self):
        result = resolve_hashtags("strict", ["#A"], ["#B", "#C"])
        self.assertNotIn("#B", result)
        self.assertNotIn("#C", result)

    def test_strict_empty_user_returns_empty(self):
        result = resolve_hashtags("strict", [], ["#B"])
        self.assertEqual(result, [])


class TestResolveHashtagsAppend(unittest.TestCase):
    """Append mode: user tags + up to 5 non-duplicate LLM tags."""

    def test_append_keeps_user_and_adds_llm(self):
        user = ["#MyBrand"]
        llm = ["#fitness", "#workout"]
        result = resolve_hashtags("append", user, llm)
        self.assertIn("#MyBrand", result)
        self.assertIn("#fitness", result)
        self.assertIn("#workout", result)

    def test_append_deduplicates(self):
        user = ["#Fitness"]
        llm = ["#fitness", "#workout"]
        result = resolve_hashtags("append", user, llm)
        lower_results = [t.lower() for t in result]
        self.assertEqual(lower_results.count("#fitness"), 1)

    def test_append_caps_at_5_llm_tags(self):
        user = ["#A"]
        llm = [f"#tag{i}" for i in range(10)]
        result = resolve_hashtags("append", user, llm)
        # user=1 + max 5 appended = 6
        self.assertLessEqual(len(result), 6)


class TestResolveHashtagsAIOnly(unittest.TestCase):
    """ai_only mode: uses LLM output, ignores user."""

    def test_ai_only_ignores_user(self):
        result = resolve_hashtags("ai_only", ["#MyBrand"], ["#fitness"])
        self.assertEqual(result, ["#fitness"])
        self.assertNotIn("#MyBrand", result)


class TestResolveDescription(unittest.TestCase):
    """Description resolution across modes."""

    def test_strict_uses_user_description(self):
        result = resolve_description("strict", "User desc", "LLM desc")
        self.assertEqual(result, "User desc")

    def test_ai_only_uses_llm_description(self):
        result = resolve_description("ai_only", "User desc", "LLM desc")
        self.assertEqual(result, "LLM desc")

    def test_append_combines(self):
        result = resolve_description("append", "User desc", "LLM desc")
        self.assertIn("User desc", result)
        self.assertIn("LLM desc", result)


class TestResolveMetadata(unittest.TestCase):
    """Full metadata resolution on a clip dict."""

    def test_strict_mode_end_to_end(self):
        clip = {}
        user_tags = ["#MyBrand", "#GymTok"]
        llm_tags = ["#fitness", "#motivation"]

        result = resolve_metadata(
            clip, "strict",
            user_tags=user_tags,
            llm_tags=llm_tags,
            user_description="My description",
            llm_description="AI description",
        )

        self.assertEqual(result["hashtags"], user_tags)
        self.assertEqual(result["description"], "My description")
        self.assertEqual(result["hashtag_mode_used"], "strict")

    def test_unknown_mode_falls_back_to_append(self):
        clip = {}
        result = resolve_metadata(
            clip, "invalid_mode",
            user_tags=["#A"],
            llm_tags=["#B"],
        )
        # Should fall back to append → both present
        self.assertIn("#A", result["hashtags"])
        self.assertIn("#B", result["hashtags"])


if __name__ == "__main__":
    success = unittest.main(verbosity=2, exit=False).result.wasSuccessful()
    sys.exit(0 if success else 1)
