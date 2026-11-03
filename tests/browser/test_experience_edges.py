"""P9 unavailable-server, throttle, keyboard and enlarged-layout cases."""
import argparse
import os
from playwright.sync_api import sync_playwright, expect
from test_live_browser import start_server, stop_server


def run(browserName):
    runtime, process, url = start_server()
    try:
        with sync_playwright() as playwright:
            options = {'headless': True}
            if browserName == 'chromium' and os.environ.get('CS2_CHROMIUM_BIN'):
                options['executable_path'] = os.environ['CS2_CHROMIUM_BIN']
            browser = getattr(playwright,browserName).launch(**options)
            context = browser.new_context(viewport={'width':1280,'height':900})
            page = context.new_page()
            errors=[]
            page.on('pageerror',lambda error:errors.append(error.stack))
            page.route('**/health',lambda route:route.fulfill(status=503,body='synthetic offline'))
            page.goto(url)
            expect(page.locator('#login-service')).to_contain_text('Server unreachable')
            page.locator('#pin').fill('synthetic-invalid-pin')
            page.locator('#connect').click()
            expect(page.locator('#loginerror')).to_contain_text('Server unreachable')
            page.locator('#demo').click()
            expect(page.locator('#logout')).to_have_text('Exit demonstration')
            page.locator('#logout').click()
            expect(page.locator('#login-service')).to_contain_text('Session ended')
            expect(page.locator('#pin')).to_have_value('')
            page.unroute('**/health')
            page.reload()
            # CSS zoom exercises enlarged layout, not a claim about every OS/browser zoom mode.
            page.evaluate("document.documentElement.style.zoom='2'")
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.locator('#pin').focus()
            page.locator('#help-from-login').click()
            expect(page.locator('#help-dialog')).to_be_visible()
            page.keyboard.press('Tab')
            assert page.evaluate('document.getElementById("help-dialog").contains(document.activeElement)')
            page.keyboard.press('Escape')
            expect(page.locator('#help-from-login')).to_be_focused()
            page.evaluate("document.documentElement.style.zoom='1'")
            for attempt in range(5):
                page.locator('#pin').fill('synthetic-invalid-pin')
                page.locator('#connect').click()
                expect(page.locator('#loginerror')).to_contain_text('Incorrect PIN')
                page.locator('#pin').fill('')
            page.locator('#pin').fill('synthetic-invalid-pin')
            page.locator('#connect').click()
            expect(page.locator('#loginerror')).to_contain_text('temporarily limited')
            # The existing server refuses before authentication; the UI must not invent a countdown.
            assert 'seconds' not in page.locator('#loginerror').inner_text()
            assert not errors,errors
            browser.close()
        print('PASS: unavailable server, demo exit, ended session, 200% CSS zoom, native keyboard focus and real login throttling')
    finally:
        stop_server(runtime, process)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--browser',choices=['chromium','firefox','webkit'],default='chromium')
    run(parser.parse_args().browser)
