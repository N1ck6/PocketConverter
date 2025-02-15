# File Converter

## Overview
File Converter is a lightweight and fast file format conversion tool that integrates directly into the Windows context menu. It allows users to instantly convert files between various formats without requiring an internet connection, ensuring privacy and speed.

## Features
- **Seamless Integration:** Converts files directly from the Windows Explorer context menu.
- **Fast Processing:** Instantly converts files without the need for external software or web-based services.
- **Offline Support:** No internet connection is required, ensuring quick and private file transformations.
- **Privacy-Focused:** Files are never uploaded to external servers, maintaining complete confidentiality.
- **Comprehensive Format Support:** A single tool for converting multiple file types, eliminating the need for various online tools.

## Supported Conversions

### Video & Audio
- `mp4` → `gif`, `mp3`
- `gif` → `mp4`, `png`, `folder` (frame images)

### Image Conversions
- `jpg` → `png`, `webp`, `ico`
- `jpeg` → `jpg`, `png`, `webp`, `ico`
- `png` → `jpg`, `webp`, `ico`
- `webp` → `jpg`, `png`, `ico`
- `bmp` → `jpg`, `png`, `webp`, `ico`
- `tiff` → `jpg`, `png`, `webp`, `ico`
- `ico` → `jpg`, `png`, `webp`
- `folder` (with images) → `pdf`, `gif`

### Document Conversions
- `txt` → `pdf`, `docx`
- `pdf` → `txt`, `docx`
- `docx` → `txt`, `pdf`

## Installation

### Requirements
Ensure you have Python installed on your system. The following dependencies are required:
```sh
pip install Pillow python-docx moviepy win11toast fpdf docx2pdf pymupdf pdf2docx
```

### Setup
1. Create executable files:
   Download zip or Clone the repository:
   ```sh
   git clone https://github.com/N1ck6/PocketConverter.git
   ```
   Navigate to the project directory and Install dependencies and pyinstaller:
   ```sh
   cd PocketConverter
   pip install -r requirements.txt
   ```
   Run pyinstaller:
   ```sh
   <path to pyinstaller.exe here> --onefile --add-data "logo.ico;." --add-data "DejaVuSansCondensed.ttf;." --noconsole --icon=logo.ico converter.py
   <path to pyinstaller.exe here> --onefile --noconsole --icon=logo.ico remove_context_menu.py
   ```
   Create folder C:\Program Files\PocketConverter and move both exe files, PocketConverter_log.txt, small.ico there.
   Run converter.exe as Administrator once to add context menu.
   
2. Download and run Installer.
   Run converter.exe as Administrator once to add context menu.
To remove context menu run remove_context_menu.exe as Administrator once

## Usage
1. Right-click on a file or folder in Windows Explorer.
2. Select "Convert to" from the context menu.
3. Choose the desired format.
4. The converted file will be saved in the same directory.
5. You will recieve notification when conversion is completed.


## Contributing
Contributions are welcome! Feel free to submit issues or pull requests to improve this utility.

---

Enjoy fast and secure file conversions directly from your desktop!

