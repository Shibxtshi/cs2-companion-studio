"""Ten complete palettes on the production composition, using synthetic profiles only."""
import argparse
import copy
import json
import os
from pathlib import Path
import time

from playwright.sync_api import expect, sync_playwright
from test_production_studio import production, login
from companion.profile_activation import target_document
from companion.profile_contracts import THEMES, THEME_NAMES
from widget_fixtures import settle

SIZES = [(1920, 1080), (1366, 768), (1280, 900), (1024, 768), (768, 1024), (390, 844), (320, 740)]


def fixture():
    document = target_document()
    first = document['profiles'][0]
    first['name'] = 'Synthetic Match Center'
    kinds = ['score', 'health', 'weapon', 'economy', 'armor', 'connection', 'inventory', 'stats', 'round_history']
    first['configuration']['layout']['widgets'] = [
        {'id': 'theme-' + kind, 'kind': kind, 'x': index % 3 * 8, 'y': index // 3 * 9,
         'width': 8, 'height': 9, 'title': '', 'variant': ['standard', 'compact', 'minimal'][index % 3],
         'color': '', 'background': '', 'opacity': [100, 85, 60][index % 3],
         'style': ['solid', 'glass', 'outline'][index % 3]} for index, kind in enumerate(kinds)]
    second = copy.deepcopy(first)
    second.update(id='p-second', name='Synthetic Second Screen')
    second['configuration']['theme'] = 'arctic-white'
    document['profiles'].append(second)
    return document


def contrast(first, second):
    def luminance(color):
        channels = [value / 255 for value in color[:3]]
        linear = [value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4 for value in channels]
        return sum(value * factor for value, factor in zip(linear, (.2126, .7152, .0722)))
    low, high = sorted((luminance(first), luminance(second)))
    return (high + .05) / (low + .05)


def check_palette(page, studio=False):
    host = '#studio-board' if studio else '#board'
    selectors = {
        'body': ['body', 'color'],
        'widgetText': [host + ' .widget', 'color'],
        'widgetTitle': [host + ' .widget-heading', 'color'],
        'widgetWarning': [host + ' .widget-data-status', 'color'],
        'primary': ['#studio-publish' if studio else '#help-done', 'color'],
        'fieldText': ['#studio-profile-name' if studio else '#dashboard-profile-menu', 'color'],
        'fieldBorder': ['#studio-profile-name' if studio else '#dashboard-profile-menu', 'borderTopColor'],
        'placeholder': ['#studio-search' if studio else '#pin', 'placeholder'],
        'secondary': ['.studio-hint' if studio else '.dashboard-heading .tiny', 'color'],
        'navigation': ['.nav-item[aria-current="page"]', 'color'],
        'focus': ['#studio-theme' if studio else '.nav-brand', 'outlineColor'],
    }
    if not studio:
        del selectors['placeholder']
    samples = page.evaluate("""selectors => {
      const canvas = document.createElement('canvas'); canvas.width = canvas.height = 1;
      const context = canvas.getContext('2d');
      const rgba = value => {context.clearRect(0,0,1,1);context.fillStyle=value;context.fillRect(0,0,1,1);return [...context.getImageData(0,0,1,1).data];};
      const over = (front, back) => {const a=front[3]/255;return [0,1,2].map(i=>front[i]*a+back[i]*(1-a)).concat(255);};
      const background = node => node ? over(rgba(getComputedStyle(node).backgroundColor), background(node.parentElement)) : [255,255,255,255];
      const result = {};
      for (const [name,[selector,property]] of Object.entries(selectors)) {
        const node=document.querySelector(selector); if (!node) continue;
        const style=getComputedStyle(node);const bg=background(node);
        const fg=rgba(property==='placeholder'?getComputedStyle(node,'::placeholder').color:style[property]);
        fg[3]*=Number(style.opacity);
        result[name]=[over(fg,bg),bg];
      }
      return result;
    }""", selectors)
    result = {}
    for name, colors in samples.items():
        ratio = contrast(*colors)
        result[name] = round(ratio, 2)
        minimum = 3 if name in ('fieldBorder', 'focus') else 4.5
        assert ratio >= minimum, (page.locator('html').get_attribute('data-theme'), studio, name, colors, ratio)
    return result


