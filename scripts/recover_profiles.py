#!/usr/bin/env python3
"""Explicit offline recovery. Stop the server/container before changing profiles."""
import argparse
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from companion.profile_recovery import (
    RecoveryError, inspect_current, prepare_reset, reset_profiles, reset_state,
    restore_legacy, restore_reset,
)


def restore(directory):
    """Retain the existing validated rotating-backup recovery interface."""
    return restore_legacy(directory)


def confirm(expected):
    print('A verified private snapshot is available. No other private settings will be reset.')
    try:
        return input('Type exactly ' + expected + ' to continue, or press Enter to cancel: ').strip() == expected
    except EOFError:
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=Path(os.environ.get(
        'PROFILE_DATA_DIR', Path(__file__).resolve().parents[1] / 'data')))
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument('--restore', action='store_true', help='Restore a validated current-format .bak; stop the service first.')
    actions.add_argument('--inspect', action='store_true', help='Read-only format classification; never print profile contents.')
    actions.add_argument('--prepare-reset', action='store_true', help='Create and verify a distinct private snapshot, without resetting.')
    actions.add_argument('--reset', metavar='BACKUP_ID', help='Confirm resetting to the CURRENT usable format, using a verified snapshot.')
    actions.add_argument('--inspect-reset', metavar='BACKUP_ID', help='Read-only status after interruption: prepared/applied/changed/missing.')
    actions.add_argument('--restore-reset', metavar='BACKUP_ID', help='Confirm restoring exact original bytes, possibly incompatible with this version.')
    parser.add_argument('--service-stopped', action='store_true', help='Explicit acknowledgement that the service/container is stopped; not a liveness probe.')
    args = parser.parse_args()
    if (args.prepare_reset or args.reset or args.restore_reset) and not args.service_stopped:
        parser.error('stop the service and pass --service-stopped; no files have been changed')
    try:
        if args.inspect:
            result = inspect_current(args.data_dir)
            print('Profile classification: ' + result['status'] + '; contract: ' + str(result['kind']))
            print('P3 still uses the unversioned current server format; target contracts are not active.')
        elif args.inspect_reset:
            print('Reset state: ' + reset_state(args.data_dir, args.inspect_reset))
        elif args.prepare_reset:
            backupId = prepare_reset(args.data_dir)
            print('Verified private backup ID: ' + backupId)
            print('No reset performed. Keep the snapshot private; .env and unrelated files were not copied.')
        elif args.reset:
            if reset_profiles(args.data_dir, args.reset, confirm):
                print('Current-format profiles reset and validated. The verified snapshot and rotating .bak were retained.')
            else:
                print('Cancelled. Profiles unchanged; the verified snapshot was retained.')
        elif args.restore_reset:
            restored, safetyId = restore_reset(args.data_dir, args.restore_reset, confirm)
            print('Original bytes restored.' if restored else 'Cancelled. Profiles unchanged.')
            if safetyId:
                print('Previous current-file snapshot ID: ' + safetyId)
            print('Raw restored bytes may require their original software version. The rotating .bak was not changed.')
        else:
            restore(args.data_dir)
            print('Profiles restored from a validated backup. The previous current file was preserved when present. Keep all recovery files private.')
    except (OSError, ValueError, UnicodeError) as error:
        code = error.code if isinstance(error, RecoveryError) else 'io_or_invalid_data'
        parser.exit(1, 'Recovery refused or failed (' + code + '). Keep all snapshots; inspect the reset state before retrying.\n')
    except KeyboardInterrupt:
        parser.exit(1, 'Interrupted. Keep all snapshots and inspect the reset state before retrying.\n')


if __name__ == '__main__':
    main()
