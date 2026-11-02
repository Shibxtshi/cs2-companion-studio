"""P9 secondary screens on a disposable authenticated server and synthetic GSI."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

from playwright.sync_api import expect, sync_playwright
from test_live_browser import PIN, TOKEN, start_server, stop_server

RESOLUTIONS = [(1920,1080),(1366,768),(1280,900),(1024,768),(768,1024),(390,844),(320,740)]


def run(browserName, output):
    runtime, process, url = start_server()
    try:
        with sync_playwright() as playwright:
            options = {'headless': True}
            if browserName == 'chromium' and os.environ.get('CS2_CHROMIUM_BIN'):
                options['executable_path'] = os.environ['CS2_CHROMIUM_BIN']
            browser = getattr(playwright, browserName).launch(**options)
            context = browser.new_context(viewport={'width':1366,'height':768}, reduced_motion='reduce')
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(error.stack))
            if output:
                output.mkdir(parents=True, exist_ok=True)

            def capture(name):
                if output:
                    page.screenshot(path=str(output / (name + '.png')), full_page=not page.locator('#help-dialog').is_visible())

            page.goto(url)
            page.select_option('#locale-select', 'FR')
            expect(page.locator('#login-service')).to_have_text('Serveur disponible')
            capture('01-connexion-desktop-fr')
            for locale in ['FR','EN']:
                page.select_option('#locale-select',locale)
                for width,height in RESOLUTIONS:
                    page.set_viewport_size({'width':width,'height':height})
                    page.evaluate('new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                    page.locator('#help-from-login').click()
                    expect(page.locator('#help-dialog')).to_be_visible()
                    assert page.evaluate('document.getElementById("help-dialog").scrollWidth <= document.getElementById("help-dialog").clientWidth')
                    page.keyboard.press('Escape')
            page.select_option('#locale-select','FR')
            page.set_viewport_size({'width':390,'height':844})
            capture('02-connexion-mobile-fr')
            page.set_viewport_size({'width':1366,'height':768})
            page.locator('#help-from-login').click()
            expect(page.locator('#help-dialog')).to_be_visible()
            capture('03-premiere-utilisation')
            page.keyboard.press('Escape')
            expect(page.locator('#help-from-login')).to_be_focused()
            page.locator('.welcome-actions button').last.click()
            page.reload()
            expect(page.locator('.welcome-steps')).to_be_hidden()
            page.locator('#open-help').click()
            expect(page.locator('#help-dialog')).to_be_visible()
            page.keyboard.press('Escape')
            page.locator('#pin').fill('wrong-synthetic-pin')
            page.locator('#connect').click()
            expect(page.locator('#loginerror')).to_contain_text('PIN incorrect')
            page.locator('#pin').fill('')
            capture('04-erreur-pin')
            page.select_option('#locale-select', 'EN')
            expect(page.locator('#loginerror')).to_contain_text('Incorrect PIN')
            capture('05-connexion-en')
            page.select_option('#locale-select', 'FR')
            expect(page.locator('#loginerror')).to_contain_text('PIN incorrect')
            page.select_option('#locale-select', 'EN')
            expect(page.locator('#loginerror')).to_contain_text('Incorrect PIN')
            page.locator('#pin').fill(PIN)
            page.locator('#connect').click()
            expect(page.locator('#view')).to_be_visible()
            expect(page.locator('#pin')).to_have_value('')
            page.select_option('#locale-select','FR')
            page.locator('[data-section="studio"]').click()
            expect(page.locator('#studio-app')).to_be_visible()
            page.locator('#production-import-file').set_input_files({'name':'invalid.json','mimeType':'application/json','buffer':b'{synthetic-private-marker-not-for-display'})
            expect(page.locator('#studio-alert')).to_be_visible()
            assert 'synthetic-private-marker' not in page.locator('#studio-alert').inner_text()
            page.evaluate("CCSNotifications.show({message:'unrelated success',kind:'success'})")
            expect(page.locator('#studio-alert')).to_be_visible()
            page.locator('#toast button').click()
            page.evaluate('() => {window.savedCreateObjectURL=URL.createObjectURL;URL.createObjectURL=()=>{throw Error("synthetic")};}')
            page.locator('#production-export').click()
            expect(page.locator('#toast')).to_contain_text('Téléchargement impossible')
            page.evaluate('URL.createObjectURL=window.savedCreateObjectURL;delete window.savedCreateObjectURL')
            page.locator('#toast button').click()
            page.select_option('#locale-select','EN')
            page.locator('[data-section="settings"]').click()
            capture('06-settings-tactical-blue-en')
            page.select_option('#locale-select', 'FR')
            page.locator('[data-section="studio"]').click()
            page.locator('#studio-profile-tab').click()
            page.select_option('#studio-theme', 'competitive-red')
            page.locator('#studio-publish').click()
            expect(page.locator('#studio-save-state')).to_contain_text('Version publiée à jour')
            page.locator('#studio-leave').click()
            page.locator('[data-section="settings"]').click()
            capture('07-parametres-competitive-red-fr')
            page.locator('#settings-help').click()
            page.locator('[data-help-topic="studio"]').click()
            expect(page.locator('#help-topic-content')).to_contain_text('brouillon local')
            capture('08-centre-aide')
            page.keyboard.press('Escape')
            page.locator('#diagnostics-toggle').click()
            expect(page.locator('#diag-ws')).to_have_text('Authentifiée et connectée')
            expect(page.locator('#diag-match')).to_have_text('Indisponibles ou périmées')
            capture('09-diagnostics-gsi-attente')
            body = json.dumps({'auth':{'token':TOKEN}, 'provider':{'appid':730},
                'map':{'name':'de_mirage','mode':'competitive','phase':'live','round':1},
                'player':{'activity':'playing','state':{'health':100}}}).encode()
            with urlopen(Request(url+'/gsi', body, {'Content-Type':'application/json'}, method='POST'),timeout=5) as response:
                assert response.status == 200
            expect(page.locator('#diag-match')).to_have_text('Données de partie récentes disponibles')
            capture('10-diagnostics-actifs')
            with page.expect_download() as download:
                page.locator('#download-support').click()
            report = Path(download.value.path()).read_text('utf-8')
            assert PIN not in report and TOKEN not in report
            # Browser offline emulation does not reliably close an existing WebSocket.
            stop_server(runtime, process)
            expect(page.locator('#diag-ws')).to_have_text('Déconnectée')
            expect(page.locator('#diag-match')).to_have_text('Indisponibles ou périmées')
            page.locator('#diagnostics-refresh').click()
            expect(page.locator('#diag-http')).to_contain_text('Serveur inaccessible')
            capture('11-diagnostics-hors-ligne')
            page.locator('[data-section="dashboard"]').click()
            page.locator('#demoagain').click()
            page.locator('[data-section="settings"]').click()
            expect(page.locator('#download-support')).to_be_hidden()
            expect(page.locator('#diag-match')).to_have_text('Démonstration · données synthétiques')
            capture('12-diagnostics-demonstration')
            for locale in ['FR','EN']:
                page.select_option('#locale-select',locale)
                for theme in ['tactical-blue','competitive-red','performance-green','creator-purple']:
                    page.evaluate('theme => {document.documentElement.dataset.theme = theme}', theme)
                    if locale == 'FR' and theme in ['performance-green','creator-purple']:
                        page.set_viewport_size({'width':1366,'height':768})
                        capture('parametres-' + theme)
                    for width,height in RESOLUTIONS:
                        page.set_viewport_size({'width':width,'height':height})
                        page.evaluate('new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
                        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (locale,theme,width,
                            page.evaluate('({root:document.documentElement.scrollWidth,body:document.body.scrollWidth,items:Array.from(document.querySelectorAll("body *")).filter(e=>e.getBoundingClientRect().right>innerWidth || (e.scrollWidth>e.clientWidth && e.clientWidth)).slice(0,20).map(e=>[e.tagName,e.id,e.className,e.scrollWidth,e.clientWidth,e.getBoundingClientRect().right])})'))
                        if locale == 'FR' and theme == 'tactical-blue' and width == 390:
                            capture('parametres-mobile-fr')
                page.locator('#settings-help').click()
                for button in page.locator('[data-help-topic]').all():
                    button.click()
                    assert page.locator('#help-topic-content').inner_text().strip()
                page.keyboard.press('Escape')
            assert not errors, errors
            browser.close()
            print('PASS: P9 login/errors, native help/focus, real PIN/GSI, offline/demo diagnostics, FR/EN, four themes and seven resolutions')
    finally:
        stop_server(runtime, process)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--browser',choices=['chromium','firefox','webkit'],default='chromium')
    parser.add_argument('--output',type=Path)
    args = parser.parse_args()
    run(args.browser,args.output)
