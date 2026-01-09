from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from textwrap import wrap


def export_to_pdf(text: str, filename: str):

    c = canvas.Canvas(filename, pagesize=A4)

    width, height = A4
    x = 40
    y = height - 60

    wrapped_lines = []
    for line in text.split("\n"):
        wrapped_lines.extend(wrap(line, 90))

    for line in wrapped_lines:
            if y < 60:
                c.showPage()
                y = height - 60
            c.drawString(x, y, line)
            y -= 18

    c.save()

    return filename