"""Four profile palettes on the production target; no historical theme editor."""
import argparse
import os
import json
from pathlib import Path
from playwright.sync_api import expect, sync_playwright
from test_production_studio import production, login
from test_rendering_regressions import fixture, THEMES


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
          selected:[read('.nav-item[aria-current="page"]','color'),read('.nav-item[aria-current="page"]','backgroundColor')],
          focus:[read('.nav-brand','outlineColor'),read('body','backgroundColor')]
        };
    }""")
    for name, colors in samples.items():
        minimum = 3 if name in ('field', 'focus') else 4.5
        assert contrast(*colors) >= minimum, (name, colors, contrast(*colors))
    return {name: round(contrast(*colors), 2) for name, colors in samples.items()}


def run(browserName, output):
    results = []
    with production(fixture()) as (url, _data, _initial, _restart):
        with sync_playwright() as playwright:
            options = {'headless':True}
            executable = os.environ.get('CCS_CHROMIUM_EXECUTABLE') or os.environ.get('CS2_CHROMIUM_BIN')
            if browserName == 'chromium' and executable:
                options['executable_path'] = executable
            browser = getattr(playwright, browserName).launch(**options)
            page = browser.new_page(viewport={'width':1366,'height':900}, reduced_motion='reduce')
            login(page, url)
            page.evaluate('() => document.fonts.ready')
            assert page.evaluate("document.fonts.check('400 14px Inter')")
            for theme in THEMES:
                page.locator('[data-section="studio"]').click()
                page.locator('#studio-profile-tab').click()
                page.select_option('#studio-theme', theme)
                page.locator('#studio-profile-name').fill('Theme check ' + theme)
                page.locator('#studio-profile-name').press('Tab')
                page.locator('#studio-publish').click()
                expect(page.locator('#studio-save-state')).to_contain_text('Published version up to date')
                page.locator('#studio-leave').click()
                expect(page.locator('html')).to_have_attribute('data-theme', theme)
                page.keyboard.press('Tab')
                page.locator('.nav-brand').focus()
                results.append({'theme':theme, 'contrast':check_palette(page)})
                if output:
                    output.mkdir(parents=True, exist_ok=True)
                    page.screenshot(path=str(output / (theme + '.png')))
            if output:
                (output / 'palette-results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
            browser.close()
    print('PASS: four published profile themes, local fonts and semantic contrast samples')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser', choices=['chromium','firefox','webkit'], default='chromium')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    run(args.browser, args.output)
