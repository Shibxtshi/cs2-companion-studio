"""Offline activation uses synthetic directories exclusively."""
import json

import pytest

from companion import profile_activation as activation
from companion.profile_contracts import decode_document, validate_contract
from companion.profile_recovery import RecoveryError, verify_backup, BACKUP_DIRECTORY
from companion.profile_runtime import create_runtime_store, runtime_lease
from tests.historical_profiles import HistoricalProfileFixture

REVISION = '2bde18cffbfa0956cf8400c4c867675df29ac4b2'


@pytest.fixture
def historical(tmp_path):
    store = HistoricalProfileFixture(tmp_path / 'profiles.json')
    original = store.path.read_bytes()
    (tmp_path / 'profiles.json.bak').write_bytes(original)
    (tmp_path / 'other-private.json').write_bytes(b'untouched synthetic private setting')
    return tmp_path, original


def test_activation_is_explicit_verified_and_reversible(historical):
    directory, original = historical
    first = activation.prepare_activation(directory, REVISION)
    second = activation.prepare_activation(directory, REVISION)
    assert first != second
    manifest = verify_backup(directory, first)
    assert manifest['files']['profiles.json']['size'] == len(original)
    assert (directory / BACKUP_DIRECTORY / first / 'profiles.json').read_bytes() == original
    assert not activation.activate_profiles(directory, first, lambda _: False)
    assert (directory / 'profiles.json').read_bytes() == original
    assert activation.activate_profiles(directory, first, lambda phrase: phrase == 'ACTIVATE ' + first)
    target = validate_contract(decode_document((directory / 'profiles.json').read_bytes()), 'server')
    assert target['profiles'][0]['configuration']['layout']['columns'] == 24
    assert activation.activation_state(directory, first) == 'activated'
    assert (directory / 'profiles.json.bak').read_bytes() == original
    assert create_runtime_store(directory).data['format'] == 'ccs-dashboard-store'
    restored, safetyId, revision = activation.restore_activation(directory, first, lambda _: True)
    assert restored and safetyId and revision == REVISION
    assert (directory / 'profiles.json').read_bytes() == original
    assert (directory / 'profiles.json.bak').read_bytes() == original
    assert (directory / 'other-private.json').read_bytes() == b'untouched synthetic private setting'
    with pytest.raises(RuntimeError, match='Historical profiles'):
        create_runtime_store(directory)


def test_source_changed_while_confirming_is_preserved(historical):
    directory, _ = historical
    backupId = activation.prepare_activation(directory, REVISION)
    changed = b'concurrent synthetic write'
    def confirm(_):
        (directory / 'profiles.json').write_bytes(changed)
        return True
    with pytest.raises(RecoveryError, match='source_changed'):
        activation.activate_profiles(directory, backupId, confirm)
    assert (directory / 'profiles.json').read_bytes() == changed


@pytest.mark.parametrize('corrupt', ['backup', 'candidate'])
def test_failed_integrity_never_replaces_source(historical, corrupt):
    directory, original = historical
    backupId = activation.prepare_activation(directory, REVISION)
    path = directory / BACKUP_DIRECTORY / backupId / 'profiles.json' if corrupt == 'backup' else directory / ('.profiles-activation-' + backupId + '.candidate')
    path.write_bytes(path.read_bytes() + b' ')
    with pytest.raises(ValueError):
        activation.activate_profiles(directory, backupId, lambda _: pytest.fail('Must fail before confirmation'))
    assert (directory / 'profiles.json').read_bytes() == original


def test_failed_install_preserves_original(historical, monkeypatch):
    directory, original = historical
    backupId = activation.prepare_activation(directory, REVISION)
    def fail(*args):
        raise OSError('synthetic disk failure')
    monkeypatch.setattr(activation, '_install', fail)
    with pytest.raises(OSError):
        activation.activate_profiles(directory, backupId, lambda _: True)
    assert (directory / 'profiles.json').read_bytes() == original


def test_interrupted_restore_blocks_startup_then_can_resume(historical, monkeypatch):
    directory, original = historical
    backupId = activation.prepare_activation(directory, REVISION)
    activation.activate_profiles(directory, backupId, lambda _: True)
    write = activation.atomic_write
    def interrupt(path, raw):
        if path.name.endswith('.bak'):
            raise OSError('synthetic interruption')
        write(path, raw)
    monkeypatch.setattr(activation, 'atomic_write', interrupt)
    with pytest.raises(OSError):
        activation.restore_activation(directory, backupId, lambda _: True)
    with pytest.raises(RuntimeError):
        create_runtime_store(directory)
    monkeypatch.setattr(activation, 'atomic_write', write)
    assert activation.restore_activation(directory, backupId, lambda _: True)[0]
    assert (directory / 'profiles.json').read_bytes() == original


def test_running_runtime_excludes_offline_tools(historical):
    directory, _ = historical
    backupId = activation.prepare_activation(directory, REVISION)
    activation.activate_profiles(directory, backupId, lambda _: True)
    store = create_runtime_store(directory)
    with runtime_lease(store):
        with pytest.raises(RecoveryError):
            activation.prepare_activation(directory, REVISION)


def test_empty_initialization_refuses_existing_data_and_cancel(tmp_path):
    assert not activation.initialize_target(tmp_path, lambda _: False)
    assert not (tmp_path / 'profiles.json').exists()
    assert activation.initialize_target(tmp_path, lambda phrase: phrase == 'INITIALIZE TARGET')
    original = (tmp_path / 'profiles.json').read_bytes()
    with pytest.raises(RecoveryError):
        activation.initialize_target(tmp_path, lambda _: True)
    assert (tmp_path / 'profiles.json').read_bytes() == original


def test_future_version_fails_without_reset(tmp_path):
    document = activation.target_document()
    document['version'] = 999
    raw = json.dumps(document).encode()
    (tmp_path / 'profiles.json').write_bytes(raw)
    with pytest.raises(RuntimeError, match='recover_profiles.py'):
        create_runtime_store(tmp_path)
    assert (tmp_path / 'profiles.json').read_bytes() == raw


def test_target_backup_recovery_changes_generation_and_preserves_failed_bytes(tmp_path):
    target = activation.target_document()
    (tmp_path / 'profiles.json.bak').write_text(json.dumps(target), encoding='utf-8')
    original = b'corrupt synthetic current document'
    (tmp_path / 'profiles.json').write_bytes(original)
    assert not activation.restore_target_backup(tmp_path, lambda _: False)[0]
    assert (tmp_path / 'profiles.json').read_bytes() == original
    restored, safetyId = activation.restore_target_backup(tmp_path, lambda _: True)
    assert restored
    current = validate_contract(decode_document((tmp_path / 'profiles.json').read_bytes()), 'server')
    assert current['storeId'] != target['storeId']
    assert current['profiles'] == target['profiles']
    assert current['receipts'] == []
    assert (tmp_path / BACKUP_DIRECTORY / safetyId / 'profiles.json').read_bytes() == original
