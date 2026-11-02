"""P7 full-catalog visual review with synthetic data and real renderer components."""
from __future__ import annotations
import argparse
import base64
import html as html_module
import re
import copy
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import URLError
from urllib.request import urlopen

from playwright.sync_api import expect, sync_playwright
from test_live_browser import ROOT
from test_profile_publication import stop
from widget_fixtures import LIVE, EMPTY, KINDS, settle

VARIANTS = ['standard','compact','minimal']


def write_gallery(output, html, corpus):
    """Bundle only synthetic gallery resources; no server credentials/runtime paths are read."""
    sheets=[]
    for name in ('tokens','themes','styles','widget-presentation'):
        sheets.append((ROOT/'static/css'/f'{name}.css').read_text('utf-8'))
    sheets.append((ROOT/'tests/browser/widget-preview.css').read_text('utf-8'))
    css='\n'.join(sheets)
    for font in (ROOT/'static/fonts').glob('*.woff2'):
        css=css.replace("../fonts/"+font.name,'data:font/woff2;base64,'+base64.b64encode(font.read_bytes()).decode())
    mark=base64.b64encode((ROOT/'static/branding/repere.svg').read_bytes()).decode()
    css=css.replace('../branding/repere.svg','data:image/svg+xml;base64,'+mark)
    html=re.sub(r'<link[^>]+rel="stylesheet"[^>]*>','',html)
    html=re.sub(r'<script[^>]*></script>','',html)
    html=html.replace('</head>','<style>'+css+'</style></head>')
    scripts=[(ROOT/'static/js'/f'{name}.js').read_text('utf-8') for name in
             ('widgets','display-format','i18n','theme-preview','widget-presentation','widget-renderer')]
    scripts.append((ROOT/'tests/browser/widget-preview.js').read_text('utf-8'))
    initialization='CS2I18N.setLocale("FR");widgetPreview.setCorpus('+json.dumps(corpus,ensure_ascii=False)+');'
    scripts.append(initialization)
    html=html.replace('</body>',''.join('<script>'+source.replace('</script',r'</script')+'</script>' for source in scripts)+'</body>')
    notices='\n\n'.join((ROOT/'static/fonts'/name).read_text('utf-8') for name in ('inter-OFL.txt','barlow-condensed-OFL.txt'))
    html=html.replace('</body>','<details><summary>Font licenses</summary><pre>'+html_module.escape(notices)+'</pre></details></body>')
    (output/'CCS-P7-GALLERY.html').write_text(html,encoding='utf8')


