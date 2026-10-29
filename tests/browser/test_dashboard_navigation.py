"""Synthetic P6 shell checks. No personal profiles or live GSI are used."""
from __future__ import annotations
import argparse
import os
from playwright.sync_api import expect, sync_playwright
from test_live_browser import start_server
from test_widget_characterization import open_fixture, settle, SNAPSHOT


def run(browser_name):
    runtime, proc, url = start_server()
    try:
        with sync_playwright() as playwright:
            options = {'headless': True}
            if browser_name == 'chromium' and os.environ.get('CS2_CHROMIUM_BIN'):
                options.update(executable_path=os.environ['CS2_CHROMIUM_BIN'], args=['--no-sandbox'])
            browser = getattr(playwright, browser_name).launch(**options)
            context = browser.new_context(viewport={'width': 1280, 'height': 900}, locale='en-US', timezone_id='UTC')
            page, fixture, faults = open_fixture(context, url, 29)
            values = page.evaluate(SNAPSHOT)
            expect(page.locator('#custom-tools')).to_be_hidden()
            page.locator('[data-section="studio"]').click()
            expect(page.locator('#custom-tools')).to_be_visible()
            expect(page.locator('#board')).to_have_class('board editing')
            page.locator('[data-section="dashboard"]').click()
            expect(page.locator('#custom-tools')).to_be_hidden()
            assert page.evaluate(SNAPSHOT) == values
            page.locator('[data-section="settings"]').click()
            expect(page.locator('#board')).to_be_hidden()
            page.select_option('#navigation-mode', 'full')
            expect(page.locator('html')).to_have_attribute('data-navigation','full')
            page.locator('#settings-help').click()
            expect(page.locator('#help-dialog')).to_be_visible()
            page.keyboard.press('Escape')
            page.select_option('#navigation-mode', 'hidden')
            page.uncheck('#navigation-floating')
            expect(page.locator('.navigation-float')).to_be_hidden()
            page.keyboard.press('Alt+m')
            expect(page.locator('.dashboard-navigation')).to_be_visible()
            page.keyboard.press('Escape')
            expect(page.locator('.dashboard-navigation')).to_be_hidden()
            page.locator('.navigation-edge').click()
            page.locator('[data-section="dashboard"]').click()
            expect(page.locator('#board')).to_be_visible()
            for width, height in [(1920,1080),(1366,768),(1280,900),(1024,768),(768,1024),(390,844),(320,740)]:
                page.set_viewport_size({'width':width, 'height':height})
                settle(page)
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
                assert page.locator('#board .widget').count() == 29
            page.set_viewport_size({'width':1280, 'height':900})
            page.locator('.navigation-edge').click()
            page.locator('[data-section="settings"]').click()
            page.select_option('#navigation-mode', 'compact')
            page.locator('[data-section="dashboard"]').click()
            page.locator('[data-section="settings"]').click()
            page.locator('#locale-select').select_option('FR')
            expect(page.locator('#dashboard-title')).to_have_text('Paramètres')
            page.locator('#locale-select').select_option('EN')
            page.locator('[data-section="dashboard"]').click()
            page.evaluate("document.documentElement.requestFullscreen=undefined")
            page.locator('#dashboard-fullscreen').click()
            expect(page.locator('html')).to_have_attribute('data-immersive','true')
            page.locator('.immersive-exit').click()
            expect(page.locator('html')).to_have_attribute('data-immersive','false')
            page.locator('#demoagain').click()
            expect(page.locator('#board .widget')).to_have_count(5)
            assert not faults, faults
            browser.close()
    finally:
        proc.terminate()
        proc.wait(timeout=10)
        runtime.cleanup()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--browser', choices=['chromium','firefox','webkit'], default='chromium')
    run(parser.parse_args().browser)
