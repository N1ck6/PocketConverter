"""
Generates the Inno Setup [Registry] fragment for the "Convert to" menus from
converter_app/formats.py, so the installer can never drift from what
converter.py actually supports. Never edit registry_generated.iss by hand.

Usage (build.ps1 runs this automatically):
    python installer/generate_registry_iss.py installer/registry_generated.iss
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from converter_app.formats import CONVERSION_MAP, FOLDER_LABELS, FOLDER_TARGETS, menu_label  # noqa: E402

TASK = 'contextmenu'
EXE = '"{app}\\converter.exe"'


def esc(s: str) -> str:
    """Inno Setup escapes embedded double quotes by doubling them; '{' starts a constant."""
    return s.replace('"', '""').replace('{', '{{')


def menu_entries(key: str, items: list) -> list:
    """
    One cascading "Convert to" menu. HKA = HKLM for an all-users install,
    HKCU for a per-user one. `items` is a list of (label, arguments).
    """
    def entry(subkey, name, data, flags=''):
        flags = f'; Flags: {flags}' if flags else ''
        return (f'Root: HKA; Subkey: "{subkey}"; ValueType: string; ValueName: "{name}"; '
                f'ValueData: "{data}"; Tasks: {TASK}{flags}')

    lines = [
        # deletekey first wipes items left over from an older version;
        # uninsdeletekey removes the whole tree on uninstall
        entry(key, 'MUIVerb', 'Convert to', 'deletekey uninsdeletekey'),
        entry(key, 'Icon', '{app}\\small.ico'),
        entry(key, 'SubCommands', ''),
        # "Player" = shown for any number of selected files (default hides it above 15;
        # v1.x used "Single", which hid it as soon as two files were selected)
        entry(key, 'MultiSelectModel', 'Player'),
    ]
    for i, (label, args) in enumerate(items):
        sub = f'{key}\\shell\\item_{i:02d}'  # Explorer sorts sub-keys by name
        lines.append(entry(sub, 'MUIVerb', esc(label)))
        lines.append(entry(f'{sub}\\command', '', f'{EXE} {args}'.replace('"', '""')))
    # Unticking the task on an upgrade must remove menus a previous install added
    lines.append(f'Root: HKA; Subkey: "{key}"; Flags: deletekey dontcreatekey; Tasks: not {TASK}')
    # v1.x wrote per-user keys even for all-users installs; they would duplicate the menu
    lines.append(f'Root: HKCU; Subkey: "{key}"; Flags: deletekey dontcreatekey; Check: IsAdminInstallMode')
    return lines


def render() -> str:
    out = [
        '; ============================================================',
        '; AUTO-GENERATED from converter_app/formats.py',
        '; Do not edit by hand - re-run installer/generate_registry_iss.py.',
        '; ============================================================',
        '',
    ]
    for ext, targets in CONVERSION_MAP.items():
        out.append(f'; --- .{ext} ---')
        key = f'Software\\Classes\\SystemFileAssociations\\.{ext}\\shell\\PocketConverter'
        out.extend(menu_entries(key, [(menu_label(ext, t), f'"%1" {t}') for t in targets]))
        out.append('')

    out.append('; --- Folders ---')
    out.extend(menu_entries('Software\\Classes\\Directory\\shell\\PocketConverter',
                            [(FOLDER_LABELS.get(t, t.upper()), f'"%V" folder{t}') for t in FOLDER_TARGETS]))
    return '\n'.join(out) + '\n'


def main():
    text = render()
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(text, encoding='utf-8-sig')  # BOM: Inno reads it as UTF-8
    else:
        sys.stdout.write(text)


if __name__ == '__main__':
    main()
