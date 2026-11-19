'use strict';const assert=require('node:assert/strict'),fs=require('node:fs'),crypto=require('node:crypto');if(!global.crypto)global.crypto=crypto.webcrypto;const v=require('./trade-ideas'),read=p=>fs.readFileSync(__dirname+'/'+p),m=JSON.parse(read(v.LATEST)),d=JSON.parse(read(m.snapshot.path.replace(/^web\//,''))),r=JSON.parse(read(m.rubric.path.replace(/^web\//,'')));
assert.equal(read(v.LATEST).length,v.PIN.bytes);assert.equal(crypto.createHash('sha256').update(read(v.LATEST)).digest('hex'),v.PIN.sha256);assert.equal(v.validate(d,r,m),d);assert.equal(d.ideas.length,5);assert.equal(d.counts.evaluated,905);assert.equal(d.counts.eligible_source_records,6);assert.equal(d.counts.actionable_trades,0);
for(const mutate of [x=>x.execution_ready=true,x=>x.training_ready=true,x=>x.counts.paper_trades_placed=1,x=>x.counts.returned=10,x=>x.ideas[0].coverage.current_price=0,x=>x.ideas[0].research_priority_score++,x=>x.ideas[0].factors[0].value=null,x=>x.ideas[0].factors[0].weight=100,x=>x.ideas[0].source_links[0].path='https://evil.test',x=>x.ideas[0].issuer_associations[0].issuer_cik='bad',x=>x.ideas[0].source_records[0].issuer_associations[0].issuer_cik='0000000001',x=>x.candidate_decisions[0].thesis_id='bad',x=>x.ideas[0].source_links[0].source_id='bad',x=>x.ideas[0].source_records[0].execution_ready=true]){const x=structuredClone(d);mutate(x);assert.throws(()=>v.validate(x,r,m));}
class N{constructor(tag){this.tag=tag;this.children=[];this.handlers={};this.textContent='';this.hidden=false;}append(...a){this.children.push(...a);}replaceChildren(...a){this.children=a;}addEventListener(k,f){this.handlers[k]=f;}setAttribute(k,v){this[k]=v;}removeAttribute(k){delete this[k];}set innerHTML(_){throw Error('Unsafe HTML');}}
const text=n=>n.textContent+' '+n.children.map(text).join(' '),links=n=>[...(n.tag==='a'?[n]:[]),...n.children.flatMap(links)];
function mock(fetcher,options){const ns={},doc={createElement:t=>new N(t),getElementById:id=>ns[id]||(ns[id]=new N('div'))};return{n:k=>doc.getElementById('ideas-'+k),api:v.setup(doc,fetcher,options)};}
(async()=>{let corrupt=false,unavailable=false,release;const calls=[];const fetcher=async path=>{calls.push(path);if(unavailable)throw Error('offline');const bytes=Uint8Array.from(read(path));if(corrupt)bytes[0]^=1;return{ok:true,arrayBuffer:async()=>bytes.buffer};};const ui=mock(fetcher,{search:"?snapshot=original"});assert.equal(ui.n('refresh').disabled,true);await ui.api.initialLoad;assert.equal(calls.length,3);assert.equal(ui.n('list').children.length,5);assert.match(text(ui.n('summary')),/899 records excluded/);assert.match(text(ui.n('list')),/Unknown/);assert.match(text(ui.n('list')),/80 \/ 100 factor weight assessed/);assert.match(text(ui.n('list')),/No entry price or position allocation/);for(const x of d.ideas){assert.ok(text(ui.n('list')).includes(x.title));for(const a of x.issuer_associations)assert(links(ui.n('list')).some(l=>l.href==='datasets.html?company_cik='+a.issuer_cik+'#company-investigation'));for(const s of x.source_records)for(const a of s.issuer_associations)assert(links(ui.n('list')).some(l=>l.href==='financial-review.html?company_cik='+a.issuer_cik+'&evidence_id='+encodeURIComponent(s.id)+'#research-scanner'));}
corrupt=true;await ui.api.load();assert.equal(ui.n('list').children.length,0);assert.equal(ui.n('summary').hidden,true);assert.match(ui.n('state').textContent,/failed integrity/);corrupt=false;await ui.api.load();assert.equal(ui.n('list').children.length,5);unavailable=true;await ui.api.load();assert.equal(ui.n('list').children.length,0);unavailable=false;
const pending=mock(async p=>{if(p===v.LATEST)await new Promise(r=>release=r);return fetcher(p);},{search:'?snapshot=original'});const before=calls.length;await pending.api.load();assert.equal(calls.length,before);release();await pending.api.initialLoad;assert.equal(pending.n('list').children.length,5);
const officialRelease=v.selectRelease(v.RELEASES);
assert.equal(officialRelease.id,'release-2');
const officialStart=calls.length;
const officialUI=mock(fetcher);await officialUI.api.initialLoad;
const officialManifest=JSON.parse(read(officialRelease.path));
assert.deepEqual(calls.slice(officialStart),[officialRelease.path,officialManifest.snapshot.path.slice(4),officialManifest.rubric.path.slice(4)]);
assert.equal(officialUI.n('list').children.length,7);
assert.match(text(officialUI.n('summary')),/900 records excluded/);
assert.match(text(officialUI.n('list')),/Coherent board authorized/);
assert.match(text(officialUI.n('list')),/TherapeuticsMD 10-Q/);
assert.ok(links(officialUI.n('list')).some(l=>l.href==='collectors.html#coherent-saved-case'));
assert.ok(links(officialUI.n('list')).some(l=>l.href==='financial-review.html#txmd-companion-10q'));
assert.match(read('collectors.html').toString(),/id="coherent-saved-case"/);
assert.match(read('financial-review.html').toString(),/id="txmd-companion-10q"/);
const empty=structuredClone(d);empty.ideas=[];empty.all_scored_candidates=[];empty.counts={...empty.counts,returned:0,consolidated_theses:0,eligible_source_records:0,excluded:905};empty.candidate_decisions=empty.candidate_decisions.map(x=>({...x,decision:'EXCLUDED',reason:'NO_ELIGIBLE_RESEARCH'}));assert.equal(v.validate(empty,r,m),empty);
// Deliberately synthetic release transport fixture. Nothing below is written or published.
const newCutoff='2026-11-19T20:12:00Z';
const testRubric={...r,declared_cutoff_utc:newCutoff};
const hash=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const json=x=>Buffer.from(JSON.stringify(x));
const pin=(path,bytes)=>({path,bytes:bytes.length,sha256:hash(bytes)});
const rubricBytes=json(testRubric);
const testSnapshot={...structuredClone(d),cutoff_utc:newCutoff,rubric_sha256:hash(rubricBytes)};
testSnapshot.ideas[0].title='SYNTHETIC TRANSPORT TEST ONLY';
for(const [i,extensionKey,extensionPrefix,extensionPath] of [
 [0,'coherent','coherent','web/collectors.html#coherent-saved-case'],
 [1,'txmd_companion','txmd_companion','web/financial-review.html#txmd-companion-10q'],
]){
 const idea=testSnapshot.ideas[i],src=idea.source_records[0],oldId=src.id;
 const newId=extensionPrefix+':'+(i?'b':'a').repeat(24);
 testSnapshot.source_pins[extensionKey]=testSnapshot.source_pins[src.source_ref.key];
 src.id=newId;src.source_ref.key=extensionKey;
 for(const link of idea.source_links)if(link.source_id===oldId){link.source_id=newId;link.path=extensionPath;}
 for(const row of testSnapshot.candidate_decisions)if(row.source_id===oldId){row.source_id=newId;row.source_ref.key=extensionKey;}
 testSnapshot.all_scored_candidates[i].source_ids=testSnapshot.all_scored_candidates[i].source_ids.map(id=>id===oldId?newId:id);
}
const snapshotBytes=json(testSnapshot);
const testManifest={...m,
 rubric:pin('web/trade-ideas/v1/rubrics/'+hash(rubricBytes)+'.json',rubricBytes),
 snapshot:pin('web/trade-ideas/v1/snapshots/'+hash(snapshotBytes)+'.json',snapshotBytes)};
const manifestBytes=json(testManifest);
const testRelease={id:'transport-test',cutoff:newCutoff,...pin('trade-ideas/v1/releases/'+hash(manifestBytes)+'.json',manifestBytes)};
const releases=[v.ORIGINAL,testRelease],fixtureFiles={
 [testRelease.path]:manifestBytes,[testManifest.rubric.path.slice(4)]:rubricBytes,[testManifest.snapshot.path.slice(4)]:snapshotBytes};
let badPath=null;const seen=[];
const fixtureFetch=async path=>{seen.push(path);const bytes=Uint8Array.from(fixtureFiles[path]||read(path));if(path===badPath)bytes[0]^=1;return{ok:true,arrayBuffer:async()=>bytes.buffer};};
assert.equal(v.selectRelease(releases),testRelease);
assert.equal(v.selectRelease(releases,'?snapshot=original'),v.ORIGINAL);
assert.throws(()=>v.selectRelease(releases,'?snapshot=transport-test&snapshot=original'));
assert.throws(()=>v.selectRelease(releases,'?snapshot=unknown'));
for(const brokenRelease of [{...testRelease,id:'original'},{...testRelease,cutoff:v.ORIGINAL.cutoff},{...testRelease,cutoff:'2026-11-31T20:12:00Z'},{...testRelease,path:v.LATEST}]){
 assert.throws(()=>v.selectRelease([v.ORIGINAL,brokenRelease]));
}
assert.throws(()=>v.validateManifest({...testManifest,rubric:m.rubric},testRelease));
assert.throws(()=>v.validate({...testSnapshot,cutoff_utc:d.cutoff_utc},testRubric,testManifest,testRelease));
const unsourced=structuredClone(testSnapshot);unsourced.ideas[0].source_links=[];
assert.throws(()=>v.validate(unsourced,testRubric,testManifest,testRelease));
const latestUI=mock(fixtureFetch,{releases});await latestUI.api.initialLoad;
assert.deepEqual(seen,[testRelease.path,testManifest.snapshot.path.slice(4),testManifest.rubric.path.slice(4)]);
assert.match(text(latestUI.n('list')),/SYNTHETIC TRANSPORT TEST ONLY/);
assert.equal(links(latestUI.n('history'))[0].href,'trade-ideas.html?snapshot=transport-test');
assert.equal(links(latestUI.n('history'))[0]['aria-current'],'page');
assert.ok(links(latestUI.n('list')).some(l=>l.href==='collectors.html#coherent-saved-case'));
assert.ok(links(latestUI.n('list')).some(l=>l.href==='financial-review.html#txmd-companion-10q'));
assert.ok(!links(latestUI.n('list')).some(l=>l.href?.includes('evidence_id=coherent')||l.href?.includes('evidence_id=txmd_companion')));
for(const path of Object.keys(fixtureFiles)){
 badPath=path;
 await latestUI.api.load();assert.equal(latestUI.n('list').children.length,0);
 assert.match(latestUI.n('state').textContent,/No ideas shown and no substitute data used/);
 assert.equal(links(latestUI.n('history'))[0].href,'trade-ideas.html?snapshot=transport-test');
}
const oldUI=mock(fixtureFetch,{releases,search:'?snapshot=original'});await oldUI.api.initialLoad;
assert.ok(text(oldUI.n("list")).includes(d.ideas[0].title));
assert.doesNotMatch(text(oldUI.n('list')),/SYNTHETIC TRANSPORT TEST ONLY/);
assert.equal(oldUI.n('original')['aria-current'],'page');
const beforeUnknown=seen.length;const unknownUI=mock(fixtureFetch,{releases,search:'?snapshot=unknown'});await unknownUI.api.initialLoad;
assert.equal(seen.length,beforeUnknown);assert.equal(unknownUI.n('list').children.length,0);
assert.match(read('trade-ideas.html').toString(),/href="trade-ideas\.html\?snapshot=original"/);
for(const file of ['index.html','trade-ideas.html'])assert.match(read(file).toString(),/trade-ideas\.html/);assert.match(read('trade-ideas.html').toString(),/trade-ideas.js\?v=20261119/);assert.match(read('../.github/workflows/ci.yml').toString(),/node --check web\/trade-ideas.js && node web\/tests-trade-ideas.js &&/);console.log('Trade ideas: verified 7-thesis successor and 5-thesis original, checked source links, corruption, busy/retry, unpriced guards and archive selection');})().catch(e=>{console.error(e);process.exitCode=1;});
