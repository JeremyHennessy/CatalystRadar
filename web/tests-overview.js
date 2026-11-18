'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {count,stamp,safeURL,financial,registry,sourceMatches,readiness,paper,overlap}=require('./overview.js');
const load=p=>JSON.parse(fs.readFileSync(path.join(__dirname,p),'utf8'));
for(const invalid of [null,undefined,-1,NaN,Infinity,1.2,'4'])assert.throws(()=>count(invalid));
assert.equal(count(0),0);assert.throws(()=>stamp('bad'));assert.equal(safeURL('javascript:alert(1)'),null);assert.equal(safeURL('http://example.com'),null);
const quarters=[['../docs/research/financial-q4-2025-coverage.json',6304,5786,3832977],['../docs/research/financial-q1-2026-coverage.json',6169,5750,3690955],['financial-history/summary.json',7714,6179,3608711],['prepared/summary.json',6516,6008,3905397]];
quarters.forEach(([p,submissions,issuers,rows],i)=>{const d=load(p),result=financial(d,i===3);assert.equal(result.submissions,submissions);assert.equal(result.issuers,issuers);assert.equal(result.rows,rows);assert.throws(()=>financial({...d,simulation_enabled:true},i===3));assert.throws(()=>financial({...d,table_rows:{}},i===3));});
const records=registry(load('../docs/research/source-registry.json'));assert.equal(records.length,27);assert.equal(sourceMatches(records[0],'sec','all'),true);assert.equal(sourceMatches(records[0],'zzzz','all'),false);assert.equal(sourceMatches(records[0],'','VERIFIED'),true);assert.equal(sourceMatches(records[0],'','other'),false);assert.throws(()=>registry({records:[{}]}));
const h=readiness(load('../docs/research/horizon-readiness-2026-11-17.json'));assert.equal(h.horizons.length,6);assert.equal(h.inventory_reproduction.qualified_examples_in_retained_feature_rows,0);assert.equal(h.inventory_reproduction.feature_counts.feature_rows,10);assert.throws(()=>readiness({...h,training_ready:true}));assert.throws(()=>readiness({...h,horizons:[]}));
const d=load('app-data.json'),p=paper(d);assert.equal(p.initial_cash,500);assert.equal(p.orders.length+p.trades.length+p.positions.length,0);assert.throws(()=>paper({...d,feeds:[]}));assert.throws(()=>paper({...d,portfolio:{...p,orders:null}}));
const o=load('../docs/research/four-quarter-overlap-2026-11-18.json');assert.equal(overlap(o).cross_batch_multiple_accession_contexts,275);assert.throws(()=>overlap({...o,training_ready:true}));assert.throws(()=>overlap({...o,overlap_counts:{...o.overlap_counts,cross_batch_multiple_accession_contexts:274}}));
// Verify static local references resolve from both new and retained entry points.
for(const f of ['index.html','operations.html'])for(const m of fs.readFileSync(path.join(__dirname,f),'utf8').matchAll(/(?:href|src)="([^"]+)"/g)){const u=m[1].split('?')[0];if(!u.startsWith('#')&&!/^https?:/.test(u))assert.ok(fs.existsSync(path.resolve(__dirname,u)),`${f}: ${u}`);}
console.log('Overview manifest contracts, source filtering, unknown-state guards and local links passed.');
for(const bad of [{...h,retained_price_evidence:{...h.retained_price_evidence,observation_window_utc:null}},{...h,horizons:h.horizons.map((x,i)=>i?x:{...x,label:null})},{...h,shared_prerequisites:[{}]}])assert.throws(()=>readiness(bad));
for(const [file,key,value]of [['prepared/summary.json','insider_submission',38152],['holdings/summary.json','holdings_infotable',3830274],['prepared/summary.json','ftd',63157],['smalloffers/summary.json','cf_form_c_submission',559],['smalloffers/summary.json','rega_reg_a_submission',184]])assert.equal(count(load(file).table_rows[key]),value);
assert.equal(count(load('notes/summary.json').submissions),6670);assert.equal(count(load('notes/summary.json').numeric_rows_missing_tag_definitions),49);assert.equal(count(load('formd/summary.json').submissions),15952);
console.log('Malformed readiness and all six dataset counts checked.');
const {insider}=require('./overview.js');
const insiderEvidence=load('../docs/research/insider-code-diagnostics-2026-11-18.json');
assert.deepEqual(insider(insiderEvidence),{total:59885,contradictions:82,footnotes:49551,amendments:979,at:'2026-11-18 00:26:53 UTC'});
for(const bad of [null,{...insiderEvidence,training_ready:true},{...insiderEvidence,execution_ready:true},{...insiderEvidence,status:'SIGNALS'},{...insiderEvidence,audit_completed_at:'bad'},{...insiderEvidence,counts:{}},{...insiderEvidence,diagnostic_flag_counts:{...insiderEvidence.diagnostic_flag_counts,FOOTNOTE_CONTEXT_REQUIRED:59886}},{...insiderEvidence,diagnostic_flag_counts:{...insiderEvidence.diagnostic_flag_counts,AMENDMENT_NOT_RECONCILED:null}}])assert.throws(()=>insider(bad));
// Overlapping flags are independently bounded by the total, never summed as distinct rows.
assert.equal(insider({...insiderEvidence,diagnostic_flag_counts:{...insiderEvidence.diagnostic_flag_counts,FOOTNOTE_CONTEXT_REQUIRED:59885,AMENDMENT_NOT_RECONCILED:59885}}).total,59885);
console.log('Insider aggregate schema, provenance date and overlapping-flag guards passed.');
