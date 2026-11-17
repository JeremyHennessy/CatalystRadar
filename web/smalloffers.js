'use strict';
function smallOffersSummary(s){
 if(!s||s.status!=='HISTORICAL_CF_REGA_AS_FILED_NOT_SIGNALS'||s.simulation_enabled!==false||s.orders_created!==0)throw Error('invalid manifest');
 for(const kind of ['cf','rega']){const d=s.datasets?.[kind];if(!d||d.accession_joins_verified!==true||[d.submissions,d.submission_issuer_ciks].some(n=>!Number.isInteger(n)||n<0))throw Error('invalid counts');}
 const f=n=>n.toLocaleString(),c=s.datasets.cf,r=s.datasets.rega;
 return `Crowdfunding: ${f(c.submissions)} submissions from ${f(c.submission_issuer_ciks)} submission-issuer CIKs. Regulation A: ${f(r.submissions)} submissions from ${f(r.submission_issuer_ciks)} submission-issuer CIKs. Both cover filings in July–September 2026. These include amendments and lifecycle reports, not unique completed offerings. Counts are separate and are not added to other issuer totals.`;
}
async function startSmallOffers(){const t=document.getElementById('dataset-smalloffers');try{const r=await fetch('smalloffers/summary.json',{cache:'no-store'});if(!r.ok)throw Error('unavailable');t.textContent=smallOffersSummary(await r.json());}catch(e){t.textContent='Crowdfunding/Regulation A coverage unavailable or inconsistent; no verified count.';}}
if(typeof document!=='undefined')startSmallOffers();
if(typeof module!=='undefined')module.exports={smallOffersSummary};
