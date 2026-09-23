"""
Entry point used by the Explorer context menu:

    converter.exe "<file or folder>" <mode>

Selecting several files makes Explorer start one process per file; they
pool their jobs through converter_app.jobqueue so the user gets a single
grouped notification instead of one per file.
"""

import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple

from converter_app import __version__
from converter_app.formats import CONVERSION_MAP, FOLDER_TARGETS, is_supported
from converter_app.utils import friendly_error, get_unique_filename, log_error, LOG_FILE_PATH

BATCH_GRACE_SECONDS = 1.5  # how long the worker waits for sibling processes of one multi-select
MAX_WORKERS = min(4, os.cpu_count() or 2)


class ConversionResult(NamedTuple):
    success: bool
    message: str
    source: Path
    output: Optional[Path] = None


class FileConverter:
    def __init__(self, progress_callback=None):
        # Imported here so processes that only hand their job to the worker start fast
        from converter_app.animated_converter import AnimatedConverter
        from converter_app.document_converter import DocumentConverter
        from converter_app.folder_converter import BatchProcessor, DataConverter
        from converter_app.image_converter import ImageConverter

        self.image_converter = ImageConverter()
        self.document_converter = DocumentConverter()
        self.animated_converter = AnimatedConverter()
        self.data_converter = DataConverter()
        self.batch_processor = BatchProcessor(progress_callback)

        self._reserved: set = set()
        self._names_lock = threading.Lock()
        self._routers: Dict[str, object] = {}
        for conv in (self.image_converter, self.document_converter,
                     self.animated_converter, self.data_converter):
            for ext in getattr(conv, "SUPPORTED_EXTENSIONS", []):
                ext = ext.lower()
                if ext in self._routers:
                    raise RuntimeError(
                        f"Extension '.{ext}' is claimed by both "
                        f"{type(self._routers[ext]).__name__} and {type(conv).__name__}"
                    )
                self._routers[ext] = conv

    def convert(self, filepath: str, mode: str) -> ConversionResult:
        path = Path(filepath)
        mode = mode.lower()

        if mode.startswith("folder"):
            if not path.is_dir():
                return ConversionResult(False, "Folder not found", path)
            if mode[len("folder"):] not in FOLDER_TARGETS:
                return ConversionResult(False, f"Unknown folder conversion '{mode}'", path)
            try:
                out = self.batch_processor.convert_folder(str(path), mode)
                return ConversionResult(True, f"Saved as {out.name}", path, out)
            except Exception as e:
                log_error(path, mode)
                return ConversionResult(False, friendly_error(e), path)

        if not path.is_file():
            return ConversionResult(False, "File doesn't exist", path)

        key = path.suffix.lower()[1:]
        if key not in self._routers or key not in CONVERSION_MAP:
            return ConversionResult(False, f"Converting .{key} files isn't supported", path)
        if not is_supported(key, mode):
            return ConversionResult(False, f"Converting .{key} to {mode.upper()} isn't supported", path)

        if mode == 'cleangpt':
            out_ext, base = 'txt', f"{path.stem}(cleaned)"
        else:
            out_ext, base = mode, path.stem
        with self._names_lock:  # parallel jobs (photo.jpg + photo.png -> webp) must not pick the same name
            new_name = get_unique_filename(path.parent, base, out_ext, self._reserved)
            out = path.parent / f"{new_name}.{out_ext}"
            self._reserved.add(out)
        if mode == 'pngs':
            out = path.parent / f"{new_name}_frames"

        try:
            produced = self._routers[key].convert(str(path), mode, new_name)
        except Exception as e:
            log_error(path, mode)
            return ConversionResult(False, friendly_error(e), path)

        out = produced if isinstance(produced, Path) else out  # e.g. a de-duplicated frames folder
        return ConversionResult(True, f"Saved as {out.name}", path, out)

    def convert_file(self, filepath: str, mode: str) -> Tuple[bool, str]:
        result = self.convert(filepath, mode)
        return result.success, result.message

    def convert_multiple_files(self, filepaths: List[str], mode: str) -> List[ConversionResult]:
        if not filepaths:
            return []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            return list(pool.map(lambda p: self.convert(p, mode), filepaths))


