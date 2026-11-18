"""Exact issuer-CIK evidence navigation, never an event, timing or security join."""
import argparse,datetime as dt,json,re,sqlite3
from collections import Counter
from pathlib import Path
from openfigi_evidence import read_pinned
from insider_review_cards import project,BATCHES,cik
from insider_transaction_evidence import audit as insider_audit
from financial_pair_candidates import sha,write_private,publish

METRICS={'Revenues','RevenueFromContractWithCustomerExcludingAssessedTax','NetIncomeLoss','EarningsPerShareDiluted'}
def date(s):
 if not isinstance(s,str) or not re.fullmatch(r'20[0-9]{2}-[0-9]{2}-[0-9]{2}',s):raise ValueError('date-only field')
 return dt.date.fromisoformat(s).isoformat()
def validate_financial(data):
 if data.get('training_ready') is not False or data.get('execution_ready') is not False:raise ValueError('financial admission flags')
 rows=data.get('records')
 if not isinstance(rows,list) or not 1<=len(rows)<=5000:raise ValueError('financial record bound')
 groups={};seen=set()
 for r in rows:
  key=cik(r['issuer_cik']);rid=r['id']
  if not re.fullmatch('[a-f0-9]{64}',rid) or rid in seen:raise ValueError('duplicate or invalid financial case')
  seen.add(rid)
  if r['status']!='EVIDENCE_REVIEW_REQUIRED' or r['comparability_verified'] is not False or r['first_observed_utc'] is not None or r['outcome_status']!='INSUFFICIENT_EVIDENCE' or r['metric'] not in METRICS:raise ValueError('unsupported financial case state')
  end=date(r['reported_end_date']);obs=r['observations']
  if not isinstance(obs,list) or not 2<=len(obs)<=100:raise ValueError('financial observation bounds')
  dates=[];accs=[]
  for o in obs:
   if not re.fullmatch(r'[0-9]{10}-[0-9]{2}-[0-9]{6}',o['accession']):raise ValueError('financial accession')
   dates.append(date(o['filing_date_as_filed']));accs.append(o['accession'])
  names=r['issuer_names_as_filed']
  if not isinstance(names,list) or not 1<=len(names)<=100 or any(not isinstance(n,str) or len(n)>500 or any(ord(c)<32 for c in n) for n in names):raise ValueError('source issuer labels')
  g=groups.setdefault(key,{'issuer_cik':key.zfill(10),'financial_issuer_names_as_filed':set(),'financial_cases':[]})
  g['financial_issuer_names_as_filed'].update(names)
  g['financial_cases'].append({'id':rid,'metric':r['metric'],'prepared_context_date_as_reported':end,'filing_dates_as_filed':sorted(set(dates)),'accessions':sorted(set(accs)),'comparability_verified':False,'outcome_status':'INSUFFICIENT_EVIDENCE'})
 if len(groups)>500:raise ValueError('issuer bound')
 for g in groups.values():g['financial_issuer_names_as_filed']=sorted(g['financial_issuer_names_as_filed']);g['financial_cases'].sort(key=lambda r:r['id'])
 return groups

def assemble(groups,filings):
 seen=set();out=[]
 for f in filings:
  key=cik(f['issuer_cik']);fid=f['batch_id']+':'+f['accession']
  if key not in groups or fid in seen or f['batch_id'] not in BATCHES or f['training_ready'] is not False or f['execution_ready'] is not False or f['original_reviewed'] is not False:raise ValueError('insider link scope/state')
  seen.add(fid)
 for key,g in sorted(groups.items()):
  fs=[f for f in filings if cik(f['issuer_cik'])==key]
  item={**g,'insider_filing_refs':[f['batch_id']+':'+f['accession'] for f in fs],'insider_selected_rows':sum(f['selected_transaction_rows'] for f in fs),
   'relationship':'EXACT_ISSUER_CIK_ONLY_INDEPENDENT_SOURCE_EVIDENCE','insider_scope_status':'SELECTED_P_S_FILING_EVIDENCE' if fs else 'NO_SELECTED_P_S_ROWS_IN_THESE_TWO_BATCHES',
   'financial_review_url':'financial-review.html?cik='+g['issuer_cik'],'security_mapping_verified':False,'temporal_alignment_verified':False,'same_event_verified':False,'causal_relationship_verified':False,
   'research_question':'Review each source independently: resolve the financial accounting context and the insider filing/footnote context before considering whether any relationship exists.','training_ready':False,'execution_ready':False}
  out.append(item)
 return out

