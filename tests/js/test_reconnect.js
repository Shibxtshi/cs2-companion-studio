/* Retry behavior without timers, network or private fixtures. */
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const context=vm.createContext({window:{},setTimeout,clearTimeout});
vm.runInContext(fs.readFileSync('static/js/reconnect.js','utf8'),context);
async function main(){
 let calls=0,pending=[],cancelled=[];
 const retry=context.window.CS2Reconnect({
  connect:async()=>{calls++;if(calls<3)throw Error('offline');},
  schedule:(fn,delay)=>{pending.push({fn,delay});return pending.length;},
  cancel:id=>cancelled.push(id)
 });
 await retry.start();assert.equal(calls,1);
 assert.equal(pending[0].delay,1000);
 await pending.shift().fn();assert.equal(calls,2);
 assert.equal(pending[0].delay,2000);
 await pending.shift().fn();assert.equal(calls,3);assert.equal(pending.length,0);
 retry.connected();retry.failed();assert.equal(pending[0].delay,1000);
 const late=pending.shift().fn;retry.stop();await late();assert.equal(calls,3);
 let release,created=0;
 const stale=context.window.CS2Reconnect({connect:async current=>{await new Promise(r=>release=r);if(current())created++;}});
 const running=stale.start();stale.stop();release();await running;assert.equal(created,0);
 console.log('OK: repeated outages, progressive delay, recovery, reset and cancellation');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
