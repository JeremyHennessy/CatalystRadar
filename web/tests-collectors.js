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
