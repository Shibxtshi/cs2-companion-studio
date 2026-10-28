"""Exercise the four palettes without changing the existing profile contract."""
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright
from test_live_browser import start_server
from test_widget_characterization import open_fixture, SNAPSHOT, settle

THEMES = ('tactical-blue', 'competitive-red', 'performance-green', 'creator-purple')


def contrast(first, second):
    def luminance(color):
        channels = [float(value) / 255 for value in color.removeprefix('rgb(').removesuffix(')').split(',')]
        linear = [value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4
                  for value in channels]
        return sum(value * factor for value, factor in zip(linear, (.2126, .7152, .0722)))
    values = sorted((luminance(first), luminance(second)))
    return (values[1] + .05) / (values[0] + .05)


def check_palette(page):
    samples = page.evaluate("""() => {
        const canvas = document.createElement('canvas');
        canvas.width = canvas.height = 1;
        const context = canvas.getContext('2d');
        const read = (selector, property) => {
          context.fillStyle = getComputedStyle(document.body).backgroundColor;
          context.fillRect(0,0,1,1);
          context.fillStyle = getComputedStyle(document.querySelector(selector))[property];
          context.fillRect(0,0,1,1);
          const pixel = context.getImageData(0,0,1,1).data;
          return 'rgb(' + Array.from(pixel).slice(0,3).join(',') + ')';
        };
        return {
          text:[read('.widget','color'),read('.widget','backgroundColor')],
          secondary:[read('.widget-heading','color'),read('.widget','backgroundColor')],
          primary:[read('#help-done','color'),read('#help-done','backgroundColor')],
          field:[read('#pin','borderTopColor'),read('#pin','backgroundColor')],
          selected:[read('.tab.active','color'),read('.tab.active','backgroundColor')],
          focus:[read('#theme-preview','outlineColor'),read('body','backgroundColor')]
        };
    }""")
    for name, colors in samples.items():
        minimum = 3 if name in ('field', 'focus') else 4.5
        assert contrast(*colors) >= minimum, (name, colors, contrast(*colors))
    return {name: round(contrast(*colors), 2) for name, colors in samples.items()}


