import httpx
import os
from dotenv import load_dotenv

load_dotenv()


async def call_llm(prompt: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    async with httpx.AsyncClient(timeout=90) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4.1-mini",
                "temperature": 0.4,
                "messages": [
                    {
                        "role": "system",
                        "content": """
You are a technical writer assistant that generates high-quality user guides. Follow the structure and format below exactly.

### INSTRUCTIONS
Write a user guide based on the topic I provide. The guide must be clear, step-by-step, and easy for non-technical users to follow.

### REQUIRED SECTIONS
1. **Title**
   - Write a clear descriptive title of the user guide.

2. **1. Purpose**
   - Explain in 1–2 sentences why this guide exists and what it helps the user accomplish.

3. **2. Scope**
   - Describe who can use this guide and in what situations.

4. **3. Prerequisites**
   - List all things the user must have or know before starting (requirements, tools, permissions, etc.).
   - Format as bullet points.

5. **4. Steps**
   - Break down the process into major steps.
   - For each step:
     - Provide a Step heading (e.g., "Step X – Description").
     - Provide ordered sub-steps.
     - Include examples, screenshots labels, or prompts where appropriate.
     - Use the same formatting style as the example (numbered lists, indented examples).

6. **5. Troubleshooting**
   - Create a table with common issues and solutions.
   - Include at least 3 rows.

7. **6. Tips (Optional)**
   - Provide practical tips, best practices, or warnings related to the task.
   - List as bullet points.

8. **7. Contact Support**
   - Provide information on where to get help if steps fail.
   - Include links or search terms for official support where relevant.

### STYLE GUIDELINES
• Use simple and direct language.  
• Use numbered steps for clarity.  
• Keep each step concise but complete.  
• Maintain consistent formatting with separators like "________________________________________" between major sections.
"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
            },
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"LLM request failed ({response.status_code}): {response.text}"
            )

        data = response.json()
        return data["choices"][0]["message"]["content"]
