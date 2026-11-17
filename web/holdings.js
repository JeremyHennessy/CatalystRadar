'use strict';
function holdingsSummary(s){
 if(!s||s.status!=='HISTORICAL_13F_AS_FILED_NOT_LIVE_HOLDINGS'||s.simulation_enabled!==false||s.orders_created!==0||s.accession_joins_verified!==true)throw Error('invalid holdings manifest');
 const keys=['filing_manager_ciks','submissions','amendment_form_cover_conflicts'];
 if(!s.table_rows||!Number.isInteger(s.table_rows.holdings_infotable)||s.table_rows.holdings_infotable<0||keys.some(k=>!Number.isInteger(s[k])||s[k]<0))throw Error('invalid counts');
 const fmt=n=>n.toLocaleString();
 return `${fmt(s.filing_manager_ciks)} reporting-manager CIKs and ${fmt(s.submissions)} submissions filed ${s.filing_date_min}–${s.filing_date_max}; ${fmt(s.table_rows.holdings_infotable)} as-filed holding rows. Report periods range ${s.report_period_min}–${s.report_period_max}, not current positions. ${fmt(s.amendment_form_cover_conflicts)} form/cover amendment conflict preserved and flagged. Managers are not held-company issuers and are not added to the issuer count above.`;
}
async function startHoldings(){const target=document.getElementById('dataset-holdings');try{const r=await fetch('holdings/summary.json',{cache:'no-store'});if(!r.ok)throw Error('unavailable');target.textContent=holdingsSummary(await r.json());}catch(e){target.textContent='Institutional-holdings coverage unavailable or inconsistent; no verified count.';}}
if(typeof document!=='undefined')startHoldings();
if(typeof module!=='undefined')module.exports={holdingsSummary};
