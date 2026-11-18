"""Predefined new-issuer revenue review packets, not comparable growth."""
import argparse,hashlib,json,re,sqlite3,zipfile
from pathlib import Path
from datetime import datetime
from collections import Counter
from openfigi_evidence import read_pinned,stamp
from research_retrieval import SNAPSHOT,SHA,SIZE,normalize_cik
from financial_pair_candidates import sha,classify,NUM_FIELDS,write_private
from financial_archive_facts import read_source_rows
from sec_prepared_data import inventory,SCHEMAS
from material_agreement_screen import build as original_screen
METRICS=('Revenues','RevenueFromContractWithCustomerExcludingAssessedTax')
TIES=['accession','current.tag','current.version','batch','submission_period','current.ddate','prior.ddate','current.qtrs','prior.qtrs','current.uom','prior.uom','current.segments','prior.segments','current.coreg','prior.coreg','current.rowid','prior.rowid']
BATCHES={'q1':'q1_2026_filing_batch','q2':'q2_2026_filing_batch','q3':'q3_2026_filing_batch','q4':'q4_2025_filing_batch'}
def encode(obj):return (json.dumps(obj,ensure_ascii=True,sort_keys=True,separators=(',',':'))+'\n').encode()
def digest(raw):return hashlib.sha256(raw).hexdigest()
def key(batch,p):
 return tuple(p[k.split('.')[0]][k.split('.')[1]] if '.' in k else batch if k=='batch' else p[k] for k in TIES)
def select(batches,excluded):
 candidates=[];counts=Counter();identities=set()
 for batch,pairs in sorted(batches.items()):
  for p in pairs:
   counts['input_pairs']+=1
   if p['current']['tag'] not in METRICS:counts['excluded_other_metric_pairs']+=1;continue
   cik=normalize_cik(p['issuer_cik_as_filed']);identity=key(batch,p)
   if identity in identities:raise ValueError('duplicate full candidate identity')
   identities.add(identity)
   if cik in excluded:counts['excluded_existing_queue_pairs']+=1;continue
   if not re.fullmatch('[0-9]{8}',p['filing_date_as_filed']):raise ValueError('filing date')
   datetime.strptime(p['filing_date_as_filed'],'%Y%m%d')
   if not re.fullmatch('[0-9]{10}-[0-9]{2}-[0-9]{6}',p['accession']):raise ValueError('accession format')
   candidates.append((cik,batch,p));counts['eligible_pairs']+=1
 eligible=sorted({c for c,_,_ in candidates},key=int);chosen=[]
 if len(eligible)<5:raise ValueError('insufficient predefined cohort')
 for cik in eligible[:5]:
  pool=[(b,p) for c,b,p in candidates if c==cik]
  latest=max(p['filing_date_as_filed'] for b,p in pool)
  b,p=min(((b,p) for b,p in pool if p['filing_date_as_filed']==latest),key=lambda x:key(*x))
  chosen.append((cik,b,p,len(pool)))
 counts['eligible_ciks']=len(eligible);counts['selected_ciks']=5;counts['eligible_unselected_ciks']=len(eligible)-5
 counts['eligible_pairs_not_selected']=len(candidates)-5
 return chosen,dict(sorted(counts.items()))
def inputs(root,workspace,plan_path,plan_sha):
 plan,_=read_pinned(plan_path,plan_sha,20000)
 stamp(plan['created_at_utc'])
 if plan['policy_version']!=2 or plan['issuer_limit']!=5 or plan['metrics']!=list(METRICS) or plan['tie_break_fields']!=TIES or set(plan['inputs'])!=set(BATCHES):raise ValueError('unsupported policy')
 if plan['queue']!={'path':SNAPSHOT,'sha256':SHA}:raise ValueError('excluded cohort pin')
 queue,_=read_pinned(Path(root)/SNAPSHOT,SHA,SIZE);excluded={r['issuer_cik'] for r in queue['records']}
 if len(excluded)!=108:raise ValueError('excluded cohort scope')
 batches={};summaries={}
 for b,m in plan['inputs'].items():
  directory=Path(workspace)/m['directory']
  if (directory/'INCOMPLETE').exists():raise ValueError('incomplete batch')
  complete,_=read_pinned(directory/'COMPLETE.json',m['files']['COMPLETE.json'],10000)
  for n,k in [('candidate-pairs.json','candidate_pairs_sha256'),('summary.json','summary_sha256')]:
   if complete[k]!=m['files'][n]:raise ValueError('completion mismatch')
  batches[b],_=read_pinned(directory/'candidate-pairs.json',m['files']['candidate-pairs.json'],100000000)
  summaries[b],_=read_pinned(directory/'summary.json',m['files']['summary.json'],20000)
  if summaries[b]['candidate_pairs']!=len(batches[b]) or summaries[b]['comparability_verified']is not False or summaries[b]['training_ready']is not False:raise ValueError('batch scope mismatch')
 return plan,batches,summaries,excluded

