"""
Remove the space padding Inno Setup leaves in Setup.exe's version strings.

Inno writes each version string (ProductName, ProductVersion, ...) into a
fixed-size placeholder and pads the rest with spaces, so Setup.exe reports
"PocketConverter          ". SignPath compares product name and version
exactly, so the padding is replaced with NUL characters in place: the file
keeps its size and layout, and every reader sees the exact string.

Usage: python installer/trim_version_info.py <Setup.exe>
"""

import struct
import sys
from pathlib import Path

VERSION_KEY = 'VS_VERSION_INFO'.encode('utf-16-le')


def _u16(data, pos):
    return struct.unpack_from('<H', data, pos)[0]


def _align4(pos, base):
    return pos + (-(pos - base) % 4)


def _read_key(data, pos):
    end = pos
    while data[end:end + 2] != b'\0\0':
        end += 2
    return data[pos:end].decode('utf-16-le'), end + 2


def _blocks(data, start, end):
    """Yield (offset, wLength, wValueLength, wType, key, value_offset) for sibling blocks."""
    pos = start
    while pos + 6 <= end:
        length = _u16(data, pos)
        if length == 0:
            break
        key, after_key = _read_key(data, pos + 6)
        yield pos, length, _u16(data, pos + 2), _u16(data, pos + 4), key, _align4(after_key, start)
        pos = _align4(pos + length, start)


def trim(data: bytearray) -> list:
    root = data.find(VERSION_KEY) - 6
    if root < 0:
        raise ValueError("no version resource found")
    length, fixed_size = _u16(data, root), _u16(data, root + 2)
    _, after_key = _read_key(data, root + 6)
    children = _align4(_align4(after_key, root) + fixed_size, root)

    changed = []
    for _, _, _, _, sfi_key, sfi_children in _blocks(data, children, root + length):
        if sfi_key != 'StringFileInfo':
            continue
        for table, table_len, _, _, _, table_children in _blocks(data, sfi_children, root + length):
            for entry, entry_len, value_len, _, key, value_pos in _blocks(data, table_children, table + table_len):
                value, _ = _read_key(data, value_pos)
                trimmed = value.rstrip(' ')
                if trimmed == value:
                    continue
                start = value_pos + len(trimmed) * 2
                data[start:value_pos + len(value) * 2] = b'\0' * ((len(value) - len(trimmed)) * 2)
                struct.pack_into('<H', data, entry + 2, len(trimmed) + 1)  # wValueLength incl. NUL
                changed.append(f"{key}={trimmed!r}")
            break
        break
    return changed


def main():
    path = Path(sys.argv[1])
    data = bytearray(path.read_bytes())
    changed = trim(data)
    path.write_bytes(data)
    print(f"{path.name}: trimmed {len(changed)} version string(s): " + ', '.join(changed))


if __name__ == '__main__':
    main()
