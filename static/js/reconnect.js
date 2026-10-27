/* Retry transport failures until explicitly stopped; stale attempts are ignored. */
(()=>{
 'use strict';
 window.CS2Reconnect=({connect,schedule=setTimeout,cancel=clearTimeout})=>{
  let generation=0,active=false,timer=null,failures=0;
  const current=token=>active&&generation===token;
  function retry(token){
   if(!current(token)||timer!==null)return;
   const delay=Math.min(15000,1000*2**Math.min(failures++,4));
   timer=schedule(()=>{timer=null;return run(token);},delay);
  }
  async function run(token){
   if(!current(token))return;
   try{await connect(()=>current(token));}
   catch{retry(token);}
  }
  function stop(){active=false;generation++;if(timer!==null)cancel(timer);timer=null;}
  return {
   start(){stop();active=true;failures=0;return run(generation);},
   failed(){retry(generation);},
   connected(){failures=0;},
   stop
  };
 };
})();
