"""
Add or remove the "Convert to" context menu for the current user, without
the installer (e.g. for a manual/dev setup). No admin rights needed: all
keys live under HKEY_CURRENT_USER.

Usage:
    python remove_context_menu.py            # toggle
    python remove_context_menu.py add [--exe "D:\\Tools\\PocketConverter\\converter.exe"]
    python remove_context_menu.py remove
"""

import argparse
import sys
import winreg
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from converter_app.formats import CONVERSION_MAP, FOLDER_LABELS, FOLDER_TARGETS, menu_label  # noqa: E402

DEFAULT_EXE = r"C:\Program Files\PocketConverter\converter.exe"
FILE_KEY = r"Software\Classes\SystemFileAssociations\.{ext}\shell\PocketConverter"
DIR_KEY = r"Software\Classes\Directory\shell\PocketConverter"


def menus(exe: str):
    """Yield (key path, [(label, command), ...]) for every menu to register."""
    for ext, targets in CONVERSION_MAP.items():
        yield FILE_KEY.format(ext=ext), [(menu_label(ext, t), f'"{exe}" "%1" {t}') for t in targets]
    yield DIR_KEY, [(FOLDER_LABELS.get(t, t.upper()), f'"{exe}" "%V" folder{t}') for t in FOLDER_TARGETS]


def delete_key_recursive(hkey, path):
    """Removes a registry key and all its subkeys; missing keys are fine."""
    try:
        with winreg.OpenKey(hkey, path) as key:
            while True:
                try:
                    subkey = winreg.EnumKey(key, 0)  # always 0: we delete as we go
                except OSError:
                    break
                delete_key_recursive(hkey, f"{path}\\{subkey}")
        winreg.DeleteKey(hkey, path)
    except FileNotFoundError:
        pass


def add_context_menu(exe: str):
    icon = str(Path(exe).with_name('small.ico'))
    for key_path, items in menus(exe):
        delete_key_recursive(winreg.HKEY_CURRENT_USER, key_path)  # drop stale items from older versions
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.SetValueEx(key, "MUIVerb", 0, winreg.REG_SZ, "Convert to")
            winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, icon)
            winreg.SetValueEx(key, "SubCommands", 0, winreg.REG_SZ, "")
            winreg.SetValueEx(key, "MultiSelectModel", 0, winreg.REG_SZ, "Player")
        for i, (label, command) in enumerate(items):
            sub = f"{key_path}\\shell\\item_{i:02d}"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, sub) as key:
                winreg.SetValueEx(key, "MUIVerb", 0, winreg.REG_SZ, label)
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"{sub}\\command") as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command)
    print(f"Context menu added (converter: {exe})")


def remove_context_menu():
    for key_path, _ in menus(DEFAULT_EXE):
        delete_key_recursive(winreg.HKEY_CURRENT_USER, key_path)
    print("Context menu removed")


def is_installed() -> bool:
    try:
        winreg.OpenKey(winreg.HKEY_CURRENT_USER, FILE_KEY.format(ext='png')).Close()
        return True
    except FileNotFoundError:
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('action', nargs='?', choices=['add', 'remove'], help='default: toggle')
    parser.add_argument('--exe', default=DEFAULT_EXE, help='path to converter.exe')
    args = parser.parse_args()

    action = args.action or ('remove' if is_installed() else 'add')
    if action == 'add':
        if not Path(args.exe).exists():
            print(f"Warning: {args.exe} doesn't exist yet")
        add_context_menu(args.exe)
    else:
        remove_context_menu()
