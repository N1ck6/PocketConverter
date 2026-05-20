from converter_app.image_converter import ImageConverter
from converter_app.document_converter import DocumentConverter
from converter_app.animated_converter import AnimatedConverter
from converter_app.folder_converter import DataConverter, BatchProcessor
from converter_app.utils import show_toast, get_unique_filename
from os import devnull
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging


class FileConverter:
    def __init__(self):
        self.image_converter = ImageConverter()
        self.document_converter = DocumentConverter()
        self.animated_converter = AnimatedConverter()
        self.data_converter = DataConverter()
        self.batch_processor = BatchProcessor()
        
        self._routers: Dict[str, object] = {}
        for conv in (self.image_converter, self.document_converter, 
                     self.animated_converter, self.data_converter):
            for ext in getattr(conv, "SUPPORTED_EXTENSIONS", []):
                self._routers[ext.lower()] = conv

    def convert_file(self, filepath: str, mode: str):
        path = Path(filepath)
        
        if "folder" in mode:
            if not path.is_dir():
                show_toast("Folder doesn't exist", "How and Why?")
            self.batch_processor.convert_folder(filepath, mode)
            sys.exit()

        if not path.is_file():
            show_toast("File doesn't exist", "How and Why?")

        ext, target = path.suffix.lower(), f".{mode.lower()}"
        key = ext[1:]

        if ext == target:
            show_toast("File with that extension already exists", "How and Why?")
        if key not in self._routers:
            show_toast("Format not allowed right now", "Maybe in next updates...")

        new_name = get_unique_filename(path.parent, path.stem, mode)
        self._routers[key].convert(str(path), mode, new_name)
    
    def convert_multiple_files(self, filepaths: List[str], mode: str) -> List[Tuple[bool, str]]:
        first_ext = Path(filepaths[0]).suffix.lower()
        validated_files = []

        for filepath in filepaths:
            path = Path(filepath)
            if not path.exists() or path.suffix.lower() != first_ext \
                or path.suffix.lower() == target or key not in self._routers: continue

            key = path.suffix.lower()[1:]
            target = f".{mode.lower()}"
            validated_files.append(filepath)

        if not validated_files: return [(False, "No valid files to convert")]

        results = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_file = {
                executor.submit(self.convert_file, filepath, mode): filepath
                for filepath in validated_files
            }
            
            for future in as_completed(future_to_file):
                filepath = future_to_file[future]
                try:
                    success, message = future.result()
                    results.append((success, message))

                except Exception as e:
                    error_msg = f"Unexpected error for {filepath}: {str(e)}"
                    results.append((False, error_msg))

        return results
        
        
if __name__ == "__main__":
    devnull = open(devnull, 'w')
    sys.stdout, sys.stderr = devnull, devnull   # Disable console window popping up
        
    if len(sys.argv) < 3: sys.exit("Usage: converter.exe <filepath> <mode>")
    
    mode = sys.argv[-1]
    filepaths = sys.argv[1:-1]

    if not filepaths: sys.exit("Error: No input files provided")

    converter = FileConverter()

    if len(filepaths) == 1:
        converter.convert_file(filepaths[0], mode)
    else:
        results = converter.convert_multiple_files(filepaths, mode)

        success_count = sum(1 for success, _ in results if success)
        total_count = len(results)
        show_toast(f"Conversion into {mode}", f"Converted {success_count}/{total_count} files")
    
else:
    show_toast("Not main launch", "App is not launched right")