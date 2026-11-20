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
const xrxHref='financial-review.html#xerox-exchange-chronology';
const xrxCards=officialUI.n('list').children.filter(card=>links(card).some(l=>l.href===xrxHref));
assert.equal(xrxCards.length,1);
assert.match(text(xrxCards[0]),/Xerox/i);
assert.equal(links(ui.n('list')).some(l=>l.href===xrxHref),false);
const xrxPanel=read('financial-review.html').toString().split('id="xerox-exchange-chronology"')[1].split('</article>')[0];
for (const value of ['2026-10-29','2026-11-13','173,679,000','121,086,000','3,872,062',
    '000119312526437046/d18274dex991.htm','000119312526460692/d134827d8k.htm','fresh November surprise',
    'Face amounts are not net debt','No ranking, outcome or trade status changes']) assert.ok(xrxPanel.includes(value),value);

const hrbHref='financial-review.html#hrb-plan-replacement';
const hrbCards=officialUI.n('list').children.filter(card=>links(card).some(l=>l.href===hrbHref));
assert.equal(hrbCards.length,1);
assert.match(text(hrbCards[0]),/H&R Block/);
assert.equal(links(ui.n('list')).some(l=>l.href===hrbHref),false);
const hrbPanel=read('financial-review.html').toString().split('id="hrb-plan-replacement"')[1].split('</article>')[0];
for (const value of ['8,242,771','6,500,000','2,220,954','6.6%','90,578,373','93,613,719',
    '11,553,837','96.76%','000110465926111942/tm2617324-4_def14a.htm',
    '000001265926000042/hrb-20261110.htm','000001265926000042/hrb-2026longxtermincentive.htm',
    'not establish current available capacity','does not change the frozen ranking']) assert.ok(hrbPanel.includes(value),value);
assert.equal(90578373+1501832+1533514,93613719);
assert.equal((100*90578373/93613719).toFixed(2),'96.76');

const emrHref='financial-review.html#emerson-note-pricing';
const emrCards=officialUI.n('list').children.filter(card=>links(card).some(l=>l.href===emrHref));
assert.equal(emrCards.length,1);
assert.match(text(emrCards[0]),/Emerson Electric/i);
assert.equal(links(ui.n('list')).some(l=>l.href===emrHref),false);
const emrPanel=read('financial-review.html').toString().split('id="emerson-note-pricing"')[1].split('</article>')[0];
for (const value of ['€750 million','4.000%','99.639%','99.264%','€744.48 million','commercial paper',
    '000114036126043026/ny20084788x4_fwp.htm',
    '000114036126043442/ef20085458_8k.htm','000114036126043426/ny20084788x3_424b5.htm',
    '000114036126043782/ef20085543_8k.htm','not evidence that borrowing was repaid',
    'not another €750 million issuance','No ranking, outcome or trade status changes']) assert.ok(emrPanel.includes(value),value);
assert.equal(750000000*99264/100000,744480000);
const vitaHref='financial-review.html#vitaspring-loss-follow-up';
const vitaCards=officialUI.n('list').children.filter(card=>links(card).some(l=>l.href===vitaHref));
assert.equal(vitaCards.length,1);
assert.match(text(vitaCards[0]),/both reported periods remain loss-making/i);
assert.equal(links(ui.n('list')).some(l=>l.href===vitaHref),false);
const vitaPanel=read('financial-review.html').toString().split('id="vitaspring-loss-follow-up"')[1].split('</article>')[0];
for (const value of ['July 31, 2026','July 31, 2025','$155,817','$110,845','$44,972','40.6%',
    'zero reported revenue','000164033426001572/R4.htm','000164033426001541/vsbt10-qnt.htm',
    '000164033426001572/vsbc_10q.htm','$11,283','$2.411 million','does not revise the frozen ranking']) assert.ok(vitaPanel.includes(value),value);
assert.equal(155817-110845,44972);
assert.equal((100*44972/110845).toFixed(1),'40.6');

