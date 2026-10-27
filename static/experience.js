/* V1P-E · User experience. No extra API and no profile synchronization.
 * Diagnostics reveal only /health before authentication. Game state is used
 * only after a PIN-authenticated WebSocket (or the explicit local demo).
 */
(()=>{'use strict';
 const $=id=>document.getElementById(id);
 const els=['open-help','help-from-login','help-dialog','help-close','help-done','diagnostics-toggle','diagnostics-panel','diagnostics-refresh','session-banner','session-title','session-description','diag-http','diag-ws','diag-gsi','diag-http-icon','diag-ws-icon','diag-gsi-icon'];
 if(els.some(id=>!$(id)))return;
 const tr=s=>window.CS2I18N?.translate(s)||s;
 let fromHelp=null, socketState='disconnected', state={online:false,gsi_connected:false,demo:false},healthState='unknown', checking=false;
 function help(open){const dialog=$('help-dialog');if(open){fromHelp=document.activeElement;if(typeof dialog.showModal==='function'&&!dialog.open)dialog.showModal();else dialog.setAttribute('open','');$('help-close').focus();}else{if(typeof dialog.close==='function'&&dialog.open)dialog.close();else dialog.removeAttribute('open');if(fromHelp?.isConnected)fromHelp.focus();}}
 $('open-help').addEventListener('click',()=>help(true));$('help-from-login').addEventListener('click',()=>help(true));$('help-close').addEventListener('click',()=>help(false));$('help-done').addEventListener('click',()=>help(false));$('help-dialog').addEventListener('click',ev=>{if(ev.target===$('help-dialog'))help(false);});
 $('diagnostics-toggle').addEventListener('click',()=>{const open=$('diagnostics-panel').classList.toggle('hidden')===false;$('diagnostics-toggle').setAttribute('aria-expanded',String(open));if(open)checkHealth();});
 $('diagnostics-refresh').addEventListener('click',()=>checkHealth());
 const icon=(id,ok)=>{$(id).textContent=ok===true?'✓':ok===false?'×':'○';$(id).className=ok===true?'diag-success':ok===false?'diag-failure':'diag-unknown';};
 function render(){
  const title=$('session-title'),description=$('session-description'),banner=$('session-banner');
  let kind='waiting',heading='En attente de CS2',summary='La connexion est établie, mais les données de partie ne sont pas encore disponibles.';
  if(state.demo){kind='demo';heading='Mode démo';summary='Exemples simulés. Aucune donnée CS2 réelle n’est utilisée.';}
  else if(socketState==='connecting'){kind='waiting';heading='Connexion en cours';summary='Connexion au serveur Companion…';}
  else if(socketState==='lost'||socketState==='error'){kind='error';heading='Connexion interrompue';summary='Le dashboard tente de se reconnecter. Vérifie Docker et ton réseau.';}
  else if(socketState!=='authenticated'){kind='waiting';heading='Connexion au serveur';summary='Entre ton PIN pour recevoir les données du jeu.';}
  else if(state.online){kind='live';heading='CS2 connecté';summary='Les données de la partie sont reçues en direct.';}
  else if(state.gsi_connected){kind='waiting';heading='GSI actif, partie en attente';summary='CS2 communique avec le serveur. Lance une partie ou un entraînement pour afficher les données.';}
  banner.dataset.state=kind;title.textContent=tr(heading);description.textContent=tr(summary);
  const visible=!$('view').classList.contains('hidden');
  if(!visible)return;
  $('diag-http').textContent=tr(healthState==='ok'?'Serveur disponible':healthState==='bad'?'Serveur inaccessible':'Non vérifié');icon('diag-http-icon',healthState==='ok'?true:healthState==='bad'?false:null);
  $('diag-ws').textContent=tr(state.demo?'Mode démo (sans connexion)':socketState==='authenticated'?'Authentifiée et active':socketState==='lost'?'Reconnexion en cours':socketState==='error'?'Connexion impossible':socketState==='connecting'?'Connexion en cours':'Non connectée');icon('diag-ws-icon',state.demo?null:socketState==='authenticated'?true:['lost','error'].includes(socketState)?false:null);
  $('diag-gsi').textContent=tr(state.demo?'Données simulées':state.online?'Données de partie en direct':state.gsi_connected?'Signal GSI reçu, partie en attente':'Aucune donnée récente de CS2');icon('diag-gsi-icon',state.demo?null:state.online?true:state.gsi_connected?null:false);
 }
 async function checkHealth(){if(checking)return;checking=true;const btn=$('diagnostics-refresh');btn.disabled=true;
   try{const r=await fetch('/health',{cache:'no-store',credentials:'same-origin',signal:AbortSignal.timeout(5000)});if(!r.ok)throw Error('health');const d=await r.json();healthState=d?.service==='ok'?'ok':'bad';}catch{healthState='bad';}
   checking=false;btn.disabled=false;render();
 }
 document.addEventListener('cs2:status',ev=>{
  // Use machine-readable state rather than parsing translated display text.
  const code=ev.detail?.code;
  if(code==='connecting')socketState='connecting';
  else if(code==='error')socketState='error';
  else if(code==='lost')socketState='lost';
  render();
 });
 document.addEventListener('cs2:authenticated',()=>{socketState='authenticated';healthState='ok';render();});
 document.addEventListener('cs2:state',ev=>{state={online:!!ev.detail?.online,gsi_connected:!!ev.detail?.gsi_connected,demo:!!ev.detail?.demo};if(state.demo)socketState='demo';else if(socketState!=='error'&&socketState!=='lost')socketState='authenticated';render();});
 document.addEventListener('cs2:connection-lost',()=>{socketState='lost';state.online=false;render();});
 document.addEventListener('cs2:network-error',()=>{socketState='error';render();});
 document.addEventListener('cs2:logout',()=>{state={online:false,gsi_connected:false,demo:false};socketState='disconnected';render();});
 // Native keyboard tab navigation, independent of the widget drag controls.
 const tabs=[$('tab-default'),$('tab-custom')];tabs.forEach((tab,i)=>tab.addEventListener('keydown',e=>{
  let next=null;if(e.key==='ArrowRight'||e.key==='ArrowDown')next=tabs[(i+1)%tabs.length];
  if(e.key==='ArrowLeft'||e.key==='ArrowUp')next=tabs[(i+tabs.length-1)%tabs.length];
  if(e.key==='Home')next=tabs[0];if(e.key==='End')next=tabs.at(-1);
  if(next){e.preventDefault();next.click();next.focus();}
 }));
 // Repaint new status labels when the existing EN/FR preference changes.
 $('locale-select').addEventListener('change',()=>queueMicrotask(render));
 render();
})();
