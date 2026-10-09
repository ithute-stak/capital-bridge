const assert=require("node:assert/strict");
const fs=require("node:fs"),vm=require("node:vm");
const source=fs.readFileSync("web/realtime-refresh.js","utf8");
const company="22222222-2222-4222-8222-222222222222";
const other="33333333-3333-4333-8333-333333333333";
const scope={location:{protocol:"https:",host:"capitalbridge.co.ls",hostname:"capitalbridge.co.ls"}};
scope.window=scope;scope.globalThis=scope;vm.runInNewContext(source,scope);
const sockets=[],timers=[],emitted=[];
const sub=scope.CapitalBridgeRealtime.subscribe({
 companyId:company,onInvalidate:type=>emitted.push(type),
 socketFactory:url=>{const ws={url,close(){},onopen:null,onmessage:null,onclose:null};sockets.push(ws);return ws;},
 schedule:(fn,ms)=>{timers.push({fn,ms});return timers.length;},cancel:()=>{}
});
const first=sockets[0];
first.onopen();
first.onclose();
assert.equal(timers.length,1);
assert.equal(timers[0].ms,1000);
timers.shift().fn();
const second=sockets[1];
second.onopen();
assert.deepEqual(emitted,["resynchronise","resynchronise"]);
first.onmessage({data:JSON.stringify({type:"finance.changed",company_id:company,event_id:"stale"})});
assert.deepEqual(emitted,["resynchronise","resynchronise"]);
second.onmessage({data:JSON.stringify({type:"finance.changed",company_id:other,event_id:"foreign"})});
assert.deepEqual(emitted,["resynchronise","resynchronise"]);
second.onmessage({data:JSON.stringify({type:"finance.changed",company_id:company,event_id:"new"})});
assert.deepEqual(emitted,["resynchronise","resynchronise","finance.changed"]);
sub.stop();
second.onmessage({data:JSON.stringify({type:"finance.changed",company_id:company,event_id:"stopped"})});
assert.equal(emitted.length,3);
console.log("Reconnect isolation and missed-event resynchronisation tests passed");
