/* Behavioral profile synchronization checks; no browser or personal data. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('static/studio.js', 'utf8');
const start = source.indexOf('// Server is authoritative');
const end = source.indexOf('function toast(');
function harness(){
 const elements=new Map();
 const context=vm.createContext({structuredClone,JSON,WebSocket:{OPEN:1},
   setTimeout:()=>1,clearTimeout:()=>{},confirm:()=>true,tr:x=>x,
   $:id=>{if(!elements.has(id))elements.set(id,{hidden:false,textContent:''});return elements.get(id);},
   renderBoard:()=>{},newProfile:()=>({}),modeDemo:false,profilesReady:true,
   profilesRevision:1,sessionId:'a',saveTimer:null,saveInFlight:false,saveQueued:false,
   profiles:[{id:'p',name:'local'}],activeProfile:'p',currentView:'custom',
   editing:false,catalogOpen:false,ws:{readyState:1,send:raw=>context.sent.push(JSON.parse(raw))},sent:[]});
 vm.runInContext(source.slice(start,end),context);
 return {run:code=>vm.runInContext(code,context),context};
}
const snapshot=(revision,name,source=null)=>({revision,source,activeProfile:'p',profiles:[{id:'p',name}]});
{
 const h=harness();h.run('save();flushSave()');
 assert.equal(h.context.sent.length,1);
 h.run('profiles[0].name="newer";save()');
 h.context.msg=snapshot(2,'local','a');h.run('acceptServerProfiles(msg)');
 assert.equal(h.context.sent.length,2);
 assert.equal(h.context.sent[1].document.profiles[0].name,'newer');
 assert.equal(h.context.sent[1].revision,2);
 h.context.msg=snapshot(3,'newer','a');h.run('acceptServerProfiles(msg)');
 assert.equal(h.run('saveInFlight||saveQueued'),false);
}
{
 const h=harness();h.run('save()');h.context.msg=snapshot(2,'remote','b');
 h.run('acceptServerProfiles(msg);flushSave()');
 assert.equal(h.context.sent.length,0);
 assert.equal(h.run('profiles[0].name'),'local');
 assert.equal(h.run('saveBlocked'),true);
 h.run('resolveSave(true)');
 assert.equal(h.context.sent[0].revision,2);
 assert.equal(h.context.sent[0].document.profiles[0].name,'local');
}
{
 const h=harness();h.run('save()');h.context.msg=snapshot(5,'remote');
 h.run('acceptServerProfiles(msg);resolveSave(false)');
 assert.equal(h.run('profiles[0].name'),'remote');
 assert.equal(h.context.sent.length,0);
 assert.equal(h.run('saveQueued||saveBlocked'),false);
}
{
 const h=harness();h.run('save()');h.context.ws.send=()=>{throw Error('closed');};
 h.run('flushSave()');
 assert.equal(h.run('saveQueued&&saveBlocked&&!saveInFlight'),true);
 h.context.msg=snapshot(1,'after-restart');h.run('acceptServerProfiles(msg)');
 assert.equal(h.run('profiles[0].name'),'local');
 h.run('clearPrivateProfiles()');
 assert.equal(h.run('profiles.length'),0);
 assert.equal(h.run('latestServerProfiles'),null);
}
console.log('OK: queued edits, acknowledgements, concurrent conflict, explicit resolution, send failure and privacy reset');
