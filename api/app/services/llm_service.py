"""
Shared LLM service that supports multiple providers (Ollama, Groq, Hugging Face).
"""
import requests
from typing import Optional
from app.config import settings

def call_llm(prompt: str, system_prompt: Optional[str] = None, timeout: int = 30) -> str:
    """
    Call LLM API based on configured provider.
    
    Args:
        prompt: User prompt
        system_prompt: Optional system prompt
        timeout: Request timeout in seconds
        
    Returns:
        LLM response text
    """
    provider = settings.LLM_PROVIDER.lower()
    
    if provider == "groq":
        return _call_groq(prompt, system_prompt, timeout)
    elif provider == "huggingface":
        return _call_huggingface(prompt, system_prompt, timeout)
    else:  # Default to Ollama
        return _call_ollama(prompt, system_prompt, timeout)

def _call_ollama(prompt: str, system_prompt: Optional[str] = None, timeout: int = 30) -> str:
    """Call Ollama API."""
    try:
        url = f"{settings.OLLAMA_BASE_URL}/api/generate"
        payload = {
            "model": settings.OLLAMA_MODEL,
            "prompt": prompt,
            "system": system_prompt or "",
            "stream": False
        }
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
        return response.json().get("response", "")
    except Exception as e:
        return f"Error calling Ollama: {str(e)}"

def _call_groq(prompt: str, system_prompt: Optional[str] = None, timeout: int = 30) -> str:
    """Call Groq API (free tier available)."""
    try:
        if not settings.GROQ_API_KEY:
            return "Error: GROQ_API_KEY not set. Get a free API key from https://console.groq.com/"
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": settings.GROQ_MODEL,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2048
        }
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error calling Groq API: {str(e)}"

def _call_huggingface(prompt: str, system_prompt: Optional[str] = None, timeout: int = 60) -> str:
    """Call Hugging Face Inference API (free tier available)."""
    try:
        if not settings.HUGGINGFACE_API_KEY:
            return "Error: HUGGINGFACE_API_KEY not set. Get a free API key from https://huggingface.co/settings/tokens"
        
        url = f"https://api-inference.huggingface.co/models/{settings.HUGGINGFACE_MODEL}"
        headers = {
            "Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}",
            "Content-Type": "application/json"
        }
        
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        payload = {
            "inputs": full_prompt,
            "parameters": {
                "max_new_tokens": 512,
                "temperature": 0.7,
                "return_full_text": False
            }
        }
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        response.raise_for_status()
        result = response.json()
        
        # Handle different response formats
        if isinstance(result, list) and len(result) > 0:
            return result[0].get("generated_text", str(result[0]))
        elif isinstance(result, dict) and "generated_text" in result:
            return result["generated_text"]
        else:
            return str(result)
    except Exception as e:
        return f"Error calling Hugging Face API: {str(e)}"

