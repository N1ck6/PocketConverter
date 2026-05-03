import re
from pathlib import Path
from converter_app.utils import show_toast, FONT_PATH

class DocumentConverter:
    SUPPORTED_EXTENSIONS = {'txt', 'pdf', 'docx', 'md', 'markdown', 'html', 'rtf', 'odt', 'epub'}

    _RE_MARKDOWN_CLEAN = re.compile(r'(?m)^(#+\s*|[*_`~]|> |\s+-\s+)')
    _RE_MATH_SQRT = re.compile(r'\\sqrt(?:\[(\d+)\])?[\(\{]([^)\}]+)[\)\}]')
    _RE_MATH_FRAC = re.compile(r'\\frac\{([^}]+)\}\{([^}]+)\}')
    _RE_HTML_TAGS = re.compile(r'<[^>]+>')
    _RE_WHITESPACE = re.compile(r'\n{3,}')

    def convert(self, filepath: str, mode: str, new_name: str) -> None:
        ext = Path(filepath).suffix[1:].lower()
        mode = mode.lower()

        handlers = {
            'txt': self._convert_from_txt, 'docx': self._convert_from_docx,
            'pdf': self._convert_from_pdf, 'md': self._convert_from_markdown,
            'markdown': self._convert_from_markdown, 'html': self._convert_from_html
        }
        handler = handlers.get(ext)
        if not handler: show_toast("Error", f"Source format .{ext} not supported")
        handler(filepath, mode, new_name)

    def _convert_from_txt(self, filepath: str, mode: str, new_name: str) -> None:
        processed = self._process_txt_with_gpt_support(filepath)
        out = Path(filepath).parent / f"{new_name}"
        if mode == 'pdf': self._write_pdf(out, processed)
        elif mode == 'docx': self._write_docx(out, processed)
        elif mode in ('md', 'markdown'): (out.with_suffix('.md')).write_text(processed, encoding='utf-8')
        elif mode == 'html': self._write_html(out, processed)
        else: show_toast("Error", f"Target format .{mode} not supported")

    def _convert_from_docx(self, filepath: str, mode: str, new_name: str) -> None:
        from docx import Document
        
        doc = Document(filepath)
        text = '\n'.join(p.text for p in doc.paragraphs)
        out = Path(filepath).parent / new_name
        
        if mode == 'txt': out.with_suffix('.txt').write_text(text, encoding='utf-8')
        elif mode == 'pdf': self._write_pdf(out, text)
        elif mode in ('md', 'markdown'): out.with_suffix('.md').write_text(text, encoding='utf-8')
        else: show_toast("Error", f"Target format .{mode} not supported")

    def _convert_from_pdf(self, filepath: str, mode: str, new_name: str) -> None:
        from pymupdf import open as pdfopen

        doc = pdfopen(filepath)
        text = ''.join(page.get_text('text') for page in doc); doc.close()
        out = Path(filepath).parent / new_name
        
        if mode == 'txt': out.with_suffix('.txt').write_text(text, encoding='utf-8')
        elif mode == 'docx': self._pdf_to_docx(filepath, new_name)
        elif mode == 'md': out.with_suffix('.md').write_text(text, encoding='utf-8')
        else: show_toast("Error", f"Target format .{mode} not supported")

    def _pdf_to_docx(self, filepath: str, new_name: str) -> None:
        try:
            from pdf2docx import Converter
        except ImportError: raise DependencyError("pdf2docx required")
        
        out = Path(filepath).parent / f"{new_name}.docx"
        cv = Converter(filepath)
        try: cv.convert(str(out), start=0, end=None)
        finally: cv.close()

    def _convert_from_markdown(self, filepath: str, mode: str, new_name: str) -> None:
        import markdown

        md_text = Path(filepath).read_text(encoding='utf-8')
        out = Path(filepath).parent / new_name
        
        if mode == 'pdf': self._write_pdf(out, self._html_to_text(markdown.markdown(md_text)))
        elif mode == 'html': (out.with_suffix('.html')).write_text(self._wrap_html(markdown.markdown(md_text, extensions=['extra', 'codehilite']), Path(filepath).stem), encoding='utf-8')
        elif mode == 'docx': self._markdown_to_docx(md_text, out)
        elif mode == 'txt': out.with_suffix('.txt').write_text(self._RE_MARKDOWN_CLEAN.sub('', md_text), encoding='utf-8')
        else: show_toast("Error", f"Target format .{mode} not supported")

    def _markdown_to_docx(self, text: str, out: Path) -> None:
        from docx import Document

        doc = Document()
        for line in text.split('\n'):
            line = line.rstrip()
            if line.startswith('# '): doc.add_heading(line[2:], level=1)
            elif line.startswith('## '): doc.add_heading(line[3:], level=2)
            elif line.startswith('### '): doc.add_heading(line[4:], level=3)
            elif line.strip(): doc.add_paragraph(line)
        doc.save(str(out.with_suffix('.docx')))

    def _convert_from_html(self, filepath: str, mode: str, new_name: str) -> None:
        from bs4 import BeautifulSoup

        html = Path(filepath).read_text(encoding='utf-8')
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text(separator='\n')
        out = Path(filepath).parent / f"{new_name}"

        if mode == 'pdf': self._write_pdf(out, text)
        elif mode == 'txt': out.with_suffix('.txt').write_text(text, encoding='utf-8')
        elif mode == 'md': import html2text; out.with_suffix('.md').write_text(html2text.html2text(html), encoding='utf-8')
        else: show_toast("Error", f"Target format .{mode} not supported")

    def _write_pdf(self, out: Path, text: str) -> None:
        from fpdf import FPDF; from textwrap import wrap

        pdf = FPDF()
        pdf.set_auto_page_break(True, margin=10)
        pdf.add_font('DejaVu', '', str(FONT_PATH), uni=True)
        pdf.set_font('DejaVu', '', size=11)
        pdf.add_page()

        for line in text.split('\n'):
            for wrapped in wrap(line, 90) or ['']: pdf.cell(0, 4.8, wrapped, ln=1)
        pdf.output(str(out.with_suffix('.pdf')), 'F')

    def _write_docx(self, out: Path, text: str) -> None:
        from docx import Document

        doc = Document()
        doc.add_paragraph(text)
        doc.save(str(out.with_suffix('.docx')))

    def _write_html(self, out: Path, text: str) -> None:
        (out.with_suffix('.html')).write_text(f"<!DOCTYPE html><html><head><meta charset='utf-8'></head><body><pre>{text}</pre></body></html>",
            encoding='utf-8')

    def _html_to_text(self, html: str) -> str:
        return self._RE_HTML_TAGS.sub('\n', html).replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')

    def _wrap_html(self, body: str, title: str) -> str:
        return f"""<!DOCTYPE html><html><head><meta charset='utf-8'><title>{title}</title>
               <style>body{{font-family:sans-serif;max-width:800px;margin:0 auto;padding:20px}}
               code{{background:#f4f4f4;padding:2px 5px;border-radius:3px}}
               pre{{background:#f4f4f4;padding:10px;border-radius:5px;overflow-x:auto}}</style></head>
               <body>{body}</body></html>"""

    def _process_txt_with_gpt_support(self, filepath: str) -> str:
        content = Path(filepath).read_text(encoding='utf-8')
        cleaned = self._RE_MARKDOWN_CLEAN.sub('', content)
        cleaned = self._RE_WHITESPACE.sub('\n\n', cleaned)
        return self._convert_formulas(cleaned).strip()

    def _convert_formulas(self, text: str) -> str:
        text = self._RE_MATH_SQRT.sub(lambda m: f"({m.group(2)})^(1/{m.group(1) or 2})", text)
        text = self._RE_MATH_FRAC.sub(r'(\1)/(\2)', text)
        text = text.replace('×', '*').replace('÷', '/').replace('−', '-').replace('±', '+/-')
        text = text.replace('π', 'pi').replace('∞', 'inf')
        return re.sub(r'\\(sin|cos|tan|log|ln|exp)', r'\1', text)

    @staticmethod
    def merge_pdfs(pdf_files: list[str], output_path: str) -> None:
        from pypdf import PdfMerger
        
        merger = PdfMerger()
        for f in pdf_files: merger.append(f)
        merger.write(output_path); merger.close()

    @staticmethod
    def split_pdf(pdf_path: str, output_folder: str, pages_per_file: int = 1) -> None:
        from pypdf import PdfReader, PdfWriter

        reader = PdfReader(pdf_path)
        out_dir = Path(output_folder); out_dir.mkdir(exist_ok=True)
        total = len(reader.pages)

        for i in range(0, total, pages_per_file):
            writer = PdfWriter()
            for j in range(i, min(i + pages_per_file, total)): writer.add_page(reader.pages[j])
            with open(out_dir / f"split_{i//pages_per_file + 1}.pdf", "wb") as f: writer.write(f)