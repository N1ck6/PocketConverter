from converter_app.image_converter import ImageConverter
from converter_app.document_converter import DocumentConverter
from converter_app.animated_converter import AnimatedConverter
from converter_app.folder_converter import DataConverter, BatchProcessor
from converter_app.utils import (
    show_toast,
    get_unique_filename,
    parse_filepath,
    ICON_PATH,
    FONT_PATH,
    LOG_FILE_PATH
)
import os
import sys
import traceback
from pathlib import Path


class FileConverter:
    def __init__(self):
        self.image_converter = ImageConverter()
        self.document_converter = DocumentConverter()
        self.animated_converter = AnimatedConverter()
        self.data_converter = DataConverter()
        self.batch_processor = BatchProcessor()

    def convert_file(self, filepath: str, mode: str) -> str:
        if "folder" in mode:
            if not os.path.isdir(filepath):
                show_toast("Folder doesn't exist", "How and Why?", icon=ICON_PATH)
                sys.exit()
            return self.folder_converter.convert_folder(filepath, mode)

        if not os.path.isfile(filepath):
            show_toast("File doesn't exist", "How and Why?", icon=ICON_PATH)
            sys.exit()

        file_info = parse_filepath(filepath)
        ext = file_info['ext']

        if ext == "." + mode:
            show_toast("File with that extension already exists", "How and Why?", icon=ICON_PATH)
            sys.exit()

        new_name = get_unique_filename(Path(file_info['dir']), file_info['name'], mode)

        if ext[1:] in self.image_converter.SUPPORTED_EXTENSIONS:
            self.image_converter.convert(filepath, mode, new_name)
        elif ext[1:] in self.document_converter.SUPPORTED_EXTENSIONS:
            self.document_converter.convert(filepath, mode, new_name)
        elif ext[1:] in self.animated_converter.SUPPORTED_EXTENSIONS:
            self.animated_converter.convert(filepath, mode, new_name)
        else:
            show_toast("Format not allowed right now", "Maybe in next updates...", icon=ICON_PATH)
            sys.exit()

        return new_name