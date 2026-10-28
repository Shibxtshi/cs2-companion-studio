#!/usr/bin/env python3
"""CI-only synthetic settings test; recreate containers without rebuilding images."""
from pathlib import Path
import subprocess

from smoke import wait_for_health

COMPOSE = ['docker', 'compose']
SERVICE = 'cs2-companion-studio'
PROBE = """
import asyncio, json, os
from websockets.asyncio.client import connect

async def check():
    async with connect('ws://127.0.0.1:8080/ws', origin='http://127.0.0.1:8080',
                       open_timeout=10, close_timeout=3) as socket:
        await socket.send(json.dumps({'type': 'auth', 'pin': os.environ['DASHBOARD_PIN']}))
        assert json.loads(await asyncio.wait_for(socket.recv(), timeout=10))['type'] == 'auth_ok'
        for _ in range(10):
            message = json.loads(await asyncio.wait_for(socket.recv(), timeout=10))
            if 'bomb_timer' in message:
                assert message['bomb_timer']['enabled'] is EXPECTED
                return
        raise AssertionError('No dashboard state received')

asyncio.run(check())
"""


def docker_output(*args):
    return subprocess.check_output(['docker', *args], text=True).strip()


def profile_digest():
    # Read as the unprivileged container user; private volume permissions stay intact.
    return docker_output('compose', 'exec', '-T', SERVICE, 'python', '-c',
                         "import hashlib; from pathlib import Path; "
                         "print(hashlib.sha256(Path('data/profiles.json').read_bytes()).hexdigest())")


def run():
    envPath = Path('.env')
    originalEnv = envPath.read_text(encoding='utf-8')
    assert 'BOMB_TIMER_ENABLED=false' in originalEnv, 'Requires synthetic CI defaults'
    originalContainer = docker_output('compose', 'ps', '-q', SERVICE)
    originalImage = docker_output('inspect', '--format', '{{.Image}}', originalContainer)
    profileDigest = profile_digest()
    try:
        for enabled in (True, False):
            envPath.write_text(originalEnv.replace('BOMB_TIMER_ENABLED=false',
                                                  'BOMB_TIMER_ENABLED=' + str(enabled).lower()),
                               encoding='utf-8')
            subprocess.run(COMPOSE + ['config', '--quiet'], check=True)
            subprocess.run(COMPOSE + ['up', '-d', '--no-build', '--pull', 'never',
                                      '--force-recreate', '--wait', '--wait-timeout', '120', SERVICE],
                           check=True)
            wait_for_health('http://127.0.0.1:8080')
            currentContainer = docker_output('compose', 'ps', '-q', SERVICE)
            assert currentContainer != originalContainer, 'Container was not recreated'
            assert docker_output('inspect', '--format', '{{.Image}}', currentContainer) == originalImage
            subprocess.run(COMPOSE + ['exec', '-T', SERVICE, 'python', '-c',
                                      PROBE.replace('EXPECTED', repr(enabled))], check=True)
            assert profile_digest() == profileDigest, 'Profiles changed'
            originalContainer = currentContainer
    finally:
        envPath.write_text(originalEnv, encoding='utf-8')
    print('OK: timer enabled/disabled over authenticated WebSocket, same image, profiles preserved')


if __name__ == '__main__':
    run()
