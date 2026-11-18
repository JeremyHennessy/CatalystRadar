'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),crypto=require('node:crypto'),v=require('./material-agreements');
const bytes=fs.readFileSync(__dirname+'/'+v.PATH),d=JSON.parse(bytes),clone=x=>structuredClone(x);
assert.equal(bytes.length,v.SIZE);assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'),v.SHA);assert.equal(v.validate(d),d);
assert.equal(d.packages.length,10);assert.equal(d.packages.filter(p=>p.reviewed_finding).length,1);assert.equal(d.packages.filter(p=>p.status==='NO_ITEM_1_01_HEADER_DECLARATION_NOT_NO_AGREEMENT').length,9);
const p=d.packages.find(p=>p.reviewed_finding),f=p.reviewed_finding;
assert.deepEqual(p.filers_as_reported.map(r=>r.cik),['0001770450','0000108772']);assert.equal(f.exchanged_old_notes.obligor_cik,'0001770450');assert.equal(f.new_notes.issuer_cik,'0000108772');assert.equal(f.new_notes.parent_guarantor_cik,'0001770450');assert.equal(f.equity_component.issuer_cik,'0001770450');
assert.equal(f.support_agreement_date_as_reported,'2026-10-29');assert.equal(f.exchange_agreement_date_as_reported,'2026-11-13');assert.equal(f.settlement_date_as_reported,'2026-11-13');assert.equal(f.independent_settlement_verified,false);
for(const x of [f.exchanged_old_notes.currency_iso,f.new_notes.currency_iso,f.equity_component.share_price,f.equity_component.equity_value,f.net_debt_change,f.transaction_value,f.economic_gain,p.first_public_utc])assert.equal(x,null);
const selected=x=>x.packages.find(p=>p.reviewed_finding);
for(const mutate of [x=>x.execution_ready=true,x=>x.counts.packages=9,x=>x.packages.pop(),x=>x.packages[0].first_public_utc='2026-11-13',x=>x.packages[0].event_verified=true,x=>x.packages[0].source_url='https://evil.test',x=>x.packages[0].source_url='javascript:alert(1)',x=>selected(x).reviewed_finding.new_notes.issuer_cik='0001770450',x=>selected(x).reviewed_finding.equity_component.issuer_cik='0000108772',x=>selected(x).reviewed_finding.exchanged_old_notes.currency_iso='USD',x=>selected(x).reviewed_finding.equity_component.share_price='1',x=>selected(x).reviewed_finding.net_debt_change='0',x=>selected(x).reviewed_finding.independent_settlement_verified=true,x=>selected(x).reviewed_finding.previously_announced_as_reported=false]){const bad=clone(d);mutate(bad);assert.throws(()=>v.validate(bad));}
console.log('Material agreements: exact payload,10packages/1finding/9bounded absences,distinct issuer roles/dates/nulls/safety URLs pass');
class Node{
 constructor(tag){this.tag=tag;this.children=[];this.handlers={};this.textContent='';this.style={};}
 append(...x){this.children.push(...x);}replaceChildren(...x){this.children=x;}addEventListener(k,f){this.handlers[k]=f;}setAttribute(k,v){this[k]=v;}
 set innerHTML(_){throw Error('Source fields must be rendered inertly');}
}
const text=n=>[n.textContent,...n.children.map(text)].join(' ');
(async()=>{
 const nodes=Object.fromEntries(['agreements-load','agreements-state','agreements-body'].map(k=>[k,new Node()])),doc={getElementById:k=>nodes[k],createElement:t=>new Node(t)};
 let calls=0,bad=true,delay=false,release;
 v.setup(doc,{crypto:crypto.webcrypto},async(path,opt)=>{calls++;assert.equal(path,v.PATH);assert.equal(opt.cache,'no-store');assert.ok(opt.signal);if(delay){delay=false;await new Promise(r=>{release=r;});}const b=Uint8Array.from(bytes);if(bad)b[3]^=1;return{ok:true,arrayBuffer:async()=>b.buffer};});
 const button=nodes['agreements-load'],state=nodes['agreements-state'],body=nodes['agreements-body'];assert.equal(calls,0);
 await button.handlers.click();assert.equal(calls,1);assert.equal(body.children.length,0);assert.match(state.textContent,/unavailable|unverified/i);assert.equal(button.disabled,false);
 bad=false;delay=true;const request=button.handlers.click();assert.equal(button.disabled,true);await button.handlers.click();assert.equal(calls,2);release();await request;assert.equal(button.disabled,false);
 for(const s of ['Xerox Holdings Corporation','Xerox Corporation','173,679,000','121,086,000','3,872,062','5.500','10.250','October 29, 2026','November 13, 2026'])assert.ok(text(body).includes(s),'rendered literal '+s);
 assert.match(text(body),/not.*independent|independent.*unverified/i);assert.match(text(body),/first.public/i);assert.match(text(body),/not no|not.*absence|not.*agreement/i);
 for(const row of d.packages){assert.ok(text(body).includes(row.accession),'all bounded packages visible');}
 const n=body.children.length;await button.handlers.click();assert.equal(calls,2);assert.equal(body.children.length,n);
 // Separate HTTP failure remains retryable and never establishes facts.
 const failed=Object.fromEntries(['agreements-load','agreements-state','agreements-body'].map(k=>[k,new Node()]));let attempts=0;v.setup({getElementById:k=>failed[k],createElement:t=>new Node(t)},{crypto:crypto.webcrypto},async()=>{attempts++;return{ok:false};});failed['agreements-body'].append(new Node());await failed['agreements-load'].handlers.click();assert.equal(failed['agreements-body'].children.length,0);await failed['agreements-load'].handlers.click();assert.equal(attempts,2);assert.equal(failed['agreements-load'].disabled,false);
 console.log('Material agreement mock: lazy/corrupt and HTTP retry,busy dedup,cached repeat,failure clearing,inert labels,all10packages and distinct Xerox economic roles pass');
})().catch(e=>{console.error(e);process.exitCode=1;});
const html=fs.readFileSync(__dirname+'/financial-review.html','utf8');assert.ok(html.includes('material-agreements.js?v=20261118-role-bound-evidence'));for(const id of ['agreements-load','agreements-state','agreements-body','xerox-identity'])assert.ok(html.includes(`id="${id}"`));
