"""
PDF Generator Module
Converts Markdown summaries to PDF files
"""

import markdown
from fpdf import FPDF
import re

class PDFGenerator:
    def __init__(self):
        pass

    def clean_markdown(self, text):
        """
        Strip markdown formatting for simple PDF text generation
        or prepare it for processing.
        For FPDF, we often need to strip bold/italic markers or handle them specifically.
        This is a simple implementation that strips some common markdown.
        """
        # Remove bold/italic markers
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        return text

    def generate_pdf(self, markdown_content, output_file):
        """
        Generate a simple PDF from markdown content
        """
        pdf = FPDF()
        pdf.add_page()
        
        # Add a Unicode font (DejaVu) to support emojis and varied characters if possible,
        # but for standard FPDF we might stick to built-in fonts or need to load a TTF.
        # For simplicity/reliability without external assets, we use standard fonts 
        # and replace unsupported characters.
        pdf.set_font("Arial", size=12)
        
        # Split content by lines
        lines = markdown_content.split('\n')
        
        for line in lines:
            # Handle headers
            if line.startswith('# '):
                pdf.set_font("Arial", 'B', 24)
                text = line.replace('# ', '')
                pdf.cell(200, 15, txt=text.encode('latin-1', 'replace').decode('latin-1'), ln=1)
                pdf.set_font("Arial", size=12)
            elif line.startswith('## '):
                pdf.set_font("Arial", 'B', 18)
                text = line.replace('## ', '')
                pdf.cell(200, 12, txt=text.encode('latin-1', 'replace').decode('latin-1'), ln=1)
                pdf.set_font("Arial", size=12)
            elif line.startswith('### '):
                pdf.set_font("Arial", 'B', 14)
                text = line.replace('### ', '')
                pdf.cell(200, 10, txt=text.encode('latin-1', 'replace').decode('latin-1'), ln=1)
                pdf.set_font("Arial", size=12)
            elif line.startswith('---'):
                pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                pdf.ln(5)
            else:
                # Regular text
                # Basic cleaning
                text = self.clean_markdown(line)
                if text.strip():
                    pdf.multi_cell(0, 8, txt=text.encode('latin-1', 'replace').decode('latin-1'))
                else:
                    pdf.ln(5)

        pdf.output(output_file)
        return output_file
