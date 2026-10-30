"""Reproducible production-composition timings and an optional bounded synthetic soak."""
import argparse
import copy
import json
import os
from pathlib import Path
import platform
import statistics
import sys
import time

from playwright.sync_api import expect, sync_playwright
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from companion.profile_activation import target_document
from companion.profile_store import PROFILE_KINDS
from test_production_studio import production, login, PIN
from test_production_resilience import options

def document(count):
    corpus=json.loads((ROOT/'tests/browser/fixtures/draft-contracts.json').read_text('utf-8'))
    base=corpus['profile']['configuration']['layout']['widgets'][0]
    kinds=sorted(PROFILE_KINDS)
    value=target_document()
    profile=value['profiles'][0]
    profile['name']='Measured '+str(count)
    profile['configuration']['layout']['widgets']=[{**base,'id':'measured-'+str(index),
        'kind':kinds[index%29],'x':index%3*8,'y':index//3*9,'width':8,'height':8,'variant':'standard'}
        for index in range(count)]
    second=copy.deepcopy(profile)
    second.update(id='p-other',name='Other measured profile')
    value['profiles'].append(second)
    return value


def signal(page,url,value):
    response=page.request.post(url+'/gsi',data={'auth':{'token':'synthetic-production-gsi'},
        'map':{'name':'de_synthetic','phase':'live','round':1},'round':{'phase':'live'},
        'player':{'name':'Synthetic benchmark','state':{'health':value,'armor':80,'money':2600}}})
    assert response.status==200


def memory(context,page):
    result={'dashboardNodes':page.locator('#board *').count(),'studioNodes':page.locator('#studio-board *').count()}
    if context.browser and context.browser.browser_type.name=='chromium':
        session=context.new_cdp_session(page)
        try:
            session.send('HeapProfiler.collectGarbage')
            result['postGcHeapBytes']=session.send('Runtime.getHeapUsage')['usedSize']
            reference=session.send('Runtime.evaluate',{'expression':'document'})['result']['objectId']
            result['documentListeners']=len(session.send('DOMDebugger.getEventListeners',{'objectId':reference})['listeners'])
            session.send('Runtime.releaseObject',{'objectId':reference})
        finally:
            session.detach()
    return result


def timings(browser,repeats):
    samples=[]
    for count in [29,60]:
        for repeat in range(repeats):
            started=time.perf_counter()
            with production(document(count)) as (url,data,_initial,restart):
                samples.append({'operation':'isolatedServiceReadyIncludingFixtureMs','widgets':count,'repeat':repeat,'ms':(time.perf_counter()-started)*1000})
                context=browser.new_context(viewport={'width':1920,'height':1080},reduced_motion='reduce')
                try:
                    page=context.new_page()
                    def measure(operation,action):
                        start=time.perf_counter()
                        action()
                        samples.append({'operation':operation,'widgets':count,'repeat':repeat,'ms':(time.perf_counter()-start)*1000})
                    measure('pageDclMs',lambda:page.goto(url,wait_until='domcontentloaded'))
                    def authenticate():
                        page.locator('#pin').fill(PIN)
                        page.locator('#connect').click()
                        expect(page.locator('#board>.widget')).to_have_count(count)
                    measure('authenticateAndDashboardMs',authenticate)
                    def update():
                        signal(page,url,55+repeat)
                        expect(page.locator('#board .w-health').first).to_contain_text(str(55+repeat))
                    measure('gsiHttpToWidgetMs',update)
                    def enter():
                        page.locator('[data-section="studio"]').click()
                        expect(page.locator('#studio-board>.widget')).to_have_count(count)
                    measure('openStudioMs',enter)
                    last=page.locator('#studio-board>.widget').last
                    measure('selectWidgetMs',lambda:last.click(position={'x':15,'y':15}))
                    def geometry(kind):
                        handle=last.locator('[data-studio-gesture="'+kind+'"]')
                        field=page.locator('#studio-y' if kind=='move' else '#studio-height')
                        expected=int(field.input_value())+1
                        handle.press('ArrowDown')
                        expect(field).to_have_value(str(expected))
                        expect(page.locator('#studio-save-state')).to_contain_text('Draft kept locally')
                    measure('keyboardMoveAndLocalSaveMs',lambda:geometry('move'))
                    measure('keyboardResizeAndLocalSaveMs',lambda:geometry('resize'))
                    variant='minimal' if page.locator('#studio-variant').input_value()!='minimal' else 'standard'
                    def variant_and_save():
                        page.select_option('#studio-variant',variant)
                        expect(page.locator('#studio-save-state')).to_contain_text('Draft kept locally')
                    measure('variantAndConfirmedLocalSaveMs',variant_and_save)
                    def publish():
                        page.locator('#studio-publish').click()
                        expect(page.locator('#studio-save-state')).to_contain_text('Published version up to date')
                    measure('confirmedPublicationMs',publish)
                    page.locator('.studio-brand').click()
                    expect(page.locator('#studio-app')).to_be_hidden()
                    def select_profile():
                        page.select_option('#dashboard-profile-menu','p-other')
                        expect(page.locator('#dashboard-title')).to_contain_text('Other measured profile')
                    measure('profileSelectionMs',select_profile)
                    for width,height in [(1366,768),(390,844),(1920,1080)]:
                        def reflow():
                            page.set_viewport_size({'width':width,'height':height})
                            page.evaluate('() => new Promise(resolve => requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
                        measure('reflow-'+str(width)+'Ms',reflow)
                    samples.append({'operation':'footprint','widgets':count,'repeat':repeat,**memory(context,page)})
                finally:
                    context.close()
    return samples


def soak(browser,seconds,output):
    start=time.monotonic()
    snapshots=[]
    with production(document(60)) as (url,data,_initial,_restart):
        context=browser.new_context(viewport={'width':1366,'height':900},reduced_motion='reduce')
        try:
            context.add_init_script('''(() => {
              window.p10Writes={};
              const original=IDBObjectStore.prototype.put;
              IDBObjectStore.prototype.put=function(...args){
                window.p10Writes[this.name]=(window.p10Writes[this.name]||0)+1;
                return original.apply(this,args);
              };
            })();''')
            page=context.new_page()
            faults=[]
            sockets=[]
            page.on('pageerror',lambda error:faults.append(str(error)))
            page.on('websocket',lambda socket:sockets.append(socket.url))
            login(page,url)
            page.locator('[data-section="studio"]').click()
            expect(page.locator('#studio-board>.widget')).to_have_count(60)
            page.locator('.studio-brand').click()
            expect(page.locator('#studio-app')).to_be_hidden()
            page.evaluate('window.p10Card=document.querySelector("#board>.widget")')
            original=(data/'profiles.json').read_bytes()
            snapshots.append({'elapsedSeconds':round(time.monotonic()-start,2),**memory(context,page)})
            ticks=0
            nextSnapshot=time.monotonic()+300
            while time.monotonic()-start<seconds:
                signal(page,url,70+ticks%10)
                expect(page.locator('#board .w-health').first).to_contain_text(str(70+ticks%10))
                if ticks%30==0:
                    page.locator('[data-section="studio"]').click()
                    expect(page.locator('#studio-board>.widget')).to_have_count(60)
                    page.locator('.studio-brand').click()
                    expect(page.locator('#studio-app')).to_be_hidden()
                assert page.evaluate('window.p10Card===document.querySelector("#board>.widget")')
                assert len(sockets)==1 and not faults,(sockets,faults)
                ticks+=1
                if time.monotonic()>=nextSnapshot:
                    snapshots.append({'elapsedSeconds':round(time.monotonic()-start,2),**memory(context,page)})
                    nextSnapshot+=300
                progress={'elapsedSeconds':round(time.monotonic()-start,2),'ticks':ticks,'sockets':len(sockets),'faults':faults,'snapshots':snapshots}
                output.with_suffix('.progress.json').write_text(json.dumps(progress,indent=2),encoding='utf-8')
                page.wait_for_timeout(900)
            snapshots.append({'elapsedSeconds':round(time.monotonic()-start,2),**memory(context,page)})
            writes=page.evaluate('window.p10Writes')
            assert not writes.get('drafts') and not writes.get('publications'),writes
            assert (data/'profiles.json').read_bytes()==original
            if 'documentListeners' in snapshots[0]:
                assert snapshots[-1]['documentListeners']==snapshots[0]['documentListeners']
            return {'elapsedSeconds':round(time.monotonic()-start,2),'ticks':ticks,'sockets':len(sockets),
                'faults':faults,'writes':writes,'snapshots':snapshots,'publishedFileUnchanged':True,'dashboardCardRetained':True}
        finally:
            context.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser',choices=['chromium','firefox','webkit'],default='chromium')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--repeats',type=int,default=3)
    parser.add_argument('--soak-seconds',type=int,default=0)
    parser.add_argument('--soak-only',action='store_true')
    args=parser.parse_args()
    if not 1<=args.repeats<=10 or not 0<=args.soak_seconds<=7200:parser.error('Use 1–10 repeats and 0–7200 soak seconds')
    if args.soak_only and not args.soak_seconds:parser.error('--soak-only requires a positive --soak-seconds duration')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as playwright:
        browser=getattr(playwright,args.browser).launch(**options(args.browser))
        try:
            report={'os':platform.platform(),'python':platform.python_version(),'browser':browser.version,
                'method':'End-to-end wall time including automation and waits. Fresh fixture per repetition. Move/resize timings use keyboard controls; pointer functionality is covered separately, pointer timing is not collected. Heap samples are post-GC Chromium only; no arbitrary timing or heap gate.',
                'samples':[] if args.soak_only else timings(browser,args.repeats)}
            grouped={}
            for sample in report['samples']:
                if 'ms' in sample:grouped.setdefault(sample['operation']+'/'+str(sample['widgets']),[]).append(sample['ms'])
            report['mediansMs']={key:round(statistics.median(values),3) for key,values in grouped.items()}
            if args.soak_seconds:report['soak']=soak(browser,args.soak_seconds,args.output)
            args.output.write_text(json.dumps(report,indent=2),encoding='utf-8')
        finally:
            browser.close()
    print('PASS: production composition measurements; bounded soak only when explicitly requested',flush=True)
