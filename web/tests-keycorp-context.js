'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),crypto=require('node:crypto'),v=require('./keycorp-context');
const bytes=fs.readFileSync(__dirname+'/'+v.PATH),d=JSON.parse(bytes),clone=x=>structuredClone(x);
assert.equal(bytes.length,v.SIZE);assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'),v.SHA);assert.equal(v.validate(d),d);
const bucket=(crypto.createHash('sha256').update(d.cusip_as_reported).digest()[0]%64).toString(16).padStart(2,'0');
const series=JSON.parse(fs.readFileSync(__dirname+`/settlement/ftd-directory-v1/shard-${bucket}.json`)).series.find(s=>s.cusip_as_reported===d.cusip_as_reported);
v.match(d,series);assert.equal(series.observations.length,4);
for(const r of d.ftd_exact_cusip_records){const o=series.observations.find(o=>o.source_row.sqlite_rowid===r.source_rowid);assert.ok(o);assert.equal(o.settlement_date_as_reported.replaceAll('-',''),r.settlement_date_as_reported);assert.equal(o.symbol_as_reported,r.symbol_as_reported);assert.equal(o.description_as_reported,r.description_as_reported);assert.equal(o.source_row.full_six_field_canonical_sha256,r.full_source_row_sha256);}
assert.equal(d.holdings_exact_cusip_records.length,2);assert.ok(d.holdings_exact_cusip_records.some(r=>r.class_as_reported==='Common Stock'));assert.equal(d.notice_status,'INTENTION_TO_REDEEM_NOT_VERIFIED_COMPLETION');
for(const mutate of [x=>x.execution_ready=true,x=>x.historical_mapping_verified=true,x=>x.class_labels_corrected=true,x=>x.current_security_identity_verified=true,x=>x.redemption_completion_verified=true,x=>x.provenance.first_public_utc='2026-11-13',x=>x.cusip_as_reported='493267108',x=>x.notice_status='COMPLETED',x=>x.ftd_exact_cusip_records.pop(),x=>x.holdings_exact_cusip_records.pop(),x=>x.source_url='https://evil.test',x=>x.links_constructed_not_fetched_this_audit=false]){const bad=clone(d);mutate(bad);assert.throws(()=>v.validate(bad));}
for(const mutate of [x=>x.cusip_as_reported='493267108',x=>x.observations.pop(),x=>x.observations[0].settlement_date_as_reported='2026-10-15',x=>x.observations[0].symbol_as_reported='KEY',x=>x.observations[0].description_as_reported='COMMON',x=>x.observations[0].source_row.sqlite_rowid++,x=>x.observations[0].source_row.full_six_field_canonical_sha256='0'.repeat(64)]){const bad=clone(series);mutate(bad);assert.throws(()=>v.match(d,bad));}
console.log('KeyCorp context: payload pin, all four exact FTD associations, two13F labels and unresolved-identity safeguards pass');
class Node{
 constructor(tag){this.tag=tag;this.children=[];this.handlers={};this.textContent='';this.style={};}
 append(...x){this.children.push(...x);}replaceChildren(...x){this.children=x;}addEventListener(k,f){this.handlers[k]=f;}setAttribute(k,v){this[k]=v;}
 set innerHTML(_){throw Error('Source text must not be interpreted as HTML');}
}
const doc={createElement:t=>new Node(t)},text=n=>[n.textContent,...n.children.map(text)].join(' ');
(async()=>{
 const originalSeries=JSON.stringify(series);
 let calls=0,bad=true,delay=false,release;
 const app=v.create(doc,{crypto:crypto.webcrypto},async(path,opt)=>{calls++;assert.equal(path,v.PATH);assert.equal(opt.cache,'no-store');assert.ok(opt.signal);if(delay){delay=false;await new Promise(r=>{release=r;});}const b=Uint8Array.from(bytes);if(bad)b[3]^=1;return{ok:true,arrayBuffer:async()=>b.buffer};});
 const wrong=new Node();assert.equal(app.mount(wrong,{...series,cusip_as_reported:'493267108'}),undefined);assert.equal(wrong.children.length,0);assert.equal(calls,0);
 const source=clone(series),root=new Node(),box=app.mount(root,source),button=box.children[1],state=box.children[2],body=box.children[3];assert.equal(calls,0);
 await button.handlers.click();assert.equal(calls,1);assert.equal(body.children.length,0);assert.match(state.textContent,/unavailable or association unverified/);assert.equal(button.disabled,false);
 bad=false;delay=true;const first=button.handlers.click();assert.equal(button.disabled,true);await button.handlers.click();assert.equal(calls,2);
 const secondBox=app.mount(new Node(),clone(series));const second=secondBox.children[1].handlers.click();assert.equal(calls,2);release();await Promise.all([first,second]);assert.equal(button.disabled,false);
 assert.match(state.textContent,/Historical mapping, class correction and completed redemption remain unverified/);
 assert.match(text(body),/Class as reported: Common Stock/);assert.match(text(body),/Preserved, not corrected/);assert.match(text(body),/intention to redeem/);assert.match(text(body),/first-public time unknown/);assert.match(text(body),/not backdated to June or October/);
 for(const r of d.ftd_exact_cusip_records){assert.ok(text(body).includes(String(r.source_rowid)));assert.ok(text(body).includes(r.full_source_row_sha256));}
 for(const r of d.holdings_exact_cusip_records){assert.ok(text(body).includes(r.name_as_reported));assert.ok(text(body).includes(r.class_as_reported));assert.ok(text(body).includes(r.full_source_row_sha256));}
 const count=body.children.length;await button.handlers.click();assert.equal(calls,2);assert.equal(body.children.length,count);
 // Matching is rechecked even when the annotation payload is cached.
 source.observations[0].symbol_as_reported='KEY';await button.handlers.click();assert.equal(calls,2);assert.equal(body.children.length,0);assert.match(state.textContent,/No issuer or class mapping established/);
 source.observations[0].symbol_as_reported=series.observations[0].symbol_as_reported;await button.handlers.click();assert.equal(calls,2);assert.match(state.textContent,/context verified against four source rows/);
 let attempts=0;const network=v.create(doc,{crypto:crypto.webcrypto},async()=>{attempts++;return{ok:false};}),net=network.mount(new Node(),series);await net.children[1].handlers.click();await net.children[1].handlers.click();assert.equal(attempts,2);assert.equal(net.children[3].children.length,0);assert.equal(net.children[1].disabled,false);
 assert.equal(JSON.stringify(series),originalSeries); // Source balances are never mutated by rendering.
 console.log('KeyCorp mock: lazy exact-CUSIP eligibility, corrupt/network retry, shared pending/busy guard, cache join recheck and mismatch clearing, text-only labels and retrospective caveats pass');
})().catch(e=>{console.error(e);process.exitCode=1;});

const html=fs.readFileSync(__dirname+'/datasets.html','utf8');const contextScript=html.indexOf('keycorp-context.js'),directoryScript=html.indexOf('ftd-directory.js?v=20261118-retrospective-context');assert.ok(contextScript>=0&&directoryScript>contextScript,'context module must load before refreshed directory integration');
