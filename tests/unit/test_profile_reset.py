"""Offline destructive recovery tests use temporary synthetic files exclusively."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from companion import profile_recovery as recovery
from companion.profile_contracts import encode_document, new_server_document
from companion.profile_store import ProfileStore, read_document

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def private(tmp_path):
    current = tmp_path / 'profiles.json'
    current.write_bytes(b'old incompatible synthetic bytes')
    (tmp_path / 'profiles.json.bak').write_bytes(b'private rotating backup')
    (tmp_path / '.env').write_bytes(b'SYNTHETIC_PRIVATE_SETTING')
    (tmp_path / 'other-private.json').write_bytes(b'untouched')
    return tmp_path


def snapshot(directory):
    return {path.name: path.read_bytes() for path in directory.iterdir() if path.is_file()
            and path.name != '.profiles-recovery.lock'}


def test_read_only_inspection_and_unique_verified_snapshots(private):
    before = snapshot(private)
    assert recovery.inspect_current(private)['status'] == 'corrupt'
    assert snapshot(private) == before
    assert not (private / '.profiles-recovery.lock').exists()
    first = recovery.prepare_reset(private)
    second = recovery.prepare_reset(private)
    assert first != second
    for backupId in (first, second):
        manifest = recovery.verify_backup(private, backupId)
        folder = private / recovery.BACKUP_DIRECTORY / backupId
        assert set(path.name for path in folder.iterdir()) == {'profiles.json', 'profiles.json.bak', 'manifest.json'}
        for name, entry in manifest['files'].items():
            assert entry['sha256'] == hashlib.sha256(before[name]).hexdigest()
            assert (folder / name).read_bytes() == before[name]
    assert snapshot(private) == before


def test_cancelled_reset_keeps_every_original_byte(private):
    before = snapshot(private)
    backupId = recovery.prepare_reset(private)
    prompts = []
    assert not recovery.reset_profiles(private, backupId, lambda expected: prompts.append(expected) or False)
    assert prompts == ['RESET ' + backupId]
    assert snapshot(private) == before
    assert recovery.reset_state(private, backupId) == 'prepared'


def test_reset_only_current_format_and_preserves_private_state(private):
    before = snapshot(private)
    backupId = recovery.prepare_reset(private)
    assert recovery.reset_profiles(private, backupId, lambda _: True)
    restored = ProfileStore(private / 'profiles.json')
    assert restored.revision == 1
    assert len(restored.data['profiles'][0]['widgets']) == 5
    assert restored.data['activeProfile'] == 'p-default'
    assert 'format' not in json.loads(restored.path.read_bytes())
    for name in ('profiles.json.bak', '.env', 'other-private.json'):
        assert (private / name).read_bytes() == before[name]
    assert recovery.reset_state(private, backupId) == 'applied'
    assert (private / recovery.BACKUP_DIRECTORY / backupId / 'profiles.json').read_bytes() == before['profiles.json']
    recovery.verify_backup(private, backupId)
    with pytest.raises(recovery.RecoveryError, match='source_changed'):
        recovery.reset_profiles(private, backupId, lambda _: True)


@pytest.mark.parametrize('stage', ['before', 'during-main', 'during-backup'])
def test_source_changes_are_not_overwritten(private, stage):
    backupId = recovery.prepare_reset(private)
    expected = b'concurrently changed synthetic data'
    def confirm(_):
        (private / ('profiles.json.bak' if stage == 'during-backup' else 'profiles.json')).write_bytes(expected)
        return True
    if stage == 'before':
        (private / 'profiles.json').write_bytes(expected)
        confirm = lambda _: pytest.fail('Confirmation must not be reached')
    with pytest.raises(recovery.RecoveryError, match='source_changed'):
        recovery.reset_profiles(private, backupId, confirm)
    assert expected in snapshot(private).values()


@pytest.mark.parametrize('name', ['profiles.json', 'profiles.json.bak', 'manifest.json'])
def test_failed_backup_prevents_reset(private, monkeypatch, name):
    before = snapshot(private)
    original = recovery._exclusive
    def write(path, data):
        if path.name == name:
            raise OSError('synthetic backup failure')
        original(path, data)
    monkeypatch.setattr(recovery, '_exclusive', write)
    with pytest.raises(OSError):
        recovery.prepare_reset(private)
    assert snapshot(private) == before
    incomplete = next((private / recovery.BACKUP_DIRECTORY).iterdir()).name
    with pytest.raises((OSError, ValueError)):
        recovery.reset_profiles(private, incomplete, lambda _: True)
    assert snapshot(private) == before


def test_backup_integrity_and_path_validation(private):
    backupId = recovery.prepare_reset(private)
    before = snapshot(private)
    folder = private / recovery.BACKUP_DIRECTORY / backupId
    (folder / 'profiles.json').write_bytes(b'tampered')
    with pytest.raises(recovery.RecoveryError, match='backup_integrity'):
        recovery.reset_profiles(private, backupId, lambda _: pytest.fail('No confirmation for bad backup'))
    for invalidId in ('../outside', '', 'constructor', 'a' * 33):
        with pytest.raises(recovery.RecoveryError, match='backup_id'):
            recovery.verify_backup(private, invalidId)
    assert snapshot(private) == before


def test_existing_snapshot_is_never_overwritten(private, monkeypatch):
    backupId = recovery.prepare_reset(private)
    folder = private / recovery.BACKUP_DIRECTORY / backupId
    before = {path.name: path.read_bytes() for path in folder.iterdir()}
    monkeypatch.setattr(recovery.uuid, 'uuid4', lambda: SimpleNamespace(hex=backupId))
    with pytest.raises(FileExistsError):
        recovery.prepare_reset(private)
    assert {path.name: path.read_bytes() for path in folder.iterdir()} == before


def test_failed_current_write_keeps_original(private, monkeypatch):
    before = snapshot(private)
    backupId = recovery.prepare_reset(private)
    monkeypatch.setattr(recovery, 'atomic_write', lambda *_: (_ for _ in ()).throw(OSError('disk failure')))
    with pytest.raises(recovery.RecoveryError, match='write_failed'):
        recovery.reset_profiles(private, backupId, lambda _: True)
    assert snapshot(private) == before
    recovery.verify_backup(private, backupId)
    assert recovery.reset_state(private, backupId) == 'prepared'


def test_post_write_validation_failure_rolls_back(private, monkeypatch):
    before = snapshot(private)
    backupId = recovery.prepare_reset(private)
    original = recovery.decode_stored_document
    calls = 0
    def validate(raw):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise ValueError('synthetic readback failure')
        return original(raw)
    monkeypatch.setattr(recovery, 'decode_stored_document', validate)
    with pytest.raises(recovery.RecoveryError, match='write_failed'):
        recovery.reset_profiles(private, backupId, lambda _: True)
    assert snapshot(private) == before
    recovery.verify_backup(private, backupId)


def test_rollback_failure_keeps_verified_snapshot(private, monkeypatch):
    backupId = recovery.prepare_reset(private)
    originalWrite = recovery.atomic_write
    originalValidate = recovery.decode_stored_document
    writes = validations = 0
    def write(path, raw):
        nonlocal writes
        writes += 1
        if writes == 2:
            raise OSError('rollback disk failure')
        originalWrite(path, raw)
    def validate(raw):
        nonlocal validations
        validations += 1
        if validations == 2:
            raise ValueError('readback failure')
        return originalValidate(raw)
    monkeypatch.setattr(recovery, 'atomic_write', write)
    monkeypatch.setattr(recovery, 'decode_stored_document', validate)
    with pytest.raises(recovery.RecoveryError, match='rollback_required'):
        recovery.reset_profiles(private, backupId, lambda _: True)
    recovery.verify_backup(private, backupId)
    assert read_document(private / 'profiles.json')[1] == 1


@pytest.mark.parametrize('afterCommit', [False, True])
def test_interruption_has_a_deterministic_recovery_state(private, monkeypatch, afterCommit):
    backupId = recovery.prepare_reset(private)
    before = (private / 'profiles.json').read_bytes()
    original = recovery.atomic_write
    def interrupted(path, content):
        if afterCommit:
            original(path, content)
        raise KeyboardInterrupt()
    with monkeypatch.context() as patch:
        patch.setattr(recovery, 'atomic_write', interrupted)
        with pytest.raises(KeyboardInterrupt):
            recovery.reset_profiles(private, backupId, lambda _: True)
    assert recovery.reset_state(private, backupId) == ('applied' if afterCommit else 'prepared')
    assert (private / recovery.BACKUP_DIRECTORY / backupId / 'profiles.json').read_bytes() == before
    recovery.verify_backup(private, backupId)
    if afterCommit:
        assert ProfileStore(private / 'profiles.json').revision == 1
    else:
        assert (private / 'profiles.json').read_bytes() == before
        assert recovery.reset_profiles(private, backupId, lambda _: True)


def test_raw_restore_preserves_newer_current_and_leaves_rotating_backup(private):
    original = (private / 'profiles.json').read_bytes()
    backupId = recovery.prepare_reset(private)
    recovery.reset_profiles(private, backupId, lambda _: True)
    store = ProfileStore(private / 'profiles.json')
    document = copy.deepcopy(store.data)
    document['profiles'][0]['name'] = 'After reset'
    store.put(document, store.revision)
    current, backup = (private / 'profiles.json').read_bytes(), (private / 'profiles.json.bak').read_bytes()
    restored, safetyId = recovery.restore_reset(private, backupId, lambda _: True)
    assert restored and safetyId != backupId
    assert (private / 'profiles.json').read_bytes() == original
    assert (private / 'profiles.json.bak').read_bytes() == backup
    assert (private / recovery.BACKUP_DIRECTORY / safetyId / 'profiles.json').read_bytes() == current
    recovery.verify_backup(private, safetyId)


def test_raw_restore_cancellation_and_missing_current(private):
    backupId = recovery.prepare_reset(private)
    before = snapshot(private)
    restored, safetyId = recovery.restore_reset(private, backupId, lambda _: False)
    assert not restored and safetyId
    assert snapshot(private) == before
    (private / 'profiles.json').unlink()
    restored, safetyId = recovery.restore_reset(private, backupId, lambda _: True)
    assert restored and safetyId is None
    assert (private / 'profiles.json').read_bytes() == before['profiles.json']


def test_static_and_oversized_sources_are_refused(tmp_path, monkeypatch):
    static = tmp_path / 'static'
    static.mkdir()
    (static / 'profiles.json').write_bytes(b'synthetic')
    with pytest.raises(recovery.RecoveryError, match='unsafe_directory'):
        recovery.prepare_reset(static)
    directory = tmp_path / 'private'
    directory.mkdir()
    (directory / 'profiles.json').write_bytes(b'12345')
    monkeypatch.setattr(recovery, 'MAX_SOURCE_BYTES', 4)
    # Default arguments are fixed at definition, so exercise the bounded read directly.
    with pytest.raises(recovery.RecoveryError, match='source_size_limit'):
        recovery._read(directory / 'profiles.json', 4)


def test_recovery_lock_is_nonblocking_and_released(private):
    with recovery.recovery_lock(private):
        with pytest.raises(recovery.RecoveryError, match='recovery_busy'):
            recovery.prepare_reset(private)
    assert recovery.prepare_reset(private)


def test_process_death_releases_recovery_lock(private):
    code = "from companion.profile_recovery import recovery_lock; import os,sys;\nwith recovery_lock(sys.argv[1]): os._exit(9)"
    result = subprocess.run([sys.executable, '-c', code, str(private)], cwd=ROOT, timeout=20)
    assert result.returncode == 9
    assert recovery.prepare_reset(private)


def test_symlink_source_is_refused(tmp_path):
    directory = tmp_path / 'private'
    directory.mkdir()
    source = tmp_path / 'other-private-file'
    source.write_bytes(b'untouched')
    try:
        (directory / 'profiles.json').symlink_to(source)
    except OSError:
        pytest.skip('Symlink creation is unavailable; Linux CI covers this case')
    with pytest.raises(recovery.RecoveryError, match='linked_file'):
        recovery.prepare_reset(directory)
    assert source.read_bytes() == b'untouched'


def test_cli_refusal_and_read_only_inspection(private):
    command = [sys.executable, str(ROOT / 'scripts/recover_profiles.py'), '--data-dir', str(private)]
    before = snapshot(private)
    refused = subprocess.run(command + ['--prepare-reset'], capture_output=True, text=True, timeout=20)
    assert refused.returncode != 0
    assert not (private / recovery.BACKUP_DIRECTORY).exists()
    inspected = subprocess.run(command + ['--inspect'], capture_output=True, text=True, timeout=20)
    assert inspected.returncode == 0 and 'corrupt' in inspected.stdout
    assert 'old incompatible' not in inspected.stdout + inspected.stderr
    backupId = recovery.prepare_reset(private)
    cancelled = subprocess.run(command + ['--reset', backupId, '--service-stopped'], input='',
                               capture_output=True, text=True, timeout=20)
    assert cancelled.returncode == 0 and 'Cancelled' in cancelled.stdout
    assert snapshot(private) == before
    reset = subprocess.run(command + ['--reset', backupId, '--service-stopped'], input='RESET ' + backupId + '\n',
                           capture_output=True, text=True, timeout=20)
    assert reset.returncode == 0
    assert read_document(private / 'profiles.json')[1] == 1
    assert snapshot(private)['.env'] == before['.env']


def test_incompatible_startup_requires_explicit_offline_action(private):
    target = new_server_document()
    (private / 'profiles.json').write_bytes(encode_document(target))
    original = (private / 'profiles.json').read_bytes()
    env = dict(os.environ, GSI_TOKEN='synthetic-gsi-token-for-startup-test', DASHBOARD_PIN='synthetic-startup-pin',
               PROFILE_DATA_DIR=str(private), DIAGNOSTICS_DIR=str(private / 'diagnostics'))
    failed = subprocess.run([sys.executable, '-c', 'import companion.server'], cwd=ROOT, env=env,
                            capture_output=True, text=True, timeout=20)
    assert failed.returncode != 0 and 'recover_profiles.py' in failed.stderr
    assert (private / 'profiles.json').read_bytes() == original
    backupId = recovery.prepare_reset(private)
    recovery.reset_profiles(private, backupId, lambda _: True)
    ready = subprocess.run([sys.executable, '-c',
        "import companion.server,sys; assert 'companion.profile_contracts' not in sys.modules"],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=20)
    assert ready.returncode == 0, ready.stderr
    assert (private / recovery.BACKUP_DIRECTORY / backupId / 'profiles.json').read_bytes() == original
