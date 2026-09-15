"""
Generates a REGEDIT5-compatible .reg file directly from CONVERSION_MAP /
MENU_LABELS in remove_context_menu.py, with noremal structure and
formatting.

Usage:
    python generate_reg_file.py > Pocket.reg
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from remove_context_menu import CONVERSION_MAP, MENU_LABELS, EXE_PATH, ICON_PATH


def esc(s: str) -> str:
    """.reg string values escape backslashes and double quotes."""
    return s.replace('\\', '\\\\').replace('"', '\\"')


def block(lines_out: list, key_path: str, values: list = None):
    """
    Append one [key] block.
    `values` is a list of (name, data) tuples; name=None means the
    default value (@="..."). No values -> a bare empty key declaration.
    """
    lines_out.append(f'[{key_path}]')
    for name, data in (values or []):
        if name is None:
            lines_out.append(f'@="{esc(data)}"')
        else:
            lines_out.append(f'"{name}"="{esc(data)}"')
    lines_out.append('')  # exactly one blank line before the next block


def emit_menu(lines_out: list, base_path: str, targets: list,
              command_fmt: str, include_precursor_keys: bool):
    if include_precursor_keys:
        parent = base_path.rsplit('\\shell\\PocketConverter', 1)[0]
        block(lines_out, parent)
        block(lines_out, f'{parent}\\shell')

    block(lines_out, base_path, [
        ('MUIVerb', 'Convert to'),
        ('Icon', ICON_PATH),
        ('SubCommands', ''),
        ('MultiSelectModel', 'Single'),
    ])
    block(lines_out, f'{base_path}\\shell')

    for i, target in enumerate(targets):
        label = MENU_LABELS.get(target, target)
        sub_path = f'{base_path}\\shell\\sub_one_{i}'
        block(lines_out, sub_path, [('MUIVerb', label)])
        block(lines_out, f'{sub_path}\\command', [(None, command_fmt.format(target=target))])


def main():
    lines = ['Windows Registry Editor Version 5.00', '']

    for ext, targets in CONVERSION_MAP.items():
        base_path = f'HKEY_CURRENT_USER\\Software\\Classes\\SystemFileAssociations\\.{ext}\\shell\\PocketConverter'
        cmd_fmt = f'{EXE_PATH} "%1" {{target}}'
        emit_menu(lines, base_path, targets, cmd_fmt, include_precursor_keys=True)

    dir_base = 'HKEY_CLASSES_ROOT\\Directory\\shell\\PocketConverter'
    cmd_fmt = f'{EXE_PATH} "%V" folder{{target}}'
    emit_menu(lines, dir_base, ['pdf', 'gif'], cmd_fmt, include_precursor_keys=False)

    while lines and lines[-1] == '':
        lines.pop()

    sys.stdout.write('\n'.join(lines) + '\n')


if __name__ == '__main__':
    main()
