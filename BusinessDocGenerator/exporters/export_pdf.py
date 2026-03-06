"""
exporters/export_pdf.py

Converts a structured guide dict directly to a formatted PDF.
Mirrors the same section layout as export_docx (title, purpose,
step-by-step instructions, need help) using ReportLab.
"""

import re
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY


def export_to_pdf(guide_data: dict, output_file: str) -> None:
    """
    Convert a structured guide dict to a formatted PDF and save to disk.

    Args:
        guide_data (dict): Guide dict from call_llm() with keys:
                           title, purpose, steps[], help_section
        output_file (str): Destination path for the .pdf file
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    doc = SimpleDocTemplate(
        output_file,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "GuideTitle",
        parent=styles["Heading1"],
        fontSize=20,
        textColor=colors.HexColor("#1F497D"),
        spaceAfter=16,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    )

    section_heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#1F497D"),
        spaceBefore=14,
        spaceAfter=6,
        fontName="Helvetica-Bold",
    )

    step_heading_style = ParagraphStyle(
        "StepHeading",
        parent=styles["Heading3"],
        fontSize=11,
        textColor=colors.black,
        spaceBefore=10,
        spaceAfter=4,
        fontName="Helvetica-Bold",
    )

    body_style = ParagraphStyle(
        "GuideBody",
        parent=styles["BodyText"],
        fontSize=11,
        leading=16,
        spaceAfter=8,
        alignment=TA_JUSTIFY,
    )

    bullet_style = ParagraphStyle(
        "GuideBullet",
        parent=styles["BodyText"],
        fontSize=11,
        leading=16,
        leftIndent=20,
        spaceAfter=4,
    )

    def md_to_html(text: str) -> str:
        """Convert **bold** markers to ReportLab <b> tags."""
        return re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)

    elements = []

    # Title
    elements.append(Paragraph(guide_data.get("title", "User Guide"), title_style))
    elements.append(Spacer(1, 0.1 * inch))

    # Purpose
    elements.append(Paragraph("Purpose", section_heading_style))
    elements.append(Paragraph(
        md_to_html(guide_data.get("purpose", "")), body_style
    ))

    # Step-by-Step Instructions
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph("Step-by-Step Instructions", section_heading_style))

    for step in guide_data.get("steps", []):
        elements.append(Paragraph(step.get("title", ""), step_heading_style))
        for instruction in step.get("instructions", []):
            elements.append(Paragraph(
                f"• {md_to_html(instruction)}", bullet_style
            ))

    # Need Help
    elements.append(Spacer(1, 0.15 * inch))
    elements.append(Paragraph("Need Help?", section_heading_style))
    elements.append(Paragraph(
        md_to_html(guide_data.get("help_section", "")), body_style
    ))

    doc.build(elements)
    print(f"✓ PDF saved to: {output_file}")
