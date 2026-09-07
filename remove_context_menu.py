import os
import sys
import ctypes
import winreg
from win11toast import toast
from platform import system

base_path = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
icon_dir = os.path.join(base_path, 'logo.ico')
EXE_PATH = r"C:\Program Files\PocketConverter\converter.exe"
ICON_PATH = r"C:\Program Files\PocketConverter\small.ico"

# source -> target mapping
CONVERSION_MAP = {
    # Images
    'bmp': ['jpg', 'png', 'webp', 'ico'],
    'heic': ['jpg', 'png', 'webp', 'ico'],
    'heif': ['jpg', 'png', 'webp', 'ico'],
    'ico': ['jpg', 'png', 'webp'],
    'jpeg': ['jpg', 'png', 'webp', 'ico'],
    'jpg': ['png', 'webp', 'ico'],
    'png': ['jpg', 'webp', 'ico'],
    'svg': ['png', 'jpg', 'webp'],
    'tiff': ['jpg', 'png', 'webp', 'ico'],
    'webp': ['jpg', 'png', 'ico'],
    # Documents
    'docx': ['txt', 'pdf', 'md'],
    'html': ['pdf', 'txt', 'md'],
    'md': ['pdf', 'html', 'docx', 'txt'],
    'pdf': ['txt', 'docx', 'md'],
    'txt': ['pdf', 'docx', 'md', 'html', 'cleangpt'],
    # Animated & Audio
    'gif': ['mp4', 'png', 'pngs'],
    'mp4': ['gif', 'mp3', 'wav', 'flac'],
    'aac': ['mp3', 'wav', 'flac', 'ogg'],
    'flac': ['mp3', 'wav', 'aac', 'ogg'],
    'mp3': ['wav', 'flac', 'aac', 'ogg'],
    'ogg': ['mp3', 'wav', 'flac', 'aac'],
    'wav': ['mp3', 'flac', 'aac', 'ogg'],
    # Data
    'csv': ['json', 'xml', 'yaml'],
    'json': ['csv', 'xml', 'yaml'],
    'xml': ['json', 'csv', 'yaml'],
    'yaml': ['json', 'csv', 'xml'],
}

# Display names for menu items where label isn't self-explanatory
MENU_LABELS = {
    'cleangpt': 'Clean GPT Text',
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
    for ext, targets in CONVERSION_MAP.items():  # File extensions
        key_path = fr"Software\Classes\SystemFileAssociations\.{ext}\shell\PocketConverter"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.SetValueEx(key, "MUIVerb", 0, winreg.REG_SZ, "Convert to")
            winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, ICON_PATH)
            winreg.SetValueEx(key, "SubCommands", 0, winreg.REG_SZ, "")
            winreg.SetValueEx(key, "MultiSelectModel", 0, winreg.REG_SZ, "Single")

        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"{key_path}\\shell"):
            pass

        for i, target in enumerate(targets):
            subkey_path = f"{key_path}\\shell\\sub_one_{i}"
            cmd_path = f"{subkey_path}\\command"
            label = MENU_LABELS.get(target, target)

            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, subkey_path) as key:
                winreg.SetValueEx(key, "MUIVerb", 0, winreg.REG_SZ, label)
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, cmd_path) as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f'"{EXE_PATH}" "%1" {target}')

    # Directory context menu (folders)
    dir_key_path = r"Directory\shell\PocketConverter"
    with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, dir_key_path) as key:
        winreg.SetValueEx(key, "MUIVerb", 0, winreg.REG_SZ, "Convert to")
        winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, ICON_PATH)
        winreg.SetValueEx(key, "SubCommands", 0, winreg.REG_SZ, "")
        winreg.SetValueEx(key, "MultiSelectModel", 0, winreg.REG_SZ, "Single")

    with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, f"{dir_key_path}\\shell"):
        pass

    for i, target in enumerate(['pdf', 'gif']):
        subkey_path = f"{dir_key_path}\\shell\\sub_one_{i}"
        cmd_path = f"{subkey_path}\\command"

        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, subkey_path) as key:
            winreg.SetValueEx(key, "MUIVerb", 0, winreg.REG_SZ, target)
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


def create_reg_file(output_path="Pocket.reg"):
    """Generate a .reg file with exact structure matching the provided Pocket.reg."""
    lines = ["Windows Registry Editor Version 5.00", ""]

    # Directory section first (as in original reg)
    dir_key_path = r"Directory\shell\PocketConverter"
    lines.append(f"[HKEY_CLASSES_ROOT\\{dir_key_path}]")
    lines.append('"MUIVerb"="Convert to"')
    lines.append(f'"Icon"="{ICON_PATH.replace(chr(92), chr(92)+chr(92))}"')
    lines.append('"SubCommands"=""')
    lines.append('"MultiSelectModel"="Single"')
    lines.append("")
    lines.append(f"[HKEY_CLASSES_ROOT\\{dir_key_path}\\shell]")
    lines.append("")

    for i, target in enumerate(['pdf', 'gif']):
        sub = f"sub_one_{i}"
        lines.append(f"[HKEY_CLASSES_ROOT\\{dir_key_path}\\shell\\{sub}]")
        lines.append(f'"MUIVerb"="{target}"')
        lines.append("")
        lines.append(f"[HKEY_CLASSES_ROOT\\{dir_key_path}\\shell\\{sub}\\command]")
        # Escape for .reg: backslashes doubled, inner quotes escaped
        cmd = f'{EXE_PATH} "%V" folder{target}'
        cmd_escaped = cmd.replace('\\', '\\\\').replace('"', '\\"')
        lines.append(f'@="{cmd_escaped}"')
        lines.append("")

    # File extensions (order roughly follows original, but dict order is fine)
    for ext, targets in CONVERSION_MAP.items():
        base = fr"Software\Classes\SystemFileAssociations\.{ext}"
        # Empty parent keys as in the exported reg
        lines.append(f"[HKEY_CURRENT_USER\\{base}]")
        lines.append("")
        lines.append(f"[HKEY_CURRENT_USER\\{base}\\shell]")
        lines.append("")

        key_path = fr"{base}\shell\PocketConverter"
        lines.append(f"[HKEY_CURRENT_USER\\{key_path}]")
        lines.append('"MUIVerb"="Convert to"')
        lines.append(f'"Icon"="{ICON_PATH.replace(chr(92), chr(92)+chr(92))}"')
        lines.append('"SubCommands"=""')
        lines.append('"MultiSelectModel"="Single"')
        lines.append("")
        lines.append(f"[HKEY_CURRENT_USER\\{key_path}\\shell]")
        lines.append("")

        for i, target in enumerate(targets):
            sub = f"sub_one_{i}"
            label = MENU_LABELS.get(target, target)
            lines.append(f"[HKEY_CURRENT_USER\\{key_path}\\shell\\{sub}]")
            lines.append(f'"MUIVerb"="{label}"')
            lines.append("")
            lines.append(f"[HKEY_CURRENT_USER\\{key_path}\\shell\\{sub}\\command]")
            cmd = f'{EXE_PATH} "%1" {target}'
            cmd_escaped = cmd.replace('\\', '\\\\').replace('"', '\\"')
            lines.append(f'@="{cmd_escaped}"')
            lines.append("")

    # Write as UTF-16 LE with BOM (standard for .reg files)
    content = "\r\n".join(lines)
    with open(output_path, "w", encoding="utf-16") as f:
        f.write(content)
    return output_path


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