def check_notifications(page, output, theme):
    samples = {}
    for kind in ('info', 'success', 'warning', 'error', 'loading', 'pending'):
        page.evaluate("kind => {CCSNotifications.dismiss(); CCSNotifications.show({message:'Synthetic theme review',kind});}", kind)
        token = {'error': '--error', 'warning': '--warning'}.get(kind, '--ccs-text')
        expected = page.evaluate('token => getComputedStyle(document.documentElement).getPropertyValue(token).trim()', token).lstrip('#')
        expectedRgb = 'rgb(' + ', '.join(str(int(expected[index:index + 2], 16)) for index in (0, 2, 4)) + ')'
        expect(page.locator('#toast')).to_have_css('color', expectedRgb)
        settle(page)
        colors = page.locator('#toast').evaluate(r"""node => {
            const style = getComputedStyle(node);
            const rgb = color => color.match(/[\d.]+/g).slice(0,3).map(Number);
            return {text:rgb(style.color), background:rgb(style.backgroundColor), border:rgb(style.borderTopColor)};
        }""")
        ratio = contrast(colors['text'], colors['background'])
        assert ratio >= 4.5, (theme, kind, colors, ratio)
        samples[kind] = round(ratio, 2)
        if output and theme == 'arctic-white':
            page.locator('#toast').screenshot(path=str(output / ('arctic-white-status-' + kind + '.png')))
    page.evaluate('() => CCSNotifications.dismiss()')
    return samples


def send_game(context, url):
    response = context.request.post(url + '/gsi', data={
        'auth': {'token': 'synthetic-production-gsi'}, 'provider': {'timestamp': time.time()},
        'map': {'name': 'de_mirage', 'mode': 'competitive', 'phase': 'live', 'round': 14,
                'team_ct': {'score': 8}, 'team_t': {'score': 5}},
        'round': {'phase': 'live'},
        'player': {'name': 'Synthetic player', 'team': 'CT', 'activity': 'playing',
                   'state': {'health': 87, 'armor': 94, 'helmet': True, 'money': 3200, 'equip_value': 4300},
                   'match_stats': {'kills': 18, 'assists': 4, 'deaths': 11, 'mvps': 3, 'score': 42},
                   'weapons': {'weapon_0': {'name': 'weapon_ak47', 'type': 'Rifle', 'state': 'active',
                                            'ammo_clip': 21, 'ammo_clip_max': 30, 'ammo_reserve': 90}}},
    })
    assert response.ok


