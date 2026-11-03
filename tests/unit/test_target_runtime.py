"""Fresh target-only runtime: no legacy fallback, conversion or recovery overwrite."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from companion import profile_runtime as runtime
from companion.profile_contracts import encode_document, new_server_document
from companion.profile_protocol import PublishedProfileProtocol
from companion.profile_recovery import RecoveryError, recovery_lock
from companion.profile_store import default_document


def test_fresh_directory_initializes_empty_target_and_reopens_unchanged(tmp_path):
    directory = tmp_path / 'data'
    store = runtime.create_runtime_store(directory)
    assert isinstance(store, PublishedProfileProtocol)
    assert store.data['format'] == 'ccs-dashboard-store'
    assert store.data['version'] == 1
    assert store.data['profiles'][0]['configuration']['layout'] == {'columns':24, 'widgets':[]}
    assert store.data['profiles'][0]['configuration']['navigation']['mode'] == 'compact'
    original = (directory / 'profiles.json').read_bytes()
    assert runtime.create_runtime_store(directory).data == store.data
    assert (directory / 'profiles.json').read_bytes() == original
    assert not (directory / 'profiles.json.bak').exists()


def test_valid_target_and_backup_are_unchanged(tmp_path):
    original = encode_document(new_server_document())
    (tmp_path / 'profiles.json').write_bytes(original)
    (tmp_path / 'profiles.json.bak').write_bytes(original)
    assert runtime.create_runtime_store(tmp_path).data['storeId'] == json.loads(original)['storeId']
    assert (tmp_path / 'profiles.json').read_bytes() == original
    assert (tmp_path / 'profiles.json.bak').read_bytes() == original


@pytest.mark.parametrize('raw', [b'{broken', b'{}', b'[]',
    json.dumps(default_document()).encode(),
    encode_document({**new_server_document(), 'version':999}),
    encode_document({**new_server_document(), 'format':'unknown-format'})])
def test_existing_invalid_historical_or_future_document_is_preserved(tmp_path, raw):
    (tmp_path / 'profiles.json').write_bytes(raw)
    (tmp_path / 'profiles.json.bak').write_bytes(b'keep backup bytes')
    with pytest.raises(RuntimeError, match='recover_profiles.py'):
        runtime.create_runtime_store(tmp_path)
    assert (tmp_path / 'profiles.json').read_bytes() == raw
    assert (tmp_path / 'profiles.json.bak').read_bytes() == b'keep backup bytes'


@pytest.mark.parametrize('artifact', ['profiles.json.bak', 'profile-reset-backups',
    '.profiles-activation-abc.candidate', '.profiles-restore-abc.pending',
    '.profiles-initialize-interrupted', 'private-setting.json'])
def test_missing_main_with_any_recovery_or_private_data_refuses_initialization(tmp_path, artifact):
    path = tmp_path / artifact
    if artifact == 'profile-reset-backups':
        path.mkdir()
    else:
        path.write_bytes(b'preserve')
    with pytest.raises(RuntimeError):
        runtime.create_runtime_store(tmp_path)
    assert path.exists()
    assert not (tmp_path / 'profiles.json').exists()


def test_pending_restore_blocks_even_valid_target(tmp_path):
    original = encode_document(new_server_document())
    (tmp_path / 'profiles.json').write_bytes(original)
    (tmp_path / '.profiles-restore-test.pending').write_bytes(b'keep')
    with pytest.raises(RuntimeError):
        runtime.create_runtime_store(tmp_path)
    assert (tmp_path / 'profiles.json').read_bytes() == original


def test_running_lease_excludes_another_store_and_offline_tools(tmp_path):
    store = runtime.create_runtime_store(tmp_path)
    with runtime.runtime_lease(store):
        with pytest.raises(RuntimeError):
            runtime.create_runtime_store(tmp_path)
        with pytest.raises(RecoveryError):
            with recovery_lock(tmp_path):
                pytest.fail('Concurrent writer admitted')


def test_atomic_initialization_does_not_overwrite_a_racing_file(tmp_path, monkeypatch):
    racing = b'concurrent source bytes'
    link = runtime.os.link
    def compete(source, destination):
        Path(destination).write_bytes(racing)
        link(source, destination)
    monkeypatch.setattr(runtime.os, 'link', compete)
    with pytest.raises(RuntimeError):
        runtime.create_runtime_store(tmp_path)
    assert (tmp_path / 'profiles.json').read_bytes() == racing


def test_failed_initialization_write_does_not_create_main(tmp_path, monkeypatch):
    def fail(*_args):
        raise OSError('Synthetic full disk')
    monkeypatch.setattr(runtime, 'atomic_write', fail)
    with pytest.raises(RuntimeError):
        runtime.create_runtime_store(tmp_path)
    assert not (tmp_path / 'profiles.json').exists()


def test_fresh_real_server_serves_target_and_rejects_legacy_autosave(tmp_path):
    root = Path(__file__).resolve().parents[2]
    env = dict(os.environ, DASHBOARD_PIN='synthetic-fresh-pin', GSI_TOKEN='synthetic-fresh-gsi-token',
               PROFILE_DATA_DIR=str(tmp_path / 'data'), DIAGNOSTICS_DIR=str(tmp_path / 'logs'))
    code = '''
from companion.server import app
from fastapi.testclient import TestClient
from pathlib import Path
import os
with TestClient(app) as client:
    assert '/static/js/application.js' in client.get('/').text
    for path in ['/static/legacy.html', '/static/js/studio.js', '/static/js/profile-sync.js',
                 '/static/js/dashboard-target.js', '/static/js/studio-target.js',
                 '/__dashboard_target__.js', '/__studio_target__.js']:
        assert client.get(path).status_code == 404
    original = (Path(os.environ['PROFILE_DATA_DIR']) / 'profiles.json').read_bytes()
    with client.websocket_connect('/ws', headers={'origin':'http://testserver'}) as socket:
        socket.send_json({'type':'auth','pin':'synthetic-fresh-pin'})
        assert socket.receive_json()['type'] == 'auth_ok'
        assert socket.receive_json()['type'] == 'profiles_catalog'
        socket.receive_json()
        socket.send_json({'type':'profiles_save','document':{}})
        assert socket.receive_json()['type'] == 'profile_operation_error'
    assert (Path(os.environ['PROFILE_DATA_DIR']) / 'profiles.json').read_bytes() == original
'''
    for _ in range(2):
        result = subprocess.run([sys.executable, '-B', '-c', code], cwd=root, env=env,
                                capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, result.stderr


def test_distributed_pages_reference_only_existing_target_assets():
    from html.parser import HTMLParser
    root = Path(__file__).resolve().parents[2]
    class Assets(HTMLParser):
        def __init__(self):
            super().__init__()
            self.sources = []
            self.ids = set()
        def handle_starttag(self, tag, attrs):
            attributes = dict(attrs)
            self.ids.add(attributes.get('id'))
            if tag == 'script':
                self.sources.append((attributes.get('src') or attributes.get('data-ccs-src', '')).split('?')[0])
    for name in ['static/index.html', 'static/preview.html']:
        parser = Assets()
        parser.feed((root / name).read_text('utf-8'))
        assert parser.ids.isdisjoint({'tab-custom', 'custom-tools', 'catalog-items', 'profile-select', 'edit-hint'})
        for source in parser.sources:
            assert source not in ['/static/js/studio.js', '/static/js/profile-sync.js']
            assert (root / source.lstrip('/')).is_file(), (name, source)
    assert not (root / 'static/legacy.html').exists()
    assert not (root / 'static/js/studio.js').exists()
    assert not (root / 'static/js/profile-sync.js').exists()


def test_native_initializations_have_independent_generations(tmp_path):
    first = runtime.create_runtime_store(tmp_path / 'first')
    second = runtime.create_runtime_store(tmp_path / 'second')
    assert first.data['storeId'] != second.data['storeId']


def test_new_recovery_artifact_during_staging_prevents_initialization(tmp_path, monkeypatch):
    write = runtime.atomic_write
    def create_backup(path, raw):
        write(path, raw)
        (tmp_path / 'profiles.json.bak').write_bytes(b'concurrent recovery bytes')
    monkeypatch.setattr(runtime, 'atomic_write', create_backup)
    with pytest.raises(RuntimeError):
        runtime.create_runtime_store(tmp_path)
    assert not (tmp_path / 'profiles.json').exists()
    assert (tmp_path / 'profiles.json.bak').read_bytes() == b'concurrent recovery bytes'


@pytest.mark.parametrize('invalid', [False, True])
def test_only_empty_placeholder_is_a_fresh_directory(tmp_path, invalid):
    marker = tmp_path / '.gitkeep'
    marker.write_bytes(b'not a placeholder' if invalid else b'')
    if invalid:
        with pytest.raises(RuntimeError, match='invalid_empty_directory_marker'):
            runtime.create_runtime_store(tmp_path)
        assert not (tmp_path / 'profiles.json').exists()
    else:
        assert runtime.create_runtime_store(tmp_path).data['format'] == 'ccs-dashboard-store'
    assert marker.read_bytes() == (b'not a placeholder' if invalid else b'')


def test_unsupported_atomic_publication_fails_without_main(tmp_path, monkeypatch):
    def unsupported(*_args):
        raise OSError('Synthetic unsupported hard links')
    monkeypatch.setattr(runtime.os, 'link', unsupported)
    with pytest.raises(RuntimeError, match='atomic_initialization_unavailable'):
        runtime.create_runtime_store(tmp_path)
    assert not (tmp_path / 'profiles.json').exists()
