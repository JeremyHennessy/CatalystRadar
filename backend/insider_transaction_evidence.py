"""Offline reported-code diagnostics, not insider trading signals or compliance findings."""
import argparse
from collections import Counter,defaultdict
import datetime as dt
from decimal import Decimal,InvalidOperation
import hashlib,json,re,sqlite3,zipfile
from pathlib import Path
from financial_pair_candidates import sha,write_private,publish
from sec_prepared_data import SCHEMAS,inventory

CODES={'A':'grant_award_or_rule16b3_acquisition','C':'derivative_conversion','D':'disposition_to_issuer','E':'short_derivative_expiration','F':'exercise_price_or_tax_withholding','G':'gift','H':'long_derivative_expiration_or_cancellation','I':'discretionary_rule16b3_transaction','J':'other_acquisition_or_disposition','L':'small_acquisition','M':'exempt_derivative_exercise_or_conversion','O':'out_of_money_exercise','P':'open_market_or_private_purchase','S':'open_market_or_private_sale','U':'change_of_control_tender_disposition','W':'will_or_descent_distribution','X':'in_or_at_money_exercise','Z':'voting_trust_deposit_or_withdrawal'}
FIELDS=('TRANS_DATE','DEEMED_EXECUTION_DATE','TRANS_FORM_TYPE','TRANS_CODE','EQUITY_SWAP_INVOLVED','TRANS_TIMELINESS','TRANS_SHARES','TRANS_PRICEPERSHARE','TRANS_ACQUIRED_DISP_CD','DIRECT_INDIRECT_OWNERSHIP')
SUB_FIELDS=('ACCESSION_NUMBER','FILING_DATE','PERIOD_OF_REPORT','DATE_OF_ORIG_SUB','DOCUMENT_TYPE','ISSUERCIK','ISSUERTRADINGSYMBOL','AFF10B5ONE')
MONTHS={v:i for i,v in enumerate('JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC'.split(),1)}
def date(value):
    m=re.fullmatch(r'(\d{2})-([A-Z]{3})-(\d{4})',value)
    if not m or m[2] not in MONTHS:return None
    try:return dt.date(int(m[3]),MONTHS[m[2]],int(m[1]))
    except ValueError:return None

def numeric_status(value):
    if value=='':return 'MISSING'
    if len(value)>100 or not re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?',value):return 'INVALID'
    try:
        n=Decimal(value)
        if not n.is_finite():return 'INVALID'
        return 'NEGATIVE' if n<0 else 'ZERO' if n==0 else 'POSITIVE'
    except InvalidOperation:return 'INVALID'

