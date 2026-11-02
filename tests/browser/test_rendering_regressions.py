"""Targeted R1 rendering regressions on the real production composition, synthetic data only."""
import argparse
import copy
import json
import os
from pathlib import Path

from playwright.sync_api import expect, sync_playwright
from test_production_studio import production, login
from companion.profile_activation import target_document

THEMES = ['tactical-blue', 'competitive-red', 'performance-green', 'creator-purple']


def fixture():
    document = target_document()
    widgets = document['profiles'][0]['configuration']['layout']['widgets']
    for style in ['solid', 'glass', 'outline']:
        for background, opacity in [('', 100), ('#ff0000', 60), ('#ff0000', 100)]:
            index = len(widgets)
            widgets.append({'id': 'r11-' + str(index), 'kind': 'health', 'x': index % 3 * 8,
                            'y': index // 3 * 8, 'width': 8, 'height': 8, 'title': '',
                            'variant': 'standard', 'color': '#00ff00' if background else '', 'background': background,
                            'opacity': opacity, 'style': style})
    return document


def assert_surfaces(page, selector):
    # Wait for existing border transitions before comparing final rendered RGBA.
    page.locator(selector).evaluate_all(
        "cards => Promise.all(cards.flatMap(card => card.getAnimations()).map(animation => animation.finished.catch(() => {})))")
    # Compare rendered RGBA, not only custom properties or data attributes.
    result = page.locator(selector).evaluate_all('''cards => cards.map(card => {
      function rgba(color) {
        const canvas = document.createElement('canvas'); canvas.width = canvas.height = 1;
        const context = canvas.getContext('2d'); context.fillStyle = color;
        context.fillRect(0, 0, 1, 1); return [...context.getImageData(0, 0, 1, 1).data];
      }
      const style = getComputedStyle(card);
      const probe = document.createElement('div'); probe.style.background = 'var(--card)';
      card.append(probe); const automatic = rgba(getComputedStyle(probe).backgroundColor); probe.remove();
      return {id:card.dataset.id, style:card.dataset.style, actual:rgba(style.backgroundColor), automatic,
        opacity:parseFloat(card.style.getPropertyValue('--widget-opacity')),
        custom:card.style.getPropertyValue('--widget-bg'), blur:style.backdropFilter,
        border:rgba(style.borderTopColor)};
    })''')
    assert len(result) == 9, result
    for item in result:
        factor = {'solid': 1, 'glass': .67, 'outline': .15}[item['style']]
        expected = [255, 0, 0, 255] if item['custom'] else item['automatic']
        expected = expected[:3] + [round(expected[3] * factor * item['opacity'] / 100)]
        assert all(abs(actual - wanted) <= 3 for actual, wanted in zip(item['actual'], expected)), item
        if item['style'] == 'outline' and item['custom']:
            assert item['border'] == [0, 255, 0, 255], item
        if item['style'] == 'glass':
            assert 'blur(10px)' in item['blur'], item


def proxy_commands(page, commands):
    def proxy(socket):
        server = socket.connect_to_server()
        server.on_message(socket.send)
        def forward(raw):
            commands.append(json.loads(raw)['type'])
            server.send(raw)
        socket.on_message(forward)
    page.route_web_socket('**/ws', proxy)


def surfaces(browser, output):
    with production(fixture()) as (url, data, initial, _restart):
        page = browser.new_page(viewport={'width':1920, 'height':1080})
        commands = []
        proxy_commands(page, commands)
        login(page, url)
        assert_surfaces(page, '#board>.widget')
        page.locator('[data-section="studio"]').click()
        page.locator('#studio-board>.widget').first.click(position={'x':15, 'y':15})
        page.locator('#studio-background').fill('#ff0000')
        page.locator('#studio-background').press('Tab')
        page.locator('#studio-opacity').focus()
        page.locator('#studio-opacity').press('Home')
        assert_surfaces(page, '#studio-board>.widget')
        page.locator('#studio-opacity').press('End')
        page.locator('#studio-background').fill('')
        page.locator('#studio-background').press('Tab')
        assert_surfaces(page, '#studio-board>.widget')
        page.locator('#studio-profile-tab').click()
        for theme in THEMES:
            page.select_option('#studio-theme', theme)
            page.locator('#studio-profile-name').fill('Surface test ' + theme)
            page.locator('#studio-profile-name').press('Tab')
            expect(page.locator('html')).to_have_attribute('data-theme', theme)
            assert_surfaces(page, '#studio-board>.widget')
            with page.expect_popup() as popup:
                page.locator('#studio-open-preview').click()
            preview = popup.value
            expect(preview.locator('#board>.widget')).to_have_count(9)
            assert_surfaces(preview, '#board>.widget')
            preview.close()
            page.locator('#studio-publish').click()
            expect(page.locator('#studio-save-state')).to_contain_text('Published version up to date')
            page.locator('#studio-leave').click()
            assert_surfaces(page, '#board>.widget')
            login(page, url)
            expect(page.locator('html')).to_have_attribute('data-theme', theme)
            assert_surfaces(page, '#board>.widget')
            if output:
                page.screenshot(path=str(output / ('surfaces-' + theme + '.png')))
            page.locator('[data-section="studio"]').click()
            page.locator('#studio-profile-tab').click()
        assert 'profiles_save' not in commands
        current = json.loads((data / 'profiles.json').read_bytes())
        assert current['profiles'][0]['configuration']['layout']['widgets'] == initial['profiles'][0]['configuration']['layout']['widgets']
        page.close()


