'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),crypto=require('node:crypto'),v=require('./manager-difference');
const bytes=fs.readFileSync(__dirname+'/'+v.PATH),d=JSON.parse(bytes),clone=x=>structuredClone(x);
assert.equal(bytes.length,v.SIZE);assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'),v.SHA);assert.equal(v.validate(d),d);
const manager=JSON.parse(fs.readFileSync(__dirname+`/holdings/manager-directory-v1/shard-${(Number(d.manager_cik)%16).toString(16)}.json`)).managers.find(m=>m.manager_cik===d.manager_cik);
v.match(d,manager);
assert.equal(d.comparison.earlier_only.length,4);assert.equal(d.comparison.later_only.length,13);assert.equal(d.comparison.common_literal_keys,168);
for(const group of [...d.comparison.earlier_only,...d.comparison.later_only])for(const row of group.source_rows){assert.deepEqual(group.key,d.comparison.key_fields.map(k=>row[k]));assert.equal(row.security_identity_verified,false);for(const k of ['VALUE','SSHPRNAMT','PHONE','FILINGMANAGER_STREET1','issuer_cik'])assert.ok(!(k in row));assert.ok(row.source_data_row>0);}
for(const mutate of [x=>x.execution_ready=true,x=>x.first_public_utc='2026-08-07',x=>x.manager_cik='0000000001',x=>x.comparison.economic_changes_qualified=true,x=>x.comparison.common_literal_keys++,x=>x.comparison.later_only.pop(),x=>x.comparison.earlier_only[0].key[0]='wrong',x=>x.comparison.earlier_only[0].source_rows[0].VALUE='123',x=>x.comparison.earlier_only[0].source_rows[0].security_identity_verified=true,x=>x.filings[0].source_url='https://evil.test',x=>x.filings[0].row_count=1,x=>x.filings[0].confidential_omitted_as_filed='Y',x=>x.filings.reverse()]){const bad=clone(d);mutate(bad);assert.throws(()=>v.validate(bad));}
for(const mutate of [m=>m.manager_cik='0000000001',m=>m.filings.pop(),m=>m.filings[0].report_period_as_filed='2025-03-31',m=>m.filings[0].filing_date_as_filed='2026-08-08',m=>m.filings[0].source_rows.cover++,m=>m.filings[0].amendment_flag_as_filed='Y',m=>m.filings[0].confidential_omitted_as_filed='Y']){const bad=clone(manager);mutate(bad);assert.throws(()=>v.match(d,bad));}
console.log('Manager difference: exact artifact pin,17 literal keys/source fields, safety corruption and directory join mismatches passed');
class Node{
 constructor(tag){this.tag=tag;this.children=[];this.handlers={};this.textContent='';this.disabled=false;}
 append(...x){this.children.push(...x);}replaceChildren(...x){this.children=x;}addEventListener(k,f){this.handlers[k]=f;}setAttribute(k,v){this[k]=v;}
 set innerHTML(_){throw Error('HTML interpretation forbidden in source rendering');}
}
const doc={createElement:tag=>new Node(tag)},text=n=>[n.textContent,...n.children.map(text)].join(' ');
(async()=>{
 let calls=0,bad=true,delay=false,release;
 const app=v.create(doc,{crypto:crypto.webcrypto},async(path,opt)=>{calls++;assert.equal(path,v.PATH);assert.equal(opt.cache,'no-store');assert.ok(opt.signal);if(delay){delay=false;await new Promise(r=>{release=r;});}const b=Uint8Array.from(bytes);if(bad)b[3]^=1;return{ok:true,arrayBuffer:async()=>b.buffer};});
 const wrong=new Node();assert.equal(app.mount(wrong,{...manager,manager_cik:'0000000001'}),undefined);assert.equal(wrong.children.length,0);
 const missing=new Node();assert.equal(app.mount(missing,{...manager,filings:manager.filings.slice(0,1)}),undefined);assert.equal(missing.children.length,0);assert.equal(calls,0);
 const source=clone(manager),root=new Node(),box=app.mount(root,source),button=box.children[1],state=box.children[2],body=box.children[3];assert.equal(calls,0);
 await button.handlers.click();assert.equal(calls,1);assert.match(state.textContent,/unavailable or source association unverified/);assert.equal(body.children.length,0);assert.equal(button.disabled,false);
 bad=false;delay=true;const first=button.handlers.click();assert.equal(calls,2);assert.equal(button.disabled,true);await button.handlers.click();assert.equal(calls,2);
 const otherRoot=new Node(),otherBox=app.mount(otherRoot,clone(manager));const concurrent=otherBox.children[1].handlers.click();assert.equal(calls,2);release();await Promise.all([first,concurrent]);
 assert.equal(button.disabled,false);assert.match(state.textContent,/Verified saved literal comparison/);assert.match(text(body),/4 earlier-only keys.*13 later-only keys.*168 common literal keys/);
 assert.match(text(body),/Blank \/ unknown/);assert.match(text(body),/not bought, sold, opened or closed positions/);assert.match(text(body),/not newly fetched or verified/);
 for(const group of [...d.comparison.earlier_only,...d.comparison.later_only])for(const row of group.source_rows){assert.ok(text(body).includes(row.NAMEOFISSUER+' · source label only'));assert.ok(text(body).includes(String(row.source_data_row)));for(const key of group.key.filter(Boolean))assert.ok(text(body).includes(key));}
 const originalChildren=body.children.length;await button.handlers.click();assert.equal(calls,2);assert.equal(body.children.length,originalChildren);
 // Cached data still requires fresh exact directory association before every render.
 source.filings[0].source_rows.cover++;await button.handlers.click();assert.equal(calls,2);assert.equal(body.children.length,0);assert.match(state.textContent,/source association unverified/);
 source.filings[0].source_rows.cover--;await button.handlers.click();assert.equal(calls,2);assert.match(state.textContent,/Verified saved literal comparison/);
 const mismatch=clone(manager);mismatch.filings[0].report_period_as_filed='2025-03-31';const failBox=app.mount(new Node(),mismatch);await failBox.children[1].handlers.click();assert.equal(failBox.children[3].children.length,0);assert.match(failBox.children[2].textContent,/source association unverified/);
 // Independent response failure never establishes coverage and can be retried.
 let networkCalls=0;const networkApp=v.create(doc,{crypto:crypto.webcrypto},async()=>{networkCalls++;return{ok:false};}),networkBox=networkApp.mount(new Node(),manager);await networkBox.children[1].handlers.click();await networkBox.children[1].handlers.click();assert.equal(networkCalls,2);assert.equal(networkBox.children[3].children.length,0);assert.equal(networkBox.children[1].disabled,false);
 console.log('Manager difference mock: lazy eligibility, corruption/network retry, busy dedup and shared pending, cache revalidation, mismatch clearing and text-only17-key rendering passed');
})().catch(e=>{console.error(e);process.exitCode=1;});
