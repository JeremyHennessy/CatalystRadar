'use strict';
function financialHistorySummary(s){
 if(!s||s.status!=='HISTORICAL_FINANCIAL_Q2_NOT_COMPARABLE_FACTS'||s.simulation_enabled!==false||s.orders_created!==0||s.accession_joins_verified!==true)throw Error('invalid manifest');
 for(const n of [s.submissions,s.issuer_ciks,s.table_rows?.financial_num,s.rows_missing_tag_definitions])if(!Number.isInteger(n)||n<0)throw Error('invalid counts');
 const f=n=>n.toLocaleString();return `${f(s.submissions)} financial submissions across ${f(s.issuer_ciks)} issuer CIKs filed ${s.filing_date_min}–${s.filing_date_max}; ${f(s.table_rows.financial_num)} numeric rows retained. This is a Q2 filing-date batch with mixed fiscal periods, not Q2-only results. ${f(s.rows_missing_tag_definitions)} rows lack matching taxonomy definitions. Counts remain separate from the later baseline; no automatic growth comparisons or financial totals.`;
}
async function startFinancialHistory(){const t=document.getElementById('dataset-financial-history');try{const r=await fetch('financial-history/summary.json',{cache:'no-store'});if(!r.ok)throw Error('unavailable');t.textContent=financialHistorySummary(await r.json());}catch(e){t.textContent='Earlier financial coverage unavailable or inconsistent; no verified count.';}}
if(typeof document!=='undefined')startFinancialHistory();
if(typeof module!=='undefined')module.exports={financialHistorySummary};
