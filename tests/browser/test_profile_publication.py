"""Synthetic full publication chain through the canonical ASGI app and native IndexedDB."""
from __future__ import annotations
import argparse
import copy
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import URLError
from urllib.request import urlopen

from playwright.sync_api import sync_playwright
from test_live_browser import ROOT
sys.path.insert(0, str(ROOT))
from companion.profile_contracts import encode_document, validate_contract
from companion.profile_publication import access_id, renewed_generation

PIN = 'synthetic-publication-pin'


def launch(runtime, port):
    env = dict(os.environ, GSI_TOKEN='synthetic-publication-gsi-token', DASHBOARD_PIN=PIN,
               PROFILE_DATA_DIR=str(runtime / 'legacy'), DIAGNOSTICS_DIR=str(runtime / 'logs'),
               BOMB_TIMER_ENABLED='false')
    process = subprocess.Popen([sys.executable, str(ROOT / 'tests/browser/publication_server.py'), str(runtime), str(port)],
                               cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    url = f'http://127.0.0.1:{port}'
    for _ in range(100):
        if process.poll() is not None:
            raise RuntimeError('Synthetic publication server failed: ' + process.stderr.read().decode()[:1600])
        try:
            with urlopen(url + '/health', timeout=.3):
                return process, url
        except (URLError, OSError):
            time.sleep(.1)
    process.terminate()
    raise RuntimeError('Synthetic publication server timeout')


def stop(process):
    if os.name == 'nt' and process.poll() is None:
        subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    elif process.poll() is None:
        process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill(); process.wait(timeout=5)


def prepare(context, url):
    page = context.new_page()
    page.goto(url + '/__publication_test__')
    page.wait_for_function('() => window.publicationHarness !== undefined')
    page.evaluate('pin => publicationHarness.connect(pin)', PIN)
    return page


def wait_state(page, code):
    page.wait_for_function('code => publicationHarness.snapshot().controller?.code === code', arg=code, timeout=12000)
    assert page.evaluate('publicationHarness.snapshot().errors') == []


def edit(page, profileId, name, choice='new'):
    page.evaluate('([id, name, choice]) => publicationHarness.edit(id, name, choice)', [profileId, name, choice])


def run(browserName, output):
    corpus = json.loads((ROOT / 'tests/browser/fixtures/draft-contracts.json').read_text('utf-8'))
    profile = corpus['profile']
    with tempfile.TemporaryDirectory(prefix='ccs-publication-e2e-') as temporary:
        runtime = Path(temporary)
        (runtime / '.synthetic-publication-test').touch()
        target = runtime / 'target/profiles.json'
        target.parent.mkdir()
        document = {'format': 'ccs-dashboard-store', 'version': 1, 'storeId': '1' * 32,
                    'catalogRevision': 7, 'profiles': [profile, {**copy.deepcopy(profile), 'id': 'p-second', 'revision': 1}],
                    'tombstones': [], 'receipts': []}
        target.write_bytes(encode_document(validate_contract(document, 'server')))
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 0)); port = listener.getsockname()[1]
        process, url = launch(runtime, port)
        measurements = []
        try:
            with sync_playwright() as playwright:
                options = {'headless': True}
                if browserName == 'chromium' and os.environ.get('CS2_CHROMIUM_BIN'):
                    options.update(executable_path=os.environ['CS2_CHROMIUM_BIN'], args=['--no-sandbox'])
                browser = getattr(playwright, browserName).launch(**options)
                contexts = []
                def context():
                    result = browser.new_context(viewport={'width': 1280, 'height': 900}, locale='en-US', timezone_id='UTC')
                    contexts.append(result)
                    return result
                try:
                    migrated = context()
                    old = migrated.new_page()
                    old.goto(url + '/__publication_test__')
                    seed = {**corpus['draftMetadata'], 'name': 'Preserved P4 draft',
                            'configuration': profile['configuration'], 'localRevision': 1}
                    old.evaluate("""async ({draft, accessId}) => {
                        const database = await new Promise((resolve, reject) => {
                            const request = indexedDB.open('ccs-local-drafts', 1);
                            request.onupgradeneeded = () => {
                                request.result.createObjectStore('contexts', {keyPath:'key'});
                                request.result.createObjectStore('drafts', {keyPath:'key'});
                            };
                            request.onsuccess = () => resolve(request.result);
                            request.onerror = () => reject(request.error);
                        });
                        await new Promise((resolve, reject) => {
                            const tx = database.transaction(['contexts','drafts'], 'readwrite');
                            const contextKey = JSON.stringify([draft.storeId, accessId]);
                            tx.objectStore('contexts').put({key:contextKey, epoch:0});
                            tx.objectStore('drafts').put({key:JSON.stringify([draft.storeId,accessId,1,draft.profileId]),
                                contextKey, writeId:'b'.repeat(32), createdAt:1000, draft});
                            tx.oncomplete = resolve; tx.onabort = () => reject(tx.error);
                        });
                        database.close();
                    }""", {'draft': seed, 'accessId': access_id(document['storeId'])})
                    old.evaluate('pin => publicationHarness.connect(pin)', PIN)
                    assert old.evaluate('id => publicationHarness.read(id).then(value => value.draft.name)', profile['id']) == 'Preserved P4 draft'
                    migrated.close()

                    shared = context()
                    a, b = prepare(shared, url), prepare(shared, url)
                    b.evaluate("publicationHarness.select('p-second')")
                    before = target.read_bytes()
                    edit(a, profile['id'], 'Explicit publication')
                    assert target.read_bytes() == before
                    a.evaluate("publicationHarness.setAckMode('hold'); publicationHarness.begin(); publicationHarness.begin()")
                    a.wait_for_function('() => publicationHarness.snapshot().sent.length === 1')
                    assert a.evaluate('publicationHarness.tryEdit()') == 'publication_locked'
                    assert a.evaluate('publicationHarness.snapshot().controller.code') == 'publishing'
                    a.wait_for_function("() => publicationHarness.snapshot().catalog.profiles[0].name === 'Explicit publication'")
                    a.evaluate('publicationHarness.release()')
                    wait_state(a, 'published')
                    assert b.evaluate('publicationHarness.snapshot().selected') == 'p-second'
                    assert a.evaluate('publicationHarness.inspectStorage()') == {'drafts': 0, 'publications': 0}

                    edit(a, profile['id'], 'Independent profile A')
                    edit(b, 'p-second', 'Independent profile B')
                    a.evaluate('publicationHarness.begin()')
                    b.evaluate('publicationHarness.begin()')
                    wait_state(a, 'published'); wait_state(b, 'published')
                    assert json.loads(target.read_bytes())['profiles'][1]['name'] == 'Independent profile B'

                    edit(a, profile['id'], 'Quota retains draft')
                    sent = a.evaluate('publicationHarness.snapshot().sent.length')
                    a.evaluate('publicationHarness.setQueueQuota(true); publicationHarness.begin()')
                    wait_state(a, 'local_error')
                    assert a.evaluate('publicationHarness.snapshot().sent.length') == sent
                    a.evaluate('publicationHarness.setQueueQuota(false); publicationHarness.begin()')
                    wait_state(a, 'published')

                    edit(a, profile['id'], 'Published cleanup failure')
                    a.evaluate('publicationHarness.setCleanupAbort(true); publicationHarness.begin()')
                    wait_state(a, 'published_cleanup_error')
                    assert a.evaluate('publicationHarness.snapshot().controller.serverCommitted')
                    assert a.evaluate('publicationHarness.inspectStorage()') == {'drafts': 1, 'publications': 1}
                    sent = a.evaluate('publicationHarness.snapshot().sent.length')
                    a.evaluate('publicationHarness.setCleanupAbort(false); publicationHarness.retry()')
                    wait_state(a, 'published')
                    assert a.evaluate('publicationHarness.snapshot().sent.length') == sent

                    edit(a, profile['id'], 'Lost response survives reload')
                    a.evaluate("publicationHarness.setAckMode('drop'); publicationHarness.begin()")
                    wait_state(a, 'publication_uncertain')
                    lostId = a.evaluate('publicationHarness.snapshot().sent.at(-1).operationId')
                    before = target.read_bytes()
                    a.close()
                    a = prepare(shared, url)
                    a.evaluate('id => publicationHarness.reopen(id)', profile['id'])
                    wait_state(a, 'reconciliation_required')
                    a.evaluate('publicationHarness.retry()')
                    wait_state(a, 'published')
                    assert a.evaluate('publicationHarness.snapshot().sent.at(-1).operationId') == lostId
                    assert target.read_bytes() == before

                    edit(a, profile['id'], 'Committed before restart')
                    revision = a.evaluate('publicationHarness.snapshot().catalog.catalogRevision')
                    a.evaluate("publicationHarness.setAckMode('hold'); publicationHarness.begin()")
                    a.wait_for_function('revision => publicationHarness.snapshot().catalog.catalogRevision > revision', arg=revision)
                    stop(process)
                    process, url = launch(runtime, port)
                    a.evaluate('pin => publicationHarness.connect(pin)', PIN)
                    a.evaluate('publicationHarness.setAckMode(null); publicationHarness.retry()')
                    wait_state(a, 'published')
                    a.evaluate('publicationHarness.release()')

                    edit(a, profile['id'], 'Captured older snapshot')
                    a.evaluate("publicationHarness.setAckMode('hold'); publicationHarness.begin()")
                    a.wait_for_function("() => publicationHarness.snapshot().catalog.profiles[0].name === 'Captured older snapshot'")
                    a.evaluate("publicationHarness.preserveNewer('Newer retained edits')")
                    a.evaluate('publicationHarness.release()')
                    wait_state(a, 'published_draft_retained')
                    assert a.evaluate('id => publicationHarness.read(id).then(value => value.draft.name)', profile['id']) == 'Newer retained edits'
                    assert json.loads(target.read_bytes())['profiles'][0]['name'] == 'Captured older snapshot'
                    a.evaluate('publicationHarness.discard()')

                    other = context()
                    c = prepare(other, url)
                    edit(a, profile['id'], 'Device A winner')
                    edit(c, profile['id'], 'Device C replacement')
                    a.evaluate('publicationHarness.begin()'); wait_state(a, 'published')
                    c.evaluate('publicationHarness.begin()'); wait_state(c, 'revision_conflict')
                    reviewed = c.evaluate('publicationHarness.snapshot().catalog.profiles[0].revision')
                    c.evaluate('revision => publicationHarness.useLocal({confirmed:false, reviewedRevision:revision})', reviewed)
                    assert c.evaluate('window.publicationResult') == {'error': 'confirmation_required'}
                    oldBase = c.evaluate('id => publicationHarness.read(id).then(value => value.draft.baseRevision)', profile['id'])
                    c.evaluate('revision => {publicationHarness.setAckMode("hold"); publicationHarness.useLocal({confirmed:true, reviewedRevision:revision});}', reviewed)
                    c.wait_for_function('() => publicationHarness.snapshot().sent.length === 2')
                    assert c.evaluate('id => publicationHarness.read(id).then(value => value.draft.baseRevision)', profile['id']) == oldBase
                    c.evaluate('publicationHarness.release()'); wait_state(c, 'published')
                    assert c.evaluate('publicationHarness.snapshot().sent[0].operationId !== publicationHarness.snapshot().sent[1].operationId')
                    edit(a, profile['id'], 'Server choice winner')
                    edit(c, profile['id'], 'Discard after review')
                    a.evaluate('publicationHarness.begin()'); wait_state(a, 'published')
                    c.evaluate('publicationHarness.begin()'); wait_state(c, 'revision_conflict')
                    reviewed = c.evaluate('publicationHarness.snapshot().catalog.profiles[0].revision')
                    c.evaluate('revision => publicationHarness.useServer({confirmed:true, reviewedRevision:revision})', reviewed)
                    wait_state(c, 'server_kept')
                    assert c.evaluate('publicationHarness.inspectStorage()') == {'drafts': 0, 'publications': 0}
                    other.close()

                    b.evaluate('pin => publicationHarness.connect(pin)', PIN)
                    edit(a, profile['id'], 'Older tab memory')
                    edit(b, profile['id'], 'Newer tab draft', 'resume')
                    before = target.read_bytes()
                    a.evaluate('publicationHarness.begin()'); wait_state(a, 'local_conflict')
                    assert target.read_bytes() == before
                    b.evaluate('publicationHarness.begin()'); wait_state(b, 'published')
                    shared.close()

                    management = context()
                    d = prepare(management, url)
                    d.evaluate('content => publicationHarness.create("p-created", content)', {'name': 'Created profile', 'configuration': profile['configuration']})
                    wait_state(d, 'published')
                    edit(d, 'p-created', 'Orphan draft')
                    revision = d.evaluate('publicationHarness.snapshot().catalog.profiles.find(value => value.id === "p-created").revision')
                    d.evaluate('revision => publicationHarness.remove("p-created", revision)', arg=revision)
                    wait_state(d, 'published')
                    assert d.evaluate('publicationHarness.inspect("p-created").then(value => value.status)') == 'profile_deleted'
                    assert d.evaluate('publicationHarness.read("p-created").then(value => value.status)') == 'valid'
                    management.close()

                    logoutContext = context()
                    logoutA, logoutB = prepare(logoutContext, url), prepare(logoutContext, url)
                    edit(logoutA, profile['id'], 'Confirmed logout')
                    logoutA.evaluate("publicationHarness.setAckMode('hold'); publicationHarness.begin()")
                    logoutA.wait_for_function("() => publicationHarness.snapshot().catalog.profiles[0].name === 'Confirmed logout'")
                    logoutA.evaluate('publicationHarness.logout()')
                    assert logoutB.evaluate('async id => {try {await publicationHarness.read(id);} catch(error) {return error.code;}}', profile['id']) == 'context_revoked'
                    logoutA.evaluate('pin => publicationHarness.connect(pin)', PIN)
                    assert logoutA.evaluate('publicationHarness.inspectStorage()') == {'drafts': 0, 'publications': 0}
                    logoutContext.close()

                    generation = context()
                    e = prepare(generation, url)
                    edit(e, profile['id'], 'Old-generation operation')
                    e.evaluate("publicationHarness.setAckMode('drop'); publicationHarness.begin()")
                    wait_state(e, 'publication_uncertain')
                    stop(process)
                    target.write_bytes(encode_document(renewed_generation(json.loads(target.read_bytes()))))
                    process, url = launch(runtime, port)
                    e.evaluate('pin => publicationHarness.connect(pin)', PIN)
                    before = target.read_bytes()
                    e.evaluate('publicationHarness.retry()'); wait_state(e, 'store_changed')
                    e.evaluate('publicationHarness.rawRetry()'); wait_state(e, 'store_changed')
                    assert target.read_bytes() == before
                    generation.close()

                    measured = context()
                    observer1, observer2, p = prepare(measured, url), prepare(measured, url), prepare(measured, url)
                    for _ in range(7):
                        result = p.evaluate('id => publicationHarness.benchmark(id)', profile['id'])
                        assert result['status'] == 'published'
                        measurements.append(result)
                    revision = p.evaluate('publicationHarness.snapshot().catalog.catalogRevision')
                    for observer in (observer1, observer2):
                        observer.wait_for_function('revision => publicationHarness.snapshot().catalog.catalogRevision >= revision', arg=revision)
                    assert p.evaluate('publicationHarness.inspectStorage()') == {'drafts': 0, 'publications': 0}
                    measured.close()
                finally:
                    browser.close()
            if output:
                output.mkdir(parents=True, exist_ok=True)
                (output / (browserName + '-publication.json')).write_text(json.dumps({'clients': 3, 'samples': measurements}, indent=2), encoding='utf-8')
            print('OK: real authenticated publication, IndexedDB journal/reload, restart/retry, explicit conflicts, retained newer edits, local cleanup, tabs, create/delete and generation isolation')
            print(json.dumps({'browser': browserName, 'clients': 3, 'publication60WidgetsMs': [round(value['elapsedMs'], 2) for value in measurements]}))
        finally:
            stop(process)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--browser', choices=('chromium', 'firefox', 'webkit'), default='chromium')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    run(args.browser, args.output)
