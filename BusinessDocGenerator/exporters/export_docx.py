from docx import Document
from datetime import datetime


def export_to_docx(text: str, filename: str):

    doc = Document()

    doc.add_heading("Business Test Documentation", level=1)
    doc.add_paragraph(f"Generated On: {datetime.now()}")

    doc.add_paragraph()
    for line in text.split("\n"):
        doc.add_paragraph(line)

    doc.save(filename)

    return filename