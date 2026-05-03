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
from converter_app.utils import show_toast, get_unique_filename


class DataConverter:
    SUPPORTED_EXTENSIONS = {'json', 'xml', 'csv', 'yaml', 'yml'}

    def convert(self, filepath: str, mode: str, new_name: str):
        ext = Path(filepath).suffix[1:].lower()
        handlers = {
            'json': self._convert_from_json,
            'csv': self._convert_from_csv,
            'xml': self._convert_from_xml,
            'yaml': self._convert_from_yaml,
            'yml': self._convert_from_yaml
        }
        handler = handlers.get(ext)
        if not handler:
            show_toast("Error", f"Source format .{ext} not supported by DataConverter")
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
            show_toast("Error", "PyYAML package required")
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        self._route_out(data, filepath, mode, new_name)

    def _route_out(self, data, filepath: str, mode: str, new_name: str):
        mode = mode.lower()
        if mode == 'json': self._data_to_json(data, filepath, new_name)
        elif mode == 'csv': self._data_to_csv(data, filepath, new_name)
        elif mode == 'xml': self._data_to_xml(data, filepath, new_name)
        elif mode in ('yaml', 'yml'): self._data_to_yaml(data, filepath, new_name)
        else: show_toast("Error", f"Source format .{mode} not supported by DataConverter")

    def _data_to_json(self, data, filepath: str, new_name: str):
        out = Path(filepath).parent / f"{new_name}.json"
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _data_to_csv(self, data, filepath: str, new_name: str):
        out = Path(filepath).parent / f"{new_name}.csv"
        if isinstance(data, dict): data = [data]
        if not data or not isinstance(data[0], dict):
            out.touch(); return
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
        target = [data] if isinstance(data, dict) else data
        for item in target:
            self._dict_to_xml(item, root)
        ET.ElementTree(root).write(out, encoding='utf-8', xml_declaration=True)

    def _dict_to_xml(self, data, dict, parent):
        import xml.etree.ElementTree as ET
        for k, v in data.items():
            k = str(k).replace(' ', '_').replace('-', '_')
            if isinstance(v, dict):
                c = ET.SubElement(parent, k); self._dict_to_xml(v, c)
            elif isinstance(v, list):
                c = ET.SubElement(parent, k)
                for i in v:
                    if isinstance(i, dict): ic = ET.SubElement(c, 'item'); self._dict_to_xml(i, ic)
                    else: ic = ET.SubElement(c, 'item'); ic.text = str(i)
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
    
    def _images_to_pdf(self, folder: str) -> str:
        from fpdf import FPDF
        
        exts = {'png', 'jpg', 'jpeg'}
        paths = sorted(os.path.join(folder, f) for f in os.listdir(folder) if f.rsplit('.', 1)[-1] in exts)
        if not paths: show_toast("Error", "No PNG/JPG images in folder")
        
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
    
    def _images_to_gif(self, folder: str) -> str:
        fp = Path(folder); out_dir = fp.parent
        exts = {'png', 'jpg', 'jpeg', 'bmp', 'webp'}
        files = sorted(f for f in os.listdir(folder) if f.rsplit('.', 1)[-1] in exts)
        if not files: show_toast("Error", "No supported images in folder")
        
        if self.progress_callback: self.progress_callback(0, len(files), "Loading...")
        imgs = [Image.open(fp / f).convert('RGB') for f in files]
        mw, mh = min(i.width for i in imgs), min(i.height for i in imgs)
        imgs = [i.resize((mw, mh)) for i in imgs]
        fn = get_unique_filename(out_dir, 'Combined_images', 'gif')
        out = out_dir / f"{fn}.gif"
        imgs[0].save(out, save_all=True, append_images=imgs[1:], duration=25*len(imgs), loop=0)
        return fn
