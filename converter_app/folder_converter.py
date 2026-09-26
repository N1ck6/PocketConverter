"""
Handles conversions between JSON, XML, CSV, YAML and other data formats.
Handles folder-based conversions.
"""

import csv
import io
import json
import os
import re
import xml.etree.ElementTree as ET
from datetime import date, datetime
from pathlib import Path
from typing import Callable, Optional

from PIL import Image, ImageOps

from converter_app.utils import get_unique_filename, natural_key, output_path, read_text


def _json_default(value):
    """YAML turns `2024-01-01` into a date object, which json can't serialize on its own."""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


class DataConverter:
    SUPPORTED_EXTENSIONS = {'json', 'xml', 'csv', 'yaml', 'yml'}

    def convert(self, filepath: str, mode: str, new_name: str):
        ext = Path(filepath).suffix[1:].lower()
        readers = {
            'json': self._read_json,
            'csv': self._read_csv,
            'xml': self._read_xml,
            'yaml': self._read_yaml,
            'yml': self._read_yaml,
        }
        reader = readers.get(ext)
        if not reader:
            raise ValueError(f"Source format .{ext} not supported by DataConverter")
        self._route_out(reader(filepath), filepath, mode, new_name)

    # ── Readers ─────────────────────────────────────────────────────────

    @staticmethod
    def _read_json(filepath):
        return json.loads(read_text(filepath))

    @staticmethod
    def _read_csv(filepath):
        text = read_text(filepath)
        try:  # Excel in many locales writes ';'-separated "CSV"
            dialect = csv.Sniffer().sniff(text[:8192], delimiters=',;\t|')
        except csv.Error:
            dialect = csv.excel
        return list(csv.DictReader(io.StringIO(text), dialect=dialect))

    def _read_xml(self, filepath):
        return self._xml_to_dict(ET.parse(filepath).getroot())  # expat honours the BOM / declared encoding

    @staticmethod
    def _read_yaml(filepath):
        import yaml
        return yaml.safe_load(read_text(filepath))

    # ── Writers ─────────────────────────────────────────────────────────

    def _route_out(self, data, filepath, mode: str, new_name: str):
        mode = mode.lower()
        writers = {'json': self._data_to_json, 'csv': self._data_to_csv,
                   'xml': self._data_to_xml, 'yaml': self._data_to_yaml}
        writer = writers.get(mode)
        if not writer:
            raise ValueError(f"Target format .{mode} not supported by DataConverter")
        writer(data, output_path(filepath, new_name, mode))

    @staticmethod
    def _data_to_json(data, out: Path):
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=_json_default)

    @staticmethod
    def _records(data) -> list:
        """
        Find the list of rows in common JSON/XML/YAML shapes:
        [{...}, ...], {...}, or a wrapper like {"users": [{...}, ...]}.
        """
        if isinstance(data, dict):
            list_values = [v for v in data.values() if isinstance(v, list)]
            if len(data) == 1 and list_values and all(isinstance(i, dict) for i in list_values[0]):
                return list_values[0]
            return [data]
        if isinstance(data, list):
            return [item if isinstance(item, dict) else {'value': item} for item in data]
        return [{'value': data}]

    def _data_to_csv(self, data, out: Path):
        rows = self._records(data)
        if not rows:
            raise ValueError("There are no rows to write to CSV")
        keys = list(dict.fromkeys(k for row in rows for k in row))  # first-seen column order

        def cell(value):
            if value is None:
                return ''
            if isinstance(value, (dict, list)):  # keep nested data instead of dropping it
                return json.dumps(value, ensure_ascii=False, default=_json_default)
            if isinstance(value, bool):
                return 'true' if value else 'false'
            return value

        with open(out, 'w', encoding='utf-8-sig', newline='') as f:  # BOM so Excel detects UTF-8
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            for row in rows:
                w.writerow({k: cell(row.get(k)) for k in keys})

    def _data_to_xml(self, data, out: Path):
        root = ET.Element('root')
        self._fill_xml(root, data)
        ET.indent(root)
        ET.ElementTree(root).write(out, encoding='utf-8', xml_declaration=True)

    @staticmethod
    def _data_to_yaml(data, out: Path):
        import yaml
        with open(out, 'w', encoding='utf-8') as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    # ── XML mapping ─────────────────────────────────────────────────────

    _RE_BAD_TAG_CHARS = re.compile(r'[^\w.\-]')

    def _tag(self, key) -> str:
        """Turn any dict key into a valid XML element name."""
        tag = self._RE_BAD_TAG_CHARS.sub('_', str(key)) or '_'
        if not (tag[0].isalpha() or tag[0] == '_') or tag.lower().startswith('xml'):
            tag = '_' + tag
        return tag

    @staticmethod
    def _xml_text(value) -> str:
        if value is None:
            return ''
        if isinstance(value, bool):
            return 'true' if value else 'false'
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        return str(value)

    def _fill_xml(self, element, value):
        """Recursively write value into element. '@key' becomes an attribute and '#text' the text, mirroring _xml_to_dict."""
        if isinstance(value, dict):
            for k, v in value.items():
                k = str(k)
                if k.startswith('@') and not isinstance(v, (dict, list)):
                    element.set(self._tag(k[1:]), self._xml_text(v))
                elif k == '#text':
                    element.text = self._xml_text(v)
                elif isinstance(v, list):
                    for item in v:  # repeated elements, as in the source XML
                        self._fill_xml(ET.SubElement(element, self._tag(k)), item)
                else:
                    self._fill_xml(ET.SubElement(element, self._tag(k)), v)
        elif isinstance(value, list):
            for item in value:
                self._fill_xml(ET.SubElement(element, 'item'), item)
        else:
            element.text = self._xml_text(value)

    def _xml_to_dict(self, element):
        res = {f'@{k}': v for k, v in element.attrib.items()}
        children = list(element)
        if children:
            cd = {}
            for c in children:
                cd_data = self._xml_to_dict(c)
                if c.tag in cd:
                    if not isinstance(cd[c.tag], list): cd[c.tag] = [cd[c.tag]]
                    cd[c.tag].append(cd_data)
                else: cd[c.tag] = cd_data
            res.update(cd)
        if element.text and element.text.strip():
            if res: res['#text'] = element.text.strip()
            else: return element.text.strip()
        return res