def imported_kind(browser, output):
    with production() as (url, data, _initial, _restart):
        page = browser.new_page(viewport={'width':1920, 'height':1080})
        commands = []
        proxy_commands(page, commands)
        login(page, url)
        original = (data / 'profiles.json').read_bytes()
        page.locator('[data-section="studio"]').click()
        for kind in ['health', 'armor']:
            page.locator('.studio-library-item[data-kind="' + kind + '"] button').click()
        cards = page.locator('#studio-board>.widget')
        cards.nth(0).click(position={'x':15, 'y':15})
        page.evaluate('''() => {window.originalCards = [...document.querySelectorAll('#studio-board>.widget')];}''')
        expect(page.locator('#studio-save-state')).to_contain_text('Draft kept locally')
        draft = page.evaluate('''() => new Promise((resolve, reject) => {
          const request = indexedDB.open('ccs-local-drafts');
          request.onerror = () => reject(request.error);
          request.onsuccess = () => {const db = request.result;
            const transaction = db.transaction('drafts', 'readonly');
            const read = transaction.objectStore('drafts').getAll();
            read.onsuccess = () => resolve(read.result[0].draft);
            transaction.oncomplete = () => db.close();};
        })''')
        document = {'format':'ccs-dashboard-export', 'version':1, 'name':draft['name'],
                    'configuration':copy.deepcopy(draft['configuration'])}
        document['configuration']['layout']['widgets'][0].update(kind='weapon', variant='compact')
        page.locator('#production-import-file').set_input_files({'name':'synthetic-kind.json',
            'mimeType':'application/json', 'buffer':json.dumps(document).encode()})
        page.locator('#studio-dialog button[value="replace"]').click()
        expect(cards.nth(0)).to_have_attribute('data-kind', 'weapon')
        expect(cards.nth(0)).to_have_attribute('data-variant', 'compact')
        cards.nth(0).click(position={'x':15, 'y':15})
        expect(page.locator('#studio-selection-label')).to_contain_text('weapon')
        minimum = page.evaluate("() => CCSDashboardLayout.minimum('weapon', 'compact')")
        expect(page.locator('#studio-minimum')).to_contain_text(str(minimum[0]) + ' × ' + str(minimum[1]))
        assert page.evaluate('''() => originalCards[1] === document.querySelectorAll('#studio-board>.widget')[1]''')
        assert page.evaluate('''() => !originalCards[0].isConnected''')
        page.locator('#studio-undo').click()
        expect(cards.nth(0)).to_have_attribute('data-kind', 'health')
        page.locator('#studio-redo').click()
        expect(cards.nth(0)).to_have_attribute('data-kind', 'weapon')
        expect(page.locator('#studio-save-state')).to_contain_text('Draft kept locally')
        assert (data / 'profiles.json').read_bytes() == original
        assert 'profile_operation' not in commands and 'profiles_save' not in commands
        page.locator('#studio-leave').click()
        login(page, url)
        page.locator('[data-section="studio"]').click()
        page.locator('#studio-dialog button[value="resume"]').click()
        expect(cards.nth(0)).to_have_attribute('data-kind', 'weapon')
        assert (data / 'profiles.json').read_bytes() == original
        if output:
            page.screenshot(path=str(output / 'import-kind-reconciled.png'))
        page.locator('#studio-publish').click()
        expect(page.locator('#studio-save-state')).to_contain_text('Published version up to date')
        published = json.loads((data / 'profiles.json').read_bytes())['profiles'][0]['configuration']['layout']['widgets']
        assert published[0]['kind'] == 'weapon' and published[0]['id'] == draft['configuration']['layout']['widgets'][0]['id']
        assert commands.count('profile_operation') == 1
        page.close()


def legacy_surfaces(browser, output):
    document = fixture()
    widgets = document['profiles'][0]['configuration']['layout']['widgets']
    historical = {'activeProfile':'legacy', 'profiles':[{'id':'legacy', 'name':'Synthetic legacy',
        'widgets':[{key:widget[key] for key in ['id', 'kind', 'title', 'color', 'background', 'opacity', 'style']}
                   | {'span':4} for widget in widgets]}]}
    with production(historical) as (url, data, _initial, _restart):
        from test_production_studio import PIN
        page = browser.new_page()
        page.goto(url)
        page.locator('#pin').fill(PIN)
        page.locator('#connect').click()
        page.locator('#tab-custom').click()
        original = (data / 'profiles.json').read_bytes()
        assert_surfaces(page, '#board>.widget')
        page.locator('[data-section="settings"]').click()
        for theme in THEMES:
            page.select_option('#theme-preview', theme)
            assert_surfaces(page, '#board>.widget')
        assert (data / 'profiles.json').read_bytes() == original
        page.close()