def audit(root,workspace,plan_path,plan_sha,databases,archives,original_zip,original_receipt,original_package):
 plan,batches,summaries,excluded=inputs(root,workspace,plan_path,plan_sha)
 chosen,counts=select(batches,excluded)
 # Inspect only exact accessions in this explicit retained original inventory.
 originals=original_screen(original_zip);original_acc={r['accession'] for r in originals['packages']}
 receipt_sha='7faa83a8083bb5c5ec2667a773be2a35a782701feb2ebed656229f4edf42f334'
 receipt,_=read_pinned(original_receipt,receipt_sha,1000000)
 if sha(original_package)!=receipt['zip_sha256'] or Path(original_package).stat().st_size!=receipt['zip_byte_count']:raise ValueError('original XBRL pin')
 original_acc.add(receipt['accession']);packets=[];sources={}
 for b in sorted({b for _,b,_,_ in chosen}):
  summary=summaries[b];db=Path(databases[BATCHES[b]]);archive=Path(archives[BATCHES[b]])
  if sha(db)!=summary['database_sha256'] or sha(archive)!=summary['source_archive_sha256']:raise ValueError('raw source pin')
  conn=sqlite3.connect(db.resolve().as_uri()+'?mode=ro',uri=True);conn.row_factory=sqlite3.Row
  try:
   pending=[];wanted={'num.txt':set(),'sub.txt':set(),'tag.txt':set(),'pre.txt':set()}
   for cik,batch,p,alternatives in chosen:
    if batch!=b:continue
    if p['database_sha256']!=summary['database_sha256'] or p['source_archive_sha256']!=summary['source_archive_sha256']:raise ValueError('candidate provenance mismatch')
    subs=[dict(x) for x in conn.execute('SELECT rowid,* FROM financial_sub WHERE adsh=?',(p['accession'],))]
    if len(subs)!=1 or normalize_cik(subs[0]['cik'])!=cik:raise ValueError('submission identity')
    sub=subs[0];tag=p['taxonomy'];tags=[dict(x) for x in conn.execute('SELECT rowid,* FROM financial_tag WHERE tag=? AND version=?',(p['current']['tag'],p['current']['version']))]
    if tags!=[tag]:raise ValueError('taxonomy reference changed')
    nums=[dict(x) for x in conn.execute("SELECT rowid,* FROM financial_num WHERE adsh=? AND tag=? AND version=? AND uom=? AND qtrs='1' AND segments='' AND coreg=''",(p['accession'],p['current']['tag'],p['current']['version'],p['current']['uom']))]
    reason,recheck=classify([{k:n[k] for k in NUM_FIELDS} for n in nums],sub,{(tag['tag'],tag['version']):tags})
    if reason!='context_matched_candidate' or any(recheck[k]!=p[k] for k in recheck):raise ValueError('candidate no longer matches source')
    presentation=[dict(x) for x in conn.execute('SELECT rowid,* FROM financial_pre WHERE adsh=? AND tag=? AND version=?',(p['accession'],tag['tag'],tag['version']))]
    if presentation!=p['presentation']:raise ValueError('presentation reference changed')
    rows={'num.txt':[n for n in nums if n['rowid'] in (p['current']['rowid'],p['prior']['rowid'])],'sub.txt':[sub],'tag.txt':tags,'pre.txt':presentation}
    for member,items in rows.items():wanted[member].update(x['rowid'] for x in items)
    pending.append((cik,p,alternatives,sub,rows))
   with zipfile.ZipFile(archive) as z:
    inventory(z,'financial');raw={m:read_source_rows(z,m,ids) for m,ids in wanted.items()}
    members={}
    for member in wanted:
     h=hashlib.sha256()
     with z.open(member) as f:
      for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
     members[member]=h.hexdigest()
    for cik,p,alternatives,sub,rows in pending:
     for member,items in rows.items():
      for row in items:
       if {k:row[k] for k in SCHEMAS[member]}!=raw[member][row['rowid']]:raise ValueError('raw archive/DB disagreement')
     facts=[]
     for role in ('current','prior'):
      n=p[role];facts.append({'candidate_role':role,'metric':n['tag'],'taxonomy_as_reported':n['version'],'value_as_reported':n['value'],'unit_as_reported':n['uom'],'reported_context_date_as_filed':n['ddate'],'quarters_as_reported':n['qtrs'],'segments_as_reported':n['segments'],'coreg_as_reported':n['coreg'],'footnote_as_reported':n['footnote'],'source_num_rowid':n['rowid'],'source_row_sha256':digest(encode(raw['num.txt'][n['rowid']])),'exact_period_start':None,'exact_period_end_verified':False})
     packets.append({'id':digest(encode({'batch':b,'identity':key(b,p)})),'issuer_cik':cik,'issuer_name_as_filed':sub['name'],'status':'PREPARED_REVENUE_REVIEW_CANDIDATE_NOT_COMPARABLE','filing_batch':BATCHES[b],'accession':p['accession'],'form_as_filed':sub['form'],'amendment_as_filed':sub['form'].endswith('/A'),'filing_date_as_filed':sub['filed'],'submission_report_period_as_filed':sub['period'],'fiscal_year_as_filed':sub['fy'],'fiscal_period_as_filed':sub['fp'],'source_sub_rowid':sub['rowid'],'source_sub_row_sha256':digest(encode(raw['sub.txt'][sub['rowid']])),'source_url':f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{p['accession'].replace('-','')}/{p['accession']}-index.html",'source_link_verified_by_fetch':False,'facts':facts,'taxonomy':{k:p['taxonomy'][k] for k in ('rowid','tag','version','custom','abstract','datatype','iord')},'source_tag_row_sha256':digest(encode(raw['tag.txt'][p['taxonomy']['rowid']])),'presentation':p['presentation'],'source_pre_row_sha256':{str(r['rowid']):digest(encode(raw['pre.txt'][r['rowid']])) for r in p['presentation']},'source_archive_sha256':summary['source_archive_sha256'],'database_sha256':summary['database_sha256'],'other_candidate_pairs_for_issuer_not_shown':alternatives-1,'other_candidates_reconciled':False,'original_status':'EXACT_ACCESSION_PRESENT_NOT_REVIEWED' if p['accession'] in original_acc else 'NO_EXACT_ACCESSION_IN_SCOPED_RETAINED_ORIGINAL_INVENTORY','original_filing_text_checked':False,'first_public_utc':None,'first_observed_utc':None,'consolidated_scope_verified':False,'comparability_verified':False,'absolute_change':None,'percentage_change':None,'outcome_status':'INSUFFICIENT_EVIDENCE','next_review_action':'Read the exact accession original statements and contexts to establish start/end dates, unit, consolidation and comparative presentation before considering any change calculation.'})
   sources[b]={'archive_sha256':summary['source_archive_sha256'],'database_sha256':summary['database_sha256'],'members_sha256':members,'archive_url':'https://www.sec.gov/files/dera/data/financial-statement-data-sets/'+('2025q4' if b=='q4' else '2026'+b)+'.zip'}
  finally:conn.close()
  if sha(db)!=summary['database_sha256'] or sha(archive)!=summary['source_archive_sha256']:raise ValueError('source changed')
 return {'schema_version':1,'policy_sha256':plan_sha,'policy':{k:plan[k] for k in ('policy_version','created_at_utc','selection','metrics','issuer_limit','tie_break_fields','duplicate_tie_policy')},'queue_exclusion_pin':plan['queue'],'completed_input_pins':{b:m['files'] for b,m in plan['inputs'].items()},'counts':counts,'upstream_group_dispositions':{b:{'context_groups':s['context_groups'],'group_dispositions':s['group_dispositions'],'row_counts':s['row_counts']} for b,s in summaries.items()},'source_receipts':sources,'scoped_original_inventory':{'accessions_checked':len(original_acc),'ten_package_archive':originals['provenance'],'xbrl_receipt_sha256':receipt_sha,'xbrl_archive_sha256':receipt['zip_sha256']},'packets':sorted(packets,key=lambda p:int(p['issuer_cik'])),'limitations':['Purposeful retrospective lowest-CIK diagnostic sample, not representative or selected for performance. Most recent means only among these retained candidate batches.','Prepared values match raw archive fields; qtrs and rounded context dates do not establish exact durations or accounting comparability. Empty dimensions do not prove consolidated scope.','Each selected pair remains unqualified. Missing originals refer only to the explicit checked inventory; no network availability or global absence claim.','Other candidate filings and all upstream rejection categories remain in pinned inputs. No values are reconciled, amendments collapsed, or conflicts overwritten.','No change arithmetic, forecasts, prices, timing eligibility, security mapping, training admission or trading actions. Existing108 queue is unchanged.'],'training_ready':False,'execution_ready':False}
def run(destination,**kwargs):
 out=Path(destination).resolve();repo=Path(__file__).resolve().parents[1]
 if out.is_relative_to(repo) or not out.parent.is_dir():raise ValueError('trusted external output parent required')
 out.mkdir(mode=0o700,exist_ok=False);write_private(out/'INCOMPLETE',{'status':'INCOMPLETE_NOT_USABLE'})
 result=audit(**kwargs);write_private(out/'review.json',result)
 write_private(out/'COMPLETE.json',{'review_sha256':sha(out/'review.json')});(out/'INCOMPLETE').unlink()
 return result

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('root','workspace','plan-path','plan-sha','databases','archives','original-zip','original-receipt','original-package','output-directory'):p.add_argument('--'+n,required=True)
 a=vars(p.parse_args());out=a.pop('output_directory');a['databases']=json.loads(Path(a['databases']).read_text());a['archives']=json.loads(Path(a['archives']).read_text());run(out,**a)
if __name__=='__main__':main()
