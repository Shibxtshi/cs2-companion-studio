#!/usr/bin/env python3
"""Reject release zip files that accidentally contain private config or runtime state."""
import argparse
import re
import zipfile
from pathlib import PurePosixPath

DENIED_FILES = {'.env', 'PIN.txt', 'profiles.json', 'support-summary.json',
                'events.jsonl', 'events.previous.jsonl'}
DENIED_DIRS = {'.git', '.venv', '.installer-state', '__pycache__'}


def check_zip(file):
    with zipfile.ZipFile(file) as archive:
        for name in archive.namelist():
            path = PurePosixPath(name)
            if path.name in DENIED_FILES or any(p in DENIED_DIRS for p in path.parts):
                raise ValueError(f'Private/generated file present: {name}')
            if path.name.startswith('gamestate_integration_') and path.suffix == '.cfg':
                raise ValueError(f'Generated GSI token file present: {name}')
            if re.search(r'(?i)(^|/)\.env(?!\.example)(?:$|/)', name):
                raise ValueError(f'Private environment in ZIP: {name}')
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('zip_path')
    args = parser.parse_args()
    check_zip(args.zip_path)
    print('OK: archive has no known secrets or private runtime data')
