"""Descriptive secondary-screen timings; synthetic data, real clocks, no thresholds."""
import argparse
import json
import os
from pathlib import Path
import time

from playwright.sync_api import sync_playwright
from test_live_browser import start_server


def run(repeats, output):
    runtime, process, url = start_server()
    samples = []
    try:
        with sync_playwright() as playwright:
            options = {'headless': True}
            if os.environ.get('CS2_CHROMIUM_BIN'):
                options['executable_path'] = os.environ['CS2_CHROMIUM_BIN']
            browser = playwright.chromium.launch(**options)
            version = browser.version
            for iteration in range(repeats):
                context = browser.new_context(viewport={'width':1366,'height':768}, reduced_motion='reduce')
                page = context.new_page()
                start = time.perf_counter()
                page.goto(url)
                page.locator('#login').wait_for(state='visible')
                page.evaluate('document.fonts.ready')
                result = {'iteration':iteration, 'openIncludingAutomationMs':(time.perf_counter()-start)*1000,
                          'navigationDclMs':page.evaluate('performance.getEntriesByType("navigation")[0].domContentLoadedEventEnd')}
                page.locator('#demo').click()
                page.locator('#view').wait_for(state='visible')
                asyncClick = '''async selector => {const start=performance.now();document.querySelector(selector).click();await Promise.resolve();void document.body.offsetHeight;return performance.now()-start;}'''
                result['settingsUiMs'] = page.evaluate(asyncClick,'[data-section="settings"]')
                result['helpUiMs'] = page.evaluate(asyncClick,'#settings-help')
                page.keyboard.press('Escape')
                result['diagnosticsUiMs'] = page.evaluate(asyncClick,'#diagnostics-toggle')
                result['languageUiMs'] = page.evaluate('''async()=>{const start=performance.now();CS2I18N.setLocale('FR');await Promise.resolve();void document.body.offsetHeight;return performance.now()-start;}''')
                result['dashboardUiMs'] = page.evaluate(asyncClick,'[data-section="dashboard"]')
                result['domElements'] = page.locator('body *').count()
                samples.append(result)
                context.close()
            browser.close()
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps({'browser':version,'viewport':[1366,768],'repeats':repeats,
            'notes':'UI timings include microtasks/forced layout, exclude automation. Opening includes automation/fonts/HTTP. Real clocks, sequential samples, synthetic demo. No latency gate.',
            'samples':samples},indent=2),encoding='utf-8')
        print('PASS: secondary-screen samples recorded',output)
    finally:
        process.terminate();process.wait(timeout=10);runtime.cleanup()


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--repeats',type=int,default=5)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    run(args.repeats,args.output)
