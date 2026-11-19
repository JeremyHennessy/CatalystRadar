(function () {
'use strict';
const PATH='company-findings/ieh-sec-reconciliation-v1.json', SHA='bb3927141dabda2627736449e5d1cff5acec88aaea510bfd1a3a0a066efcf9ea', SIZE=1539;
const fail=()=>{throw Error('Invalid IEH reconciliation evidence');};
const source='https://www.sec.gov/Archives/edgar/data/50292/';
const expected=[
  ['10-Q','0001213900-26-118861','ea0310481-10q_iehcorp.htm','2026-11-12T20:30:55Z'],
  ['8-K EX-99.1','0001174947-26-000991','ex99-1.htm','2026-11-13T21:09:21Z']
];
const pair=(a,x,y)=>Array.isArray(a)&&a.length===2&&a[0]===x&&a[1]===y;
function validate(d){
  if(d?.schema_version!==1 || d.id!=='ieh-sec-duplicate-revenue-review' || d.issuer_cik!=='0000050292'
    || d.archived_revenue_sha256!=='74c4fff28c44a4213993cfa487b7745006a71a23d9274f5cbdd5516257719002'
    || !pair(d.quarter_ends,'2026-09-30','2025-09-30') || !Array.isArray(d.filings) || d.filings.length!==2
    || d.first_public_utc!==null || d.whole_document_novelty_evaluated!==false
    || d.accounting_comparability_verified!==false || d.execution_ready!==false) fail();
  const [earlier,later]=d.filings;
  d.filings.forEach((f,i)=>{
    const [form,accession,filename,clock]=expected[i];
    const filingBase=source+accession.replaceAll('-','')+'/';
    if (f?.form!==form || f.accession!==accession || f.index_url!==filingBase+accession+'-index.htm'
      || f.document_url!==filingBase+filename || f.acceptance_utc!==clock) fail();
  });
  if(!pair(earlier.revenue,10700084,7077592) || !pair(later.revenue,...earlier.revenue)
    || !pair(earlier.operating_income,1046496,-104380) || !pair(later.operating_income,...earlier.operating_income)
    || d.duplicate_revenue_in_later_accepted_filing!==true || d.tax_benefit_current_quarter_10q!==262109
    || d.exhibit_date_as_reported!=='2026-11-12' || d.acceptance_gap_seconds!==88706
    || (Date.parse(later.acceptance_utc)-Date.parse(earlier.acceptance_utc))/1000!==d.acceptance_gap_seconds
    || earlier.revenue[0]-earlier.revenue[1]!==d.revenue_difference
    || (100*d.revenue_difference/earlier.revenue[1]).toFixed(4)!==d.revenue_growth_pct_4dp) fail();
  return d;
}
function render(doc,root,d){
  const el=(tag,value)=>{const n=doc.createElement(tag);n.textContent=value;return n;};
  const anchor=(label,url)=>{const a=el('a',label);a.href=url;return a;};
  const p=txt=>el('p',txt);
  const links=el('ul','');
  for(const f of d.filings){
    const entry=el('li','');
    entry.append(anchor('SEC '+f.form+' · '+f.accession,f.document_url),el('span',' · '),anchor('Acceptance record',f.index_url));
    links.append(entry);
  }
  root.replaceChildren(
    p('Both filings report \$10,700,084 versus \$7,077,592 for the quarters ended September 30, 2026 and 2025. The difference is \$3,622,492 (51.1825%). They also report operating income of \$1,046,496 versus a \$104,380 operating loss. The 10-Q’s \$262,109 tax benefit is separate from operating income.'),
    p('EDGAR accepted the 10-Q on November 12, 2026 at 20:30:55 UTC and the 8-K on November 13, 2026 at 21:09:21 UTC, 24h 38m 26s later. The exhibit itself is dated November 12. Acceptance order does not establish the first time either document was available to the public.'),
    p('The later accepted filing repeats the scoped revenue and operating-income facts. Do not count it as a separate revenue surprise on those figures alone. Whole-document novelty, market availability and accounting comparability are not established.'),
    p('This later review resolves the archived record’s unchecked 10-Q comparison only for the reported revenue and operating-income amounts above. Archived rankings and qualification are unchanged.'),
    links
  );
}
async function init(doc,crypto,fetcher){
  const root=doc.getElementById('ieh-sec-reconciliation-body');
  if(!root)return;
  try{
    const r=await fetcher(PATH,{cache:'no-store',signal:AbortSignal.timeout(30000)});
    if(!r.ok)fail();
    const b=await r.arrayBuffer();
    if(b.byteLength!==SIZE)fail();
    const h=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',b)), n=>n.toString(16).padStart(2,'0')).join('');
    if(h!==SHA)fail();
    render(doc,root,validate(JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(b))));
  }catch{
    const note=doc.createElement('p');
    note.textContent='The supplemental SEC reconciliation could not be verified. Archived evidence and research status are unchanged.';
    root.replaceChildren(note);
  }
}
if(typeof module!=='undefined')module.exports={PATH,SHA,SIZE,validate,init};
else init(document,window.crypto,window.fetch.bind(window));
})();
