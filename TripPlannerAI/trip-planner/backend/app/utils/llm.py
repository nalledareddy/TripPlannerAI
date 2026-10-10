from __future__ import annotations

import json
import logging
from functools import lru_cache
from typing import Any

from app.config import get_settings

try:
    from langchain_openai import ChatOpenAI
except Exception:  # pragma: no cover - optional dependency load failure
    ChatOpenAI = None


logger = logging.getLogger(__name__)


def _extract_json_block(text: str) -> str | None:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if "\n" in cleaned:
            cleaned = cleaned.split("\n", 1)[1]
    starts = [index for index in (cleaned.find("{"), cleaned.find("[")) if index >= 0]
    if not starts:
        return None
    start = min(starts)
    opening = cleaned[start]
    closing = "}" if opening == "{" else "]"
    depth = 0
    for index in range(start, len(cleaned)):
        char = cleaned[index]
        if char == opening:
            depth += 1
        elif char == closing:
            depth -= 1
            if depth == 0:
                return cleaned[start : index + 1]
    return None


def safe_json_loads(text: str, fallback: Any) -> Any:
    try:
        return json.loads(text)
    except Exception:
        snippet = _extract_json_block(text)
        if not snippet:
            return fallback
        try:
            return json.loads(snippet)
        except Exception:
            return fallback


class SafeLLMClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.model_name = settings.openai_model
        self.available = False
        self.client = None

        if settings.openai_api_key and ChatOpenAI is not None:
            try:
                self.client = ChatOpenAI(
                    api_key=settings.openai_api_key,
                    model=settings.openai_model,
                    temperature=0.2,
                    timeout=settings.request_timeout,
                    max_retries=0,
                )
                self.available = True
            except Exception:
                self.client = None
                self.available = False

    def ask_for_json(self, system_prompt: str, user_prompt: str, fallback: Any) -> Any:
        if not self.available or self.client is None:
            return fallback
        try:
            response = self.client.invoke(
                [
                    ("system", system_prompt),
                    ("user", user_prompt),
                ]
            )
            content = response.content
            if isinstance(content, list):
                text = " ".join(
                    part.get("text", "") if isinstance(part, dict) else str(part) for part in content
                )
            else:
                text = str(content)
            parsed = safe_json_loads(text, fallback)
            return parsed if isinstance(parsed, type(fallback)) else fallback
        except Exception as exc:
            logger.warning("LLM JSON request failed, using fallback output: %s", exc)
            return fallback


@lru_cache(maxsize=1)
def get_llm_client() -> SafeLLMClient:
    return SafeLLMClient()
