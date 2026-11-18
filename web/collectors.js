(function(){
'use strict';
const LABELS={sec_watchlist:'SEC watchlist metadata',private_daily_prices:'Private daily-price receipts',prepared_and_reference_imports:'Prepared and reference imports'};
const EVIDENCE=new Set(['.github/workflows/sec-observations.yml','data/latest_scan.json','data/price_feed_status.json']);
const date=x=>typeof x==='string'&&Number.isFinite(Date.parse(x));
function validate(d){
 const fail=()=>{throw Error('Invalid saved collector status');};
 if(!d||d.schema_version!==1||!date(d.as_of)||d.collection_enabled_by_this_index!==false||d.execution_ready!==false||d.history_completeness!=='LATEST_ACTIONS_ATTEMPTS_NOT_VERIFIED'||!Array.isArray(d.collectors)||d.collectors.length!==3)fail();
 const ids=new Set();
 for(const c of d.collectors){
  if(!c||!Object.hasOwn(LABELS,c.id)||ids.has(c.id))fail();ids.add(c.id);
  const manual=c.id==='prepared_and_reference_imports';
  if(c.mode!==(manual?'MANUAL_OFFLINE_IMPORTS':'SCHEDULED_BOUNDED')||c.policy_state!==(manual?'MANUAL_ONLY':'BOUNDED_TRIAL')||c.next_run_guaranteed!==false)fail();
  if(c.last_attempt!==null||c.last_attempt_status!=='UNVERIFIED_ACTIONS_HISTORY'||c.workflow_failure!==null||c.workflow_failure_status!=='UNVERIFIED_ACTIONS_HISTORY'||c.missing_periods_status!=='NOT_AUDITED')fail();
  for(const key of ['accepted_records','rejected_records','held_records','missing_periods'])if(c[key]!==null)fail();
  if(c.last_successful_observation!==null&&(!date(c.last_successful_observation)||Date.parse(c.last_successful_observation)>Date.parse(d.as_of)))fail();
  if(c.last_verified_complete_run!==null&&!/^https:\/\/github\.com\/JeremyHennessy\/CatalystRadar\/actions\/runs\/[0-9]+$/.test(c.last_verified_complete_run))fail();
  if(manual){if(c.expiry_utc!==null||c.next_configured_slot!==null||c.last_successful_observation!==null)fail();}
  else if(!date(c.expiry_utc)||!date(c.next_configured_slot)||Date.parse(c.next_configured_slot)<Date.parse(d.as_of)||Date.parse(c.next_configured_slot)>=Date.parse(c.expiry_utc)||typeof c.configured_cron!=='string'||!Number.isInteger(c.observation_age_seconds)||c.observation_age_seconds<0||c.observation_age_seconds!==Math.floor((Date.parse(d.as_of)-Date.parse(c.last_successful_observation))/1000))fail();
  if(!Array.isArray(c.blockers)||!c.blockers.length||!c.blockers.every(x=>typeof x==='string'&&x.length)||!Array.isArray(c.evidence)||!c.evidence.every(x=>EVIDENCE.has(x.path)&&/^[a-f0-9]{64}$/.test(x.sha256)))fail();
  for(const key of ['source_status','quota_status','rights_status','storage'])if(typeof c[key]!=='string'||!c[key])fail();
  if(c.id==='sec_watchlist'&&(!Number.isInteger(c.configured_issuers)||c.configured_issuers<1||!Number.isInteger(c.successful_issuers)||c.successful_issuers<0||c.successful_issuers>c.configured_issuers))fail();
  if(c.id==='private_daily_prices'&&(!Number.isInteger(c.saved_snapshots)||c.saved_snapshots<0||!Number.isInteger(c.rows_per_snapshot)||c.rows_per_snapshot<1))fail();
  if(c.last_retained_reservation&&(!date(c.last_retained_reservation.reserved_at)||!/^\d+$/.test(c.last_retained_reservation.run_id)||typeof c.reservation_warning!=='string'))fail();
 }
 return d;
}
// The publication projection is separate from the frozen operational audit.
function publishedSec(d){
 const feed=Array.isArray(d?.feeds)?d.feeds.filter(x=>x?.name==='SEC filings'):[];
 if(feed.length!==1||feed[0].status!=='snapshot_only'||!date(feed[0].as_of)||!date(d.generated_at)||Date.parse(feed[0].as_of)>Date.parse(d.generated_at)||typeof feed[0].detail!=='string'||!feed[0].detail.trim()||feed[0].detail.length>1000)throw Error('Invalid published SEC metadata');
 return {observed:feed[0].as_of,generated:d.generated_at,detail:feed[0].detail};
}
function init(doc,fetcher){
 const root=doc.getElementById('collector-list'),state=doc.getElementById('collector-state'),asof=doc.getElementById('collector-asof'),button=doc.getElementById('collector-refresh');let busy=false;
 const published=doc.getElementById('collector-published-sec');
 const el=(tag,text)=>{const n=doc.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
 const dl=(parent,rows)=>{const n=el('dl');rows.forEach(([k,v])=>n.append(el('dt',k),el('dd',v)));parent.append(n);};
 const link=(label,url)=>{const n=el('a',label);n.href=url;return n;};
 function render(d){
  const fragment=el('div');
  for(const c of d.collectors){
   const section=el('section');section.className='panel';section.id=c.id;
   section.append(el('h2',LABELS[c.id]),el('p',c.mode==='MANUAL_OFFLINE_IMPORTS'?'Manual, offline imports. No scheduled collector in the audited repositories.':'Bounded scheduled trial configuration. Current running health is not established.'));
   if(c.id==='sec_watchlist')section.append(el('p',`${c.successful_issuers} of ${c.configured_issuers} configured issuers have successful observations in the retained receipt. This is not all-market coverage.`));
   if(c.id==='private_daily_prices')section.append(el('p',`${c.saved_snapshots} saved private snapshots × ${c.rows_per_snapshot} rows per snapshot. Public receipt metadata only; no prices or returns.`));
   dl(section,[['Last successful observation',c.last_successful_observation??'Unknown for this grouped manual-import row'],['Latest attempt / result','Unknown · Actions history not verified'],['Failure diagnosis','Unknown · not proof of no failure'],['Receipt age at snapshot',c.observation_age_seconds===undefined?'Not established':`${c.observation_age_seconds.toLocaleString('en-US')} seconds`],['Trial stop boundary (UTC)',c.expiry_utc??'Not applicable · manual only'],['Next configured slot at snapshot',c.next_configured_slot??'None · manual only'],['Will that slot run?',c.mode==='MANUAL_OFFLINE_IMPORTS'?'Not applicable · no scheduled slot':'Not guaranteed'],['Accepted / rejected / held','Unknown / unknown / unknown'],['Missing periods','Unknown · not audited']]);
   if(c.last_verified_complete_run)section.append(link('Open retained verified run ↗',c.last_verified_complete_run));
   section.append(el('h3','Continuation blockers'));const ul=el('ul');c.blockers.forEach(x=>ul.append(el('li',x)));section.append(ul);
   const details=el('details');details.append(el('summary','Receipt provenance and policy scope'));dl(details,[['Saved source status',c.source_status],['Storage boundary',c.storage],['Quota scope',c.quota_status],['Rights scope',c.rights_status],['Configured cron (UTC)',c.configured_cron??'No scheduled collector']]);
   if(c.last_retained_reservation){dl(details,[['Retained reservation time',c.last_retained_reservation.reserved_at],['Reservation run ID',c.last_retained_reservation.run_id]]);details.append(el('p',c.reservation_warning));}
   c.evidence.forEach(e=>{details.append(el('p',e.path),el('code',e.sha256));});if(!c.evidence.length)details.append(el('p','No grouped source receipt is certified here. Inspect the individual dataset manifests.'));
   section.append(details);fragment.append(section);
  }
  root.replaceChildren(...fragment.children);root.hidden=false;
  asof.textContent=`Saved snapshot as of ${d.as_of} · not a live timestamp`;
  state.textContent='Three collection groups loaded from saved evidence. Latest attempts and failures remain unknown.';
 }
 async function load(){if(busy)return;busy=true;button.disabled=true;root.hidden=true;root.replaceChildren();asof.textContent='Snapshot time unknown until validation completes.';state.textContent='Loading and validating saved evidence…';
  published.textContent='Loading latest saved SEC projection…';
  const readPublished=(async()=>{try{
   const r=await fetcher('app-data.json',{cache:'no-store',signal:AbortSignal.timeout(30000)});
   if(!r.ok)throw Error();
   const x=publishedSec(await r.json());
   published.replaceChildren(el('p',x.detail));
   dl(published,[['Saved successful observation (UTC)',x.observed],['Dashboard generation (UTC, not deploy time)',x.generated],['Later attempts or failure status','Unknown from this projection']]);
  }catch{published.replaceChildren();published.textContent='Latest saved SEC projection unavailable or unverified; the earlier checkpoint is not a substitute.';}})();
  try{const r=await fetcher('collector-status.json',{cache:'no-store',signal:AbortSignal.timeout(30000)});if(!r.ok)throw Error();render(validate(await r.json()));}
  catch{state.textContent='Saved status unavailable or invalid. Collection health, timestamps and counts are unknown. Use Refresh saved evidence to retry; no collector will run.';asof.textContent='Snapshot time unknown.';}
  finally{await readPublished;busy=false;button.disabled=false;}
 }
 button.addEventListener('click',load);return load();
}
if(typeof module!=='undefined')module.exports={validate,init,publishedSec};
if(typeof document!=='undefined')init(document,window.fetch.bind(window));
})();
