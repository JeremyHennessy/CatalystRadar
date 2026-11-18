'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),crypto=require('node:crypto'),v=require('./ftd-directory');
const wc=crypto.webcrypto,hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const bytes=fs.readFileSync(__dirname+'/'+v.PATH+'index.json'),index=JSON.parse(bytes),clone=x=>structuredClone(x);
(async()=>{
assert.equal(bytes.length,v.SIZE);assert.equal(hash(bytes),v.SHA);await v.validateIndex(index,wc);
let rows=0,cusips=0;const all=[];
for(const [bucket,ref] of Object.entries(index.shards)){
 const b=fs.readFileSync(__dirname+'/settlement/ftd-directory-v1/'+ref.path),d=JSON.parse(b);
 assert.equal(b.length,ref.bytes);assert.equal(hash(b),ref.sha256);await v.validateShard(d,bucket,index,wc);
 assert.equal(d.series.length,ref.cusips);
 for(const s of d.series){assert.equal(await v.bucket(s.cusip_as_reported,wc),bucket);rows+=s.observations.length;cusips++;all.push(s);const axis=v.axis(s,index.settlement_dates_as_reported);assert.equal(axis.length,12);assert.equal(axis.filter(x=>x.status==='NO_SOURCE_ROW').length,12-s.observations.length);for(const a of axis.filter(x=>x.status==='NO_SOURCE_ROW'))assert.equal(a.outstanding_fail_shares_as_reported,null);}
}
assert.equal(rows,63157);assert.equal(cusips,13097);
for(const mutation of [x=>x.execution_ready=true,x=>x.short_interest=0,x=>x.cross_date_balance_sum=1,x=>x.current_security_identity_verified=true,x=>x.counts.source_rows++,x=>x.entries.reverse(),x=>x.entries[0][1]++,x=>x.shards['00'].path='../secret.json',x=>x.provenance.first_public_utc='2026-10-15',x=>x.settlement_dates_as_reported.reverse()]){
 const d=clone(index);mutation(d);await assert.rejects(()=>v.validateIndex(d,wc));
}
const bucket=await v.bucket(all[0].cusip_as_reported,wc),original=JSON.parse(fs.readFileSync(__dirname+'/settlement/ftd-directory-v1/'+index.shards[bucket].path));
for(const mutation of [x=>x.bucket='ff',x=>x.series.reverse(),x=>x.series.pop(),x=>x.series[0].reported_observations++,x=>x.series[0].cusip_as_reported='000000000',x=>x.series[0].issuer_cik='123',x=>x.series[0].observations[0].symbol_as_reported='INVENTED',x=>x.series[0].observations[0].outstanding_fail_shares_as_reported=1,x=>x.series[0].observations[0].PRICE='2',x=>x.series[0].observations[0].source_row.full_six_field_canonical_sha256='bad',x=>x.series[0].observations[0].settlement_date_as_reported='2026-11-01']){
 const d=clone(original);mutation(d);await assert.rejects(()=>v.validateShard(d,bucket,index,wc));
}
const entries=index.entries;
assert.deepEqual(v.filter(entries,'00039J','exact'),[]);
assert.deepEqual(v.filter(entries,'00039J','prefix'),entries.filter(e=>e[0].startsWith('00039J')));
assert.deepEqual(v.filter(entries,'00039J202','exact'),entries.filter(e=>e[0]==='00039J202'));
assert.deepEqual(v.filter(entries,'AMTD','symbol'),entries.filter(e=>e[2].includes('AMTD')));assert.ok(v.filter(entries,'AMTD','symbol').length>1);
assert.deepEqual(v.filter(entries,'amtd','symbol'),[]);assert.deepEqual(v.filter(entries,'00039j','prefix'),[]);
assert.deepEqual(v.filter(entries,'','exact'),entries);assert.deepEqual(v.filter(entries,'','prefix'),entries);
assert.deepEqual(v.filter(entries,'','symbol'),entries.filter(e=>e[2].includes('')));
assert.deepEqual(v.filter(entries,'[','prefix'),[]);assert.deepEqual(v.filter(entries,'.*','symbol'),[]);
await mockFlows();
console.log('FTD directory: all64 shard hashes,13097 CUSIPs,63157 rows,12-date null axes, corruption rejection and literal ambiguous search passed');
})().catch(e=>{console.error(e);process.exitCode=1;});

