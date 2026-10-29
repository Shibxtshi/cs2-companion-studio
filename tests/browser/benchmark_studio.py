"""Optional real-clock Studio measurements. Synthetic only; no timing acceptance threshold."""
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
from test_profile_publication import PIN, launch, stop
from test_widget_characterization import KINDS, LIVE, settle
from companion.profile_contracts import encode_document


def run(output, repeats):
    source=document()
    template=source['profiles'][0]
    base=template['configuration']['layout']['widgets'][0]
    source['profiles']=[]
    for count in [29,60]:
        profile=copy.deepcopy(template)
        profile.update(id='p-'+str(count),name='Measured '+str(count))
        profile['configuration']['layout']['widgets']=[
            {**base,'id':'w-'+str(i),'kind':KINDS[i%29],'variant':'standard',
             'x':i%3*8,'y':i//3*9,'width':8,'height':8} for i in range(count)]
        source['profiles'].append(profile)
    samples=[]
    with tempfile.TemporaryDirectory(prefix='ccs-studio-benchmark-') as temporary:
        runtime=Path(temporary)
        (runtime/'.synthetic-publication-test').touch()
        target=runtime/'target/profiles.json'
        target.parent.mkdir(); target.write_bytes(encode_document(source))
        with socket.socket() as listener:
            listener.bind(('127.0.0.1',0));port=listener.getsockname()[1]
        process,url=launch(runtime,port)
        try:
            with sync_playwright() as pw:
                options={'headless':True}
                if os.environ.get('CS2_CHROMIUM_BIN'):
                    options.update(executable_path=os.environ['CS2_CHROMIUM_BIN'],args=['--no-sandbox'])
                browser=pw.chromium.launch(**options)
                for repeat in range(repeats):
                    context=browser.new_context(viewport={'width':1920,'height':1080},locale='en-US',timezone_id='UTC',reduced_motion='reduce')
                    context.add_init_script("""(() => {
                      window.studioWriteTimes=[];
                      const original=IDBObjectStore.prototype.put;
                      IDBObjectStore.prototype.put=function(...args){
                        const start=performance.now();const result=original.apply(this,args);
                        const name=this.name;
                        this.transaction.addEventListener('complete',()=>studioWriteTimes.push({store:name,putToCompleteMs:performance.now()-start}),{once:true});
                        return result;
                      };
                    })();""")
                    page=context.new_page()
                    page.bring_to_front()
                    start=time.perf_counter()
                    page.goto(url+'/__studio_test__')
                    page.locator('#pin').fill(PIN);page.locator('#connect').click()
                    expect(page.locator('#studio-board .widget')).to_have_count(29)
                    page.evaluate('document.fonts.ready')
                    samples.append({'operation':'openStudio29IncludingAuthAutomation','repeat':repeat,'ms':(time.perf_counter()-start)*1000})
                    for count in [29,60]:
                        if count==60:
                            start=time.perf_counter()
                            page.select_option('#studio-profile','p-60')
                            expect(page.locator('#studio-board .widget')).to_have_count(60)
                            samples.append({'operation':'open60IncludingAutomation','repeat':repeat,'ms':(time.perf_counter()-start)*1000})
                        page.evaluate('state=>CCSStudioTarget.previewData(state,true)',LIVE)
                        ui=page.evaluate("""() => {
                          const samples=[];const board=document.getElementById('studio-board');
                          const measure=(operation,action)=>{const start=performance.now();action();board.getBoundingClientRect();samples.push({operation,ms:performance.now()-start});};
                          for(let i=0;i<5;i++)measure('select',()=>board.children[i].click());
                          for(let i=0;i<5;i++)measure('inspector',()=>document.getElementById(i%2?'studio-widget-tab':'studio-profile-tab').click());
                          document.getElementById('studio-widget-tab').click();board.firstElementChild.click();
                          const variant=document.getElementById('studio-variant');variant.value='compact';variant.dispatchEvent(new Event('change'));
                          for(const value of ['minimal','standard','compact','minimal','standard'])measure('variant',()=>{variant.value=value;variant.dispatchEvent(new Event('change'));});
                          document.getElementById('studio-profile-tab').click();
                          const theme=document.getElementById('studio-theme');
                          for(const value of ['competitive-red','performance-green','creator-purple','tactical-blue']){
                            measure('theme',()=>{theme.value=value;theme.dispatchEvent(new Event('change'));});
                          }
                          for(let i=0;i<5;i++){measure('undo',()=>document.getElementById('studio-undo').click());measure('redo',()=>document.getElementById('studio-redo').click());}
                          document.getElementById('studio-widget-tab').click();
                          return samples;
                        }""")
                        samples.extend({**sample,'widgets':count,'repeat':repeat} for sample in ui)
                        for operation in ['move','resize']:
                            for _ in range(3):
                                handle=page.locator('#studio-board .widget').last.locator('[data-studio-gesture="'+operation+'"]')
                                handle.evaluate('node=>node.scrollIntoView({block:"center"})')
                                box=handle.bounding_box()
                                start=time.perf_counter()
                                page.mouse.move(box['x']+box['width']/2,box['y']+box['height']/2)
                                page.mouse.down()
                                page.mouse.move(box['x']+box['width']/2,box['y']+box['height']/2+40,steps=5)
                                page.mouse.up()
                                samples.append({'operation':operation+'IncludingAutomation','widgets':count,'repeat':repeat,'ms':(time.perf_counter()-start)*1000})
                        start=time.perf_counter()
                        page.wait_for_function("()=>CCSStudioTarget.snapshot().state?.status==='saved'")
                        samples.append({'operation':'awaitLocalSaveIncludingDebounce','widgets':count,'repeat':repeat,'ms':(time.perf_counter()-start)*1000})
                        state=page.evaluate('CCSStudioTarget.snapshot().state')
                        cdp=context.new_cdp_session(page)
                        cdp.send('HeapProfiler.collectGarbage')
                        heap=cdp.send('Runtime.getHeapUsage')
                        cdp.detach()
                        samples.append({'operation':'footprint','widgets':count,'repeat':repeat,
                            'boardNodes':page.locator('#studio-board *').count(),'heapUsedBytes':heap['usedSize'],
                            'historySerializedBytes':state['history']['bytes']})
                        samples.extend({'operation':'nativeIDBPutToTransactionComplete','widgets':count,'repeat':repeat,**sample}
                                       for sample in page.evaluate('window.studioWriteTimes'))
                        page.evaluate('window.studioWriteTimes=[]')
                        start=time.perf_counter()
                        page.reload();page.locator('#pin').fill(PIN);page.locator('#connect').click()
                        page.locator('#studio-dialog button[value="resume"]').click()
                        page.wait_for_function("()=>CCSStudioTarget.snapshot().state?.status==='saved'")
                        samples.append({'operation':'restoreIncludingReloadAuthAutomation','widgets':count,'repeat':repeat,'ms':(time.perf_counter()-start)*1000})
                        start=time.perf_counter()
                        page.locator('#studio-publish').click()
                        page.wait_for_function("()=>CCSStudioTarget.snapshot().publication?.code==='published' && CCSStudioTarget.snapshot().state?.status==='pristine'")
                        samples.append({'operation':'publishIncludingCatalogAutomation','widgets':count,'repeat':repeat,'ms':(time.perf_counter()-start)*1000})
                        for width,height in [(1366,768),(390,844),(1920,1080)]:
                            start=time.perf_counter();page.set_viewport_size({'width':width,'height':height});settle(page)
                            samples.append({'operation':'reflowIncludingAutomationTwoFrames','width':width,'widgets':count,'repeat':repeat,'ms':(time.perf_counter()-start)*1000})
                        samples.extend({'operation':'nativeIDBPutToTransactionComplete','widgets':count,'repeat':repeat,**sample}
                                       for sample in page.evaluate('window.studioWriteTimes'))
                    context.close()
                output.parent.mkdir(parents=True,exist_ok=True)
                output.write_text(json.dumps({'browser':browser.version,'viewport':[1920,1080],'repeats':repeats,
                    'foreground':True,'method':'native clocks; labelled automation/debounce costs; post-GC Chromium heap, not a memory ceiling',
                    'samples':samples},indent=2),encoding='utf8')
                browser.close()
                print('OK: reproducible Studio 29/60 timings, native transactions, history/DOM/heap samples; no timing gate')
        finally:
            stop(process)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--repeats',type=int,default=5)
    args=parser.parse_args()
    if not 1<=args.repeats<=20: parser.error('repeats must be between 1 and 20')
    run(args.output,args.repeats)
