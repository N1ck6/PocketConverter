from converter_app.image_converter import ImageConverter
from converter_app.document_converter import DocumentConverter
from converter_app.animated_converter import AnimatedConverter
from converter_app.folder_converter import DataConverter, BatchProcessor
from converter_app.utils import show_toast, get_unique_filename
from os import devnull
import sys
from pathlib import Path
from typing import Dict


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
        
        
if __name__ == "__main__":
    devnull = open(devnull, 'w')
    sys.stdout, sys.stderr = devnull, devnull
        
    if len(sys.argv) != 3:
        sys.exit("Usage: converter.exe <filepath> <mode>")
    converter = FileConverter()
    converter.convert_file(sys.argv[1], sys.argv[2])
else:
    show_toast("Not main launch", "App is not launched right")