class BatchProcessor:
    IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.webp', '.tiff', '.tif', '.heic', '.heif'}
    A4 = (210, 297)  # mm
    MARGIN = 10  # mm
    GIF_FRAME_MS = 100  # 10 fps
    GIF_MAX_SIDE = 800

    def __init__(self, progress_callback: Optional[Callable] = None):
        self.progress_callback = progress_callback

    def convert_folder(self, folder_path: str, mode: str) -> Path:
        if "pdf" in mode: return self._images_to_pdf(folder_path)
        elif "gif" in mode: return self._images_to_gif(folder_path)
        else: raise ValueError(f"Unsupported folder conversion mode: {mode}")

    def _list_images(self, folder) -> list:
        """Images in the folder, case-insensitive (camera files are .JPG), in natural order."""
        files = [p for p in Path(folder).iterdir() if p.is_file() and p.suffix.lower() in self.IMAGE_EXTENSIONS]
        if not files:
            raise ValueError("No images found in this folder")
        if any(p.suffix.lower() in ('.heic', '.heif') for p in files):
            from pillow_heif import register_heif_opener
            register_heif_opener()
        return sorted(files, key=lambda p: natural_key(p.name))

    @staticmethod
    def _output_dir_and_name(folder) -> tuple:
        """Save next to the folder, named after it: Photos/ -> Photos.pdf"""
        folder = Path(os.path.abspath(folder))  # not resolve(): keep the path as the user/Explorer gave it
        if folder.parent == folder:  # drive root: nowhere "next to" it, so save inside
            return folder, 'Combined_images'
        return folder.parent, folder.name

    def _progress(self, i, total, name):
        if self.progress_callback:
            self.progress_callback(i, total, name)

    def _images_to_pdf(self, folder: str) -> Path:
        from fpdf import FPDF

        paths = self._list_images(folder)
        pdf = FPDF(unit='mm', format='A4')
        pdf.set_auto_page_break(False)

        for i, p in enumerate(paths):
            self._progress(i + 1, len(paths), p.name)
            source, (w, h) = self._pdf_image_source(p)

            landscape = w > h  # rotate the page, not the photo
            page_w, page_h = (self.A4[1], self.A4[0]) if landscape else self.A4
            pdf.add_page(orientation='L' if landscape else 'P')
            scale = min((page_w - 2 * self.MARGIN) / w, (page_h - 2 * self.MARGIN) / h)
            iw, ih = w * scale, h * scale
            pdf.image(source, (page_w - iw) / 2, (page_h - ih) / 2, iw, ih)

        out_dir, base = self._output_dir_and_name(folder)
        out = out_dir / f"{get_unique_filename(out_dir, base, 'pdf')}.pdf"
        pdf.output(str(out))
        return out

    @staticmethod
    def _pdf_image_source(path: Path):
        """
        Return (source for fpdf, pixel size). Plain RGB JPEGs are embedded as-is
        (no quality loss, small PDF); anything rotated, transparent or in another
        format is normalized to an in-memory JPEG.
        """
        with Image.open(path) as img:
            size = img.size
            orientation = img.getexif().get(0x0112, 1)
            if img.format == 'JPEG' and img.mode in ('RGB', 'L') and orientation == 1:
                return str(path), size
            img = ImageOps.exif_transpose(img)
            if 'A' in img.getbands() or (img.mode == 'P' and 'transparency' in img.info):
                rgba = img.convert('RGBA')
                flat = Image.new('RGB', rgba.size, (255, 255, 255))
                flat.paste(rgba, mask=rgba.getchannel('A'))
                img = flat
            else:
                img = img.convert('RGB')
            buf = io.BytesIO()
            img.save(buf, 'JPEG', quality=92)
            buf.seek(0)
            return buf, img.size

    def _images_to_gif(self, folder: str) -> Path:
        paths = self._list_images(folder)
        out_dir, base = self._output_dir_and_name(folder)
        out = out_dir / f"{get_unique_filename(out_dir, base, 'gif')}.gif"

        with Image.open(paths[0]) as first:
            first = ImageOps.exif_transpose(first).convert('RGB')
        first.thumbnail((self.GIF_MAX_SIDE, self.GIF_MAX_SIDE), Image.Resampling.LANCZOS)
        size = first.size

        def frames():
            # A generator, so only one photo is in memory at a time
            for i, p in enumerate(paths[1:], start=2):
                self._progress(i, len(paths), p.name)
                with Image.open(p) as img:
                    frame = ImageOps.exif_transpose(img).convert('RGB')
                yield ImageOps.pad(frame, size, color=(0, 0, 0))  # letterbox instead of stretching

        self._progress(1, len(paths), paths[0].name)
        first.save(out, save_all=True, append_images=frames(), duration=self.GIF_FRAME_MS, loop=0, optimize=False)
        return out
