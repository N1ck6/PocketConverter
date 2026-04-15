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
LOG_FILE_PATH = r"C:\Program Files\PocketConverter\PocketConverter_log.txt"

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


def show_toast(title: str, message: str, icon: str = None, group: str = None):
    toast(title, message, icon=icon)


def get_unique_filename(directory: Path, basename: str, extension: str) -> str:
    filepath = directory / f"{basename}.{extension}"
    if extension != 'pngs' and filepath.exists():
        for i in range(1, 101):
            new_name = f"{basename}({i})"
            filepath = directory / f"{new_name}.{extension}"
            if not filepath.exists():
                return new_name
        show_toast("File name already exists", "Try renaming the file", icon=ICON_PATH)
        sys.exit()
    return basename


def parse_filepath(filepath_str: str) -> dict:
    path = Path(filepath_str)
    return {
        'dir': str(path.parent) + '\\',
        'name': path.stem,
        'ext': path.suffix,
        'full': str(path)
    }
