"""Run with: python -m tests.standalone.test_profiles_and_diagnostics (offline, no CS2 required)."""
import json
import os
import tempfile
from pathlib import Path

os.environ['GSI_TOKEN'] = 'fake-dev-only-gsi-token'
os.environ['DASHBOARD_PIN'] = '1234567890'
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from profile_store import ProfileStore
from support_diagnostics import Diagnostics
import app


def run():
    with tempfile.TemporaryDirectory() as folder:
        app.profile_store = ProfileStore(Path(folder) / 'data' / 'profiles.json')
        app.diagnostics = Diagnostics(Path(folder) / 'logs', '1.0.0')
        with TestClient(app.app) as client:
            # Neither unauthenticated HTTP nor the open demo has any profile route.
            for route in ('/profiles', '/api/profiles', '/data/profiles.json', '/logs/support-summary.json'):
                assert client.get(route).status_code in (404, 405), route
            with client.websocket_connect('/ws', headers={'origin': 'http://testserver'}) as a, client.websocket_connect('/ws', headers={'origin': 'http://testserver'}) as b:
                for ws in (a, b):
                    ws.send_json({'type': 'auth', 'pin': '1234567890'})
                    assert ws.receive_json()['type'] == 'auth_ok'
                    snap = ws.receive_json()
                    assert snap['type'] == 'profiles_state' and snap['profiles'][0]['name'] == 'My dashboard'
                    ws.receive_json()  # live GSI state
                original = app.profile_store.snapshot()
                changed = {'profiles': original['profiles'], 'activeProfile': original['activeProfile']}
                changed['profiles'][0]['name'] = 'Public custom dashboard'
                a.send_json({'type': 'profiles_save', 'revision': original['revision'], 'document': changed})
                for ws in (a, b):
                    saved = ws.receive_json()
                    assert saved['type'] == 'profiles_state' and saved['profiles'][0]['name'] == 'Public custom dashboard'
                    assert saved['revision'] == original['revision'] + 1
                b.send_json({'type': 'profiles_save', 'revision': original['revision'], 'document': changed})
                assert b.receive_json()['code'] == 'conflict'
                assert b.receive_json()['type'] == 'profiles_state'
                # Decline malicious payloads without overwriting disk.
                bad = json.loads(json.dumps(changed))
                bad['profiles'][0]['widgets'][0]['kind'] = '<script>alert(1)</script>'
                a.send_json({'type': 'profiles_save', 'revision': app.profile_store.revision, 'document': bad})
                assert a.receive_json()['code'] == 'invalid'
                a.send_json({'type': 'diagnostics_request'})
                rep = a.receive_json()
                assert rep['type'] == 'diagnostics_data'
                assert 'player' not in rep['report'] and 'steam' not in rep['report']
                assert '1234567890' not in json.dumps(rep)
                assert 'fake-dev-only-gsi-token' not in json.dumps(rep)
            reloaded = ProfileStore(Path(folder) / 'data' / 'profiles.json')
            assert reloaded.snapshot()['profiles'][0]['name'] == 'Public custom dashboard'
            log = (Path(folder) / 'logs' / 'events.jsonl').read_text()
            assert '1234567890' not in log and 'fake-dev-only-gsi-token' not in log
            assert 'Public custom dashboard' not in log
    print('OK: isolated profiles, authenticated WS, multi-client sync, conflict, validation, restart persistence, safe support diagnostics')

if __name__ == '__main__':
    run()
