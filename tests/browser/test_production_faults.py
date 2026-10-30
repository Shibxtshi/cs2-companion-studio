"""Production authentication, lost replies and reviewed import failure paths."""
import argparse
import copy
import json
import os
import re
from pathlib import Path

from playwright.sync_api import expect, sync_playwright
from test_production_studio import production, login, PIN
from test_production_acceptance import field, saved, name_profile, publish
from test_production_resilience import options, read_drafts
from companion.profile_activation import target_document


def connection_feedback(browser):
    with production() as (url,_data,_initial,_restart):
        context=browser.new_context()
        try:
            page=context.new_page()
            page.goto(url)
            page.locator('#pin').fill('incorrect-synthetic-pin')
            page.locator('#connect').click()
            expect(page.locator('#pin')).to_have_attribute('aria-invalid','true')
            page.locator('#pin').fill(PIN)
            page.locator('#connect').click()
            expect(page.locator('#view')).to_be_visible()
            expect(page.locator('#pin')).not_to_have_attribute('aria-invalid','true')
            page.once('dialog',lambda dialog:dialog.accept())
            page.locator('#logout').click()
            expect(page.locator('#view')).to_be_hidden()
            expect(page.locator('#pin')).not_to_have_attribute('aria-invalid','true')
            page.route('**/health',lambda route:route.fulfill(json={'service':'ok','version':'future-synthetic-version'}))
            page.locator('#pin').fill(PIN)
            page.locator('#connect').click()
            expect(page.locator('#loginerror')).to_contain_text('versions differ')
            expect(page.locator('#view')).to_be_hidden()
        finally:
            context.close()
    print('PASS: native authentication feedback resets invalid state and distinguishes incompatible server version',flush=True)


def game_freshness(browser):
    initial=target_document()
    root=Path(__file__).resolve().parents[2]
    corpus=json.loads((root/'tests/browser/fixtures/draft-contracts.json').read_text('utf-8'))
    widget=copy.deepcopy(corpus['profile']['configuration']['layout']['widgets'][0])
    widget.update(id='p10-health',kind='health',x=0,y=0,width=8,height=6,variant='standard')
    initial['profiles'][0]['configuration']['layout']['widgets']=[widget]
    with production(initial) as (url,data,_initial,_restart):
        context=browser.new_context()
        try:
            page=context.new_page()
            states=[]
            def observe(socket):
                def received(frame):
                    value=json.loads(frame)
                    if value.get('type')=='state':states.append(value)
                socket.on('framereceived',received)
            page.on('websocket',observe)
            login(page,url)
            original=(data/'profiles.json').read_bytes()
            def gsi(payload):
                response=page.request.post(url+'/gsi',data={'auth':{'token':'synthetic-production-gsi'},**payload})
                assert response.status==200
            gsi({'provider':{'name':'Synthetic CS2'},'player':{'name':'Synthetic menu','activity':'menu'}})
            expect(page.locator('#status')).to_contain_text('GSI active')
            gsi({'map':{'name':'de_synthetic','phase':'live','round':1},'round':{'phase':'live'},
                 'player':{'state':{'health':0,'armor':0,'money':0}}})
            expect(page.locator('#board .w-health')).to_contain_text('0')
            page.evaluate('window.p10RetainedCard=document.querySelector("#board>.widget")')
            gsi({'player':{'state':{'health':55}}})
            expect(page.locator('#board .w-health')).to_contain_text('55')
            expect(page.locator('#board .w-health')).not_to_contain_text('55',timeout=26000)
            expect(page.locator('#board .w-health')).to_have_attribute('data-data-state','stale')
            expect(page.locator('#board .w-health')).to_contain_text(re.compile('offline',re.I))
            gsi({'player':{'name':'Synthetic identity only','activity':'menu'}})
            expect(page.locator('#status')).to_contain_text('GSI active')
            expect(page.locator('#board .w-health')).not_to_contain_text('55')
            gsi({'player':{'state':{'health':41}}})
            expect(page.locator('#board .w-health')).to_contain_text('41')
            assert page.evaluate('window.p10RetainedCard===document.querySelector("#board>.widget")')
            assert states and all(not state['bomb_timer']['enabled'] for state in states)
            assert (data/'profiles.json').read_bytes()==original
        finally:
            context.close()
    print('PASS: native identity-only GSI, zero/missing/stale/live values, 20-second expiry, resumed data, retained DOM and default-disabled bomb timer',flush=True)


