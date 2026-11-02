"""Logo home actions use real authentication, existing save/exit guards and synthetic stores."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import socket
import tempfile

from playwright.sync_api import expect, sync_playwright
from test_profile_publication import launch, stop, PIN as TARGET_PIN
from test_customization_studio import document
from companion.profile_contracts import encode_document
from companion.profile_publication import access_id


def authenticate(page, pin):
    page.locator('#pin').fill(pin)
    page.locator('#connect').click()


def target(browser):
    with tempfile.TemporaryDirectory(prefix='ccs-logo-target-') as temporary:
        runtime=Path(temporary);(runtime/'.synthetic-publication-test').touch()
        path=runtime/'target/profiles.json';path.parent.mkdir()
        initial=document();path.write_bytes(encode_document(initial))
        with socket.socket() as listener:listener.bind(('127.0.0.1',0));port=listener.getsockname()[1]
        process,url=launch(runtime,port)
        try:
            context=browser.new_context(viewport={'width':1366,'height':900},has_touch=True)
            page=context.new_page();other=context.new_page();errors=[]
            for tab in [page,other]:
                tab.on('pageerror',lambda error:errors.append(str(error)))
                tab.goto(url+'/__dashboard_test__');authenticate(tab,TARGET_PIN)
                expect(tab.locator('#dashboard-profile-menu')).to_be_visible()
            page.select_option('#dashboard-profile-menu','p-second')
            other.select_option('#dashboard-profile-menu','p-competitive')
            page.locator('[data-section="settings"]').click()
            page.evaluate("window.logoNavigationSentinel='target'")
            page.locator('.nav-brand').click()
            assert page.locator('#dashboard-profile-menu').input_value()=='p-second'
            assert other.locator('#dashboard-profile-menu').input_value()=='p-competitive'
            assert page.evaluate('window.logoNavigationSentinel')=='target'
            # A Studio preference can differ from the old Dashboard hint after a restored session.
            page.evaluate('id=>sessionStorage.setItem("ccs-studio-profile:"+id,"p-second")',initial['storeId'])
            page.evaluate('context=>CCSProfileSelection.remember(context,"p-competitive")',
                          {'storeId':initial['storeId'],'accessId':access_id(initial['storeId'])})
            page.goto(url+'/__studio_test__')
            original=page.url
            page.locator('.studio-brand').click()
            assert page.url==original
            authenticate(page,TARGET_PIN)
            page.wait_for_function('() => CCSStudioTarget.snapshot().selectedProfileId==="p-second" && CCSStudioTarget.snapshot().state')
            page.select_option('#locale-select','FR')
            def edit(title):
                page.locator('#studio-board .widget').first.click(position={'x':20,'y':20})
                page.locator('#studio-title').fill(title);page.locator('#studio-title').press('Tab')
            def choose(value):page.locator('#studio-dialog button[value="'+value+'"]').click()
            before=path.read_bytes()
            edit('Unpublished logo draft')
            page.locator('.studio-brand').focus();page.keyboard.press('Enter')
            expect(page.locator('#studio-dialog')).to_be_visible()
            expect(page.locator('#studio-dialog-title')).to_have_text('Quitter le Studio ?')
            assert page.locator('#studio-dialog button').count()==4
            choose('cancel')
            assert page.url==original and path.read_bytes()==before
            page.locator('.studio-brand').click();choose('keep')
            page.wait_for_url('**/__dashboard_test__')
            assert path.read_bytes()==before
            authenticate(page,TARGET_PIN)
            expect(page.locator('#dashboard-profile-menu')).to_have_value('p-second')
            assert other.locator('#dashboard-profile-menu').input_value()=='p-competitive'
            page.goto(url+'/__studio_test__');authenticate(page,TARGET_PIN)
            expect(page.locator('#studio-dialog')).to_be_visible();choose('resume')
            page.wait_for_function('() => CCSStudioTarget.snapshot().state?.status==="saved"')
            page.select_option('#locale-select','EN')
            page.set_viewport_size({'width':390,'height':844})
            page.locator('.studio-brand').tap();choose('discard')
            expect(page.locator('#studio-dialog-title')).to_contain_text('Discard local draft')
            choose('discard');page.wait_for_url('**/__dashboard_test__')
            assert path.read_bytes()==before
            page.set_viewport_size({'width':1366,'height':900})
            page.goto(url+'/__studio_test__');authenticate(page,TARGET_PIN)
            page.wait_for_function('() => CCSStudioTarget.snapshot().state')
            edit('Explicitly published through logo')
            page.locator('.studio-brand').click()
            assert path.read_bytes()==before
            choose('publish');page.wait_for_url('**/__dashboard_test__')
            published=json.loads(path.read_text('utf-8'))
            profile=next(item for item in published['profiles'] if item['id']=='p-second')
            assert profile['revision']==2
            assert profile['configuration']['layout']['widgets'][0]['title']=='Explicitly published through logo'
            authenticate(page,TARGET_PIN)
            expect(page.locator('#dashboard-profile-menu')).to_have_value('p-second')
            assert not errors,errors
            context.close()
        finally:stop(process)


def run(browserName):
    with sync_playwright() as playwright:
        options={'headless':True}
        if browserName=='chromium' and os.environ.get('CS2_CHROMIUM_BIN'):options['executable_path']=os.environ['CS2_CHROMIUM_BIN']
        browser=getattr(playwright,browserName).launch(**options)
        try:target(browser)
        finally:browser.close()
    print('PASS: logo mouse/keyboard/touch, auth gates, no section reload, profile preservation, all four Studio exit choices')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--browser',choices=['chromium','firefox','webkit'],default='chromium')
    run(parser.parse_args().browser)
