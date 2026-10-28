(()=>{'use strict';
const tr=text=>window.CS2I18N?.translate(text)||text,$=id=>document.getElementById(id);
const {isNum}=window.CS2DisplayFormat;
const widgetRenderer=window.CS2WidgetRenderer({board:$('board'),format:window.CS2DisplayFormat});
const W=window.CS2WidgetCatalog;
if(!W)throw new Error('Widget catalog must load before studio.js');
const VERSION='1.0.0', COLOR='#f3ac52', DEFAULT_IDS=['score','weapon','economy','stats','bomb'];
let profilesReady=false;
let modeDemo=false,last=null,anchor=null,pin='',currentView='default',editing=false,search='',category='all',openedSettings=new Set(),catalogOpen=false,profiles=[],activeProfile='',seq=1,notifyTimeout=null,dragId=null,pointerDrag=null;
const WIDTHS=[3,4,6,8,12], STYLES=['solid','glass','outline'];
const TEMPLATES={
 competitive:{name:'Compétitif compact',widgets:[['score',12],['weapon',4],['economy',8],['stats',12],['bomb',12]]},
 mobile:{name:'Essentiel mobile',widgets:[['score',12],['weapon',6],['ammo',6],['economy',12],['round_stats',12],['bomb',12]]},
 match:{name:'Vue du match',widgets:[['score',12],['map',4],['round',4],['match_phase',4],['round_history',12],['stats',12]]},
 stream:{name:'Streaming / statistiques',widgets:[['score',12],['stats',8],['kd',4],['round_stats',8],['mvp',4],['bomb',12],['events',12]]},
 blank:{name:'Page vide',widgets:[]}
};
const freshId=()=>`w${Date.now().toString(36)}${(seq++).toString(36)}`,freshProfileId=()=>`p${Date.now().toString(36)}${(seq++).toString(36)}`;
const newWidget=(kind,size)=>({id:freshId(),kind,span:size||W[kind].size,title:'',color:'',background:'',opacity:100,style:'solid'});
const seedWidgets=()=>DEFAULT_IDS.map(k=>newWidget(k));
function newProfile(name){return {id:freshProfileId(),name,accent:COLOR,density:'normal',widgets:seedWidgets()};}
function presetWidgets(key){return (TEMPLATES[key]?.widgets||TEMPLATES.competitive.widgets).map(([kind,span])=>newWidget(kind,span));}
function safeDensity(x){return x==='compact'?'compact':'normal';}
function safeOpacity(x){return Number.isFinite(x)&&x>=60&&x<=100&&x%5===0?x:100;}
function safeStyle(x){return STYLES.includes(x)?x:'solid';}
function safeColor(x){return typeof x==='string'&&/^#[0-9a-fA-F]{6}$/.test(x)?x:'';}
function sanitizeWidget(w){if(!w||typeof w!=='object'||typeof w.kind!=='string'||!Object.hasOwn(W,w.kind))return null;return {id:freshId(),kind:w.kind,span:WIDTHS.includes(w.span)?w.span:W[w.kind].size,title:typeof w.title==='string'?w.title.slice(0,36):'',color:safeColor(w.color),background:safeColor(w.background),opacity:safeOpacity(w.opacity),style:safeStyle(w.style)};}
// Profile synchronization is isolated from dashboard rendering and translated text.
function showSaveState(code){
 const panel=$('profile-save-panel');if(!panel)return;
 panel.hidden=!code||modeDemo||!profilesReady;
 $('profile-save-message').textContent=window.CS2I18N.message('profile.'+code);
 $('profile-save-retry').hidden=!profileSync.resolvable;
 $('profile-save-discard').hidden=!profileSync.resolvable;
}
const profileSync=window.CS2ProfileSync({
 getDocument:()=>({profiles,activeProfile}),
 applyDocument:message=>{profiles=structuredClone(message.profiles||[]);activeProfile=message.activeProfile||profiles[0]?.id||'';profilesReady=true;renderBoard();},
 canSave:()=>profilesReady&&!modeDemo&&dashboardClient.isOpen,
 send:command=>dashboardClient.send(command),
 onStatus:showSaveState
});
const profile=()=>profiles.find(p=>p.id===activeProfile)||profiles[0]||newProfile('Demo');
function save(){if(profilesReady&&!modeDemo)profileSync.changed();}
function clearPrivateProfiles(){
 profiles=[];activeProfile='';profilesReady=false;profileSync.clear();
 currentView='default';editing=false;catalogOpen=false;
}
function allowDiscardPending(){
 return !profileSync.dirty||confirm(window.CS2I18N.message('profile.discardPrompt'));
}
function toast(message){const t=$('toast');t.textContent=message;t.classList.remove('hidden');clearTimeout(notifyTimeout);notifyTimeout=setTimeout(()=>t.classList.add('hidden'),3000);}
function setStatus(msg,kind='',code=''){const x=$('status');x.textContent=msg;x.className='badge '+kind;document.dispatchEvent(new CustomEvent('cs2:status',{detail:{message:msg,kind,code}}));}
function setOnline(s){if(modeDemo)setStatus('Mode démo','ok');else setStatus(s?.online?'Partie connectée':s?.gsi_connected?'GSI actif · en attente de partie':'CS2 hors ligne',s?.online?'ok':'bad');$('notice').classList.toggle('hidden',!!s?.online&&!modeDemo);$('notice').textContent=modeDemo?'Données simulées':(!s?.online?'En attente de données de partie CS2.':'');document.dispatchEvent(new CustomEvent('cs2:state',{detail:{online:!!s?.online,gsi_connected:!!s?.gsi_connected,demo:modeDemo}}));}
function updateProfiles(){const x=$('profile-select');x.replaceChildren();for(const p of profiles){const o=document.createElement('option');o.value=p.id;o.textContent=p.name;o.setAttribute('translate','no');x.append(o);}x.value=activeProfile;$('accent').value=profile()?.accent||COLOR;$('density').value=profile()?.density||'normal';$('delete-profile').disabled=profiles.length<=1;if(currentView==='custom')document.documentElement.style.setProperty('--profile-accent',profile()?.accent||COLOR);else document.documentElement.style.removeProperty('--profile-accent');}
function updateChrome(){const custom=currentView==='custom'&&!modeDemo&&profilesReady;$('tab-custom').classList.toggle('hidden',modeDemo||!profilesReady);$('tab-default').classList.toggle('active',!custom);$('tab-custom').classList.toggle('active',custom);$('tab-default').setAttribute('aria-selected',String(!custom));$('tab-custom').setAttribute('aria-selected',String(custom));$('tab-default').tabIndex=custom?-1:0;$('tab-custom').tabIndex=custom?0:-1;$('custom-tools').classList.toggle('hidden',!custom);$('edit').classList.toggle('hidden',!custom);$('add').classList.toggle('hidden',!custom);$('edit').textContent=editing?'✓ Terminer':'✎ Personnaliser';$('edit').setAttribute('aria-pressed',String(editing));$('add').disabled=!editing;$('catalog').classList.toggle('hidden',!custom||!editing||!catalogOpen);$('edit-hint').classList.toggle('hidden',!custom||!editing);updateProfiles();}
function currentWidgets(){return currentView==='default'||modeDemo||!profilesReady?DEFAULT_IDS.map((k,i)=>({id:'default'+i,kind:k,span:W[k].size,title:'',color:''})):profile().widgets;}
function makeBtn(label,tip,action){const b=document.createElement('button');b.type='button';b.textContent=label;b.title=tip;b.setAttribute('aria-label',tip);b.addEventListener('click',action);return b;}
function renderBoard(){updateChrome();const board=$('board');board.replaceChildren();const widgets=currentWidgets();board.classList.toggle('editing',currentView==='custom'&&editing);board.dataset.view=currentView;board.dataset.density=currentView==='custom'?(profile()?.density||'normal'):'normal';$('empty-board').classList.toggle('hidden',widgets.length>0);
 for(const w of widgets){const d=W[w.kind];if(!d)continue;const article=widgetRenderer.createCard(w,d);
 if(currentView==='custom'&&editing){const settings=document.createElement('div');settings.className='widget-settings';const controls=document.createElement('div');controls.className='edit-controls';
 controls.append(makeBtn('⠿','Glisser pour déplacer',()=>{}),makeBtn('↑','Monter le widget',()=>shift(w.id,-1)),makeBtn('↓','Descendre le widget',()=>shift(w.id,1)),makeBtn('⚙','Options du widget',()=>{openedSettings.has(w.id)?openedSettings.delete(w.id):openedSettings.add(w.id);renderBoard();}),makeBtn('×','Supprimer le widget',()=>removeWidget(w.id)));
 controls.firstElementChild.classList.add('move');controls.lastElementChild.classList.add('remove');const details=document.createElement('div');details.className='details'+(openedSettings.has(w.id)?' open':'');
 const labelTitle=document.createElement('label');labelTitle.textContent='Titre';const titleInput=document.createElement('input');titleInput.className='input';titleInput.type='text';titleInput.maxLength=36;titleInput.placeholder=d.title;titleInput.value=w.title||'';titleInput.addEventListener('change',()=>{w.title=titleInput.value.trim().slice(0,36);save();renderBoard();});
 const widthLabel=document.createElement('label');widthLabel.textContent='Largeur';const widths=document.createElement('select');widths.className='select';for(const [val,txt] of [[3,'¼'],[4,'⅓'],[6,'½'],[8,'⅔'],[12,'Pleine']]){const op=new Option(txt,String(val));widths.append(op);}widths.value=String(w.span);widths.addEventListener('change',()=>{w.span=Number(widths.value);save();renderBoard();});
 const colLabel=document.createElement('label');colLabel.textContent='Accent';const color=document.createElement('input');color.type='color';color.value=w.color||profile().accent||COLOR;color.addEventListener('change',()=>{w.color=color.value;save();renderBoard();});
 const clear=makeBtn('Auto','Couleur automatique',()=>{w.color='';save();renderBoard();});
 const bgLabel=document.createElement('label');bgLabel.textContent='Fond';const bgColor=document.createElement('input');bgColor.type='color';bgColor.value=w.background||'#182333';bgColor.setAttribute('aria-label','Couleur de fond');bgColor.addEventListener('change',()=>{w.background=bgColor.value;save();renderBoard();});
 const bgReset=makeBtn('Auto','Fond automatique',()=>{w.background='';save();renderBoard();});
 const styleLabel=document.createElement('label');styleLabel.textContent='Style';const styleSel=document.createElement('select');styleSel.className='select';for(const [value,label] of [['solid','Plein'],['glass','Verre'],['outline','Contour']])styleSel.add(new Option(label,value));styleSel.value=w.style||'solid';styleSel.addEventListener('change',()=>{w.style=styleSel.value;save();renderBoard();});
 const opacityLabel=document.createElement('label');opacityLabel.textContent='Opacité du fond';const opacityInput=document.createElement('input');opacityInput.type='range';opacityInput.min='60';opacityInput.max='100';opacityInput.step='5';opacityInput.value=w.opacity??100;opacityInput.setAttribute('aria-label','Opacité du fond');const opacityValue=document.createElement('span');opacityValue.className='tiny';opacityValue.textContent=opacityInput.value+'%';opacityInput.addEventListener('input',()=>{opacityValue.textContent=opacityInput.value+'%';article.style.setProperty('--widget-opacity',opacityInput.value+'%');});opacityInput.addEventListener('change',()=>{w.opacity=Number(opacityInput.value);save();renderBoard();});
 details.append(labelTitle,titleInput,widthLabel,widths,colLabel,color,clear,bgLabel,bgColor,bgReset,styleLabel,styleSel,opacityLabel,opacityInput,opacityValue);settings.append(controls,details);article.append(settings);article.draggable=true;
 const resizer=document.createElement('button');resizer.className='resize-grip';resizer.type='button';resizer.textContent='⇲';resizer.title='Glisser pour redimensionner · flèches gauche/droite au clavier';resizer.setAttribute('aria-label','Redimensionner le widget');resizer.setAttribute('aria-valuetext',w.span+' / 12');article.append(resizer);attachResizeGrip(resizer,article,w);
 article.addEventListener('dragstart',e=>{if(e.target.closest('input,select')){e.preventDefault();return;}dragId=w.id;article.classList.add('dragging');if(e.dataTransfer){e.dataTransfer.effectAllowed='move';e.dataTransfer.setData('text/plain',w.id);}});
 article.addEventListener('dragend',()=>{dragId=null;clearDragStyle();});article.addEventListener('dragover',e=>{if(dragId&&dragId!==w.id){e.preventDefault();article.classList.add('drag-over');}});article.addEventListener('dragleave',()=>article.classList.remove('drag-over'));
 article.addEventListener('drop',e=>{e.preventDefault();const from=dragId||e.dataTransfer?.getData('text/plain');clearDragStyle();if(from)reorder(from,w.id);dragId=null;});
 }board.append(article);
 }
 if(currentView==='custom'&&editing)attachTouchHandles();updateValues();}
function attachResizeGrip(grip,card,w){
 let resizing=null;
 grip.addEventListener('pointerdown',e=>{if(e.button!==0)return;e.preventDefault();e.stopPropagation();const board=$('board');const gap=parseFloat(getComputedStyle(board).columnGap)||14;const col=(board.clientWidth-11*gap)/12;if(col<=0)return;resizing={x:e.clientX,start:w.span,col:col+gap,id:e.pointerId};card.draggable=false;grip.setPointerCapture(e.pointerId);card.classList.add('resizing');});
 grip.addEventListener('pointermove',e=>{if(!resizing||resizing.id!==e.pointerId)return;const target=resizing.start+(e.clientX-resizing.x)/resizing.col;const next=WIDTHS.reduce((best,candidate)=>Math.abs(candidate-target)<Math.abs(best-target)?candidate:best,WIDTHS[0]);w.span=next;card.style.setProperty('--span',next);grip.setAttribute('aria-valuetext',next+' / 12');grip.title=next+' / 12';});
 const finish=e=>{if(!resizing||resizing.id!==e.pointerId)return;const canceled=e.type==='pointercancel';w.span=canceled?resizing.start:w.span;resizing=null;card.draggable=true;card.classList.remove('resizing');save();renderBoard();};
 grip.addEventListener('pointerup',finish);grip.addEventListener('pointercancel',finish);
 grip.addEventListener('keydown',e=>{if(e.key!=='ArrowRight'&&e.key!=='ArrowLeft')return;e.preventDefault();const idx=WIDTHS.indexOf(w.span);w.span=WIDTHS[Math.max(0,Math.min(WIDTHS.length-1,idx+(e.key==='ArrowRight'?1:-1)))];save();renderBoard();const replacement=document.querySelector('.widget[data-id="'+CSS.escape(w.id)+'"] .resize-grip');replacement?.focus();});
}
function clearDragStyle(){document.querySelectorAll('.drag-over,.dragging').forEach(e=>e.classList.remove('drag-over','dragging'));}
function reorder(from,to){if(!from||from===to)return;const a=profile().widgets,fromIndex=a.findIndex(w=>w.id===from),toIndex=a.findIndex(w=>w.id===to);if(fromIndex<0||toIndex<0)return;const [item]=a.splice(fromIndex,1);a.splice(toIndex,0,item);save();renderBoard();}
function shift(id,direction){const a=profile().widgets,i=a.findIndex(w=>w.id===id),j=i+direction;if(j<0||j>=a.length)return;[a[i],a[j]]=[a[j],a[i]];save();renderBoard();}
function removeWidget(id){profile().widgets=profile().widgets.filter(x=>x.id!==id);openedSettings.delete(id);save();renderBoard();}
function attachTouchHandles(){document.querySelectorAll('.widget .move').forEach(handle=>{
 handle.addEventListener('pointerdown',e=>{if(e.pointerType==='mouse')return;const card=handle.closest('.widget');pointerDrag={id:card.dataset.id,x:e.clientX,y:e.clientY,target:null,handle,moved:false};handle.setPointerCapture(e.pointerId);e.preventDefault();});
 handle.addEventListener('pointermove',e=>{const p=pointerDrag;if(!p||p.handle!==handle)return;if(Math.hypot(e.clientX-p.x,e.clientY-p.y)<7&&!p.moved)return;p.moved=true;clearDragStyle();const hit=document.elementFromPoint(e.clientX,e.clientY)?.closest('.widget');if(hit&&hit.dataset.id!==p.id){p.target=hit.dataset.id;hit.classList.add('drag-over');}});
 handle.addEventListener('pointerup',()=>{const p=pointerDrag;pointerDrag=null;clearDragStyle();if(p?.target)reorder(p.id,p.target);});handle.addEventListener('pointercancel',()=>{pointerDrag=null;clearDragStyle();});
 });}
function renderCatalog(){const parent=$('catalog-items');parent.replaceChildren();let group='';for(const [kind,d] of Object.entries(W)){if(category!=='all'&&category!==d.cat)continue;const terms=[kind,d.title,d.cat,tr(d.title),tr(d.cat)].join(' ').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();if(search&&!terms.includes(search.normalize('NFD').replace(/[\u0300-\u036f]/g,'')))continue;if(group!==d.cat){group=d.cat;const h=document.createElement('div');h.className='cat-divider';h.textContent=tr(group);parent.append(h);}
 const b=document.createElement('button');b.className='catalog-item';b.dataset.kind=kind;b.type='button';const icon=document.createElement('div');icon.className='catalog-icon';icon.textContent=d.icon;const txt=document.createElement('div');const strong=document.createElement('strong');strong.textContent=d.title;const sm=document.createElement('small');sm.textContent=d.cat;txt.append(strong,sm);b.append(icon,txt);b.addEventListener('click',()=>{if(profile().widgets.length>=60){toast('Maximum 60 widgets par profil.');return;}profile().widgets.push(newWidget(kind));save();renderBoard();toast(d.title+' ajouté');});parent.append(b);
 }if(!parent.children.length){const x=document.createElement('div');x.textContent='Aucun widget trouvé';parent.append(x);}}
function updateValues(){widgetRenderer.updateValues(last,{modeDemo,anchor});}
function paintBomb(){widgetRenderer.paintBomb(last,anchor);}
function renderData(s){last=s;anchor=s.bomb_timer?.status==='active'&&isNum(s.bomb_timer.remaining)?{at:performance.now(),left:s.bomb_timer.remaining}:null;$('login').classList.add('hidden');$('view').classList.remove('hidden');setOnline(s);updateValues();}
const dashboardClient=window.CS2DashboardClient({
 version:VERSION,
 getPin:()=>pin,
 isDemo:()=>modeDemo,
 onConnecting:()=>setStatus('Connexion…','','connecting'),
 onHealthError:(error,versionMismatch)=>{
  if(versionMismatch){
   $('loginerror').textContent='Redémarre Docker avec la version 1.0.0.';
   setStatus('Mise à jour requise','bad','error');
  }else{
   $('loginerror').textContent='Serveur indisponible : '+error.message;
   setStatus('Hors ligne','bad','error');
  }
 },
 onMessage:handleServerMessage,
 onNetworkError:({failed})=>{
  if(!failed)setStatus('Erreur réseau','bad','error');
  document.dispatchEvent(new Event('cs2:network-error'));
 },
 onClose:({authorized,failed})=>{
  profileSync.disconnected();
  if(!authorized){
   if(!failed)$('loginerror').textContent='Impossible de se connecter au WebSocket.';
   setStatus('Déconnecté','bad','lost');
   if(!failed)reconnect.failed();
   return;
  }
  setStatus('Reconnexion…','bad','lost');
  document.dispatchEvent(new CustomEvent('cs2:connection-lost'));
  anchor=null;
  if(last){
   last.bomb_timer={status:'stale'};
   last.online=false;
   setOnline(last);
   paintBomb();
  }
  reconnect.failed();
 }
});
const reconnect=window.CS2Reconnect({connect:isCurrent=>dashboardClient.connect(isCurrent)});
function login(){
 modeDemo=false;pin=$('pin').value.trim()||pin;$('loginerror').textContent='';$('pin').setAttribute('aria-invalid','false');
 if(pin.length<6){$('loginerror').textContent='Code PIN trop court.';$('pin').setAttribute('aria-invalid','true');return;}
 reconnect.stop();dashboardClient.close();
 reconnect.start();
}
function handleServerMessage(message){
 if(message.type==='auth_error'){
  reconnect.stop();
  $('loginerror').textContent=message.message||'Code incorrect.';
  $('pin').setAttribute('aria-invalid','true');
  setStatus('PIN incorrect','bad','error');
  return;
 }
 if(message.type==='auth_ok'){
  reconnect.connected();
  profileSync.authenticate(message.session||'');
  profilesReady=true;
  $('pin').value='';
  $('download-support').classList.remove('hidden');
  setStatus('Connecté','ok');
  document.dispatchEvent(new Event('cs2:authenticated'));
  return;
 }
 if(message.type==='profiles_state'){profileSync.receive(message);return;}
 if(message.type==='profiles_error'){profileSync.failed(message.code);return;}
 if(message.type==='diagnostics_data'){
  const blob=new Blob([JSON.stringify(message.report,null,2)],{type:'application/json'});
  const downloadUrl=URL.createObjectURL(blob);
  const downloadLink=document.createElement('a');
  downloadLink.href=downloadUrl;
  downloadLink.download='CS2_Companion_support.json';
  downloadLink.click();
  setTimeout(()=>URL.revokeObjectURL(downloadUrl),1000);
  return;
 }
 if(message.type==='state')renderData(message);
}
const SAMPLE={type:'state',online:true,gsi_connected:true,age_seconds:0,map:'de_mirage',map_mode:'competitive',map_phase:'live',round:14,round_phase:'live',ct:8,t:5,round_winner:'',recent_wins:[{round:10,winner:'ct_win'},{round:11,winner:'t_win'},{round:12,winner:'ct_win'}],bomb_state:'',bomb_timer:{enabled:false,status:'disabled',duration:40},economy:{on_loss:5600,loss_bonus:2400,loss_streak_known:true,source:'gsi'},events:[{message:'Élimination · 18 au total',at:Date.now()/1000,category:'kill'},{message:'Nouvelle manche · MIRAGE',at:Date.now()/1000-35,category:'round'}],provider:{version:'CS2'},player:{name:'Player',team:'CT',activity:'playing',money:3200,health:87,armor:94,helmet:true,defusekit:true,equip_value:4300,flashed:0,smoked:0,burning:0,weapon:'weapon_ak47',ammo_clip:21,ammo_max:30,ammo_reserve:90,kills:18,assists:4,deaths:11,mvps:3,score:42,round_kills:2,round_killhs:1,round_totaldmg:167,weapons:[{name:'weapon_ak47',type:'Rifle',state:'active',ammo_clip:21},{name:'weapon_usp_silencer',type:'Pistol',state:'holstered',ammo_clip:12},{name:'weapon_smokegrenade',type:'Grenade',state:'holstered'},{name:'weapon_flashbang',type:'Grenade',state:'holstered'}]}};
function demo(){if(!allowDiscardPending())return;reconnect.stop();clearPrivateProfiles();pin='';$('pin').value='';$('download-support').classList.add('hidden');modeDemo=true;dashboardClient.close();renderData(structuredClone(SAMPLE));}function demoBomb(n){if(!modeDemo)return;const s=structuredClone(SAMPLE);s.bomb_state=n==='stop'?'defused':'planted';s.bomb_timer=n==='stop'?{enabled:true,status:'idle',duration:40}:{enabled:true,status:'active',remaining:n,duration:40};renderData(s);}
function initialize(){updateProfiles();renderBoard();renderCatalog();}
$('tab-default').addEventListener('click',()=>{currentView='default';editing=false;catalogOpen=false;renderBoard();});$('tab-custom').addEventListener('click',()=>{if(modeDemo||!profilesReady)return;currentView='custom';renderBoard();});
$('edit').addEventListener('click',()=>{editing=!editing;if(!editing)catalogOpen=false;renderBoard();});$('add').addEventListener('click',()=>{catalogOpen=!catalogOpen;updateChrome();if(catalogOpen)$('search-widgets').focus();});$('close-catalog').addEventListener('click',()=>{catalogOpen=false;updateChrome();});$('search-widgets').addEventListener('input',e=>{search=e.target.value.toLowerCase();renderCatalog();});$('catalog-category').addEventListener('change',e=>{category=e.target.value;renderCatalog();});
$('profile-select').addEventListener('change',e=>{activeProfile=e.target.value;editing=false;catalogOpen=false;save();renderBoard();});$('accent').addEventListener('change',e=>{profile().accent=safeColor(e.target.value)||COLOR;save();updateChrome();});$('density').addEventListener('change',e=>{profile().density=safeDensity(e.target.value);save();renderBoard();});
$('create-template').addEventListener('click',()=>{if(profiles.length>=12){toast('Maximum 12 profils.');return;}const key=$('template-select').value,t=TEMPLATES[key]||TEMPLATES.competitive;const p=newProfile(tr(t.name));p.widgets=presetWidgets(key);profiles.push(p);activeProfile=p.id;currentView='custom';editing=true;catalogOpen=false;save();renderBoard();toast('Profil créé');});
$('new-profile').addEventListener('click',()=>{if(profiles.length>=12){toast('Maximum 12 profils.');return;}const name=prompt(tr('Nom du nouveau profil :'),tr('Mon setup'));if(name===null)return;const p=newProfile(name.trim().slice(0,32)||'Mon setup');p.widgets=[];profiles.push(p);activeProfile=p.id;editing=true;save();renderBoard();});
$('rename-profile').addEventListener('click',()=>{if(!profilesReady||modeDemo)return;const p=profile(),name=prompt(tr('Nouveau nom du dashboard :'),p.name);if(name===null)return;const clean=name.trim().slice(0,32);if(!clean)return;p.name=clean;save();updateProfiles();toast(tr('Dashboard renommé'));});
$('duplicate-profile').addEventListener('click',()=>{if(profiles.length>=12){toast('Maximum 12 profils.');return;}const p=profile(),copy={id:freshProfileId(),name:(p.name+' copie').slice(0,32),accent:p.accent,density:safeDensity(p.density),widgets:p.widgets.map(x=>sanitizeWidget(x))};profiles.push(copy);activeProfile=copy.id;save();renderBoard();});
$('delete-profile').addEventListener('click',()=>{if(profiles.length<=1)return;if(!confirm(tr('Supprimer ce profil ?')))return;profiles=profiles.filter(p=>p.id!==activeProfile);activeProfile=profiles[0].id;save();renderBoard();});
$('reset').addEventListener('click',()=>{if(!confirm(tr('Remettre ce profil à sa disposition initiale ?')))return;profile().widgets=seedWidgets();profile().accent=COLOR;profile().density='normal';openedSettings.clear();save();renderBoard();});
$('export').addEventListener('click',()=>{const data={format:'cs2-companion-layout',version:2,profile:{name:profile().name,accent:profile().accent,density:profile().density,widgets:profile().widgets.map(({kind,span,title,color,background,opacity,style})=>({kind,span,title,color,background,opacity,style}))}};const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='CS2_Companion_'+profile().name.replace(/[^a-z0-9_-]+/gi,'_')+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),500);toast('Profil exporté');});
$('import').addEventListener('click',()=>$('import-file').click());$('import-file').addEventListener('change',async e=>{const file=e.target.files?.[0];e.target.value='';if(!file)return;if(file.size>150000){toast('Fichier trop volumineux.');return;}try{const data=JSON.parse(await file.text());if(data.format!=='cs2-companion-layout'||data.version!==2||!data.profile||!Array.isArray(data.profile.widgets))throw Error('Format inconnu');if(profiles.length>=12)throw Error('Maximum 12 profils');const items=data.profile.widgets.slice(0,60).map(sanitizeWidget).filter(Boolean);const p={id:freshProfileId(),name:String(data.profile.name||'Import').slice(0,32),accent:safeColor(data.profile.accent)||COLOR,density:safeDensity(data.profile.density),widgets:items};profiles.push(p);activeProfile=p.id;editing=true;save();renderBoard();toast('Profil importé · '+items.length+' widgets');}catch(err){toast('Import impossible : '+err.message);}});
$('download-support').addEventListener('click',()=>{if(!modeDemo&&profilesReady&&dashboardClient.isOpen)dashboardClient.send({type:'diagnostics_request'});});
$('connect').addEventListener('click',login);$('pin').addEventListener('keydown',e=>{if(e.key==='Enter')login();});$('demo').addEventListener('click',demo);$('demoagain').addEventListener('click',demo);
$('board').addEventListener('click',e=>{const b=e.target.closest('[data-demo]');if(b&&modeDemo){const n=b.dataset.demo;demoBomb(n==='stop'?'stop':Number(n));}});
$('logout').addEventListener('click',()=>{if(!allowDiscardPending())return;reconnect.stop();clearPrivateProfiles();pin='';$('pin').value='';$('download-support').classList.add('hidden');document.dispatchEvent(new Event('cs2:logout'));modeDemo=false;dashboardClient.close();last=null;anchor=null;$('view').classList.add('hidden');$('login').classList.remove('hidden');setStatus('Non connecté');});
$('locale-select').addEventListener('change',()=>setTimeout(()=>{renderCatalog();showSaveState(profileSync.status);},0));
// Repaint the countdown only while it is running and the tab is visible.
setInterval(()=>{
 if(!document.hidden&&last?.bomb_timer?.status==='active')paintBomb();
},100);
const savePanel=document.createElement('section');
savePanel.id='profile-save-panel';savePanel.hidden=true;savePanel.className='notice';
const saveMessage=document.createElement('p');saveMessage.id='profile-save-message';saveMessage.setAttribute('role','status');
const retrySave=makeBtn('Enregistrer ma version','Remplacer la version du serveur par mes modifications',()=>profileSync.resolve(true));retrySave.id='profile-save-retry';
const discardSave=makeBtn('Charger la version du serveur','Abandonner mes modifications non enregistrées',()=>profileSync.resolve(false));discardSave.id='profile-save-discard';
savePanel.append(saveMessage,retrySave,discardSave);$('custom-tools').after(savePanel);
window.addEventListener('beforeunload',event=>{if(profileSync.dirty){event.preventDefault();event.returnValue='';}});
initialize();
})();
