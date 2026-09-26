"""
Single source of truth for which conversions the context menu offers.

Everything that registers menu entries (installer/generate_registry_iss.py,
generate_reg_file.py, remove_context_menu.py) and converter.py itself read
these tables — add or remove a format here and nowhere else.
"""

# source extension -> target modes, in menu order
CONVERSION_MAP = {
    # Images
    'bmp': ['jpg', 'png', 'webp', 'ico'],
    'heic': ['jpg', 'png', 'webp', 'ico'],
    'heif': ['jpg', 'png', 'webp', 'ico'],
    'ico': ['jpg', 'png', 'webp'],
    'jpeg': ['jpg', 'png', 'webp', 'ico'],
    'jpg': ['png', 'webp', 'ico'],
    'png': ['jpg', 'webp', 'ico'],
    'svg': ['png', 'jpg', 'webp', 'ico'],
    'tiff': ['jpg', 'png', 'webp', 'ico'],
    'webp': ['jpg', 'png', 'ico'],
    # Documents
    'docx': ['txt', 'pdf', 'md'],
    'html': ['pdf', 'txt', 'md'],
    'htm': ['pdf', 'txt', 'md'],
    'md': ['pdf', 'html', 'docx', 'txt'],
    'pdf': ['txt', 'docx', 'md'],
    'txt': ['pdf', 'docx', 'md', 'html', 'cleangpt'],
    # Video, GIF & Audio
    'gif': ['mp4', 'png', 'pngs'],
    'mp4': ['gif', 'mp3', 'wav', 'flac', 'aac', 'ogg'],
    'mov': ['mp4', 'gif', 'mp3', 'wav'],
    'mkv': ['mp4', 'gif', 'mp3', 'wav'],
    'avi': ['mp4', 'gif', 'mp3', 'wav'],
    'webm': ['mp4', 'gif', 'mp3', 'wav'],
    'aac': ['mp3', 'wav', 'flac', 'ogg'],
    'flac': ['mp3', 'wav', 'aac', 'ogg'],
    'm4a': ['mp3', 'wav', 'flac', 'ogg'],
    'mp3': ['wav', 'flac', 'aac', 'ogg'],
    'ogg': ['mp3', 'wav', 'flac', 'aac'],
    'wav': ['mp3', 'flac', 'aac', 'ogg'],
    # Data
    'csv': ['json', 'xml', 'yaml'],
    'json': ['csv', 'xml', 'yaml'],
    'xml': ['json', 'csv', 'yaml'],
    'yaml': ['json', 'csv', 'xml'],
    'yml': ['json', 'csv', 'xml'],
}

# Right-click on a folder -> these modes (passed to converter.exe as "folder<mode>")
FOLDER_TARGETS = ['pdf', 'gif']

# Menu captions; anything not listed is shown upper-cased (e.g. "PNG")
MENU_LABELS = {
    'cleangpt': 'Clean GPT text',
    'pngs': 'PNG (all frames)',
}
GIF_LABELS = {'png': 'PNG (first frame)'}
FOLDER_LABELS = {'pdf': 'PDF (all images)', 'gif': 'GIF (all images)'}


def menu_label(source: str, target: str) -> str:
    if source == 'gif' and target in GIF_LABELS:
        return GIF_LABELS[target]
    return MENU_LABELS.get(target, target.upper())


def is_supported(source: str, target: str) -> bool:
    return target in CONVERSION_MAP.get(source, [])
