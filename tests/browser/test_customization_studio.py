"""First P8 review journey against a disposable, authenticated target store."""
from __future__ import annotations
import argparse
import copy
import json
import os
from pathlib import Path
import socket
import sys
import tempfile

from playwright.sync_api import expect, sync_playwright
from test_profile_publication import ROOT, PIN, launch, stop, prepare, edit, wait_state
from widget_fixtures import LIVE, settle
sys.path.insert(0, str(ROOT))
from companion.profile_contracts import encode_document, validate_contract


def document():
    corpus = json.loads((ROOT / 'tests/browser/fixtures/draft-contracts.json').read_text('utf-8'))
    profile = copy.deepcopy(corpus['profile'])
    profile.update(id='p-competitive', name='Competitive', revision=1)
    base = profile['configuration']['layout']['widgets'][0]
    rectangles = [('score', 0, 0, 12, 6), ('health', 12, 0, 6, 6), ('armor', 18, 0, 6, 6),
                  ('weapon', 0, 6, 8, 6), ('economy', 8, 6, 8, 8), ('round', 16, 6, 8, 6),
                  ('stats', 0, 14, 8, 6), ('inventory', 8, 14, 16, 8)]
    profile['configuration']['layout'] = {'columns': 24, 'widgets': [
        {**base, 'id': 'studio-' + kind, 'kind': kind, 'x': x, 'y': y, 'width': width,
         'height': height, 'variant': 'standard'} for kind, x, y, width, height in rectangles]}
    second = copy.deepcopy(profile)
    second.update(id='p-second', name='Second Screen')
    return validate_contract({'format': 'ccs-dashboard-store', 'version': 1, 'storeId': '8' * 32,
        'catalogRevision': 1, 'profiles': [profile, second], 'receipts': [], 'tombstones': []}, 'server')


