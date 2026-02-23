"""LLM client abstraction layer for GitHub Models."""

import os
from openai import OpenAI


class LLMClient:
    """Thin wrapper around the OpenAI-compatible GitHub Models endpoint."""

    def __init__(self, endpoint: str, model: str):
        self.client = OpenAI(
            base_url=endpoint,
            api_key=os.getenv("GITHUB_TOKEN"),
        )
        self.model = model

    def score_batch(self, prompt: str, temperature: float = 0.2, max_tokens: int = 2048) -> str:
        """
        Send a batch scoring prompt to the model and return raw JSON string.

        Args:
            prompt: Formatted batch prompt.
            temperature: Sampling temperature (low = deterministic).
            max_tokens: Maximum tokens in the response.

        Returns:
            Raw JSON string from the model.
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Return JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            response_format={"type": "json_object"},
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