def run(browserName, output, themes=THEMES):
    results, errors = [], []
    if output:
        output.mkdir(parents=True, exist_ok=True)
    with production(fixture()) as (url, data, initial, restart):
        with sync_playwright() as playwright:
            options = {'headless': True}
            executable = os.environ.get('CCS_CHROMIUM_EXECUTABLE') or os.environ.get('CS2_CHROMIUM_BIN')
            if browserName == 'chromium' and executable:
                options['executable_path'] = executable
            browser = getattr(playwright, browserName).launch(**options)
            context = browser.new_context(viewport={'width': 1920, 'height': 1080}, reduced_motion='reduce')
            page, other = context.new_page(), context.new_page()
            commands = []
            def proxy(socket):
                server = socket.connect_to_server()
                server.on_message(socket.send)
                def forward(raw):
                    commands.append(json.loads(raw).get('type'))
                    server.send(raw)
                socket.on_message(forward)
            page.route_web_socket('**/ws', proxy)
            for tab in (page, other):
                tab.on('pageerror', lambda error: errors.append(str(error)))
            login(page, url)
            login(other, url)
            other.select_option('#dashboard-profile-menu', 'p-second')
            page.bring_to_front()
            expect(other.locator('html')).to_have_attribute('data-theme', 'arctic-white')
            assert page.locator('#studio-theme option').count() == len(THEMES)
            assert page.locator('#theme-preview option').count() == len(THEMES)
            page.evaluate('() => document.fonts.ready')
            assert page.evaluate("() => document.fonts.check('400 14px Inter')")
            for theme in themes:
                print('Checking theme: ' + theme, flush=True)
                page.set_viewport_size({'width': 1920, 'height': 1080})
                page.locator('[data-section="studio"]').click()
                page.locator('#studio-profile-tab').click()
                original = (data / 'profiles.json').read_bytes()
                publications = commands.count('profile_operation')
                previous = page.locator('#studio-theme').input_value()
                page.select_option('#studio-theme', theme)
                if previous != theme:
                    page.locator('#studio-undo').click()
                    expect(page.locator('html')).to_have_attribute('data-theme', previous)
                    page.locator('#studio-redo').click()
                    expect(page.locator('html')).to_have_attribute('data-theme', theme)
                page.locator('#studio-profile-name').fill('Synthetic ' + THEME_NAMES[theme])
                page.locator('#studio-profile-name').press('Tab')
                expect(page.locator('#studio-save-state')).to_contain_text('Draft kept locally')
                assert (data / 'profiles.json').read_bytes() == original
                assert commands.count('profile_operation') == publications
                page.select_option('#locale-select', 'FR')
                expect(page.locator('#studio-theme')).to_have_value(theme)
                assert page.locator('#studio-theme option:checked').inner_text() == THEME_NAMES[theme]
                page.select_option('#locale-select', 'EN')
                page.locator('#studio-theme').focus()
                settle(page)
                entry = {'theme': theme, 'name': THEME_NAMES[theme], 'studioContrast': check_palette(page, True)}
                primary = page.locator('#studio-publish')
                primary.hover()
                entry['studioHoverContrast'] = check_palette(page, True)['primary']
                page.mouse.down()
                entry['studioPressedContrast'] = check_palette(page, True)['primary']
                page.mouse.move(0, 0)
                page.mouse.up()
                assert (data / 'profiles.json').read_bytes() == original
                expectedScheme = 'light' if theme == 'arctic-white' else 'dark'
                assert page.evaluate('() => getComputedStyle(document.documentElement).colorScheme') == expectedScheme
                entry['disabledControl'] = page.locator('#studio-redo').evaluate('node=>({disabled:node.disabled,opacity:getComputedStyle(node).opacity,color:getComputedStyle(node).color})')
                if theme == 'arctic-white':
                    for width, height in SIZES:
                        page.set_viewport_size({'width': width, 'height': height})
                        if width <= 1100:
                            page.locator('button[data-panel="inspector"]').click()
                        expect(page.locator('#studio-theme')).to_be_visible()
                        settle(page)
                        assert page.evaluate('() => document.documentElement.scrollWidth <= innerWidth'), ('Studio', theme, width)
                        if output and width in (768, 320):
                            page.screenshot(path=str(output / ('arctic-white-studio-' + str(width) + '.png')))
                    page.set_viewport_size({'width': 1920, 'height': 1080})
                assert page.locator('meta[name="theme-color"]').get_attribute('content').lower() == page.evaluate("() => getComputedStyle(document.documentElement).getPropertyValue('--ccs-bg').trim().toLowerCase()")
                if output:
                    page.evaluate('() => window.scrollTo(0,0)')
                    page.screenshot(path=str(output / (theme + '-studio-desktop.png')))
                    if theme == 'arctic-white':
                        page.locator('#studio-board .w-health').click(position={'x':15,'y':15})
                        page.locator('#studio-widget-tab').click()
                        page.screenshot(path=str(output / 'arctic-white-inspector.png'))
                        page.locator('.studio-profile-actions summary').click()
                        page.screenshot(path=str(output / 'arctic-white-menu.png'))
                        page.keyboard.press('Escape')
                        page.locator('#studio-help').click()
                        expect(page.locator('#studio-dialog')).to_be_visible()
                        dialog = page.locator('#studio-dialog').bounding_box()
                        assert dialog['width'] <= 520 and dialog['x'] > 0 and dialog['y'] > 0
                        expect(page.locator('#studio-dialog')).to_have_css('background-color','rgb(226, 233, 242)')
                        page.screenshot(path=str(output / 'arctic-white-dialog.png'))
                        page.locator('#studio-dialog button[value="cancel"]').click()
                        page.locator('#studio-profile-tab').click()
                with page.expect_popup() as popup:
                    page.locator('#studio-open-preview').click()
                preview = popup.value
                expect(preview.locator('html')).to_have_attribute('data-theme', theme)
                expect(preview.locator('#board .widget')).to_have_count(9)
                assert preview.evaluate('() => getComputedStyle(document.documentElement).colorScheme') == expectedScheme
                preview.close()
                page.bring_to_front()
                page.locator('#studio-publish').click()
                expect(page.locator('#studio-save-state')).to_contain_text('Published version up to date')
                assert commands.count('profile_operation') == publications + 1
                page.locator('#studio-leave').click()
                expect(page.locator('html')).to_have_attribute('data-theme', theme)
                send_game(context, url)
                for team in ('ct', 't'):
                    token = page.evaluate('name=>getComputedStyle(document.documentElement).getPropertyValue(name).trim()', '--team-' + team).lstrip('#')
                    rgb = 'rgb(' + ', '.join(str(int(token[index:index + 2], 16)) for index in (0, 2, 4)) + ')'
                    expect(page.locator('#board .team-' + team).first).to_have_css('color', rgb)
                page.locator('.nav-brand').focus()
                settle(page)
                entry['dashboardContrast'] = check_palette(page)
                entry['notifications'] = check_notifications(page, output, theme)
                if output:
                    page.screenshot(path=str(output / (theme + '-dashboard-desktop.png')))
                for width, height in SIZES:
                    page.set_viewport_size({'width': width, 'height': height})
                    settle(page)
                    assert page.evaluate('() => document.documentElement.scrollWidth <= innerWidth'), (theme, width)
                    if output and width == 390:
                        page.screenshot(path=str(output / (theme + '-dashboard-mobile.png')))
                page.set_viewport_size({'width': 390, 'height': 844})
                page.locator('[data-section="studio"]').click()
                page.locator('button[data-panel="inspector"]').click()
                page.locator('#studio-profile-tab').click()
                expect(page.locator('#studio-theme')).to_be_visible()
                if output:
                    page.screenshot(path=str(output / (theme + '-studio-mobile.png')))
                page.set_viewport_size({'width': 1920, 'height': 1080})
                page.locator('#studio-leave').click()
                login(page, url)
                expect(page.locator('html')).to_have_attribute('data-theme', theme)
                assert other.locator('#dashboard-profile-menu').input_value() == 'p-second'
                expect(other.locator('html')).to_have_attribute('data-theme', 'arctic-white')
                current = json.loads((data / 'profiles.json').read_bytes())
                assert current['profiles'][0]['configuration']['theme'] == theme
                assert current['profiles'][1] == initial['profiles'][1]
                assert current['profiles'][0]['configuration']['layout'] == initial['profiles'][0]['configuration']['layout']
                results.append(entry)
            page.select_option('#dashboard-profile-menu', 'p-second')
            expect(page.locator('html')).to_have_attribute('data-theme', 'arctic-white')
            settle(page)
            page.wait_for_timeout(250)
            expect(page.locator('html')).to_have_attribute('data-theme', 'arctic-white')
            page.select_option('#dashboard-profile-menu', initial['profiles'][0]['id'])
            expect(page.locator('html')).to_have_attribute('data-theme', themes[-1])
            settle(page)
            page.wait_for_timeout(250)
            expect(page.locator('html')).to_have_attribute('data-theme', themes[-1])
            authentications = commands.count('auth')
            restart()
            for _ in range(100):
                if commands.count('auth') > authentications:
                    break
                page.wait_for_timeout(100)
            assert commands.count('auth') > authentications, 'The active tab must reconnect to the restarted server'
            expect(page.locator('html')).to_have_attribute('data-theme', themes[-1])
            assert not errors, errors
            if output:
                (output / 'palette-results.json').write_text(json.dumps({'browser': browser.version, 'palettes': results,
                    'widths': SIZES, 'errors': errors}, indent=2), encoding='utf8')
            browser.close()
    print('PASS: ' + str(len(themes)) + ' published themes, draft/history/preview, profile isolation, reload, color-scheme and measured contrasts')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser', choices=['chromium', 'firefox', 'webkit'], default='chromium')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--themes', nargs='+', choices=THEMES, default=THEMES)
    args = parser.parse_args()
    run(args.browser, args.output, args.themes)
