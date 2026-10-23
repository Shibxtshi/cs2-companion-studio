"""First public-security regression checks. Run: python test_security.py"""
import os
os.environ['GSI_TOKEN'] = 'v1p-test-token-example-not-real'
os.environ['DASHBOARD_PIN'] = '1234567890'
os.environ['BOMB_TIMER_ENABLED'] = 'false'

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from security import LoginLimiter, same_origin
import app


def run():
    assert same_origin('http://testserver', 'testserver')
    assert same_origin('http://192.168.1.20:8080', '192.168.1.20:8080')
    assert not same_origin('https://malicious.example', 'testserver')
    assert not same_origin('null', 'testserver')
    assert not same_origin(None, 'testserver')
    limiter = LoginLimiter(limit=3, window=300, lockout=900)
    for sec in (1, 2, 3):
        limiter.fail('test', sec)
    assert not limiter.allowed('test', 4)
    assert not limiter.allowed('test', 902)
    assert limiter.allowed('test', 904)
    with TestClient(app.app) as client:
        r = client.get('/health')
        assert r.json() == {'service': 'ok', 'version': '1p-f'}
        assert r.headers['x-frame-options'] == 'DENY'
        assert "script-src 'self'" in r.headers['content-security-policy']
        assert 'gsi_online' not in r.text
        assert client.get('/static/studio.js').status_code == 200
        assert client.get('/static/styles.css').status_code == 200
        try:
            with client.websocket_connect('/ws', headers={'origin': 'http://evil.test'}):
                raise AssertionError('Cross origin unexpectedly accepted')
        except WebSocketDisconnect as exc:
            assert exc.code == 1008
        with client.websocket_connect('/ws', headers={'origin': 'http://testserver'}) as ws:
            ws.send_json({'type': 'auth', 'pin': '1234567890'})
            assert ws.receive_json()['type'] == 'auth_ok'
            assert ws.receive_json()['type'] == 'profiles_state'
            assert ws.receive_json()['type'] == 'state'
            payload = {'auth': {'token': 'v1p-test-token-example-not-real'}, 'round': {'phase': 'live'},
                       'player': {'state': {'health': 87}}}
            assert client.post('/gsi', json=payload).status_code == 200
            assert ws.receive_json()['player']['health'] == 87
            assert client.post('/gsi', json={'auth': {'token': 'incorrect'}}).status_code == 401
            assert client.post('/gsi', content=b'x' * 262145).status_code == 413
            assert client.post('/gsi', json={'auth':payload['auth'], 'player': {'state': ['malformed']}}).status_code == 400
        # Five incorrect PINs from the same peer result in a temporary lock.
        for _ in range(5):
            with client.websocket_connect('/ws', headers={'origin': 'http://testserver'}) as wrong:
                wrong.send_json({'type': 'auth', 'pin': '0000000000'})
                assert wrong.receive_json()['type'] == 'auth_error'
        try:
            with client.websocket_connect('/ws', headers={'origin': 'http://testserver'}):
                raise AssertionError('The sixth connection should be locked')
        except WebSocketDisconnect as exc:
            assert exc.code == 1008
    print('OK: V1P auth, same-origin WS, integrated throttling, size cap, payload validation, response headers')


if __name__ == '__main__':
    run()
