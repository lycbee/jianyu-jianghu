"""Multi-provider AI API client using only Python standard library.

Supports: Anthropic, DeepSeek (auto-detected from API key prefix).
"""

import json
import os
import urllib.request
import urllib.error


def _detect_provider() -> str:
    """Detect API provider from the API key prefix."""
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if key.startswith("sk-ant"):
        return "anthropic"
    return "deepseek"


def call_claude(
    prompt: str,
    *,
    system: str = "",
    model: str | None = None,
    max_tokens: int = 4096,
    temperature: float = 0.7,
) -> str:
    """Call the AI API and return the response text.

    Auto-detects provider from API key format.
    For Anthropic keys (sk-ant-*), uses Anthropic Messages API.
    For other keys (sk-*), uses DeepSeek/OpenAI-compatible Chat Completions API.
    """
    provider = _detect_provider()

    if provider == "anthropic":
        return _call_anthropic(prompt, system=system, model=model,
                               max_tokens=max_tokens, temperature=temperature)
    else:
        return _call_deepseek(prompt, system=system, model=model,
                              max_tokens=max_tokens, temperature=temperature)


def _call_anthropic(
    prompt: str,
    *,
    system: str = "",
    model: str | None = None,
    max_tokens: int = 4096,
    temperature: float = 0.7,
) -> str:
    """Call Anthropic Messages API."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    if model is None:
        model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

    body = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        body["system"] = system

    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=data,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )

    with _send_request(req) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    content = result.get("content", [])
    if not content:
        raise RuntimeError(f"Empty response: {json.dumps(result, ensure_ascii=False)[:500]}")
    return content[0].get("text", "")


def _call_deepseek(
    prompt: str,
    *,
    system: str = "",
    model: str | None = None,
    max_tokens: int = 4096,
    temperature: float = 0.7,
) -> str:
    """Call DeepSeek API (OpenAI-compatible Chat Completions)."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    if model is None:
        model = os.getenv("ANTHROPIC_MODEL", "deepseek-chat")

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    body = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": messages,
    }

    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        "https://api.deepseek.com/v1/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with _send_request(req) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    choices = result.get("choices", [])
    if not choices:
        raise RuntimeError(f"Empty response: {json.dumps(result, ensure_ascii=False)[:500]}")
    return choices[0]["message"]["content"]


def _send_request(req: urllib.request.Request):
    """Send HTTP request with error handling."""
    try:
        return urllib.request.urlopen(req, timeout=300)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"API error {e.code}: {error_body[:500]}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Network error: {e.reason}") from e
