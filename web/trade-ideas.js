/* Bounded research priority only. No prices, allocations, orders or execution. */
(function(){'use strict';
const LATEST='trade-ideas/v1/latest.json';
// Filled only from the independently reviewed published source release.
const PIN=Object.freeze({bytes:420,sha256:'8c70e86caeddcb8a8b9c254f1eaa8ba8eb53175c73eace8d1a492e8f34d3d8b7'});
const ORIGINAL=Object.freeze({id:'original',cutoff:'2026-11-19T18:57:49Z',path:LATEST,...PIN});
// Add only independently reviewed immutable release pins. Do not replace ORIGINAL.
const RELEASES=Object.freeze([ORIGINAL,Object.freeze({id:'release-2',cutoff:'2026-11-19T20:10:08Z',path:'trade-ideas/v1/releases/0185e53523fb7687fc97a97aeee6e99ddebd6de7a0c3d142f23cb1311fe2ba36.json',bytes:486,sha256:'0185e53523fb7687fc97a97aeee6e99ddebd6de7a0c3d142f23cb1311fe2ba36'})]);
// Independently pinned assessment overlays; archived ranking bytes are never edited.
const ASSESSMENT_PINS=Object.freeze({"ddd63c5342f25e8c091481d98b97f46086b698cb541f989bf1068e7503b4e1f8":{"path":"web/trade-ideas/v1/assessments/180747dd7b5720f8bd704321745487ac971169a2ecc0a2da211c509bbf0979d6.json","bytes":13993,"sha256":"180747dd7b5720f8bd704321745487ac971169a2ecc0a2da211c509bbf0979d6"},"28e8b1d7b80a34de480ad03e9bdf7a5d18b65fdf5816239968f2f2fd52e6196a":{"path":"web/trade-ideas/v1/assessments/1de726badd03bee2565065b3beebb4740353bba8df50d479964b50c12b1b1ec5.json","bytes":19189,"sha256":"1de726badd03bee2565065b3beebb4740353bba8df50d479964b50c12b1b1ec5"}});
const DOSSIER_PINS=Object.freeze({"28e8b1d7b80a34de480ad03e9bdf7a5d18b65fdf5816239968f2f2fd52e6196a":{"path":"web/trade-ideas/v1/dossiers/31ca8c69d27f4051462b1094ac6d68275d18af180b6bbbf4d37ef048beaa54b3.json","bytes":8552,"sha256":"31ca8c69d27f4051462b1094ac6d68275d18af180b6bbbf4d37ef048beaa54b3"},"ddd63c5342f25e8c091481d98b97f46086b698cb541f989bf1068e7503b4e1f8":{"path":"web/trade-ideas/v1/dossiers/66e4e02805b720ea7384447ad35dad8c68cd42dd394ca788c0feea4375b169b3.json","bytes":6121,"sha256":"66e4e02805b720ea7384447ad35dad8c68cd42dd394ca788c0feea4375b169b3"}});
const fail=()=>{throw Error('Unverified trade-idea snapshot');};
const digest=async b=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',b))).map(x=>x.toString(16).padStart(2,'0')).join('');
async function request(fetcher,path,pin){if(!Number.isSafeInteger(pin?.bytes)||pin.bytes<1||pin.bytes>5000000||!/^[a-f0-9]{64}$/.test(pin.sha256))fail();const response=await fetcher(path,{cache:'no-store',signal:AbortSignal.timeout(30000)});if(!response.ok)fail();const bytes=await response.arrayBuffer();if(bytes.byteLength!==pin.bytes||await digest(bytes)!==pin.sha256)fail();return JSON.parse(new TextDecoder().decode(bytes));}
const strings=x=>Array.isArray(x)&&x.every(t=>typeof t==='string');
const sha=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x),cik=x=>typeof x==='string'&&/^\d{10}$/.test(x)&&Number(x)>0,num=x=>Number.isSafeInteger(x)&&x>=0,text=x=>typeof x==='string'&&x.length>0;
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const localPath=x=>['web/company-ieh.html','web/company.html#net-loss','web/company.html#company-finding','web/financial-review.html#shareholder-votes','web/company.html#debt-offering','web/financial-review.html#material-agreements'].includes(x);
const cutoff=x=>typeof x==='string'&&/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/.test(x)&&Number.isFinite(Date.parse(x))&&new Date(x).toISOString()===x.slice(0,-1)+'.000Z';
function validateReleases(releases){
  if(!Array.isArray(releases)||!releases.length||!same(releases[0],ORIGINAL))fail();
  const ids=new Set(['original']),pins=new Set([PIN.sha256]);
  for(let i=1;i<releases.length;i++){
    const x=releases[i];
    if(!x||typeof x.id!=='string'||!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(x.id)||x.id.length>64||ids.has(x.id)||!cutoff(x.cutoff)||x.cutoff<=releases[i-1].cutoff||!num(x.bytes)||x.bytes<1||x.bytes>5000000||!sha(x.sha256)||pins.has(x.sha256)||x.path!=='trade-ideas/v1/releases/'+x.sha256+'.json')fail();
    ids.add(x.id);pins.add(x.sha256);
  }
  return releases;
}
function selectRelease(releases,search=''){
  validateReleases(releases);
  const ids=new URLSearchParams(search).getAll('snapshot');
  if(!ids.length)return releases.at(-1);
  const selected=ids.length===1&&releases.find(x=>x.id===ids[0]);
  return selected||fail();
}
// These reviewed extension records are outside the frozen scanner index.
const extensionPath=(id,key)=>id.startsWith('coherent:')&&key==='coherent'?'web/collectors.html#coherent-saved-case':id.startsWith('txmd_companion:')&&key==='txmd_companion'?'web/financial-review.html#txmd-companion-10q':null;
function validateManifest(m,release=ORIGINAL){if(m?.schema_version!==1||m.execution_ready!==false||m.training_ready!==false)fail();for(const p of [m.snapshot,m.rubric])if(!p||!num(p.bytes)||!p.bytes||!sha(p.sha256))fail();if(m.snapshot.path!=='web/trade-ideas/v1/snapshots/'+m.snapshot.sha256+'.json'||m.rubric.path!==(release.id==='original'?'web/trade-ideas/v1/rubric.json':'web/trade-ideas/v1/rubrics/'+m.rubric.sha256+'.json'))fail();return m;}
function validate(d,r,m,release=ORIGINAL){validateManifest(m,release);if(d?.schema_version!==1||d.mode!=='RETROSPECTIVE_RESEARCH_PRIORITY'||d.execution_ready!==false||d.training_ready!==false||d.provider_requests_made!==false||d.actionability!=='UNPRICED_NOT_ACTIONABLE'||!cutoff(d.cutoff_utc)||d.cutoff_utc!==release.cutoff||!strings(d.limitations)||!strings(d.not_evaluated_extensions)||!text(d.scope?.scope))fail();if(r?.schema_version!==1||r.execution_ready!==false||r.training_ready!==false||d.rubric_id!==r.id||d.rubric_sha256!==m.rubric.sha256||r.declared_cutoff_utc!==d.cutoff_utc||!text(r.purpose)||!same(r.weights,{accession_citation:20,declared_filing_age:20,exact_period_context:20,source_review:40}))fail();const c=d.counts;if(!c||!Object.values(c).every(num)||c.actionable_trades!==0||c.paper_trades_placed!==0||c.evaluated!==c.excluded+c.eligible_source_records||c.returned>10||c.returned!==Math.min(10,c.consolidated_theses)||!Array.isArray(d.ideas)||c.returned!==d.ideas.length||!Array.isArray(d.candidate_decisions)||d.candidate_decisions.length!==c.evaluated)fail();if(!Array.isArray(d.all_scored_candidates)||d.all_scored_candidates.length!==c.consolidated_theses)fail();const scored=new Map(),allSources=new Map();let scoreOrder=Infinity;for(const [i,x]of d.all_scored_candidates.entries()){if(!/^research-[a-f0-9]{24}$/.test(x.id)||scored.has(x.id)||x.rank!==i+1||!num(x.research_priority_score)||x.research_priority_score>100||x.research_priority_score>scoreOrder||!strings(x.source_ids)||!x.source_ids.length||!Array.isArray(x.factors))fail();scoreOrder=x.research_priority_score;let total=0,known=0;const factors=new Set();for(const f of x.factors){if(factors.has(f.id)||!Object.hasOwn(r.weights,f.id)||f.weight!==r.weights[f.id]||!text(f.meaning))fail();factors.add(f.id);if(f.value===null){if(f.points!==null)fail();}else{if(![0,.5,1].includes(f.value)||f.points!==f.weight*f.value)fail();total+=f.points;known+=f.weight;}}if(factors.size!==4||total!==x.research_priority_score||known!==x.coverage?.known_factor_weight||x.coverage.total_factor_weight!==100)fail();for(const id of x.source_ids){if(allSources.has(id))fail();allSources.set(id,x.id);}scored.set(x.id,x);}const ids=new Set(),sources=new Set();let previous=Infinity;for(const [i,x]of d.ideas.entries()){if(!/^research-[a-f0-9]{24}$/.test(x.id)||ids.has(x.id)||x.rank!==i+1||!['WATCH','ABSTAIN'].includes(x.status)||x.actionability!==d.actionability||x.execution_ready!==false||x.training_ready!==false||!text(x.title)||!text(x.summary)||!text(x.next_action)||!strings(x.blockers)||!x.blockers.length||!Array.isArray(x.issuer_associations)||!x.issuer_associations.length||!Array.isArray(x.source_records)||!x.source_records.length||!Array.isArray(x.source_clocks)||!Array.isArray(x.source_links))fail();const ranked=d.all_scored_candidates[i];if(ranked.id!==x.id||ranked.research_priority_score!==x.research_priority_score||!same(ranked.factors,x.factors)||!same(ranked.coverage,x.coverage)||!same([...ranked.source_ids].sort(),x.source_records.map(s=>s.id).sort()))fail();ids.add(x.id);for(const a of x.issuer_associations)if(!cik(a.issuer_cik)||!strings(a.names_as_reported)||!a.names_as_reported.length||!text(a.role))fail();let points=0,known=0;const factorIDs=new Set();if(!Array.isArray(x.factors)||x.factors.length!==4)fail();for(const f of x.factors){if(!Object.hasOwn(r.weights,f.id)||factorIDs.has(f.id)||f.weight!==r.weights[f.id]||!text(f.meaning))fail();factorIDs.add(f.id);if(f.value===null){if(f.points!==null)fail();}else{if(![0,.5,1].includes(f.value)||f.points!==f.weight*f.value)fail();points+=f.points;known+=f.weight;}}if(x.research_priority_score!==points||points>previous||x.coverage?.known_factor_weight!==known||x.coverage.total_factor_weight!==100)fail();previous=points;for(const k of ['current_price','expected_return','first_public_verified','return_outcome','security_mapping','corporate_action_continuity'])if(x.coverage[k]!==null)fail();for(const clock of x.source_clocks)if(!text(clock.meaning)||!Object.hasOwn(clock,'value_as_reported'))fail();const sourceIds=new Set();for(const source of x.source_records){if(!/^[a-z_]+:[a-f0-9]{24}$/.test(source.id)||sources.has(source.id)||source.execution_ready!==false||source.training_ready!==false||source.evidence_state!=='SOURCE_REVIEWED_WITH_LIMITS'||!sha(source.source_ref?.object_sha256)||!d.source_pins[source.source_ref.key]||!source.issuer_associations.every(a=>x.issuer_associations.some(b=>a.issuer_cik===b.issuer_cik)))fail();const path=extensionPath(source.id,source.source_ref.key);if(path&&(release.id==='original'||!x.source_links.some(link=>link.source_id===source.id&&link.path===path)))fail();sources.add(source.id);sourceIds.add(source.id);}for(const link of x.source_links){const source=x.source_records.find(s=>s.id===link.source_id);if(!text(link.label)||!sourceIds.has(link.source_id)||!text(link.path)||!(localPath(link.path)||link.path===extensionPath(source.id,source.source_ref.key)))fail();}}
const seen=new Set();let included=0,excluded=0;for(const x of d.candidate_decisions){if(!text(x.source_id)||seen.has(x.source_id)||!sha(x.source_ref?.object_sha256))fail();seen.add(x.source_id);if(x.decision==='INCLUDED_IN_THESIS'){included++;if(!scored.has(x.thesis_id)||allSources.get(x.source_id)!==x.thesis_id)fail();}else if(x.decision==='EXCLUDED'){excluded++;if(!text(x.reason)||allSources.has(x.source_id))fail();}else fail();}if(included!==c.eligible_source_records||excluded!==c.excluded||allSources.size!==included)fail();return d;}
// This overlay may explain a blocked paper decision; it cannot qualify, upgrade or execute one.
const exactKeys=(o,keys)=>o&&typeof o==='object'&&!Array.isArray(o)&&Object.keys(o).length===keys.length&&keys.every(k=>Object.hasOwn(o,k));
function validateAssessment(a,d,m){
  if(!exactKeys(a,['schema_version','assessment_id','cutoff_utc','snapshot','checks','assessments'])
    ||a.schema_version!==1||a.assessment_id!=='documentary-coverage-and-readiness-v1'||a.cutoff_utc!==d.cutoff_utc
    ||!exactKeys(a.snapshot,['path','bytes','sha256'])||a.snapshot.path!==m.snapshot.path
    ||a.snapshot.bytes!==m.snapshot.bytes||a.snapshot.sha256!==m.snapshot.sha256||!Array.isArray(a.checks)
    ||a.checks.length!==10||!Array.isArray(a.assessments)||a.assessments.length!==d.ideas.length)fail();
  const ids=a.checks.map(c=>c.id);
  const required=['source_identity','event_content','event_availability','instrument_identity','financial_comparability','market_data','liquidity','trading_status','corporate_actions','outcome_evidence'];
  const gateOrder=['event_availability','instrument_identity','market_data','corporate_actions','liquidity','trading_status'];
  if(!same(ids,required))fail();
  if(new Set(ids).size!==10||!a.checks.every(c=>exactKeys(c,['id','label'])&&/^[a-z_]+$/.test(c.id)&&text(c.label)))fail();
  for(const [i,x]of a.assessments.entries()){
    if(!exactKeys(x,['id','evidence','readiness'])||x.id!==d.ideas[i].id
      ||!exactKeys(x.evidence,['verified','total','checks'])||x.evidence.total!==ids.length
      ||!num(x.evidence.verified)||!Array.isArray(x.evidence.checks)||x.evidence.checks.length!==ids.length)fail();
    const checks=x.evidence.checks;
    if(!checks.every((c,j)=>exactKeys(c,['id','state','detail'])&&c.id===ids[j]&&text(c.detail)
      &&['VERIFIED','UNKNOWN','UNAVAILABLE','NOT_ASSESSED','FAILED_QUALIFICATION','VERIFIED_ABSENCE'].includes(c.state))
      ||checks.filter(c=>c.state==='VERIFIED').length!==x.evidence.verified)fail();
    const readiness=x.readiness;
    if(!exactKeys(readiness,['state','first_blocker','blockers'])||readiness.state!=='NEEDS_EVENT_VERIFICATION'
      ||!Array.isArray(readiness.blockers)||!readiness.blockers.length||!same(readiness.blockers[0],readiness.first_blocker)
      ||readiness.first_blocker.id!=='event_availability'
      ||!same(readiness.blockers.map(b=>b.id),gateOrder)
      ||!readiness.blockers.every(b=>exactKeys(b,['id','detail'])&&ids.includes(b.id)&&text(b.detail)&&checks.find(c=>c.id===b.id).state!=='VERIFIED'&&checks.find(c=>c.id===b.id).detail===b.detail))fail();
  }
  return a;
}
function validateDossiers(a,d,m){
  if(!exactKeys(a,['schema_version','review_id','snapshot','notes'])||a.schema_version!==1
    ||a.review_id!=='documentary-dossiers-v1'||!exactKeys(a.snapshot,['path','bytes','sha256'])
    ||!['path','bytes','sha256'].every(k=>a.snapshot[k]===m.snapshot[k])
    ||!Array.isArray(a.notes)||a.notes.length!==d.ideas.length)fail();
  for(const [i,n]of a.notes.entries()){
    const idea=d.ideas[i],fields=['favorable_evidence','counterweight','unknowns','investigate_or_weaken'];
    if(!exactKeys(n,['thesis_id',...fields,'sources'])||n.thesis_id!==idea.id
      ||!fields.every(k=>text(n[k])&&n[k].trim()&&n[k].length<=2000)
      ||!Array.isArray(n.sources)||n.sources.length!==idea.source_records.length)fail();
    for(const [j,ref]of n.sources.entries()){
      const row=idea.source_records[j],sourcePin=d.source_pins[row.source_ref.key];
      if(!exactKeys(ref,['source_id','accessions','object_sha256','json_pointer','path','file_sha256'])
        ||ref.source_id!==row.id||!same(ref.accessions,row.source_accessions)
        ||ref.object_sha256!==row.source_ref.object_sha256||ref.json_pointer!==row.source_ref.json_pointer
        ||ref.path!==sourcePin.path||ref.file_sha256!==sourcePin.sha256)fail();
    }
  }
  return a;
}
function setup(doc,fetcher,{releases=RELEASES,search='',assessments={},dossiers={}}={}){const get=id=>doc.getElementById('ideas-'+id),button=get('refresh');if(!button)return;let busy=false;const el=(tag,value)=>{const e=doc.createElement(tag);if(value!==undefined)e.textContent=String(value);return e;},list=(parent,items)=>{const ul=el('ul');for(const s of items)ul.append(el('li',s));parent.append(ul);},link=(path,label)=>{const a=el('a',label);a.href=path;return a;},label=x=>x.replaceAll('_',' '),value=x=>x===null?'Unknown':typeof x==='object'?JSON.stringify(x):String(x);
function renderHistory(selected){
  const history=get('history');if(!history)return;
  const original=doc.getElementById('ideas-original');
  if(original){if(selected?.id==='original')original.setAttribute('aria-current','page');else original.removeAttribute('aria-current');}
  history.replaceChildren(...releases.slice(1).map(release=>{
    const a=link('trade-ideas.html?snapshot='+encodeURIComponent(release.id),release.cutoff+' snapshot');
    if(release.id===selected?.id)a.setAttribute('aria-current','page');
    return a;
  }));
}
function renderAssessments(a,mounts,pin,notice){
  for(const row of a.assessments){
    const mount=mounts.get(row.id);
    const detail=el('details');
    detail.append(el('summary','Inspect evidence and trade blockers'));
    for(const check of row.evidence.checks){
      const def=a.checks.find(x=>x.id===check.id);
      detail.append(el('p',def.label+' · '+label(check.state)+': '+check.detail));
    }
    const other=row.readiness.blockers.filter(x=>x.id!==row.readiness.first_blocker.id);
    if(other.length){detail.append(el('h4','Other known barriers'));list(detail,other.map(x=>x.detail));}
    mount.replaceChildren(el('h3','Why didn’t this qualify as a trade?'),
      el('p','Evidence completeness: '+row.evidence.verified+' of '+row.evidence.total+' requirements verified.'),
      el('p','Trade readiness: '+label(row.readiness.state)),
      el('p','First blocker: '+row.readiness.first_blocker.detail),detail);
  }
  notice.replaceChildren(el('p','Verified readiness assessment. This separate retrospective review does not change archived scores or represent a trading-time decision.'),link(pin.path.slice(4),'Assessment criteria and complete results'));
}
function renderDossiers(a,mounts,pin,notice){
  for(const row of a.notes){
    const details=el('details');
    details.append(el('summary','Investigate the research thesis'),
      el('h4','Evidence supporting the thesis'),el('p',row.favorable_evidence),
      el('h4','Counterpoint'),el('p',row.counterweight),
      el('h4','What remains unknown'),el('p',row.unknowns),
      el('h4','What to check next'),el('p',row.investigate_or_weaken),
      el('h4','Reviewed filing accessions'));
    list(details,[...new Set(row.sources.flatMap(ref=>ref.accessions))]);
    mounts.get(row.thesis_id).replaceChildren(details);
  }
  notice.replaceChildren(el('p','Source-backed dossiers add context, not a forecast or trade plan.'),link(pin.path.slice(4),'Published dossier evidence references'));
}
function render(d,r,m,pin,dossierPin){const mounts=new Map(),dossierMounts=new Map();const summary=get('summary');summary.append(el('h2','Research ideas '+d.ideas.length+' / 10'),el('p','Execution-qualified '+d.counts.actionable_trades+' · Paper trades placed '+d.counts.paper_trades_placed),el('p','Prospective decisions awaiting outcomes: none in this retrospective snapshot. Measured outcomes: none in this snapshot.'),el('p',d.counts.evaluated+' retained evidence records evaluated; '+d.counts.eligible_source_records+' eligible records consolidated into '+d.counts.returned+' theses. '+d.counts.excluded+' records excluded. Zero actionable trades. No entries padded to reach ten.'),el('p','Snapshot cutoff: '+d.cutoff_utc+' · retrospective, not live market coverage.'),el('p',d.scope.scope),...(d.not_evaluated_extensions.length?[el('p','Not evaluated in this snapshot: '+d.not_evaluated_extensions.join('; ')+'.')]:[]));const method=el('details');method.append(el('summary','Scoring policy and audit trail'),el('p',r.purpose));list(method,d.limitations);for(const [k,v]of Object.entries(r.rules))method.append(el('p',label(k)+': '+v));method.append(link(m.snapshot.path.replace(/^web\//,''),'Full snapshot and exclusion decisions'),el('p','Snapshot SHA-256: '+m.snapshot.sha256),link(m.rubric.path.replace(/^web\//,''),'Published scoring rubric'));summary.append(method);summary.hidden=false;const notice=el('div');if(pin){notice.append(el('p','Verifying the separate readiness assessment…'));summary.append(notice);}const dossierNotice=el('div');if(dossierPin){dossierNotice.append(el('p','Verifying the research dossiers…'));summary.append(dossierNotice);}
if(!d.ideas.length)get('list').append(el('p','No research ideas meet the published selection policy. Nothing has been substituted.'));
for(const x of d.ideas){const card=el('article');card.className='idea-card';const heading=el('div');heading.className='idea-heading';const title=el('div');title.append(el('p','Rank '+x.rank+' · '+x.status),el('h2',x.title));title.children[0].className='idea-rank';const score=el('div');score.className='idea-score';score.append(el('strong',x.research_priority_score+' / 100'),el('span','Research priority'));heading.append(title,score);card.append(heading,el('p',x.summary));const meta=el('p',x.status+' / UNPRICED · NOT ACTIONABLE');meta.className='tag caution';card.append(meta,el('p',x.coverage.known_factor_weight+' / 100 factor weight assessed. Unknown factors remain unknown, not zero; score is not renormalized or a probability.'));const links=el('div');links.className='idea-links';for(const a of x.issuer_associations)links.append(link('datasets.html?company_cik='+a.issuer_cik+'#company-investigation',a.names_as_reported.join(' / ')+' · CIK '+a.issuer_cik));card.append(links,el('p','Issuer associations remain separate, not verified security identity.'));
const grid=el('div');grid.className='idea-grid';const why=el('section');why.append(el('h3','What to investigate next'),el('p',x.next_action),el('p','Evaluation horizon: unavailable. No verified price window or expected-return horizon.'),el('h3','Evidence dates and freshness'),el('p','Declared filing date: '+value(x.declared_filing_date)+'. Filing age is not event novelty or first-public availability.'));for(const f of x.factors)if(f.id==='declared_filing_age')why.append(el('p','Filing age at snapshot cutoff: '+(f.age_days===undefined||f.age_days===null?'Unknown':f.age_days+' days')+'.'));for(const c of x.source_clocks)why.append(el('p',label(c.meaning)+': '+value(c.value_as_reported)));const blockers=el('section');blockers.append(el('h3','What still blocks action'));list(blockers,x.blockers);blockers.append(el('p','Current price, expected return, security mapping and corporate-action continuity: unknown. No entry price or position allocation.'));grid.append(why,blockers);card.append(grid);
if(pin){const mount=el('section');mounts.set(x.id,mount);card.append(mount);}
if(dossierPin){const mount=el('section');dossierMounts.set(x.id,mount);card.append(mount);}
if(m.snapshot.sha256==='28e8b1d7b80a34de480ad03e9bdf7a5d18b65fdf5816239968f2f2fd52e6196a' &&
   x.id==='research-4c01192f934e6179415a76dc' && x.source_records.some(s=>s.source_accessions.includes('0001193125-26-460692'))){
  card.append(link('financial-review.html#xerox-exchange-chronology','Compare the Xerox announcement and settlement'));
}
const factors=el('details');factors.append(el('summary','Inspect all score factors'));const table=el('table');table.className='idea-factors';const head=el('tr');for(const t of ['Factor','Weight','Value','Points'])head.append(el('th',t));const thead=el('thead');thead.append(head);table.append(thead);const tbody=el('tbody');for(const f of x.factors){const row=el('tr'),cell=el('td');cell.append(el('strong',label(f.id)),el('p',f.meaning));row.append(cell,el('td',f.weight),el('td',value(f.value)),el('td',value(f.points)));tbody.append(row);}table.append(tbody);factors.append(table);card.append(factors,el('h3','Source evidence'));const sourceLinks=el('div');sourceLinks.className='idea-links';for(const l of x.source_links)sourceLinks.append(link(l.path.replace(/^web\//,''),l.label));for(const s of x.source_records)if(!extensionPath(s.id,s.source_ref.key))for(const a of s.issuer_associations)sourceLinks.append(link('financial-review.html?company_cik='+a.issuer_cik+'&evidence_id='+encodeURIComponent(s.id)+'#research-scanner','Inspect exact evidence · CIK '+a.issuer_cik));card.append(sourceLinks);const provenance=el('details');provenance.append(el('summary','Source references and integrity'));for(const s of x.source_records)provenance.append(el('p',s.id+' · '+s.source_ref.key+' · pointer '+(s.source_ref.json_pointer||'(root)')),el('p','Source object SHA-256: '+s.source_ref.object_sha256));card.append(provenance);get('list').append(card);}return{mounts,notice,dossierMounts,dossierNotice};}
async function load(){
  if(busy)return;
  busy=true;button.disabled=true;
  const clear=()=>{get('list').replaceChildren();get('summary').replaceChildren();get('summary').hidden=true;};
  clear();get('state').textContent='Verifying the published shortlist, snapshot and scoring rubric…';
  try{
    const release=selectRelease(releases,search);
    renderHistory(release);
    const m=validateManifest(await request(fetcher,release.path,release),release);
    const [d,r]=await Promise.all([request(fetcher,m.snapshot.path.replace(/^web\//,''),m.snapshot),request(fetcher,m.rubric.path.replace(/^web\//,''),m.rubric)]);
    validate(d,r,m,release);
    const pin=assessments[m.snapshot.sha256];
    const dossierPin=dossiers[m.snapshot.sha256];
    const {mounts,notice,dossierMounts,dossierNotice}=render(d,r,m,pin,dossierPin);
    get('state').textContent='Published snapshot and rubric verified. '+d.ideas.length+' research priorities; zero actionable trades.';
    async function showDossiers(){
      if(!dossierPin)return;
      try{
        if(!sha(dossierPin.sha256)||dossierPin.path!=='web/trade-ideas/v1/dossiers/'+dossierPin.sha256+'.json')fail();
        const a=await request(fetcher,dossierPin.path.slice(4),dossierPin);
        validateDossiers(a,d,m);
        renderDossiers(a,dossierMounts,dossierPin,dossierNotice);
      }catch{
        for(const mount of dossierMounts.values())mount.replaceChildren();
        dossierNotice.replaceChildren(el('p','Research dossiers could not be verified. Ranking and trade-readiness information are unchanged.'));
      }
    }
    async function showAssessment(){
      if(!pin)return;
      try{
        if(!sha(pin.sha256)||pin.path!=='web/trade-ideas/v1/assessments/'+pin.sha256+'.json')fail();
        const a=await request(fetcher,pin.path.slice(4),pin);
        validateAssessment(a,d,m);
        renderAssessments(a,mounts,pin,notice);
      }catch{
        for(const mount of mounts.values())mount.replaceChildren();
        notice.replaceChildren(el('p','Readiness assessment could not be verified. The original ranking and its recorded blockers are shown unchanged.'));
      }
    }
    await Promise.all([showAssessment(),showDossiers()]);
  }catch{
    clear();
    get('state').textContent='The selected trade-idea snapshot is unavailable or failed integrity checks. No ideas shown and no substitute data used. Retry, or open the original snapshot.';
  }finally{busy=false;button.disabled=false;}
}button.addEventListener('click',load);button.disabled=false;const initialLoad=load();return{load,initialLoad};}
const api={LATEST,PIN,ORIGINAL,RELEASES,ASSESSMENT_PINS,DOSSIER_PINS,request,validateManifest,validate,validateAssessment,validateDossiers,selectRelease,setup};if(typeof module!=='undefined')module.exports=api;if(typeof document!=='undefined')setup(document,fetch,{search:document.location.search,assessments:ASSESSMENT_PINS,dossiers:DOSSIER_PINS});
})();
