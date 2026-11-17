'use strict';
function formDSummary(s){
 if(!s||s.status!=='HISTORICAL_FORM_D_NOTICES_NOT_INVESTMENT_SIGNALS'||s.simulation_enabled!==false||s.orders_created!==0||s.accession_joins_verified!==true||s.one_primary_issuer_per_submission_verified!==true)throw Error('invalid manifest');
 for(const n of [s.submissions,s.issuer_ciks_in_batch,s.submission_types?.['D/A'],s.indefinite_total_offering_amount_rows])if(!Number.isInteger(n)||n<0)throw Error('invalid counts');
 const f=n=>n.toLocaleString();return `${f(s.submissions)} notices filed ${s.filing_date_min}–${s.filing_date_max}, covering ${f(s.issuer_ciks_in_batch)} issuer CIKs in this batch; ${f(s.submission_types['D/A'])} amendments. ${f(s.indefinite_total_offering_amount_rows)} offering amounts are explicitly Indefinite. These include private issuers/funds, not a listed-company universe or completed financing rounds. Counts remain separate from other issuer coverage.`;
}
async function startFormD(){const t=document.getElementById('dataset-formd');try{const r=await fetch('formd/summary.json',{cache:'no-store'});if(!r.ok)throw Error('unavailable');t.textContent=formDSummary(await r.json());}catch(e){t.textContent='Exempt-offering coverage unavailable or inconsistent; no verified count.';}}
if(typeof document!=='undefined')startFormD();
if(typeof module!=='undefined')module.exports={formDSummary};
