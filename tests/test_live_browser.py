"""Real HTTP + WebSocket E2E. Usage: python tests/test_live_browser.py --browser chromium|firefox|webkit"""
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

ROOT = Path(__file__).resolve().parents[1]
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
    proc = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app:app',
                             '--host', '127.0.0.1', '--port', str(port), '--no-access-log'],
                            cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    url = f'http://127.0.0.1:{port}'
    for _ in range(80):
        if proc.poll() is not None:
            err = proc.stderr.read().decode('utf-8', 'replace')[:1400]
            raise RuntimeError('Server crashed: ' + err)
        try:
            with urlopen(url + '/health', timeout=.3) as response:
                if json.load(response)['version'] == '1.0.0':
                    return runtime, proc, url
        except (URLError, TimeoutError, OSError):
            time.sleep(.1)
    proc.terminate()
    raise TimeoutError('HTTP server did not become ready')


def login(page, url):
    page.goto(url, wait_until='domcontentloaded')
    page.locator('#pin').fill(PIN)
    page.locator('#connect').click()
    page.locator('#tab-custom').wait_for(state='visible', timeout=10000)
    assert page.locator('#profile-select option').count() == 1


def run(browser_name):
    runtime, proc, url = start_server()
    try:
        with sync_playwright() as playwright:
            options = {'headless': True}
            if browser_name == 'chromium' and os.environ.get('CS2_CHROMIUM_BIN'):
                options['executable_path'] = os.environ['CS2_CHROMIUM_BIN']
                options['args'] = ['--no-sandbox']
            browser = getattr(playwright, browser_name).launch(**options)
            desktop = browser.new_context(viewport={'width': 1280, 'height': 900})
            phone = browser.new_context(viewport={'width': 390, 'height': 844}, is_mobile=(browser_name != 'firefox'))
            guest = browser.new_context()
            errors = []
            # Guest: public demo must never contain private server profile name.
            public = guest.new_page()
            public.on('pageerror', lambda error: errors.append(str(error)))
            public.goto(url)
            public.locator('#demo').click()
            assert not public.locator('#tab-custom').is_visible()
            assert public.locator('#download-support').is_hidden()

            a = desktop.new_page()
            a.on('pageerror', lambda error: errors.append(str(error)))
            faults = {'next': None}

            def route_socket(socket):
                server = socket.connect_to_server()
                server.on_message(socket.send)

                def forward(message):
                    command = json.loads(message)
                    if command.get('type') == 'profiles_save' and faults['next']:
                        fault = faults['next']
                        faults['next'] = None
                        if fault == 'disconnect':
                            socket.close(code=1012, reason='Synthetic reconnect test')
                            server.close()
                            return
                        if fault == 'conflict':
                            command['revision'] = -1
                        else:
                            command['document'] = {}
                        server.send(json.dumps(command))
                    else:
                        server.send(message)
                socket.on_message(forward)

            a.route_web_socket('**/ws', route_socket)
            login(a, url)
            a.locator('#tab-custom').click()
            a.on('dialog', lambda dialog: dialog.accept('Shared v1.0.0 setup'))
            a.locator('#rename-profile').click()
            expect(a.locator('#profile-select')).to_contain_text('Shared v1.0.0 setup', timeout=8000)

            b = phone.new_page()
            b.on('pageerror', lambda error: errors.append(str(error)))
            login(b, url)
            b.locator('#tab-custom').click()
            expect(b.locator('#profile-select')).to_contain_text('Shared v1.0.0 setup', timeout=8000)

            # Observe the live status in the DOM instead of evaluating JS:
            # Firefox correctly enforces the app's restrictive CSP.
            # Real simulated GSI POST must propagate over WS to both authenticated devices.
            body = json.dumps({'auth': {'token': TOKEN},
                'map': {'name': 'de_mirage', 'phase': 'live', 'round': 3,
                        'team_ct': {'score': 2}, 'team_t': {'score': 1}},
                'round': {'phase': 'live'},
                'player': {'name': 'Synthetic test player', 'team': 'CT',
                           'state': {'health': 77, 'money': 2600}}}).encode()
            with urlopen(Request(url+'/gsi', body, {'Content-Type': 'application/json'}, method='POST'), timeout=5) as r:
                assert r.status == 200
            expect(a.locator('#session-banner')).to_have_attribute('data-state', 'live', timeout=8000)
            expect(b.locator('#session-banner')).to_have_attribute('data-state', 'live', timeout=8000)

            # Search must work in either language, and no JS runtime errors.
            a.locator('#edit').click()
            a.locator('#add').click()
            a.locator('#search-widgets').fill('map')
            assert a.locator('#catalog-items .catalog-item').count() >= 1
            a.locator('#locale-select').select_option('FR')
            a.locator('#search-widgets').fill('carte')
            assert a.locator('#catalog-items .catalog-item').count() >= 1
            assert not errors, errors
            # Complete an actual widget edit and a JSON export/import round trip.
            before = a.locator('#board .widget').count()
            a.locator('#catalog-items .catalog-item').first.click()
            expect(a.locator('#board .widget')).to_have_count(before + 1)
            expect(a.locator('#profile-save-panel')).to_be_hidden()
            with a.expect_download() as download_info:
                a.locator('#export').click()
            exported = Path(download_info.value.path()).read_bytes()
            a.locator('#import-file').set_input_files({'name': 'synthetic-layout.json', 'mimeType': 'application/json', 'buffer': exported})
            expect(a.locator('#profile-select option')).to_have_count(2)
            expect(a.locator('#profile-save-panel')).to_be_hidden()

            # Real server rejects a stale revision/invalid document; local edits survive.
            a.remove_all_listeners('dialog')
            rename = {'value': ''}
            a.on('dialog', lambda dialog: dialog.accept(rename['value']))
            for fault in ('conflict', 'invalid', 'disconnect'):
                faults['next'] = fault
                rename['value'] = 'Retained ' + fault
                a.locator('#rename-profile').click()
                expect(a.locator('#profile-save-panel')).to_be_visible()
                expect(a.locator('#profile-select')).to_contain_text(rename['value'])
                expect(a.locator('#profile-save-retry')).to_be_visible(timeout=12000)
                # For reconnect, wait until the new authenticated snapshot arrives.
                if fault == 'disconnect':
                    expect(a.locator('#profile-save-message')).to_contain_text('serveur', timeout=12000)
                a.locator('#profile-save-retry').click()
                expect(a.locator('#profile-save-panel')).to_be_hidden(timeout=10000)
                expect(b.locator('#profile-select')).to_contain_text(rename['value'])
            # Explicitly loading the server version discards only after user action.
            faults['next'] = 'conflict'
            rename['value'] = 'Discard this local edit'
            a.locator('#rename-profile').click()
            expect(a.locator('#profile-save-discard')).to_be_visible()
            a.locator('#profile-save-discard').click()
            expect(a.locator('#profile-select')).to_contain_text('Retained disconnect')
            expect(a.locator('#profile-save-panel')).to_be_hidden()
            assert not errors, errors
            browser.close()
        # Data is server-side and persists after clients disconnect.
        store = json.loads((Path(runtime.name) / 'data' / 'profiles.json').read_text('utf-8'))
        assert store['profiles'][0]['name'] == 'Shared v1.0.0 setup'
        print(f'OK: {browser_name} real server, demo isolation, auth, shared profiles, mobile, GSI propagation, bilingual search')
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill(); proc.wait(timeout=5)
        runtime.cleanup()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--browser', choices=['chromium', 'firefox', 'webkit'], default='chromium')
    run(parser.parse_args().browser)
