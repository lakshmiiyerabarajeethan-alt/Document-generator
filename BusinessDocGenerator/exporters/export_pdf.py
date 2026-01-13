"""
Export generated documentation to PDF format.
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
import re


def export_to_pdf(markdown_text: str, output_file: str):
    """
    Convert markdown text to a formatted PDF document.
    
    Args:
        markdown_text: The markdown-formatted documentation text
        output_file: Path where the PDF file should be saved
    """
    
    # Create PDF document
    doc = SimpleDocTemplate(
        output_file,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1F4E78'),
        spaceAfter=30,
        alignment=TA_CENTER,
    )
    
    heading1_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1F4E78'),
        spaceAfter=12,
        spaceBefore=12,
    )
    
    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#4F81BD'),
        spaceAfter=10,
        spaceBefore=10,
    )
    
    heading3_style = ParagraphStyle(
        'CustomHeading3',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#4F81BD'),
        spaceAfter=8,
        spaceBefore=8,
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        leading=16,
        alignment=TA_JUSTIFY,
        spaceAfter=12,
    )
    
    code_style = ParagraphStyle(
        'CustomCode',
        parent=styles['Code'],
        fontSize=9,
        fontName='Courier',
        textColor=colors.HexColor('#C80000'),
        leftIndent=20,
        spaceAfter=6,
    )
    
    bullet_style = ParagraphStyle(
        'CustomBullet',
        parent=styles['BodyText'],
        fontSize=11,
        leftIndent=20,
        bulletIndent=10,
        spaceAfter=6,
    )
    
    # Split text into lines
    lines = markdown_text.split('\n')
    
    in_code_block = False
    in_table = False
    table_lines = []
    is_first_heading = True
    
    for line in lines:
        line_stripped = line.strip()
        
        # Skip empty lines (but add spacing)
        if not line_stripped:
            if not in_code_block and not in_table:
                elements.append(Spacer(1, 0.1 * inch))
            continue
        
        # Handle code blocks
        if line_stripped.startswith('```'):
            in_code_block = not in_code_block
            continue
        
        if in_code_block:
            elements.append(Paragraph(_escape_html(line), code_style))
            continue
        
        # Handle tables
        if line_stripped.startswith('|'):
            if not in_table:
                in_table = True
                table_lines = []
            table_lines.append(line_stripped)
            continue
        else:
            if in_table:
                # Process accumulated table
                _add_table_to_pdf(elements, table_lines)
                in_table = False
                table_lines = []
        
        # Handle headers
        if line_stripped.startswith('#'):
            level = len(line_stripped) - len(line_stripped.lstrip('#'))
            text = line_stripped.lstrip('#').strip()
            text = _escape_html(text)
            
            if level == 1:
                if is_first_heading:
                    elements.append(Paragraph(text, title_style))
                    is_first_heading = False
                else:
                    elements.append(Paragraph(text, heading1_style))
            elif level == 2:
                elements.append(Paragraph(text, heading1_style))
            elif level == 3:
                elements.append(Paragraph(text, heading2_style))
            else:
                elements.append(Paragraph(text, heading3_style))
            
            continue
        
        # Handle horizontal rules
        if line_stripped in ['---', '___', '***', '________________________________________']:
            elements.append(Spacer(1, 0.2 * inch))
            elements.append(Paragraph('_' * 100, body_style))
            elements.append(Spacer(1, 0.2 * inch))
            continue
        
        # Handle bullet lists
        if line_stripped.startswith(('- ', '* ', '+ ')):
            text = line_stripped[2:].strip()
            text = _convert_markdown_formatting(text)
            elements.append(Paragraph(f'• {text}', bullet_style))
            continue
        
        # Handle numbered lists
        if re.match(r'^\d+\.\s', line_stripped):
            text = re.sub(r'^(\d+)\.\s', r'<b>\1.</b> ', line_stripped).strip()
            text = _convert_markdown_formatting(text)
            elements.append(Paragraph(text, bullet_style))
            continue
        
        # Handle regular paragraphs
        text = _convert_markdown_formatting(line_stripped)
        elements.append(Paragraph(text, body_style))
    
    # Process any remaining table
    if in_table and table_lines:
        _add_table_to_pdf(elements, table_lines)
    
    # Build PDF
    doc.build(elements)
    print(f"✓ PDF exported to: {output_file}")


def _add_table_to_pdf(elements, table_lines):
    """Add a markdown table to the PDF."""
    if len(table_lines) < 2:
        return
    
    # Parse table rows
    rows = []
    for line in table_lines:
        if line.startswith('|---') or line.startswith('| ---'):
            continue  # Skip separator line
        
        cells = [cell.strip() for cell in line.split('|')[1:-1]]
        if cells:
            rows.append(cells)
    
    if not rows:
        return
    
    # Create table
    table = Table(rows)
    
    # Style the table
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F81BD')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ])
    
    table.setStyle(table_style)
    
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(table)
    elements.append(Spacer(1, 0.2 * inch))


def _escape_html(text):
    """Escape HTML special characters."""
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text


def _convert_markdown_formatting(text):
    """Convert markdown formatting to ReportLab HTML tags."""
    
    # Escape HTML first
    text = _escape_html(text)
    
    # Remove image syntax
    text = re.sub(r'!\[([^\]]*)\]\([^\)]*\)', r'\1', text)
    
    # Convert links
    text = re.sub(r'\[([^\]]*)\]\(([^\)]*)\)', r'<link href="\2">\1</link>', text)
    
    # Convert bold
    text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
    
    # Convert italic
    text = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', text)
    
    # Convert inline code
    text = re.sub(r'`([^`]+)`', r'<font name="Courier" color="#C80000">\1</font>', text)
    
    return text