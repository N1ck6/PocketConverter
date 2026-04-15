"""
Utility functions and constants for the converter application.
"""

import sys
import shutil
from pathlib import Path
from win11toast import toast


# Configuration constants
SUPPORTED_EXTENSIONS = [
    'mp4', 'gif', 'txt', 'pdf', 'docx', 'jpg', 'jpeg', 'png', 
    'webp', 'bmp', 'tiff', 'ico', 'heic', 'svg', 'md', 'markdown',
    'json', 'xml', 'csv', 'mp3', 'wav', 'flac', 'aac', 'ogg'
]
LOG_FILE_PATH = r"C:\Program Files\PocketConverter\PocketConverter_log.txt"

# Quality settings defaults
DEFAULT_IMAGE_QUALITY = 95
DEFAULT_AUDIO_BITRATE = '192k'
DEFAULT_VIDEO_BITRATE = '2000k'

# Get base path for frozen/unfrozen execution
if getattr(sys, 'frozen', False):
    BASE_PATH = sys._MEIPASS
else:
    BASE_PATH = Path(__file__).parent.parent

ICON_PATH = BASE_PATH / 'logo.ico'
FONT_PATH = BASE_PATH / 'DejaVuSansCondensed.ttf'


def check_ffmpeg():
    """
    Check if FFmpeg is installed and available in system PATH.
    
    Returns:
        bool: True if FFmpeg is available, False otherwise
    """
    return shutil.which('ffmpeg') is not None


def get_ffmpeg_help():
    """
    Get help message for installing FFmpeg.
    
    Returns:
        str: Installation instructions
    """
    return """FFmpeg is required for audio/video conversions.

Installation options:
1. Download from: https://ffmpeg.org/download.html
2. Install via winget: winget install ffmpeg
3. Install via chocolatey: choco install ffmpeg

After installation, restart the application."""


def show_toast(title: str, message: str, icon: str = None, group: str = None):
    """
    Display a Windows toast notification.
    
    Args:
        title: Notification title
        message: Notification message
        icon: Path to icon file
        group: Notification group identifier
    """
    toast(title, message, icon=icon)


def get_unique_filename(directory: Path, basename: str, extension: str) -> str:
    """
    Generate a unique filename if file already exists.
    
    Args:
        directory: Directory path
        basename: Base filename without extension
        extension: File extension
        
    Returns:
        Unique filename (without extension)
    """
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
    """
    Parse filepath string into directory, basename, and extension.
    
    Args:
        filepath_str: Full file path as string
        
    Returns:
        Dictionary with 'dir', 'name', 'ext', and 'full' keys
    """
    path = Path(filepath_str)
    return {
        'dir': str(path.parent) + '\\',
        'name': path.stem,
        'ext': path.suffix,
        'full': str(path)
    }
