"""Exercise the target protocol through the existing PIN/Origin WebSocket gate."""
import asyncio

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from companion.profile_contracts import encode_document, new_server_document
from companion.profile_protocol import PublishedProfileProtocol
from companion.profile_publication import PublishedProfileStore
from tests.unit.test_profile_publication import operation


@pytest.fixture
def target(monkeypatch, tmp_path):
    monkeypatch.setenv('GSI_TOKEN', 'synthetic-publication-gsi-token')
    monkeypatch.setenv('DASHBOARD_PIN', 'synthetic-publication-pin')
    monkeypatch.setenv('PROFILE_DATA_DIR', str(tmp_path / 'legacy'))
    monkeypatch.setenv('DIAGNOSTICS_DIR', str(tmp_path / 'logs'))
    from companion import server
    from companion.security import LoginLimiter
    from companion.support_diagnostics import Diagnostics
    path = tmp_path / 'target' / 'profiles.json'
    path.parent.mkdir()
    path.write_bytes(encode_document(new_server_document()))
    adapter = PublishedProfileProtocol(PublishedProfileStore(path))
    monkeypatch.setattr(server, 'profile_store', adapter)
    monkeypatch.setattr(server, 'limiter', LoginLimiter())
    monkeypatch.setattr(server, 'DASHBOARD_PIN', 'synthetic-publication-pin')
    monkeypatch.setattr(server, 'GSI_TOKEN', 'synthetic-publication-gsi-token')
    monkeypatch.setattr(server, 'diagnostics', Diagnostics(tmp_path / 'logs', '1.1.0'))
    monkeypatch.setattr(server, 'lock', asyncio.Lock())
    monkeypatch.setattr(server, 'state', {'map': {}, 'round': {}, 'player': {}, 'provider': {}})
    monkeypatch.setattr(server, 'last_seen', None)
    monkeypatch.setattr(server, 'last_game_seen', None)
    return server, adapter


def authenticate(socket, server):
    socket.send_json({'type': 'auth', 'pin': server.DASHBOARD_PIN})
    assert socket.receive_json()['type'] == 'auth_ok'
    catalog = socket.receive_json()
    assert catalog['type'] == 'profiles_catalog'
    socket.receive_json()
    return catalog['catalog']


def send(socket, command):
    socket.send_json({'type': 'profile_operation', 'operation': command})
    return socket.receive_json()


def test_authenticated_publish_broadcast_retry_and_reconnect(target):
    server, adapter = target
    with TestClient(server.app) as client:
        with client.websocket_connect('/ws', headers={'origin': 'http://testserver'}) as a:
            catalog = authenticate(a, server)
            with client.websocket_connect('/ws', headers={'origin': 'http://testserver'}) as b:
                authenticate(b, server)
                command = operation(adapter.data)
                answer = send(a, command)
                assert answer['type'] == 'profile_operation_ack'
                assert answer['receipt']['result']['revision'] == 2
                assert a.receive_json()['catalog']['profiles'][0]['revision'] == 2
                assert b.receive_json()['catalog']['profiles'][0]['revision'] == 2
                assert send(a, command)['replayed']
                assert a.receive_json()['catalog']['catalogRevision'] == 2
                b.send_json({'type': 'profile_catalog_request'})
                assert b.receive_json()['catalog']['catalogRevision'] == 2
        with client.websocket_connect('/ws', headers={'origin': 'http://testserver'}) as reconnected:
            assert authenticate(reconnected, server)['profiles'][0]['revision'] == 2
    assert adapter.data['profiles'][0]['revision'] == 2


def test_target_conflicts_and_generation_errors_expose_latest_without_writing(target):
    server, adapter = target
    with TestClient(server.app) as client:
        with client.websocket_connect('/ws', headers={'origin': 'http://testserver'}) as socket:
            authenticate(socket, server)
            first = operation(adapter.data)
            send(socket, first)
            socket.receive_json()
            stale = operation(adapter.data)
            before = adapter.store.path.read_bytes()
            error = send(socket, stale)
            assert error['code'] == 'revision_conflict'
            assert error['catalog']['profiles'][0]['revision'] == 2
            stale['storeId'] = '0' * 32
            assert send(socket, stale)['code'] == 'store_changed'
            assert adapter.store.path.read_bytes() == before


@pytest.mark.parametrize('raw', ['{', '[]', '{"type":"profile_catalog_request","type":"profile_catalog_request"}',
                                 '{"type":"profile_operation","operation":NaN}', 'x' * 81001],
                         ids=['malformed', 'array', 'duplicate-key', 'non-finite', 'oversized'])
def test_target_strict_json_and_size_are_controlled(target, raw):
    server, adapter = target
    before = adapter.store.path.read_bytes()
    with TestClient(server.app) as client:
        with client.websocket_connect('/ws', headers={'origin': 'http://testserver'}) as socket:
            authenticate(socket, server)
            socket.send_text(raw)
            assert socket.receive_json()['code'] == 'invalid_document'
            socket.send_json({'type': 'diagnostics_request'})
            assert socket.receive_json()['type'] == 'diagnostics_data'
    assert adapter.store.path.read_bytes() == before


@pytest.mark.parametrize('origin', [None, 'null', 'http://evil.test'])
def test_target_origin_gate_is_unchanged(target, origin):
    server, _ = target
    with TestClient(server.app) as client:
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect('/ws', headers={'origin': origin} if origin else {}):
                pass


