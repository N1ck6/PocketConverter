from converter_app.image_converter import ImageConverter
from converter_app.document_converter import DocumentConverter
from converter_app.animated_converter import AnimatedConverter
from converter_app.folder_converter import DataConverter, BatchProcessor
from converter_app.utils import show_toast, get_unique_filename, clear_toast_queue
from os import devnull
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

class ProgressBar:
    def __init__(self, total: int, title: str = "Converting"):
        self.total = total
        self.current = 0
        self.title = title
        self.start_time = time.time()
        self._last_update = 0

    def update(self, amount: int = 1, filename: str = ""):
        self.current += amount
        elapsed = time.time() - self.start_time

        current_time = time.time() # Disable updates flickering
        if current_time - self._last_update < 0.1 and self.current < self.total:
            return

        self._last_update = current_time
        percent = (self.current / self.total) * 100
        bar_length = 40
        filled = int(bar_length * self.current // self.total)
        bar = '█' * filled + '░' * (bar_length - filled)

        if self.current > 0:
            eta = (elapsed / self.current) * (self.total - self.current)
            eta_str = f"{eta:.0f}s"
        else:
            eta_str = "--"

        if filename: # Truncate filename
            filename = filename[:30] + "..." if len(filename) > 33 else filename
            status = f"\r{self.title}: [{bar}] {percent:5.1f}% ({self.current}/{self.total}) | File: {filename} | ETA: {eta_str}"
        else:
            status = f"\r{self.title}: [{bar}] {percent:5.1f}% ({self.current}/{self.total}) | ETA: {eta_str}"

        print(status, end='', flush=True)

        if self.current >= self.total:
            print(f"\n✓ Completed {self.total} conversions in {elapsed:.1f}s")

    def finish(self):
        if self.current < self.total:
            self.current = self.total
            self.update(0)

class FileConverter:
    def __init__(self, progress_callback: Optional[Callable] = None):
        self.image_converter = ImageConverter()
        self.document_converter = DocumentConverter()
        self.animated_converter = AnimatedConverter()
        self.data_converter = DataConverter()
        self.batch_processor = BatchProcessor(progress_callback)
        self.progress_callback = progress_callback
        
        self._routers: Dict[str, object] = {}
        for conv in (self.image_converter, self.document_converter, 
                     self.animated_converter, self.data_converter):
            for ext in getattr(conv, "SUPPORTED_EXTENSIONS", []):
                self._routers[ext.lower()] = conv

    def convert_file(self, filepath: str, mode: str) -> Tuple[bool, str]:
        path = Path(filepath)
        
        if "folder" in mode:
            if not path.is_dir(): return (False, "Folder doesn't exist")
            try:
                self.batch_processor.convert_folder(filepath, mode)
                return (True, f"Folder converted to {mode}")
            except Exception as e:
                return (False, f"Folder conversion failed: {str(e)}")

        if not path.is_file(): return (False, "File doesn't exist")

        ext, target = path.suffix.lower(), f".{mode.lower()}"
        key = ext[1:]

        if ext == target: return (False, "File with that extension already exists")
        if key not in self._routers: return (False, "Format not allowed right now")

        try:
            new_name = get_unique_filename(path.parent, path.stem, mode)
            self._routers[key].convert(str(path), mode, new_name)
            return (True, f"Converted to {mode}")
        except Exception as e:
            return (False, f"Conversion error: {str(e)}")
    
    def convert_multiple_files(self, filepaths: List[str], mode: str,
                                show_progress: bool = False) -> List[Tuple[bool, str]]:
        if not filepaths: return [(False, "No valid files to convert")]
        first_ext = Path(filepaths[0]).suffix.lower()
        validated_files = []
        target = f".{mode.lower()}"

        for filepath in filepaths:
            path = Path(filepath)
            if not path.exists() or path.suffix.lower() != first_ext or path.suffix.lower() == target:
                continue

            key = path.suffix.lower()[1:]
            if key not in self._routers: continue
            
            validated_files.append(filepath)

        if not validated_files: return [(False, "No valid files to convert")]

        results = []
        show_progress = show_progress or len(validated_files) >= 4

        if show_progress:
            progress = ProgressBar(len(validated_files), f"Converting to {mode}")
        else:
            progress = None
        
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
                    if progress:
                        filename = Path(filepath).name
                        progress.update(1, filename)
                except Exception as e:
                    error_msg = f"Unexpected error for {filepath}: {str(e)}"
                    results.append((False, error_msg))
                    if progress:
                        progress.update(1, Path(filepath).name)
        
        clear_toast_queue(f"Conversion into {mode}")
        
        return results
        
        
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: converter.exe <filepath> <mode>")
        quit()
    
    mode = sys.argv[-1]
    filepaths = sys.argv[1:-1]

    if not filepaths:
        print("Error: No input files provided")
        quit()

    converter = FileConverter()
    if len(filepaths) == 1:
        devnull = open(devnull, 'w')
        sys.stdout, sys.stderr = devnull, devnull   # Disable console window popping up
        
        success, message = converter.convert_file(filepaths[0], mode)
        if success:
            show_toast("Conversion complete", message)
        else:
            show_toast("Conversion failed", message)
    else:
        # Batch conversion with progress bar
        results = converter.convert_multiple_files(filepaths, mode, show_progress=True)

        success_count = sum(1 for success, _ in results if success)
        total_count = len(results)
        show_toast(f"Conversion into {mode}", f"Converted {success_count}/{total_count} files")