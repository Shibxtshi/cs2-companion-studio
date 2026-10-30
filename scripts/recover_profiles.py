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
from companion.profile_activation import (
    prepare_activation, activate_profiles, activation_state, restore_activation, initialize_target, restore_target_backup,
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
    actions.add_argument('--prepare-activation', action='store_true', help='Verify historical files and prepare a private target candidate; do not activate.')
    actions.add_argument('--activate', metavar='BACKUP_ID', help='Explicitly replace verified historical profiles with the prepared target generation.')
    actions.add_argument('--inspect-activation', metavar='BACKUP_ID', help='Read-only activation/interruption classification.')
    actions.add_argument('--restore-activation', metavar='BACKUP_ID', help='Restore both original profile files after preserving the current state.')
    actions.add_argument('--initialize-target', action='store_true', help='Explicit first-install initialization in an empty data directory only.')
    actions.add_argument('--restore-target', action='store_true', help='Restore validated target .bak into a new generation after preserving current bytes.')
    parser.add_argument('--application-revision', help='Exact 40-character historical application commit retained for rollback.')
    parser.add_argument('--service-stopped', action='store_true', help='Explicit acknowledgement that the service/container is stopped; not a liveness probe.')
    args = parser.parse_args()
    if (args.prepare_reset or args.reset or args.restore_reset or args.prepare_activation or args.activate
            or args.restore_activation or args.initialize_target or args.restore_target) and not args.service_stopped:
        parser.error('stop the service and pass --service-stopped; no files have been changed')
    try:
        if (args.reset or args.restore_reset or args.restore) and inspect_current(args.data_dir).get('status') == 'recognized':
            raise RecoveryError('target_requires_activation_recovery')
        if args.restore_target:
            print('Restore target backup configuration into a NEW generation. Later publications are not included; old drafts/intents are not adopted.')
            restored, safetyId = restore_target_backup(args.data_dir, confirm)
            print('Target backup restored and validated.' if restored else 'Cancelled. Current profiles unchanged.')
            print('Pre-restore private snapshot ID: ' + safetyId)
        elif args.prepare_activation:
            backupId = prepare_activation(args.data_dir, args.application_revision)
            print('Verified private backup: ' + str(args.data_dir.absolute() / 'profile-reset-backups' / backupId))
            print('Activation candidate ID: ' + backupId + '. No activation performed.')
            print('Keep the matching application/image revision available. Credentials and unrelated files were not copied.')
        elif args.inspect_activation:
            print('Activation state: ' + activation_state(args.data_dir, args.inspect_activation))
        elif args.activate:
            print('This resets ALL historical profile layouts, names and customizations to a new empty target profile.')
            print('The verified private backup remains available. PIN, GSI token, .env and unrelated data stay unchanged.')
            print('Stop all old tabs and writers; run only a compatible application after activation.')
            applied = activate_profiles(args.data_dir, args.activate, confirm)
            print('Target generation installed and validated.' if applied else 'Cancelled. Historical profiles unchanged.')
        elif args.restore_activation:
            print('Restore requires a stopped service and the retained compatible application/image.')
            print('If target publications succeeded, they will not appear in the historical state. Their snapshot is retained.')
            restored, safetyId, revision = restore_activation(args.data_dir, args.restore_activation, confirm)
            print('Historical files restored.' if restored else 'Cancelled. Current files unchanged.')
            print('Retained compatible application revision: ' + revision)
            if safetyId:
                print('Pre-restore private snapshot ID: ' + safetyId)
        elif args.initialize_target:
            print('Initialize a new target generation only in an empty directory. Existing profiles are never replaced.')
            print('Target initialized.' if initialize_target(args.data_dir, confirm) else 'Cancelled. No target created.')
        elif args.inspect:
            result = inspect_current(args.data_dir)
            print('Profile classification: ' + result['status'] + '; contract: ' + str(result['kind']))
            print('The active runtime follows the validated file format; no inspection performs activation.')
        elif args.inspect_reset:
            print('Reset state: ' + reset_state(args.data_dir, args.inspect_reset))
        elif args.prepare_reset:
            backupId = prepare_reset(args.data_dir)
            print('Verified private backup ID: ' + backupId)
            print('No reset performed. Keep the snapshot private; .env and unrelated files were not copied.')
        elif args.reset:
            if inspect_current(args.data_dir).get('status') == 'recognized':
                raise RecoveryError('target_requires_activation_recovery')
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