def authentication(browser):
    with production() as (url,data,_initial,_restart):
        context=browser.new_context()
        try:
            page=context.new_page()
            page.goto(url)
            page.locator('.topbar [data-dashboard-home]').dispatch_event('click')
            expect(page.locator('#view')).to_be_hidden()
            original=(data/'profiles.json').read_bytes()
            (data/'profile-reset-backups').mkdir()
            (data/'profile-reset-backups/synthetic-private.txt').write_text('synthetic private backup',encoding='utf-8')
            for path in ['/data/profiles.json','/.env','/profile-reset-backups/synthetic-private.txt',
                         '/__studio_test__','/__dashboard_test__','/__publication_test__']:
                assert page.request.get(url+path).status==404,path
            for attempt in range(5):
                tab=context.new_page()
                tab.goto(url)
                tab.locator('#pin').fill('incorrect-synthetic-pin')
                tab.locator('#connect').click()
                expect(tab.locator('#loginerror')).to_contain_text('Incorrect PIN')
                expect(tab.locator('#view')).to_be_hidden()
                tab.close()
            page.locator('#pin').fill(PIN)
            page.locator('#connect').click()
            expect(page.locator('#loginerror')).to_contain_text('temporarily limited')
            expect(page.locator('#view')).to_be_hidden()
            assert (data/'profiles.json').read_bytes()==original
            page.locator('#demo').click()
            expect(page.locator('#view')).to_be_visible()
            expect(page.locator('#dashboard-profile-menu option')).to_have_count(0)
            expect(page.locator('[data-section="studio"]')).to_be_disabled()
        finally:
            context.close()
    print('PASS: native PIN rejection and default throttling, unauthenticated logo, demo and private/test route isolation',flush=True)


def lost_acknowledgement(browser,restartOnAck=False,output=None):
    with production() as (url,data,_initial,restart):
        context=browser.new_context(viewport={'width':1366,'height':900})
        page=context.new_page()
        messages={'hold':False,'queued':[],'operations':[],'authentications':0,'links':[]}
        faults=[]
        page.on('pageerror',lambda error:faults.append(str(error)))
        def intercept(socket):
            server=socket.connect_to_server()
            messages['links'].append((socket,server))
            def inbound(raw):
                value=json.loads(raw)
                if messages['hold'] and value.get('type') in ['profile_operation_ack','profiles_catalog']:
                    messages['queued'].append(value)
                    return
                socket.send(raw)
            def outbound(raw):
                value=json.loads(raw)
                if value.get('type')=='profile_operation':
                    messages['operations'].append(value['operation']['operationId'])
                if value.get('type')=='auth':
                    messages['authentications']+=1
                server.send(raw)
            server.on_message(inbound)
            socket.on_message(outbound)
        page.route_web_socket('**/ws',intercept)
        try:
            login(page,url)
            selectedId=page.locator('#dashboard-profile-menu').input_value()
            page.locator('[data-section="studio"]').click()
            page.locator('.studio-library-item[data-kind="health"] button').click()
            saved(page)
            messages['hold']=True
            page.locator('#studio-publish').evaluate('node=>{node.click();node.click();}')
            for _ in range(50):
                if any(value['type']=='profile_operation_ack' for value in messages['queued']):break
                page.wait_for_timeout(100)
            assert any(value['type']=='profile_operation_ack' for value in messages['queued'])
            expect(page.locator('#studio-title')).to_be_disabled()
            expect(page.locator('#studio-save-state')).not_to_contain_text('Published version up to date')
            if output:
                output.mkdir(parents=True,exist_ok=True)
                page.screenshot(path=str(output/('publishing-before-'+('restart' if restartOnAck else 'reply-loss')+'.png')))
            messages['hold']=False
            socket,server=messages['links'][-1]
            socket.close(code=1011,reason='Synthetic P10 reply lost')
            server.close(code=1011,reason='Synthetic P10 transport interruption')
            if restartOnAck:restart()
            # Recovery may reconcile automatically, but must use the same persisted operation.
            for _ in range(150):
                if page.locator('#studio-save-state').inner_text()=='Published version up to date':
                    break
                if page.locator('#studio-retry').is_visible() and messages['authentications']>=2:
                    page.locator('#studio-retry').click()
                page.wait_for_timeout(100)
            expect(page.locator('#studio-save-state')).to_contain_text('Published version up to date')
            document=json.loads((data/'profiles.json').read_bytes())
            profile=next(profile for profile in document['profiles'] if profile['id']==selectedId)
            assert profile['revision']==2 and document['catalogRevision']==2
            assert len(document['receipts'])==1
            assert messages['operations'] and len(set(messages['operations']))==1
            assert not read_drafts(page)['publications']
            assert not faults,faults
        finally:
            context.close()
    print('PASS: native double click, locked in-flight editing, committed reply loss, '+('actual server restart, ' if restartOnAck else '')+'reconnect/retry, one operation ID and one revision increment',flush=True)


