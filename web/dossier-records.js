(function(){'use strict';
// Presentation of already-verified, unchanged public source records only.
function render(doc,section,r,cik){
 const el=(tag,text)=>{const n=doc.createElement(tag);if(text!==undefined)n.textContent=text;return n;},box=el('article'),add=t=>box.append(el('p',t));box.className='panel';box.style.overflowWrap='anywhere';
 const link=(text,url)=>{const a=el('a',text);a.href=url;box.append(a);};
 const index=a=>`https://www.sec.gov/Archives/edgar/data/${Number(cik)}/${a.replaceAll('-','')}/${a}-index.html`;
 const list=items=>{const ul=el('ul');items.forEach(t=>ul.append(el('li',t)));box.append(ul);};
 if(section==='financial'){
  box.append(el('h4',r.metric+' · '+r.reported_end_date));
  add('SEC rounded month-end context (ddate), not verified exact period boundaries. Taxonomy '+r.taxonomy+'; source-reported unit '+r.reported_unit+'.');
  add('Recorded relation: '+r.numeric_relation.replaceAll('_',' ')+'. Numerical equality or difference is not accounting comparability or a restatement.');
  for(const o of r.observations){add(o.issuer_name_as_filed+' · filed '+o.filing_date_as_filed+' · '+o.filing_batch);link('Inspect filing '+o.accession+' ↗',index(o.accession));}
  add('Next review: original statements, notes, scope and amendment lineage. This metadata page contains no monetary values; the existing financial workspace retains its separate archive-value inspection.');
 }else if(section==='insider'){
  box.append(el('h4',r.issuer_name_as_filed+' · '+r.form_as_filed+' · '+r.accession));
  add('Filed '+r.filing_date+' in '+r.batch_id+'; reported transaction dates '+r.transaction_date_min+' to '+r.transaction_date_max+'. These dates are independent of financial or disclosure evidence.');
  add('Ticker as filed: '+(r.issuer_ticker_as_filed||'not reported')+'. Not a verified current listing.');
  add('P rows: '+(r.reported_code_counts.P||0)+'; S rows: '+(r.reported_code_counts.S||0)+'. P/S includes open-market OR private activity. Source rows are not economic trades; no net exposure or intent is inferred.');
  link('Locate accession in SEC search ↗','https://www.sec.gov/edgar/search/#/q='+r.accession);list(r.review_questions);
  add('Original filing unreviewed; amendment reconciliation '+(r.amendment_reconciled===false?'not reconciled':'unknown')+'. Submission plan flag '+r.submission_plan_flag_status+' does not establish transaction intent or compliance.');
 }else if(section==='disclosure'){
  box.append(el('h4',r.issuer_name_as_filed+' · '+r.form_as_filed+' · '+r.filing_date));
  add(r.disclosure_records+' source accounting contexts, not confirmed deals. Filing date is not a transaction date or first-public time.');
  list(r.concepts.map(c=>c.tag+' · '+c.taxonomy_version+' · '+c.records+' records'));
  link('Inspect filing '+r.accession+' ↗',index(r.accession));add('Next review: original narrative, accounting scope, transaction status and dates. No targets, values, completion or current catalyst are inferred.');
 }else if(section==='reported'&&r.id==='ieh-reported-quarterly-revenue'){
  box.append(el('h4',r.title));add(r.finding);add('Currency ISO and exact period starts are unknown. Underlying 10-Q and accounting comparability have not been independently checked.');list(r.blockers);list(r.next_research_steps);link('Open existing IEH source investigation','company-ieh.html');
 }else if(section==='reported'&&r.id==='emerson-reported-note-completion'){
  box.append(el('h4','Emerson: issuer-reported debt completion'));const f=r.facts;add('EUR '+f.principal_as_reported+' notes · coupon '+f.coupon_percent_as_reported+'% · maturity year '+f.maturity_year_as_reported+'. Coupon is not yield; full maturity date unknown.');add('Reported completion '+f.reported_completion_date+'; prior pricing filing '+f.reported_prior_pricing_filing_date+'. Previously announced, not independently settled.');list(r.limitations);link('Open existing financing investigation','company.html#debt-offering');
 }else throw Error('Unsupported dossier record');
 add('Source links are retained or constructed references, not newly fetched originals. No verified security identity, aligned event, causality, forecast or trade qualification.');
 const d=el('details'),pre=el('pre',JSON.stringify(r,null,2));pre.style.whiteSpace='pre-wrap';pre.style.overflowWrap='anywhere';d.append(el('summary','Exact retained public record and provenance'),pre);box.append(d);return box;
}
const api={render};if(typeof module!=='undefined')module.exports=api;if(typeof window!=='undefined')window.CatalystDossierRecords=api;
})();