async function mockFlows(){
 class Node{constructor(){this.children=[];this.handlers={};this.style={};this.textContent='';this.value='';this.hidden=false;}append(...n){this.children.push(...n);}replaceChildren(...n){this.children=n;}setAttribute(k,v){this[k]=v;}addEventListener(k,f){this.handlers[k]=f;}scrollIntoView(){this.scrolled=true;}focus(){this.focused=true;}}
 const nodes=Object.fromEntries(['load','state','work','query','mode','results','detail','detail-state','retry','prev','next','clear'].map(k=>['fd-'+k,new Node()]));nodes['fd-mode'].value='exact';
 const doc={getElementById:k=>nodes[k],createElement:()=>new Node()},text=n=>[n.textContent,...n.children.map(text)].join(' ');
 let indexBad=true,shardBad=true,delay=false,release;const calls=[];
 v.setup(doc,{crypto:wc},async(path,options)=>{calls.push(path);assert.equal(options.cache,'no-store');assert.ok(options.signal);if(delay){delay=false;await new Promise(r=>{release=r;});}let b=fs.readFileSync(__dirname+'/'+path);if((path.endsWith('index.json')&&indexBad)||(!path.endsWith('index.json')&&shardBad)){b=Buffer.from(b);b[3]^=1;}return{ok:true,arrayBuffer:async()=>Uint8Array.from(b).buffer};});
 assert.equal(calls.length,0);await nodes['fd-load'].handlers.click();assert.equal(nodes['fd-work'].hidden,true);assert.match(nodes['fd-state'].textContent,/unavailable or unverified/);assert.equal(nodes['fd-results'].children.length,0);
 indexBad=false;await nodes['fd-load'].handlers.click();assert.equal(nodes['fd-work'].hidden,false);assert.equal(nodes['fd-results'].children.length,20);assert.equal(calls.length,2);
 const select=q=>{nodes['fd-query'].value=q;nodes['fd-query'].handlers.input();return nodes['fd-results'].children[0]?.children[0];};
 let button=select('00032Q104');await button.handlers.click();assert.match(nodes['fd-detail-state'].textContent,/unavailable or unverified/);assert.equal(nodes['fd-detail'].children.length,0);assert.equal(nodes['fd-retry'].hidden,false);
 shardBad=false;await nodes['fd-retry'].handlers.click();assert.equal(nodes['fd-retry'].hidden,true);assert.match(text(nodes['fd-detail']),/Source CUSIP 00032Q104/);assert.equal((text(nodes['fd-detail']).match(/No source row/g)||[]).length,11);
 const fetched=calls.length;await button.handlers.click();assert.equal(calls.length,fetched);assert.match(nodes['fd-detail-state'].textContent,/Verified retained-file/);
 // Clear must invalidate even a successful in-flight shard; repeat clicks share one request.
 let newCusip;const loadedBucket=await v.bucket('00032Q104',wc);for(const e of index.entries){if(await v.bucket(e[0],wc)!==loadedBucket){newCusip=e[0];break;}}
 button=select(newCusip);delay=true;const first=button.handlers.click(),second=button.handlers.click();assert.equal(calls.length,fetched+1);nodes['fd-clear'].handlers.click();release();await Promise.all([first,second]);assert.equal(nodes['fd-detail'].children.length,0);assert.match(nodes['fd-detail-state'].textContent,/Choose a source CUSIP/);
 // Cached late response remains valid evidence but must only render after a fresh selection.
 button=select(newCusip);await button.handlers.click();assert.equal(calls.length,fetched+1);assert.match(text(nodes['fd-detail']),new RegExp(newCusip));
 nodes['fd-query'].value='AMTD';nodes['fd-mode'].value='symbol';nodes['fd-mode'].handlers.change();assert.match(nodes['fd-state'].textContent,/Ambiguous source symbol/);assert.equal(nodes['fd-results'].children.length,2);assert.equal(nodes['fd-detail'].children.length,0);
 nodes['fd-query'].value='no-match';nodes['fd-query'].handlers.input();assert.equal(nodes['fd-results'].children.length,0);assert.equal(nodes['fd-next'].disabled,true);assert.match(nodes['fd-state'].textContent,/not zero fails/);
 nodes['fd-clear'].handlers.click();nodes['fd-next'].handlers.click();assert.match(nodes['fd-state'].textContent,/Page 2/);assert.ok(nodes['fd-state'].scrolled&&nodes['fd-state'].focused);nodes['fd-prev'].handlers.click();assert.match(nodes['fd-state'].textContent,/Page 1/);
 console.log('FTD mock: lazy index/shard hash failure and retry, cached selection, in-flight deduplication, stale-response clearing, ambiguity, empty state and pagination passed');
}
