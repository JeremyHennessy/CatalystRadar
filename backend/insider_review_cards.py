"""Source-bound filing review cards; no owner, transaction-value or trade inference."""
import argparse
from collections import Counter, defaultdict
import datetime as dt
import json,re,sqlite3
from pathlib import Path
from urllib.parse import quote
from insider_transaction_evidence import audit as source_audit, canonical_sha, date
from financial_pair_candidates import sha, write_private, publish

COHORT={'820318':'COHR','12659':'HRB','20286':'CINF','25743':'TXMD','31791':'RVTY','32604':'EMR','42582':'GT','91576':'KEY','108516':'WOR','1770450':'XRX'}
BATCHES={'2026q2':('2026-04-01','2026-06-30'),'2026q3':('2026-07-01','2026-09-30')}
LIMITATIONS=[
 'P and S mean open-market OR private purchases/sales as reported; these are filing review records, not verified market executions, recommendations or bullish/bearish signals.',
 'Counts are source nonderivative transaction rows and filings, not unique economic trades, people, positions or dollars. Derivatives and other codes are outside scope.',
 'Amendments remain separate and unreconciled. Code/direction conflicts and footnotes require original-filing review; no correction, intent, compliance or plan applicability is inferred.',
 'Dates are as-filed date-only values, not authenticated first-public or decision-time clocks. Download/retrieval clocks are unknown; generation time is an audit clock only.',
 'The ten issuer CIKs are an existing research watchlist. Its ticker labels are navigation labels, not verified current or historical security mappings. No selected rows does not mean no insider trading.',
 'Names and ticker text are as reported by each submission, not preferred current identities. Render all strings as inert text.',
 'Source links identify the retained SEC prepared archive. Individual original filing links are not verified; use accession to locate and review the original before drawing a conclusion.',
 'No owner names, addresses, quantities, prices, transaction values or footnote narratives are published. No training, execution or price-outcome qualification is granted.'
]
def cik(value):
 if not isinstance(value,str) or not re.fullmatch(r'[0-9]{1,10}',value) or int(value)==0:raise ValueError('invalid issuer CIK')
 return str(int(value))
def label(value):
 if not isinstance(value,str) or len(value)>500 or any(ord(c)<32 for c in value):raise ValueError('invalid issuer label')
 return value

def review_questions(flags,form):
 questions=['Locate this exact accession in SEC search and inspect the original transaction codes, dates and explanatory footnotes before interpreting reported activity.','Determine whether reported P/S activity was open-market or private; neither is established by these codes alone.']
 if 'PURCHASE_SALE_DIRECTION_CONTRADICTION' in flags:questions.append('Resolve the reported P/S versus acquisition/disposition code conflict from the original filing; do not repair or interpret the economic direction automatically.')
 if form.endswith('/A'):questions.append('Compare this amendment with its original and any later amendments; do not count both as independent economic trades.')
 if 'FOOTNOTE_CONTEXT_REQUIRED' in flags:questions.append('Read the referenced footnotes. Resolved footnote identifiers do not mean the explanation has been reviewed.')
 questions.append('The plan flag is submission-level only: establish any row-specific plan context from the original, without inferring intent or compliance.')
 return questions

