import httpx

from app.core.config import settings


class LlmServiceError(RuntimeError):
    pass


def generate_text(prompt: str) -> str:
    if settings.LLM_PROVIDER != "ollama":
        raise LlmServiceError("Unsupported LLM provider")

    url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate"
    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }

    try:
        response = httpx.post(url, json=payload, timeout=120)
        response.raise_for_status()
    except httpx.RequestError as exc:
        raise LlmServiceError("LLM provider is unavailable") from exc
    except httpx.HTTPStatusError as exc:
        raise LlmServiceError("LLM provider returned an error") from exc

    data = response.json()
    generated_text = data.get("response")
    if not isinstance(generated_text, str):
        raise LlmServiceError("LLM provider returned an invalid response")

    return generated_text.strip()
