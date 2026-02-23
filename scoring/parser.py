"""JSON extraction and validation for LLM responses."""

import re
import json
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

_COMPONENT_SCORE_FIELDS = (
    "hook_score",
    "retention_score",
    "emotion_score",
    "relatability_score",
    "completion_score",
    "platform_fit_score",
)


def parse_json(text: str) -> dict:
    """
    Extract and parse a JSON object from a raw LLM response string.

    Handles:
    - Clean JSON: {"segments": [...]}
    - Markdown-wrapped: ```json\\n{...}\\n```
    - Text with embedded JSON

    Args:
        text: Raw model response string.

    Returns:
        Parsed dictionary.

    Raises:
        ValueError: If no valid JSON object is found.
    """
    if not text or not isinstance(text, str):
        raise ValueError("Empty or invalid response")

    # Strip markdown code fences
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)

    start = text.find("{")
    if start == -1:
        raise ValueError(f"No JSON object found in response: {text[:200]}")

    # Walk braces to find the matching closing brace
    depth = 0
    end = start
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break

    if depth != 0:
        raise ValueError(f"Unbalanced braces in JSON: {text[start:start + 200]}")
    else:
        json_str = text[start:end]

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc}\nExtracted: {json_str[:200]}") from exc


def extract_score(data: dict, field: str, default: float = 0.0) -> float:
    """
    Safely extract and clamp a component score (0-10) from a parsed dict.

    Args:
        data: Parsed segment dict from the LLM response.
        field: Score field name (e.g. 'hook_score').
        default: Fallback value when the field is absent or invalid.

    Returns:
        Float score clamped to [0.0, 10.0].
    """
    try:
        value = data.get(field, default)
        score = float(value) if isinstance(value, (int, float)) else float(str(value).strip())
        return max(0.0, min(10.0, score))
    except (ValueError, TypeError):
        logger.warning("Invalid score for '%s', using default %s", field, default)
        return default


def extract_segment_scores(raw: dict) -> Dict[str, float]:
    """
    Extract all component scores from a single segment's LLM analysis dict.

    Args:
        raw: Parsed dict for one segment from the LLM batch response.

    Returns:
        Dict mapping score field names to float values.
    """
    return {field: extract_score(raw, field) for field in _COMPONENT_SCORE_FIELDS}


def validate_batch_response(data: dict, expected_count: int) -> List[dict]:
    """
    Validate a parsed batch response and return the segments list.

    Args:
        data: Top-level parsed JSON dict (must contain 'segments' key).
        expected_count: Expected number of segment entries.

    Returns:
        List of segment dicts (may be shorter than expected_count on mismatch).
    """
    segments = data.get("segments", [])
    if not isinstance(segments, list):
        raise ValueError(f"'segments' must be a list, got {type(segments)}")
    if len(segments) != expected_count:
        logger.warning(
            "Batch response count mismatch: expected %d, got %d",
            expected_count,
            len(segments),
        )
    return segments
