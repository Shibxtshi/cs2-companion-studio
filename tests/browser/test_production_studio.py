"""Exercise the distributed composition using the real ASGI entry point."""
import argparse
from contextlib import contextmanager
import copy
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen

from playwright.sync_api import expect, sync_playwright
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from companion.profile_activation import target_document
from companion.profile_contracts import encode_document

PIN = 'synthetic-production-pin'


@contextmanager
def production(initial=None):
    with tempfile.TemporaryDirectory(prefix='ccs-production-browser-') as temporary:
        runtime = Path(temporary)
        data = runtime / 'data'
        data.mkdir()
        if initial is None:
            initial = target_document()
            second = copy.deepcopy(initial['profiles'][0])
            second.update(id='p-second', name='Second Screen')
            initial['profiles'].append(second)
        (data / 'profiles.json').write_bytes(encode_document(initial))
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 0))
            port = listener.getsockname()[1]
        env = dict(os.environ, DASHBOARD_PIN=PIN, GSI_TOKEN='synthetic-production-gsi',
                   PROFILE_DATA_DIR=str(data), DIAGNOSTICS_DIR=str(runtime / 'logs'), BOMB_TIMER_ENABLED='false')
        process = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'companion.server:app', '--host',
                                    '127.0.0.1', '--port', str(port), '--no-access-log'],
                                   cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        url = 'http://127.0.0.1:' + str(port)
        try:
            for _ in range(100):
                if process.poll() is not None:
                    raise RuntimeError(process.stderr.read().decode())
                try:
                    urlopen(url + '/health', timeout=.3)
                    break
                except OSError:
                    time.sleep(.1)
            else:
                raise RuntimeError('Synthetic production server did not start')
            def restart():
                nonlocal process
                if os.name == 'nt':
                    subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                else:
                    process.terminate()
                process.wait(timeout=10)
                process = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'companion.server:app', '--host',
                                            '127.0.0.1', '--port', str(port), '--no-access-log'],
                                           cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                for _ in range(100):
                    if process.poll() is not None:
                        raise RuntimeError(process.stderr.read().decode())
                    try:
                        urlopen(url + '/health', timeout=.3)
                        return
                    except OSError:
                        time.sleep(.1)
                raise RuntimeError('Synthetic production restart failed')
            yield url, data, initial, restart
        finally:
            if os.name == 'nt':
                subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            else:
                process.terminate()
            process.wait(timeout=10)


def login(page, url):
    page.goto(url)
    page.locator('#pin').fill(PIN)
    page.locator('#connect').click()
    expect(page.locator('#dashboard-profile-menu')).to_be_visible()