# ── Notifications ───────────────────────────────────────────────────────

def _label(mode: str) -> str:
    mode = mode.lower()
    if mode == 'cleangpt':
        return 'clean text'
    if mode == 'pngs':
        return 'PNG frames'
    return mode.replace('folder', '').upper()


def notify_results(mode: str, results: List[ConversionResult]) -> None:
    from converter_app.utils import show_toast

    ok = [r for r in results if r.success]
    failed = [r for r in results if not r.success]
    open_target = ok[0].output.parent if ok and ok[0].output else None

    if len(results) == 1:
        r = results[0]
        if r.success:
            show_toast(f"Converted to {_label(mode)}", r.output.name if r.output else r.message, open_target)
        else:
            show_toast("Conversion failed", f"{r.source.name}: {r.message}")
        return

    title = (f"Converted {len(ok)} files to {_label(mode)}" if not failed
             else f"Converted {len(ok)} of {len(results)} files to {_label(mode)}")
    lines = [f"{r.source.name}: {r.message}" for r in failed[:3]]
    if len(failed) > 3:
        lines.append(f"...and {len(failed) - 3} more (see log)")
    body = '\n'.join(lines) if lines else f"Saved in {open_target}" if open_target else ''
    show_toast(title, body, open_target)


# ── Worker ──────────────────────────────────────────────────────────────

def run_worker(lock) -> None:
    """Convert queued jobs until the queue has been quiet for BATCH_GRACE_SECONDS."""
    from converter_app import jobqueue

    converter = FileConverter()
    groups: Dict[str, List[ConversionResult]] = {}  # finished results per target mode
    in_flight: Dict[str, int] = {}
    last_arrival: Dict[str, float] = {}
    futures = {}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        last_activity = time.monotonic()
        while True:
            for path, mode in jobqueue.take_all():
                futures[pool.submit(converter.convert, path, mode)] = (path, mode)
                in_flight[mode] = in_flight.get(mode, 0) + 1
                last_arrival[mode] = last_activity = time.monotonic()

            for fut in [f for f in futures if f.done()]:
                path, mode = futures.pop(fut)
                try:
                    result = fut.result()
                except Exception as e:  # convert() catches everything, but never lose a result
                    result = ConversionResult(False, friendly_error(e), Path(path))
                groups.setdefault(mode, []).append(result)
                in_flight[mode] -= 1

            # A mode's batch is complete once nothing is running for it and no
            # sibling process has added to it for a moment -> one notification.
            now = time.monotonic()
            for mode in list(groups):
                if in_flight[mode] == 0 and now - last_arrival[mode] >= BATCH_GRACE_SECONDS:
                    notify_results(mode, groups.pop(mode))

            if futures or groups or now - last_activity < BATCH_GRACE_SECONDS:
                time.sleep(0.05)
                continue

            lock.release()
            if jobqueue.has_jobs() and lock.acquire():
                last_activity = time.monotonic()
                continue
            break


def show_about() -> None:
    from converter_app.utils import show_message_box
    show_message_box(
        f"PocketConverter {__version__}",
        "PocketConverter works from the Explorer context menu:\n\n"
        "  1. Right-click a file (or a folder of images)\n"
        "  2. Choose \"Convert to\" and pick a format\n"
        "  3. The result is saved next to the original\n\n"
        "Windows 11: the entry is under \"Show more options\" (or Shift+F10).\n"
        "You can select several files at once.\n\n"
        f"Error log: {LOG_FILE_PATH}"
    )


def main(argv: List[str]) -> int:
    args = argv[1:]
    if not args or args[0] in ('-h', '--help', '/?'):
        show_about()
        return 0
    if args[0] == '--version':
        print(__version__)
        return 0
    if len(args) < 2:
        show_about()
        return 2

    from converter_app import jobqueue

    mode = args[-1].lower()
    for filepath in args[:-1]:
        jobqueue.submit(os.path.abspath(filepath), mode)

    lock = jobqueue.WorkerLock()
    if not lock.acquire():
        return 0  # another converter.exe is already working and will pick our job up
    try:
        run_worker(lock)
    finally:
        lock.release()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
