/* Profile synchronization controller. Private drafts remain in memory only. */
(()=>{
 'use strict';
 window.CS2ProfileSync = function({getDocument,applyDocument,canSave,send,onStatus}){
  let revision=0,session='',timer=null,inFlight=false,queued=false,blocked=false,latest=null,status='';
  function notify(code){status=code;onStatus(code,{resolvable:blocked&&!!latest});}
  function flush(){
   if(!queued||inFlight||blocked||!canSave())return;
   inFlight=true;queued=false;notify('saving');
   try{send({type:'profiles_save',revision,document:getDocument()});}
   catch{inFlight=false;queued=true;blocked=true;notify('disconnected');}
  }
  function changed(){
   queued=true;clearTimeout(timer);notify(blocked?'choose':'pending');
   if(!inFlight&&!blocked)timer=setTimeout(flush,180);
  }
  function receive(message){
   if(!session)return;
   latest=structuredClone(message);
   if(message.source===session&&inFlight){
    revision=message.revision;inFlight=false;
    if(queued)flush();else{applyDocument(message);notify('');}
    return;
   }
   if(inFlight)return;
   if(queued||blocked){blocked=true;notify('conflict');return;}
   revision=message.revision;applyDocument(message);notify('');
  }
  function failed(code){
   inFlight=false;queued=true;blocked=true;
   notify(code==='conflict'?'conflict':'error');
  }
  function disconnected(){
   const pending=inFlight||queued;
   inFlight=false;queued=pending;blocked=pending||blocked;
   // Never offer a stale snapshot while waiting for a new authenticated connection.
   latest=null;
   if(pending)notify('disconnected');
  }
  function resolve(useLocal){
   if(!latest||inFlight)return;
   blocked=false;revision=latest.revision;
   if(useLocal){queued=true;flush();}
   else{queued=false;applyDocument(latest);notify('');}
  }
  function clear(){
   clearTimeout(timer);revision=0;session='';inFlight=false;queued=false;
   blocked=false;latest=null;notify('');
  }
  return {changed,flush,receive,failed,disconnected,resolve,clear,
   authenticate:id=>{session=id;},
   get dirty(){return queued||inFlight||blocked;},
   get status(){return status;},
   get resolvable(){return blocked&&!!latest;}};
 };
})();