def test_target_needs_real_pin_not_public_ids(target):
    server, adapter = target
    before = adapter.store.path.read_bytes()
    with TestClient(server.app) as client:
        with client.websocket_connect('/ws', headers={'origin': 'http://testserver'}) as socket:
            socket.send_json({'type': 'profile_operation', 'operation': operation(adapter.data)})
            assert socket.receive_json()['type'] == 'auth_error'
        with client.websocket_connect('/ws', headers={'origin': 'http://testserver'}) as socket:
            socket.send_json({'type': 'auth', 'pin': adapter.store.catalog()['accessId']})
            assert socket.receive_json()['type'] == 'auth_error'
    assert adapter.store.path.read_bytes() == before


@pytest.mark.parametrize('kind', ['valid', 'legacy', 'unknown', 'oversized', 'duplicate', 'secret'])
def test_import_validation_is_authenticated_strict_and_read_only(target, kind):
    import json
    server, adapter = target
    before = adapter.store.path.read_bytes()
    profile = adapter.data['profiles'][0]
    exported = {'format': 'ccs-dashboard-export', 'version': 1,
                'name': profile['name'], 'configuration': profile['configuration']}
    if kind == 'legacy':
        exported['format'] = 'cs2-companion-layout'
    elif kind == 'unknown':
        exported['version'] = 99
    elif kind == 'secret':
        exported['pin'] = 'synthetic-disallowed-value'
    raw = json.dumps(exported)
    if kind == 'duplicate':
        raw = raw[:-1] + ',"name":"duplicate"}'
    elif kind == 'oversized':
        raw += ' ' * 70001
    with TestClient(server.app) as client:
        with client.websocket_connect('/ws', headers={'origin': 'http://testserver'}) as socket:
            authenticate(socket, server)
            socket.send_json({'type': 'profile_import_validate', 'requestId': 'a' * 32, 'document': raw})
            answer = socket.receive_json()
            assert answer['requestId'] == 'a' * 32
            assert answer['type'] == ('profile_import_validated' if kind == 'valid' else 'profile_import_error')
            if kind == 'valid':
                assert answer['content'] == {key: profile[key] for key in ['name', 'configuration']}
            if kind == 'legacy':
                assert answer['code'] == 'legacy_export'
    assert adapter.store.path.read_bytes() == before


def test_disk_error_never_acknowledges_or_changes_published_state(target, monkeypatch):
    from companion import profile_publication
    server, adapter = target
    before = adapter.data
    monkeypatch.setattr(profile_publication, 'atomic_write', lambda *_: (_ for _ in ()).throw(OSError('synthetic failure')))
    with TestClient(server.app) as client:
        with client.websocket_connect('/ws', headers={'origin': 'http://testserver'}) as socket:
            authenticate(socket, server)
            answer = send(socket, operation(before))
            assert answer['type'] == 'profile_operation_error' and answer['code'] == 'disk'
            assert answer['catalog']['catalogRevision'] == before['catalogRevision']
    assert adapter.data == before


def test_ack_loss_still_broadcasts_and_retry_reconciles(target):
    server, adapter = target
    class Peer:
        def __init__(self, broken=False):
            self.broken, self.messages = broken, []
        async def send_text(self, value):
            if self.broken:
                raise RuntimeError('synthetic disconnected sender')
            self.messages.append(value)
        async def close(self, code):
            pass
    broken, healthy = Peer(True), Peer()
    clients = {broken, healthy}
    command = operation(adapter.data)
    import json
    asyncio.run(adapter.dispatch(json.dumps({'type': 'profile_operation', 'operation': command}), broken, clients))
    assert len(healthy.messages) == 1
    assert 'profiles_catalog' in healthy.messages[0]
    receipt = adapter.store.publish(command)
    assert receipt['replayed'] and receipt['result']['revision'] == 2


def test_target_disk_wait_does_not_hold_the_gsi_ingestion_lock(target, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    import threading
    from companion import profile_publication
    server, adapter = target
    entered, release = threading.Event(), threading.Event()
    original = profile_publication.atomic_write
    def delayed(path, content):
        if path == adapter.store.path:
            entered.set()
            assert release.wait(5), 'Synthetic writer gate timeout'
        original(path, content)
    monkeypatch.setattr(profile_publication, 'atomic_write', delayed)
    with TestClient(server.app) as client:
        with client.websocket_connect('/ws', headers={'origin': 'http://testserver'}) as socket:
            authenticate(socket, server)
            socket.send_json({'type': 'profile_operation', 'operation': operation(adapter.data)})
            try:
                assert entered.wait(2)
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(client.post, '/gsi', json={
                        'auth': {'token': server.GSI_TOKEN}, 'player': {'state': {'health': 77}}})
                    assert future.result(timeout=2).status_code == 200
            finally:
                release.set()
            for _ in range(5):
                if socket.receive_json().get('type') == 'profile_operation_ack':
                    break
            else:
                pytest.fail('No committed acknowledgement')


@pytest.mark.parametrize('frame, expectedCode', [('binary', 1003), ('oversized', 1009)])
def test_target_preserves_binary_and_transport_size_closures(target, frame, expectedCode):
    server, adapter = target
    before = adapter.store.path.read_bytes()
    with TestClient(server.app) as client:
        with client.websocket_connect('/ws', headers={'origin': 'http://testserver'}) as socket:
            authenticate(socket, server)
            if frame == 'binary':
                socket.send_bytes(b'synthetic')
            else:
                socket.send_text('x' * 225001)
            with pytest.raises(WebSocketDisconnect) as error:
                socket.receive_json()
            assert error.value.code == expectedCode
    assert adapter.store.path.read_bytes() == before
