"""Offline Chromium UX checks for public E.1 features."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import re
R=Path(__file__).resolve().parents[2]
html=re.sub(r'<script defer[^>]*></script>', '', (R/'static/index.html').read_text())
html=re.sub(r'<link rel="stylesheet"[^>]*>', '', html)

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1100,'height':800})
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_content(html)
    page.evaluate("""()=>{
      const mem={'cs2-companion-studio-v3': JSON.stringify({profiles:[{name:'SECRET DEMO PROFILE'}]})};
      Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>mem[k]||null,setItem:(k,v)=>mem[k]=v}});
      window.__sent=[];
      window.fetch=async()=>({ok:true,json:async()=>({service:'ok',version:'1.0.0'})});
      window.WebSocket=class{
        static OPEN=1;static CLOSED=3;
        constructor(){this.readyState=0;window.__socket=this;setTimeout(()=>{this.readyState=1;this.onopen?.();},0);}
        send(raw){const req=JSON.parse(raw);window.__sent.push(req);if(req.type==='auth'){
          setTimeout(()=>{this.onmessage?.({data:JSON.stringify({type:'auth_ok',version:'1.0.0',session:'s123'})});
            this.onmessage?.({data:JSON.stringify({type:'profiles_state',revision:1,source:null,profiles:[{id:'p123',name:'Shared profile',accent:'#f3ac52',density:'normal',widgets:[{id:'w1',kind:'score',span:12,title:'',color:'',background:'',opacity:100,style:'solid'}]}],activeProfile:'p123'})});
            this.onmessage?.({data:JSON.stringify({type:'state',online:false,player:{},bomb_timer:{status:'disabled'}})});},0);
          }else if(req.type==='profiles_save')setTimeout(()=>this.onmessage?.({data:JSON.stringify({type:'profiles_state',revision:2,source:'s123',...req.document})}),0);
        }
        close(){this.readyState=3;}
      };
    }""")
    page.add_style_tag(content=(R/'static/styles.css').read_text())
    for name in ('i18n.js','widgets.js','studio.js','experience.js'):
        page.add_script_tag(content=(R/'static'/name).read_text())
    page.evaluate("document.dispatchEvent(new Event('DOMContentLoaded'))")
    page.locator('#demo').click()
    assert not page.locator('#tab-custom').is_visible(), 'custom tab exposed to demo'
    assert 'SECRET DEMO PROFILE' not in page.locator('body').inner_text()
    assert page.locator('#download-support').is_hidden(), 'support exposed in demo'
    page.locator('#logout').click()
    page.locator('#pin').fill('1234567890')
    page.locator('#connect').click()
    page.wait_for_timeout(200)
    assert page.locator('#tab-custom').is_visible()
    assert page.locator('#profile-select option').count()==1
    assert page.locator('#profile-select').input_value()=='p123'
    page.locator('#tab-custom').click()
    page.locator('#edit').click()
    page.locator('#add').click()
    page.locator('#search-widgets').fill('map')
    assert page.locator('#catalog-items .catalog-item').count()>=1, 'Map search in EN'
    assert 'Map' in page.locator('#catalog-items').inner_text()
    page.locator('#locale-select').select_option('FR')
    page.locator('#search-widgets').fill('map')
    assert page.locator('#catalog-items .catalog-item').count()>=1, 'Map search in FR'
    assert page.locator('#rename-profile').is_visible()
    page.on('dialog', lambda d: d.accept('Tablet setup'))
    page.locator('#rename-profile').click()
    page.wait_for_timeout(250)
    assert page.locator('#profile-select').input_value()=='p123'
    assert 'Tablet setup' in page.locator('#profile-select').inner_text()
    assert any(x['type']=='profiles_save' for x in page.evaluate('window.__sent'))
    assert page.locator('#diagnostics-toggle').evaluate("e=>e.closest('.diagnostics-footer')!==null")
    assert not errors,errors
    print('OK: public demo isolated, authenticated profiles, renaming and server save, bilingual map search, diagnostics at bottom')
    browser.close()
