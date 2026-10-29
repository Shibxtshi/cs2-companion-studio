"""P8 complete catalog, responsive, keyboard/touch and descriptive timing matrix."""
from __future__ import annotations
import argparse
import copy
import json
import os
from pathlib import Path
import socket
import tempfile
import time

from playwright.sync_api import expect, sync_playwright
from test_customization_studio import document
from test_studio_workflows import close_preview
from test_profile_publication import PIN, launch, stop
from test_widget_characterization import KINDS, LIVE, settle
from companion.profile_contracts import encode_document, validate_contract

SIZES = [(1920,1080),(1366,768),(1280,900),(1024,768),(768,1024),(390,844),(320,740)]


def run(browserName, output):
    source = document()
    template = source['profiles'][0]
    base = template['configuration']['layout']['widgets'][0]
    source['profiles'] = []
    for variant in ['standard','compact','minimal']:
        profile = copy.deepcopy(template)
        profile.update(id='p-' + variant, name=variant.title())
        profile['configuration']['layout']['widgets'] = [
            {**base, 'id': variant + '-' + kind, 'kind': kind, 'variant': variant,
             'x': i % 3 * 8, 'y': i // 3 * 9, 'width':8, 'height':8}
            for i,kind in enumerate(KINDS)]
        source['profiles'].append(profile)
    profile = copy.deepcopy(source['profiles'][0])
    profile.update(id='p-sixty', name='Sixty instances')
    profile['configuration']['layout']['widgets'] = [
        {**base, 'id':'many-'+str(i), 'kind':KINDS[i%29], 'variant':['standard','compact','minimal'][i%3],
         'x':i%3*8, 'y':i//3*9, 'width':8, 'height':8} for i in range(60)]
    source['profiles'].append(profile)
    empty = copy.deepcopy(template)
    empty.update(id='p-empty', name='Empty')
    empty['configuration']['layout']['widgets'] = []
    source['profiles'].append(empty)
    timings = []
    with tempfile.TemporaryDirectory(prefix='ccs-studio-matrix-') as temporary:
        runtime = Path(temporary)
        (runtime / '.synthetic-publication-test').touch()
        target = runtime / 'target/profiles.json'
        target.parent.mkdir()
        target.write_bytes(encode_document(validate_contract(source,'server')))
        original = target.read_bytes()
        with socket.socket() as listener:
            listener.bind(('127.0.0.1',0)); port=listener.getsockname()[1]
        process,url=launch(runtime,port)
        try:
            with sync_playwright() as pw:
                options={'headless':True}
                if browserName=='chromium' and os.environ.get('CS2_CHROMIUM_BIN'):
                    options.update(executable_path=os.environ['CS2_CHROMIUM_BIN'],args=['--no-sandbox'])
                browser=getattr(pw,browserName).launch(**options)
                context=browser.new_context(viewport={'width':1920,'height':1080},locale='en-US',timezone_id='UTC',reduced_motion='reduce')
                page=context.new_page()
                errors=[]
                page.on('pageerror',lambda error:errors.append(str(error)))
                start=time.perf_counter()
                page.goto(url+'/__studio_test__')
                page.locator('#pin').fill(PIN); page.locator('#connect').click()
                expect(page.locator('#studio-board .widget')).to_have_count(29)
                page.evaluate('document.fonts.ready')
                timings.append({'operation':'open29IncludingAuthAutomation','ms':(time.perf_counter()-start)*1000})
                page.evaluate('state=>CCSStudioTarget.previewData(state,true)',LIVE)
                for variant in ['standard','compact','minimal']:
                    page.select_option('#studio-profile','p-'+variant)
                    page.wait_for_function('(id)=>CCSStudioTarget.snapshot().draft?.profileId===id',arg='p-'+variant)
                    expect(page.locator('#studio-board .widget')).to_have_count(29)
                    assert page.locator('#studio-board .widget[data-variant="'+variant+'"]').count()==29
                    originalGeometry=page.evaluate('CCSStudioTarget.snapshot().draft.configuration.layout')
                    for width,height in SIZES:
                        start=time.perf_counter()
                        page.set_viewport_size({'width':width,'height':height})
                        settle(page)
                        timings.append({'operation':'reflow29AutomationTwoFrames','variant':variant,'width':width,'ms':(time.perf_counter()-start)*1000})
                        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(variant,width)
                        assert page.evaluate('CCSStudioTarget.snapshot().draft.configuration.layout')==originalGeometry
                        # Bodies remain keyboard-scrollable when the actual reading footprint overflows.
                        clipping=page.locator('#studio-board .widget').evaluate_all('''cards=>cards.filter(card=>{
                          const body=card.querySelector('.widget-body');
                          return body && body.scrollHeight>body.clientHeight+1 && getComputedStyle(body).overflowY==='hidden';
                        }).map(card=>card.dataset.kind)''')
                        assert not clipping,(variant,width,clipping)
                    page.set_viewport_size({'width':1920,'height':1080})
                    page.evaluate('''() => {
                      const samples=[];
                      const measure=(operation,action)=>{const begin=performance.now();action();document.getElementById('studio-board').getBoundingClientRect();samples.push({operation,ms:performance.now()-begin});};
                      for(let i=0;i<5;i++) {
                        measure('selectWidget29',()=>document.querySelectorAll('#studio-board .widget')[i].click());
                        measure('inspector29',()=>document.getElementById('studio-profile-tab').click());
                      }
                      window.studioMeasured=samples;
                    }''')
                    timings.extend(page.evaluate('window.studioMeasured'))
                    assert target.read_bytes()==original
                start=time.perf_counter()
                page.select_option('#studio-profile','p-sixty')
                expect(page.locator('#studio-board .widget')).to_have_count(60)
                timings.append({'operation':'open60Automation','ms':(time.perf_counter()-start)*1000})
                page.evaluate('window.retainedStudioCards=[...document.querySelectorAll("#studio-board .widget")]')
                for theme in ['tactical-blue','competitive-red','performance-green','creator-purple']:
                    page.locator('#studio-profile-tab').click()
                    start=time.perf_counter()
                    page.select_option('#studio-theme',theme)
                    page.wait_for_function("()=>['saved','pristine'].includes(CCSStudioTarget.snapshot().state?.status)")
                    timings.append({'operation':'theme60IncludingLocalDebounce','theme':theme,'ms':(time.perf_counter()-start)*1000})
                    expect(page.locator('html')).to_have_attribute('data-theme',theme)
                    assert page.evaluate('retainedStudioCards.every((card,i)=>card===document.querySelectorAll("#studio-board .widget")[i])')
                    if output:
                        output.mkdir(parents=True,exist_ok=True)
                        page.screenshot(path=str(output/('studio60-'+theme+'.png')))
                # The preview consumes draft navigation/fullscreen preferences, not server state.
                for mode in ['full','compact','hidden']:
                    page.select_option('#studio-navigation',mode)
                    page.uncheck('#studio-floating')
                    page.uncheck('#studio-connection')
                    page.wait_for_function("()=>['saved','pristine'].includes(CCSStudioTarget.snapshot().state?.status)")
                    with page.expect_popup() as opened:
                        page.locator('#studio-open-preview').click()
                    preview=opened.value
                    preview.on('pageerror',lambda error:errors.append(str(error)))
                    expect(preview.locator('#board .widget')).to_have_count(60)
                    expect(preview.locator('html')).to_have_attribute('data-navigation',mode)
                    expect(preview.locator('html')).to_have_attribute('data-fullscreen-status','false')
                    if mode=='hidden':
                        expect(preview.locator('.navigation-edge')).to_be_visible()
                        preview.locator('.navigation-edge').click()
                        expect(preview.locator('html')).to_have_attribute('data-navigation-revealed','true')
                    if mode=='full':
                        preview.evaluate('document.documentElement.requestFullscreen=undefined')
                        preview.locator('#dashboard-fullscreen').click()
                        expect(preview.locator('html')).to_have_attribute('data-immersive','true')
                        preview.keyboard.press('Escape')
                        expect(preview.locator('html')).to_have_attribute('data-immersive','false')
                    close_preview(preview)
                page.locator('#studio-widget-tab').click()
                page.locator('#studio-board .widget').first.click()
                measured=page.evaluate('''() => {
                  const out=[];const measure=(operation,action)=>{const start=performance.now();action();document.getElementById('studio-board').getBoundingClientRect();out.push({operation,ms:performance.now()-start});};
                  for(const value of ['compact','minimal','standard']) measure('variant60',()=>{const select=document.getElementById('studio-variant');select.value=value;select.dispatchEvent(new Event('change'));});
                  for(let i=0;i<5;i++){measure('undo60',()=>document.getElementById('studio-undo').click());measure('redo60',()=>document.getElementById('studio-redo').click());}
                  return out;
                }''')
                timings.extend(measured)
                page.wait_for_function("()=>['saved','pristine'].includes(CCSStudioTarget.snapshot().state?.status)")
                page.locator('#studio-search').fill('health')
                expect(page.locator('#studio-library-items .studio-library-item')).to_have_count(1)
                page.locator('#studio-library-items button').click()
                expect(page.locator('#studio-alert')).to_contain_text('60')
                assert page.locator('#studio-board .widget').count()==60
                # Empty profile is usable after explicitly preserving the current local draft.
                page.select_option('#studio-profile','p-empty')
                page.locator('#studio-dialog button[value="keep"]').click()
                expect(page.locator('#studio-empty')).to_be_visible()
                assert target.read_bytes()==original
                page.locator('#studio-search').fill('health')
                page.locator('#studio-library-items button').click()
                expect(page.locator('#studio-board .widget')).to_have_count(1)
                page.wait_for_function("()=>['saved','pristine'].includes(CCSStudioTarget.snapshot().state?.status)")
                widget=page.locator('#studio-board .widget')
                widget.focus()
                page.keyboard.press('Control+z')
                expect(page.locator('#studio-board .widget')).to_have_count(0)
                page.keyboard.press('Control+Shift+z')
                expect(page.locator('#studio-board .widget')).to_have_count(1)
                # Touch panels use a separate actual touch-enabled browser context.
                touch=browser.new_context(viewport={'width':390,'height':844},has_touch=True,locale='en-US')
                mobile=touch.new_page(); mobile.on('pageerror',lambda error:errors.append(str(error)))
                mobile.goto(url+'/__studio_test__')
                mobile.locator('#pin').fill(PIN); mobile.locator('#connect').tap()
                expect(mobile.locator('#studio-app')).to_be_visible()
                mobile.locator('button[data-panel="library"]').tap()
                mobile.locator('#studio-search').fill('health')
                mobile.locator('#studio-library-items button').tap()
                mobile.locator('button[data-panel="inspector"]').tap()
                expect(mobile.locator('#studio-variant')).to_be_visible()
                mobile.select_option('#studio-variant','minimal')
                mobile.wait_for_function("()=>['saved','pristine'].includes(CCSStudioTarget.snapshot().state?.status)")
                assert mobile.evaluate('document.documentElement.scrollWidth<=innerWidth')
                if output: mobile.screenshot(path=str(output/'studio-mobile-properties.png'))
                assert not errors,errors
                if output:
                    (output/'studio-matrix.json').write_text(json.dumps({'browser':browser.version,
                        'combinations':87,'sizes':SIZES,'maximumInstances':60,'themes':4,'touch':True,'errors':errors,'samples':timings},indent=2),encoding='utf8')
                browser.close()
                print('OK: Studio 87 combinations, seven sizes, four themes, 60 instances, keyed DOM, empty profile, keyboard and touch')
        finally:
            stop(process)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--browser',choices=['chromium','firefox','webkit'],default='chromium')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    run(args.browser,args.output)
