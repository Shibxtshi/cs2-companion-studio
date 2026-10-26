(()=>{'use strict';
const tr=text=>window.CS2I18N?.translate(text)||text,$=id=>document.getElementById(id), isNum=x=>typeof x==='number'&&Number.isFinite(x),v=(x,none='—')=>x===null||x===undefined||x===''?none:String(x),cash=x=>isNum(x)?x.toLocaleString(window.CS2I18N?.locale()==='FR'?'fr-FR':'en-US')+' $':'—',fmt=x=>isNum(x)?x.toLocaleString(window.CS2I18N?.locale()==='FR'?'fr-FR':'en-US'):'—',pct=x=>isNum(x)?Math.max(0,Math.min(100,x))+'%':'0%',weaponName=x=>v(x).replace(/^weapon_/,'').replaceAll('_',' ').toUpperCase(),capitalize=s=>v(s).replace(/^./,x=>x.toUpperCase());
const W={
 score:{title:'Score',icon:'🏆',cat:'Partie',size:12,html:`<div class="flex"><div><div class="smallish" data-v="map"></div><div class="muted" data-v="round"></div></div><div class="score-side"><span class="team-ct" data-v="ct"></span><span class="muted">:</span><span class="team-t" data-v="t"></span></div></div>`},
 map:{title:'Carte',icon:'🗺',cat:'Partie',size:4,html:`<div class="big" data-v="map"></div><div class="muted space" data-v="map_mode"></div>`},
 round:{title:'Manche',icon:'◷',cat:'Partie',size:4,html:`<div class="big" data-v="round_number"></div><div class="muted space" data-v="round_phase"></div><div class="tiny" data-v="round_winner"></div>`},
 score_split:{title:'Score détaillé',icon:'⚔',cat:'Partie',size:6,html:`<div class="stat-tiles"><div><span class="tiny">CT</span><b class="team-ct" data-v="ct"></b></div><div><span class="tiny">T</span><b class="team-t" data-v="t"></b></div></div><div class="tiny space" data-v="round"></div>`},
 match_phase:{title:'Phase du match',icon:'⏳',cat:'Partie',size:4,html:`<div class="medium" data-v="map_phase"></div><div class="muted space" data-v="round_phase"></div>`},
 round_history:{title:'Historique des manches',icon:'▥',cat:'Partie',size:6,html:`<div class="history-list" data-list="wins"></div><div class="tiny space">Disponible selon les données envoyées par CS2</div>`},
 weapon:{title:'Arme équipée',icon:'⌖',cat:'Armement',size:4,html:`<div class="weapon-text" data-v="weapon"></div><div class="rowgap space"><span class="big" data-v="ammo_clip"></span><span class="muted" data-v="ammo_reserve"></span></div>`},
 ammo:{title:'Munitions',icon:'▰',cat:'Armement',size:4,html:`<div class="rowgap"><div class="big" data-v="ammo_clip"></div><div class="muted" data-v="ammo_reserve"></div></div><div class="bar"><div class="bar-fill" data-p="ammo"></div></div><div class="tiny space" data-v="weapon"></div>`},
 inventory:{title:'Inventaire',icon:'▦',cat:'Armement',size:8,html:`<div class="inventory-list" data-list="weapons"></div>`},
 grenades:{title:'Grenades possédées',icon:'✳',cat:'Armement',size:6,html:`<div class="inventory-list" data-list="grenades"></div><div class="tiny space">Inventaire personnel uniquement</div>`},
 equip_value:{title:'Valeur d’équipement',icon:'▣',cat:'Armement',size:4,html:`<div class="big" data-v="equip_value"></div><div class="muted space">Valeur rapportée par CS2</div>`},
 gear:{title:'Équipement',icon:'⬡',cat:'Armement',size:4,html:`<div class="rowgap"><span class="tag" data-v="helmet"></span><span class="tag" data-v="kit"></span></div><div class="tiny space" data-v="armor_line"></div>`},
 economy:{title:'Économie',icon:'＄',cat:'Économie',size:8,html:`<div class="flex"><div><div class="big accent" data-v="money"></div><div class="muted">Argent disponible</div></div><div style="text-align:right"><div class="medium" data-v="nextmoney"></div><div class="muted">Si défaite · estimation</div></div></div><div class="divider"></div><div class="flex tiny"><span data-v="lossbonus"></span><span data-v="econ_note"></span></div>`},
 cash:{title:'Argent actuel',icon:'＄',cat:'Économie',size:4,html:`<div class="big accent" data-v="money"></div><div class="muted space">Disponible</div>`},
 forecast:{title:'Prochain round',icon:'↗',cat:'Économie',size:6,html:`<div class="big" data-v="nextmoney"></div><div class="muted space" data-v="lossbonus"></div><div class="tiny space" data-v="econ_note"></div>`},
 stats:{title:'Statistiques K / A / D',icon:'✦',cat:'Statistiques',size:12,html:`<div class="stat-tiles"><div><span class="tiny">Éliminations</span><b data-v="kills"></b></div><div><span class="tiny">Assists</span><b data-v="assists"></b></div><div><span class="tiny">Morts</span><b data-v="deaths"></b></div></div>`},
 kd:{title:'Ratio K / D',icon:'◎',cat:'Statistiques',size:4,html:`<div class="big" data-v="kd"></div><div class="muted space">Éliminations / morts</div>`},
 mvp:{title:'MVP',icon:'★',cat:'Statistiques',size:4,html:`<div class="big" data-v="mvps"></div><div class="muted space">Étoiles MVP</div>`},
 personal_score:{title:'Score personnel',icon:'♛',cat:'Statistiques',size:4,html:`<div class="big" data-v="personal_score"></div><div class="muted space">Points au scoreboard</div>`},
 round_stats:{title:'Statistiques du round',icon:'◉',cat:'Statistiques',size:8,html:`<div class="stat-tiles"><div><span class="tiny">Kills</span><b data-v="round_kills"></b></div><div><span class="tiny">Headshots</span><b data-v="round_hs"></b></div><div><span class="tiny">Dégâts</span><b data-v="round_damage"></b></div></div>`},
 health:{title:'Santé',icon:'♥',cat:'Joueur',size:4,html:`<div class="big" data-v="health"></div><div class="bar"><div class="bar-fill" data-p="health"></div></div>`},
 armor:{title:'Armure',icon:'⬟',cat:'Joueur',size:4,html:`<div class="big" data-v="armor"></div><div class="bar"><div class="bar-fill" data-p="armor"></div></div>`},
 effects:{title:'Effets subis',icon:'☀',cat:'Joueur',size:6,html:`<div class="stat-tiles"><div><span class="tiny">Flash</span><b data-v="flash"></b></div><div><span class="tiny">Smoke</span><b data-v="smoke"></b></div><div><span class="tiny">Feu</span><b data-v="fire"></b></div></div><div class="tiny space">Intensité rapportée par CS2 · 0–255</div>`},
 player:{title:'Joueur',icon:'◈',cat:'Joueur',size:6,html:`<div class="medium" data-v="name"></div><div class="rowgap space"><span class="pill" data-v="team"></span><span class="pill" data-v="activity"></span></div>`},
 bomb:{title:'Bombe',icon:'◉',cat:'Bombe',size:12,html:`<div class="flex"><span class="smallish" data-v="bomb_state"></span><span class="pill">Chrono estimé</span></div><div class="bomb-clock" data-bomb-clock>--.- s</div><div class="bomb-track"><div class="bomb-fill" data-bomb-fill></div></div><div class="bomb-legend" data-bomb-msg>En attente</div><div class="demo-controls hidden" data-demo-controls><button class="btn small" data-demo="40">40 s</button><button class="btn small" data-demo="9">9 s</button><button class="btn small" data-demo="4">4 s</button><button class="btn small" data-demo="stop">Stop</button></div>`},
 bomb_state:{title:'État de la bombe',icon:'●',cat:'Bombe',size:4,html:`<div class="medium" data-v="bomb_state"></div><div class="tiny space" data-v="round_phase"></div>`},
 connection:{title:'Connexion GSI',icon:'◌',cat:'Système',size:4,html:`<div class="medium" data-v="connection"></div><div class="muted space" data-v="lastpacket"></div>`},
 events:{title:'Journal de la partie',icon:'☷',cat:'Système',size:8,html:`<div class="event-list" data-list="events"></div><div class="tiny space">Événements déduits des données GSI reçues</div>`},
 provider:{title:'Version du jeu',icon:'⚙',cat:'Système',size:4,html:`<div class="medium" data-v="provider"></div><div class="tiny space">Donnée GSI provider</div>`}
};
const VERSION='1.0.0', COLOR='#f3ac52', DEFAULT_IDS=['score','weapon','economy','stats','bomb'];
let profilesReady=false,profilesRevision=0,sessionId='',saveTimer=null,saveInFlight=false,saveQueued=false;
let ws=null,modeDemo=false,last=null,anchor=null,pin='',currentView='default',editing=false,search='',category='all',openedSettings=new Set(),catalogOpen=false,profiles=[],activeProfile='',seq=1,notifyTimeout=null,dragId=null,pointerDrag=null;
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
function sanitizeWidget(w){if(!w||typeof w!=='object'||!W[w.kind])return null;return {id:freshId(),kind:w.kind,span:WIDTHS.includes(w.span)?w.span:W[w.kind].size,title:typeof w.title==='string'?w.title.slice(0,36):'',color:safeColor(w.color),background:safeColor(w.background),opacity:safeOpacity(w.opacity),style:safeStyle(w.style)};}
// Server is authoritative: no dashboard profiles in localStorage or in public demo.
function save(){
 if(!profilesReady||modeDemo)return;
 saveQueued=true;
 clearTimeout(saveTimer);
 if(!saveInFlight)saveTimer=setTimeout(flushSave,180);
}
function flushSave(){
 if(!saveQueued||saveInFlight||!profilesReady||modeDemo||!ws||ws.readyState!==WebSocket.OPEN)return;
 saveInFlight=true;saveQueued=false;
 ws.send(JSON.stringify({type:'profiles_save',revision:profilesRevision,document:{profiles,activeProfile}}));
}
const profile=()=>profiles.find(p=>p.id===activeProfile)||profiles[0]||newProfile('Demo');
function acceptServerProfiles(msg){
 if(modeDemo||!sessionId)return;
 if(msg.revision<profilesRevision)return;
 if(saveInFlight && msg.source!==sessionId && msg.source){profilesRevision=msg.revision;return;}
 const localPending=saveQueued;
 profilesRevision=msg.revision;
 if(msg.source===sessionId)saveInFlight=false;
 if(!localPending){
   profiles=Array.isArray(msg.profiles)?msg.profiles:[];
   activeProfile=msg.activeProfile||profiles[0]?.id||'';
   profilesReady=true;
   renderBoard();
 }else if(!saveInFlight){flushSave();}
}
function clearPrivateProfiles(){
 clearTimeout(saveTimer);profiles=[];activeProfile='';profilesRevision=0;
 profilesReady=false;saveQueued=false;saveInFlight=false;sessionId='';
 currentView='default';editing=false;catalogOpen=false;
}
function toast(message){const t=$('toast');t.textContent=message;t.classList.remove('hidden');clearTimeout(notifyTimeout);notifyTimeout=setTimeout(()=>t.classList.add('hidden'),3000);}
function setStatus(msg,kind=''){const x=$('status');x.textContent=msg;x.className='badge '+kind;document.dispatchEvent(new CustomEvent('cs2:status',{detail:{message:msg,kind}}));}
function setOnline(s){if(modeDemo)setStatus('Mode démo','ok');else setStatus(s?.online?'Partie connectée':s?.gsi_connected?'GSI actif · en attente de partie':'CS2 hors ligne',s?.online?'ok':'bad');$('notice').classList.toggle('hidden',!!s?.online&&!modeDemo);$('notice').textContent=modeDemo?'Données simulées':(!s?.online?'En attente de données de partie CS2.':'');document.dispatchEvent(new CustomEvent('cs2:state',{detail:{online:!!s?.online,gsi_connected:!!s?.gsi_connected,demo:modeDemo}}));}
function updateProfiles(){const x=$('profile-select');x.replaceChildren();for(const p of profiles){const o=document.createElement('option');o.value=p.id;o.textContent=p.name;x.append(o);}x.value=activeProfile;$('accent').value=profile()?.accent||COLOR;$('density').value=profile()?.density||'normal';$('delete-profile').disabled=profiles.length<=1;document.documentElement.style.setProperty('--accent',currentView==='custom'?profile()?.accent||COLOR:COLOR);}
function updateChrome(){const custom=currentView==='custom'&&!modeDemo&&profilesReady;$('tab-custom').classList.toggle('hidden',modeDemo||!profilesReady);$('tab-default').classList.toggle('active',!custom);$('tab-custom').classList.toggle('active',custom);$('tab-default').setAttribute('aria-selected',String(!custom));$('tab-custom').setAttribute('aria-selected',String(custom));$('tab-default').tabIndex=custom?-1:0;$('tab-custom').tabIndex=custom?0:-1;$('custom-tools').classList.toggle('hidden',!custom);$('edit').classList.toggle('hidden',!custom);$('add').classList.toggle('hidden',!custom);$('edit').textContent=editing?'✓ Terminer':'✎ Personnaliser';$('edit').setAttribute('aria-pressed',String(editing));$('add').disabled=!editing;$('catalog').classList.toggle('hidden',!custom||!editing||!catalogOpen);$('edit-hint').classList.toggle('hidden',!custom||!editing);updateProfiles();}
function currentWidgets(){return currentView==='default'||modeDemo||!profilesReady?DEFAULT_IDS.map((k,i)=>({id:'default'+i,kind:k,span:W[k].size,title:'',color:''})):profile().widgets;}
function makeBtn(label,tip,action){const b=document.createElement('button');b.type='button';b.textContent=label;b.title=tip;b.setAttribute('aria-label',tip);b.addEventListener('click',action);return b;}
function renderBoard(){updateChrome();const board=$('board');board.replaceChildren();const widgets=currentWidgets();board.classList.toggle('editing',currentView==='custom'&&editing);board.dataset.view=currentView;board.dataset.density=currentView==='custom'?(profile()?.density||'normal'):'normal';$('empty-board').classList.toggle('hidden',widgets.length>0);
 for(const w of widgets){const d=W[w.kind];if(!d)continue;const article=document.createElement('article');article.className='widget w-'+w.kind;article.dataset.id=w.id;article.dataset.kind=w.kind;article.style.setProperty('--span',w.span);if(w.color)article.style.setProperty('--widget-accent',w.color);if(w.background)article.style.setProperty('--widget-bg',w.background);article.style.setProperty('--widget-opacity',(w.opacity??100)+'%');article.dataset.style=w.style||'solid';
 const top=document.createElement('div');top.className='widget-top';const title=document.createElement('div');title.className='widget-heading';title.textContent=w.title||d.title;const icon=document.createElement('span');icon.className='widget-icon';icon.textContent=d.icon;top.append(title,icon);article.append(top);
 const body=document.createElement('div');body.className='widget-body';body.innerHTML=d.html;article.append(body);
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
 const b=document.createElement('button');b.className='catalog-item';b.type='button';const icon=document.createElement('div');icon.className='catalog-icon';icon.textContent=d.icon;const txt=document.createElement('div');const strong=document.createElement('strong');strong.textContent=d.title;const sm=document.createElement('small');sm.textContent=d.cat;txt.append(strong,sm);b.append(icon,txt);b.addEventListener('click',()=>{if(profile().widgets.length>=60){toast('Maximum 60 widgets par profil.');return;}profile().widgets.push(newWidget(kind));save();renderBoard();toast(d.title+' ajouté');});parent.append(b);
 }if(!parent.children.length){const x=document.createElement('div');x.textContent='Aucun widget trouvé';parent.append(x);}}
function fieldData(s){const p=s.player||{},econ=s.economy||{},b=s.bomb_timer||{},map=v(s.map).replace(/^de_/,'').toUpperCase();return{
 map,round:`Round ${v(s.round)} · ${v(s.round_phase,s.map_phase||'—')}`,round_number:isNum(s.round)?String(s.round):'—',ct:v(s.ct),t:v(s.t),map_mode:v(s.map_mode),map_phase:capitalize(s.map_phase),round_phase:capitalize(s.round_phase),round_winner:s.round_winner?'Gagnant : '+v(s.round_winner):'',
 weapon:weaponName(p.weapon),ammo_clip:v(p.ammo_clip),ammo_reserve:'/ '+v(p.ammo_reserve),money:cash(p.money),nextmoney:cash(econ.on_loss),lossbonus:isNum(econ.loss_bonus)?'Bonus de défaite +'+cash(econ.loss_bonus):'Bonus indisponible',econ_note:econ.source==='gsi'?'Bonus fourni par GSI · hors exceptions':econ.source==='history'?'Estimation à partir des manches · règles standard':'Historique insuffisant · bonus inconnu',
 kills:v(p.kills),assists:v(p.assists),deaths:v(p.deaths),kd:isNum(p.kills)&&isNum(p.deaths)?(p.kills/Math.max(1,p.deaths)).toFixed(2):'—',mvps:v(p.mvps),personal_score:v(p.score),round_kills:v(p.round_kills),round_hs:v(p.round_killhs),round_damage:v(p.round_totaldmg),
 health:v(p.health),armor:v(p.armor),equip_value:cash(p.equip_value),helmet:p.helmet===null||p.helmet===undefined?'Casque —':p.helmet?'✓ Casque':'Sans casque',kit:p.defusekit===null||p.defusekit===undefined?'Kit —':p.defusekit?'✓ Kit':'Sans kit',armor_line:'Armure : '+v(p.armor),flash:v(p.flashed),smoke:v(p.smoked),fire:v(p.burning),name:v(p.name,'Joueur'),team:v(p.team,'Équipe —'),activity:capitalize(p.activity),
 bomb_state:({planted:'Plantée',defused:'Désamorcée',exploded:'Explosée',dropped:'Au sol',planting:'Pose en cours'})[s.bomb_state]||v(s.bomb_state,'En attente'),
 connection:s.online?'Données en direct':s.gsi_connected?'GSI actif · match en attente':'Hors ligne',lastpacket:s.age_seconds!==null&&s.age_seconds!==undefined?'Dernier paquet : '+s.age_seconds+' s':'En attente de données',provider:v(s.provider?.version)
 };}
function addItem(parent,label,active=false){const el=document.createElement('div');el.className='item'+(active?' active':'');el.textContent=label;parent.append(el);}
function updateValues(){if(!last)return;const f=fieldData(last),p=last.player||{};for(const card of $('board').children){const kind=card.dataset.kind;card.querySelectorAll('[data-v]').forEach(node=>node.textContent=f[node.dataset.v]??'—');card.querySelectorAll('[data-p]').forEach(node=>{let amount=0;if(node.dataset.p==='ammo'&&isNum(p.ammo_max)&&p.ammo_max>0&&isNum(p.ammo_clip))amount=p.ammo_clip/p.ammo_max*100;if(node.dataset.p==='health')amount=p.health;if(node.dataset.p==='armor')amount=p.armor;node.style.width=pct(amount);});
 const list=card.querySelector('[data-list]');if(list){list.replaceChildren();if(list.dataset.list==='weapons'||list.dataset.list==='grenades'){
  const items=(p.weapons||[]).filter(w=>list.dataset.list==='weapons'||w.type==='Grenade'||/grenade|flashbang|molotov|incgrenade|decoy|smokegrenade/.test(w.name));if(!items.length)addItem(list,'Aucune donnée');else for(const w of items){const ammo=isNum(w.ammo_clip)&&w.type!=='Grenade'?' · '+w.ammo_clip:'';addItem(list,weaponName(w.name)+ammo,w.state==='active');}
 }else if(list.dataset.list==='wins'){const items=last.recent_wins||[];if(!items.length)addItem(list,'Historique indisponible');for(const w of items)addItem(list,`#${w.round} · ${w.winner}`);
 }else if(list.dataset.list==='events'){const items=last.events||[];if(!items.length)addItem(list,'Aucun événement enregistré');for(const evt of items.slice(0,8)){const item=document.createElement('div');item.className='item';const txt=document.createElement('span');txt.textContent=evt.message;const when=document.createElement('span');when.className='tiny';when.textContent=isNum(evt.at)?new Date(evt.at*1000).toLocaleTimeString(window.CS2I18N?.locale()==='FR'?'fr-FR':'en-US',{hour:'2-digit',minute:'2-digit',second:'2-digit'}):'';item.append(txt,when);list.append(item);}}
 }
 if(kind==='bomb'){const demoCtl=card.querySelector('[data-demo-controls]');if(demoCtl)demoCtl.classList.toggle('hidden',!modeDemo);} }
 paintBomb();}
function paintBomb(){if(!last)return;let left=null,kind='',message='En attente',timer=last.bomb_timer||{};if(timer.status==='active'&&anchor){left=Math.max(0,anchor.left-(performance.now()-anchor.at)/1000);if(left>10){kind='yellow';message='Désamorçage possible sans kit';}else if(left>5){kind='orange';message='Kit nécessaire pour commencer';}else{kind='red';message='Trop tard pour commencer';}if(left===0)message='Explosion estimée';}
 else if(timer.status==='expired'){left=0;kind='red';message='Explosion estimée';}else if(timer.status==='disabled'){message='Minuteur désactivé';}else if(timer.status==='stale')message='Données interrompues';else if(timer.status==='unknown_start')message='Heure de pose inconnue';else if(last.bomb_state==='defused')message='Bombe désamorcée';else if(last.bomb_state==='exploded')message='Bombe explosée';else message='En attente d’une pose';
 for(const card of document.querySelectorAll('.widget.w-bomb')){const clock=card.querySelector('[data-bomb-clock]'),bar=card.querySelector('[data-bomb-fill]'),msg=card.querySelector('[data-bomb-msg]');if(!clock||!bar||!msg)continue;clock.textContent=left===null?'--.- s':left.toFixed(1)+' s';clock.className='bomb-clock '+kind;bar.style.width=left===null?'0%':pct(100*left/(timer.duration||40));bar.className='bomb-fill '+kind;msg.textContent=message;}}
function renderData(s){last=s;anchor=s.bomb_timer?.status==='active'&&isNum(s.bomb_timer.remaining)?{at:performance.now(),left:s.bomb_timer.remaining}:null;$('login').classList.add('hidden');$('view').classList.remove('hidden');setOnline(s);updateValues();}
async function login(){modeDemo=false;pin=$('pin').value.trim()||pin;$('loginerror').textContent='';$('pin').setAttribute('aria-invalid','false');if(pin.length<6){$('loginerror').textContent='Code PIN trop court.';$('pin').setAttribute('aria-invalid','true');return;}if(ws){ws.onclose=null;ws.close();ws=null;}setStatus('Connexion…');
 try{const res=await fetch('/health',{cache:'no-store'});if(!res.ok)throw Error('HTTP '+res.status);const health=await res.json();if(health.version!==VERSION){$('loginerror').textContent='Redémarre Docker avec la version 1.0.0.';setStatus('Mise à jour requise','bad');return;}}
 catch(err){$('loginerror').textContent='Serveur indisponible : '+err.message;setStatus('Hors ligne','bad');return;}
 const url=(location.protocol==='https:'?'wss:':'ws:')+'//'+location.host+'/ws',socket=new WebSocket(url);ws=socket;let authorized=false,failed=false;
 socket.onopen=()=>socket.send(JSON.stringify({type:'auth',pin}));
 socket.onmessage=e=>{
  if(modeDemo||ws!==socket)return;
  let msg;
  try{msg=JSON.parse(e.data);}catch{return;}
  if(msg.type==='auth_error'){
   failed=true;
   $('loginerror').textContent=msg.message||'Code incorrect.';
   $('pin').setAttribute('aria-invalid','true');
   setStatus('PIN incorrect','bad');
   return;
  }
  if(msg.type==='auth_ok'){
   authorized=true;
   sessionId=msg.session||'';
   profilesReady=true;
   $('pin').value='';
   $('download-support').classList.remove('hidden');
   setStatus('Connecté','ok');
   document.dispatchEvent(new Event('cs2:authenticated'));
   return;
  }
  if(msg.type==='profiles_state'&&authorized){acceptServerProfiles(msg);return;}
  if(msg.type==='profiles_error'&&authorized){
   saveInFlight=false;
   saveQueued=false;
   toast(msg.code==='conflict'?tr('Profils modifiés sur un autre appareil : actualisation.'):tr('Enregistrement impossible. Vérifie le stockage du serveur.'));
   return;
  }
  if(msg.type==='diagnostics_data'&&authorized){
   const blob=new Blob([JSON.stringify(msg.report,null,2)],{type:'application/json'});
   const downloadUrl=URL.createObjectURL(blob);
   const anchor=document.createElement('a');
   anchor.href=downloadUrl;
   anchor.download='CS2_Companion_support.json';
   anchor.click();
   setTimeout(()=>URL.revokeObjectURL(downloadUrl),1000);
   return;
  }
  if(msg.type==='state'&&authorized)renderData(msg);
 };
 socket.onerror=()=>{
  if(!failed)setStatus('Erreur réseau','bad');
  document.dispatchEvent(new Event('cs2:network-error'));
 };
 socket.onclose=()=>{
  if(modeDemo||ws!==socket)return;
  saveInFlight=false;
  saveQueued=true;
  if(!authorized){
   if(!failed)$('loginerror').textContent='Impossible de se connecter au WebSocket.';
   setStatus('Déconnecté','bad');
   return;
  }
  setStatus('Reconnexion…','bad');
  document.dispatchEvent(new CustomEvent('cs2:connection-lost'));
  anchor=null;
  if(last){
   last.bomb_timer={status:'stale'};
   last.online=false;
   setOnline(last);
   paintBomb();
  }
  setTimeout(()=>{
   if(!modeDemo&&ws===socket&&socket.readyState===WebSocket.CLOSED)login();
  },3000);
 };
}
const SAMPLE={type:'state',online:true,gsi_connected:true,age_seconds:0,map:'de_mirage',map_mode:'competitive',map_phase:'live',round:14,round_phase:'live',ct:8,t:5,round_winner:'',recent_wins:[{round:10,winner:'ct_win'},{round:11,winner:'t_win'},{round:12,winner:'ct_win'}],bomb_state:'',bomb_timer:{enabled:false,status:'disabled',duration:40},economy:{on_loss:5600,loss_bonus:2400,loss_streak_known:true,source:'gsi'},events:[{message:'Élimination · 18 au total',at:Date.now()/1000,category:'kill'},{message:'Nouvelle manche · MIRAGE',at:Date.now()/1000-35,category:'round'}],provider:{version:'CS2'},player:{name:'Player',team:'CT',activity:'playing',money:3200,health:87,armor:94,helmet:true,defusekit:true,equip_value:4300,flashed:0,smoked:0,burning:0,weapon:'weapon_ak47',ammo_clip:21,ammo_max:30,ammo_reserve:90,kills:18,assists:4,deaths:11,mvps:3,score:42,round_kills:2,round_killhs:1,round_totaldmg:167,weapons:[{name:'weapon_ak47',type:'Rifle',state:'active',ammo_clip:21},{name:'weapon_usp_silencer',type:'Pistol',state:'holstered',ammo_clip:12},{name:'weapon_smokegrenade',type:'Grenade',state:'holstered'},{name:'weapon_flashbang',type:'Grenade',state:'holstered'}]}};
function demo(){clearPrivateProfiles();pin='';$('pin').value='';$('download-support').classList.add('hidden');modeDemo=true;if(ws){ws.onclose=null;ws.close();ws=null;}renderData(structuredClone(SAMPLE));}function demoBomb(n){if(!modeDemo)return;const s=structuredClone(SAMPLE);s.bomb_state=n==='stop'?'defused':'planted';s.bomb_timer=n==='stop'?{enabled:true,status:'idle',duration:40}:{enabled:true,status:'active',remaining:n,duration:40};renderData(s);}
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
$('import').addEventListener('click',()=>$('import-file').click());$('import-file').addEventListener('change',async e=>{const file=e.target.files?.[0];e.target.value='';if(!file)return;if(file.size>150000){toast('Fichier trop volumineux.');return;}try{const data=JSON.parse(await file.text());if(data.format!=='cs2-companion-layout'||![1,2].includes(data.version)||!data.profile||!Array.isArray(data.profile.widgets))throw Error('Format inconnu');if(profiles.length>=12)throw Error('Maximum 12 profils');const items=data.profile.widgets.slice(0,60).map(sanitizeWidget).filter(Boolean);const p={id:freshProfileId(),name:String(data.profile.name||'Import').slice(0,32),accent:safeColor(data.profile.accent)||COLOR,density:safeDensity(data.profile.density),widgets:items};profiles.push(p);activeProfile=p.id;editing=true;save();renderBoard();toast('Profil importé · '+items.length+' widgets');}catch(err){toast('Import impossible : '+err.message);}});
$('download-support').addEventListener('click',()=>{if(!modeDemo&&profilesReady&&ws?.readyState===WebSocket.OPEN)ws.send(JSON.stringify({type:'diagnostics_request'}));});
$('connect').addEventListener('click',login);$('pin').addEventListener('keydown',e=>{if(e.key==='Enter')login();});$('demo').addEventListener('click',demo);$('demoagain').addEventListener('click',demo);
$('board').addEventListener('click',e=>{const b=e.target.closest('[data-demo]');if(b&&modeDemo){const n=b.dataset.demo;demoBomb(n==='stop'?'stop':Number(n));}});
$('logout').addEventListener('click',()=>{clearPrivateProfiles();pin='';$('pin').value='';$('download-support').classList.add('hidden');document.dispatchEvent(new Event('cs2:logout'));modeDemo=false;if(ws){ws.onclose=null;ws.close();ws=null;}last=null;anchor=null;$('view').classList.add('hidden');$('login').classList.remove('hidden');setStatus('Non connecté');});
$('locale-select').addEventListener('change',()=>setTimeout(renderCatalog,0));
// Repaint the countdown only while it is running and the tab is visible.
setInterval(()=>{
 if(!document.hidden&&last?.bomb_timer?.status==='active')paintBomb();
},100);
initialize();
})();