def canonical_sha(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

def classify(row,sub,footnotes):
    code=row['TRANS_CODE'];flags=[];links=[]
    if code not in CODES:flags.append('MISSING_OR_UNKNOWN_TRANSACTION_CODE')
    ad=row['TRANS_ACQUIRED_DISP_CD']
    if ad not in {'A','D'}:flags.append('MISSING_OR_UNKNOWN_ACQUIRE_DISPOSE_CODE')
    if code in {'P','S'} and ad!={'P':'A','S':'D'}[code]:flags.append('PURCHASE_SALE_DIRECTION_CONTRADICTION')
    form=sub['DOCUMENT_TYPE']
    if form.endswith('/A'):flags.append('AMENDMENT_NOT_RECONCILED')
    if form not in {'3','3/A','4','4/A','5','5/A'}:flags.append('UNKNOWN_SUBMISSION_FORM')
    if row['TRANS_FORM_TYPE'] not in {'3','4','5'}:flags.append('UNKNOWN_TRANSACTION_FORM')
    elif row['TRANS_FORM_TYPE']!=form.split('/')[0]:flags.append('TRANSACTION_SUBMISSION_FORM_DIFFERENCE')
    filed=date(sub['FILING_DATE']);trans=date(row['TRANS_DATE']);lag=None
    if filed is None or trans is None:flags.append('MISSING_OR_INVALID_DATE')
    else:
        lag=(filed-trans).days
        if lag<0:flags.append('TRANSACTION_DATE_AFTER_FILING_DATE')
    if row['DEEMED_EXECUTION_DATE']:flags.append('DEEMED_EXECUTION_DATE_REQUIRES_REVIEW')
    if row['EQUITY_SWAP_INVOLVED'] in {'1','true'}:flags.append('EQUITY_SWAP_REPORTED')
    elif row['EQUITY_SWAP_INVOLVED'] not in {'0','false'}:flags.append('UNKNOWN_EQUITY_SWAP_FLAG')
    statuses={k:numeric_status(row[k]) for k in ['TRANS_SHARES','TRANS_PRICEPERSHARE']}
    for key,status in statuses.items():
        if status!='POSITIVE':flags.append(key+'_'+status)
    for field,value in row.items():
        if not field.endswith('_FN') or not value:continue
        flags.append('FOOTNOTE_CONTEXT_REQUIRED')
        ids=[v.strip() for v in value.split(',')]
        if any(not re.fullmatch(r'F\d+',v) for v in ids) or len(set(ids))!=len(ids):
            flags.append('UNSUPPORTED_FOOTNOTE_REFERENCE');links.append({'field':field,'reference_as_filed':value,'status':'UNPARSED'});continue
        for key in ids:
            matches=footnotes.get((row['ACCESSION_NUMBER'],key),[])
            status='RESOLVED' if len(matches)==1 else 'MISSING' if not matches else 'AMBIGUOUS'
            if status!='RESOLVED':flags.append('FOOTNOTE_'+status)
            links.append({'field':field,'id':key,'status':status,'source_rows':matches})
    plan=sub['AFF10B5ONE'];plan_status='REPORTED_TRUE' if plan in {'1','true'} else 'REPORTED_FALSE' if plan in {'0','false'} else 'UNKNOWN'
    if plan_status=='UNKNOWN':flags.append('UNKNOWN_SUBMISSION_PLAN_FLAG')
    return {'reported_code_category':CODES.get(code,'unknown'),'diagnostic_flags':sorted(set(flags)),'numeric_field_status':statuses,'calendar_days_transaction_to_filing':lag,'submission_plan_flag_status':plan_status,'footnote_links':links,'open_market_trade_verified':False,'economic_direction_verified':False,'training_ready':False}

def audit(database,expected_db_sha,archive,expected_archive_sha):
    if sha(database)!=expected_db_sha or sha(archive)!=expected_archive_sha:raise ValueError('input hash mismatch')
    with zipfile.ZipFile(archive) as z:
        inventory(z,'insider');info=z.getinfo('FORM_345_readme.htm')
        if info.file_size>1_000_000:raise ValueError('readme bound')
        readme_sha=hashlib.sha256(z.read(info)).hexdigest()
    db=sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    try:
        if db.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise ValueError('database integrity')
        for name in ['SUBMISSION.tsv','NONDERIV_TRANS.tsv','FOOTNOTES.tsv']:
            table='insider_'+name[:-4].lower()
            if [r[1] for r in db.execute('PRAGMA table_info('+table+')')]!=SCHEMAS[name]:raise ValueError('source schema mismatch')
        subs={}
        for raw in db.execute('SELECT rowid,* FROM insider_submission'):
            r=dict(raw);key=r['ACCESSION_NUMBER']
            if key in subs or not re.fullmatch(r'\d{10}-\d{2}-\d{6}',key):raise ValueError('submission identity')
            subs[key]=r
        if len(subs)>100_000:raise ValueError('submission bound')
        notes=defaultdict(list)
        for raw in db.execute('SELECT rowid,* FROM insider_footnotes'):
            r=dict(raw)
            if r['ACCESSION_NUMBER'] not in subs:raise ValueError('orphan footnote')
            notes[(r['ACCESSION_NUMBER'],r['FOOTNOTE_ID'])].append({'rowid':r['rowid'],'source_row_sha256':canonical_sha({k:v for k,v in r.items() if k!='rowid'})})
        if sum(map(len,notes.values()))>500_000:raise ValueError('footnote bound')
        counts=Counter();codes=Counter();forms=Counter();flags=Counter();plans=Counter();lags=Counter();records=[];ids=set()
        for raw in db.execute('SELECT rowid,* FROM insider_nonderiv_trans ORDER BY rowid'):
            r=dict(raw);rowid=r.pop('rowid');acc=r['ACCESSION_NUMBER'];key=(acc,r['NONDERIV_TRANS_SK'])
            if acc not in subs or key in ids or not re.fullmatch(r'\d{1,20}',r['NONDERIV_TRANS_SK']):raise ValueError('orphan or duplicate transaction identity')
            ids.add(key);sub=subs[acc];v=classify(r,sub,notes);counts['transaction_rows']+=1;codes[r['TRANS_CODE'] if r['TRANS_CODE'] in CODES else 'MISSING' if r['TRANS_CODE']=='' else 'UNKNOWN']+=1;forms[sub['DOCUMENT_TYPE'] if sub['DOCUMENT_TYPE'] in {'3','3/A','4','4/A','5','5/A'} else 'UNKNOWN']+=1;flags.update(v['diagnostic_flags']);plans[v['submission_plan_flag_status']]+=1
            lag=v['calendar_days_transaction_to_filing'];lags['UNKNOWN' if lag is None else 'NEGATIVE' if lag<0 else 'ZERO' if lag==0 else '1_TO_7' if lag<=7 else '8_TO_30' if lag<=30 else 'OVER_30']+=1
            if not v['diagnostic_flags']:counts['rows_without_listed_diagnostics_not_qualified']+=1
            records.append({'source_rowid':rowid,'source_row_sha256':canonical_sha(r),'transaction_key':r['NONDERIV_TRANS_SK'],'accession':acc,'transaction_fields_as_filed':{k:r[k] for k in FIELDS},'submission_rowid':sub['rowid'],'submission_as_filed':{k:sub[k] for k in SUB_FIELDS},**v})
            if len(records)>100_000:raise ValueError('transaction bound')
    finally:db.close()
    if not records:raise ValueError('empty transaction evidence')
    if sha(database)!=expected_db_sha or sha(archive)!=expected_archive_sha:raise ValueError('input changed')
    summary={'schema_version':1,'status':'REPORTED_INSIDER_CODE_DIAGNOSTICS_NOT_SIGNALS','audit_completed_at':dt.datetime.now(dt.timezone.utc).isoformat(),'source_archive_sha256':expected_archive_sha,'database_sha256':expected_db_sha,'bundled_readme_sha256':readme_sha,'source_tables':['NONDERIV_TRANS.tsv','SUBMISSION.tsv','FOOTNOTES.tsv'],'counts':dict(counts),'reported_code_counts':dict(sorted(codes.items())),'transaction_rows_by_submission_form':dict(sorted(forms.items())),'diagnostic_flag_counts':dict(sorted(flags.items())),'submission_plan_flag_per_transaction_counts':dict(sorted(plans.items())),'calendar_day_lag_buckets':dict(sorted(lags.items())),'transaction_accessions':len({r['accession'] for r in records}),'training_ready':False,'execution_ready':False,'limitations':['P/S codes describe open-market OR private transactions, not verified exchange executions or directional signals.','Code/direction contradictions, amendments and footnotes require primary-source review; no rows are repaired or removed. Diagnostics overlap and cannot be summed as distinct transactions.','Form 10b5-1 flag is submission-level and does not establish every individual row was under a valid plan or imply intent.','Transaction and filing fields are date-only; calendar-day differences are not business-day deadlines, compliance findings or first-public timestamps.','Shares, prices and ownership remain as filed. No currency is inferred, no dollar totals or current positions computed, and reporting-owner joins do not multiply transaction rows.','No owner names, addresses or individual transaction values appear in the public aggregate. Private row hashes/rowids bind original data, not source authenticity or prospectively known features.','A row without listed diagnostics is not financially qualified, a complete validation or an approved training example. Derivative transactions/holdings are outside this scoped audit.']}
    return summary,records

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--database',required=True);p.add_argument('--database-sha256',required=True);p.add_argument('--archive',required=True);p.add_argument('--archive-sha256',required=True);p.add_argument('--output-directory',required=True);a=p.parse_args();out=Path(a.output_directory).resolve()
    if out.is_relative_to(Path(__file__).resolve().parents[1]) or not out.parent.is_dir():raise ValueError('trusted private parent outside checkout required')
    out.mkdir(mode=0o700,exist_ok=False);write_private(out/'INCOMPLETE',{'status':'INCOMPLETE_NOT_USABLE'});s,rows=audit(a.database,a.database_sha256,a.archive,a.archive_sha256);publish(out,s,rows);print(json.dumps(s))
