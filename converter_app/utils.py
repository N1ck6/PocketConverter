"""
Shared helpers: resource paths, text decoding, output naming, FFmpeg,
error logging and Windows notifications.
"""

import os
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path
from typing import Optional

if getattr(sys, 'frozen', False):
    BASE_PATH = Path(sys._MEIPASS)
else:
    BASE_PATH = Path(__file__).parent.parent

ICON_PATH = BASE_PATH / "logo.ico"
FONT_PATH = BASE_PATH / "DejaVuSansCondensed.ttf"

# Per-user writable location — Program Files is read-only for normal users,
# which is where the log used to go (and silently never got written).
DATA_DIR = Path(os.environ.get('LOCALAPPDATA') or Path.home() / 'AppData' / 'Local') / 'PocketConverter'
LOG_FILE_PATH = DATA_DIR / 'PocketConverter_log.txt'
LOG_MAX_BYTES = 1_000_000

APP_ID = 'N1ck6.PocketConverter'  # must match AppUserModelID in installer.iss

DEFAULT_IMAGE_QUALITY = 95
DEFAULT_AUDIO_BITRATE = '192k'
DEFAULT_VIDEO_BITRATE = '2000k'

CREATE_NO_WINDOW = 0x08000000  # keep FFmpeg from flashing a console window


# ── Text ────────────────────────────────────────────────────────────────

def read_text(path) -> str:
    """
    Read a text file whatever Windows tool produced it: UTF-8 with or
    without BOM, UTF-16 (BOM), or the legacy ANSI code page (e.g. cp1251).
    Line endings are normalized to "\n": text-mode writes turn them back
    into CRLF, while keeping "\r\n" here would produce "\r\r\n".
    """
    return _decode(Path(path).read_bytes()).replace('\r\n', '\n').replace('\r', '\n')


def _decode(raw: bytes) -> str:
    if raw.startswith((b'\xff\xfe', b'\xfe\xff')):
        return raw.decode('utf-16')
    try:
        return raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        pass
    import locale
    for enc in (locale.getpreferredencoding(False), 'cp1252'):
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode('utf-8', errors='replace')


# ── Output naming ───────────────────────────────────────────────────────

def get_unique_filename(directory: Path, basename: str, extension: str, taken: set = frozenset()) -> str:
    """
    Return a basename such that <directory>/<basename>.<extension> doesn't
    exist yet and isn't in `taken` (names reserved by parallel conversions).
    """
    ext = extension.strip().lstrip('.')
    directory = Path(directory)

    def free(name):
        path = directory / f"{name}.{ext}"
        return not path.exists() and path not in taken

    if free(basename):
        return basename
    for i in range(1, 1000):
        candidate = f"{basename}({i})"
        if free(candidate):
            return candidate
    return f"{basename}_{time.time_ns()}"


def get_unique_dirname(directory: Path, basename: str) -> Path:
    directory = Path(directory)
    candidate = directory / basename
    i = 1
    while candidate.exists():
        candidate = directory / f"{basename}({i})"
        i += 1
    return candidate


def output_path(filepath, new_name: str, ext: str) -> Path:
    """
    Build the output path next to the source. Never use Path.with_suffix()
    on new_name: for "my.notes" it would drop ".notes" and silently write
    (and overwrite) "my.<ext>".
    """
    return Path(filepath).parent / f"{new_name}.{ext}"


def natural_key(name: str):
    """Sort key so that img2 < img10."""
    import re
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', name)]


# ── FFmpeg ──────────────────────────────────────────────────────────────

def get_ffmpeg_exe() -> str:
    """Prefer the FFmpeg bundled with imageio-ffmpeg, so users don't have to install one."""
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and Path(exe).exists():
            return exe
    except Exception:
        pass
    exe = shutil.which('ffmpeg')
    if exe:
        return exe
    raise RuntimeError("FFmpeg not found. Reinstall PocketConverter or install FFmpeg from https://ffmpeg.org")


def run_ffmpeg(args: list) -> None:
    cmd = [get_ffmpeg_exe(), '-hide_banner', '-loglevel', 'error', '-y', *args]
    result = subprocess.run(
        cmd, capture_output=True,
        creationflags=CREATE_NO_WINDOW if os.name == 'nt' else 0,
    )
    if result.returncode != 0:
        err = result.stderr.decode(errors='ignore').strip()
        if 'does not contain any stream' in err or 'matches no streams' in err:
            raise RuntimeError("The file has no audio track")
        last = err.splitlines()[-1] if err else f"exit code {result.returncode}"
        raise RuntimeError(f"FFmpeg failed: {last}")


# ── Errors & logging ────────────────────────────────────────────────────

def friendly_error(exc: BaseException) -> str:
    """Short, user-facing explanation for a notification."""
    if isinstance(exc, PermissionError):
        return "No permission to write in this folder, or the file is open in another program"
    if isinstance(exc, FileNotFoundError):
        return "File not found"
    if type(exc).__name__ == 'UnidentifiedImageError':
        return "The file is damaged or is not a valid image"
    msg = str(exc).strip() or type(exc).__name__
    return msg if len(msg) <= 200 else msg[:197] + '...'


def log_error(filepath, target) -> None:
    """Append the current exception's traceback to the per-user log file."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if LOG_FILE_PATH.exists() and LOG_FILE_PATH.stat().st_size > LOG_MAX_BYTES:
            LOG_FILE_PATH.replace(LOG_FILE_PATH.with_suffix('.old.txt'))
        with open(LOG_FILE_PATH, 'a', encoding='utf-8') as log_file:
            log_file.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Input: {filepath} | Mode: {target}\n")
            log_file.write(traceback.format_exc())
            log_file.write('-' * 70 + '\n')
    except OSError:
        pass


# ── Notifications ───────────────────────────────────────────────────────

def show_toast(title: str, message: str, open_path: Optional[Path] = None) -> None:
    """
    Fire-and-forget Windows notification. Clicking it opens `open_path`
    (usually the folder with the result). Falls back to stdout off-Windows
    or when the notification platform isn't available.
    """
    try:
        if os.environ.get('POCKETCONVERTER_NO_TOAST'):  # tests / CI
            raise RuntimeError
        from win11toast import notify
        kwargs = {'app_id': APP_ID, 'icon': str(ICON_PATH.resolve())}
        if open_path:
            kwargs['on_click'] = Path(open_path).resolve().as_uri()
        notify(title, message, **kwargs)
    except Exception:
        try:
            print(f"[{title}] {message}")
        except Exception:
            pass


def show_message_box(title: str, text: str) -> None:
    if os.name == 'nt':
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, text, title, 0x40)  # MB_ICONINFORMATION
    else:
        print(f"{title}\n{text}")
