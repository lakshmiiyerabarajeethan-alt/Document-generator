"""
exporters/export_docx.py

Saves a structured guide dict to a .docx file.
All formatting logic lives in llm_client.build_docx().
"""

import os
from llm_client import build_docx


def export_to_docx(guide_data: dict, output_file: str) -> None:
    """
    Convert a structured guide dict to a formatted .docx and save to disk.

    Args:
        guide_data (dict): Guide dict from call_llm() with keys:
                           title, purpose, steps[], help_section
        output_file (str): Destination path for the .docx file
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    docx_bytes = build_docx(guide_data)

    with open(output_file, "wb") as f:
        f.write(docx_bytes)

    print(f"✓ DOCX saved to: {output_file}")
