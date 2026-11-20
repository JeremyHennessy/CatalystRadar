'use strict';const assert=require('node:assert/strict'),fs=require('node:fs');const{validate,init,publishedSec}=require('./collectors.js');const data=JSON.parse(fs.readFileSync(__dirname+'/collector-status.json','utf8'));assert.equal(validate(data),data);
for(const mutate of [d=>d.collectors.push(d.collectors[0]),d=>d.collectors[1].id=d.collectors[0].id,d=>d.execution_ready=true,d=>d.collectors[0].next_run_guaranteed=true,d=>d.collectors[0].last_verified_complete_run='https://evil.test/',d=>d.collectors[0].observation_age_seconds=0,d=>d.collectors[0].accepted_records=0,d=>d.collectors[0].evidence[0].path='../secret',d=>d.collectors[2].next_configured_slot=d.as_of,d=>d.collectors[0].last_attempt=d.as_of]){const d=structuredClone(data);mutate(d);assert.throws(()=>validate(d));}
const projection={generated_at:'2026-11-18T19:26:45Z',feeds:[{name:'SEC filings',status:'snapshot_only',as_of:'2026-11-18T19:26:45Z',detail:'10/10 configured feeds; 1 discovery'}]};
assert.equal(publishedSec(projection).detail,'10/10 configured feeds; 1 discovery');
assert.throws(()=>publishedSec({...projection,generated_at:data.as_of}));
assert.throws(()=>publishedSec({...projection,feeds:[...projection.feeds,...projection.feeds]}));
class Node{constructor(){this.children=[];this.handlers={};this.hidden=false;this.textContent='';}append(...n){this.children.push(...n);}replaceChildren(...n){this.children=n;}addEventListener(k,v){this.handlers[k]=v;}}
const document=()=>{const ids={};return{ids,getElementById(id){return ids[id]??=new Node();},createElement(){return new Node();}};};const text=n=>[n.textContent,...n.children.map(text)].flat().join(' ');
(async()=>{const doc=document();let calls=0,fail=false;await init(doc,async(path,options)=>{assert.ok(['collector-status.json','app-data.json'].includes(path));assert.equal(options.cache,'no-store');assert.ok(options.signal);calls++;return{ok:!fail,json:async()=>path==='app-data.json'?projection:data};});assert.equal(calls,2);assert.match(text(doc.ids['collector-published-sec']),/10\/10 configured/);assert.equal(doc.ids['collector-list'].children.length,3);assert.match(text(doc.ids['collector-list']),/Unknown \/ unknown \/ unknown/);assert.match(doc.ids['collector-asof'].textContent,/2026-11-18T01:13:16/);assert.match(text(doc.ids['collector-list']),/2026-11-21/);assert.match(text(doc.ids['collector-list']),/2026-11-22/);fail=true;await doc.ids['collector-refresh'].handlers.click();assert.equal(doc.ids['collector-list'].hidden,true);assert.equal(doc.ids['collector-list'].children.length,0);assert.equal(doc.ids['collector-refresh'].disabled,false);assert.match(doc.ids['collector-asof'].textContent,/unknown/);fail=false;await doc.ids['collector-refresh'].handlers.click();assert.equal(calls,6);assert.equal(doc.ids['collector-list'].hidden,false);console.log('Collector snapshot semantics, validation, source bounds and refresh failure/recovery passed');})();

for(const file of ['index.html','company.html','disclosures.html']) assert.ok(fs.readFileSync(__dirname+'/'+file,'utf8').includes('href="collectors.html"'));

(async()=>{
 for(const unavailable of ['collector-status.json','app-data.json']){
  const doc=document();
  await init(doc,async path=>({ok:path!==unavailable,json:async()=>path==='app-data.json'?projection:data}));
  assert.equal(doc.ids['collector-list'].hidden,unavailable==='collector-status.json');
  assert.match(text(doc.ids['collector-published-sec']),unavailable==='app-data.json'?/unavailable or unverified/:/10\/10 configured/);
 }
})();

const {policyAt}=require('./collectors.js');
const at=s=>policyAt(Date.parse(s));
assert.deepEqual(at('2026-11-20T23:59:59.999Z'),{checked:'2026-11-20T23:59:59.999Z',sec:'CUTOFF_NOT_REACHED',prices:'CUTOFF_NOT_REACHED'});
assert.deepEqual(at('2026-11-21T00:00:00.000Z'),{checked:'2026-11-21T00:00:00.000Z',sec:'EXPIRED',prices:'CUTOFF_NOT_REACHED'});
assert.equal(at('2026-11-21T23:59:59.999Z').prices,'CUTOFF_NOT_REACHED');
assert.deepEqual(at('2026-11-22T00:00:00.000Z'),{checked:'2026-11-22T00:00:00.000Z',sec:'EXPIRED',prices:'EXPIRED'});
for(const invalid of [null,NaN,Infinity,9e15,'2026-11-20']){
 assert.deepEqual(policyAt(invalid),{checked:null,sec:'UNKNOWN',prices:'UNKNOWN'});
}
(async()=>{
 let clock=Date.parse('2026-11-20T23:59:59.999Z');
 const doc=document(),requests=[];
 await init(doc,async path=>{requests.push(path);return {ok:false};},()=>clock);
 assert.match(doc.ids['collector-policy-sec'].textContent,/Cutoff not reached/);
 assert.match(doc.ids['collector-policy-clock'].textContent,/2026-11-20T23:59:59.999Z/);
 assert.match(doc.ids['collector-state'].textContent,/Collection health.*unknown/);
 clock=Date.parse('2026-11-21T00:00:00.000Z');
 await doc.ids['collector-refresh'].handlers.click();
 assert.equal(doc.ids['collector-policy-sec'].textContent,'Expired by browser clock');
 assert.equal(doc.ids['collector-policy-prices'].textContent,'Cutoff not reached by browser clock');
 assert.deepEqual(requests,['app-data.json','collector-status.json','app-data.json','collector-status.json']);
})().catch(e=>{console.error(e);process.exitCode=1;});
