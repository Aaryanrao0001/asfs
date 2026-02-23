"""Main scoring orchestration: LLM → component scores → server-side calibration."""

import logging
from typing import List, Dict, Callable, Optional

from scoring.llm_client import LLMClient
from scoring.calibrator import compute_final_score
from scoring.prompt_builder import build_batch_prompt
from scoring.parser import parse_json, extract_segment_scores, validate_batch_response
from scoring.config import MODEL_NAME, ENDPOINT, BATCH_SIZE, TEMPERATURE, MAX_TOKENS

logger = logging.getLogger(__name__)

_FALLBACK_SCORES: Dict = {
    "hook_score": 0.0,
    "retention_score": 0.0,
    "emotion_score": 0.0,
    "relatability_score": 0.0,
    "completion_score": 0.0,
    "platform_fit_score": 0.0,
    "key_strengths": [],
    "key_weaknesses": ["AI scoring failed"],
    "first_3_seconds": "",
    "primary_emotion": "neutral",
    "optimal_platform": "none",
}


def _make_fallback(segment: dict) -> dict:
    result = dict(segment)
    result.update(_FALLBACK_SCORES)
    result["final_score"] = 0
    result["verdict"] = "skip"
    return result


class ViralScoringEngine:
    """
    Orchestrates the viral scoring pipeline.

    Flow:
      1. Batch segments → LLM (component scores only, no final math)
      2. Extract component scores via parser
      3. Compute deterministic final score via calibrator
      4. Rank by percentile and assign verdicts
    """

    def __init__(
        self,
        model: str = MODEL_NAME,
        endpoint: str = ENDPOINT,
        batch_size: int = BATCH_SIZE,
        llm_client: Optional[LLMClient] = None,
    ):
        self.llm = llm_client or LLMClient(endpoint=endpoint, model=model)
        self.batch_size = batch_size

    def score_segments(
        self,
        segments: List[Dict],
        llm_scorer_func: Optional[Callable] = None,
    ) -> List[Dict]:
        """
        Score a list of segments and return them ranked by final score with verdicts.

        Args:
            segments: List of segment dicts (each must have 'text' and 'duration').
            llm_scorer_func: Optional override for the LLM scoring step (useful for testing).

        Returns:
            Segments sorted descending by final_score with 'verdict' assigned.
        """
        if not segments:
            return []

        scored: List[Dict] = []

        for batch_start in range(0, len(segments), self.batch_size):
            batch = segments[batch_start:batch_start + self.batch_size]
            scored.extend(self._score_batch(batch, llm_scorer_func))

        return self._rank_percentile(scored)

    def _score_batch(
        self,
        batch: List[Dict],
        llm_scorer_func: Optional[Callable],
    ) -> List[Dict]:
        """Send one batch to the LLM and calibrate scores server-side."""
        try:
            prompt = build_batch_prompt(batch)

            if llm_scorer_func is not None:
                raw_text = llm_scorer_func(prompt)
            else:
                raw_text = self.llm.score_batch(
                    prompt, temperature=TEMPERATURE, max_tokens=MAX_TOKENS
                )

            data = parse_json(raw_text)
            segments_data = validate_batch_response(data, len(batch))

            results = []
            for i, seg in enumerate(batch):
                if i < len(segments_data):
                    raw = segments_data[i]
                    component_scores = extract_segment_scores(raw)
                    final_score = compute_final_score(component_scores, seg.get("duration", 0))

                    result = dict(seg)
                    result.update(component_scores)
                    result["final_score"] = final_score
                    # Carry through non-score fields from the LLM
                    for field in ("key_strengths", "key_weaknesses", "first_3_seconds",
                                  "primary_emotion", "optimal_platform"):
                        result[field] = raw.get(field, _FALLBACK_SCORES[field])
                    results.append(result)
                else:
                    results.append(_make_fallback(seg))

            return results

        except Exception as exc:
            logger.error("Batch scoring failed: %s", exc)
            return [_make_fallback(seg) for seg in batch]

    @staticmethod
    def _rank_percentile(segments: List[Dict]) -> List[Dict]:
        """
        Sort segments by final_score and assign relative-percentile verdicts.

        Top 15 %  → "viral"
        Next 25 % → "maybe"
        Rest      → "skip"
        """
        segments.sort(key=lambda x: x.get("final_score", 0), reverse=True)
        total = len(segments)

        for i, seg in enumerate(segments):
            percentile = i / total if total > 0 else 0
            if percentile <= 0.15:
                seg["verdict"] = "viral"
            elif percentile <= 0.40:
                seg["verdict"] = "maybe"
            else:
                seg["verdict"] = "skip"

        return segments
