import os
import winreg
import sys
import ctypes
from win11toast import toast

all_list = ['mp4', 'gif', 'txt', 'pdf', 'docx', 'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'ico', 'webp']
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(__file__)
icon_dir = os.path.join(base_path, 'logo.ico')


def run_as_admin():
    if not ctypes.windll.shell32.IsUserAnAdmin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)


def check_registry_key():
    registry_path = r"Software\Classes\SystemFileAssociations\.webp\shell\PocketConverter"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path):
            pass
        return True
    except FileNotFoundError:
        return False


def get_extensions(extension):
    # Get convert variants for each extension
    ext = [['mp4', 'gif'], ['txt', 'pdf', 'docx'], ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'webp', 'ico'], ['jpg', 'png', 'webp', 'ico']]
    for exts in ext:
        if extension in exts:
            if len(exts) == len(ext[2]):
                ext = ext[3]
                if extension in ext:
                    ext.remove(extension)
                return ext
            else:
                exts.remove(extension)
                if extension == 'gif':
                    exts.append('pngs')
                    exts.append('png')
                if extension == 'mp4':
                    exts.append('mp3')
                return exts


def remove_context_menu():
    try:
        key_path = r"Directory\shell\PocketConverter"
        for i in range(2):
            subkey_path = key_path + fr"\shell\sub_one_{i}"
            winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, subkey_path + r"\command")
            winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, subkey_path)
        winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, key_path + r"\shell")
        winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, key_path)
        for extension in [i for i in all_list]:
            key_path = fr"Software\Classes\SystemFileAssociations\.{extension}\shell\PocketConverter"
            for c in range(len(get_extensions(extension))):
                subkey_path = key_path + fr"\shell\sub_one_{c}"
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, subkey_path + r"\command")
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, subkey_path)
                c += 1
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path + r"\shell")
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
    except FileNotFoundError:
        pass
    except Exception as e:
        toast("Error", e, icon=icon_dir, group='done')


if __name__ == "__main__":
    try:
        run_as_admin()
        if check_registry_key():
            if ctypes.windll.shell32.IsUserAnAdmin():
                remove_context_menu()
                toast("Context menu was deleted", "Bye! Hope to see you soon", icon=icon_dir, group='done')
        else:
            toast("Start Error", "Menu was already removed", icon=icon_dir, group='done')
    except Exception as e:
        toast("Start Error", e, icon=icon_dir)
