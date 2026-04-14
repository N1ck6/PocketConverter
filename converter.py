"""
Pocket Converter Application
A modular file conversion tool supporting images, documents, audio, and video.
"""

from converter_app.image_converter import ImageConverter
from converter_app.document_converter import DocumentConverter
from converter_app.animated_converter import AnimatedConverter
from converter_app.folder_converter import FolderConverter
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
    """Main file conversion dispatcher."""
    
    def __init__(self):
        self.image_converter = ImageConverter()
        self.document_converter = DocumentConverter()
        self.animated_converter = AnimatedConverter()
        self.folder_converter = FolderConverter()
    
    def convert_file(self, filepath: str, mode: str) -> str:
        """
        Main conversion dispatcher.
        
        Args:
            filepath: Path to the file or folder to convert
            mode: Target format/mode
            
        Returns:
            Name of the converted file
        """
        # Handle folder conversions
        if "folder" in mode:
            if not os.path.isdir(filepath):
                show_toast("Folder doesn't exist", "How and Why?", icon=ICON_PATH)
                sys.exit()
            return self.folder_converter.convert_folder(filepath, mode)
        
        # Validate file exists
        if not os.path.isfile(filepath):
            show_toast("File doesn't exist", "How and Why?", icon=ICON_PATH)
            sys.exit()
        
        # Parse file information
        file_info = parse_filepath(filepath)
        ext = file_info['ext']
        
        # Check if already correct format
        if ext == "." + mode:
            show_toast("File with that extension already exists", "How and Why?", icon=ICON_PATH)
            sys.exit()
        
        # Generate output filename
        new_name = get_unique_filename(Path(file_info['dir']), file_info['name'], mode)
        
        # Route to appropriate converter
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


if __name__ == "__main__":
    try:
        devnull = open(os.devnull, 'w')
        sys.stdout, sys.stderr = devnull, devnull
        
        if len(sys.argv) == 3:
            file_path, mode = sys.argv[1], sys.argv[2]
            logs_input = f"Input! File: {file_path}, Mode: {mode}\n"
            
            # Parse file path if not a folder conversion
            if "folder" not in mode:
                file_info = parse_filepath(file_path)
                file = file_info['full']
            else:
                file = file_path
            
            converter = FileConverter()
            name = converter.convert_file(file, mode)
            
            # Extract extension for notification
            if "folder" in mode:
                mode = mode[-3:]
            
            # Show completion notification
            if mode == "pngs":
                show_toast("Done!", "Saved as extracted gif folder", icon=ICON_PATH, group='done')
            else:
                show_toast("Done!", f"Saved as {name}.{mode}", icon=ICON_PATH, group='done')
        else:
            show_toast("Hi!", "I need to be used through context menu ;)", icon=ICON_PATH, group='done')
            
    except Exception as e:
        # Log errors to file
        if os.path.isfile(LOG_FILE_PATH):
            with open(LOG_FILE_PATH, 'a') as log_file:
                log_file.write(f"Error! Input: {logs_input} File: {file}, Mode: {mode}\n")
                log_file.write("Error Output:\n")
                log_file.write(traceback.format_exc())
                log_file.write('---------------------------------------------------------------------\n')
        
        show_toast("Conversion error", 
                  r"Check log file in C:\Program Files\PocketConverter for more information", 
                  icon=ICON_PATH)
