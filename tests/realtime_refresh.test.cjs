const assert=require("node:assert/strict");
const fs=require("node:fs");
const vm=require("node:vm");
const code=fs.readFileSync("web/realtime-refresh.js","utf8");
function setup(){
 const scope={location:{protocol:"https:",host:"capitalbridge.co.ls",hostname:"capitalbridge.co.ls"}};
 scope.window=scope;scope.globalThis=scope;
 vm.runInNewContext(code,scope);
 return scope;
}
const scope=setup();
const emitted=[],urls=[],timers=[];
let ws;
const sub=scope.CapitalBridgeRealtime.subscribe({
 companyId:"22222222-2222-4222-8222-222222222222",
 onInvalidate:x=>emitted.push(x),
 socketFactory:url=>{urls.push(url);ws={close(){},onopen:null,onmessage:null,onclose:null};return ws;},
 schedule:(fn,ms)=>{timers.push({fn,ms});return timers.length;},
 cancel:()=>{}
});
assert.equal(urls[0],"wss://capitalbridge.co.ls/api/v1/companies/22222222-2222-4222-8222-222222222222/realtime/ws");
ws.onopen();
assert.deepEqual(emitted,["resynchronise"]);
ws.onmessage({data:JSON.stringify({type:"finance.changed",company_id:"other",event_id:"1"})});
assert.deepEqual(emitted,["resynchronise"]);
const notice={type:"finance.changed",company_id:"22222222-2222-4222-8222-222222222222",event_id:"abc"};
ws.onmessage({data:JSON.stringify(notice)});
ws.onmessage({data:JSON.stringify(notice)});
assert.deepEqual(emitted,["resynchronise","finance.changed"]);
ws.onclose();assert.equal(timers.length,1);sub.stop();
ws.onmessage({data:JSON.stringify({...notice,event_id:"after-stop"})});
assert.deepEqual(emitted,["resynchronise","finance.changed"]);

assert.throws(()=>scope.CapitalBridgeRealtime.subscribe({companyId:"bad",onInvalidate() {}}));
console.log("Realtime client tests passed");