def canvas_focus(browser, output):
    with production(fixture()) as (url, _data, initial, _restart):
        page = browser.new_page()
        login(page, url)
        content = {key:initial['profiles'][0][key] for key in ['name', 'configuration']}
        result = page.evaluate('''content => {
          const board = document.createElement('div'); board.className = 'studio-board';
          board.style.width = '1200px'; document.body.append(board);
          let selections = 0;
          const canvas = CCSStudioCanvas({board, select:() => selections++,
            gesture:{}, onGeometry:() => {}, report:() => {}});
          const first = content.configuration.layout.widgets[0];
          canvas.update(content, first.id);
          const before = [...board.querySelectorAll('.widget')];
          before[0].querySelector('[data-studio-gesture="move"]').focus();
          first.kind = 'weapon'; first.variant = 'compact';
          canvas.update(content, first.id);
          const after = [...board.querySelectorAll('.widget')];
          const result = {focused:document.activeElement === after[0].querySelector('[data-studio-gesture="move"]'),
            replaced:before[0] !== after[0], unchanged:before.slice(1).every((card, index) => card === after[index + 1]),
            kind:after[0].dataset.kind, variant:after[0].dataset.variant, selections};
          canvas.dispose(); board.remove(); return result;
        }''', content)
        assert result == {'focused':True, 'replaced':True, 'unchanged':True,
                          'kind':'weapon', 'variant':'compact', 'selections':2}, result
        page.close()


def demonstration(browser, output):
    initial = fixture()
    widget = initial['profiles'][0]['configuration']['layout']['widgets'][0]
    initial['profiles'][0]['configuration']['layout']['widgets'] = [{**widget, 'kind':'bomb'}]
    with production(initial) as (url, data, _initial, _restart):
        context = browser.new_context()
        page = context.new_page()
        commands = []
        proxy_commands(page, commands)
        original = (data / 'profiles.json').read_bytes()
        page.goto(url)
        page.locator('#demo').click()
        expect(page.locator('#status')).to_contain_text('Demonstration')
        page.locator('.bomb-demo-options summary').click()
        clock = page.locator('[data-bomb-clock]')
        for seconds in [40, 9, 4]:
            page.locator('[data-demo="' + str(seconds) + '"]').click()
            expect(clock).not_to_have_text('--.- s')
            start = float(clock.inner_text().split()[0])
            assert seconds - 2 < start <= seconds
            page.wait_for_timeout(300)
            assert float(clock.inner_text().split()[0]) < start
            if output:
                page.screenshot(path=str(output / ('demo-bomb-' + str(seconds) + '.png')))
        page.locator('[data-demo="stop"]').click()
        expect(clock).to_have_text('--.- s')
        page.wait_for_timeout(200)
        expect(clock).to_have_text('--.- s')
        assert commands == [] and (data / 'profiles.json').read_bytes() == original
        assert page.evaluate("() => indexedDB.databases().then(dbs => dbs.length)") == 0
        page.locator('#logout').click()
        expect(page.locator('#login')).to_be_visible()
        login(page, url)
        expect(page.locator('#board>.widget')).to_have_count(1)
        expect(page.locator('#board>.widget')).to_have_attribute('data-kind', 'bomb')
        expect(clock).to_have_text('--.- s')
        page.locator('[data-demo="9"]').dispatch_event('click')
        page.wait_for_timeout(200)
        expect(clock).to_have_text('--.- s')
        expect(page.locator('#status')).not_to_contain_text('Demonstration')
        assert commands == ['auth']
        assert (data / 'profiles.json').read_bytes() == original
        context.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser', choices=['chromium', 'firefox', 'webkit'], default='chromium')
    parser.add_argument('--case', choices=['all', 'surfaces', 'import', 'demo', 'legacy', 'focus'], default='all')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.output:
        args.output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        options = {}
        if args.browser == 'chromium' and os.environ.get('CCS_CHROMIUM_EXECUTABLE'):
            options['executable_path'] = os.environ['CCS_CHROMIUM_EXECUTABLE']
        browser = getattr(playwright, args.browser).launch(headless=True, **options)
        try:
            for name, check in [('surfaces', surfaces), ('import', imported_kind), ('demo', demonstration),
                                ('legacy', legacy_surfaces), ('focus', canvas_focus)]:
                if args.case in ['all', name]:
                    check(browser, args.output)
                    print('PASS: R1 rendering regression ' + name, flush=True)
        finally:
            browser.close()
