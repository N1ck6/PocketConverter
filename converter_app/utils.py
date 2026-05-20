"""
Utility functions and constants.
"""

import sys
import shutil
from pathlib import Path
from win11toast import toast
from typing import Optional, List, Dict
import threading

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

_toast_queue: Dict[str, List[str]] = {}
_toast_lock = threading.Lock()

def check_ffmpeg():
    return shutil.which('ffmpeg') is not None


def get_ffmpeg_help():
    return "FFmpeg is required for audio/video edit. Download from: https://ffmpeg.org/download.html"


def show_toast(title: str, message: str):
    icon=ICON_PATH
    toast(title, message, icon=icon)
    sys.exit()
    
def show_toast(title: str, message: str, group: str = 'default'):
    icon = ICON_PATH

    with _toast_lock:
        if title not in _toast_queue:
            _toast_queue[title] = []
        _toast_queue[title].append(message)

        all_messages = _toast_queue[title]

        if len(all_messages) > 1:
            completed = sum(1 for m in all_messages if 'success' in m.lower() or 'converted' in m.lower())
            failed = len(all_messages) - completed
            grouped_msg = f"Completed: {completed} | Failed: {failed} | Total: {len(all_messages)}"
            toast(title, grouped_msg, icon=icon, group=group)
        else:
            toast(title, message, icon=icon, group=group)

def clear_toast_queue(title: Optional[str] = None):
    global _toast_queue
    with _toast_lock:
        if title:
            _toast_queue.pop(title, None)
        else:
            _toast_queue.clear()

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
    if os.path.isfile(LOG_FILE_PATH) and ext and target:
        with open(LOG_FILE_PATH, 'a') as log_file:  # Logs file to check what might have caused an error
            log_file.write(f"Error! Input: File: {ext}, Mode: {target}\n")
            log_file.write("Error Output:\n")
            log_file.write(traceback.format_exc())
            log_file.write('---------------------------------------------------------------------\n')
    show_toast("Conversion error", f"Check log file in exe directory in Program Files for more information")
