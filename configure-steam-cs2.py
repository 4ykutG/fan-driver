#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Safely add the MSI/GameMode/NVIDIA wrapper to CS2's Steam config."""

import datetime
import os
import pathlib
import re
import shutil
import sys
import tempfile

TARGET_PATH = ('UserLocalConfigStore', 'Software', 'Valve', 'Steam', 'apps', '730')
LAUNCH_COMMAND = 'msi-game-run %command%'
KEY_ONLY = re.compile(r'^\s*"((?:\\.|[^"\\])*)"\s*$')
KEY_VALUE = re.compile(
    r'^(\s*)"((?:\\.|[^"\\])*)"\s+"((?:\\.|[^"\\])*)"\s*$')


def configure(path):
    text = path.read_text(encoding='utf-8')
    lines = text.splitlines(keepends=True)
    stack = []
    pending_key = None
    target_open = False
    launch_line = None
    close_line = None
    target_indent = None

    for index, line in enumerate(lines):
        stripped = line.strip()
        key_only = KEY_ONLY.match(line.rstrip('\r\n'))
        key_value = KEY_VALUE.match(line.rstrip('\r\n'))

        if key_value:
            if tuple(stack) == TARGET_PATH and key_value.group(2) == 'LaunchOptions':
                launch_line = index
                target_indent = key_value.group(1)
            pending_key = None
        elif key_only:
            pending_key = key_only.group(1)
        elif stripped == '{':
            if pending_key is None:
                raise RuntimeError(f'Unexpected opening brace at line {index + 1}')
            stack.append(pending_key)
            pending_key = None
            if tuple(stack) == TARGET_PATH:
                target_open = True
        elif stripped == '}':
            if tuple(stack) == TARGET_PATH:
                close_line = index
                target_indent = target_indent or (
                    line[:len(line) - len(line.lstrip())] + '\t')
            if stack:
                stack.pop()
            pending_key = None
        elif stripped and not stripped.startswith('//'):
            pending_key = None

    if not target_open or close_line is None:
        raise RuntimeError('CS2 app 730 block was not found in localconfig.vdf')

    newline = '\r\n' if '\r\n' in text else '\n'
    replacement = f'{target_indent}"LaunchOptions"\t\t"{LAUNCH_COMMAND}"{newline}'
    if launch_line is None:
        lines.insert(close_line, replacement)
    else:
        match = KEY_VALUE.match(lines[launch_line].rstrip('\r\n'))
        current = match.group(3)
        if current == LAUNCH_COMMAND:
            print(f'CS2 launch options already configured: {path}')
            return False
        if 'msi-game-run' in current:
            replacement = f'{target_indent}"LaunchOptions"\t\t"{current}"{newline}'
        elif '%command%' in current:
            current = current.replace('%command%', LAUNCH_COMMAND, 1)
            replacement = f'{target_indent}"LaunchOptions"\t\t"{current}"{newline}'
        elif current:
            replacement = (
                f'{target_indent}"LaunchOptions"\t\t'
                f'"{LAUNCH_COMMAND} {current}"{newline}')
        lines[launch_line] = replacement

    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    backup = path.with_name(f'{path.name}.backup-{stamp}')
    shutil.copy2(path, backup)

    fd, temporary = tempfile.mkstemp(prefix=f'.{path.name}.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as output:
            output.writelines(lines)
            output.flush()
            os.fsync(output.fileno())
        os.chmod(temporary, path.stat().st_mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

    print(f'Configured CS2 launch options: {path}')
    print(f'Backup: {backup}')
    return True


def main():
    home = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path.home())
    roots = (home / '.local/share/Steam/userdata', home / '.steam/steam/userdata')
    configs = []
    for root in roots:
        if root.is_dir():
            configs.extend(root.glob('*/config/localconfig.vdf'))
    unique = sorted(set(path.resolve() for path in configs))
    if not unique:
        raise RuntimeError('No Steam localconfig.vdf was found')
    for path in unique:
        configure(path)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError) as error:
        print(f'configure-steam-cs2: {error}', file=sys.stderr)
        raise SystemExit(1)