// The separately pinned overlay must never mutate or conceal the original ranking.
const assessmentPin=v.ASSESSMENT_PINS[officialManifest.snapshot.sha256];
const assessmentKey=assessmentPin.path.slice(4);
const verifiedOverlay=JSON.parse(read(assessmentKey));
const actualSnapshot=JSON.parse(read(officialManifest.snapshot.path.slice(4)));
assert.equal(v.validateAssessment(verifiedOverlay,actualSnapshot,officialManifest),verifiedOverlay);
for(const mutate of [
 a=>a.snapshot.sha256='0'.repeat(64),
 a=>a.assessments[0].readiness.state='HYPOTHETICAL_TRADE_QUALIFIED',
 a=>a.assessments[0].readiness.first_blocker.id='market_data',
 a=>a.assessments[0].evidence.verified=10,
 a=>a.assessments[0].evidence.checks[0].id='fake',
 a=>a.assessments[0].readiness.blockers.splice(1,1),
 a=>a.assessments[0].id=a.assessments[1].id,
 a=>a.execution_ready=true
]){const changed=structuredClone(verifiedOverlay);mutate(changed);assert.throws(()=>v.validateAssessment(changed,actualSnapshot,officialManifest));}
const overlayUI=mock(fetcher,{assessments:v.ASSESSMENT_PINS});
await overlayUI.api.initialLoad;
assert.equal(overlayUI.n('list').children.length,7);
assert.match(text(overlayUI.n('list')),/Research priority/);
assert.match(text(overlayUI.n('list')),/Evidence completeness: 2 of 10 requirements verified/);
assert.match(text(overlayUI.n('list')),/Trade readiness: NEEDS EVENT VERIFICATION/);
assert.match(text(overlayUI.n('list')),/First blocker: No verified first-public time/);
assert.match(text(overlayUI.n('summary')),/Prospective decisions awaiting outcomes: none/);
assert.match(text(overlayUI.n('summary')),/does not change archived scores/);
const archiveOverlay=mock(fetcher,{search:'?snapshot=original',assessments:v.ASSESSMENT_PINS});await archiveOverlay.api.initialLoad;
assert.equal(archiveOverlay.n('list').children.length,5);
assert.match(text(archiveOverlay.n('list')),/Evidence completeness: 2 of 10/);
const corruptOverlay=mock(async path=>{
 if(path!==assessmentKey)return fetcher(path);
 const bytes=Uint8Array.from(read(path));bytes[0]^=1;return {ok:true,arrayBuffer:async()=>bytes.buffer};
},{assessments:v.ASSESSMENT_PINS});await corruptOverlay.api.initialLoad;
assert.equal(corruptOverlay.n('list').children.length,7);
assert.doesNotMatch(text(corruptOverlay.n('list')),/Trade readiness:/);
assert.match(text(corruptOverlay.n('summary')),/Readiness assessment could not be verified/);
// Documentary overlays are archive- and source-bound independently of trade gates.
const dossierPin=v.DOSSIER_PINS[officialManifest.snapshot.sha256],dossierKey=dossierPin.path.slice(4);
const frozenDossier=JSON.parse(read(dossierKey));
assert.equal(v.validateDossiers(frozenDossier,actualSnapshot,officialManifest),frozenDossier);
for(const change of [
 a=>a.snapshot.sha256='0'.repeat(64),
 a=>a.notes[0].thesis_id=a.notes[1].thesis_id,
 a=>a.notes[0].unknowns='  ',
 a=>a.notes[0].execution_ready=true,
 a=>a.notes[0].sources[0].accessions=['0000000000-00-000000'],
 a=>a.notes[0].sources[0].file_sha256='0'.repeat(64),
 a=>a.notes[0].sources[0].json_pointer='/unrelated',
 a=>a.notes[0].sources[0].path='https://external.invalid/',
 a=>a.notes[0].sources=[]
]){const changed=structuredClone(frozenDossier);change(changed);assert.throws(()=>v.validateDossiers(changed,actualSnapshot,officialManifest));}
const withDossier=mock(fetcher,{assessments:v.ASSESSMENT_PINS,dossiers:v.DOSSIER_PINS});await withDossier.api.initialLoad;
assert.equal(withDossier.n('list').children.length,7);
assert.match(text(withDossier.n('list')),/Investigate the research thesis/);
assert.match(text(withDossier.n('list')),/No completed purchases or spending were reported/);
assert.match(text(withDossier.n('list')),/0001193125-26-467737/);
assert.match(text(withDossier.n('list')),/approximately CAD 100,000/);
assert.match(text(withDossier.n('list')),/Trade readiness: NEEDS EVENT VERIFICATION/);
const origDossier=mock(fetcher,{search:'?snapshot=original',dossiers:v.DOSSIER_PINS});await origDossier.api.initialLoad;
assert.equal(origDossier.n('list').children.length,5);
assert.match(text(origDossier.n('list')),/Evidence supporting the thesis/);
assert.doesNotMatch(text(origDossier.n('list')),/0001193125-26-467737/);
const brokenDossier=mock(async path=>{
 if(path!==dossierKey)return fetcher(path);
 const bytes=Uint8Array.from(read(path));bytes[0]^=1;return {ok:true,arrayBuffer:async()=>bytes.buffer};
},{assessments:v.ASSESSMENT_PINS,dossiers:v.DOSSIER_PINS});await brokenDossier.api.initialLoad;
assert.equal(brokenDossier.n('list').children.length,7);
assert.doesNotMatch(text(brokenDossier.n('list')),/Investigate the research thesis/);
assert.match(text(brokenDossier.n('list')),/Trade readiness: NEEDS EVENT VERIFICATION/);
assert.match(text(brokenDossier.n('summary')),/Research dossiers could not be verified/);
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
for(const file of ['index.html','trade-ideas.html'])assert.match(read(file).toString(),/trade-ideas\.html/);assert.match(read('trade-ideas.html').toString(),/trade-ideas.js\?v=20261120-vitaspring-loss-follow-up/);assert.match(read('../.github/workflows/ci.yml').toString(),/node --check web\/trade-ideas.js && node web\/tests-trade-ideas.js &&/);console.log('Trade ideas: verified 7-thesis successor and 5-thesis original, checked source links, corruption, busy/retry, unpriced guards and archive selection');})().catch(e=>{console.error(e);process.exitCode=1;});
