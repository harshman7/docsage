"""
LLM via Google Gemini (Google AI Studio / Generative Language API).
"""
import requests
from typing import Optional
from app.config import settings


def call_llm(prompt: str, system_prompt: Optional[str] = None, timeout: int = 30) -> str:
    """
    Call Gemini with an optional system instruction.

    Requires GOOGLE_API_KEY or GEMINI_API_KEY in the environment (see api/.env).
    """
    try:
        if not settings.GOOGLE_API_KEY:
            return (
                "Error: GOOGLE_API_KEY not set. Create a key at "
                "https://aistudio.google.com/apikey and set GOOGLE_API_KEY or GEMINI_API_KEY in api/.env."
            )

        model_id = settings.GOOGLE_AI_MODEL.strip()
        if model_id.startswith("models/"):
            model_id = model_id[len("models/") :]

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
            return f"Error calling Google Gemini API: invalid JSON ({response.status_code})"

        if response.status_code != 200:
            err = data.get("error") if isinstance(data, dict) else None
            msg = err.get("message", response.text) if isinstance(err, dict) else response.text
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
    except requests.exceptions.Timeout:
        return "Error calling Google Gemini API: request timed out."
    except Exception as e:
        return f"Error calling Google Gemini API: {str(e)}"