def launch(runtime):
    (runtime / '.synthetic-widget-preview').touch()
    with socket.socket() as listener:
        listener.bind(('127.0.0.1',0))
        port=listener.getsockname()[1]
    env=dict(os.environ,GSI_TOKEN='synthetic-widget-preview-gsi',DASHBOARD_PIN='synthetic-widget-preview-pin',
             PROFILE_DATA_DIR=str(runtime/'data'),DIAGNOSTICS_DIR=str(runtime/'logs'),BOMB_TIMER_ENABLED='false')
    process=subprocess.Popen([sys.executable,str(ROOT/'tests/browser/widget_preview_server.py'),str(runtime),str(port)],
                             cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    url=f'http://127.0.0.1:{port}'
    for _ in range(100):
        if process.poll() is not None:
            raise RuntimeError(process.stderr.read().decode()[:1200])
        try:
            with urlopen(url+'/health',timeout=.3):
                return process,url
        except (URLError,OSError):
            time.sleep(.1)
    process.terminate()
    raise RuntimeError('Synthetic widget preview did not start')


def run(browserName,output):
    with tempfile.TemporaryDirectory(prefix='ccs-widget-preview-') as temporary:
        process,url=launch(Path(temporary))
        try:
            with sync_playwright() as playwright:
                options={'headless':True}
                if browserName=='chromium' and os.environ.get('CS2_CHROMIUM_BIN'):
                    options.update(executable_path=os.environ['CS2_CHROMIUM_BIN'],args=['--no-sandbox'])
                browser=getattr(playwright,browserName).launch(**options)
                context=browser.new_context(viewport={'width':1280,'height':1000},locale='fr-FR',timezone_id='UTC',
                                            reduced_motion='reduce')
                page=context.new_page()
                faults=[]
                page.on('pageerror',lambda error:faults.append(str(error)))
                response=page.goto(url+'/__widget_preview__')
                original_html=response.text()
                page.wait_for_function('window.widgetPreview !== undefined')
                page.evaluate("CS2I18N.setLocale('FR');performance.now=()=>1000")
                page.evaluate('document.fonts.ready')
                state=copy.deepcopy(LIVE)
                state['economy']['source']='history'
                state['bomb_state']='planted'
                state['bomb_timer']={'enabled':True,'status':'active','remaining':9,'duration':40}
                state['player']['weapons'] += [
                    {'name':'weapon_usp_silencer','type':'Pistol','state':'holstered','ammo_clip':12},
                    {'name':'weapon_flashbang','type':'Grenade','state':'holstered'}]
                page.evaluate('state=>widgetPreview.render(state,true)',state)
                settle(page)
                initial=page.evaluate('JSON.stringify(widgetPreview.configuration())')
                assert page.locator('.presented-widget').count()==87
                assert page.get_by_role('heading',level=4).count()==87
                for kind in KINDS:
                    cards=page.locator('[data-preview-kind="'+kind+'"] .widget')
                    values=cards.evaluate_all('(cards)=>cards.map(card=>Object.fromEntries([...card.querySelectorAll("[data-v]")].map(n=>[n.dataset.v,n.textContent])))')
                    assert values[0]==values[1]==values[2],kind
                for variant in ['standard','compact','minimal']:
                    bomb=page.locator('.w-bomb[data-variant="'+variant+'"]')
                    expect(bomb.locator('.pill')).to_contain_text('estimé')
                    expect(bomb.locator('[data-bomb-msg]')).to_be_visible()
                    expect(bomb.locator('[data-bomb-msg]')).to_contain_text('Kit')
                    expect(page.locator('.w-economy[data-variant="'+variant+'"] [data-v="econ_note"]')).to_be_visible()
                scenarios=page.locator('.w-bomb[data-variant="minimal"] .bomb-demo-options')
                scenarios.locator('summary').click()
                scenarios.locator('[data-demo="4"]').click()
                expect(page.locator('.w-bomb[data-variant="minimal"] [data-bomb-msg]')).to_contain_text('Trop tard')
                scenarios.locator('[data-demo="9"]').click()
                scenarios.locator('summary').click()
                details=page.locator('.w-inventory[data-variant="minimal"] .widget-more')
                details.locator('summary').focus()
                page.keyboard.press('Enter')
                expect(details).to_have_attribute('open','')
                expect(details.locator('[data-list="weapons"]')).to_be_visible()
                page.keyboard.press('Enter')
                page.evaluate("widgetPreview.setVariant('score','minimal','standard')")
                expect(page.locator('[data-id="preview-score-minimal"]')).to_have_attribute('data-variant','standard')
                page.evaluate("widgetPreview.setVariant('score','minimal','minimal')")
                assert page.evaluate('JSON.stringify(widgetPreview.configuration())')==initial
                page.evaluate('document.activeElement.blur()')
                if output:
                    output.mkdir(parents=True,exist_ok=True)
                    for kind in KINDS:
                        page.locator('[data-preview-kind="'+kind+'"]').screenshot(path=str(output/(kind+'-wide.png')))
                    page.screenshot(path=str(output/'overview-wide.png'),full_page=True)
                for width,height in [(1920,1080),(1366,768),(1280,900),(1024,768),(768,1024),(390,844),(320,740)]:
                    page.set_viewport_size({'width':width,'height':height})
                    settle(page)
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),width
                    if output:
                        for kind in KINDS:
                            page.locator('[data-preview-kind="'+kind+'"]').screenshot(path=str(output/(kind+'-'+str(width)+'.png')))
                variants=page.evaluate('widgetPreview.variants()')
                for variant in VARIANTS:
                    for kind in KINDS:
                        page.evaluate('([kind,variant])=>widgetPreview.setVariant(kind,variant,"standard")',[kind,variant])
                        page.evaluate('([kind,variant])=>widgetPreview.setVariant(kind,variant,variant)',[kind,variant])
                assert page.evaluate('widgetPreview.variants()')==variants
                complete=copy.deepcopy(state)
                partial=copy.deepcopy(state)
                partial['player']={'health':None,'armor':0,'money':0,'weapons':[]}
                zero=copy.deepcopy(state)
                for key,value in zero['player'].items():
                    if isinstance(value,(int,float)) and not isinstance(value,bool):
                        zero['player'][key]=0
                stale=copy.deepcopy(EMPTY)
                stale['age_seconds']=20
                waiting=copy.deepcopy(EMPTY)
                waiting['gsi_connected']=True
                long=copy.deepcopy(state)
                long['player']['name']='Carte'
                long['player']['weapon']='weapon_very_long_synthetic_weapon_name_for_layout'
                long['player']['weapons'][0]['name']=long['player']['weapon']
                long['events']=[{'message':'Synthetic long event '+('x'*80),'at':1700000000,'category':'round'} for _ in range(8)]
                for key in ('kills','assists','deaths','money','equip_value','score','round_totaldmg'):
                    long['player'][key]=123456789
                corpus=[('normal',complete,False),('partial',partial,False),('missing',EMPTY,False),
                        ('zero',zero,False),('stale',stale,False),('waiting',waiting,False),('long',long,False),('demo',state,True)]
                if output:
                    write_gallery(output,original_html,{name:{'state':sample,'demo':mode} for name,sample,mode in corpus})
                    previous_viewport=page.viewport_size
                    page.set_viewport_size({'width':1280,'height':900})
                    page.bring_to_front()
                    # Capture timing with the native clock, not the frozen screenshot clock.
                    page.evaluate('delete performance.now')
                    (output/'variant-performance.json').write_text(json.dumps({'viewport':[1280,900],'samples':page.evaluate('widgetPreview.benchmark()')},indent=2),encoding='utf8')
                    page.evaluate('performance.now=()=>1000')
                    page.set_viewport_size(previous_viewport)
                    (output/'dom-metrics.json').write_text(json.dumps(page.evaluate('widgetPreview.metrics()'),indent=2),encoding='utf8')
                for name,sample,mode in corpus:
                    page.evaluate('([state,mode])=>widgetPreview.render(state,mode)',[sample,mode])
                    settle(page)
                    for kind in KINDS:
                        values=page.locator('[data-preview-kind="'+kind+'"] .widget').evaluate_all('(cards)=>cards.map(card=>Object.fromEntries([...card.querySelectorAll("[data-v]")].map(n=>[n.dataset.v,n.textContent])))')
                        assert values[0]==values[1]==values[2],(name,kind)
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),name
                page.evaluate('state=>widgetPreview.render(state,false)',long)
                page.evaluate('widgetPreview.customize({title:"Carte",color:"#76bbfd",background:"#182333",opacity:85,style:"outline"})')
                for locale in ['EN','FR']:
                    page.select_option('#locale-select',locale)
                    settle(page)
                    expect(page.locator('.widget-heading').first).to_have_text('Carte')
                    expect(page.locator('.w-player [data-v="name"]').first).to_have_text('Carte')
                    expect(page.locator('.w-player [data-v="activity"]').first).to_have_text('Playing' if locale=='EN' else 'En jeu')
                for theme in ['tactical-blue','competitive-red','performance-green','creator-purple']:
                    page.select_option('#theme-preview',theme)
                    settle(page)
                    assert page.locator('.widget').first.evaluate('card=>card.style.getPropertyValue("--widget-accent")')=='#76bbfd'
                    assert page.locator('.widget').first.evaluate('card=>card.style.getPropertyValue("--widget-bg")')=='#182333'
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),theme
                for surface in ['solid','glass','outline']:
                    page.evaluate('style=>widgetPreview.customize({style})',surface)
                    assert page.locator('.widget').first.get_attribute('data-style')==surface
                page.evaluate('state=>widgetPreview.render(state,false)',EMPTY)
                expect(page.locator('[data-inventory-count]').first).to_have_text('—')
                expect(page.locator('[data-grenade-count]').first).to_have_text('—')
                no_grenades=copy.deepcopy(state)
                no_grenades['player']['weapons']=[no_grenades['player']['weapons'][0]]
                page.evaluate('state=>widgetPreview.render(state,false)',no_grenades)
                expect(page.locator('[data-grenade-count]').first).to_have_text('0')
                page.evaluate('state=>widgetPreview.render(state,false)',EMPTY)
                for variant in ['standard','compact','minimal']:
                    expect(page.locator('.w-health[data-variant="'+variant+'"] [data-v="health"]')).to_have_text('—')
                    expect(page.locator('.w-health[data-variant="'+variant+'"] [role="progressbar"]')).not_to_have_attribute('aria-valuenow', '0')
                zero=copy.deepcopy(state)
                zero['player']['health']=0
                page.evaluate('state=>widgetPreview.render(state,false)',zero)
                expect(page.locator('.w-health[data-variant="minimal"] [data-v="health"]')).to_have_text('0')
                for locale in ['EN','FR']:
                    page.select_option('#locale-select',locale)
                    settle(page)
                    expected='More details' if locale=='EN' else 'Plus de détails'
                    expect(details.locator('summary')).to_have_text(expected)
                assert not faults,faults
                if output:
                    (output/'validation.json').write_text(json.dumps({'browser':browser.version,'representatives':KINDS,
                         'combinations':87,'widths':[1920,1366,1280,1024,768,390,320],'states':['normal','partial','missing','zero','stale','waiting','long','demo'],'themes':4,'errors':faults},indent=2),encoding='utf8')
                browser.close()
        finally:
            stop(process)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--browser',choices=['chromium','firefox','webkit'],default='chromium')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    run(args.browser,args.output)
