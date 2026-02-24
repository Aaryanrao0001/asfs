"""Builds scoring prompts for the LLM. No math here."""

from typing import List, Dict
from pathlib import Path

# Openings that immediately kill virality — LLM must score hook_score 0-2
DEATH_SIGNALS = [
    "today we're going to",
    "in this video",
    "welcome back",
    "hey guys",
    "what's up everyone",
    "hello and welcome",
    "thanks for watching",
    "before we start",
    "let me introduce",
    "so basically what we're doing",
]

_DEATH_SIGNAL_INSTRUCTION = (
    "DEATH SIGNALS — if the clip's first sentence matches any of the following "
    "informational or greeting openings, you MUST score hook_score as 0-2:\n"
    + "\n".join(f'  - "{ds}"' for ds in DEATH_SIGNALS)
    + "\n"
)


def _load_criteria() -> str:
    """Load the scoring criteria from the shared prompt template."""
    prompt_path = Path(__file__).parent.parent / "ai" / "prompt.txt"
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def build_batch_prompt(segments: List[Dict]) -> str:
    """
    Build a batch scoring prompt for multiple segments.

    The prompt asks the LLM to return component scores only (0-10 each).
    Final score and verdict are computed server-side by the calibrator.

    Args:
        segments: List of segment dicts, each with 'text' and 'duration' keys.

    Returns:
        Formatted prompt string ready to send to the LLM.
    """
    criteria = _load_criteria()

    segment_blocks = []
    for i, seg in enumerate(segments, 1):
        segment_blocks.append(
            f"\n\n━━━ SEGMENT {i} ━━━\n"
            f"Text: {seg['text']}\n"
            f"Duration: {seg['duration']:.1f}s\n"
        )

    return (
        f"Score the following {len(segments)} video segment(s) using the criteria below.\n\n"
        f"{criteria}\n\n"
        f"{_DEATH_SIGNAL_INSTRUCTION}\n"
        f"{''.join(segment_blocks)}\n\n"
        "Return JSON with an array of component scores ONLY "
        "(do NOT compute final_score or verdict — those are calculated server-side):\n"
        "{\n"
        '  "segments": [\n'
        "    {\n"
        '      "segment_id": 1,\n'
        '      "hook_score": <0-10>,\n'
        '      "retention_score": <0-10>,\n'
        '      "emotion_score": <0-10>,\n'
        '      "relatability_score": <0-10>,\n'
        '      "completion_score": <0-10>,\n'
        '      "platform_fit_score": <0-10>,\n'
        '      "key_strengths": ["strength 1"],\n'
        '      "key_weaknesses": ["weakness 1"],\n'
        '      "first_3_seconds": "exact quote",\n'
        '      "primary_emotion": "neutral",\n'
        '      "optimal_platform": "tiktok"\n'
        "    }\n"
        "  ]\n"
        "}\n"
    )
