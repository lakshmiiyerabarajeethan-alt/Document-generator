import httpx
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


async def call_llm(prompt: str):

    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set")

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}"
            },
            json={
                "model": "gpt-4.1-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a QA analyst writing formal business test documentation."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
        )

        data = response.json()
        return data["choices"][0]["message"]["content"]
