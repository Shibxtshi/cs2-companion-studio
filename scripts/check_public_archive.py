#!/usr/bin/env python3
"""Reject private or generated material from a distributable source ZIP."""
import argparse
import stat
import zipfile
from pathlib import PurePosixPath

PRIVATE_CONTEXT_FILES = {
    'AGENTS.md', 'PROJECT_CONTEXT.md', 'DECISIONS.md',
    'LOCAL_WORK_PLAN.md', 'LOCAL_AUDIT_FIX_GUIDE.md',
}
PRIVATE_DIRS = {'.git', '.venv', '.installer-state', '__pycache__', '.pytest_cache'}
RUNTIME_DIRS = {'data', 'logs'}
PRIVATE_FILES = {'pin.txt', 'profiles.json', 'support-summary.json'}


def check_zip(file):
    with zipfile.ZipFile(file) as archive:
        for info in archive.infolist():
            normalized = info.filename.replace('\\', '/')
            path = PurePosixPath(normalized)
            parts = path.parts
            lowered = [part.lower() for part in parts]
            if path.is_absolute() or '..' in parts or any(':' in part for part in parts):
                raise ValueError('Unsafe archive path: ' + info.filename)
            if stat.S_ISLNK(info.external_attr >> 16):
                raise ValueError('Unsafe archive symlink: ' + info.filename)
            if any(part in PRIVATE_DIRS for part in lowered):
                raise ValueError('Private/generated directory: ' + info.filename)
            if any(part.startswith('.env') and part != '.env.example' for part in lowered):
                raise ValueError('Private environment in ZIP: ' + info.filename)
            if any(part in RUNTIME_DIRS for part in lowered):
                # Empty scaffolding is safe; runtime contents are never distributable.
                if info.is_dir():
                    continue
                if path.name == '.gitkeep' and info.file_size == 0:
                    continue
                raise ValueError('Private runtime file: ' + info.filename)
            name = path.name.lower()
            if (name in {value.lower() for value in PRIVATE_CONTEXT_FILES} or name in PRIVATE_FILES
                    or name.startswith('.companion-write-')
                    or name.endswith(('.bak', '.log', '.jsonl')) or '.corrupt-' in name
                    or (name.startswith('gamestate_integration_') and name.endswith('.cfg'))):
                raise ValueError('Private/generated file: ' + info.filename)
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('zip_path')
    args = parser.parse_args()
    check_zip(args.zip_path)
    print('OK: archive contains no prohibited private/generated paths')
