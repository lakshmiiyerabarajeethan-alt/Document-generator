import os
from dotenv import load_dotenv
import httpx

# ------------------------------------------------------
# Load environment variables FIRST (critical)
# ------------------------------------------------------
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY not set. "
        "Ensure it exists in your .env file or environment variables."
    )

# ------------------------------------------------------
# OpenAI configuration
# ------------------------------------------------------
DEFAULT_MODEL = "gpt-4-turbo-preview"  # High-quality technical writing


# ------------------------------------------------------
# Standard (non-streaming) LLM call
# ------------------------------------------------------
async def call_llm(prompt: str, model: str | None = None) -> str:
    """
    Call OpenAI Chat Completions API to generate documentation.

    Args:
        prompt (str): Prompt text
        model (str | None): Optional model override

    Returns:
        str: Generated documentation text
    """
    selected_model = model or DEFAULT_MODEL

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": selected_model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are an expert technical writer specializing in "
                            "clear, professional, step-by-step user guides "
                            "for non-technical users."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 4000
            }
        )

        data = response.json()

        if response.status_code != 200:
            raise RuntimeError(
                f"OpenAI API error {response.status_code}: {data}"
            )

        if "choices" not in data or not data["choices"]:
            raise RuntimeError("OpenAI API returned no choices")

        return data["choices"][0]["message"]["content"]


# ------------------------------------------------------
# Streaming LLM call (optional, advanced use)
# ------------------------------------------------------
async def call_llm_streaming(prompt: str, model: str | None = None):
    """
    Stream OpenAI responses in real time.

    Args:
        prompt (str): Prompt text
        model (str | None): Optional model override

    Yields:
        str: Partial chunks of generated text
    """
    selected_model = model or DEFAULT_MODEL

    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream(
            "POST",
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": selected_model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are an expert technical writer creating "
                            "clear, structured documentation."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 4000,
                "stream": True
            }
        ) as response:
            async for line in response.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue

                chunk = line.replace("data: ", "")

                if chunk == "[DONE]":
                    break

                try:
                    import json
                    data = json.loads(chunk)
                    delta = data["choices"][0].get("delta", {})
                    if "content" in delta:
                        yield delta["content"]
                except Exception:
                    continue
