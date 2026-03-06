import os
import json
import re
from io import BytesIO
from dotenv import load_dotenv
import httpx

from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

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
DEFAULT_MODEL = "gpt-4-turbo-preview"

# ------------------------------------------------------
# System prompt — instructs the LLM to return
# structured JSON matching the user guide format
# ------------------------------------------------------
SYSTEM_PROMPT = """You are an expert technical writer specializing in
clear, professional, step-by-step user guides for non-technical users.

IMPORTANT: You must respond ONLY with a valid JSON object and nothing else.
Do not include markdown fences, preamble, or any text outside the JSON.

The JSON must follow this exact structure:
{
  "title": "string — document title",
  "purpose": "string — 2-3 sentence overview of what the guide covers",
  "steps": [
    {
      "title": "string — e.g. 'Step 1: Access the Application'",
      "instructions": [
        "string — each bullet point instruction"
      ]
    }
  ],
  "help_section": "string — closing support/help paragraph"
}

Guidelines:
- Use clear, action-oriented language (Click, Navigate, Enter, Select)
- Bold key UI element names inside instructions using **double asterisks**
- Each step should have 2-5 concise bullet instructions
- The help_section should invite users to contact support if needed
"""


# ------------------------------------------------------
# build_docx: convert guide JSON dict to .docx bytes
# Produces the Single Asset Upload User Guide style
# ------------------------------------------------------
def build_docx(data: dict) -> bytes:
    """
    Convert a structured guide dict into a formatted .docx file.

    Args:
        data (dict): Parsed guide JSON with keys:
                     title, purpose, steps[], help_section

    Returns:
        bytes: The .docx file content
    """
    doc = Document()

    # Page margins (1 inch all around)
    for section in doc.sections:
        section.top_margin    = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin   = Inches(1)
        section.right_margin  = Inches(1)

    def add_run_with_bold(paragraph, text: str):
        """Parse **bold** markers and add styled runs to a paragraph."""
        parts = re.split(r"(\*\*[^*]+\*\*)", text)
        for part in parts:
            if part.startswith("**") and part.endswith("**"):
                run = paragraph.add_run(part[2:-2])
                run.bold = True
            else:
                if part:
                    paragraph.add_run(part)

    # Title
    title_para = doc.add_paragraph()
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_para.add_run(data.get("title", "User Guide"))
    title_run.bold = True
    title_run.font.size = Pt(18)
    title_run.font.color.rgb = RGBColor(0x1F, 0x49, 0x7D)

    doc.add_paragraph()

    # Purpose
    purpose_heading = doc.add_paragraph()
    ph_run = purpose_heading.add_run("Purpose")
    ph_run.bold = True
    ph_run.font.size = Pt(13)

    purpose_body = doc.add_paragraph()
    purpose_body.paragraph_format.space_after = Pt(8)
    add_run_with_bold(purpose_body, data.get("purpose", ""))

    # Step-by-Step Instructions heading
    doc.add_paragraph()
    sbs_heading = doc.add_paragraph()
    sbs_run = sbs_heading.add_run("Step-by-Step Instructions")
    sbs_run.bold = True
    sbs_run.font.size = Pt(13)

    # Steps
    for step in data.get("steps", []):
        step_title_para = doc.add_paragraph()
        step_title_para.paragraph_format.space_before = Pt(8)
        st_run = step_title_para.add_run(step.get("title", ""))
        st_run.bold = True
        st_run.font.size = Pt(11)

        for instruction in step.get("instructions", []):
            bullet = doc.add_paragraph(style="List Bullet")
            bullet.paragraph_format.left_indent = Inches(0.25)
            bullet.paragraph_format.space_after = Pt(3)
            add_run_with_bold(bullet, instruction)

    # Need Help
    doc.add_paragraph()
    help_heading = doc.add_paragraph()
    hh_run = help_heading.add_run("Need Help?")
    hh_run.bold = True
    hh_run.font.size = Pt(13)

    help_body = doc.add_paragraph()
    add_run_with_bold(help_body, data.get("help_section", ""))

    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


# ------------------------------------------------------
# Standard (non-streaming) LLM call
# Returns a parsed guide dict — callers decide how to export
# ------------------------------------------------------
async def call_llm(prompt: str, model: str | None = None) -> dict:
    """
    Call OpenAI Chat Completions API and return a structured guide dict.

    The dict has keys: title, purpose, steps[], help_section
    Pass it to build_docx() or export_to_pdf() to produce files.

    Args:
        prompt (str): Workflow description prompt
        model (str | None): Optional model override

    Returns:
        dict: Structured guide data
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
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 4000,
                "response_format": {"type": "json_object"}
            }
        )

        data = response.json()

        if response.status_code != 200:
            raise RuntimeError(
                f"OpenAI API error {response.status_code}: {data}"
            )

        if "choices" not in data or not data["choices"]:
            raise RuntimeError("OpenAI API returned no choices")

        raw_text = data["choices"][0]["message"]["content"]

        try:
            return json.loads(raw_text)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"LLM returned invalid JSON: {e}\n\n{raw_text}")


# ------------------------------------------------------
# Streaming LLM call
# Yields raw JSON text chunks; assemble and parse when done
# ------------------------------------------------------
async def call_llm_streaming(prompt: str, model: str | None = None):
    """
    Stream OpenAI responses in real time.

    Yields raw JSON text chunks. When the stream ends, join all chunks
    and pass through json.loads() + build_docx() to produce a file.

    Example:
        chunks = []
        async for chunk in call_llm_streaming("..."):
            chunks.append(chunk)
        guide_data = json.loads("".join(chunks))
        docx_bytes = build_docx(guide_data)
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
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": prompt}
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
                    chunk_data = json.loads(chunk)
                    delta = chunk_data["choices"][0].get("delta", {})
                    if "content" in delta:
                        yield delta["content"]
                except Exception:
                    continue
