"""Read-only P6 dashboard against the isolated P5 authenticated target composition."""
from __future__ import annotations
import argparse
import copy
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import time
from urllib.request import Request, urlopen

from playwright.sync_api import expect, sync_playwright
from test_profile_publication import ROOT, PIN, launch, stop, prepare, edit, wait_state
from widget_fixtures import KINDS, settle
sys.path.insert(0, str(ROOT))
from companion.profile_contracts import encode_document, validate_contract


def run(browserName, output):
    corpus = json.loads((ROOT / 'tests/browser/fixtures/draft-contracts.json').read_text('utf-8'))
    first = copy.deepcopy(corpus['profile'])
    first.update(id='p-first', name='Competitive')
    base = first['configuration']['layout']['widgets'][0]
    first['configuration']['layout'] = {'columns':24, 'widgets': [
        {**base, 'id':'target-' + str(i), 'kind':KINDS[i % 29],
         'x':i % 4 * 6, 'y':i // 4 * 6, 'width':6, 'height':4,'variant':['standard','compact','minimal'][i%3]} for i in range(60)]}
    first['configuration']['layout']['widgets'][1].update(x=0,y=0)
    second = copy.deepcopy(first)
    second.update(id='p-second',name='Second Screen',revision=1)
    second['configuration']['theme']='creator-purple'
    document = {'format':'ccs-dashboard-store','version':1,'storeId':'1'*32,'catalogRevision':7,
                'profiles':[first,second],'tombstones':[],'receipts':[]}
    measurements = []
    with tempfile.TemporaryDirectory(prefix='ccs-dashboard-target-') as temporary:
        runtime = Path(temporary)
        (runtime / '.synthetic-publication-test').touch()
        target = runtime / 'target/profiles.json'
        target.parent.mkdir()
        target.write_bytes(encode_document(validate_contract(document,'server')))
        with socket.socket() as listener:
            listener.bind(('127.0.0.1',0)); port=listener.getsockname()[1]
        process,url=launch(runtime,port)
        try:
            with sync_playwright() as playwright:
                options={'headless':True}
                if browserName=='chromium' and os.environ.get('CS2_CHROMIUM_BIN'):
                    options.update(executable_path=os.environ['CS2_CHROMIUM_BIN'],args=['--no-sandbox'])
                browser=getattr(playwright,browserName).launch(**options)
                context=browser.new_context(viewport={'width':1280,'height':900},locale='en-US',timezone_id='UTC')
                faults=[]
                def page(context):
                    result=context.new_page()
                    result.on('pageerror',lambda error:faults.append(str(error)))
                    result.goto(url+'/__dashboard_test__')
                    expect(result.locator('script[data-ccs-src="/static/js/studio-preview-host.js"]')).to_have_count(0)
                    expect(result.locator('#login')).to_be_visible()
                    result.locator('#pin').fill(PIN)
                    result.locator('#connect').click()
                    expect(result.locator('#dashboard-profile-menu')).to_be_visible()
                    expect(result.locator('#board .widget')).to_have_count(60)
                    return result
                a=page(context)
                b=page(context)
                device=browser.new_context(viewport={'width':390,'height':844},locale='en-US',timezone_id='UTC',has_touch=True)
                c=page(device)
                b.select_option('#dashboard-profile-menu','p-second')
                c.select_option('#dashboard-profile-menu','p-second')
                expect(a.locator('html')).to_have_attribute('data-theme','tactical-blue')
                expect(b.locator('html')).to_have_attribute('data-theme','creator-purple')
                expect(c.locator('#theme-preview')).to_have_value('creator-purple')
                c.locator('[data-section="settings"]').tap()
                c.select_option('#navigation-mode','hidden')
                c.uncheck('#navigation-floating')
                c.locator('.navigation-edge').tap()
                c.locator('[data-section="dashboard"]').tap()
                expect(c.locator('#board')).to_be_visible()
                raw=target.read_bytes()
                a.bring_to_front()
                settle(a)
                measured = a.evaluate("""layout => {
                    const samples=[];
                    const measure=(operation,action)=>{
                        const started=performance.now(); action();
                        document.getElementById('board').getBoundingClientRect();
                        samples.push({operation,ms:performance.now()-started});
                    };
                    for(let i=0;i<5;i++){
                        measure('profile60',()=>{const select=document.getElementById('dashboard-profile-menu');select.value=i%2?'p-first':'p-second';select.dispatchEvent(new Event('change'));});
                        measure('theme',()=>{const select=document.getElementById('theme-preview');select.value=document.documentElement.dataset.theme==='tactical-blue'?'competitive-red':'tactical-blue';select.dispatchEvent(new Event('change'));});
                    }
                    const select=document.getElementById('dashboard-profile-menu');select.value='p-first';select.dispatchEvent(new Event('change'));
                    document.documentElement.requestFullscreen=undefined;
                    for(let i=0;i<5;i++){
                        measure('immersiveEnter',()=>document.getElementById('dashboard-fullscreen').click());
                        measure('immersiveExit',()=>document.querySelector('.immersive-exit').click());
                    }
                    for(const width of [1600,900,600,390,320]){
                        const started=performance.now();
                        for(let i=0;i<100;i++) CCSDashboardLayout.project(layout,width);
                        samples.push({operation:'project60',width,count:100,ms:(performance.now()-started)/100});
                    }
                    return samples;
                }""",first['configuration']['layout'])
                measurements.extend(measured)
                a.evaluate('window.originalCard=document.querySelector("#board").firstElementChild')
                a.evaluate("""() => {
                    window.resizePaintMs=null;
                    addEventListener('resize',()=>{
                        const start=performance.now();
                        requestAnimationFrame(()=>requestAnimationFrame(()=>{window.resizePaintMs=performance.now()-start;}));
                    });
                }""")
                saved_geometry=copy.deepcopy(first['configuration']['layout'])
                for width,height in [(1920,1080),(1366,768),(1280,900),(1024,768),(768,1024),(390,844),(320,740),(1920,1080)]:
                    start=time.perf_counter()
                    a.set_viewport_size({'width':width,'height':height})
                    settle(a)
                    measurements.append({'operation':'reflow','width':width,'ms':(time.perf_counter()-start)*1000,'eventToTwoFramesMs':a.evaluate('window.resizePaintMs')})
                    assert a.evaluate('document.documentElement.scrollWidth <= innerWidth'),width
                    assert a.locator('#board .widget').count()==60
                    assert a.evaluate('window.originalCard===document.querySelector("#board").firstElementChild')
                    boxes=a.locator('#board>.widget').evaluate_all('(cards)=>cards.map(card=>{const r=card.getBoundingClientRect();return {x:r.x,y:r.y,right:r.right,bottom:r.bottom};})')
                    for i,box in enumerate(boxes):
                        for other in boxes[i+1:]:
                            assert box['right']<=other['x']+.5 or other['right']<=box['x']+.5 or box['bottom']<=other['y']+.5 or other['bottom']<=box['y']+.5
                inventory=a.locator('.w-inventory[data-variant="minimal"]').first
                beforeHeight=inventory.bounding_box()['height']
                inventory.locator('summary').click()
                settle(a)
                assert inventory.bounding_box()['height']>=beforeHeight
                inventory.locator('summary').click()
                settle(a)
                assert target.read_bytes()==raw,'Responsive/details must not write storage'
                assert json.loads(target.read_bytes())['profiles'][0]['configuration']['layout']==saved_geometry
                b.evaluate('window.originalCard=document.querySelector("#board").firstElementChild')
                publisher=prepare(context,url)
                edit(publisher,'p-first','Competitive published')
                publisher.evaluate('publicationHarness.begin()')
                wait_state(publisher,'published')
                expect(a.locator('#dashboard-title')).to_have_text('Competitive published')
                expect(b.locator('#dashboard-title')).to_have_text('Second Screen')
                expect(c.locator('#dashboard-title')).to_have_text('Second Screen')
                assert b.evaluate('window.originalCard===document.querySelector("#board").firstElementChild')
                body=json.dumps({'auth':{'token':'synthetic-publication-gsi-token'},
                    'map':{'name':'de_mirage','phase':'live','round':3,'team_ct':{'score':2},'team_t':{'score':1}},
                    'round':{'phase':'live'},'player':{'team':'CT','state':{'health':77}}}).encode()
                with urlopen(Request(url+'/gsi',body,{'Content-Type':'application/json'},method='POST'),timeout=5) as response:
                    assert response.status==200
                expect(a.locator('.w-health [data-v="health"]').first).to_have_text('77')
                assert a.evaluate('window.originalCard!==document.querySelector("#board").firstElementChild')
                a.evaluate('window.liveCard=document.querySelector("#board").firstElementChild')
                for _ in range(3):
                    with urlopen(Request(url+'/gsi',body,{'Content-Type':'application/json'},method='POST'),timeout=5):
                        pass
                settle(a)
                assert a.evaluate('window.liveCard===document.querySelector("#board").firstElementChild')
                publisher.evaluate("publicationHarness.remove('p-second',1)")
                wait_state(publisher,'published')
                expect(b.locator('#dashboard-profile-menu')).to_have_value('p-first')
                expect(c.locator('#dashboard-profile-menu')).to_have_value('p-first')
                content={'name':'Empty target','configuration':copy.deepcopy(first['configuration'])}
                content['configuration']['layout']['widgets']=[]
                publisher.evaluate("([id,content])=>publicationHarness.create(id,content)",['p-empty',content])
                wait_state(publisher,'published')
                a.select_option('#dashboard-profile-menu','p-empty')
                expect(a.locator('#empty-board')).to_be_visible()
                expect(a.locator('#board .widget')).to_have_count(0)
                content['name']='One widget'
                content['configuration']['layout']['widgets']=[first['configuration']['layout']['widgets'][0]]
                publisher.evaluate("([id,content])=>publicationHarness.create(id,content)",['p-one',content])
                wait_state(publisher,'published')
                a.select_option('#dashboard-profile-menu','p-one')
                expect(a.locator('#board .widget')).to_have_count(1)
                content['name']='Bounded fallback'
                content['configuration']['layout']['widgets']=[
                    {**base,'id':'overflow-'+str(i),'kind':'health','x':0,'y':0,'width':24,'height':4096}
                    for i in range(3)]
                publisher.evaluate("([id,content])=>publicationHarness.create(id,content)",['p-fallback',content])
                wait_state(publisher,'published')
                a.select_option('#dashboard-profile-menu','p-fallback')
                expect(a.locator('#board .widget')).to_have_count(3)
                expect(a.locator('#board .layout-fallback')).to_have_count(1)
                boxes=a.locator('#board>.widget').evaluate_all('(cards)=>cards.map(card=>{const r=card.getBoundingClientRect();return {y:r.y,bottom:r.bottom};})')
                assert boxes[1]['y']>=boxes[0]['bottom'] and boxes[2]['y']>=boxes[1]['bottom']
                expect(a.locator('#notice')).to_contain_text('remaining widgets')
                a.select_option('#dashboard-profile-menu','p-first')
                for variant in ['standard','compact','minimal']:
                    content={'name':variant,'configuration':copy.deepcopy(first['configuration'])}
                    content['configuration']['layout']['widgets']=copy.deepcopy(first['configuration']['layout']['widgets'][:29])
                    for widget in content['configuration']['layout']['widgets']:
                        widget['variant']=variant
                    publisher.evaluate("([id,content])=>publicationHarness.create(id,content)",['p-'+variant,content])
                    wait_state(publisher,'published')
                    a.select_option('#dashboard-profile-menu','p-'+variant)
                    a.bring_to_front()
                    for width,height in [(1920,1080),(1366,768),(1280,900),(1024,768),(768,1024),(390,844),(320,740)]:
                        a.set_viewport_size({'width':width,'height':height})
                        settle(a)
                        assert a.evaluate('document.documentElement.scrollWidth <= innerWidth'),(variant,width)
                        clipped=a.locator('#board>.widget').evaluate_all('(cards)=>cards.filter(card=>card.scrollHeight>card.clientHeight+2).map(card=>({kind:card.dataset.kind,height:card.clientHeight,scroll:card.scrollHeight}))')
                        assert not clipped,(variant,width,clipped)
                a.select_option('#dashboard-profile-menu','p-first')
                assert not faults,faults
                if output:
                    output.mkdir(parents=True,exist_ok=True)
                    (output/'target-performance.json').write_text(json.dumps(measurements,indent=2),encoding='utf8')
                    a.screenshot(path=str(output/'target-desktop.png'))
                    c.screenshot(path=str(output/'target-phone.png'))
                browser.close()
        finally:
            stop(process)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--browser',choices=['chromium','firefox','webkit'],default='chromium')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    run(args.browser,args.output)
