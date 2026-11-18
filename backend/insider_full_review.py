"""Bounded full retained P/S filing review, never economic trade or model admission."""
import argparse
from collections import Counter, defaultdict
import hashlib,json,sqlite3,re
from pathlib import Path
from insider_review_cards import project, cik, BATCHES, LIMITATIONS
from insider_transaction_evidence import audit as source_audit, canonical_sha
from financial_pair_candidates import sha

BASE='web/insider-full/v1/'
CARD_FIELDS=('batch_id','accession','issuer_cik','issuer_name_as_filed','issuer_ticker_as_filed','form_as_filed','filing_date','period_of_report_as_filed','selected_transaction_rows','reported_code_counts','transaction_date_min','transaction_date_max','invalid_transaction_date_rows','diagnostic_row_counts','submission_plan_flag_status','review_status','original_reviewed','amendment_reconciled','sec_accession_lookup_url','source_link_status','source_submission_rowid','source_submission_sha256','first_public_utc','decision_utc','training_ready','execution_ready')
LIMITS={'index_bytes':3_000_000,'shard_bytes':1_000_000,'package_bytes':64_000_000,'filings':50_000,'rows':200_000}

def encoded(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)+'\n').encode()
def digest(value):return hashlib.sha256(value).hexdigest()
def bucket(c):return hashlib.sha256(c.encode('ascii')).hexdigest()[:2]
def row_bundle(rows):
    refs=sorted([{'rowid':r['source_rowid'],'sha256':r['source_row_sha256'],'transaction_key':r['transaction_key']} for r in rows],key=lambda x:(x['rowid'],x['transaction_key']))
    return digest(encoded(refs))

def project_all(batch,records,subs):
    """No deletion of a bad row: quarantine its whole filing, preserve private evidence."""
    groups=defaultdict(list);seen=set();codes=Counter()
    for r in records:
        if r['transaction_fields_as_filed']['TRANS_CODE'] not in {'P','S'}:continue
        key=(r['accession'],r['transaction_key'])
        if key in seen:raise ValueError('duplicate selected source identity')
        seen.add(key);groups[r['accession']].append(r);codes[r['transaction_fields_as_filed']['TRANS_CODE']]+=1
    if len(seen)>LIMITS['rows'] or len(groups)>LIMITS['filings']:raise ValueError('selected input bound')
    cards=[];held=[]
    for acc,rows in sorted(groups.items()):
        bundle=row_bundle(rows)
        try:
            cohort={cik(r['submission_as_filed']['ISSUERCIK']) for r in rows}
            if len(cohort)!=1:raise ValueError('conflicting filing issuer')
            cs,selected=project(batch,rows,subs,cohort)
            if len(cs)!=1 or len(selected)!=len(rows):raise ValueError('filing incomplete')
        except ValueError:
            # Never echo malformed values or exception text into public artifacts.
            safe_acc=acc if isinstance(acc,str) and re.fullmatch(r'[0-9]{10}-[0-9]{2}-[0-9]{6}',acc) else None
            held.append({'batch_id':batch,'accession':safe_acc,'quarantine_id':digest(encoded({'batch_id':batch,'bundle':bundle})),'selected_transaction_rows':len(rows),'source_transaction_bundle_sha256':bundle,'status':'WHOLE_FILING_QUARANTINED','reason':'FILING_PROJECTION_VALIDATION_FAILED','training_ready':False,'execution_ready':False})
            continue
        c={k:cs[0][k] for k in CARD_FIELDS};c['source_transaction_bundle_sha256']=bundle
        cards.append(c)
    if sum(c['selected_transaction_rows'] for c in cards+held)!=len(seen):raise ValueError('row conservation')
    return cards,held,{'selected_transaction_rows':len(seen),'selected_filings':len(groups),'reported_code_counts':dict(sorted(codes.items())),'admitted_review_filings':len(cards),'quarantined_filings':len(held),'quarantined_rows':sum(x['selected_transaction_rows'] for x in held)}

