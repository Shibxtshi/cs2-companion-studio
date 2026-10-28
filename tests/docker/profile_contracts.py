"""Check packaged contracts/recovery using only disposable container /tmp files."""
import subprocess
import textwrap


def main():
    code = textwrap.dedent('''
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from companion.profile_contracts import encode_document, new_server_document
        from companion.profile_operations import apply_operation
        from companion.profile_recovery import prepare_reset, reset_profiles, reset_state, restore_reset
        from companion.profile_store import read_document

        document = new_server_document()
        command = {
            'format': 'ccs-dashboard-operation', 'version': 1,
            'storeId': document['storeId'], 'operationId': 'a' * 32,
            'kind': 'update', 'profileId': document['profiles'][0]['id'],
            'expectedRevision': 1,
            'profile': {key: document['profiles'][0][key] for key in ('name', 'configuration')},
        }
        updated, receipt = apply_operation(document, command)
        assert updated['profiles'][0]['revision'] == 2
        assert not receipt['replayed']
        replayed, receipt = apply_operation(updated, command)
        assert replayed == updated and receipt['replayed']
        with TemporaryDirectory(prefix='ccs-contracts-', dir='/tmp') as temporary:
            directory = Path(temporary)
            original = encode_document(document)
            (directory / 'profiles.json').write_bytes(original)
            (directory / '.env').write_bytes(b'synthetic-setting=keep')
            backupId = prepare_reset(directory)
            assert not reset_profiles(directory, backupId, lambda expected: False)
            assert reset_profiles(directory, backupId, lambda expected: expected == 'RESET ' + backupId)
            assert reset_state(directory, backupId) == 'applied'
            assert len(read_document(directory / 'profiles.json')[0]['profiles'][0]['widgets']) == 5
            restored, safetyId = restore_reset(directory, backupId, lambda expected: expected == 'RESTORE ' + backupId)
            assert restored and safetyId
            assert (directory / 'profiles.json').read_bytes() == original
            assert (directory / '.env').read_bytes() == b'synthetic-setting=keep'
        print('Packaged contracts and offline recovery passed with isolated temporary data.')
    ''')
    subprocess.run(['docker', 'compose', 'exec', '-T', 'cs2-companion-studio', 'python', '-'],
                   input=code, text=True, check=True, timeout=60)


if __name__ == '__main__':
    main()
