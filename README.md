# Pocket Converter

[![Release](https://img.shields.io/github/v/release/N1ck6/PocketConverter)](https://github.com/N1ck6/PocketConverter/releases/latest)
[![CI](https://github.com/N1ck6/PocketConverter/actions/workflows/ci.yml/badge.svg)](https://github.com/N1ck6/PocketConverter/actions/workflows/ci.yml)
![Windows 10/11](https://img.shields.io/badge/Windows-10%20%7C%2011-blue)

Pocket Converter is a lightweight, **fully offline** file converter that lives in the Windows Explorer right-click menu.
Right-click a file → **Convert to** → pick a format. The result appears next to the original. Nothing is uploaded anywhere.

## Supported conversions

| Category | From → To |
|----------|-----------|
| **Images** | JPG, JPEG, PNG, WEBP, BMP, TIFF, HEIC/HEIF, SVG, ICO → JPG · PNG · WEBP · ICO |
| **Documents** | TXT → PDF · DOCX · MD · HTML · *Clean GPT text*<br>MD → PDF · HTML · DOCX · TXT<br>DOCX → PDF · TXT · MD<br>PDF → DOCX · TXT · MD<br>HTML → PDF · TXT · MD |
| **Video** | MP4, MOV, MKV, AVI, WEBM → MP4 · GIF · MP3 · WAV (MP4 also → FLAC · AAC · OGG) |
| **GIF** | GIF → MP4 · PNG (first frame) · PNG (all frames, into a folder) |
| **Audio** | MP3, WAV, FLAC, AAC, OGG, M4A → each other |
| **Data** | JSON, CSV, XML, YAML/YML → each other |
| **Folders** | Folder of images → one PDF (a page per image) · animated GIF |

The authoritative list is [`converter_app/formats.py`](converter_app/formats.py).

## Install

1. Download **`PocketConverterSetup-<version>.exe`** from the [latest release](https://github.com/N1ck6/PocketConverter/releases/latest).
2. Run it. If Windows SmartScreen says *"Windows protected your PC"*, click **More info → Run anyway**. The installer isn't code-signed yet.
3. Choose **Install for all users** (needs admin) or **Install for me only** (no admin needed).

Upgrading from 1.x? Run the new installer over the old version. It replaces 1.x in place and removes the old menu entries.
To uninstall, go to **Settings → Apps → PocketConverter → Uninstall**.

## Usage

1. Right-click a file, several files, or a folder of images in Explorer.
   On **Windows 11**, the entry is under **Show more options** (or press **Shift+F10**).
2. Choose **Convert to** → format.
3. A notification tells you when it's done. Click it to open the folder.

- Selecting many files gives you one combined notification (for example "Converted 12 files to PNG").
- Existing files are never overwritten. You get `photo(1).png` instead.
- Folder → PDF/GIF saves `<FolderName>.pdf`/`.gif` next to the folder, with images in natural order (`img2` before `img10`).

## GPT text support

Right-click a `.txt` file → **Convert to** → **Clean GPT text** to save a cleaned copy (`name(cleaned).txt`):

- **Markdown removed**: headings, bold/italic, code fences and `inline code`, quotes, list markers, horizontal rules, links (`[text](url)` → `text`)
- **Formulas made calculator-friendly**:
  `√(x)`/`√x` → `(x)^(1/2)` · `³√(x)`, `⁴√(x)` → `(x)^(1/3)`, `(x)^(1/4)` · `x²`, `10⁻³` → `x^2`, `10^(-3)` ·
  `\frac{a}{b}` → `(a)/(b)` · `½` → `1/2` · `×`, `·`, `\cdot` → `*` · `÷` → `/` · `±` → `+/-` · `≤ ≥ ≠` → `<= >= !=` ·
  `π` → `pi` · `∞` → `inf` · `\sin`, `\left(`… → `sin`, `(`

Snake_case names (`my_var`) and arithmetic like `2*3*4` are left alone. Other TXT conversions (PDF, DOCX…) keep your text exactly as written.

## Troubleshooting

- **The menu doesn't appear**: on Windows 11 look under *Show more options*. If it's still missing, re-run the installer and make sure the *Add "Convert to"…* box is ticked.
- **A conversion failed**: the notification says why. Full details are in `%LOCALAPPDATA%\PocketConverter\PocketConverter_log.txt`. Please attach that file when you [open an issue](https://github.com/N1ck6/PocketConverter/issues).
- **PDF → TXT says "no text layer"**: the PDF is a scanned image. PocketConverter doesn't do OCR.

## Building from source

Requires Windows, **Python 3.12+** and [Inno Setup 6](https://jrsoftware.org/isinfo.php) (`winget install JRSoftware.InnoSetup`).

```powershell
git clone https://github.com/N1ck6/PocketConverter.git
cd PocketConverter
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt

.\.venv\Scripts\python -m pytest Test          # unit tests
.\build.ps1 -Python .\.venv\Scripts\python.exe  # -> installer\output\PocketConverterSetup-<version>.exe
```

`build.ps1` runs the tests, freezes the app with PyInstaller, smoke-tests the frozen `converter.exe` on real files, and compiles the installer.

Without the installer, you can register the menu for your user with `python remove_context_menu.py add --exe <path to converter.exe>`, or import `Pocket.reg` (made by `generate_reg_file.py`).

### Project layout

| Path | What it is |
|------|------------|
| `converter.py` | Entry point Explorer calls: `converter.exe "<file>" <format>`. Batches multi-selections into one job. |
| `converter_app/formats.py` | **Single source of truth** for which conversions the menu offers |
| `converter_app/*_converter.py` | Image, document, media (FFmpeg), data and folder converters |
| `installer/` | Inno Setup script, registry generator, smoke and installer tests |
| `.github/workflows/` | CI (every push/PR) and Release (on `v*` tags) pipelines |

### Adding a format

1. Add it to `CONVERSION_MAP` in `converter_app/formats.py`.
2. Make sure the right converter's `SUPPORTED_EXTENSIONS` and `convert()` handle it.
3. Add a test in `Test/`. `TestFormatsConsistency` fails if a menu entry has no converter.

The installer's registry entries are generated from the map, so there's nothing else to edit.

### Releasing

1. Bump `__version__` in `converter_app/__init__.py` and add `docs/release-notes/v<version>.md`.
2. `git tag v<version>` and `git push origin v<version>`. GitHub Actions builds, tests and publishes the release.

## Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/new-format`
3. Commit your changes and push
4. Open a pull request. CI will lint, test and build it automatically.

## License

[MIT](LICENSE)
