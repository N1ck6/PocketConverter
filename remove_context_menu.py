import os
import sys
import ctypes
import winreg
from win11toast import toast
from platform import system

# Resolve paths for frozen exe vs source
base_path = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
icon_dir = os.path.join(base_path, 'logo.ico')
EXE_PATH = r"C:\Program Files\PocketConverter\converter.exe"
ICON_PATH = r"C:\Program Files\PocketConverter\small.ico"

# Dynamic source -> target mapping extracted from converter classes
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
    'markdown': ['pdf', 'html', 'docx', 'txt'],
    'md': ['pdf', 'html', 'docx', 'txt'],
    'pdf': ['txt', 'docx', 'md'],
    'txt': ['pdf', 'docx', 'md', 'html'],
    # Animated & Audio
    'gif': ['mp4', 'png', 'pngs'],
    'mp4': ['gif', 'mp3', 'wav', 'flac', 'aac', 'ogg'],
    'aac': ['mp3', 'wav', 'flac', 'ogg'],
    'flac': ['mp3', 'wav', 'aac', 'ogg'],
    'mp3': ['wav', 'flac', 'aac', 'ogg'],
    'ogg': ['mp3', 'wav', 'flac', 'aac'],
    'wav': ['mp3', 'flac', 'aac', 'ogg'],
    # Data
    'csv': ['json', 'xml', 'yaml', 'yml'],
    'json': ['csv', 'xml', 'yaml', 'yml'],
    'xml': ['json', 'csv', 'yaml', 'yml'],
    'yaml': ['json', 'csv', 'xml'],
    'yml': ['json', 'csv', 'xml'],
}

def run_as_admin():
    if not ctypes.windll.shell32.IsUserAnAdmin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

def delete_key_recursive(hkey, path):
    """Safely removes a registry key and all its subkeys."""
    try:
        with winreg.OpenKey(hkey, path) as key:
            idx = 0
            while True:
                try:
                    subkey = winreg.EnumKey(key, idx)
                    delete_key_recursive(hkey, f"{path}\\{subkey}")
                    idx += 1
                except OSError:
                    break
        winreg.DeleteKey(hkey, path)
    except FileNotFoundError:
        pass

def add_context_menu():
    # File extensions
    for ext, targets in CONVERSION_MAP.items():
        key_path = fr"Software\Classes\SystemFileAssociations\.{ext}\shell\PocketConverter"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.SetValueEx(key, "MUIVerb", 0, winreg.REG_SZ, "Convert to")
            winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, ICON_PATH)
            winreg.SetValueEx(key, "SubCommands", 0, winreg.REG_SZ, "")
            winreg.SetValueEx(key, "MultiSelectModel", 0, winreg.REG_SZ, "Single")

        for i, target in enumerate(targets):
            subkey_path = f"{key_path}\\shell\\sub_{i}"
            cmd_path = f"{subkey_path}\\command"

            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, subkey_path) as key:
                winreg.SetValueEx(key, "MUIVerb", 0, winreg.REG_SZ, target)

            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, cmd_path) as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f'"{EXE_PATH}" "%1" {target}')

    # Directory context menu (folders)
    dir_key_path = r"Directory\shell\PocketConverter"
    with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, dir_key_path) as key:
        winreg.SetValueEx(key, "MUIVerb", 0, winreg.REG_SZ, "Convert to")
        winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, ICON_PATH)
        winreg.SetValueEx(key, "SubCommands", 0, winreg.REG_SZ, "")
        winreg.SetValueEx(key, "MultiSelectModel", 0, winreg.REG_SZ, "Single")

    for i, target in enumerate(['pdf', 'gif']):
        subkey_path = f"{dir_key_path}\\shell\\sub_{i}"
        cmd_path = f"{subkey_path}\\command"

        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, subkey_path) as key:
            winreg.SetValueEx(key, "MUIVerb", 0, winreg.REG_SZ, f"folder{target}")

        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, cmd_path) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f'"{EXE_PATH}" "%V" folder{target}')

    toast("Success", "Context menu added successfully", icon=icon_dir, group='done')

def remove_context_menu():
    # File extensions
    for ext in CONVERSION_MAP.keys():
        key_path = fr"Software\Classes\SystemFileAssociations\.{ext}\shell\PocketConverter"
        delete_key_recursive(winreg.HKEY_CURRENT_USER, key_path)

    # Directory
    dir_key_path = r"Directory\shell\PocketConverter"
    delete_key_recursive(winreg.HKEY_CLASSES_ROOT, dir_key_path)

    toast("Success", "Context menu removed successfully", icon=icon_dir, group='done')

if __name__ == "__main__":
    if system() != "Windows": quit();
    try:
        run_as_admin()
        check_path = r"Software\Classes\SystemFileAssociations\.bmp\shell\PocketConverter"
        try:
            winreg.OpenKey(winreg.HKEY_CURRENT_USER, check_path)
            remove_context_menu()
        except FileNotFoundError:
            add_context_menu()
    except Exception as e:
        toast("Error", str(e), icon=icon_dir)