"""Optional comparable legacy-board measurements, with fresh synthetic browser contexts."""
from __future__ import annotations
import argparse
import copy
import json
import os
from pathlib import Path
import statistics
import time
from playwright.sync_api import expect,sync_playwright
from test_live_browser import start_server
from test_widget_characterization import LIVE,open_fixture,settle,measure_click


def run(browserName,output,repeats):
    runtime,process,url=start_server()
    results=[]
    try:
        with sync_playwright() as playwright:
            options={'headless':True}
            if browserName=='chromium' and os.environ.get('CS2_CHROMIUM_BIN'):
                options.update(executable_path=os.environ['CS2_CHROMIUM_BIN'],args=['--no-sandbox'])
            browser=getattr(playwright,browserName).launch(**options)
            for count in [29,60]:
                renders=[];updates=[];nodes=[];identities=[]
                for _ in range(repeats):
                    context=browser.new_context(viewport={'width':1280,'height':900},locale='en-US',timezone_id='UTC')
                    page,fixture,faults=open_fixture(context,url,count)
                    page.bring_to_front()
                    page.locator('#tab-default').click()
                    renders.append(measure_click(page,'#tab-custom'))
                    settle(page)
                    nodes.append(page.locator('#board *').count())
                    page.evaluate('window.measuredCard=document.querySelector("#board").firstElementChild;window.measuredItem=document.querySelector(".w-inventory .item")')
                    for index in range(10):
                        sample=copy.deepcopy(LIVE)
                        sample['player']['health']=70+index
                        started=time.perf_counter()
                        fixture.send_state(sample)
                        expect(page.locator('.w-health [data-v="health"]').first).to_have_text(str(70+index))
                        updates.append((time.perf_counter()-started)*1000)
                    identities.append(page.evaluate('({card:measuredCard===document.querySelector("#board").firstElementChild,list:measuredItem===document.querySelector(".w-inventory .item")})'))
                    assert not faults,faults
                    context.close()
                results.append({'widgets':count,'renderMs':renders,'updateMs':updates,'domNodes':nodes,
                                'identities':identities,'medianRenderMs':statistics.median(renders),
                                'medianUpdateMs':statistics.median(updates)})
            result={'browser':browser.version,'viewport':[1280,900],'repeats':repeats,'foreground':True,
                    'method':'render click plus forced layout; updates include Playwright and synthetic WS dispatch','results':results}
            output.parent.mkdir(parents=True,exist_ok=True)
            output.write_text(json.dumps(result,indent=2),encoding='utf8')
            print(json.dumps(result))
            browser.close()
    finally:
        process.terminate();process.wait(timeout=10);runtime.cleanup()


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--browser',choices=['chromium','firefox','webkit'],default='chromium')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--repeats',type=int,default=5)
    args=parser.parse_args()
    if args.repeats<1: parser.error('--repeats must be positive')
    run(args.browser,args.output,args.repeats)
