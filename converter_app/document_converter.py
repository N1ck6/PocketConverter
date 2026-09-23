import html as html_lib
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from converter_app.utils import FONT_PATH, output_path, read_text


class DocumentConverter:
    SUPPORTED_EXTENSIONS = {'txt', 'pdf', 'docx', 'md', 'html', 'htm'}

    _UNICODE_FRACTIONS = {
        '½': '1/2', '¼': '1/4', '¾': '3/4',
        '⅓': '1/3', '⅔': '2/3', '⅕': '1/5',
        '⅖': '2/5', '⅗': '3/5', '⅘': '4/5',
        '⅙': '1/6', '⅚': '5/6', '⅛': '1/8',
        '⅜': '3/8', '⅝': '5/8', '⅞': '7/8',
        '⅑': '1/9', '⅒': '1/10', '⅟': '1/',
    }
    _SUPERSCRIPTS = str.maketrans('⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺', '0123456789-+')
    _SUP = '[⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺]'

    # Each alternative either has one capture group (the text to keep) or none (drop the match).
    # Emphasis markers must hug their text and not sit inside words, so that
    # "my_var_name", "2*3*4" and "5 * 3 * 2" survive untouched.
    _RE_MARKDOWN_CLEAN = re.compile(
        r'(?m)^[ \t]*```.*$|'                                  # Code fences
        r'^[ \t]{0,3}(?:[-*_][ \t]*){3,}$|'                    # Horizontal rules
        r'^#{1,6}[ \t]+|'                                      # Headings
        r'(?<!\\)\*\*(.+?)\*\*|'                               # Bold **
        r'(?<![\w\\])__(.+?)__(?!\w)|'                         # Bold __
        r'(?<![\w\\*])\*(?![\s*])(.+?)(?<![\s\\])\*(?![\w*])|'  # Italic *
        r'(?<![\w\\])_(?![\s_])(.+?)(?<!\s)_(?!\w)|'           # Italic _
        r'`([^`\n]+)`|'                                        # Inline code
        r'!\[([^\]]*)\]\([^)]*\)|'                             # Images ![alt](src)
        r'\[([^\]]+)\]\([^)]*\)|'                              # Links [text](url)
        r'^[ \t]*>[ \t]?|'                                     # Quote markers
        r'^([ \t]*)[-*+][ \t]+|'                               # List markers (keep indent)
        r'~~(.+?)~~'                                           # Strikethrough
    )
    _RE_SQRT_N = re.compile(r'\\sqrt\[([^\]]+)\]\{([^}]+)\}')
    _RE_SQRT = re.compile(r'\\sqrt\{([^}]+)\}')
    _RE_FRAC = re.compile(r'\\[dt]?frac\{([^}]+)\}\{([^}]+)\}')
    _RE_BLANK_LINES = re.compile(r'\n{3,}')
    _BLOCK_TAGS = ['p', 'div', 'section', 'article', 'header', 'footer', 'nav', 'aside', 'main',
                   'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'dl', 'dt', 'dd',
                   'table', 'tr', 'blockquote', 'pre', 'hr', 'figure', 'figcaption', 'form']

    def convert(self, filepath: str, mode: str, new_name: str) -> None:
        ext = Path(filepath).suffix[1:].lower()
        mode = mode.lower()

        handlers = {
            'txt': self._convert_from_txt, 'docx': self._convert_from_docx,
            'pdf': self._convert_from_pdf, 'md': self._convert_from_markdown,
            'html': self._convert_from_html, 'htm': self._convert_from_html,
        }
        handler = handlers.get(ext)
        if not handler:
            raise ValueError(f"Source format .{ext} not supported")
        handler(str(filepath), mode, new_name)

    # ── Sources ─────────────────────────────────────────────────────────

    def _convert_from_txt(self, filepath: str, mode: str, new_name: str) -> None:
        # Plain conversions keep the text exactly as written; only the explicit
        # "Clean GPT text" action rewrites markdown and formulas.
        text = read_text(filepath)
        if mode == 'pdf': self._write_pdf(output_path(filepath, new_name, 'pdf'), text)
        elif mode == 'docx': self._write_docx(output_path(filepath, new_name, 'docx'), text)
        elif mode == 'md': self._write_text(output_path(filepath, new_name, 'md'), text)
        elif mode == 'html': self._write_html(output_path(filepath, new_name, 'html'), text, Path(filepath).stem)
        elif mode == 'cleangpt': self._write_text(output_path(filepath, new_name, 'txt'), self.clean_gpt_text(text))
        else: raise ValueError(f"Target format .{mode} not supported")

    def _convert_from_docx(self, filepath: str, mode: str, new_name: str) -> None:
        from docx import Document

        doc = Document(filepath)
        if mode == 'txt': self._write_text(output_path(filepath, new_name, 'txt'), self._docx_to_text(doc, markdown=False))
        elif mode == 'pdf': self._write_pdf(output_path(filepath, new_name, 'pdf'), self._docx_to_text(doc, markdown=False))
        elif mode == 'md': self._write_text(output_path(filepath, new_name, 'md'), self._docx_to_text(doc, markdown=True))
        else: raise ValueError(f"Target format .{mode} not supported")

    def _convert_from_pdf(self, filepath: str, mode: str, new_name: str) -> None:
        if mode == 'docx':
            self._pdf_to_docx(filepath, output_path(filepath, new_name, 'docx'))
            return
        if mode not in ('txt', 'md'):
            raise ValueError(f"Target format .{mode} not supported")

        from pymupdf import open as pdfopen
        with pdfopen(filepath) as doc:
            text = '\n'.join(page.get_text('text') for page in doc)
        if not text.strip():
            raise ValueError("This PDF has no text layer (probably a scan), so there is no text to extract")
        self._write_text(output_path(filepath, new_name, mode), text)

    @staticmethod
    def _pdf_to_docx(filepath: str, out: Path) -> None:
        from pdf2docx import Converter

        cv = Converter(filepath)
        try: cv.convert(str(out), start=0, end=None)
        finally: cv.close()

    def _convert_from_markdown(self, filepath: str, mode: str, new_name: str) -> None:
        import markdown

        md_text = read_text(filepath)
        if mode == 'pdf':
            self._write_pdf(output_path(filepath, new_name, 'pdf'), self._html_to_text(markdown.markdown(md_text, extensions=['extra'])))
        elif mode == 'html':
            body = markdown.markdown(md_text, extensions=['extra', 'codehilite'])
            self._write_text(output_path(filepath, new_name, 'html'), self._wrap_html(body, Path(filepath).stem))
        elif mode == 'docx': self._markdown_to_docx(md_text, output_path(filepath, new_name, 'docx'))
        elif mode == 'txt': self._write_text(output_path(filepath, new_name, 'txt'), self._clean_markdown(md_text))
        else: raise ValueError(f"Target format .{mode} not supported")

    def _markdown_to_docx(self, text: str, out: Path) -> None:
        from docx import Document

        doc = Document()
        in_code = False
        for line in text.split('\n'):
            line = line.rstrip()
            if line.lstrip().startswith('```'):
                in_code = not in_code
                continue
            if in_code:
                doc.add_paragraph(line).style = 'No Spacing'
                continue
            heading = re.match(r'^(#{1,6})\s+(.*)', line)
            bullet = re.match(r'^(\s*)[-*+]\s+(.*)', line)
            if heading:
                doc.add_heading(self._clean_markdown(heading.group(2)), level=len(heading.group(1)))
            elif bullet:
                p = doc.add_paragraph('• ' + self._clean_markdown(bullet.group(2)))
                p.paragraph_format.left_indent = self._indent(bullet.group(1))
            elif line.strip():
                doc.add_paragraph(self._clean_markdown(line))

        self._save_docx(doc, out)

    @staticmethod
    def _indent(ws: str):
        from docx.shared import Cm
        return Cm(0.63 * (1 + len(ws.replace('\t', '    ')) // 2))

    def _convert_from_html(self, filepath: str, mode: str, new_name: str) -> None:
        html = read_text(filepath)
        if mode == 'pdf': self._write_pdf(output_path(filepath, new_name, 'pdf'), self._html_to_text(html))
        elif mode == 'txt': self._write_text(output_path(filepath, new_name, 'txt'), self._html_to_text(html))
        elif mode == 'md':
            import html2text
            self._write_text(output_path(filepath, new_name, 'md'), html2text.html2text(html))
        else: raise ValueError(f"Target format .{mode} not supported")

    # ── Writers ─────────────────────────────────────────────────────────

    @staticmethod
    def _write_text(out: Path, text: str) -> None:
        out.write_text(text, encoding='utf-8')

    @staticmethod
    def _write_pdf(out: Path, text: str) -> None:
        from fpdf import FPDF
        from fpdf.enums import XPos, YPos

        pdf = FPDF()
        pdf.set_title(out.stem)
        pdf.set_margins(15, 15, 15)
        pdf.set_auto_page_break(True, margin=15)
        pdf.add_font('DejaVu', '', str(FONT_PATH))
        pdf.set_font('DejaVu', '', size=11)
        pdf.add_page()

        line_height = 5.5
        for line in text.replace('\r\n', '\n').replace('\t', '    ').split('\n'):
            if line.strip():
                pdf.multi_cell(0, line_height, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            else:
                pdf.ln(line_height)
        pdf.output(str(out))

    def _write_docx(self, out: Path, text: str) -> None:
        from docx import Document

        doc = Document()
        for line in text.replace('\r\n', '\n').split('\n'):
            doc.add_paragraph(line)
        self._save_docx(doc, out)

    @staticmethod
    def _write_html(out: Path, text: str, title: str) -> None:
        out.write_text(
            "<!DOCTYPE html>\n<html>\n<head><meta charset='utf-8'>"
            f"<title>{html_lib.escape(title)}</title></head>\n<body>\n"
            f"<pre style='white-space:pre-wrap;font-family:sans-serif'>{html_lib.escape(text)}</pre>\n"
            "</body>\n</html>",
            encoding='utf-8')

    @staticmethod
    def _docx_to_text(doc, markdown: bool) -> str:
        """Paragraphs and tables in document order (tables used to be dropped)."""
        from docx.table import Table

        lines = []
        for block in doc.iter_inner_content():
            if isinstance(block, Table):
                rows = [[cell.text.strip().replace('\n', ' ') for cell in row.cells] for row in block.rows]
                if not rows:
                    continue
                if markdown:
                    lines.append('| ' + ' | '.join(rows[0]) + ' |')
                    lines.append('|' + ' --- |' * len(rows[0]))
                    lines.extend('| ' + ' | '.join(r) + ' |' for r in rows[1:])
                else:
                    lines.extend('\t'.join(r) for r in rows)
                lines.append('')
                continue
            text = block.text
            style = (block.style.name if block.style is not None else '') or ''
            if markdown and text.strip():
                level = re.match(r'Heading (\d)', style)
                if level:
                    text = '#' * int(level.group(1)) + ' ' + text
                elif style.startswith('List'):
                    text = '- ' + text
                elif style == 'Title':
                    text = '# ' + text
            lines.append(text)
        return '\n'.join(lines)

    def _repackage_clean_docx(self, src_path: Path, dst_path: Path) -> None: # Repackage docx, removing thumbnail/customXml bloat
        import zipfile

        ESSENTIAL_FILES = {
            '[Content_Types].xml',
            '_rels/.rels',
            'word/document.xml',
            'word/_rels/document.xml.rels',
            'word/styles.xml',
            'word/settings.xml',
            'word/webSettings.xml',
            'word/fontTable.xml',
            'word/theme/theme1.xml',
            'docProps/core.xml',
            'docProps/app.xml',
        }

        with zipfile.ZipFile(src_path, 'r') as src_z:
            with zipfile.ZipFile(dst_path, 'w', zipfile.ZIP_DEFLATED) as dst_z:
                for item in src_z.infolist():
                    if item.filename in ESSENTIAL_FILES:
                        data = src_z.read(item.filename)

                        # Fix _rels/.rels: remove thumbnail relationship
                        if item.filename == '_rels/.rels':
                            data = self._remove_thumbnail_rels(data)

                        # Fix [Content_Types].xml: remove customXml/thumbnail entries
                        if item.filename == '[Content_Types].xml':
                            data = self._clean_content_types(data)

                        # Fix word/_rels/document.xml.rels: remove customXml/numbering/stylesWithEffects
                        if item.filename == 'word/_rels/document.xml.rels':
                            data = self._clean_document_rels(data)

                        dst_z.writestr(item, data)

    def _remove_thumbnail_rels(self, rels_xml: bytes) -> bytes:
        root = ET.fromstring(rels_xml)
        ns = {'': 'http://schemas.openxmlformats.org/package/2006/relationships'}
        ET.register_namespace('', 'http://schemas.openxmlformats.org/package/2006/relationships')

        for rel in root.findall('Relationship', ns):
            rel_type = rel.get('Type', '')
            if 'thumbnail' in rel_type.lower():
                root.remove(rel)

        return ET.tostring(root, encoding='UTF-8', xml_declaration=True)

    def _clean_content_types(self, ct_xml: bytes) -> bytes:
        root = ET.fromstring(ct_xml)
        ET.register_namespace('', 'http://schemas.openxmlformats.org/package/2006/content-types')

        for elem in list(root):
            part_name = elem.get('PartName', '')
            ext = elem.get('Extension', '')
            if ('customXml' in part_name or
                'thumbnail' in part_name.lower() or
                'stylesWithEffects' in part_name or
                'numbering' in part_name or
                ext.lower() == 'jpeg'):
                root.remove(elem)

        return ET.tostring(root, encoding='UTF-8', xml_declaration=True)

    def _clean_document_rels(self, rels_xml: bytes) -> bytes:
        root = ET.fromstring(rels_xml)
        ns = {'': 'http://schemas.openxmlformats.org/package/2006/relationships'}
        ET.register_namespace('', 'http://schemas.openxmlformats.org/package/2006/relationships')

        for rel in list(root.findall('Relationship', ns)):
            rel_type = rel.get('Type', '').lower()
            target = rel.get('Target', '').lower()
            if ('customxml' in rel_type or
                'numbering' in rel_type or
                'styleswitheffects' in rel_type or
                'customxml' in target or
                'numbering' in target or
                'styleswitheffects' in target):
                root.remove(rel)

        return ET.tostring(root, encoding='UTF-8', xml_declaration=True)

    def _save_docx(self, doc, out: Path) -> None:
        temp_path = out.parent / f"~{out.stem}.tmp.docx"
        doc.save(str(temp_path))
        try:
            self._repackage_clean_docx(temp_path, out)
        finally:
            temp_path.unlink(missing_ok=True)

    @staticmethod
    def _html_to_text(html: str) -> str:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, 'html.parser')
        for tag in soup(['script', 'style', 'noscript', 'template', 'head']):
            tag.decompose()
        for br in soup('br'):
            br.replace_with('\n')
        for cell in soup(['td', 'th']):
            cell.insert_after(' ')
        # Line breaks only around block elements, so <b>inline</b> text stays on its line
        for tag in soup(DocumentConverter._BLOCK_TAGS):
            tag.insert_before('\n')
            tag.insert_after('\n')
        lines = [re.sub(r'[ \t\xa0]+', ' ', line).strip() for line in soup.get_text().splitlines()]
        text = '\n'.join(lines)
        return DocumentConverter._RE_BLANK_LINES.sub('\n\n', text).strip() + '\n'

    @staticmethod
    def _wrap_html(body: str, title: str) -> str:
        return f"""<!DOCTYPE html><html><head><meta charset='utf-8'><title>{html_lib.escape(title)}</title>
               <style>body{{font-family:sans-serif;max-width:800px;margin:0 auto;padding:20px}}
               code{{background:#f4f4f4;padding:2px 5px;border-radius:3px}}
               pre{{background:#f4f4f4;padding:10px;border-radius:5px;overflow-x:auto}}</style></head>
               <body>{body}</body></html>"""

    # ── GPT text cleaning ───────────────────────────────────────────────

    def clean_gpt_text(self, text: str) -> str:
        """Strip markdown formatting and turn math notation into calculator syntax."""
        cleaned = self._clean_markdown(text)
        cleaned = self._RE_BLANK_LINES.sub('\n\n', cleaned)
        return self._convert_formulas(cleaned).strip()

    def _clean_markdown(self, text: str) -> str:
        """Remove markdown syntax while preserving content."""
        def _replace(match):
            for group in match.groups():
                if group is not None:
                    return group
            return ''
        return self._RE_MARKDOWN_CLEAN.sub(_replace, text)

    def _convert_formulas(self, text: str) -> str:
        sup, sup_to_ascii = self._SUP, self._SUPERSCRIPTS
        for unicode_frac, ascii_frac in self._UNICODE_FRACTIONS.items(): # unicode fractions
            text = text.replace(unicode_frac, ascii_frac)

        def root(index: str) -> str:
            n = index.translate(sup_to_ascii)
            return f'(1/{n})'
        operand = r'(?:\(([^)]+)\)|(\d+(?:\.\d+)?|[A-Za-z]\w*))'
        text = re.sub(rf'({sup}+)√{operand}',  # nth root: ³√(x), ⁴√16
                      lambda m: f'({m.group(2) or m.group(3)})^{root(m.group(1))}', text)
        text = re.sub(rf'√{operand}', lambda m: f'({m.group(1) or m.group(2)})^(1/2)', text) # square root
        text = self._RE_SQRT_N.sub(r'(\2)^(1/\1)', text) # \sqrt[n]{x}
        text = self._RE_SQRT.sub(r'(\1)^(1/2)', text) # \sqrt{x}
        text = self._RE_FRAC.sub(r'(\1)/(\2)', text) # \frac{a}{b}
        text = re.sub(r'\^\{([^}]+)\}', lambda m: f'^{m.group(1)}' if len(m.group(1)) == 1 else f'^({m.group(1)})', text)
        text = re.sub(rf'{sup}+', lambda m: '^' + (m.group(0).translate(sup_to_ascii) if len(m.group(0)) == 1
                                                   else f'({m.group(0).translate(sup_to_ascii)})'), text) # x² -> x^2

        text = (text.replace('×', '*').replace('÷', '/').replace('·', '*') # math symbols
                .replace('−', '-').replace('±', '+/-')
                .replace('≤', '<=').replace('≥', '>=').replace('≠', '!=')
                .replace('π', 'pi').replace('∞', 'inf')
                .replace('\\left(', '(').replace('\\right)', ')')
                .replace('\\left[', '[').replace('\\right]', ']'))
        text = re.sub(r'\\(?:cdot|times)\b\s?', '* ', text)
        text = re.sub(r'\\div\b\s?', '/ ', text)
        text = re.sub(r'\\pm\b', '+/-', text)
        text = re.sub(r'\\pi\b', 'pi', text)
        text = re.sub(r'\\infty\b', 'inf', text)
        text = re.sub(r'\\(sin|cos|tan|cot|log|ln|exp)\b', r'\1', text)
        text = re.sub(r'\\[()\[\]]', '', text) # \( \) \[ \] math delimiters

        return text
