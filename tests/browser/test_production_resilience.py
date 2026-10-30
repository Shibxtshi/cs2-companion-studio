"""Production draft persistence, privacy and browser-storage failure journeys."""
import argparse
import json
import os
from pathlib import Path
import re
import tempfile

from playwright.sync_api import expect, sync_playwright
from test_production_studio import production, login
from test_production_acceptance import field, saved


def options(browserName):
    value = {'headless':True}
    if browserName == 'chromium' and os.environ.get('CCS_CHROMIUM_EXECUTABLE'):
        value['executable_path'] = os.environ['CCS_CHROMIUM_EXECUTABLE']
    return value


def read_drafts(page):
    return page.evaluate('''() => new Promise((resolve,reject) => {
      const opening=indexedDB.open('ccs-local-drafts');
      opening.onerror=()=>reject(opening.error);
      opening.onsuccess=()=>{
        const database=opening.result;
        const transaction=database.transaction(['drafts','publications'],'readonly');
        const output={};
        for(const name of ['drafts','publications']){
          const request=transaction.objectStore(name).getAll();
          request.onsuccess=()=>{output[name]=request.result;};
        }
        transaction.oncomplete=()=>{database.close();resolve(output);};
        transaction.onabort=()=>{database.close();reject(transaction.error);};
      };
    })''')


def persistent_browser(playwright, browserName):
    with production() as (url, data, _initial, _restart), tempfile.TemporaryDirectory(prefix='ccs-p10-browser-') as temporary:
        browserType = getattr(playwright, browserName)
        context = browserType.launch_persistent_context(temporary, viewport={'width':1366,'height':900}, **options(browserName))
        try:
            page = context.new_page()
            login(page,url)
            page.locator('[data-section="studio"]').click()
            page.locator('.studio-library-item[data-kind="health"] button').click()
            field(page,'studio-title','P10 retained after full close')
            saved(page)
            original = (data / 'profiles.json').read_bytes()
            records = read_drafts(page)
            assert len(records['drafts']) == 1 and records['publications'] == []
            assert 'synthetic-production-pin' not in json.dumps(records)
            assert 'synthetic-production-gsi' not in json.dumps(records)
        finally:
            context.close()
        context = browserType.launch_persistent_context(temporary, viewport={'width':1366,'height':900}, **options(browserName))
        try:
            page = context.new_page()
            page.goto(url)
            expect(page.locator('#view')).to_be_hidden()
            expect(page.locator('#pin')).to_have_value('')
            login(page,url)
            page.locator('[data-section="studio"]').click()
            page.locator('#studio-dialog button[value="resume"]').click()
            expect(page.locator('#studio-board>.widget')).to_contain_text('P10 retained after full close')
            saved(page)
            assert (data / 'profiles.json').read_bytes() == original
            page.locator('#studio-logout').click()
            page.locator('#studio-dialog button[value="cancel"]').click()
            expect(page.locator('#studio-app')).to_be_visible()
            assert len(read_drafts(page)['drafts']) == 1
            page.locator('#studio-logout').click()
            page.locator('#studio-dialog button[value="logout"]').click()
            expect(page.locator('#view')).to_be_hidden()
            assert read_drafts(page) == {'drafts':[],'publications':[]}
            assert (data / 'profiles.json').read_bytes() == original
            page.locator('#demo').click()
            expect(page.locator('#view')).to_be_visible()
            expect(page.locator('[data-section="studio"]')).to_be_disabled()
            assert 'P10 retained after full close' not in page.locator('body').inner_text()
            assert (data / 'profiles.json').read_bytes() == original
        finally:
            context.close()
    print('PASS: real browser close/reopen, PIN not persisted, explicit draft restore, cancelled/confirmed logout and demo privacy',flush=True)


def storage_failures(browser):
    for failure in ['quota','abort']:
        with production() as (url,data,_initial,_restart):
            context = browser.new_context(viewport={'width':1366,'height':900})
            context.add_init_script('''(() => {
              window.p10StorageFailure=null;
              const original=IDBObjectStore.prototype.put;
              IDBObjectStore.prototype.put=function(...args){
                if(this.name==='drafts' && window.p10StorageFailure){
                  throw new DOMException('Synthetic P10 failure',window.p10StorageFailure==='quota'?'QuotaExceededError':'AbortError');
                }
                return original.apply(this,args);
              };
            })();''')
            try:
                page = context.new_page()
                login(page,url)
                page.locator('[data-section="studio"]').click()
                page.locator('.studio-library-item[data-kind="health"] button').click()
                field(page,'studio-title','P10 last confirmed draft')
                saved(page)
                confirmed = read_drafts(page)
                original = (data / 'profiles.json').read_bytes()
                page.evaluate('failure=>{window.p10StorageFailure=failure;}',failure)
                field(page,'studio-title','P10 not confirmed on disk')
                expect(page.locator('#studio-save-state')).to_contain_text('Local persistence failed')
                assert read_drafts(page) == confirmed
                assert (data / 'profiles.json').read_bytes() == original
                expect(page.locator('#studio-board>.widget')).to_contain_text('P10 not confirmed on disk')
                page.evaluate('window.p10StorageFailure=null')
                page.locator('#studio-leave').click()
                expect(page.locator('#studio-app')).to_be_hidden()
                assert read_drafts(page) != confirmed
                assert (data / 'profiles.json').read_bytes() == original
            finally:
                context.close()
        print('PASS: native IndexedDB '+failure+' preserves previous committed draft/server and keeps newer work in memory',flush=True)
    with production() as (url,data,_initial,_restart):
        context = browser.new_context()
        context.add_init_script("Object.defineProperty(window,'indexedDB',{get(){throw new DOMException('Synthetic P10 denial','SecurityError');}})")
        try:
            page=context.new_page()
            login(page,url)
            original=(data/'profiles.json').read_bytes()
            page.locator('[data-section="studio"]').click()
            expect(page.locator('#toast[role="alert"]')).to_be_visible()
            expect(page.locator('#studio-app')).to_be_hidden()
            expect(page.locator('#view')).to_be_visible()
            page.locator('[data-section="settings"]').click()
            expect(page.locator('#production-profile-preferences')).to_be_visible()
            assert (data/'profiles.json').read_bytes()==original
        finally:
            context.close()
    print('PASS: unavailable IndexedDB does not publish or block Dashboard/Settings access',flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser',choices=['chromium','firefox','webkit'],default='chromium')
    parser.add_argument('--group',choices=['all','persistent','storage'],default='all')
    args=parser.parse_args()
    with sync_playwright() as playwright:
        if args.group in ['all','persistent']:
            persistent_browser(playwright,args.browser)
        if args.group in ['all','storage']:
            browser=getattr(playwright,args.browser).launch(**options(args.browser))
            try:
                storage_failures(browser)
            finally:
                browser.close()