def build(financial_path,financial_sha,config):
 data,byte_count=read_pinned(financial_path,financial_sha,2_000_000);groups=validate_financial(data)
 if not isinstance(config,list) or len(config)!=2 or {i['batch_id'] for i in config}!=set(BATCHES):raise ValueError('exact Q2/Q3 input required')
 filings=[];private=[];sources=[]
 for item in sorted(config,key=lambda x:x['batch_id']):
  batch=item['batch_id'];summary,rows=insider_audit(item['database'],item['database_sha256'],item['archive'],item['archive_sha256'])
  db=sqlite3.connect(Path(item['database']).resolve().as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
  try:subs={r['ACCESSION_NUMBER']:dict(r) for r in db.execute('SELECT rowid,* FROM insider_submission')}
  finally:db.close()
  if sha(item['database'])!=item['database_sha256']:raise ValueError('input changed')
  cards,selected=project(batch,rows,subs,set(groups));filings+=cards;private +=[{'batch_id':batch,**r} for r in selected]
  sources.append({'batch_id':batch,'archive_sha256':item['archive_sha256'],'database_sha256':item['database_sha256'],'source_url':f'https://www.sec.gov/files/datastandardsinnovation/data/insider-transactions-data-sets/{batch}_form345.zip','filing_date_start':BATCHES[batch][0],'filing_date_end':BATCHES[batch][1],'selected_rows':len(selected),'selected_filings':len(cards),'selected_issuer_ciks':len({f['issuer_cik'] for f in cards}),'source_retrieved_at':None})
 if sha(financial_path)!=financial_sha:raise ValueError('financial source changed')
 companies=assemble(groups,filings)
 return {'version':1,'status':'EXACT_CIK_CROSS_EVIDENCE_NAVIGATION_NOT_COMBINED_SIGNAL','generated_at':dt.datetime.now(dt.timezone.utc).isoformat(),
 'financial_source':{'path':'web/company-findings/financial-review.json','sha256':financial_sha,'bytes':byte_count,'contexts':len(data['records']),'issuer_ciks':len(groups),'first_observed_utc':None},'insider_sources':sources,
 'selection':'All reported P/S nonderivative rows in retained Q2/Q3 insider filing batches whose validated issuer CIK appears in the pinned existing financial-review cases. No selection by numeric strength, prices, returns, timing proximity or outcomes.',
 'counts':{'financial_review_contexts':len(data['records']),'financial_review_issuers':len(groups),'issuers_with_selected_insider_rows':sum(bool(c['insider_filing_refs']) for c in companies),'issuers_without_selected_insider_rows':sum(not c['insider_filing_refs'] for c in companies),'selected_insider_rows':len(private),'selected_insider_filings':len(filings),'financial_contexts_for_linked_issuers':sum(len(c['financial_cases']) for c in companies if c['insider_filing_refs'])},
 'companies':companies,'insider_filings':filings,'training_ready':False,'execution_ready':False,
 'limitations':['CIK identifies the issuer reporting entity only. It does not establish the same tradable security, ownership class, event, investment thesis or causal connection.','The prepared financial context date is a coarse as-reported context key, not a verified exact duration/end date. Financial periods, financial filing dates, insider transaction dates and insider filing dates are separate source fields. No decision-time alignment, lead/lag test or historical availability is inferred.','All financial cases remain unqualified context reviews. Insider P/S includes open-market OR private activity; no quantities, prices, dollar exposure, people, intent or net buying/selling inference is published.','Amendments and footnote warnings remain source-specific. Counts are source rows/filings, not unique economic trades. No selected rows is not no insider trading; this selection excludes other codes, derivatives and other filing batches.','Names/tickers stay attached to their own sources. Do not reconcile names or join symbols automatically; render source labels as inert text.','This is navigable research evidence, not a combined score, forecast, recommendation, current catalyst or training example. Source retrieval/first-public clocks remain unknown; generated_at is only this processing run.','Existing public source manifests, held reports, ledger and schedules are not modified. The underlying prepared archives were previously independently audited against persisted databases. Input hashes alone do not independently establish that derivation.']},private

def save(financial_path,financial_sha,config,out):
 out=Path(out).resolve()
 if out.exists() or out.is_relative_to(Path(__file__).resolve().parents[1]) or not out.parent.is_dir():raise ValueError('new trusted private output required')
 out.mkdir(mode=0o700);write_private(out/'INCOMPLETE',{});public,private=build(financial_path,financial_sha,config);publish(out,public,private);return public
if __name__=='__main__':
 from private_prices import unique_object
 p=argparse.ArgumentParser();p.add_argument('--financial',required=True);p.add_argument('--financial-sha',required=True);p.add_argument('--config',required=True);p.add_argument('--out',required=True);a=p.parse_args();raw=Path(a.config).read_bytes()
 if len(raw)>20000:raise ValueError('config bound')
 c=json.loads(raw,object_pairs_hook=unique_object,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('invalid constant')));print(json.dumps(save(a.financial,a.financial_sha,c,a.out)['counts']))