def run(browser, output):
    with production() as (url, data, initial, restart):
        context = browser.new_context(viewport={'width':1366, 'height':900}, has_touch=True, accept_downloads=True)
        page, other = context.new_page(), context.new_page()
        errors, commands = [], []
        for tab in [page, other]:
            tab.on('pageerror', lambda error: errors.append(str(error)))
        def proxy(socket):
            server = socket.connect_to_server()
            server.on_message(socket.send)
            def forward(raw):
                commands.append(json.loads(raw).get('type'))
                server.send(raw)
            socket.on_message(forward)
        page.route_web_socket('**/ws', proxy)
        login(page, url)
        login(other, url)
        firstId = initial['profiles'][0]['id']
        other.select_option('#dashboard-profile-menu', 'p-second')
        page.locator('[data-section="studio"]').click()
        expect(page.locator('#studio-app')).to_be_visible()
        page.locator('.studio-library-item[data-kind="health"] button').click()
        expect(page.locator('#studio-board .widget')).to_have_count(1)
        page.select_option('#studio-variant', 'minimal')
        expect(page.locator('#studio-save-state')).to_contain_text('Draft kept locally')
        assert 'profile_operation' not in commands
        assert len(json.loads((data / 'profiles.json').read_bytes())['profiles'][0]['configuration']['layout']['widgets']) == 0
        page.locator('#studio-undo').click()
        expect(page.locator('#studio-variant')).to_have_value('standard')
        page.locator('#studio-redo').click()
        expect(page.locator('#studio-variant')).to_have_value('minimal')
        page.locator('#studio-publish').click()
        expect(page.locator('#studio-save-state')).to_contain_text('Published version up to date')
        assert commands.count('auth') == 1
        assert commands.count('profile_operation') == 1
        assert 'profiles_save' not in commands
        assert other.locator('#dashboard-profile-menu').input_value() == 'p-second'
        page.locator('.studio-brand').click()
        expect(page.locator('#studio-app')).to_be_hidden()
        expect(page.locator('#board .widget')).to_have_count(1)
        assert page.locator('#board .widget').get_attribute('data-variant') == 'minimal'
        assert page.locator('#dashboard-profile-menu').input_value() == firstId
        restart()
        for _ in range(100):
            if commands.count('auth') >= 2:
                break
            page.wait_for_timeout(100)
        assert commands.count('auth') == 2, 'The same browser reconnects with its in-memory PIN'
        expect(page.locator('#board .widget')).to_have_attribute('data-variant', 'minimal')
        page.locator('[data-section="settings"]').click()
        expect(page.locator('#production-profile-preferences')).to_contain_text('My dashboard')
        page.locator('.nav-brand').focus()
        page.keyboard.press('Enter')
        expect(page.locator('html')).to_have_attribute('data-section', 'dashboard')
        page.locator('[data-section="studio"]').click()
        with page.expect_download() as downloading:
            page.locator('#production-export').click()
        exported = json.loads(Path(downloading.value.path()).read_text('utf-8'))
        assert exported['format'] == 'ccs-dashboard-export'
        assert set(exported) == {'format', 'version', 'name', 'configuration'}
        assert exported['configuration']['layout']['widgets'][0]['variant'] == 'minimal'
        # Selecting a file is validation/review only; replacement remains a local edit.
        original = (data / 'profiles.json').read_bytes()
        exported['name'] = 'Reviewed import'
        page.locator('#production-import-file').set_input_files({'name':'synthetic-profile.json',
            'mimeType':'application/json', 'buffer':json.dumps(exported).encode()})
        expect(page.locator('#studio-dialog')).to_be_visible()
        assert (data / 'profiles.json').read_bytes() == original
        page.locator('#studio-dialog button[value="replace"]').click()
        expect(page.locator('#studio-save-state')).to_contain_text('Draft kept locally')
        assert (data / 'profiles.json').read_bytes() == original
        page.locator('#studio-leave').click()
        expect(page.locator('#studio-app')).to_be_hidden()
        page.reload()
        page.locator('#pin').fill(PIN)
        page.locator('#connect').click()
        expect(page.locator('#dashboard-profile-menu')).to_be_visible()
        page.locator('[data-section="studio"]').click()
        page.locator('#studio-dialog button[value="resume"]').click()
        expect(page.locator('#studio-save-state')).to_contain_text('Draft kept locally')
        assert (data / 'profiles.json').read_bytes() == original
        output.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(output / 'production-studio-desktop.png'), full_page=True)
        for width, height in [(768,1024), (390,844), (320,740)]:
            page.set_viewport_size({'width':width, 'height':height})
            page.screenshot(path=str(output / ('production-studio-' + str(width) + '.png')), full_page=True)
            overflow = page.evaluate('() => [...document.querySelectorAll("body *")].filter(el=>el.getBoundingClientRect().right>innerWidth+1).slice(0,12).map(el=>({id:el.id,tag:el.tagName,classes:el.className,right:el.getBoundingClientRect().right}))')
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), (width, overflow)
        page.set_viewport_size({'width':1366, 'height':900})
        device = browser.new_context(viewport={'width':1366, 'height':900})
        remote = device.new_page()
        login(remote, url)
        remote.select_option('#dashboard-profile-menu', firstId)
        remote.locator('[data-section="studio"]').click()
        remote.locator('.studio-library-item[data-kind="armor"] button').click()
        remote.locator('#studio-publish').click()
        expect(remote.locator('#studio-save-state')).to_contain_text('Published version up to date')
        page.locator('#studio-publish').click()
        expect(page.locator('#studio-conflict')).to_be_visible()
        expect(page.locator('#studio-save-state')).to_contain_text('Server version changed')
        page.screenshot(path=str(output / 'production-remote-conflict.png'))
        assert json.loads((data / 'profiles.json').read_bytes())['profiles'][0]['name'] == 'My dashboard'
        device.close()
        assert not errors, errors
        context.close()


