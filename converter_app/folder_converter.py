"""
Handles conversions between JSON, XML, CSV, YAML and other data formats.
Handles folder-based conversions.
"""

import json
import csv
from pathlib import Path
import os
from typing import Callable, Optional
from PIL import Image
from converter_app.utils import get_unique_filename


class DataConverter:
    SUPPORTED_EXTENSIONS = {'json', 'xml', 'csv', 'yaml'}

    def convert(self, filepath: str, mode: str, new_name: str):
        ext = Path(filepath).suffix[1:].lower()
        handlers = {
            'json': self._convert_from_json,
            'csv': self._convert_from_csv,
            'xml': self._convert_from_xml,
            'yaml': self._convert_from_yaml,
        }
        handler = handlers.get(ext)
        if not handler:
            raise ValueError(f"Source format .{ext} not supported by DataConverter")
        handler(filepath, mode, new_name)

    def _convert_from_json(self, filepath: str, mode: str, new_name: str):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self._route_out(data, filepath, mode, new_name)

    def _convert_from_csv(self, filepath: str, mode: str, new_name: str):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = list(csv.DictReader(f))
        self._route_out(data, filepath, mode, new_name)

    def _convert_from_xml(self, filepath: str, mode: str, new_name: str):
        import xml.etree.ElementTree as ET
        tree = ET.parse(filepath)
        data = self._xml_to_dict(tree.getroot())
        self._route_out(data, filepath, mode, new_name)

    def _convert_from_yaml(self, filepath: str, mode: str, new_name: str):
        try:
            import yaml
        except ImportError:
            raise ImportError("PyYAML package is required for YAML conversion. Install it with 'pip install pyyaml'.")
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        self._route_out(data, filepath, mode, new_name)

    def _route_out(self, data, filepath: str, mode: str, new_name: str):
        mode = mode.lower()
        if mode == 'json': self._data_to_json(data, filepath, new_name)
        elif mode == 'csv': self._data_to_csv(data, filepath, new_name)
        elif mode == 'xml': self._data_to_xml(data, filepath, new_name)
        elif mode == 'yaml': self._data_to_yaml(data, filepath, new_name)
        else: raise ValueError(f"Target format .{mode} not supported by DataConverter")

    def _data_to_json(self, data, filepath: str, new_name: str):
        out = Path(filepath).parent / f"{new_name}.json"
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _data_to_csv(self, data, filepath: str, new_name: str):
        out = Path(filepath).parent / f"{new_name}.csv"
        if isinstance(data, dict): data = [data]
        if not data or not isinstance(data[0], dict):
            raise ValueError("Data must be a list of objects to convert to CSV")
        keys = sorted({k for item in data for k in item.keys() if isinstance(item, dict)})
        with open(out, 'w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            for item in data:
                w.writerow({k: str(item.get(k, '')) if not isinstance(item.get(k), (dict, list)) else '' for k in keys})

    def _data_to_xml(self, data, filepath: str, new_name: str):
        import xml.etree.ElementTree as ET
        out = Path(filepath).parent / f"{new_name}.xml"
        root = ET.Element('root')

        if isinstance(data, dict):
            self._dict_to_xml(data, root)
        elif isinstance(data, list):
            for item in data:
                item_el = ET.SubElement(root, 'item')
                if isinstance(item, dict):
                    self._dict_to_xml(item, item_el)
                else:
                    item_el.text = str(item)
        else:
            root.text = str(data)

        tree = ET.ElementTree(root)
        with open(out, 'wb') as f:
            tree.write(f, encoding='utf-8', xml_declaration=True)

    def _data_to_yaml(self, data, filepath: str, new_name: str):
        try:
            import yaml
        except ImportError:
            raise ImportError("PyYAML package is required for YAML conversion. Install it with 'pip install pyyaml'.")
        out = Path(filepath).parent / f"{new_name}.yaml"
        with open(out, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    def _dict_to_xml(self, data, parent):
        """Recursively convert dict/list data to XML elements under parent."""
        import xml.etree.ElementTree as ET
        for k, v in data.items():
            k = str(k).replace(' ', '_').replace('-', '_')
            if isinstance(v, dict):
                c = ET.SubElement(parent, k)
                self._dict_to_xml(v, c)
            elif isinstance(v, list):
                c = ET.SubElement(parent, k)
                for i in v:
                    if isinstance(i, dict):
                        ic = ET.SubElement(c, 'item')
                        self._dict_to_xml(i, ic)
                    else:
                        ic = ET.SubElement(c, 'item')
                        ic.text = str(i)
            else:
                ET.SubElement(parent, k).text = str(v)

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
    def __init__(self, progress_callback: Optional[Callable] = None):
        self.progress_callback = progress_callback

    def convert_folder(self, folder_path: str, mode: str) -> str:
        if "pdf" in mode: return self._images_to_pdf(folder_path)
        elif "gif" in mode: return self._images_to_gif(folder_path)
        else: raise ValueError(f"Unsupported folder conversion mode: {mode}")

    def _images_to_pdf(self, folder: str) -> str:
        from fpdf import FPDF

        exts = {'png', 'jpg', 'jpeg'}
        paths = sorted(os.path.join(folder, f) for f in os.listdir(folder) if f.rsplit('.', 1)[-1] in exts)
        if not paths:
            raise ValueError("No PNG/JPG images in folder")
        
        pdf = FPDF()
        a4_w, a4_h = 210, 297
        
        for i, p in enumerate(paths):
            if self.progress_callback: self.progress_callback(i+1, len(paths), os.path.basename(p))
            
            pdf.add_page()
            w, h = Image.open(p).size
            s = min(a4_w/w, a4_h/h)
            if s < 1: w, h = w*s, h*s
            pdf.image(p, (a4_w-w)/2, (a4_h-h)/2, w, h)
        out_dir = Path(folder).parent
        fn = get_unique_filename(out_dir, 'Combined_images', 'pdf')
        pdf.output(out_dir / f"{fn}.pdf")
        return fn
    
    def _images_to_gif(self, folder: str) -> None:
        fp = Path(folder); out_dir = fp.parent
        exts = {'png', 'jpg', 'jpeg', 'bmp', 'webp'}
        files = sorted(f for f in os.listdir(folder) if f.rsplit('.', 1)[-1] in exts)
        if not files:
            raise ValueError("No supported images in folder")

        import imageio.v2 as imageio
        if self.progress_callback: self.progress_callback(0, len(files), "Loading...")

        first_img = Image.open(fp / files[0]).convert('RGB')
        mw, mh = first_img.size
        fn = get_unique_filename(out_dir, 'Combined_images', 'gif')
        out = out_dir / f"{fn}.gif"

        with imageio.get_writer(out, mode='I', duration=0.1, loop=0) as writer:  # ~10 fps, fixed regardless of frame count
            for i, f in enumerate(files):
                img = Image.open(fp / f).convert('RGB').resize((mw, mh))
                writer.append_data(img)
                img.close()
                if self.progress_callback: self.progress_callback(i+1, len(files), f)
        return fn