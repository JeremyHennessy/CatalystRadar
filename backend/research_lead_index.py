"""Deterministic navigation index over released research, not a signal generator."""
import argparse,hashlib,json,re
from pathlib import Path
from collections import Counter
from openfigi_evidence import read_pinned
from financial_insider_links import validate_financial
from company_disclosure_links import project as disclosure_project,PATHS as DISCLOSURE_PATHS
PATHS={**DISCLOSURE_PATHS,'insider':'web/company-findings/financial-insider-links.json','ieh':'web/company-findings/ieh-reported-revenue.json','holdings':'docs/research/holdings-figi-2026-11-17.json','mapping':'docs/research/openfigi-watchlist-2026-11-17.json'}

def holdings_gap(holdings,mapping):
 if holdings.get('status')!='EXACT_SOURCE_REPORTED_IDENTIFIER_CORRESPONDENCE_ONLY' or mapping.get('status')!='OBSERVED_IDENTIFIER_CANDIDATES_NOT_HISTORICAL_SECURITY_LINKS':raise ValueError('holdings evidence state')
 for source in (holdings,mapping):
  if source.get('training_ready') is not False or source.get('execution_ready') is not False:raise ValueError('holdings admission')
 if holdings.get('historical_security_link_verified') is not False:raise ValueError('changed security qualification requires review')
 for key in ('request','response','receipt'):
  a=holdings.get('mapping_'+key+'_sha256');b=mapping.get(key+'_sha256')
  if not isinstance(a,str) or not re.fullmatch('[a-f0-9]{64}',a) or a!=b:raise ValueError('mapping provenance mismatch')
 if holdings.get('mapping_observed_at')!=mapping.get('observed_at'):raise ValueError('mapping clock mismatch')
 jobs=mapping.get('mappings')
 if not isinstance(jobs,list) or not jobs or len(jobs)!=mapping.get('job_count'):raise ValueError('mapping job coverage')
 positions=[]
 for job in jobs:
  positions.append(job['request_position'])
  if job.get('issuer_cik_link_verified') is not False or job.get('historical_ticker_ownership_verified') is not False or job.get('training_ready') is not False:raise ValueError('new issuer mapping requires review')
 if sorted(positions)!=list(range(len(jobs))):raise ValueError('mapping position coverage')
 census=holdings['census'];keys=('holding_rows','blank_rows','valid_checksum_rows','invalid_structure_or_checksum_rows')
 if any(type(census.get(k)) is not int or census[k]<0 for k in keys) or census['holding_rows']!=sum(census[k] for k in keys[1:]):raise ValueError('holding census')
 for key in ('matched_holding_rows','matched_accessions','matched_identifier_strings'):
  if type(holdings.get(key)) is not int or not 0<=holdings[key]<=census['valid_checksum_rows']:raise ValueError('correspondence counts')
 return {'status':'BLOCKED_MISSING_VERIFIED_ISSUER_SECURITY_MAPPING','company_holdings_assessed':False,'company_position_count':None,'retained_holding_rows':census['holding_rows'],'existing_identifier_correspondences':holdings['matched_holding_rows'],'correspondence_scope':'Exact source-reported FIGI strings against ten retained ticker-query mappings, not issuer-CIK or historical security associations. These are not holdings of the research cohort.','mapping_observed_at':mapping['observed_at'],'first_public_utc':None,'required_evidence':['A permitted source explicitly binding reporting issuer CIK to the held security identifier, not the reporting manager CIK, company name or ticker similarity.','Security-class and identifier scope (CUSIP/FIGI/composite/share class), including option or debt distinctions, verified rather than inferred from a checksum.','Effective historical identity intervals covering each report period and corporate actions; a current mapping cannot establish past ownership.','Source filing/amendment/confidentiality context and observation/publication clocks before any ownership or decision-time inference.'],'next_action':'Obtain and independently review a permitted issuer-CIK to security-identifier association with class and effective dates. Until then keep company holdings unknown; do not attach candidate holdings by manager, name or ticker.','source_keys':['holdings','mapping'],'training_ready':False,'execution_ready':False}

