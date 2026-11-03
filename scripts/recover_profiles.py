#!/usr/bin/env python3
"""Explicit offline recovery. Stop the server/container before changing profiles."""
import argparse
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from companion.localization import Translator

tr = Translator().text

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
    print(tr('maintenance.snapshotReady'))
    try:
        return input(tr('maintenance.confirm', expected=expected)).strip() == expected
    except EOFError:
        return False


def main():
    global tr
    preliminary = argparse.ArgumentParser(add_help=False)
    preliminary.add_argument('--language', default='EN', choices=list(Translator().languages))
    language, _remaining = preliminary.parse_known_args()
    tr = Translator(language.language).text
    parser = argparse.ArgumentParser(description=tr('maintenance.description'), parents=[preliminary])
    parser.add_argument('--data-dir', type=Path, default=Path(os.environ.get(
        'PROFILE_DATA_DIR', Path(__file__).resolve().parents[1] / 'data')))
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument('--restore', action='store_true', help=tr('maintenance.help.restore'))
    actions.add_argument('--inspect', action='store_true', help=tr('maintenance.help.inspect'))
    actions.add_argument('--prepare-reset', action='store_true', help=tr('maintenance.help.prepareReset'))
    actions.add_argument('--reset', metavar='BACKUP_ID', help=tr('maintenance.help.reset'))
    actions.add_argument('--inspect-reset', metavar='BACKUP_ID', help=tr('maintenance.help.inspectReset'))
    actions.add_argument('--restore-reset', metavar='BACKUP_ID', help=tr('maintenance.help.restoreReset'))
    actions.add_argument('--prepare-activation', action='store_true', help=tr('maintenance.help.prepareActivation'))
    actions.add_argument('--activate', metavar='BACKUP_ID', help=tr('maintenance.help.activate'))
    actions.add_argument('--inspect-activation', metavar='BACKUP_ID', help=tr('maintenance.help.inspectActivation'))
    actions.add_argument('--restore-activation', metavar='BACKUP_ID', help=tr('maintenance.help.restoreActivation'))
    actions.add_argument('--initialize-target', action='store_true', help=tr('maintenance.help.initialize'))
    actions.add_argument('--restore-target', action='store_true', help=tr('maintenance.help.restoreTarget'))
    parser.add_argument('--application-revision', help=tr('maintenance.help.revision'))
    parser.add_argument('--service-stopped', action='store_true', help=tr('maintenance.help.stopped'))
    args = parser.parse_args()
    if (args.prepare_reset or args.reset or args.restore_reset or args.prepare_activation or args.activate
            or args.restore_activation or args.initialize_target or args.restore_target) and not args.service_stopped:
        parser.error(tr('maintenance.stopFirst'))
    try:
        if (args.reset or args.restore or args.restore_reset or args.activate or args.initialize_target or args.restore_target):
            if any(args.data_dir.glob('.profiles-restore-*.pending')):
                raise RecoveryError('restore_interrupted_keep_service_stopped')
        if (args.reset or args.restore_reset or args.restore) and inspect_current(args.data_dir).get('status') == 'recognized':
            raise RecoveryError('target_requires_activation_recovery')
        if args.restore_target:
            print(tr('maintenance.restoreTargetWarning'))
            restored, safetyId = restore_target_backup(args.data_dir, confirm)
            print(tr('maintenance.targetRestored') if restored else tr('maintenance.cancelledCurrent'))
            print(tr('maintenance.safetyId', id=safetyId))
        elif args.prepare_activation:
            backupId = prepare_activation(args.data_dir, args.application_revision)
            print(tr('maintenance.backupPath', path=str(args.data_dir.absolute() / 'profile-reset-backups' / backupId)))
            print(tr('maintenance.candidateId', id=backupId))
            print(tr('maintenance.retainImage'))
        elif args.inspect_activation:
            print(tr('maintenance.activationState', state=activation_state(args.data_dir, args.inspect_activation)))
        elif args.activate:
            print(tr('maintenance.resetWarning'))
            print(tr('maintenance.privatePreserved'))
            print(tr('maintenance.stopWriters'))
            applied = activate_profiles(args.data_dir, args.activate, confirm)
            print(tr('maintenance.targetInstalled') if applied else tr('maintenance.cancelledHistorical'))
        elif args.restore_activation:
            print(tr('maintenance.restoreWarning'))
            print(tr('maintenance.laterPublications'))
            restored, safetyId, revision = restore_activation(args.data_dir, args.restore_activation, confirm)
            print(tr('maintenance.historicalRestored') if restored else tr('maintenance.cancelledFiles'))
            print(tr('maintenance.revision', revision=revision))
            if safetyId:
                print(tr('maintenance.safetyId', id=safetyId))
        elif args.initialize_target:
            print(tr('maintenance.initializeWarning'))
            print(tr('maintenance.initialized') if initialize_target(args.data_dir, confirm) else tr('maintenance.cancelledNoTarget'))
        elif args.inspect:
            result = inspect_current(args.data_dir)
            print(tr('maintenance.classification', status=result['status'], kind=result['kind']))
            print(tr('maintenance.inspectPolicy'))
        elif args.inspect_reset:
            print(tr('maintenance.resetState', state=reset_state(args.data_dir, args.inspect_reset)))
        elif args.prepare_reset:
            backupId = prepare_reset(args.data_dir)
            print(tr('maintenance.backupId', id=backupId))
            print(tr('maintenance.notReset'))
        elif args.reset:
            if inspect_current(args.data_dir).get('status') == 'recognized':
                raise RecoveryError('target_requires_activation_recovery')
            if reset_profiles(args.data_dir, args.reset, confirm):
                print(tr('maintenance.historicalReset'))
            else:
                print(tr('maintenance.cancelledSnapshot'))
        elif args.restore_reset:
            restored, safetyId = restore_reset(args.data_dir, args.restore_reset, confirm)
            print(tr('maintenance.bytesRestored') if restored else tr('maintenance.cancelledProfiles'))
            if safetyId:
                print(tr('maintenance.previousSnapshot', id=safetyId))
            print(tr('maintenance.restoredCompatibility'))
        else:
            restore(args.data_dir)
            print(tr('maintenance.restored'))
    except (OSError, ValueError, UnicodeError) as error:
        code = error.code if isinstance(error, RecoveryError) else 'io_or_invalid_data'
        if code in ('activation_already_attempted', 'activation_prepare_again'):
            print(tr('maintenance.newAttempt'))
        parser.exit(1, tr('maintenance.failed', code=code))
    except KeyboardInterrupt:
        parser.exit(1, tr('maintenance.interrupted'))


if __name__ == '__main__':
    main()
