"""Public-release security regressions. Run: python -m pytest -q tests/test_public_security.py."""
import json
import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

# Synthetic credentials and isolated runtime folders; NEVER use personal .env here.
_tmp = tempfile.TemporaryDirectory(prefix='companion-security-')
os.environ['GSI_TOKEN'] = 'synthetic-gsi-token-for-security-testing'
os.environ['DASHBOARD_PIN'] = 'synthetic-pin-739284'
os.environ['PROFILE_DATA_DIR'] = str(Path(_tmp.name) / 'data')
os.environ['DIAGNOSTICS_DIR'] = str(Path(_tmp.name) / 'logs')
os.environ['BOMB_TIMER_ENABLED'] = 'false'

import app  # noqa: E402
from profile_store import ProfileStore, MAX_STORE_BYTES  # noqa: E402
from security import same_origin  # noqa: E402


def test_public_routes_and_headers():
    with TestClient(app.app) as client:
        for path in ('/data/profiles.json', '/logs/events.jsonl', '/profiles', '/api/profiles',
                     '/.env', '/openapi.json', '/docs', '/static/../data/profiles.json'):
            assert client.get(path).status_code not in (200, 206), path
        response = client.get('/health')
        assert response.json() == {'service': 'ok', 'version': app.VERSION}
        assert 'pin' not in response.text.lower()
        assert response.headers['x-frame-options'] == 'DENY'
        assert 'no-store' in response.headers['cache-control']
        assert "script-src 'self'" in response.headers['content-security-policy']
        assert "frame-ancestors 'none'" in response.headers['content-security-policy']


@pytest.mark.parametrize('origin', [None, 'null', 'http://evil.test', 'http://testserver.evil.test',
                                    'http://testserver@evil.test', 'https://testserver',
                                    'http://testserver/path', 'http://testserver?abc=1'])
def test_cross_site_or_missing_origin(origin):
    assert not same_origin(origin, 'testserver')
    with TestClient(app.app) as client:
        headers = {'origin': origin} if origin is not None else {}
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect('/ws', headers=headers):
                pass


def test_no_ws_data_before_auth_and_bad_pin():
    with TestClient(app.app) as client:
        with client.websocket_connect('/ws', headers={'origin': 'http://testserver'}) as ws:
            ws.send_json({'type': 'diagnostics_request'})
            answer = ws.receive_json()
            assert answer['type'] == 'auth_error'
            assert 'profiles' not in json.dumps(answer)
        with client.websocket_connect('/ws', headers={'origin': 'http://testserver'}) as ws:
            ws.send_json({'type': 'auth', 'pin': 'wrong-pin'})
            assert ws.receive_json()['type'] == 'auth_error'


@pytest.mark.parametrize('bad_section', [
    {'player': {'weapons': []}}, {'player': {'state': ['bad']}},
    {'map': {'team_ct': 13}}, {'map': {'round_wins': []}},
    {'round': 'live'}, {'provider': [1, 2]},
])
def test_invalid_gsi_shapes_are_rejected(bad_section):
    with TestClient(app.app) as client:
        payload = {'auth': {'token': os.environ['GSI_TOKEN']}, **bad_section}
        assert client.post('/gsi', json=payload).status_code == 400


def test_auth_and_streaming_body_cap():
    with TestClient(app.app) as client:
        assert client.post('/gsi', json={'auth': {'token': 'not-valid'}}).status_code == 401
        assert client.post('/gsi', json={'player': {'state': {'health': 99}}}).status_code == 401
        assert client.post('/gsi', content=b'x' * (app.MAX_GSI_SIZE + 1)).status_code == 413
        assert client.post('/gsi', content=b'{', headers={'Content-Type': 'application/json'}).status_code == 400
        good = {'auth': {'token': os.environ['GSI_TOKEN']}, 'player': {'state': {'health': 75}}}
        assert client.post('/gsi', json=good).status_code == 200
        assert 'token' not in json.dumps(app.summary())


def test_profiles_validation_persistence_and_safe_diagnostics(tmp_path):
    store = ProfileStore(tmp_path / 'data' / 'profiles.json')
    snapshot = store.snapshot()
    assert snapshot['profiles']
    original = json.loads(json.dumps(snapshot))
    document = {'profiles': original['profiles'], 'activeProfile': original['activeProfile']}
    document['profiles'][0]['name'] = '<img src=x onerror=alert(1)>'
    assert store.put(document, store.revision)
    assert '<img' in ProfileStore(store.path).snapshot()['profiles'][0]['name']
    # Names may contain markup-looking text, but they are DATA, not executed HTML.
    bad = json.loads(json.dumps(document))
    bad['profiles'][0]['widgets'][0]['kind'] = '<script>alert(1)</script>'
    with pytest.raises(ValueError):
        store.put(bad, store.revision)
    assert not store.put(document, store.revision - 1)
    assert store.path.stat().st_size < MAX_STORE_BYTES
    diagnostics_dir = Path(os.environ['DIAGNOSTICS_DIR'])
    app.diagnostics.write_summary(len(store.data['profiles']))
    files = list(diagnostics_dir.glob('*'))
    assert files
    contents = ''.join(f.read_text('utf-8') for f in files if f.is_file())
    for sensitive in (os.environ['DASHBOARD_PIN'], os.environ['GSI_TOKEN'],
                      'onerror=alert', 'steamid', 'profiles.json'):
        assert sensitive not in contents.lower(), sensitive


def test_packaged_docker_default_is_loopback():
    compose = (Path(__file__).parents[1] / 'compose.yaml').read_text('utf-8')
    assert '${BIND_HOST:-127.0.0.1}' in compose
    assert 'no-new-privileges:true' in compose
    assert 'cap_drop:' in compose
    assert 'read_only: true' in compose
