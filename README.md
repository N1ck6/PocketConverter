# Pocket Converter

[![Release](https://img.shields.io/github/v/release/N1ck6/PocketConverter)](https://github.com/N1ck6/PocketConverter/releases/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

File Converter is a lightweight but powerful file conversion tool that integrates directly into the Windows context menu. 
It allows users to instantly convert files between various formats without requiring an internet connection, ensuring privacy and speed.

## Features

- **Images**: JPG, PNG, WEBP, GIF, BMP, TIFF, HEIC, SVG, ICO (favicon)
- **Documents**: PDF ↔ DOCX ↔ TXT, EPUB ↔ MOBI, Markdown ↔ HTML, PDF Merge/Split
- **Media**: MP4, AVI, MOV, MKV → GIF, MP3 | GIF → MP4, PNG frames
- **Data**: JSON ↔ XML ↔ CSV ↔ YAML
- **Smart Core**: Single background instance with async task queue
- **Notifications**: Real-time progress & completion alerts
- **Privacy**: 100% offline, no uploads, complete confidentiality
- **Text Formatting**: Automatically cleans markdown formatting from GPT-generated text and converts mathematical formulas to calculator-friendly format

## Architecture

```
converter.py                  # Main entry & context menu handler
converter_app/
├── utils.py                  # Utilities, constants
├── image_converter.py        # Image processing
├── document_converter.py     # Document tools with GPT's text and formulas support
├── animated_converter.py     # Audio/Video conversion
└── folder_converter.py       # Batch processing
```

## Quick Start

### Install from Release
Download the latest executable: **[Releases Page](https://github.com/N1ck6/PocketConverter/releases/)**

### Manual Setup
```bash
git clone https://github.com/N1ck6/PocketConverter.git
cd PocketConverter
pip install -r requirements.txt
```

**FFmpeg** (Required for video/audio):
- Windows: `choco install ffmpeg`
- Mac: `brew install ffmpeg`
- Linux: `sudo apt install ffmpeg`

## Usage

### Context Menu (Only Windows)
1. Right-click any file/folder in Explorer
2. Select **"Convert to"** → Choose format
3. Converted file appears in the same directory
4. Receive notification when complete

### Command Line
```bash
# Single file
python converter.py input.jpg output.png

# Batch folder
python converter.py --batch ./images --format webp

# Check status
python converter.py --status
```

### Python API
```python
from converter_app.image_converter import ImageConverter
from converter_app.animated_converter import MediaConverter

ImageConverter.convert("photo.heic", "photo.jpg")
MediaConverter.convert("video.mov", "video.mp4", fps=30)
```

## Supported Conversions

| Category | Formats |
|----------|---------|
| **Images** | JPG ↔ PNG ↔ WEBP ↔ GIF ↔ BMP ↔ TIFF ↔ HEIC ↔ SVG ↔ ICO |
| **Documents** | PDF ↔ DOCX ↔ TXT, EPUB ↔ MOBI, MD ↔ HTML |
| **Media** | MP4 / AVI / MOV / MKV → GIF, MP3 \| GIF → MP4, PNGs |
| **Data** | JSON ↔ XML ↔ CSV ↔ YAML |
| **Batch** | Folder → PDF, Folder → GIF |

##  Configuration

Customize settings in `converter_app/utils.py`:
- Default quality/compression levels
- Supported format lists
- Notification preferences
- Log file location

## New Functionality: GPT Text Support

When converting TXT files, the converter now automatically:
1. **Cleans GPT Markdown Formatting**:
   - Removes heading markers (#, ##, ###)
   - Strips bold and italic formatting
   - Removes code block markers, list markers, quote markers (>)
   - Converts links [text](url) to plain text

2. **Converts Mathematical Formulas** to calculator-friendly format:
   - Square roots: √(x) → (x)^(1/2)
   - Nth roots: ⁿ√(x) → (x)^(1/n)
   - Fractions: ½ → 1/2, ¼ → 1/4, ¾ → 3/4
   - LaTeX fractions: \frac{a}{b} → (a)/(b)
   - Powers: x² → x^2
   - Math symbols: × → *, ÷ → /, − → -, ± → +/-
   - Constants: π → pi, ∞ → inf
   - Trig functions: \sin → sin, \cos → cos, \tan → tan
   - Parentheses: \left( → (, \right) → )

## Requirements

- **Python**: 3.8+
- **Core**: `Pillow`, `python-docx`, `PyPDF2`, `markdown`
- **Images**: `pillow-heif` (HEIC support)
- **Media**: `moviepy`, `pydub` + **FFmpeg**
- **Windows**: `win11toast` (notifications), `pywin32` (context menu)
- **HTML Processing**: `beautifulsoup4`, `html2text`
- **SVG**: `cairosvg`

## Contributing

1. Fork the repo
2. Create feature branch: `git checkout -b feature/new-format`
3. Commit changes: `git commit -m 'Add support for XYZ'`
4. Push: `git push origin feature/new-format`
5. Open Pull Request

## License

MIT License - See [LICENSE](LICENSE) file

---

**Enjoy fast, private, and seamless file conversions!**