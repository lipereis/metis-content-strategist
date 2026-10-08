#!/usr/bin/env python3
"""
Minimal LLM client for standalone (non-Hermes) runs.

Talks to any OpenAI-compatible chat completions endpoint and returns output
validated against a Pydantic schema. Defaults to Google's OpenAI-compatible
Gemini endpoint, which has a free tier.

Environment:
    METIS_LLM_API_KEY   API key (falls back to GEMINI_API_KEY, then OPENAI_API_KEY)
    METIS_LLM_BASE_URL  default https://generativelanguage.googleapis.com/v1beta/openai
    METIS_LLM_MODEL     default gemini-flash-latest
    METIS_LLM_TIMEOUT   seconds per request, default 120 (raise it for local models that load slowly)
"""

import json
import os
import re
from typing import Callable, Optional, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"
DEFAULT_MODEL = "gemini-flash-latest"

T = TypeVar("T", bound=BaseModel)

# (system, user) -> raw model text. Tests inject a fake one.
Transport = Callable[[str, str], str]


class LLMError(RuntimeError):
    """The model could not be reached or kept returning output that fails the schema."""


def api_key() -> Optional[str]:
    return os.getenv("METIS_LLM_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")


def llm_configured() -> bool:
    return bool(api_key())


MISSING_KEY_HELP = (
    "No LLM API key found. Set METIS_LLM_API_KEY (a free Gemini key from "
    "https://aistudio.google.com/apikey works), or pass --offline to run only the "
    "rule-based steps."
)


def _http_transport(system: str, user: str) -> str:
    key = api_key()
    if not key:
        raise LLMError(MISSING_KEY_HELP)
    base = os.getenv("METIS_LLM_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    try:
        resp = httpx.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": os.getenv("METIS_LLM_MODEL", DEFAULT_MODEL),
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                "response_format": {"type": "json_object"},
                "temperature": 0.7,
            },
            timeout=float(os.getenv("METIS_LLM_TIMEOUT", "120")),
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as e:
        raise LLMError(f"LLM request failed: HTTP {e.response.status_code} {e.response.text[:300]}") from e
    except (httpx.HTTPError, KeyError, IndexError, ValueError) as e:
        raise LLMError(f"LLM request failed: {e}") from e


def _strip_fences(text: str) -> str:
    """Models sometimes wrap JSON in ```json fences despite JSON mode."""
    match = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    return (match.group(1) if match else text).strip()


def complete_json(system: str, user: str, schema: type[T], *, transport: Optional[Transport] = None,
                  retries: int = 1) -> T:
    """Ask for JSON matching `schema`; on a validation failure, show the model its error and retry."""
    send = transport or _http_transport
    schema_hint = json.dumps(schema.model_json_schema(), ensure_ascii=False)
    system_full = f"{system}\n\nReply with a single JSON object that validates against this JSON Schema:\n{schema_hint}"
    prompt = user
    last_error = ""
    for _ in range(retries + 1):
        raw = send(system_full, prompt)
        try:
            return schema.model_validate_json(_strip_fences(raw))
        except ValidationError as e:
            last_error = str(e)
            prompt = (f"{user}\n\nYour previous reply was rejected:\n{last_error[:1500]}\n"
                      f"Return corrected JSON only.")
    raise LLMError(f"Model output failed schema validation after {retries + 1} attempts: {last_error[:500]}")
