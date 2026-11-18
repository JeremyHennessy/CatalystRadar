"""One narrow, reproducible SEC source-backed observation, not a trading signal."""
import argparse,datetime as dt,json,re
from decimal import Decimal
from pathlib import Path
from source_prepared_correspondence import audit as correspondence,USD
from openfigi_evidence import read_pinned
from financial_pair_candidates import write_private,sha

CIK='1697884';ACCESSION='0001640334-26-001075'
FACTS={'fid_2230':('2025-05-01','2025-07-31'),'fid_2231':('2024-05-01','2024-07-31')}

def build(summary,results,receipt):
 if summary.get('accession_from_pinned_manifest')!=ACCESSION or receipt.get('accession')!=ACCESSION or receipt.get('issuer_cik_verified')!=CIK:raise ValueError('case identity')
 if summary.get('comparability_verified') is not False or summary.get('training_ready') is not False or summary.get('execution_ready') is not False:raise ValueError('unexpected admission')
 if summary.get('archive_sha256')!=receipt.get('zip_sha256') or summary.get('raw_member_sha256')!=receipt.get('primary_member_sha256'):raise ValueError('source binding')
 expected=f'https://www.sec.gov/Archives/edgar/data/{CIK}/{ACCESSION.replace("-","")}/'
 if receipt.get('source_url')!=expected+ACCESSION+'-xbrl.zip' or receipt.get('primary_member')!='vsbc_10q.htm':raise ValueError('source path')
 selected={};submission=None
 for result in results:
  candidate=result.get('candidate')
  if not candidate:continue
  for f in candidate['source_group']['occurrences']:
   if f['fact_id'] not in FACTS:continue
   if f['fact_id'] in selected or result['disposition']!='candidate_numeric_equal' or candidate['numeric_equal'] is not True:raise ValueError('ambiguous or unequal evidence')
   start,end=FACTS[f['fact_id']]
   if (f['concept']!={'namespace':'http://fasb.org/us-gaap/2025','local_name':'Revenues'} or f['period']!={'kind':'duration','startDate':start,'endDate':end} or f['unit']!={'kind':'simple','measures':[USD]} or f['dimension_or_scenario_present'] is not False or f['numeric_conversion_verified'] is not True or f['numeric_value']!='0' or f['issuer_identifier_as_filed']!='0001697884' or f['issuer_identifier_scheme']!='http://www.sec.gov/CIK' or f['raw_member_sha256']!=summary['raw_member_sha256']):raise ValueError('unsupported source fact')
   if f['text_untransformed']!='-' or f['format']!={'namespace':'http://www.xbrl.org/inlineXBRL/transformation/2015-02-26','local_name':'zerodash'} or f['decimals_as_filed']!='0':raise ValueError('source transformation')
   sub=candidate['prepared_submission'];num=candidate['prepared_num']
   if sub['adsh']!=ACCESSION or sub['cik']!=CIK or sub['period']!='20250731' or sub['filed']!='20260617' or sub['form']!='10-Q':raise ValueError('prepared identity')
   if submission is not None and submission!=sub:raise ValueError('conflicting submission')
   submission=sub
   if (num['adsh']!=ACCESSION or num['tag']!='Revenues' or num['version']!='us-gaap/2025' or num['ddate']!=end.replace('-','') or num['qtrs']!='1' or num['uom']!='USD' or num['segments']!='' or num['coreg']!='' or num['footnote']!='' or not re.fullmatch(r'0(?:\.0+)?',num['value'])):raise ValueError('prepared correspondence')
   selected[f['fact_id']]={'fact_id':f['fact_id'],'concept':'Revenues','taxonomy_namespace':f['concept']['namespace'],'value':'0','currency':'USD','period_start':start,'period_end':end,'source_context_ref':f['context_ref'],'context_serialization_sha256':f['context_serialization_sha256'],'declared_decimals':'0','source_literal':'-','source_transform':'TRR3 zerodash','dimension_or_scenario_present':False,'prepared_num_rowid':num['rowid'],'prepared_value_as_filed':num['value'],'prepared_end_date':num['ddate'],'prepared_qtrs':'1','prepared_exact_start_date_verified':False}
 if set(selected)!=set(FACTS):raise ValueError('missing case facts')
 clock=dt.datetime.fromisoformat(receipt['local_verified_utc'])
 if clock.tzinfo is None or clock>dt.datetime.now(dt.timezone.utc):raise ValueError('local verification clock')
 name=submission['name']
 if not isinstance(name,str) or len(name)>300 or any(ord(c)<32 for c in name):raise ValueError('issuer label')
 return {'version':1,'id':'vitaspring-revenue-zero-baseline','status':'SOURCE_BACKED_HISTORICAL_OBSERVATION_NOT_TRADING_QUALIFIED','generated_at':dt.datetime.now(dt.timezone.utc).isoformat(),'issuer':{'cik':CIK.zfill(10),'name_as_filed':name,'ticker':None,'security_mapping_verified':False},'title':'Historical revenue evidence: zero baseline prevents a percentage-growth finding','finding':'The retained filing reports revenue of $0 for May–July 2025 and $0 for May–July 2024. A percentage growth rate using the zero comparison base is undefined; this evidence does not establish a revenue-growth lead.','research_disposition':'ABSTAIN_FROM_REVENUE_GROWTH_INFERENCE','facts':[selected[k] for k in FACTS],'calculation':{'metric':'percentage_revenue_growth','value':None,'reason':'ZERO_COMPARISON_BASE','not_zero_percent':True},'filing':{'accession':ACCESSION,'form':'10-Q','period_of_report':'2025-07-31','filing_date_as_reported':'2026-06-17','fiscal_year_as_filed':submission['fy'],'fiscal_period_as_filed':submission['fp'],'source_filing_index_url':expected+ACCESSION+'-index.html','source_primary_document_url':expected+'vsbc_10q.htm','primary_member':'vsbc_10q.htm'},'provenance':{'original_archive_sha256':summary['archive_sha256'],'original_member_sha256':summary['raw_member_sha256'],'identity_manifest_sha256':summary['identity_manifest_sha256'],'prepared_archive_sha256':summary['prepared_archive_sha256'],'prepared_database_sha256':summary['prepared_database_sha256'],'prepared_submission_rowid':submission['rowid'],'source_local_verified_utc':receipt['local_verified_utc'],'source_exact_download_utc':None,'source_first_public_utc':None,'original_bytes_retained':True,'source_numeric_extraction_checked':True,'prepared_numeric_correspondence':True,'full_accounting_comparability_verified':False},'blockers':['These are historical 2025/2024 reporting periods in a filing reported in June 2026, not current company financials.','Zero comparison base prevents a percentage revenue-growth calculation. Revenue is not earnings; no earnings-growth conclusion is made.','The second diagnostic filing was not retained after a timeout. Cross-filing comparability, novelty and earliest public timing remain unverified.','Issuer CIK is not verified tradable-security identity. No licensed price/outcome or execution evidence is joined.'],'next_research_steps':['Review the linked original statement and accounting context before interpreting the observation.','Use a separately authorized source with a nonzero comparable baseline if testing a revenue-growth hypothesis; do not fabricate a percentage here.','Establish security identity, decision-time source availability and permitted outcome data before any predictive evaluation.'],'training_ready':False,'execution_ready':False,'probability':None,'price_target':None,'return_estimate':None,'limitations':['This card is a narrow source-reported numerical observation, not independent verification of company accounting truth, a current catalyst or financial advice.','Dash-to-zero interpretation follows the declared Inline XBRL transformation; missing values are not imputed to zero.','Exact source start/end dates come from retained inline contexts. Prepared qtrs/end-date agreement alone does not prove full duration or accounting equivalence.','Context hashes cover ElementTree serialization, not original context byte slices or canonical XML. Raw member/archive hashes bind original retained bytes.','Sources were retained retrospectively. Local verification time is not download or first-public time; no historical decision or future outcome is invented.','No private addresses, contacts, raw narratives, licensed price data or held research-report contents are republished.']}

def save(config,out):
 out=Path(out).resolve()
 if out.exists() or out.is_relative_to(Path(__file__).resolve().parents[1]) or not out.parent.is_dir():raise ValueError('trusted new private output')
 out.mkdir(mode=0o700);write_private(out/'INCOMPLETE',{})
 summary,results=correspondence(**config);receipt,_=read_pinned(config['manifest'],config['manifest_sha'],100000);card=build(summary,results,receipt)
 write_private(out/'finding.json',card);write_private(out/'COMPLETE.json',{'finding_sha256':sha(out/'finding.json')});(out/'INCOMPLETE').unlink();return card

if __name__=='__main__':
 from private_prices import unique_object
 p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();b=a.config.read_bytes()
 if len(b)>20000:raise ValueError('config bound')
 c=json.loads(b,object_pairs_hook=unique_object,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('invalid constant')));print(json.dumps(save(c,a.out)))