def catalogue(browser, output):
    corpus = json.loads((ROOT / 'tests/browser/fixtures/draft-contracts.json').read_text('utf-8'))
    widget = corpus['profile']['configuration']['layout']['widgets'][0]
    from companion.profile_store import PROFILE_KINDS
    initial = target_document()
    configuration = initial['profiles'][0]['configuration']
    kinds = sorted(PROFILE_KINDS)
    configuration['layout']['widgets'] = [{**widget, 'id':'widget-' + str(index), 'kind':kinds[index % 29],
        'x':index % 3 * 8, 'y':index // 3 * 8, 'width':8, 'height':8,
        'variant':['standard','compact','minimal'][index % 3]} for index in range(60)]
    smaller = copy.deepcopy(initial['profiles'][0])
    smaller.update(id='p-29', name='29 widgets')
    smaller['configuration']['layout']['widgets'] = smaller['configuration']['layout']['widgets'][:29]
    initial['profiles'].append(smaller)
    with production(initial) as (url, data, _, _restart):
        page = browser.new_page(viewport={'width':1920,'height':1080})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        login(page, url)
        expect(page.locator('#board>.widget')).to_have_count(60)
        original = (data / 'profiles.json').read_bytes()
        page.screenshot(path=str(output / 'production-dashboard-60.png'))
        page.select_option('#dashboard-profile-menu', 'p-29')
        expect(page.locator('#board>.widget')).to_have_count(29)
        page.screenshot(path=str(output / 'production-dashboard-29.png'))
        page.select_option('#dashboard-profile-menu', initial['profiles'][0]['id'])
        page.locator('[data-section="studio"]').click()
        expect(page.locator('#studio-board>.widget')).to_have_count(60)
        for index in range(29):
            card = page.locator('#studio-board>.widget').nth(index)
            card.click(position={'x':15,'y':15})
            for variant in ['standard','compact','minimal']:
                page.select_option('#studio-variant', variant)
                expect(card).to_have_attribute('data-variant', variant)
        page.locator('#studio-profile-tab').click()
        for theme in ['tactical-blue','competitive-red','performance-green','creator-purple']:
            page.select_option('#studio-theme', theme)
            expect(page.locator('html')).to_have_attribute('data-theme', theme)
        assert (data / 'profiles.json').read_bytes() == original
        assert not errors, errors
        page.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser', choices=['chromium', 'firefox', 'webkit'], default='chromium')
    parser.add_argument('--output', type=Path, default=Path('production-browser-results'))
    args = parser.parse_args()
    with sync_playwright() as playwright:
        options = {}
        if args.browser == 'chromium' and os.environ.get('CCS_CHROMIUM_EXECUTABLE'):
            options['executable_path'] = os.environ['CCS_CHROMIUM_EXECUTABLE']
        browser = getattr(playwright, args.browser).launch(headless=True, **options)
        try:
            run(browser, args.output)
            catalogue(browser, args.output)
        finally:
            browser.close()
    print('PASS: real production composition, shared PIN session, isolated tab selection, draft/history, explicit publication, export and responsive Studio')
