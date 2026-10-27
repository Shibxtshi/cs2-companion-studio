/* Behavioral tests of profile synchronization using its public controller API. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
function harness(){
 const context=vm.createContext({window:{},structuredClone,setTimeout:()=>1,clearTimeout:()=>{}});
 vm.runInContext(fs.readFileSync('static/js/profile-sync.js','utf8'),context);
 let document={activeProfile:'p',profiles:[{id:'p',name:'local'}]};
 const sent=[],states=[];
 const api=context.window.CS2ProfileSync({getDocument:()=>document,applyDocument:msg=>{document=structuredClone(msg);},
  canSave:()=>true,send:cmd=>sent.push(structuredClone(cmd)),onStatus:code=>states.push(code)});
 api.authenticate('a');
 return {api,sent,states,get document(){return document;}};
}
const snapshot=(revision,name,source=null)=>({revision,source,activeProfile:'p',profiles:[{id:'p',name}]});
{
 const h=harness();h.api.changed();h.api.flush();
 h.document.profiles[0].name='newer';h.api.changed();
 h.api.receive(snapshot(2,'local','a'));
 assert.equal(h.sent.length,2);assert.equal(h.sent[1].document.profiles[0].name,'newer');assert.equal(h.sent[1].revision,2);
 h.api.receive(snapshot(3,'newer','a'));assert.equal(h.api.dirty,false);
}
{
 const h=harness();h.api.changed();h.api.receive(snapshot(2,'remote','b'));h.api.flush();
 assert.equal(h.sent.length,0);assert.equal(h.document.profiles[0].name,'local');assert.equal(h.api.resolvable,true);
 h.api.resolve(true);assert.equal(h.sent[0].revision,2);assert.equal(h.sent[0].document.profiles[0].name,'local');
}
{
 const h=harness();h.api.changed();h.api.receive(snapshot(5,'remote'));h.api.resolve(false);
 assert.equal(h.document.profiles[0].name,'remote');assert.equal(h.sent.length,0);assert.equal(h.api.dirty,false);
}
{
 const h=harness();h.api.receive(snapshot(10,'initial'));h.api.changed();h.api.flush();
 h.api.disconnected();assert.equal(h.api.dirty,true);assert.equal(h.api.resolvable,false);
 h.api.resolve(true);assert.equal(h.sent.length,1);
 h.api.authenticate('new-session');h.api.receive(snapshot(1,'after-restart'));
 assert.equal(h.document.profiles[0].name,'initial');assert.equal(h.api.resolvable,true);
 h.api.resolve(true);assert.equal(h.sent[1].revision,1);
 h.api.failed('disk');assert.equal(h.api.dirty,true);assert.equal(h.api.status,'error');
 h.api.clear();assert.equal(h.api.dirty,false);assert.equal(h.api.resolvable,false);
}
{
 const h=harness();h.api.disconnected();h.api.authenticate('new-session');h.api.receive(snapshot(2,'remote'));
 assert.equal(h.api.dirty,false);assert.equal(h.document.profiles[0].name,'remote');
}
console.log('OK: queued edits, conflicts, explicit resolution, reconnect revision reset, disk failure and privacy reset');
