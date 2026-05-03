"""
Utility functions and constants.
"""

import sys
import shutil
from pathlib import Path
from win11toast import toast

SUPPORTED_EXTENSIONS = [
    'mp4', 'gif', 'txt', 'pdf', 'docx', 'jpg', 'jpeg', 'png', 
    'webp', 'bmp', 'tiff', 'ico', 'heic', 'svg', 'md', 'markdown',
    'json', 'xml', 'csv', 'mp3', 'wav', 'flac', 'aac', 'ogg'
]
LOG_FILE_PATH = "C:\\Program Files\\PocketConverter\\PocketConverter_log.txt"

DEFAULT_IMAGE_QUALITY = 95
DEFAULT_AUDIO_BITRATE = '192k'
DEFAULT_VIDEO_BITRATE = '2000k'

if getattr(sys, 'frozen', False):
    BASE_PATH = sys._MEIPASS
else:
    BASE_PATH = Path(__file__).parent.parent

ICON_PATH = BASE_PATH / 'logo.ico'
FONT_PATH = BASE_PATH / 'DejaVuSansCondensed.ttf'


def check_ffmpeg():
    return shutil.which('ffmpeg') is not None


def get_ffmpeg_help():
    return "FFmpeg is required for audio/video edit. Download from: https://ffmpeg.org/download.html"


def show_toast(title: str, message: str):
    icon=ICON_PATH
    toast(title, message, icon=icon)
    sys.exit()


def get_unique_filename(directory: Path, basename: str, extension: str) -> str:
    ext = extension.strip().lstrip('.')
    filepath = directory / f"{basename}.{ext}"

    if ext != 'pngs' and filepath.exists():
        for i in range(1, 101):
            candidate = f"{basename}({i})"
            filepath = directory / f"{candidate}.{ext}"
            if not filepath.exists(): return candidate
    return basename

def log_error(ext, target):
    import os, traceback
    if os.path.isfile(LOG_FILE_PATH) and logs_input and ext and target:
        logs_input = f"Input! File: {ext}, Mode: {target}\n"
        with open(LOG_FILE_PATH, 'a') as log_file:  # Logs file to check what might have caused errors
            log_file.write(f"Error! Input: {logs_input} File: {ext}, Mode: {target}\n")
            log_file.write("Error Output:\n")
            log_file.write(traceback.format_exc())
            log_file.write('---------------------------------------------------------------------\n')
    show_toast("Conversion error", f"Check log file in exe directory in Program Files for more information")
