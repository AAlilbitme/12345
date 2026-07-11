"""Model backends that do the actual rewriting.

Design goal: always run. If no model is reachable, fall back to the rule
engine so the tool still returns cleaned text and a report instead of failing.

Supported providers:
  - ollama    local models, no API key (default when reachable)
  - openai    needs OPENAI_API_KEY
  - anthropic needs ANTHROPIC_API_KEY
  - none      skip the model, rule engine only
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass

from .prompt import build_system_prompt, build_user_prompt


class ProviderError(RuntimeError):
    """Raised when a chosen provider cannot complete a rewrite."""


@dataclass
class RewriteResult:
    text: str
    provider: str
    model: str | None


def _http_post_json(url: str, payload: dict, headers: dict, timeout: int) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _ollama(system: str, user: str, model: str, timeout: int) -> str:
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    try:
        result = _http_post_json(
            f"{host}/api/chat", payload, {"Content-Type": "application/json"}, timeout
        )
    except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
        raise ProviderError(
            f"Could not reach Ollama at {host}. Is it running? ({exc})"
        ) from exc
    return result.get("message", {}).get("content", "").strip()


def _openai(system: str, user: str, model: str, timeout: int) -> str:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise ProviderError("OPENAI_API_KEY is not set.")
    base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.9,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
    }
    try:
        result = _http_post_json(
            f"{base}/chat/completions", payload, headers, timeout
        )
    except urllib.error.HTTPError as exc:
        raise ProviderError(f"OpenAI API error: {exc}") from exc
    except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
        raise ProviderError(f"Could not reach OpenAI: {exc}") from exc
    return result["choices"][0]["message"]["content"].strip()


def _anthropic(system: str, user: str, model: str, timeout: int) -> str:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise ProviderError("ANTHROPIC_API_KEY is not set.")
    base = os.environ.get(
        "ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1"
    ).rstrip("/")
    payload = {
        "model": model,
        "max_tokens": 4096,
        "temperature": 0.9,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    headers = {
        "Content-Type": "application/json",
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
    }
    try:
        result = _http_post_json(f"{base}/messages", payload, headers, timeout)
    except urllib.error.HTTPError as exc:
        raise ProviderError(f"Anthropic API error: {exc}") from exc
    except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
        raise ProviderError(f"Could not reach Anthropic: {exc}") from exc
    return "".join(
        block.get("text", "")
        for block in result.get("content", [])
        if block.get("type") == "text"
    ).strip()


DEFAULT_MODELS = {
    "ollama": "llama3.1",
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-5-sonnet-latest",
}


def rewrite(
    text: str,
    *,
    audience: str,
    tone: str,
    provider: str = "ollama",
    model: str | None = None,
    timeout: int = 120,
) -> RewriteResult:
    """Rewrite text with the chosen provider.

    Returns the model output. Raises ProviderError if the provider is chosen
    but unavailable; the CLI decides whether to fall back to rule-only mode.
    """
    system = build_system_prompt(audience, tone)
    user = build_user_prompt(text)

    if provider == "none":
        return RewriteResult(text=text, provider="none", model=None)

    chosen_model = model or DEFAULT_MODELS.get(provider)
    if provider == "ollama":
        out = _ollama(system, user, chosen_model, timeout)
    elif provider == "openai":
        out = _openai(system, user, chosen_model, timeout)
    elif provider == "anthropic":
        out = _anthropic(system, user, chosen_model, timeout)
    else:
        raise ProviderError(f"Unknown provider: {provider!r}")

    if not out:
        raise ProviderError(f"{provider} returned an empty response.")
    return RewriteResult(text=out, provider=provider, model=chosen_model)
