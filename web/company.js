(function () {
  'use strict';
  const ID = 'vitaspring-revenue-zero-baseline';
  const PATH = 'company-findings/vitaspring-revenue.json';
  function validate(d) {
    const fail = () => { throw new Error('Reviewed finding validation failed'); };
    const text = x => typeof x === 'string' && x.trim().length > 0;
    const strings = x => Array.isArray(x) && x.length > 0 && x.every(text);
    const hash = x => typeof x === 'string' && /^[a-f0-9]{64}$/.test(x);
    if (!d || d.version !== 1 || d.id !== ID || d.status !== 'SOURCE_BACKED_HISTORICAL_OBSERVATION_NOT_TRADING_QUALIFIED' || !Number.isFinite(Date.parse(d.generated_at))) fail();
    if (d.issuer?.cik !== '0001697884' || !text(d.issuer.name_as_filed) || d.issuer.ticker !== null || d.issuer.security_mapping_verified !== false) fail();
    if (!text(d.finding) || d.research_disposition !== 'ABSTAIN_FROM_REVENUE_GROWTH_INFERENCE' || d.training_ready !== false || d.execution_ready !== false || d.probability !== null || d.price_target !== null || d.return_estimate !== null) fail();
    if (d.calculation?.metric !== 'percentage_revenue_growth' || d.calculation.value !== null || d.calculation.reason !== 'ZERO_COMPARISON_BASE' || d.calculation.not_zero_percent !== true) fail();
    const f = d.filing;
    if (!f || f.accession !== '0001640334-26-001075' || f.form !== '10-Q' || f.period_of_report !== '2025-07-31' || f.filing_date_as_reported !== '2026-06-17' || f.fiscal_year_as_filed !== '2026' || f.fiscal_period_as_filed !== 'Q2' || f.primary_member !== 'vsbc_10q.htm') fail();
    const prefix = `https://www.sec.gov/Archives/edgar/data/${Number(d.issuer.cik)}/${f.accession.replaceAll('-', '')}/`;
    if (f.source_filing_index_url !== `${prefix}${f.accession}-index.html` || f.source_primary_document_url !== `${prefix}${f.primary_member}`) fail();
    if (!Array.isArray(d.facts) || d.facts.length !== 2) fail();
    d.facts.forEach((x, i) => {
      const year = 2025 - i;
      if (x.fact_id !== `fid_${2230+i}` || x.concept !== 'Revenues' || x.taxonomy_namespace !== 'http://fasb.org/us-gaap/2025' || x.value !== '0' || x.currency !== 'USD' || x.period_start !== `${year}-05-01` || x.period_end !== `${year}-07-31` || x.source_context_ref !== `From${year}-05-01to${year}-07-31` || x.source_literal !== '-' || x.source_transform !== 'TRR3 zerodash' || x.dimension_or_scenario_present !== false || !hash(x.context_serialization_sha256)) fail();
    });
    const p = d.provenance;
    if (!p || !hash(p.original_archive_sha256) || !hash(p.original_member_sha256) || !Number.isFinite(Date.parse(p.source_local_verified_utc)) || p.source_exact_download_utc !== null || p.source_first_public_utc !== null || p.original_bytes_retained !== true || p.source_numeric_extraction_checked !== true || p.full_accounting_comparability_verified !== false) fail();
    if (!strings(d.blockers) || !strings(d.next_research_steps) || !strings(d.limitations)) fail();
    return d;
  }
  function init(doc, location, fetcher) {
    const state = doc.getElementById('company-state'), retry = doc.getElementById('company-retry'), root = doc.getElementById('company-finding');
    const id = new URLSearchParams(location.search).get('finding');
    if (id !== null && id !== ID) {
      state.textContent = 'No reviewed finding is published for this identifier. No company data or prediction is inferred.';
      doc.getElementById('company-reset').hidden = false;
      return;
    }
    const el = (tag, text, cls) => { const n = doc.createElement(tag); if (text !== undefined) n.textContent = text; if (cls) n.className = cls; return n; };
    const section = (title, wide=false) => { const n=el('section',undefined,'panel'+(wide?' company-wide':'')); n.append(el('h2',title)); return n; };
    const list = (parent, items) => { const ul=el('ul'); items.forEach(s=>ul.append(el('li',s))); parent.append(ul); };
    const link = (label,url) => { const a=el('a',label); a.href=url; return a; };
    const dl = (parent, rows) => { const n=el('dl'); rows.forEach(([k,v])=>n.append(el('dt',k),el('dd',v))); parent.append(n); };
    function render(d) {
      const grid=el('div',undefined,'company-grid');
      const lead=section(d.issuer.name_as_filed,true);
      lead.append(el('p',`CIK ${d.issuer.cik} · Historical source-reported revenue · No verified current ticker`,'subtle'));
      const facts=el('div',undefined,'fact-grid');
      d.facts.forEach(f=>{const n=el('article',undefined,'fact');n.append(el('span',`${f.period_start} to ${f.period_end}`),el('strong','US$0'),el('small','Revenue reported in the retained original filing'),el('small',`Inline fact ${f.fact_id} · ${f.source_context_ref}`)); facts.append(n);});
      lead.append(facts);
      const decision=el('div',undefined,'finding-decision'); decision.append(el('h3','Percentage growth: undefined, not 0%'),el('p',d.finding),el('p','Research decision: abstain from a revenue-growth inference. Revenue is not earnings. No probability, price target or return estimate is available.'));lead.append(decision);grid.append(lead);
      const source=section('Inspect the original source');
      source.append(el('p','The original filing bytes and these two numeric contexts were checked. The live SEC website may have access restrictions; these links do not imply a new retrieval today.'));
      const actions=el('div',undefined,'source-actions'); actions.append(link('Open original 10-Q ↗',d.filing.source_primary_document_url),link('SEC filing index ↗',d.filing.source_filing_index_url));source.append(actions);
      dl(source,[['Accession',d.filing.accession],['Reported filing date',d.filing.filing_date_as_reported],['Period of report',d.filing.period_of_report],['Fiscal label as filed',`FY${d.filing.fiscal_year_as_filed} ${d.filing.fiscal_period_as_filed}`],['Earliest public time','Unknown'],['Current security mapping','Unverified']]);source.append(el('p','Calendar observation periods, filing date and fiscal labels are different fields. Do not treat this as June 2026 revenue.','footnote'));grid.append(source);
      const blockers=section('Why this is not trade-qualified');list(blockers,d.blockers);grid.append(blockers);
      const next=section('What to research next');list(next,d.next_research_steps);grid.append(next);
      const provenance=section('How the observation was checked');provenance.append(el('p','The source shows a dash with an explicit Inline XBRL zero-dash transformation. That declared transformation yields zero; missing data was not filled with zero. Exact observation dates come from the original source contexts.'));
      dl(provenance,[['Local source verification',d.provenance.source_local_verified_utc],['Finding generated',d.generated_at],['Exact download time','Unknown'],['Full accounting comparability','Not verified']]);provenance.append(link('Inspect reviewed finding JSON',PATH));grid.append(provenance);
      const detail=section('Evidence boundaries',true);const disclosure=el('details');disclosure.append(el('summary','Source hashes and limitations'));dl(disclosure,[['Original archive SHA-256',d.provenance.original_archive_sha256],['Original member SHA-256',d.provenance.original_member_sha256]]);list(disclosure,d.limitations);detail.append(disclosure);grid.append(detail);
      root.replaceChildren(grid);root.hidden=false;
      state.textContent='1 reviewed historical company finding · Saved evidence, not a live financial feed.';
    }
    let busy=false;
    async function load() {
      if(busy) return; busy=true; retry.hidden=true;root.hidden=true;root.replaceChildren();state.textContent='Loading and validating the reviewed finding…';
      try { const r=await fetcher(PATH,{cache:'no-store',signal:AbortSignal.timeout(30000)});if(!r.ok) throw new Error('Unavailable');render(validate(await r.json())); }
      catch {state.textContent='Finding unavailable or validation failed. No observation or qualification is shown. Retry the saved evidence; this does not collect new SEC data.';retry.hidden=false;}
      finally {busy=false;}
    }
    retry.addEventListener('click',load);return load();
  }
  if(typeof module!=='undefined') module.exports={validate,init,ID};
  if(typeof document!=='undefined') init(document,window.location,window.fetch.bind(window));
})();