def index(data,pins):
 gap=holdings_gap(data['holdings'],data['mapping'])
 groups=validate_financial(data['financial']);disclosures=disclosure_project(data['financial'],data['catalog'],data['manifest'])
 insider=data['insider']
 if insider.get('status')!='EXACT_CIK_CROSS_EVIDENCE_NAVIGATION_NOT_COMBINED_SIGNAL' or insider.get('training_ready') is not False or insider.get('execution_ready') is not False or insider['financial_source']['sha256']!=pins['financial']:raise ValueError('insider financial version/state')
 companies=insider.get('companies');filings=insider.get('insider_filings')
 if not isinstance(companies,list) or len(companies)!=len(groups) or not isinstance(filings,list) or len(filings)>10000:raise ValueError('insider bounds')
 by={};refs={}
 for f in filings:
  ci=f['issuer_cik'];acc=f['accession'];batch=f['batch_id'];ref=batch+':'+acc
  if not re.fullmatch('[0-9]{10}',ci) or not int(ci) or batch not in ('2026q2','2026q3') or not re.fullmatch('[0-9]{10}-[0-9]{2}-[0-9]{6}',acc) or ref in refs:raise ValueError('insider reference')
  refs[ref]=ci
 for c in companies:
  ci=c['issuer_cik'];key=str(int(ci))
  if ci!=key.zfill(10) or key not in groups or ci in by:raise ValueError('insider cohort')
  expected={x['id'] for x in groups[key]['financial_cases']};actual=[x['id'] for x in c['financial_cases']]
  if len(actual)!=len(set(actual)) or set(actual)!=expected:raise ValueError('financial case references')
  selected=c['insider_filing_refs']
  if not isinstance(selected,list) or len(selected)!=len(set(selected)) or set(selected)!={r for r,k in refs.items() if k==ci}:raise ValueError('insider coverage')
  by[ci]=selected
 if set(refs.values())-set(by):raise ValueError('orphan insider filing')
 dc={c['issuer_cik']:c for c in disclosures['companies']};records=[]
 for key,g in sorted(groups.items(),key=lambda x:int(x[0])):
  ci=key.zfill(10);cases=g['financial_cases'];selected=by[ci];d=dc[ci]
  types=['FINANCIAL_CONTEXT_REVIEW']
  if selected:types.append('INSIDER_ORIGINAL_FILING_REVIEW')
  if d['disclosure_accessions']:types.append('ACQUISITION_DISPOSAL_DISCLOSURE_REVIEW')
  records.append({'id':'issuer-'+ci,'issuer_cik':ci,'labels_by_source':{'financial_as_filed':sorted(g['financial_issuer_names_as_filed'])},'research_types':types,'research_question':'Do the repeated financial contexts describe comparable accounting periods and scope? Review original filings before interpreting numeric differences; inspect any independently linked insider or acquisition/disposal evidence separately.','status':'HISTORICAL_EVIDENCE_REVIEW_REQUIRED','financial_case_ids':sorted(x['id'] for x in cases),'metrics':sorted({x['metric'] for x in cases}),'financial_filing_dates_as_filed':sorted({day for x in cases for day in x['filing_dates_as_filed']}),'insider_filing_refs':sorted(selected),'insider_coverage':'SELECTED_ROWS_IN_Q2_Q3_BATCHES' if selected else 'NO_SELECTED_P_S_ROWS_IN_Q2_Q3_BATCHES','disclosure_accessions':d['disclosure_accessions'],'disclosure_coverage':d['status'],'evidence_url':'financial-review.html?cik='+ci,'source_keys':['financial','insider','catalog','manifest'],'blockers':['Exact financial durations, accounting scope and amendments are not qualified.','Source first-public and decision-time availability are unknown.','CIK linkage is issuer-only; security identity, temporal alignment, causality and outcomes are unverified.'],'next_action':'Open this company investigation and inspect each original source and context before making any interpretation.','first_public_utc':None,'historical_availability_verified':False,'accounting_comparability_verified':False,'training_ready':False,'execution_ready':False})
 ieh=data['ieh'];ci=ieh['issuer']['cik']
 if ieh.get('id')!='ieh-reported-quarterly-revenue' or ci!='0000050292' or ieh.get('status')!='ISSUER_REPORTED_COMPARISON_NOT_INDEPENDENTLY_COMPARABLE' or ieh.get('training_ready') is not False or ieh.get('execution_ready') is not False or ieh['comparison']['accounting_comparability_verified'] is not False or ieh['provenance']['first_public_utc'] is not None or ieh['provenance']['historical_availability_verified'] is not False:raise ValueError('unsupported reported comparison')
 comparison=ieh['comparison']
 if comparison['current_value']!='10700084' or comparison['prior_value']!='7077592' or comparison['current_period_end']!='2026-09-30' or comparison['prior_period_end']!='2025-09-30' or comparison['reported_percent_increase']!='51' or comparison['reported_percent_matches_nearest_whole'] is not True or comparison['currency_iso'] is not None or comparison['current_period_start'] is not None or comparison['prior_period_start'] is not None or ieh['filing']['accession']!='0001174947-26-000991':raise ValueError('reported comparison requires renewed review')
 if any(r['issuer_cik']==ci for r in records):raise ValueError('issuer overlap requires explicit source consolidation review')
 name=ieh['issuer']['name_as_filed']
 if not isinstance(name,str) or not 1<=len(name)<=500 or any(ord(c)<32 for c in name):raise ValueError('issuer label')
 records.append({'id':'issuer-'+ci,'issuer_cik':ci,'labels_by_source':{'release_as_filed':[name]},'research_types':['ISSUER_REPORTED_COMPARISON_REVIEW'],'research_question':'IEH reported higher quarterly revenue and the rounded arithmetic agrees. Can the original financial statements establish currency, exact durations, accounting scope and novelty?','status':'HISTORICAL_ISSUER_REPORTED_COMPARISON_UNQUALIFIED','finding_ref':ieh['id'],'source_accession':ieh['filing']['accession'],'reported_period_ends':[ieh['comparison']['current_period_end'],ieh['comparison']['prior_period_end']],'recorded_source_retrieved_utc':ieh['provenance']['retrieved_utc_as_recorded'],'financial_case_ids':[],'metrics':['IssuerReportedRevenue'],'insider_filing_refs':[],'insider_coverage':'NOT_EVALUATED_IN_THIS_FINANCIAL_COHORT','disclosure_accessions':[],'disclosure_coverage':'NOT_EVALUATED_IN_THIS_FINANCIAL_COHORT','evidence_url':'company-ieh.html','source_keys':['ieh'],'blockers':['Explicit ISO currency and exact quarter start dates remain unknown.','Underlying 10-Q, accounting scope, amendments and comparability remain unchecked.','Recorded retrieval is retrospective, not first-public timing, novelty or a current catalyst.','Security identity, permitted outcomes and decision-time availability remain unverified.'],'next_action':'Open the issuer-reported finding and review its original quarterly statements before treating the comparison as comparable growth.','first_public_utc':None,'historical_availability_verified':False,'accounting_comparability_verified':False,'training_ready':False,'execution_ready':False})
 for record in records:
  record['holdings_coverage']='NOT_ASSESSED_MISSING_VERIFIED_ISSUER_SECURITY_MAPPING'
  record['holdings_gap_ref']='holdings_linkage'
 records.sort(key=lambda r:r['issuer_cik'])
 return {'version':2,'status':'DETERMINISTIC_COMPANY_RESEARCH_QUEUE_NOT_SIGNALS','selection':'All 106 released financial-review issuers plus the separate released IEH issuer-reported comparison. Grouping is by issuer only, not event deduplication or a claim of comprehensive company coverage.','order':'Ascending padded issuer CIK; no strength, profitability, timeliness or return ranking.','counts':{'company_entries':len(records),'financial_review_issuers':len(groups),'reported_comparison_only_issuers':1,'financial_contexts':sum(len(r['financial_case_ids']) for r in records),'with_selected_insider_filings':sum(bool(r['insider_filing_refs']) for r in records),'with_selected_disclosure_filings':sum(bool(r['disclosure_accessions']) for r in records)},'records':records,'holdings_linkage':gap,'training_ready':False,'execution_ready':False,'limitations':['Research leads are questions with cited evidence and missing prerequisites, not forecasts or buy/sell recommendations. No profitability score, probability, price target or outcome estimate is computed.','Dates and labels remain source-specific. Filing dates, period ends, retrieval clocks and first-public times are not interchangeable; no current catalyst or historical availability is established.','Insider P/S includes open-market OR private activity. Disclosure concepts are unadjudicated records, not confirmed deals. Exact CIK does not establish a common event or economic cause.','Index entries point to existing released research rather than copy narratives, transaction values, private owners or source archives. Render labels as inert text. Unknown coverage is distinct from a scoped absence.','This index is reproducible from pinned released inputs. It does not fetch data, regenerate held reports, train a model or enable any order.']}
def build(root,pins):
 data={};sources={}
 for key,path in PATHS.items():
  data[key],size=read_pinned(Path(root)/path,pins[key],5_000_000);sources[key]={'path':path,'sha256':pins[key],'bytes':size}
 if data['manifest']['metadata']!={'sha256':pins['catalog'],'byte_count':sources['catalog']['bytes']}:raise ValueError('catalog pin')
 if data['insider']['financial_source']['bytes']!=sources['financial']['bytes']:raise ValueError('financial source bytes')
 result=index(data,pins);result['sources']=sources;return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--out',required=True)
 for k in PATHS:p.add_argument('--'+k+'-sha',required=True)
 a=p.parse_args();out=Path(a.out)
 if out.exists():raise ValueError('refuse overwrite')
 result=build(a.root,{k:getattr(a,k+'_sha') for k in PATHS});out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['counts']))
