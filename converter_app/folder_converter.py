"""
Handles conversions between JSON, XML, CSV, YAML and other data formats.
Handles folder-based conversions and batch operations with progress tracking.
"""

import json
import csv
from pathlib import Path


class DataConverter:
    SUPPORTED_EXTENSIONS = {'json', 'xml', 'csv', 'yaml', 'yml'}
    
    def convert(self, filepath: str, mode: str, new_name: str):
        ext = Path(filepath).suffix[1:]
        
        if ext == "json":
            self._convert_from_json(filepath, mode, new_name)
        elif ext == "csv":
            self._convert_from_csv(filepath, mode, new_name)
        elif ext == "xml":
            self._convert_from_xml(filepath, mode, new_name)
        elif ext in ['yaml', 'yml']:
            self._convert_from_yaml(filepath, mode, new_name)
    
    def _convert_from_json(self, filepath: str, mode: str, new_name: str):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if mode == "csv":
            self._data_to_csv(data, filepath, new_name)
        elif mode == "xml":
            self._data_to_xml(data, filepath, new_name)
        elif mode in ['yaml', 'yml']:
            self._data_to_yaml(data, filepath, new_name)
    
    def _convert_from_csv(self, filepath: str, mode: str, new_name: str):
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            data = list(reader)
        
        if mode == "json":
            self._data_to_json(data, filepath, new_name)
        elif mode == "xml":
            self._data_to_xml(data, filepath, new_name)
        elif mode in ['yaml', 'yml']:
            self._data_to_yaml(data, filepath, new_name)
    
    def _convert_from_xml(self, filepath: str, mode: str, new_name: str):
        try:
            import xml.etree.ElementTree as ET
            
            tree = ET.parse(filepath)
            root = tree.getroot()
            data = self._xml_to_dict(root)
            
            if mode == "json":
                self._data_to_json(data, filepath, new_name)
            elif mode == "csv":
                self._data_to_csv(data, filepath, new_name)
            elif mode in ['yaml', 'yml']:
                self._data_to_yaml(data, filepath, new_name)
                
        except ImportError:
            raise ImportError("XML parsing requires xml library")
    
    def _convert_from_yaml(self, filepath: str, mode: str, new_name: str):
        try:
            import yaml
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if mode == "json":
                self._data_to_json(data, filepath, new_name)
            elif mode == "csv":
                self._data_to_csv(data, filepath, new_name)
            elif mode == "xml":
                self._data_to_xml(data, filepath, new_name)
                
        except ImportError:
            raise ImportError("PyYAML package required for YAML conversion")
    
    def _data_to_json(self, data, filepath: str, new_name: str):
        output_path = Path(filepath).parent / f"{new_name}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _data_to_csv(self, data, filepath: str, new_name: str):
        output_path = Path(filepath).parent / f"{new_name}.csv"
        if isinstance(data, dict):
            data = [data]
        
        if not data:
            output_path.touch()
            return
        
        fieldnames = set()
        for item in data:
            if isinstance(item, dict):
                fieldnames.update(item.keys())
        
        if not fieldnames:
            output_path.touch()
            return
        
        fieldnames = sorted(fieldnames)
        
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for item in data:
                if isinstance(item, dict):
                    writer.writerow({k: item.get(k, '') for k in fieldnames})
    
    def _data_to_xml(self, data, filepath: str, new_name: str):
        try:
            import xml.etree.ElementTree as ET
            
            output_path = Path(filepath).parent / f"{new_name}.xml"
            
            root = ET.Element('root')
            
            if isinstance(data, list):
                for item in data:
                    self._dict_to_xml(item, root)
            elif isinstance(data, dict):
                self._dict_to_xml(data, root)
            
            tree = ET.ElementTree(root)
            tree.write(output_path, encoding='utf-8', xml_declaration=True)
            
        except ImportError:
            raise ImportError("XML writing requires Python standard library")
    
    def _dict_to_xml(self, data: dict, parent: 'ET.Element'):
        import xml.etree.ElementTree as ET
        
        for key, value in data.items():
            # Clean key for XML element name
            key = str(key).replace(' ', '_').replace('-', '_')
            
            if isinstance(value, dict):
                child = ET.SubElement(parent, key)
                self._dict_to_xml(value, child)
            elif isinstance(value, list):
                child = ET.SubElement(parent, key)
                for item in value:
                    if isinstance(item, dict):
                        item_elem = ET.SubElement(child, 'item')
                        self._dict_to_xml(item, item_elem)
                    else:
                        item_elem = ET.SubElement(child, 'item')
                        item_elem.text = str(item)
            else:
                child = ET.SubElement(parent, key)
                child.text = str(value)
    
    def _data_to_yaml(self, data, filepath: str, new_name: str):
        try:
            import yaml
            
            output_path = Path(filepath).parent / f"{new_name}.yaml"
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
                
        except ImportError:
            raise ImportError("PyYAML package required for YAML conversion")
    
    def _xml_to_dict(self, element: 'ET.Element') -> dict:
        result = {}
        
        for key, value in element.attrib.items():
            result[f'@{key}'] = value
        
        children = list(element)
        if children:
            child_dict = {}
            for child in children:
                child_data = self._xml_to_dict(child)
                if child.tag in child_dict:
                    if not isinstance(child_dict[child.tag], list):
                        child_dict[child.tag] = [child_dict[child.tag]]
                    child_dict[child.tag].append(child_data)
                else:
                    child_dict[child.tag] = child_data
            
            result.update(child_dict)
        
        if element.text and element.text.strip():
            if result:
                result['#text'] = element.text.strip()
            else:
                return element.text.strip()
        
        return result


