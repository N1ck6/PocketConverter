"""
Handles conversions between TXT, PDF, DOCX, Markdown, and other document formats.
Includes PDF merge/split functionality.
"""

from pathlib import Path
from io import StringIO
import sys


class DocumentConverter:
    SUPPORTED_EXTENSIONS = {
        'txt', 'pdf', 'docx', 'md', 'markdown', 'html', 
        'rtf', 'odt', 'epub'
    }
    
    def __init__(self, font_path: Path = None):
        self.font_path = font_path or self._get_default_font_path()
    
    def _get_default_font_path(self):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = Path(__file__).parent.parent

        return base_path / 'DejaVuSansCondensed.ttf'
    
    def convert(self, filepath: str, mode: str, new_name: str):
        ext = Path(filepath).suffix[1:]  # Remove leading dot
        
        if ext == "txt":
            self._convert_from_txt(filepath, mode, new_name)
        elif ext == "docx":
            self._convert_from_docx(filepath, mode, new_name)
        elif ext == "pdf":
            self._convert_from_pdf(filepath, mode, new_name)
        elif ext in ['md', 'markdown']:
            self._convert_from_markdown(filepath, mode, new_name)
        elif ext == "html":
            self._convert_from_html(filepath, mode, new_name)
    
    def _convert_from_txt(self, filepath: str, mode: str, new_name: str):
        if mode == "pdf":
            self._txt_to_pdf(filepath, new_name)
        elif mode == "docx":
            self._txt_to_docx(filepath, new_name)
        elif mode in ['md', 'markdown']:
            self._txt_to_markdown(filepath, new_name)
        elif mode == "html":
            self._txt_to_html(filepath, new_name)
    
    def _convert_from_docx(self, filepath: str, mode: str, new_name: str):
        if mode == "txt":
            self._docx_to_txt(filepath, new_name)
        elif mode == "pdf":
            self._docx_to_pdf(filepath, new_name)
        elif mode in ['md', 'markdown']:
            self._docx_to_markdown(filepath, new_name)
    
    def _convert_from_pdf(self, filepath: str, mode: str, new_name: str):
        if mode == "txt":
            self._pdf_to_txt(filepath, new_name)
        elif mode == "docx":
            self._pdf_to_docx(filepath, new_name)
        elif mode == "md":
            self._pdf_to_markdown(filepath, new_name)
    
    def _convert_from_markdown(self, filepath: str, mode: str, new_name: str):
        if mode == "pdf":
            self._markdown_to_pdf(filepath, new_name)
        elif mode == "html":
            self._markdown_to_html(filepath, new_name)
        elif mode == "docx":
            self._markdown_to_docx(filepath, new_name)
        elif mode == "txt":
            self._markdown_to_txt(filepath, new_name)
    
    def _convert_from_html(self, filepath: str, mode: str, new_name: str):
        if mode == "pdf":
            self._html_to_pdf(filepath, new_name)
        elif mode == "txt":
            self._html_to_txt(filepath, new_name)
        elif mode == "md":
            self._html_to_markdown(filepath, new_name)
    
    def _txt_to_pdf(self, filepath: str, new_name: str):
        from fpdf import FPDF
        from textwrap import wrap
        
        pdf = FPDF()
        pdf.set_auto_page_break(True, margin=10)
        pdf.add_font('DejaVu', '', str(self.font_path), uni=True)
        pdf.set_font('DejaVu', '', size=11)
        pdf.add_page()
        
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
            for line in text.split('\n'):
                lines = wrap(line, 90)
                if not lines:
                    pdf.ln()
                for wrapped in lines:
                    pdf.cell(0, 4.8, wrapped, ln=1, align="J")
        
        output_path = Path(filepath).parent / f"{new_name}.pdf"
        pdf.output(output_path, 'F')
    
    def _txt_to_docx(self, filepath: str, new_name: str):
        from docx import Document
        
        doc = Document()
        with open(filepath, "r", encoding="utf-8") as f:
            doc.add_paragraph(f.read())
        
        output_path = Path(filepath).parent / f"{new_name}.docx"
        doc.save(output_path)
    
    def _txt_to_markdown(self, filepath: str, new_name: str):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        output_path = Path(filepath).parent / f"{new_name}.md"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
    
    def _txt_to_html(self, filepath: str, new_name: str):
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        html_content = "<!DOCTYPE html>\n<html>\n<head>\n<meta charset='utf-8'>\n</head>\n<body>\n<pre>\n"
        html_content += "".join(lines)
        html_content += "\n</pre>\n</body>\n</html>"
        
        output_path = Path(filepath).parent / f"{new_name}.html"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
    
    def _docx_to_txt(self, filepath: str, new_name: str):
        from docx import Document
        
        doc = Document(filepath)
        output_path = Path(filepath).parent / f"{new_name}.txt"
        
        with open(output_path, "w", encoding="utf-8") as f:
            for para in doc.paragraphs:
                f.write(para.text + "\n")
    
    def _docx_to_pdf(self, filepath: str, new_name: str):
        from docx2pdf import convert
        
        output_path = Path(filepath).parent / f"{new_name}.pdf"
        sys.stderr = StringIO()
        convert(filepath, output_path)
    
    def _docx_to_markdown(self, filepath: str, new_name: str):
        from docx import Document
        
        doc = Document(filepath)
        output_path = Path(filepath).parent / f"{new_name}.md"
        
        with open(output_path, "w", encoding="utf-8") as f:
            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    f.write(text + "\n\n")
    
    def _pdf_to_txt(self, filepath: str, new_name: str):
        from pymupdf import open as pdfopen
        
        output_path = Path(filepath).parent / f"{new_name}.txt"
        
        with open(output_path, "w", encoding="utf-8") as f:
            for page in pdfopen(filepath):
                f.write(page.get_text())
    
    def _pdf_to_docx(self, filepath: str, new_name: str):
        from pdf2docx import Converter
        
        cv = Converter(filepath)
        output_path = Path(filepath).parent / f"{new_name}.docx"
        cv.convert(output_path, start=0, end=None)
        cv.close()
    
    def _pdf_to_markdown(self, filepath: str, new_name: str):
        """Convert PDF to Markdown."""
        from pymupdf import open as pdfopen
        
        output_path = Path(filepath).parent / f"{new_name}.md"
        
        with open(output_path, "w", encoding="utf-8") as f:
            for page in pdfopen(filepath):
                text = page.get_text()
                # Heading markers
                lines = text.split('\n')
                for i, line in enumerate(lines):
                    if i == 0 and line.strip():
                        f.write(f"# {line}\n")
                    elif line.strip():
                        f.write(f"{line}\n")
                f.write("\n")
    
    def _markdown_to_pdf(self, filepath: str, new_name: str):
        """Convert Markdown to PDF."""
        try:
            import markdown
            from fpdf import FPDF
            
            with open(filepath, "r", encoding="utf-8") as f:
                md_content = f.read()

            html_content = markdown.markdown(md_content)
            
            pdf = FPDF()
            pdf.set_auto_page_break(True, margin=10)
            pdf.add_font('DejaVu', '', str(self.font_path), uni=True)
            pdf.set_font('DejaVu', '', size=11)
            pdf.add_page()
            
            import re
            text = re.sub(r'<[^>]+>', '\n', html_content)
            text = text.replace('&nbsp;', ' ')
            text = text.replace('&amp;', '&')
            text = text.replace('&lt;', '<')
            text = text.replace('&gt;', '>')
            
            for line in text.split('\n'):
                if line.strip():
                    pdf.cell(0, 4.8, line.strip(), ln=1, align="L")
            
            output_path = Path(filepath).parent / f"{new_name}.pdf"
            pdf.output(output_path, 'F')
            
        except ImportError:
            raise ImportError("markdown package required for Markdown conversion")
    
    def _markdown_to_html(self, filepath: str, new_name: str):
        try:
            import markdown
            
            with open(filepath, "r", encoding="utf-8") as f:
                md_content = f.read()
            
            html_content = markdown.markdown(md_content, extensions=['extra', 'codehilite'])
            
            # Wrap in HTML template
            full_html = f"""<!DOCTYPE html>
                <html>
                <head>
                <meta charset='utf-8'>
                <title>{Path(filepath).stem}</title>
                <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                code {{ background: #f4f4f4; padding: 2px 5px; border-radius: 3px; }}
                pre {{ background: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
                </style>
                </head>
                <body>
                {html_content}
                </body>
                </html>"""
            
            output_path = Path(filepath).parent / f"{new_name}.html"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(full_html)
                
        except ImportError:
            raise ImportError("markdown package required for Markdown conversion")
    
    def _markdown_to_docx(self, filepath: str, new_name: str):
        try:
            import markdown
            from docx import Document
            
            with open(filepath, "r", encoding="utf-8") as f:
                md_content = f.read()
            
            doc = Document()
            lines = md_content.split('\n')
            
            for line in lines:
                line = line.rstrip()
                if line.startswith('# '):
                    doc.add_heading(line[2:], level=1)
                elif line.startswith('## '):
                    doc.add_heading(line[3:], level=2)
                elif line.startswith('### '):
                    doc.add_heading(line[4:], level=3)
                elif line.strip():
                    doc.add_paragraph(line)
            
            output_path = Path(filepath).parent / f"{new_name}.docx"
            doc.save(output_path)
            
        except ImportError:
            raise ImportError("markdown package required for Markdown conversion")
    
    def _markdown_to_txt(self, filepath: str, new_name: str):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        import re
        text = re.sub(r'#+\s*', '', content)
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
        
        output_path = Path(filepath).parent / f"{new_name}.txt"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
    
    def _html_to_pdf(self, filepath: str, new_name: str):
        """Convert HTML to PDF."""
        try:
            from fpdf import FPDF
            from bs4 import BeautifulSoup
            
            with open(filepath, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            text = soup.get_text()
            
            pdf = FPDF()
            pdf.set_auto_page_break(True, margin=10)
            pdf.add_font('DejaVu', '', str(self.font_path), uni=True)
            pdf.set_font('DejaVu', '', size=11)
            pdf.add_page()
            
            for line in text.split('\n'):
                if line.strip():
                    pdf.cell(0, 4.8, line.strip(), ln=1, align="L")
            
            output_path = Path(filepath).parent / f"{new_name}.pdf"
            pdf.output(output_path, 'F')
            
        except ImportError:
            raise ImportError("beautifulsoup4 package required for HTML conversion")
    
    def _html_to_txt(self, filepath: str, new_name: str):
        try:
            from bs4 import BeautifulSoup
            
            with open(filepath, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            text = soup.get_text()
            
            output_path = Path(filepath).parent / f"{new_name}.txt"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text)
                
        except ImportError:
            raise ImportError("beautifulsoup4 package required for HTML conversion")
    
    def _html_to_markdown(self, filepath: str, new_name: str):
        try:
            from bs4 import BeautifulSoup
            import html2text
            
            with open(filepath, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            h = html2text.HTML2Text()
            markdown_content = h.handle(html_content)
            
            output_path = Path(filepath).parent / f"{new_name}.md"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
                
        except ImportError:
            raise ImportError("html2text package required for HTML to Markdown conversion")
    
    def merge_pdfs(self, pdf_files: list, output_path: str):
        from pypdf import PdfMerger
        
        merger = PdfMerger()
        for pdf_file in pdf_files:
            merger.append(pdf_file)
        
        merger.write(output_path)
        merger.close()
    
    def split_pdf(self, pdf_path: str, output_folder: str, pages_per_file: int = 1):
        from pypdf import PdfReader, PdfWriter
        
        reader = PdfReader(pdf_path)
        output_folder = Path(output_folder)
        output_folder.mkdir(exist_ok=True)
        
        total_pages = len(reader.pages)
        
        for i in range(0, total_pages, pages_per_file):
            writer = PdfWriter()
            start_page = i
            end_page = min(i + pages_per_file, total_pages)
            
            for j in range(start_page, end_page):
                writer.add_page(reader.pages[j])
            
            output_name = output_folder / f"split_{i//pages_per_file + 1}.pdf"
            with open(output_name, "wb") as f:
                writer.write(f)