def package(cards,quarantine,sources):
    groups=defaultdict(list);seen=set()
    for card in cards:
        k=(card['batch_id'],card['accession'])
        if k in seen:raise ValueError('duplicate filing')
        seen.add(k);groups[card['issuer_cik']].append(card)
    # Same accession in two filing batches is not presumed independent.
    valid_accessions=[x['accession'] for x in cards+quarantine if x['accession'] is not None]
    if len(set(valid_accessions))!=len(valid_accessions):raise ValueError('cross-batch accession overlap')
    if len({x['quarantine_id'] for x in quarantine})!=len(quarantine):raise ValueError('duplicate quarantine identity')
    directory=[];shards={f'{i:02x}':[] for i in range(256)}
    for key,filings in sorted(groups.items()):
        filings.sort(key=lambda c:(c['filing_date'],c['accession']))
        codes=Counter();flags=Counter()
        for f in filings:codes.update(f['reported_code_counts']);flags.update(f['diagnostic_row_counts'])
        b=bucket(key)
        directory.append({'issuer_cik':key,'issuer_names_as_filed':sorted({c['issuer_name_as_filed'] for c in filings}),'issuer_tickers_as_filed':sorted({c['issuer_ticker_as_filed'] for c in filings}),'filings':len(filings),'selected_transaction_rows':sum(c['selected_transaction_rows'] for c in filings),'reported_code_counts':dict(sorted(codes.items())),'diagnostic_row_counts':dict(sorted(flags.items())),'first_filing_date':filings[0]['filing_date'],'last_filing_date':filings[-1]['filing_date'],'shard':b,'review_status':'ORIGINAL_FILING_REVIEW_REQUIRED'})
        shards[b].append({'issuer_cik':key,'filings':filings})
    payloads={};pins=[]
    for b,issuers in sorted(shards.items()):
        raw=encoded({'schema_version':1,'bucket':b,'issuers':issuers});path=BASE+'details/'+b+'.json'
        if len(raw)>LIMITS['shard_bytes']:raise ValueError('detail shard byte bound')
        payloads[path]=raw;pins.append({'bucket':b,'path':path,'byte_count':len(raw),'sha256':digest(raw),'issuer_ciks':[i['issuer_cik'] for i in issuers],'filings':sum(len(i['filings']) for i in issuers)})
    counts={'issuer_ciks':len(groups),'filings':len(cards),'selected_transaction_rows':sum(c['selected_transaction_rows'] for c in cards),'quarantined_filings':len(quarantine),'quarantined_rows':sum(c['selected_transaction_rows'] for c in quarantine)}
    counts['all_selected_transaction_rows']=counts['selected_transaction_rows']+counts['quarantined_rows']
    if counts['all_selected_transaction_rows']!=sum(s['counts']['selected_transaction_rows'] for s in sources):raise ValueError('source to package row conservation')
    index={'schema_version':1,'status':'FULL_RETAINED_P_S_FILING_REVIEW_NOT_SIGNALS','selection':'Every reported P/S nonderivative transaction row in the two retained 2026 Q2 and Q3 filing batches; no price, outcome or issuer selection.','counts':counts,'sources':sources,'issuers':directory,'detail_shards':pins,'quarantine':quarantine,'limitations':[x for x in LIMITATIONS if not x.startswith('The ten issuer')]+['Coverage is the two retained filing batches, not complete company histories. Quarantine is whole-filing; unassessable data is never labeled no activity.','Issuer-level diagnostic counts sum rows across filings. Flags overlap; amendments are not reconciled and row counts are not economic trades.','Transaction bundle hashes bind sorted rowid/hash/key references, not original byte slices. Source archive and database hashes bind retained bytes.'],'training_ready':False,'execution_ready':False,'first_public_utc':None,'limits':LIMITS}
    raw=encoded(index)
    if len(raw)>LIMITS['index_bytes']:raise ValueError('index byte bound')
    payloads[BASE+'index.json']=raw
    if sum(map(len,payloads.values()))>LIMITS['package_bytes']:raise ValueError('package byte bound')
    return index,payloads

def build(config):
    if not isinstance(config,list) or len(config)!=2 or {x['batch_id'] for x in config}!=set(BATCHES):raise ValueError('exact retained batches required')
    allcards=[];held=[];sources=[]
    for item in sorted(config,key=lambda x:x['batch_id']):
        summary,records=source_audit(item['database'],item['database_sha256'],item['archive'],item['archive_sha256'])
        db=sqlite3.connect(Path(item['database']).resolve().as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
        try:subs={r['ACCESSION_NUMBER']:dict(r) for r in db.execute('SELECT rowid,* FROM insider_submission')}
        finally:db.close()
        cards,q,counts=project_all(item['batch_id'],records,subs)
        if sha(item['database'])!=item['database_sha256'] or sha(item['archive'])!=item['archive_sha256']:raise ValueError('source changed')
        allcards+=cards;held+=q
        sources.append({'batch_id':item['batch_id'],'archive_sha256':item['archive_sha256'],'database_sha256':item['database_sha256'],'readme_sha256':summary['bundled_readme_sha256'],'source_url':f'https://www.sec.gov/files/datastandardsinnovation/data/insider-transactions-data-sets/{item["batch_id"]}_form345.zip','filing_date_range':list(BATCHES[item['batch_id']]),'source_retrieved_at':None,'counts':counts})
    return package(allcards,held,sources)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    out=Path(a.output).resolve()
    if out.is_relative_to(Path(__file__).resolve().parents[1]) or not out.parent.is_dir():raise ValueError('new private output outside checkout required')
    index,payloads=build(json.loads(Path(a.config).read_text()))
    out.mkdir(mode=0o700,exist_ok=False);(out/'INCOMPLETE').write_text('not usable')
    for path,raw in payloads.items():
        dest=out/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);dest.chmod(0o600)
    pins=[{'path':p,'sha256':digest((out/p).read_bytes()),'byte_count':len(r)} for p,r in sorted(payloads.items())]
    if any(x['sha256']!=digest(payloads[x['path']]) for x in pins):raise ValueError('persisted output changed')
    (out/'COMPLETE.json').write_bytes(encoded({'counts':index['counts'],'files':pins}));(out/'COMPLETE.json').chmod(0o600);(out/'INCOMPLETE').unlink()
    print(json.dumps({'counts':index['counts'],'bytes':sum(map(len,payloads.values())),'max_shard':max(len(v) for k,v in payloads.items() if '/details/' in k)}))