def transfer(browser):
    root=Path(__file__).resolve().parents[2]
    corpus=json.loads((root/'tests/browser/fixtures/draft-contracts.json').read_text('utf-8'))
    configuration=copy.deepcopy(corpus['profile']['configuration'])
    exported={'format':'ccs-dashboard-export','version':1,'name':'P10 imported profile','configuration':configuration}
    with production() as (url,data,_initial,_restart):
        context=browser.new_context(viewport={'width':1366,'height':900})
        try:
            page=context.new_page()
            login(page,url)
            page.locator('[data-section="studio"]').click()
            expect(page.locator('#studio-app')).to_be_visible()
            original=(data/'profiles.json').read_bytes()
            page.locator('#production-import-file').set_input_files({'name':'profile.json','mimeType':'application/json','buffer':json.dumps(exported).encode()})
            with page.expect_popup() as opening:
                page.locator('#studio-dialog button[value="preview"]').click()
            preview=opening.value
            expect(preview.locator('#board>.widget')).to_have_count(len(configuration['layout']['widgets']))
            preview.close()
            assert (data/'profiles.json').read_bytes()==original
            page.locator('#studio-dialog button[value="create"]').click()
            name_profile(page,'P10 imported profile')
            saved(page)
            assert (data/'profiles.json').read_bytes()==original
            publish(page)
            imported=next(profile for profile in json.loads((data/'profiles.json').read_bytes())['profiles'] if profile['name']=='P10 imported profile')
            assert imported['configuration']==configuration
        finally:
            context.close()
    invalid=[b'{',json.dumps({**exported,'version':999}).encode(),
             json.dumps({**exported,'format':'cs2-companion-layout'}).encode(),
             b' '*70001,json.dumps({**exported,'pin':'synthetic-disallowed-field'}).encode()]
    for raw in invalid:
        with production() as (url,data,_initial,_restart):
            context=browser.new_context()
            try:
                page=context.new_page()
                login(page,url)
                page.locator('[data-section="studio"]').click()
                expect(page.locator('#studio-app')).to_be_visible()
                original=(data/'profiles.json').read_bytes()
                page.locator('#production-import-file').set_input_files({'name':'invalid.json','mimeType':'application/json','buffer':raw})
                expect(page.locator('#studio-alert')).to_be_visible()
                expect(page.locator('#studio-dialog')).to_be_hidden()
                assert (data/'profiles.json').read_bytes()==original
            finally:
                context.close()
    print('PASS: native import preview, local creation then explicit publication; malformed/future/legacy/oversized/secret-bearing documents rejected',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser',choices=['chromium','firefox','webkit'],default='chromium')
    parser.add_argument('--group',choices=['all','feedback','states','auth','reply','transfer'],default='all')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    with sync_playwright() as playwright:
        browser=getattr(playwright,args.browser).launch(**options(args.browser))
        try:
            if args.group in ['all','feedback']:connection_feedback(browser)
            if args.group in ['all','states']:game_freshness(browser)
            if args.group in ['all','auth']:authentication(browser)
            if args.group in ['all','reply']:
                lost_acknowledgement(browser,output=args.output)
                lost_acknowledgement(browser,restartOnAck=True,output=args.output)
            if args.group in ['all','transfer']:transfer(browser)
        finally:
            browser.close()