def project(batch,records,subs):
 if batch not in BATCHES:raise ValueError('unsupported batch')
 groups=defaultdict(list);selected=[];seen=set()
 for r in records:
  s=r['submission_as_filed'];key=cik(s['ISSUERCIK'])
  if key not in COHORT or r['transaction_fields_as_filed']['TRANS_CODE'] not in {'P','S'}:continue
  acc=r['accession']
  if not re.fullmatch(r'[0-9]{10}-[0-9]{2}-[0-9]{6}',acc) or s['ACCESSION_NUMBER']!=acc:raise ValueError('accession identity')
  ident=(acc,r['transaction_key'])
  if ident in seen:raise ValueError('duplicate selected row')
  seen.add(ident)
  full=subs.get(acc)
  if full is None or full['rowid']!=r['submission_rowid'] or any(full[k]!=v for k,v in s.items()):raise ValueError('submission evidence mismatch')
  fd=date(s['FILING_DATE'])
  if fd is None or not BATCHES[batch][0]<=fd.isoformat()<=BATCHES[batch][1]:raise ValueError('filing outside batch')
  if s['DOCUMENT_TYPE'] not in {'3','3/A','4','4/A','5','5/A'}:raise ValueError('unsupported selected form')
  selected.append(r);groups[acc].append(r)
 cards=[]
 for acc,rows in sorted(groups.items()):
  sub=subs[acc];key=cik(sub['ISSUERCIK']);flags=Counter(f for r in rows for f in r['diagnostic_flags']);codes=Counter(r['transaction_fields_as_filed']['TRANS_CODE'] for r in rows)
  ds=[date(r['transaction_fields_as_filed']['TRANS_DATE']) for r in rows];valid=[d.isoformat() for d in ds if d]
  cards.append({'batch_id':batch,'accession':acc,'issuer_cik':key.zfill(10),'issuer_name_as_filed':label(sub['ISSUERNAME']),'issuer_ticker_as_filed':label(sub['ISSUERTRADINGSYMBOL']),
   'form_as_filed':sub['DOCUMENT_TYPE'],'filing_date':date(sub['FILING_DATE']).isoformat(),'period_of_report_as_filed':sub['PERIOD_OF_REPORT'] if date(sub['PERIOD_OF_REPORT']) else None,
   'selected_transaction_rows':len(rows),'reported_code_counts':dict(sorted(codes.items())),
   'transaction_date_min':min(valid) if valid else None,'transaction_date_max':max(valid) if valid else None,'invalid_transaction_date_rows':sum(d is None for d in ds),
   'diagnostic_row_counts':dict(sorted(flags.items())),'submission_plan_flag_status':rows[0]['submission_plan_flag_status'],
   'review_status':'ORIGINAL_FILING_REVIEW_REQUIRED','original_reviewed':False,'amendment_reconciled':False if sub['DOCUMENT_TYPE'].endswith('/A') else None,
   'sec_accession_lookup_url':'https://www.sec.gov/edgar/search/#/q='+quote(acc,safe=''),'source_link_status':'CONSTRUCTED_ACCESSION_SEARCH_NOT_VERIFIED_ORIGINAL',
   'review_questions':review_questions(flags,sub['DOCUMENT_TYPE']),
   'source_submission_rowid':sub['rowid'],'source_submission_sha256':canonical_sha({k:v for k,v in sub.items() if k!='rowid'}),
   'source_transaction_rowids':[r['source_rowid'] for r in rows],'source_transaction_row_hashes':[r['source_row_sha256'] for r in rows],
   'first_public_utc':None,'decision_utc':None,'training_ready':False,'execution_ready':False})
 return cards,selected

def build(config):
 if not isinstance(config,list) or len(config)!=2 or {x['batch_id'] for x in config}!=set(BATCHES):raise ValueError('exact two batches required')
 cards=[];private=[];sources=[]
 for item in sorted(config,key=lambda x:x['batch_id']):
  batch=item['batch_id'];s,records=source_audit(item['database'],item['database_sha256'],item['archive'],item['archive_sha256'])
  db=sqlite3.connect(Path(item['database']).resolve().as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
  try:subs={r['ACCESSION_NUMBER']:dict(r) for r in db.execute('SELECT rowid,* FROM insider_submission')}
  finally:db.close()
  if sha(item['database'])!=item['database_sha256']:raise ValueError('database changed')
  c,r=project(batch,records,subs);cards+=c;private +=[{'batch_id':batch,**v} for v in r]
  sources.append({'batch_id':batch,'source_archive_sha256':item['archive_sha256'],'database_sha256':item['database_sha256'],'readme_sha256':s['bundled_readme_sha256'],
   'source_url':f'https://www.sec.gov/files/datastandardsinnovation/data/insider-transactions-data-sets/{batch}_form345.zip','filing_date_start':BATCHES[batch][0],'filing_date_end':BATCHES[batch][1],
   'selected_transaction_rows':len(r),'selected_filings':len(c),'source_retrieved_at':None})
 issuers=[]
 for key,ticker in COHORT.items():
  cs=[c for c in cards if c['issuer_cik']==key.zfill(10)]
  issuers.append({'issuer_cik':key.zfill(10),'watchlist_label':ticker,'filings':len(cs),'selected_transaction_rows':sum(c['selected_transaction_rows'] for c in cs),'status':'SELECTED_FILING_EVIDENCE' if cs else 'NO_SELECTED_P_S_ROWS_IN_THESE_BATCHES'})
 payload={'schema_version':1,'status':'HISTORICAL_INSIDER_FILING_REVIEW_NOT_TRADING_SIGNALS','generated_at':dt.datetime.now(dt.timezone.utc).isoformat(),
 'sources':sources,'selection':'All reported P/S nonderivative rows for the exact existing ten-CIK watchlist in two retained SEC filing batches; no ranking or price/outcome selection.',
 'counts':{'watchlist_issuers':len(COHORT),'issuers_with_selected_rows':sum(i['filings']>0 for i in issuers),'filings':len(cards),'selected_transaction_rows':len(private)},
 'issuers':issuers,'filings':cards,'limitations':LIMITATIONS,'training_ready':False,'execution_ready':False}
 return payload,private

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--output',required=True);a=p.parse_args();out=Path(a.output).resolve()
 if out.is_relative_to(Path(__file__).resolve().parents[1]) or not out.parent.is_dir():raise ValueError('trusted private parent required')
 out.mkdir(mode=0o700,exist_ok=False);write_private(out/'INCOMPLETE',{});public,private=build(json.loads(Path(a.config).read_text()));publish(out,public,private)
 print(json.dumps(public['counts']))
