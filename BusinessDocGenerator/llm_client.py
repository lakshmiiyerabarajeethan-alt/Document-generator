import httpx
import os
from dotenv import load_dotenv

load_dotenv()

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
                        "content": f"""
You are a Product Documentation Specialist writing an END-USER CUSTOMER GUIDE.

Write a user guide in MARKDOWN that matches the writing style, tone, and level of detail of a professional SaaS product help document.

The guide should:
- Be written for customers and non-technical end users
- Explain how to use the product step by step
- Describe every user action clearly and sequentially
- Explain what the user should click, enter, or select
- Explain what the user should see after each action
- Focus on how the product is used, not how it is built

Writing Style Requirements:
- Clear, instructional, and business-friendly
- Step-based explanations using “Step X:” headings
- Short paragraphs under each step
- Use bullet points and numbered sub-steps where helpful
- Neutral, professional tone (no marketing language)
- Assume the user is accessing the product via a web browser

Formatting Requirements:
- Output must be valid MARKDOWN
- Use headings and subheadings naturally where appropriate
- Use horizontal separators (---) to divide major sections
- Include Markdown image placeholders under relevant steps using:
  ![Descriptive image text](image-url-placeholder)
- Do not include code blocks, APIs, or technical architecture
- Do not mention internal systems or backend behavior

Content Expectations:
- Start with a brief introduction explaining what the guide covers
- Cover the full end-to-end user journey
- Include login/access steps if applicable
- Include step-by-step instructions for key user actions
- Include verification steps so users know when an action is successful
- Include optional steps where applicable (clearly marked)
- End with a short summary of what the user can accomplish

The final output should read like an official product user guide that could be published directly to a customer documentation portal.


      
"""
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
