"""
LLM via Google Gemini (Google AI Studio / Generative Language API).
Supports a primary model plus comma-separated fallbacks on overload / transient errors.
"""
import time
from typing import Optional, Tuple

import requests

from app.config import settings

# Retry same model with backoff, then advance to next model in chain.
_RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})
# Bad model / not found — try next model in chain.
_TRY_NEXT_MODEL_STATUS = frozenset({400, 404})


def _normalize_model_id(raw: str) -> str:
    m = (raw or "").strip()
    if m.startswith("models/"):
        m = m[len("models/") :]
    return m


def _model_chain() -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    parts = [settings.GOOGLE_AI_MODEL] + settings.GOOGLE_AI_MODEL_FALLBACKS.split(",")
    for part in parts:
        m = _normalize_model_id(part)
        if m and m not in seen:
            seen.add(m)
            out.append(m)
    return out


def _parse_generate_response(data: object, response: requests.Response) -> str:
    if response.status_code != 200:
        if isinstance(data, dict):
            err = data.get("error")
            msg = err.get("message", response.text) if isinstance(err, dict) else response.text
        else:
            msg = response.text
        return f"Error calling Google Gemini API (HTTP {response.status_code}): {msg}"

    if not isinstance(data, dict):
        return "Error calling Google Gemini API: unexpected response shape."

    candidates = data.get("candidates") or []
    if not candidates:
        fb = data.get("promptFeedback")
        block = (fb or {}).get("blockReason") if isinstance(fb, dict) else None
        extra = f" ({block})" if block else ""
        return f"Error: Gemini returned no candidates{extra}."

    content = candidates[0].get("content") if isinstance(candidates[0], dict) else None
    parts = (content or {}).get("parts") or [] if isinstance(content, dict) else []
    texts = [p.get("text", "") for p in parts if isinstance(p, dict) and p.get("text")]
    out = "".join(texts).strip()
    if not out:
        fr = candidates[0].get("finishReason") if isinstance(candidates[0], dict) else None
        return f"Error: Gemini returned empty text" + (f" (finishReason={fr})." if fr else ".")
    return out


def _request_generate(
    model_id: str,
    prompt: str,
    system_prompt: Optional[str],
    timeout: float,
) -> Tuple[Optional[str], int, str, Optional[requests.Response]]:
    """
    Returns (assistant_text_on_200, http_status, error_detail, response).
    On HTTP 200, first value is model output (may be an "Error: ..." user string for empty candidates).
    """
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model_id}:generateContent"
    )
    body: dict = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
    }
    if system_prompt:
        body["systemInstruction"] = {"parts": [{"text": (system_prompt or "").strip()}]}

    response = requests.post(
        url,
        params={"key": settings.GOOGLE_API_KEY},
        json=body,
        timeout=timeout,
    )
    try:
        data = response.json()
    except Exception:
        return None, response.status_code, f"invalid JSON ({response.status_code})", response

    if response.status_code != 200:
        if isinstance(data, dict):
            err = data.get("error")
            msg = err.get("message", response.text) if isinstance(err, dict) else response.text
        else:
            msg = response.text
        return None, response.status_code, msg, response

    parsed = _parse_generate_response(data, response)
    return parsed, 200, "", response


def call_llm(prompt: str, system_prompt: Optional[str] = None, timeout: int = 30) -> str:
    """
    Call Gemini with an optional system instruction.

    Tries GOOGLE_AI_MODEL first, then each id in GOOGLE_AI_MODEL_FALLBACKS (comma-separated).
    Retries transient errors (429, 5xx) with backoff per model before moving on.

    Requires GOOGLE_API_KEY or GEMINI_API_KEY in the environment (see api/.env).
    """
    try:
        if not settings.GOOGLE_API_KEY:
            return (
                "Error: GOOGLE_API_KEY not set. Create a key at "
                "https://aistudio.google.com/apikey and set GOOGLE_API_KEY or GEMINI_API_KEY in api/.env."
            )

        chain = _model_chain()
        if not chain:
            return "Error: No Gemini models configured (GOOGLE_AI_MODEL empty)."

        attempts_per_model = 3
        last_errors: list[str] = []

        for model_id in chain:
            for attempt in range(attempts_per_model):
                try:
                    text, status, detail, resp = _request_generate(
                        model_id, prompt, system_prompt, float(timeout)
                    )
                except requests.exceptions.Timeout:
                    last_errors.append(f"{model_id}: request timed out")
                    time.sleep(min(2.0**attempt, 8.0))
                    continue

                if status == 200 and text is not None:
                    return text

                if status in (401, 403):
                    return (
                        f"Error calling Google Gemini API (HTTP {status}): {detail}. "
                        "Check GOOGLE_API_KEY permissions."
                    )

                msg = detail or "unknown error"
                last_errors.append(f"{model_id} (HTTP {status}): {msg}")

                if status in _TRY_NEXT_MODEL_STATUS:
                    break

                if status in _RETRYABLE_STATUS and attempt < attempts_per_model - 1:
                    wait = min(2.0**attempt, 20.0)
                    if resp is not None:
                        ra = resp.headers.get("Retry-After")
                        if ra:
                            try:
                                wait = min(max(float(ra), 0.5), 60.0)
                            except ValueError:
                                pass
                    time.sleep(wait)
                    continue

                break

        summary = "; ".join(last_errors[-5:])
        return (
            "Error: All configured Gemini models failed. Last messages: "
            f"{summary}. You can adjust GOOGLE_AI_MODEL and GOOGLE_AI_MODEL_FALLBACKS in api/.env."
        )
    except Exception as e:
        return f"Error calling Google Gemini API: {str(e)}"
