"""
Shared test setup. Importing this module first redirects the app's
per-user data folder (log, job queue) to a temp dir, so running the tests
never touches the real %LOCALAPPDATA%\\PocketConverter.
"""

import hashlib
import os
import sys
import tempfile
from pathlib import Path

os.environ['LOCALAPPDATA'] = tempfile.mkdtemp(prefix='pc-test-appdata-')
os.environ['POCKETCONVERTER_NO_TOAST'] = '1'
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SAMPLES = Path(__file__).resolve().parent


def sha256_text(text: str) -> str:
    """Return SHA256 hex digest of a UTF-8 string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def image_pixel_hash(path: Path) -> str:
    """Hash the raw RGB pixel data (deterministic regardless of metadata)."""
    from PIL import Image
    with Image.open(path) as img:
        return hashlib.sha256(img.convert("RGB").tobytes()).hexdigest()


def pdf_text(path: Path) -> str:
    import pymupdf
    with pymupdf.open(str(path)) as doc:
        return "".join(page.get_text("text") for page in doc)


def pdf_text_hash(path: Path) -> str:
    """Extract text from PDF and return its SHA256 hash."""
    return sha256_text(pdf_text(path))


def docx_text(path: Path) -> str:
    from docx import Document
    return "\n".join(p.text for p in Document(str(path)).paragraphs)


def docx_text_hash(path: Path) -> str:
    """Extract text from DOCX and return its SHA256 hash."""
    return sha256_text(docx_text(path))