def run(browserName, output):
    with tempfile.TemporaryDirectory(prefix='ccs-studio-review-') as temporary:
        runtime = Path(temporary)
        (runtime / '.synthetic-publication-test').touch()
        target = runtime / 'target/profiles.json'
        target.parent.mkdir()
        target.write_bytes(encode_document(document()))
        original = target.read_bytes()
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 0))
            port = listener.getsockname()[1]
        process, url = launch(runtime, port)
        try:
            with sync_playwright() as playwright:
                options = {'headless': True}
                if browserName == 'chromium' and os.environ.get('CS2_CHROMIUM_BIN'):
                    options.update(executable_path=os.environ['CS2_CHROMIUM_BIN'], args=['--no-sandbox'])
                browser = getattr(playwright, browserName).launch(**options)
                context = browser.new_context(viewport={'width': 1920, 'height': 1080},
                    locale='fr-FR', timezone_id='UTC', reduced_motion='reduce')
                page = context.new_page()
                faults = []
                page.on('pageerror', lambda error: faults.append(str(error)))

                def enter():
                    page.goto(url + '/__studio_test__')
                    page.select_option('#locale-select', 'FR')
                    page.locator('#pin').fill(PIN)
                    page.locator('#connect').click()
                    expect(page.locator('#studio-app')).to_be_visible()

                def capture(name):
                    if output:
                        output.mkdir(parents=True, exist_ok=True)
                        settle(page)
                        page.screenshot(path=str(output / (name + '.png')))

                def saved():
                    page.wait_for_function("() => ['saved','pristine'].includes(CCSStudioTarget.snapshot().state?.status)")

                enter()
                expect(page.locator('#studio-board > .widget')).to_have_count(8)
                page.evaluate('state => CCSStudioTarget.previewData(state, true)', LIVE)
                saved()
                expect(page.locator('#studio-library-items .studio-library-item')).to_have_count(29)
                capture('01-desktop')
                page.locator('#studio-board .w-health').click()
                expect(page.locator('#studio-variant')).to_have_value('standard')
                capture('02-selected-health')
                page.evaluate('window.retainedCard=document.querySelector(".w-health")')
                page.select_option('#studio-variant', 'minimal')
                saved()
                assert page.evaluate('window.retainedCard===document.querySelector(".w-health")')
                expect(page.locator('#studio-board .w-health')).to_have_attribute('data-variant', 'minimal')
                page.locator('#studio-undo').click()
                expect(page.locator('#studio-board .w-health')).to_have_attribute('data-variant', 'standard')
                page.locator('#studio-redo').click()
                expect(page.locator('#studio-board .w-health')).to_have_attribute('data-variant', 'minimal')
                saved()
                assert target.read_bytes() == original, 'Editing must not write the target server'
                page.locator('#studio-title').fill('Health / Local draft')
                page.locator('#studio-title').press('Tab')
                saved()
                capture('03-unpublished-draft')
                page.locator('#studio-profile-tab').click()
                capture('04-profile-inspector')
                page.select_option('#studio-theme', 'competitive-red')
                saved()
                expect(page.locator('html')).to_have_attribute('data-theme', 'competitive-red')
                capture('05-red')
                page.select_option('#studio-theme', 'tactical-blue')
                page.locator('#studio-widget-tab').click()

                # The occupied destination is rejected without moving any neighbour.
                before = page.evaluate('CCSStudioTarget.snapshot().draft.configuration.layout')
                page.locator('#studio-x').fill('0')
                page.locator('#studio-x').press('Tab')
                expect(page.locator('#studio-alert')).to_contain_text('occupées')
                assert page.evaluate('CCSStudioTarget.snapshot().draft.configuration.layout') == before
                expect(page.locator('#studio-x')).to_have_value('12')
                page.locator('#studio-alert').evaluate('node=>node.hidden=true')
                capture('06-grid-and-selection')

                # A pointer gesture previews only a ghost and commits one history operation.
                handle = page.locator('.w-round [data-studio-gesture="move"]')
                box = handle.bounding_box()
                historyBefore = page.evaluate('CCSStudioTarget.snapshot().state.history')
                page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
                page.mouse.down()
                page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2 + 80, steps=8)
                expect(page.locator('.studio-placement-ghost')).to_have_attribute('data-valid', 'true')
                expect(page.locator('#studio-y')).to_have_value('6')
                capture('06a-drag-guides')
                page.mouse.up()
                saved()
                assert page.evaluate('CCSStudioTarget.snapshot().draft.configuration.layout.widgets.find(w=>w.kind==="round").y') == 8
                assert page.evaluate('CCSStudioTarget.snapshot().state.history.entries') == historyBefore['entries'] + 1
                page.locator('#studio-undo').click()
                assert page.evaluate('CCSStudioTarget.snapshot().draft.configuration.layout.widgets.find(w=>w.kind==="round").y') == 6
                saved()
                resize = page.locator('.w-round [data-studio-gesture="resize"]')
                box = resize.bounding_box()
                page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
                page.mouse.down()
                page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2 + 40, steps=5)
                capture('06b-resize-guides')
                page.mouse.up()
                saved()
                assert page.evaluate('CCSStudioTarget.snapshot().draft.configuration.layout.widgets.find(w=>w.kind==="round").height') == 7
                page.locator('#studio-undo').click()
                saved()
                # Escape restores the gesture baseline, without a server save.
                box = handle.bounding_box()
                page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
                page.mouse.down()
                page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2 + 80)
                page.keyboard.press('Escape')
                page.mouse.up()
                expect(page.locator('.studio-placement-ghost')).to_have_count(0)
                assert page.evaluate('CCSStudioTarget.snapshot().draft.configuration.layout.widgets.find(w=>w.kind==="round").y') == 6
                assert target.read_bytes() == original
                before = page.evaluate('CCSStudioTarget.snapshot().draft.configuration.layout')

                # Responsive projection never changes the saved desktop rectangle.
                for width, height, name in [(1024, 768, '07-tablet'), (390, 844, '08-phone'), (320, 740, '09-small-phone')]:
                    page.set_viewport_size({'width': width, 'height': height})
                    page.locator('button[data-panel="canvas"]').click()
                    settle(page)
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), width
                    capture(name)
                    assert page.evaluate('CCSStudioTarget.snapshot().draft.configuration.layout') == before
                page.set_viewport_size({'width': 390, 'height': 844})
                page.locator('button[data-panel="inspector"]').click()
                capture('10-phone-inspector')
                page.locator('button[data-panel="library"]').click()
                capture('11-phone-library')
                page.locator('button[data-panel="canvas"]').click()
                page.set_viewport_size({'width': 1920, 'height': 1080})
                saved()

                # Reload requires an explicit resume choice and preserves the draft.
                enter()
                expect(page.locator('#studio-dialog')).to_be_visible()
                page.locator('#studio-dialog button[value="resume"]').click()
                expect(page.locator('#studio-board .w-health .widget-heading')).to_have_text('Health / Local draft')
                page.evaluate('state => CCSStudioTarget.previewData(state, true)', LIVE)
                saved()
                (runtime / 'hold-studio-ack').touch()
                page.locator('#studio-publish').click()
                page.wait_for_function("() => CCSStudioTarget.snapshot().publication?.code === 'publishing'")
                capture('12a-publication-in-progress')
                (runtime / 'hold-studio-ack').unlink()
                page.wait_for_function("() => CCSStudioTarget.snapshot().publication?.code === 'published'")
                assert json.loads(target.read_bytes())['profiles'][0]['revision'] == 2
                capture('12-published')

                # A second device publishes while the Studio holds its own local edit.
                enter()
                expect(page.locator('#studio-board > .widget')).to_have_count(8)
                page.locator('#studio-board .w-health').click()
                page.locator('#studio-title').fill('Retained local work')
                page.locator('#studio-title').press('Tab')
                saved()
                other = browser.new_context()
                remote = prepare(other, url)
                edit(remote, 'p-competitive', 'Competitive remote')
                remote.evaluate('publicationHarness.begin()')
                wait_state(remote, 'published')
                page.locator('#studio-publish').click()
                page.wait_for_function("() => CCSStudioTarget.snapshot().publication?.code === 'revision_conflict'")
                expect(page.locator('#studio-conflict')).to_be_visible()
                page.evaluate('state => CCSStudioTarget.previewData(state, true)', LIVE)
                capture('13-conflict')
                assert page.evaluate('CCSStudioTarget.snapshot().draft.configuration.layout.widgets.find(w=>w.kind==="health").title') == 'Retained local work'
                # Explicit local replacement uses the reviewed remote revision.
                page.locator('#studio-conflict-local').click()
                expect(page.locator('#studio-dialog pre')).to_contain_text('Competitive remote')
                page.locator('#studio-dialog button[value="confirm"]').click()
                page.wait_for_function("() => CCSStudioTarget.snapshot().publication?.code === 'published'")
                page.wait_for_function("() => ['saved','pristine'].includes(CCSStudioTarget.snapshot().state?.status)")
                assert json.loads(target.read_bytes())['profiles'][0]['configuration']['layout']['widgets'][1]['title'] == 'Retained local work'
                page.locator('#studio-board .w-health').click()
                page.locator('#studio-title').fill('Discard this local version')
                page.locator('#studio-title').press('Tab')
                saved()
                edit(remote, 'p-competitive', 'Server choice retained')
                remote.evaluate('publicationHarness.begin()')
                wait_state(remote, 'published')
                page.locator('#studio-publish').click()
                page.wait_for_function("() => CCSStudioTarget.snapshot().publication?.code === 'revision_conflict'")
                page.locator('#studio-conflict-server').click()
                page.locator('#studio-dialog button[value="confirm"]').click()
                page.wait_for_function("() => CCSStudioTarget.snapshot().draft?.name === 'Server choice retained'")
                assert page.evaluate('CCSStudioTarget.snapshot().draft.configuration.layout.widgets.find(w=>w.kind==="health").title') == 'Retained local work'
                assert not faults, faults
                if output:
                    (output / 'validation.json').write_text(json.dumps({'browser': browser.version,
                        'scope': 'first visual milestone, not final P8 validation', 'errors': faults,
                        'serverUnchangedDuringEditing': True, 'publishedRevision': 2,
                        'conflictPreservesDraft': True}, indent=2), encoding='utf8')
                browser.close()
                print('OK: first Studio journey, native local drafts, retained DOM, undo/redo, responsive, explicit publication and real conflict')
        finally:
            stop(process)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--browser', choices=['chromium', 'firefox', 'webkit'], default='chromium')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    run(args.browser, args.output)
