#!/usr/bin/env python3
"""Explicit offline profile recovery. Stop the server/container before restoring."""
import argparse
import os
from pathlib import Path
import secrets
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from profile_store import atomic_write, read_document


def restore(directory):
    directory = Path(directory)
    current = directory / 'profiles.json'
    backup = directory / 'profiles.json.bak'
    read_document(backup)  # Refuse invalid backups before touching any file.
    if current.exists():
        preserved = directory / ('profiles.json.corrupt-' + secrets.token_hex(8))
        atomic_write(preserved, current.read_bytes())
    atomic_write(current, backup.read_bytes())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=Path(os.environ.get('PROFILE_DATA_DIR', Path(__file__).resolve().parents[1] / 'data')))
    parser.add_argument('--restore', action='store_true', help='Explicitly restore the validated backup; stop the service first.')
    args = parser.parse_args()
    if not args.restore:
        parser.error('--restore is required; no files have been changed')
    try:
        restore(args.data_dir)
    except (OSError, ValueError, UnicodeError):
        parser.exit(1, 'Recovery failed. Preserve private files and check the backup and directory permissions.\n')
    print('Profiles restored from a validated backup. The previous current file was preserved when present. Keep all recovery files private.')


if __name__ == '__main__':
    main()
