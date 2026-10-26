#!/usr/bin/env python3
"""Smoke-test an already-running Docker Compose instance on CI's loopback port."""
import json
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def token_from_env(path=Path('.env')):
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.startswith('GSI_TOKEN='):
            return line.split('=', 1)[1]
    raise RuntimeError('Missing GSI token in private test env')


def get(url):
    with urlopen(url, timeout=2) as response:
        return response.status, response.read().decode('utf-8')


def wait_for_health(base, timeout=60):
    """Wait until the server is ready, including after a Compose restart.

    Compose reports "Started" before the HTTP listener is necessarily ready.
    A connection reset during this short window is expected, not a failure.
    """
    deadline = time.monotonic() + timeout
    last_error = None
    while time.monotonic() < deadline:
        try:
            code, data = get(base + '/health')
            if code == 200 and json.loads(data).get('version') == '1.0.0':
                return
        except (URLError, OSError, ValueError) as exc:
            # URLError: refused connections; OSError: resets/disconnects;
            # ValueError: incomplete or invalid health JSON during startup.
            last_error = exc
        time.sleep(0.5)
    raise RuntimeError('Docker service not healthy or wrong version after restart') from last_error


def run():
    base = 'http://127.0.0.1:8080'
    wait_for_health(base)
    for path in ('/profiles', '/data/profiles.json', '/logs/support-summary.json'):
        try:
            status, _ = get(base + path)
        except HTTPError as exc:
            status = exc.code
        if status in (200, 206):
            raise AssertionError('Private endpoint accidentally exposed: ' + path)
    payload = json.dumps({'auth': {'token': token_from_env()}, 'map': {'name': 'de_mirage', 'phase': 'live', 'round': 1}, 'player': {'state': {'health': 92}}}).encode()
    request = Request(base+'/gsi', data=payload, headers={'Content-Type': 'application/json'}, method='POST')
    with urlopen(request, timeout=5) as response:
        assert response.status == 200 and json.loads(response.read()).get('ok') is True
    assert Path('data/profiles.json').is_file()
    print('OK: Docker running, no private HTTP routes, synthetic GSI accepted, profiles volume mounted')


if __name__ == '__main__':
    run()
