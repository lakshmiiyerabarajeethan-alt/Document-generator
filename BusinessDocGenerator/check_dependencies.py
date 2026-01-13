"""
Script to create all necessary files for the exporters package.
Run this in your project root directory.
"""

import os

# Create exporters directory
os.makedirs("exporters", exist_ok=True)

# Create __init__.py
init_content = '''"""
Exporters package for converting documentation to various formats.
"""

from .export_docx import export_to_docx
from .export_pdf import export_to_pdf

__all__ = ['export_to_docx', 'export_to_pdf']
'''

with open("exporters/__init__.py", "w", encoding="utf-8") as f:
    f.write(init_content)
    print("✅ Created: exporters/__init__.py")

# Message for other files
print("\n📝 Now you need to create these files:")
print("   1. exporters/export_docx.py")
print("   2. exporters/export_pdf.py")
print("\nCopy the content from the artifacts I provided.")
print("\nOr download them from your project repository.")