import os
import sys
from typing import Callable, Optional
from PIL import Image
from converter_app.utils import ICON_PATH, show_toast, get_unique_filename

class BatchProcessor:
    def __init__(self, progress_callback: Optional[Callable] = None):
        self.progress_callback = progress_callback
    
    def convert_folder(self, folder_path: str, mode: str) -> str:
        if "pdf" in mode:
            return self._images_to_pdf(folder_path)
        elif "gif" in mode:
            return self._images_to_gif(folder_path)
    
    def _images_to_pdf(self, folder: str) -> str:
        from fpdf import FPDF
        
        image_extensions = {'png', 'jpg', 'jpeg'}
        image_paths = [
            os.path.join(folder, f) 
            for f in sorted(os.listdir(folder))
            if f.rsplit('.', 1)[-1] in image_extensions
        ]
        
        if not image_paths:
            show_toast("Folder doesn't have images", "Available format: png, jpg, jpeg", icon=ICON_PATH)
            sys.exit()
        
        pdf = FPDF()
        a4_w, a4_h = 210, 297
        
        for i, image_path in enumerate(image_paths):
            if self.progress_callback:
                self.progress_callback(i + 1, len(image_paths), os.path.basename(image_path))
            
            pdf.add_page()
            width, height = Image.open(image_path).size
            scale = min(a4_w / width, a4_h / height)
            if scale < 1:
                width *= scale
                height *= scale
            pdf.image(image_path, (a4_w - width) / 2, (a4_h - height) / 2, width, height)
        
        folder_path = Path(folder)
        output_dir = folder_path.parent
        filename = get_unique_filename(output_dir, 'Combined_images', 'pdf')
        pdf.output(output_dir / f"{filename}.pdf")
        return filename
    
    def _images_to_gif(self, folder: str) -> str:
        folder_path = Path(folder)
        output_dir = folder_path.parent
        
        filename = get_unique_filename(output_dir, 'Combined_images', 'gif')
        output_path = output_dir / f"{filename}.gif"
        
        image_extensions = {'png', 'jpg', 'jpeg', 'bmp', 'webp'}
        image_files = [
            f for f in os.listdir(folder) 
            if f.rsplit('.', 1)[-1] in image_extensions
        ]
        
        if not image_files:
            show_toast("Folder doesn't have images", "Available format: png, jpg, jpeg, bmp, webp", icon=ICON_PATH)
            sys.exit()
        
        if self.progress_callback:
            self.progress_callback(0, len(image_files), "Loading images...")
        
        images = [Image.open(folder_path / f).convert('RGB') for f in sorted(image_files)]
        
        min_width = min(img.width for img in images)
        min_height = min(img.height for img in images)
        images = [img.resize((min_width, min_height)) for img in images]
        
        images[0].save(
            output_path, 
            save_all=True, 
            append_images=images[1:], 
            duration=25 * len(images), 
            loop=0
        )
        return filename
    
    def batch_convert_files(self, file_paths: list, target_format: str, 
                           output_folder: str = None) -> list:
        from converter_app.image_converter import ImageConverter
        from converter_app.document_converter import DocumentConverter
        
        results = []
        image_converter = ImageConverter()
        document_converter = DocumentConverter()
        
        total = len(file_paths)
        
        for i, filepath in enumerate(file_paths):
            if self.progress_callback:
                self.progress_callback(i + 1, total, os.path.basename(filepath))
            
            try:
                path = Path(filepath)
                ext = path.suffix[1:].lower()
                
                out_dir = Path(output_folder) if output_folder else path.parent
                out_dir.mkdir(exist_ok=True)
                
                if ext in ImageConverter.SUPPORTED_EXTENSIONS:
                    image_converter.convert(filepath, target_format, 
                                          out_dir / path.stem)
                elif ext in DocumentConverter.SUPPORTED_EXTENSIONS:
                    document_converter.convert(filepath, target_format,
                                              out_dir / path.stem)
                
                output_path = out_dir / f"{path.stem}.{target_format}"
                results.append(str(output_path))
                
            except Exception as e:
                print(f"Error converting {filepath}: {e}", file=sys.stderr)
                continue
        
        return results
