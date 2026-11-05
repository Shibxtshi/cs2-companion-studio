"""Real HTTP + WebSocket E2E. Usage: python tests/browser/test_live_browser.py --browser chromium|firefox|webkit"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen, Request
from urllib.error import URLError

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
PIN = 'e2e-pin-239840'
TOKEN = 'e2e-synthetic-gsi-token-very-long'


def start_server():
    runtime = tempfile.TemporaryDirectory(prefix='cs2-companion-e2e-')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    env = dict(os.environ, DASHBOARD_PIN=PIN, GSI_TOKEN=TOKEN,
               PROFILE_DATA_DIR=str(Path(runtime.name) / 'data'),
               DIAGNOSTICS_DIR=str(Path(runtime.name) / 'logs'),
               BOMB_TIMER_ENABLED='false')
    proc = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'companion.server:app',
                             '--host', '127.0.0.1', '--port', str(port), '--no-access-log', '--ws-max-size', '262144', '--ws-max-queue', '8'],
                            cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    url = f'http://127.0.0.1:{port}'
    for _ in range(80):
        if proc.poll() is not None:
            err = proc.stderr.read().decode('utf-8', 'replace')[:1400]
            raise RuntimeError('Server crashed: ' + err)
        try:
            with urlopen(url + '/health', timeout=.3) as response:
                if json.load(response)['version'] == '1.1.0':
                    return runtime, proc, url
        except (URLError, TimeoutError, OSError):
            time.sleep(.1)
    proc.terminate()
    raise TimeoutError('HTTP server did not become ready')



def stop_server(runtime, process):
    if process.poll() is None:
        if os.name == 'nt':
            subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        else:
            process.terminate()
        process.wait(timeout=10)
    runtime.cleanup()


def login(page, url):
    page.goto(url, wait_until='domcontentloaded')
    page.locator('#pin').fill(PIN)
    page.locator('#connect').click()
    expect(page.locator('#dashboard-profile-menu')).to_be_visible()


def run(browserName):
    runtime, process, url = start_server()
    try:
        with sync_playwright() as playwright:
            options = {'headless':True}
            executable = os.environ.get('CCS_CHROMIUM_EXECUTABLE') or os.environ.get('CS2_CHROMIUM_BIN')
            if browserName == 'chromium' and executable:
                options['executable_path'] = executable
            browser = getattr(playwright, browserName).launch(**options)
            context = browser.new_context(viewport={'width':1366,'height':900})
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(url)
            page.locator('.brand').dispatch_event('click')
            expect(page.locator('#view')).to_be_hidden()
            page.locator('#pin').fill('wrong-pin')
            page.locator('#connect').click()
            expect(page.locator('#loginerror')).to_contain_text('Incorrect PIN')
            login(page, url)
            expect(page.locator('#board>.widget')).to_have_count(0)
            document = json.loads((Path(runtime.name) / 'data/profiles.json').read_bytes())
            assert document['format'] == 'ccs-dashboard-store'
            for path in ['/static/legacy.html','/static/js/studio.js','/static/js/profile-sync.js']:
                assert page.request.get(url + path).status == 404
            page.locator('[data-section="studio"]').click()
            page.locator('.studio-library-item[data-kind="health"] button').click()
            expect(page.locator('#studio-save-state')).to_contain_text('Draft kept locally')
            original = (Path(runtime.name) / 'data/profiles.json').read_bytes()
            page.locator('#studio-publish').click()
            expect(page.locator('#studio-save-state')).to_contain_text('Published version up to date')
            page.locator('#studio-leave').click()
            expect(page.locator('#board>.widget')).to_have_count(1)
            payload = {'auth':{'token':TOKEN}, 'map':{'name':'de_mirage','phase':'live','round':3},
                       'player':{'state':{'health':75}}}
            request = Request(url + '/gsi', data=json.dumps(payload).encode(),
                              headers={'Content-Type':'application/json'}, method='POST')
            assert urlopen(request).status == 200
            expect(page.locator('#board [data-v="health"]')).to_have_text('75')
            assert (Path(runtime.name) / 'data/profiles.json').read_bytes() != original
            published = (Path(runtime.name) / 'data/profiles.json').read_bytes()
            assert json.loads(published)['profiles'][0]['revision'] == 2
            for width, height in [(1366,900),(390,844),(320,740)]:
                page.set_viewport_size({'width':width,'height':height})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
            assert not errors, errors
            context.close()
            browser.close()
        print('PASS: fresh target initialization, PIN gate, Studio publication, GSI and responsive production')
    finally:
        stop_server(runtime, process)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser', choices=['chromium','firefox','webkit'], default='chromium')
    run(parser.parse_args().browser)
