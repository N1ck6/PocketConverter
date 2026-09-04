# Pocket Converter

[![Release](https://img.shields.io/github/v/release/N1ck6/PocketConverter)](https://github.com/N1ck6/PocketConverter/releases/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

File Converter is a lightweight but powerful file conversion tool that integrates directly into the Windows context menu. <br>
It allows users to instantly convert files between various formats without requiring an internet connection, ensuring privacy and speed.

## Supported Conversions
| Category | Formats |
|----------|---------|
| **Images** | JPG ↔ JPEG ↔ PNG ↔ WEBP ↔ BMP ↔ TIFF ↔ HEIC/HEIF ↔ SVG ↔ ICO |
| **Documents** | PDF ↔ DOCX ↔ TXT ↔ HTML ↔ MD |
| **Video/GIF** | MP4 → GIF, MP3, WAV, FLAC, AAC, OGG \| GIF → MP4, PNG(s) |
| **Audio** | MP3 ↔ WAV ↔ FLAC ↔ AAC ↔ OGG |
| **Data** | JSON ↔ XML ↔ CSV ↔ YAML |
| **Batch** | Folder → PDF, Folder → GIF |

## Features

- **Progress Bar**: Progress for large batch conversions (visible in console/dev runs)
- **Privacy**: 100% offline, no uploads, complete confidentiality
- **Notifications**: Grouped completion alerts via Windows toast
- **Text Formatting**: Cleans markdown from GPT-generated text and converts formulas to calculator format

## Usage

### Context Menu (Windows Only)
1. Right-click any supported file or folder in Windows Explorer
2. Select **"Convert to"** → Choose format
3. Converted file appears in the same directory
4. Receive notification when complete

## Quick Start

### 1) Run Installer
Download from latest **[Release](https://github.com/N1ck6/PocketConverter/releases/)**

### 2) Manual Setup
```bash
git clone https://github.com/N1ck6/PocketConverter.git
cd PocketConverter
pip install -r requirements.txt
# Use pyinstaller to compile into .exe:
# pyinstaller --onefile --noconsole --icon=small.ico --add-data "logo.ico;." --add-data "DejaVuSansCondensed.ttf;." --add-data "converter_app;converter_app" converter.py
# Place in subfolder "PocketConverter" in "Program Files" folder
```

##  GPT Text Support

Right-click a `.txt` file → **"Convert to"** → **"Clean GPT Text"** to save a cleaned copy (`name(cleaned).txt`) next to the original, with the following applied:

**Clean GPT Markdown**:
   - Removes heading markers (#, ##, ###)
   - Strips bold and italic formatting
   - Removes code block markers, list markers, quote markers (>)
   - Converts links [text](url) to plain text

**Convert Formulas**:
   - Square roots: √(x) → (x)^(1/2)
   - Nth roots: ⁿ√(x) → (x)^(1/n)
   - Fractions: ½ → 1/2, ¼ → 1/4, ¾ → 3/4
   - LaTeX fractions: \frac{a}{b} → (a)/(b)
   - Powers: x² → x^2
   - Math symbols: × → *, ÷ → /, − → -, ± → +/-
   - Constants: π → pi, ∞ → inf
   - Trig functions: \sin → sin, \cos → cos, \tan → tan
   - Parentheses: \left( → (, \right) → )


## Contributing

1. Fork the repo
2. Create feature branch: `git checkout -b feature/new-format`
3. Commit changes: `git commit -m 'Add support for XYZ'`
4. Push: `git push origin feature/new-format`
5. Open Pull Request
---

## Enjoy fast, private, and seamless file conversions!