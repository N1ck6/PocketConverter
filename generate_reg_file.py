"""
Generates Pocket.reg — a double-clickable alternative to the installer for
people who copy converter.exe manually. Built from the same tables as the
installer (converter_app/formats.py), per-user only (no admin needed).

Usage:
    python generate_reg_file.py                     # writes Pocket.reg
    python generate_reg_file.py out.reg --exe "D:\\Tools\\PocketConverter\\converter.exe"
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from remove_context_menu import DEFAULT_EXE, menus  # noqa: E402


def esc(s: str) -> str:
    """.reg string values escape backslashes and double quotes."""
    return s.replace('\\', '\\\\').replace('"', '\\"')


def render(exe: str) -> str:
    icon = str(Path(exe).with_name('small.ico'))
    lines = ['Windows Registry Editor Version 5.00', '']
    for key_path, items in menus(exe):
        full = f'HKEY_CURRENT_USER\\{key_path}'
        lines += [f'[-{full}]', '']  # remove any older version of this menu first
        lines += [f'[{full}]', '"MUIVerb"="Convert to"', f'"Icon"="{esc(icon)}"',
                  '"SubCommands"=""', '"MultiSelectModel"="Player"', '']
        for i, (label, command) in enumerate(items):
            sub = f'{full}\\shell\\item_{i:02d}'
            lines += [f'[{sub}]', f'"MUIVerb"="{esc(label)}"', '']
            lines += [f'[{sub}\\command]', f'@="{esc(command)}"', '']
    return '\r\n'.join(lines).rstrip() + '\r\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('output', nargs='?', default='Pocket.reg')
    parser.add_argument('--exe', default=DEFAULT_EXE)
    args = parser.parse_args()
    # regedit's native format is UTF-16 LE with BOM
    Path(args.output).write_bytes(render(args.exe).encode('utf-16'))
    print(f"Wrote {args.output}")