def run(browserName, output):
    runtime, process, url = start_server()
    results = []
    try:
        with sync_playwright() as playwright:
            options = {'headless': True}
            if browserName == 'chromium' and os.environ.get('CS2_CHROMIUM_BIN'):
                options.update(executable_path=os.environ['CS2_CHROMIUM_BIN'], args=['--no-sandbox'])
            browser = getattr(playwright, browserName).launch(**options)
            for width, height in ((1280, 900), (1024, 768), (390, 844), (320, 740)):
                context = browser.new_context(viewport={'width': width, 'height': height},
                                              locale='en-US', timezone_id='UTC', reduced_motion='reduce',
                                              has_touch=(width <= 390),
                                              is_mobile=(width <= 390 and browserName != 'firefox'))
                requests = []
                context.on('request', lambda request: requests.append(request.url))
                page, fixture, faults = open_fixture(context, url)
                page.evaluate('() => document.fonts.ready')
                assert page.evaluate("document.fonts.check('400 14px Inter') && document.fonts.check('700 34px \"Barlow Condensed\"')")
                initial = page.evaluate(SNAPSHOT)
                document = copy.deepcopy(fixture.document)
                revision = fixture.revision
                storage = page.evaluate('JSON.stringify([Object.entries(localStorage),Object.entries(sessionStorage)])')
                for theme in THEMES:
                    page.locator('#theme-preview').select_option(theme)
                    expect(page.locator('html')).to_have_attribute('data-theme', theme)
                    page.locator('#theme-preview').focus()
                    page.keyboard.press('Tab')
                    page.keyboard.press('Shift+Tab')
                    expect(page.locator('#theme-preview')).to_be_focused()
                    if page.evaluate("matchMedia('(pointer:coarse)').matches"):
                        targets = page.locator('.btn,.tab,.edit-controls button,#theme-preview')
                        for target in targets.all():
                            if target.is_visible():
                                assert target.bounding_box()['height'] >= 44
                    ratios = check_palette(page)
                    assert page.evaluate(SNAPSHOT) == initial, (width, theme)
                    assert fixture.document == document
                    assert fixture.revision == revision, 'Theme preview must not autosave profiles'
                    assert page.locator('.w-economy .accent').evaluate(
                        "node => getComputedStyle(node).color") == 'rgb(243, 172, 82)'
                    assert page.locator('#board .widget').first.evaluate(
                        "node => getComputedStyle(node,'::before').backgroundColor") == 'rgb(118, 187, 253)'
                    assert page.evaluate('JSON.stringify([Object.entries(localStorage),Object.entries(sessionStorage)])') == storage
                    dimensions = page.evaluate('({width:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth})')
                    assert dimensions['scroll'] <= dimensions['width'], (width, theme, dimensions)
                    for locale in ('FR', 'EN'):
                        page.locator('#locale-select').select_option(locale)
                        expectedLabel = 'Thème d’aperçu' if locale == 'FR' else 'Theme preview'
                        expect(page.locator('label[for="theme-preview"]')).to_have_text(expectedLabel)
                        expect(page.locator('#theme-preview')).to_have_attribute('aria-label', expectedLabel)
                        if width <= 390:
                            assert page.locator('#locale-select').evaluate("""node => {
                                const context = document.createElement('canvas').getContext('2d');
                                const style = getComputedStyle(node);
                                context.font = style.fontWeight + ' ' + style.fontSize + ' ' + style.fontFamily;
                                return context.measureText(node.selectedOptions[0].text).width + 40 <= node.clientWidth;
                            }""")
                        if output and width in (1280, 390):
                            page.locator('#main-content').screenshot(path=str(output / f'{theme}-{width}-{locale}.png'))
                    results.append({'theme': theme, 'width': width, 'contrast': ratios})
                # Inspect the existing editor and catalog at narrow widths as well.
                page.locator('#edit').click()
                page.locator('#add').click()
                expect(page.locator('#catalog')).to_be_visible()
                page.locator('#search-widgets').fill('map')
                assert page.locator('#catalog-items .catalog-item').count() > 0
                page.locator('#board .widget').first.locator('.edit-controls button').nth(3).click()
                dimensions = page.evaluate('({width:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth})')
                assert dimensions['scroll'] <= dimensions['width'], ('editor', width, dimensions)
                if output and width in (1280, 390):
                    page.locator('#main-content').screenshot(path=str(output / f'creator-purple-{width}-editor.png'))
                page.locator('#close-catalog').click()
                page.locator('#edit').click()
                # The preview remains independent across tabs and resets after reload.
                page.locator('#theme-preview').select_option('creator-purple')
                other = context.new_page()
                other.goto(url)
                expect(other.locator('html')).to_have_attribute('data-theme', 'tactical-blue')
                expect(page.locator('html')).to_have_attribute('data-theme', 'creator-purple')
                other.close()
                page.reload()
                expect(page.locator('html')).to_have_attribute('data-theme', 'tactical-blue')
                # Capture real login and the existing themed help dialog without a PIN.
                if output and width in (1280, 390):
                    for theme in THEMES:
                        page.locator('#theme-preview').select_option(theme)
                        page.locator('#main-content').screenshot(path=str(output / f'{theme}-{width}-login.png'))
                        page.locator('#open-help').click()
                        expect(page.locator('#help-dialog')).to_be_visible()
                        expect(page.locator('#help-dialog')).to_contain_text('Open “My dashboard”')
                        page.locator('#help-dialog').screenshot(path=str(output / f'{theme}-{width}-help.png'))
                        page.keyboard.press('Escape')
                    page.route('**/health', lambda route: route.fulfill(status=503, body='Synthetic service outage'))
                    page.locator('#pin').fill('synthetic-test-value')
                    page.locator('#connect').click()
                    expect(page.locator('#loginerror')).to_contain_text('503')
                    page.locator('#pin').fill('')
                    for theme in THEMES:
                        page.locator('#theme-preview').select_option(theme)
                        page.locator('#main-content').screenshot(path=str(output / f'{theme}-{width}-error.png'))
                assert not faults, faults
                assert all(urlsplit(request).netloc == urlsplit(url).netloc for request in requests), requests
                context.close()
            browser.close()
    finally:
        process.terminate()
        process.wait(timeout=10)
        runtime.cleanup()
    if output:
        (output / 'contrast.json').write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
    print('OK: 4 complete palettes, 29-widget parity, EN/FR, keyboard, responsive, local fonts, no profile/storage writes')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser', choices=('chromium', 'firefox', 'webkit'), default='chromium')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.output:
        args.output.mkdir(parents=True, exist_ok=True)
    run(args.browser, args.output)
