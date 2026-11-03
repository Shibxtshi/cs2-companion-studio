"""Production locale switching, explicit bindings and preservation of personal text."""
import argparse
import json
import os
from pathlib import Path

from playwright.sync_api import expect, sync_playwright
from test_production_studio import PIN, ROOT, production, target_document
from widget_fixtures import settle


def run(browser):
    initial = target_document()
    initial['profiles'][0]['name'] = 'studio.publish'
    with production(initial) as (url, data, _initial, _restart):
        context = browser.new_context(viewport={'width': 1366, 'height': 900})
        context.add_init_script("if (!localStorage.getItem('cs2-companion-language')) localStorage.setItem('cs2-companion-language', 'FR')")
        page = context.new_page()
        errors, commands = [], []
        page.on('pageerror', lambda error: errors.append(str(error)))

        def proxy(socket):
            server = socket.connect_to_server()
            server.on_message(socket.send)

            def forward(raw):
                commands.append(json.loads(raw).get('type'))
                server.send(raw)

            socket.on_message(forward)

        page.route_web_socket('**/ws', proxy)
        page.goto(url)
        page.wait_for_function("() => document.documentElement.dataset.i18nReady === 'true'")
        expect(page.locator('#login-title')).to_have_text('Se connecter à CCS')
        page.locator('#pin').fill('incorrect-synthetic-pin')
        page.locator('#connect').click()
        expect(page.locator('#loginerror')).to_contain_text('PIN incorrect')
        page.select_option('#locale-select', 'EN')
        expect(page.locator('#loginerror')).to_contain_text('Incorrect PIN')
        page.locator('#pin').fill(PIN)
        page.locator('#connect').click()
        expect(page.locator('#dashboard-profile-menu')).to_be_visible()
        expect(page.locator('#dashboard-profile-menu option:checked')).to_have_text('studio.publish')
        page.locator('[data-section="studio"]').click()
        expect(page.locator('#studio-app')).to_be_visible()
        page.locator('.studio-library-item[data-kind="health"] button').click()
        personal = 'Santé "Émilie" <img src=x onerror=alert(1)> {amount}'[:36]
        page.locator('#studio-title').fill(personal)
        page.locator('#studio-title').dispatch_event('change')
        expect(page.locator('#studio-board .widget-heading')).to_have_text(personal)
        page.select_option('#locale-select', 'FR')
        expect(page.locator('.studio-library-item[data-kind="health"] h3')).to_have_text('Santé')
        expect(page.locator('#studio-board .widget-heading')).to_have_text(personal)
        expect(page.locator('#studio-publish')).to_have_text('Enregistrer et appliquer')
        page.select_option('#studio-variant', 'compact')
        expect(page.locator('#studio-save-state')).to_contain_text('Brouillon conservé')
        assert 'profile_operation' not in commands
        assert not json.loads((data / 'profiles.json').read_bytes())['profiles'][0]['configuration']['layout']['widgets']
        page.locator('[data-section="dashboard"]').click()
        expect(page.locator('#studio-dialog')).to_be_visible()
        expect(page.locator('#studio-dialog-title')).to_have_text('Quitter le Studio ?')
        page.evaluate("() => CS2I18N.setLocale('EN')")
        expect(page.locator('#studio-dialog-title')).to_have_text('Leave the Studio?')
        page.locator('#studio-dialog button[value="cancel"]').click()
        page.locator('#studio-publish').click()
        expect(page.locator('#studio-save-state')).to_contain_text('Published version up to date')
        assert commands.count('profile_operation') == 1
        with page.expect_popup() as popup:
            page.locator('#studio-open-preview').click()
        preview = popup.value
        expect(preview.locator('#board .widget-heading')).to_have_text(personal)
        preview.select_option('#locale-select', 'FR')
        expect(preview.locator('#studio-preview-exit')).to_have_text('Fermer l’aperçu')
        expect(preview.locator('#board .widget-heading')).to_have_text(personal)
        preview.close()
        page.locator('.studio-brand').click()
        expect(page.locator('#board .widget-heading')).to_have_text(personal)
        page.reload()
        expect(page.locator('#login-title')).to_have_text('Se connecter à CCS')
        page.locator('#pin').fill(PIN)
        page.locator('#connect').click()
        expect(page.locator('#board .widget-heading')).to_have_text(personal)
        assert page.locator('#board img').count() == 0
        page.locator('[data-section="studio"]').click()
        page.locator('#studio-board .widget').first.click()
        page.locator('#studio-title').fill('widgets.health.title')
        page.locator('#studio-title').dispatch_event('change')
        page.select_option('#locale-select', 'EN')
        expect(page.locator('#studio-board .widget-heading')).to_have_text('widgets.health.title')
        expect(page.locator('#dashboard-profile-menu option:checked')).to_have_text('studio.publish')
        assert commands.count('profile_operation') == 1
        page.locator('.studio-library-item[data-kind="events"] button').click()
        for health in (100, 87):
            response = context.request.post(url + '/gsi', data={
                'auth': {'token': 'synthetic-production-gsi'},
                'map': {'name': 'de_mirage', 'phase': 'live', 'round': 1},
                'player': {'name': 'Synthetic Santé', 'state': {'health': health}},
            })
            assert response.ok
        expect(page.locator('#studio-board .w-events [data-list="events"]')).to_contain_text('Damage taken · 87 HP remaining')
        page.select_option('#locale-select', 'FR')
        expect(page.locator('#studio-board .w-events [data-list="events"]')).to_contain_text('Dégâts reçus · 87 HP restants')
        for width in (390, 320):
            page.set_viewport_size({'width': width, 'height': 844})
            settle(page)
            dimensions = page.evaluate("() => ({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,items:[...document.querySelectorAll('body *')].map(node=>({tag:node.tagName,cls:node.className,text:node.textContent.slice(0,70),right:node.getBoundingClientRect().right})).filter(item=>item.right>innerWidth).slice(0,15)})")
            assert dimensions['scrollWidth'] <= dimensions['width'], dimensions
        assert commands.count('profile_operation') == 1
        assert not errors, errors
        context.close()

        # A complete third language is data-only and is not shipped as a real translation.
        registry = json.loads((ROOT / 'static/locales/languages.json').read_text('utf-8'))
        registry['languages'].append({'code': 'ZZ', 'name': 'Synthetic', 'file': 'zz.json', 'confirmYes': 'Y'})
        third = json.loads((ROOT / 'static/locales/en.json').read_text('utf-8'))
        third['experience.login'] = 'Synthetic <img src=x onerror=alert(1)> sign-in'
        context = browser.new_context(viewport={'width': 390, 'height': 844})
        page = context.new_page()
        page.route('**/static/locales/languages.json', lambda route: route.fulfill(json=registry))
        page.route('**/static/locales/zz.json', lambda route: route.fulfill(json=third))
        page.goto(url)
        expect(page.locator('#locale-select option[value="ZZ"]')).to_have_count(1)
        page.select_option('#locale-select', 'ZZ')
        expect(page.locator('#login-title')).to_have_text('Synthetic <img src=x onerror=alert(1)> sign-in')
        assert page.locator('#login-title img').count() == 0
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        context.close()
    print('PASS: production FR/EN, hot PIN/dialog/preview translation, data-only third locale, explicit publication and personal-text isolation')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--browser', default='chromium', choices=['chromium', 'firefox', 'webkit'])
    args = parser.parse_args()
    with sync_playwright() as playwright:
        options = {'headless': True}
        if args.browser == 'chromium' and os.environ.get('CCS_CHROMIUM_EXECUTABLE'):
            options.update(executable_path=os.environ['CCS_CHROMIUM_EXECUTABLE'], args=['--no-sandbox'])
        browser = getattr(playwright, args.browser).launch(**options)
        try:
            run(browser)
        finally:
            browser.close()
