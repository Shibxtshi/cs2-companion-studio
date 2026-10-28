"""Real IndexedDB persistence, fault injection and tab isolation on synthetic data."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import statistics
import tempfile

from playwright.sync_api import sync_playwright
from test_live_browser import PIN, TOKEN, ROOT, login, start_server

MODULES = ('draft-schema', 'draft-contract', 'edit-history', 'draft-store', 'draft-session')
CORPUS = json.loads((ROOT / 'tests/browser/fixtures/draft-contracts.json').read_text('utf-8'))
HARNESS = (ROOT / 'tests/browser/draft-harness.js').read_text('utf-8')


def prepare(page, url, errors, commands):
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('websocket', lambda socket: socket.on('framesent', lambda frame: commands.append(frame)))
    login(page, url)
    page.route('**/static/js/draft-test-harness.js',
               lambda route: route.fulfill(body=HARNESS, content_type='application/javascript'))
    for module in (*MODULES, 'draft-test-harness'):
        page.add_script_tag(url=url + '/static/js/' + module + '.js')
    page.evaluate('profile => draftHarness.initialize(profile)', CORPUS['profile'])


def run(browserName, output):
    runtime, process, url = start_server()
    errors, commands = [], []
    results = {}
    profilePath = Path(runtime.name) / 'data/profiles.json'
    original = profilePath.read_bytes()
    try:
        with tempfile.TemporaryDirectory(prefix='ccs-browser-drafts-') as userData:
            with sync_playwright() as playwright:
                options = {'headless': True, 'viewport': {'width': 1280, 'height': 900},
                           'locale': 'en-US', 'timezone_id': 'UTC'}
                if browserName == 'chromium' and os.environ.get('CS2_CHROMIUM_BIN'):
                    options.update(executable_path=os.environ['CS2_CHROMIUM_BIN'], args=['--no-sandbox'])
                engine = getattr(playwright, browserName)
                context = engine.launch_persistent_context(userData, **options)
                try:
                    a = context.new_page()
                    prepare(a, url, errors, commands)
                    a.evaluate('draftHarness.create()')
                    a.reload()
                    prepare(a, url, errors, commands)
                    a.evaluate('draftHarness.restore()')
                finally:
                    context.close()
                # A fresh browser process reuses only its temporary on-disk browser profile.
                context = engine.launch_persistent_context(userData, **options)
                try:
                    a, b = context.new_page(), context.new_page()
                    prepare(a, url, errors, commands)
                    prepare(b, url, errors, commands)
                    results['revisionAfterReopen'] = a.evaluate('draftHarness.restore()')
                    a.evaluate('draftHarness.failureCases()')
                    a.reload()
                    prepare(a, url, errors, commands)
                    a.evaluate('draftHarness.restore()')
                    a.evaluate('draftHarness.corruptionCases()')
                    b.evaluate('draftHarness.readForRace()')
                    a.evaluate('draftHarness.winRace()')
                    b.evaluate('draftHarness.loseRace()')
                    b.evaluate('draftHarness.distinctProfile()')
                    a.evaluate('draftHarness.isolation()')
                    a.evaluate('draftHarness.aba()')
                    a.evaluate('draftHarness.cancelledLogout()')
                    # A network outage does not disable local configuration persistence.
                    context.set_offline(True)
                    results['performance'] = a.evaluate('draftHarness.benchmark()')
                    context.set_offline(False)
                    a.evaluate('draftHarness.corruptSecondaryMetadata()')
                    a.evaluate('draftHarness.logout()')
                    b.evaluate('draftHarness.revoked()')
                    a.evaluate('draftHarness.afterLogout()')
                    a.evaluate('([pin, token]) => draftHarness.inspectSecrets(pin, token)', [PIN, TOKEN])
                    b.evaluate('draftHarness.close()')
                    a.evaluate('draftHarness.futureDatabase()')
                    assert not errors, errors
                finally:
                    context.close()
        # HTTP LAN origins must not require secure-context-only randomUUID().
        with sync_playwright() as playwright:
            options = {'headless': True}
            if browserName == 'chromium' and os.environ.get('CS2_CHROMIUM_BIN'):
                options.update(executable_path=os.environ['CS2_CHROMIUM_BIN'], args=['--no-sandbox'])
            browser = getattr(playwright, browserName).launch(**options)
            try:
                isolated = browser.new_context()
                assets = {module + '.js': (ROOT / 'static/js' / (module + '.js')).read_text('utf-8') for module in MODULES}
                assets['draft-test-harness.js'] = HARNESS
                def route_insecure(route):
                    name = route.request.url.rsplit('/', 1)[-1]
                    if name in assets:
                        route.fulfill(body=assets[name], content_type='application/javascript')
                    else:
                        route.fulfill(body='<html><body>Synthetic HTTP context</body></html>', content_type='text/html')
                isolated.route('http://ccs-drafts.invalid/**', route_insecure)
                page = isolated.new_page()
                page.goto('http://ccs-drafts.invalid/')
                assert not page.evaluate('window.isSecureContext')
                for module in (*MODULES, 'draft-test-harness'):
                    page.add_script_tag(url='http://ccs-drafts.invalid/' + module + '.js')
                page.evaluate('profile => draftHarness.initialize(profile)', CORPUS['profile'])
                page.evaluate('draftHarness.create()')
                page.evaluate('draftHarness.restore()')
                isolated.close()
            finally:
                browser.close()
        assert profilePath.read_bytes() == original, 'Draft foundation changed published server profiles'
        assert not any(json.loads(frame).get('type') == 'profiles_save' for frame in commands if isinstance(frame, str)), 'Draft foundation used server autosave'
        values = results['performance']
        summary = {'browser': browserName, 'widgets': 60,
                   'medianEditMs': round(statistics.median(values['edits']), 3),
                   'medianRestoreMs': round(statistics.median(values['restoreSamples']), 3),
                   'flushMs': round(values['flushMs'], 3),
                   'writesFor100Edits': values['writesFor100Edits'],
                   'writesFor100GestureMoves': values['writesFor100GestureMoves'],
                   'historyBytes': values['retainedHistory']['bytes']}
        if output:
            output.mkdir(parents=True, exist_ok=True)
            (output / (browserName + '-drafts.json')).write_text(json.dumps(results, indent=2), encoding='utf-8')
        print('OK: native IndexedDB reload/browser reopen, transactions/quota, tabs/CAS, logout, isolation, no secrets or server saves')
        print(json.dumps(summary, sort_keys=True))
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except Exception:
            process.kill()
            process.wait(timeout=5)
        runtime.cleanup()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--browser', choices=('chromium', 'firefox', 'webkit'), default='chromium')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    run(args.browser, args.output)
