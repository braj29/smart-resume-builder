from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class OpenAIClient:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        try:
            import openai  # type: ignore
        except Exception as exc:  # pragma: no cover - import guard
            raise RuntimeError(
                "openai package is required. Install with `pip install openai`."
            ) from exc

        self._raw = openai
        self.model = model

        # Handle both v1 and legacy SDK initializers.
        if hasattr(openai, "OpenAI"):
            self.client = openai.OpenAI(api_key=api_key)
            self._mode = "client"
        else:
            openai.api_key = api_key
            self.client = openai
            self._mode = "legacy"

    def chat(self, prompt: str, *, max_retries: int = 3) -> str:
        messages = [{"role": "user", "content": prompt}]
        delay = 1.0
        last_error: Exception | None = None
        for attempt in range(max_retries):
            try:
                if self._mode == "client":
                    resp = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=0.2,
                    )
                    return resp.choices[0].message.content or ""
                # Legacy fallback
                resp = self.client.ChatCompletion.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.2,
                )
                return resp["choices"][0]["message"]["content"] or ""
            except Exception as exc:  # pragma: no cover - network call
                last_error = exc
                if _is_rate_limit_error(exc):
                    # User indicated ~3 req/min; wait ~20s before retrying.
                    wait_time = max(delay, 20.0)
                    logger.warning(
                        "OpenAI rate limit encountered (attempt %s). Waiting %.1fs",
                        attempt + 1,
                        wait_time,
                    )
                    time.sleep(wait_time)
                else:
                    logger.warning(
                        "OpenAI call failed (attempt %s): %s", attempt + 1, exc
                    )
                    time.sleep(delay)
                delay *= 2
        raise RuntimeError(f"OpenAI call failed after retries: {last_error}")  # pragma: no cover - network call

    def chat_json(self, prompt: str, *, max_retries: int = 3) -> Dict[str, Any]:
        raw = self.chat(prompt, max_retries=max_retries)
        parsed = _safe_json_parse(raw)
        if parsed is not None:
            return parsed

        # Ask model to repair the JSON if parsing failed.
        repair_prompt = (
            "The previous response was invalid JSON. "
            "Return ONLY valid JSON that fixes it without adding new facts.\n"
            f"Original response:\n{raw}"
        )
        repaired_raw = self.chat(repair_prompt, max_retries=max_retries)
        repaired = _safe_json_parse(repaired_raw)
        if repaired is None:
            raise ValueError("Model did not return valid JSON after repair attempt")
        return repaired


def _safe_json_parse(text: str) -> Dict[str, Any] | None:
    # Attempt direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to extract JSON substring if wrapped in text.
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        snippet = text[start : end + 1]
        try:
            return json.loads(snippet)
        except json.JSONDecodeError:
            return None
    return None


def _is_rate_limit_error(exc: Exception) -> bool:
    # Works with both new and legacy SDK exceptions.
    msg = str(exc).lower()
    if "rate limit" in msg or "rate_limit" in msg:
        return True
    if hasattr(exc, "status_code") and getattr(exc, "status_code") == 429:
        return True
    return False
